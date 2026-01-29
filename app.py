import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Finans v4", layout="wide")

# --- 2. VERİ ÜRETME SİMÜLASYONU ---
@st.cache_data
def veri_hazirla():
    np.random.seed(42)
    # 50 Müşteri havuzu
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    musteriler[0] = "Mehmet Gök" # Örnek müşteri
    
    urunler = [f"Ürün {i}" for i in range(1, 41)]
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    
    data = []
    bugun = datetime(2026, 1, 30)
    
    # 1000 satırlık hareket verisi oluşturuyoruz
    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler)
        t = np.random.choice(tedarikciler)
        adet = np.random.randint(5, 50)
        alis = np.random.randint(200, 800)
        
        # Karlılık senaryoları (Yeşil, Sarı, Kırmızı dağılımı için)
        kar_sans = np.random.rand()
        if kar_sans > 0.6: # Yüksek kar
            satis = alis * np.random.uniform(1.30, 1.50)
        elif kar_sans > 0.3: # Orta kar
            satis = alis * np.random.uniform(1.15, 1.25)
        else: # Düşük kar
            satis = alis * np.random.uniform(1.01, 1.10)
            
        stok = np.random.randint(10, 500)
        satis_t = bugun - timedelta(days=np.random.randint(0, 30))
        m_vade = satis_t + timedelta(days=np.random.randint(150, 300))
        
        # Vade dengesi
        if np.random.rand() > 0.5:
            t_vade = m_vade + timedelta(days=30)
        else:
            t_vade = m_vade - timedelta(days=30)
            
        data.append([m, u, t, adet, alis, satis, m_vade, t_vade, stok])
        
    df_raw = pd.DataFrame(data, columns=['Müşteri', 'Ürün', 'Tedarikçi', 'Adet', 'Alis', 'Satis', 'M_Vade', 'T_Vade', 'Stok'])
    
    # Hesaplamalar
    df_raw['Borc'] = df_raw['Alis'] * df_raw['Adet']
    df_raw['Tahsilat'] = df_raw['Satis'] * df_raw['Adet']
    
    # Finansman maliyeti düşülmüş kar oranı hesaplama
    vade_gun = (df_raw['M_Vade'] - df_raw['T_Vade']).dt.days
    df_raw['Net_Kar_Orani'] = ((df_raw['Satis'] - df_raw['Alis']) - (df_raw['Alis'] * 0.001 * vade_gun)) / df_raw['Alis']
    
    return df_raw

df_raw = veri_hazirla()

# --- 3. ÜST METRİKLER ---
st.title("🌿 Zirai İşletme Finans ve Karlılık Paneli")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Toplam Borç", f"{df_raw['Borc'].sum():,.0f} ₺")
c2.metric("Kasadaki Çekler", f"{df_raw['Tahsilat'].sum():,.0f} ₺")
genel_kar = df_raw['Net_Kar_Orani'].mean()
c3.metric("Genel Kar Ortalaması", f"{genel_kar:.2%}")
c4.metric("Aktif Müşteri", df_raw['Müşteri'].nunique())

st.divider()

# --- 4. ANA SEKMELER ---
tab1, tab2, tab3 = st.tabs(["👥 Müşteri Karlılık Analizi", "💰 Nakit Akışı", "📦 Stok Yönetimi"])

with tab1:
    st.subheader("Müşteri Genel Karlılık Durumu")
    st.info("💡 Bu tablo müşterilerin tüm alımlarının ortalamasını analiz eder.")
    
    # Müşteri Bazlı Gruplama
    m_analiz = df_raw.groupby('Müşteri').agg({
        'Tahsilat': 'sum',
        'Net_Kar_Orani': 'mean',
        'Adet': 'sum'
    }).reset_index()

    def musteri_renkle(val):
        if val >= 0.25: color = '#d1fae5' # Yeşil
        elif 0.12 <= val < 0.25: color = '#fef3c7' # Sarı
        else: color = '#fee2e2' # Kırmızı
        return f'background-color: {color}'

    st.dataframe(
        m_analiz.sort_values('Net_Kar_Orani', ascending=False).style
        .applymap(musteri_renkle, subset=['Net_Kar_Orani'])
        .format({'Net_Kar_Orani': '{:.2%}', 'Tahsilat': '{:,.0f}₺'}),
        use_container_width=True
    )

with tab2:
    st.subheader("Tedarikçi Borç ve Tahsilat Dengesi")
    t_analiz = df_raw.groupby('Tedarikçi').agg({
        'Borc': 'sum', 'Tahsilat': 'sum', 'T_Vade': 'min', 'M_Vade': 'max'
    }).reset_index()
    t_analiz['Denge'] = t_analiz['Tahsilat'] - t_analiz['Borc']
    t_analiz['Vade_Farki'] = (t_analiz['T_Vade'] - t_analiz['M_Vade']).dt.days

    def nakit_renkle(row):
        if row['Denge'] > 0 and row['Vade_Farki'] >= 0: return ['background-color: #d1fae5'] * len(row)
        else: return ['background-color: #fee2e2'] * len(row)

    st.dataframe(t_analiz.style.apply(nakit_renkle, axis=1).format(precision=0), use_container_width=True)

with tab3:
    st.subheader("Ürün Stok ve Güvenli Satış Tarihleri")
    stok_df = df_raw.groupby('Ürün').agg({'Stok': 'mean', 'T_Vade': 'min'}).reset_index()
    stok_df['Son Güvenli Satış Tarihi'] = stok_df['T_Vade'] - timedelta(days=15)
    st.dataframe(stok_df.sort_values('Stok'), use_container_width=True)

# --- 5. YAN MENÜ ---
st.sidebar.header("⚙️ Kontrol Paneli")
ara = st.sidebar.text_input("🔍 Müşteri/Ürün Ara")
if ara:
    st.subheader(f"'{ara}' için Arama Sonuçları")
    sonuc = df_raw[df_raw['Müşteri'].str.contains(ara, case=False) | df_raw['Ürün'].str.contains(ara, case=False)]
    st.dataframe(sonuc)
