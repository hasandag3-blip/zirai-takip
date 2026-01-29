import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Analiz Pro - Müşteri Bazlı", layout="wide")

@st.cache_data
def veri_hazirla():
    np.random.seed(42)
    # 50 Müşteri ve 40 Ürün havuzu
    musteri_listesi = [f"Müşteri {i}" for i in range(1, 51)]
    musteri_listesi[0] = "Mehmet Gök" # Örnek müşteri
    
    urunler = [f"Ürün {i}" for i in range(1, 41)]
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]

    raw_data = []
    baslangic_tarihi = datetime(2025, 2, 1)

    # 1000 adet satış kaydı oluşturuyoruz (Aynı müşteri birçok kez geçecek)
    for i in range(1000):
        m = np.random.choice(musteri_listesi)
        u = np.random.choice(urunler)
        t = np.random.choice(tedarikciler)
        
        adet = np.random.randint(1, 200)
        alis_f = np.random.randint(100, 1000)
        satis_f = alis_f * np.random.uniform(1.10, 1.60)
        
        satis_t = baslangic_tarihi + timedelta(days=np.random.randint(0, 30))
        m_vade = satis_t + timedelta(days=np.random.randint(200, 400))
        t_vade = satis_t + timedelta(days=np.random.randint(30, 150))
        
        vade_farki = (m_vade - t_vade).days
        finansman_kaybi = (alis_f * 0.001) * vade_farki 
        net_kar_orani = (satis_f - (alis_f + finansman_kaybi)) / alis_f
        
        raw_data.append([m, u, t, adet, alis_f * adet, satis_f * adet, m_vade, t_vade, net_kar_orani])

    df_raw = pd.DataFrame(raw_data, columns=[
        'Müşteri', 'Ürün', 'Tedarikçi', 'Toplam Adet', 'Toplam Maliyet', 
        'Toplam Satış', 'Son Müşteri Vadesi', 'Son Tedarikçi Vadesi', 'Ortalama Kar Oranı'
    ])
    
    # --- MÜŞTERİ BAZLI BİRLEŞTİRME (GROUPBY) ---
    musteri_ozet = df_raw.groupby('Müşteri').agg({
        'Ürün': lambda x: ', '.join(x.unique()[:3]) + "...", # Aldığı ilk 3 farklı ürün
        'Toplam Adet': 'sum',
        'Toplam Maliyet': 'sum',
        'Toplam Satış': 'sum',
        'Son Müşteri Vadesi': 'max',   # En uzak ödeme tarihi
        'Son Tedarikçi Vadesi': 'max', # En uzak borç tarihi
        'Ortalama Kar Oranı': 'mean'   # Tüm satışlarının kar ortalaması
    }).reset_index()

    return musteri_ozet

df = veri_hazirla()

# --- ARAYÜZ ---
st.title("👥 Müşteri Bazlı Konsolide Analiz")
st.markdown("Aynı isimli müşterilerin tüm alımları birleştirilmiş ve valör farkları hesaplanmıştır.")

# Bölüm 1: Metrikler
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Toplam Kayıtlı Müşteri", len(df))
with c2:
    st.metric("Genel Ciro", f"{df['Toplam Satış'].sum():,.2f} ₺")
with c3:
    ortalama_kar = df['Ortalama Kar Oranı'].mean()
    st.metric("Portföy Kar Ortalaması", f"{ortalama_kar:.2%}")

st.divider()

# Bölüm 2: Filtreleme
arama = st.text_input("Müşteri Adı Ara...", "")
f_df = df[df['Müşteri'].str.contains(arama, case=False)]

# Bölüm 3: Renklendirme ve Tablo
def renk_kodla(val):
    if val >= 0.25: color = 'background-color: #28a745; color: white'
    elif 0.12 <= val < 0.25: color = 'background-color: #ffc107; color: black'
    else: color = 'background-color: #dc3545; color: white'
    return color

st.subheader("📋 Müşteri Karlılık Tablosu (Birleştirilmiş)")
st.dataframe(
    f_df.style.applymap(renk_kodla, subset=['Ortalama Kar Oranı'])
    .format({
        'Ortalama Kar Oranı': '{:.2%}', 
        'Toplam Maliyet': '{:.2f}₺', 
        'Toplam Satış': '{:.2f}₺'
    }),
    use_container_width=True
)

# Bölüm 4: Uyarı Paneli
st.sidebar.header("📊 Analiz Detayı")
st.sidebar.info("""
**Nasıl Hesaplandı?**
1. Müşterinin tüm alımları toplandı.
2. Her satış için kendi vadesine göre finansman yükü düşüldü.
3. Çıkan 'Net Kar' oranlarının ortalaması alındı.
""")
