import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Finans Dashboard", page_icon="🌿", layout="wide")

# --- 2. VERİ YÜKLEME VE HESAPLAMA ---
@st.cache_data
def veri_yukle_stratejik():
    np.random.seed(99)
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    musteriler[0] = "Mehmet Gök"
    urunler = [f"Ürün {i}" for i in range(1, 41)]
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    
    data = []
    bugun = datetime(2026, 1, 30)
    
    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler)
        t = np.random.choice(tedarikciler)
        adet = np.random.randint(5, 50)
        alis_f = np.random.randint(200, 800)
        
        # Karlılık senaryoları (Net karı etkileyecek fiyatlar)
        kar_sans = np.random.rand()
        if kar_sans > 0.7: satis_f = alis_f * np.random.uniform(1.40, 1.60)
        elif kar_sans > 0.4: satis_f = alis_f * np.random.uniform(1.20, 1.30)
        else: satis_f = alis_f * np.random.uniform(1.05, 1.15)
        
        stok = np.random.randint(10, 500)
        satis_t = bugun - timedelta(days=np.random.randint(0, 30))
        
        # Vade Senaryoları
        v_senaryo = np.random.choice(['uzun', 'kisa', 'normal'])
        if v_senaryo == 'uzun':
            m_vade, t_vade = satis_t + timedelta(days=120), satis_t + timedelta(days=240)
        elif v_senaryo == 'kisa':
            m_vade, t_vade = satis_t + timedelta(days=200), satis_t + timedelta(days=60)
        else:
            m_vade, t_vade = satis_t + timedelta(days=150), satis_t + timedelta(days=160)
        
        data.append([m, u, t, adet, alis_f, satis_f, m_vade, t_vade, stok])
        
    df = pd.DataFrame(data, columns=['Müşteri', 'Ürün', 'Tedarikçi', 'Adet', 'Alis_F', 'Satis_F', 'Cek_Vade', 'Borc_Vade', 'Stok'])
    
    # Finansal Hesaplamalar
    df['Borc_Tutari'] = df['Alis_F'] * df['Adet']
    df['Tahsilat_Tutari'] = df['Satis_F'] * df['Adet']
    df['Stok_Potansiyel_Ciro'] = df['Satis_F'] * df['Stok']
    
    # Valörlü Net Kar Oranı (Vade farkı maliyeti düşülmüş)
    vade_gun_farki = (df['Cek_Vade'] - df['Borc_Vade']).dt.days
    df['Net_Kar_Orani'] = ((df['Satis_F'] - df['Alis_F']) - (df['Alis_F'] * 0.001 * vade_gun_farki)) / df['Alis_F']
    
    return df

df = veri_yukle_stratejik()

# --- 3. ÜST PANEL (METRİKLER) ---
st.title("🛡️ Stratejik Finans ve Müşteri Karlılık Yönetimi")

m1, m2, m3, m4, m5 = st.columns(5)
total_borc = df['Borc_Tutari'].sum()
total_tahsilat = df['Tahsilat_Tutari'].sum()
total_stok = df['Stok_Potansiyel_Ciro'].sum()
genel_net_kar = df['Net_Kar_Orani'].mean()
net_likidite = (total_tahsilat + total_stok) - total_borc

m1.metric("Toplam Borç", f"{total_borc:,.0f} ₺")
m2.metric("Kasadaki Çekler", f"{total_tahsilat:,.0f} ₺")
m3.metric("Stok Satış Değeri", f"{total_stok:,.0f} ₺")
m4.metric("Net Likidite", f"{net_likidite:,.0f} ₺")
m5.metric("Genel Ortalama Net Kar", f"{genel_net_kar:.2%}", delta="GÜNCEL")

st.divider()

# --- 4. ANALİZ SEKMELERİ ---
tab1, tab2, tab3 = st.tabs(["👥 Müşteri Net Karlılık", "💰 Nakit Akış & Denge", "📦 Stok Takvimi"])

# --- TAB 1: MÜŞTERİ NET KARLILIK ---
with tab1:
    st.subheader("Müşteri Bazlı Konsolide Net Karlılık Raporu")
    st.info("💡 Bu tablo, müşterinin tüm alımlarını ve vade maliyetlerini hesaplayarak 'Net Karlılığı' bulur.")
    
    # Müşteri bazlı toplulaştırma
    m_ozet = df.groupby('Müşteri').agg({
        'Tahsilat_Tutari': 'sum',
        'Net_Kar_Orani': 'mean',
        'Adet': 'sum'
    }).reset_index()
    
    # Yeni Net Karlılık Sütunu (Sıralama için)
    m_ozet = m_ozet.rename(columns={'Net_Kar_Orani': 'Net Karlılık'})

    def musteri_stil(row):
        val = row['Net Karlılık']
        if val >= 0.25: color = '#d4edda; color: #155724' # Yeşil
        elif 0.12 <= val < 0.25: color = '#fff3cd; color: #856404' # Sarı
        else: color = '#f8d7da; color: #721c24' # Kırmızı
        return [f'background-color: {color}'] * len(row)

    st.dataframe(
        m_ozet.sort_values('Net Karlılık', ascending=False).style
        .apply(musteri_stil, axis=1)
        .format({'Net Karlılık': '{:.2%}', 'Tahsilat_Tutari': '{:,.0f}₺'}),
        use_container_width=True
    )

# --- TAB 2: NAKİT AKIŞ ANALİZİ ---
with tab2:
    st.subheader("Tedarikçi ve Vade Denge Analizi")
    t_analiz = df.groupby('Tedarikçi').agg({
        'Borc_Tutari': 'sum',
        'Tahsilat_Tutari': 'sum',
        'Stok_Potansiyel_Ciro': 'sum',
        'Borc_Vade': 'min',
        'Cek_Vade': 'max'
    }).reset_index()
    
    t_analiz['Net_Denge'] = (t_analiz['Tahsilat_Tutari'] + t_analiz['Stok_Potansiyel_Ciro']) - t_analiz['Borc_Tutari']
    t_analiz['Gun_Farki'] = (t_analiz['Borc_Vade'] - t_analiz['Cek_Vade']).dt.days

    def nakit_stil(row):
        if row['Net_D
