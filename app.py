import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Finans v3", layout="wide")

# --- 2. VERİ ÜRETME SİMÜLASYONU ---
@st.cache_data
def veri_hazirla():
    np.random.seed(42)
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    urunler = [f"Ürün {i}" for i in range(1, 41)]
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    
    data = []
    bugun = datetime(2026, 1, 30)
    
    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler)
        t = np.random.choice(tedarikciler)
        adet = np.random.randint(5, 50)
        alis = np.random.randint(200, 800)
        satis = alis * np.random.uniform(1.30, 1.80)
        stok = np.random.randint(10, 500)
        
        # Vade Senaryoları
        satis_t = bugun - timedelta(days=np.random.randint(0, 30))
        m_vade = satis_t + timedelta(days=np.random.randint(150, 300))
        
        # Rastgele Yeşil/Kırmızı dengesi
        if np.random.rand() > 0.4:
            t_vade = m_vade + timedelta(days=30) # Yeşil
        else:
            t_vade = m_vade - timedelta(days=30) # Kırmızı
            
        data.append([m, u, t, adet, alis, satis, m_vade, t_vade, stok])
        
    df = pd.DataFrame(data, columns=['Müşteri', 'Ürün', 'Tedarikçi', 'Adet', 'Alis', 'Satis', 'M_Vade', 'T_Vade', 'Stok'])
    df['Borc'] = df['Alis'] * df['Adet']
    df['Tahsilat'] = df['Satis'] * df['Adet']
    df['Stok_Deger'] = df['Satis'] * df['Stok']
    return df

df = veri_hazirla()

# --- 3. ÜST METRİKLER (MODERN GÖRÜNÜM) ---
st.title("🌿 Zirai İşletme Finans Paneli")
st.markdown("### Stratejik Nakit Akışı ve Stok Yönetimi")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Toplam Borç", f"{df['Borc'].sum():,.0f} ₺")
c2.metric("Kasadaki Çekler", f"{df['Tahsilat'].sum():,.0f} ₺")
c3.metric("Stok Potansiyeli", f"{df['Stok_Deger'].sum():,.0f} ₺")
net_d = (df['Tahsilat'].sum() + df['Stok_Deger'].sum()) - df['Borc'].sum()
c4.metric("Net Likidite", f"{net_d:,.0f} ₺", delta="GÜVENLİ")

st.divider()

# --- 4. ANA SEKMELER ---
tab1, tab2, tab3 = st.tabs(["💰 Nakit Akış Analizi", "📦 Stok Takvimi", "🔍 Arama"])

with tab1:
    st.subheader("Tedarikçi Ödeme Dengesi")
    t_analiz = df.groupby('Tedarikçi').agg({
        'Borc': 'sum', 'Tahsilat': 'sum', 'Stok_Deger': 'sum',
        'T_Vade': 'min', 'M_Vade': 'max'
    }).reset_index()
    
    t_analiz['Net_Denge'] = (t_analiz['Tahsilat'] + t_analiz['Stok_Deger']) - t_analiz['Borc']
    t_analiz['Gun_Farki'] = (t_analiz['T_Vade'] - t_analiz['M_Vade']).dt.days

    def nakit_renkle(row):
        if row['Net_Denge'] > 0 and row['Gun_Farki'] >= 0:
            return ['background-color: #d1fae5'] * len(row) # Yeşil
        elif row['Net_Denge'] > 0 and row['Gun_Farki'] < 0:
            return ['background-color: #fef3c7'] * len(row) # Sarı
        else:
            return ['background-color: #fee2e2'] * len(row) # Kırmızı

    st.dataframe(t_analiz.style.apply(nakit_renkle, axis=1).format(precision=0), use_container_width=True)

with tab2:
    st.subheader("Kritik Stok ve Satış Planı")
    stok_df = df.groupby('Ürün').agg({'Stok': 'mean', 'T_Vade': 'min'}).reset_index()
    stok_df['En Geç Güvenli Satış'] = stok_df['T_Vade'] - timedelta(days=15)
    
    st.dataframe(stok_df.sort_values('Stok'), use_container_width=True)

with tab3:
    st.subheader("Hızlı Sorgulama")
    ara = st.text_input("Müşteri veya Ürün adı girin...")
    if ara:
        f_df = df[df['Müşteri'].str.contains(ara, case=False) | df['Ürün'].str.contains(ara, case=False)]
        st.dataframe(f_df, use_container_width=True)
    else:
        st.write("Lütfen arama kutusunu kullanın.")

# --- 5. YAN MENÜ ---
st.sidebar.header("⚙️ Ayarlar")
if st.sidebar.button("📊 Verileri Tazele"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("✅ Sistem Aktif")
st.sidebar.write(f"📅 {datetime.now().strftime('%d.%m.%Y')}")
