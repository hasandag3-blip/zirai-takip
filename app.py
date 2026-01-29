import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Analiz Pro", layout="wide")

# --- VERİ ÜRETME / ÇEKME FONKSİYONU ---
@st.cache_data
def veri_hazirla():
    np.random.seed(42)
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    musteriler[0] = "Mehmet Gök"
    
    urunler = [f"Ürün {i}" for i in range(1, 41)]
    urunler[0] = "Böcek İlacı 100ml"
    
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    tedarikciler[0] = "MsT Firması"

    data = []
    baslangic_tarihi = datetime(2025, 2, 1)

    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler)
        t = np.random.choice(tedarikciler)
        
        alis_f = np.random.randint(100, 1000)
        satis_f = alis_f * np.random.uniform(1.10, 1.60)
        stok = np.random.randint(0, 100)
        
        satis_t = baslangic_tarihi + timedelta(days=np.random.randint(0, 30))
        m_vade = satis_t + timedelta(days=np.random.randint(200, 400))
        t_vade = satis_t + timedelta(days=np.random.randint(30, 150))
        
        # Valör Hesabı
        vade_farki = (m_vade - t_vade).days
        finansman_kaybi = (alis_f * 0.001) * vade_farki 
        net_kar = (satis_f - (alis_f + finansman_kaybi)) / alis_f
        
        data.append([m, u, t, alis_f, satis_f, satis_t, m_vade, t_vade, stok, net_kar])

    return pd.DataFrame(data, columns=[
        'Müşteri', 'Ürün', 'Tedarikçi', 'Alış Fiyatı', 'Satış Fiyatı', 
        'Satış Tarihi', 'Müşteri Çek Vadesi', 'Tedarikçi Vade', 'Stok', 'Net Kar Oranı'
    ])

df = veri_hazirla()

# --- ARAYÜZ ---
st.title("🚜 Zirai İlaç Ticari Analiz Paneli")

# Bölüm 1: Stok ve Özet
st.header("📦 Stok ve Finansal Durum")
c1, c2, c3 = st.columns(3)

azalanlar = df[df['Stok'] < 10][['Ürün', 'Stok']].drop_duplicates()

with c1:
    st.metric("Kritik Stoktaki Ürün Sayısı", len(azalanlar))
    if st.checkbox("Azalan Ürünleri Listele"):
        st.warning("Stok Seviyesi 10'un Altında Olanlar:")
        st.write(azalanlar)

with c2:
    toplam_tahsilat = df['Satış Fiyatı'].sum()
    st.metric("Toplam Beklenen Tahsilat", f"{toplam_tahsilat:,.2f} ₺")

with c3:
    st.info("💡 Valör hesabı günlük %0.1 finansman maliyeti ile hesaplanmaktadır.")

st.divider()

# Bölüm 2: Filtreleme
st.header("🔍 Müşteri ve Ürün Sorgulama")
arama = st.text_input("Aramak istediğiniz isim veya ürün (Örn: Mehmet Gök)", "")
f_df = df[df['Müşteri'].str.contains(arama, case=False) | df['Ürün'].str.contains(arama, case=False)]

# Bölüm 3: Renkli Tablo
def renk_kodla(val):
    if val >= 0.25: color = 'background-color: #28a745; color: white'
    elif 0.12 <= val < 0.25: color = 'background-color: #ffc107; color: black'
    else: color = 'background-color: #dc3545; color: white'
    return color

st.subheader("📊 Karlılık Analiz Tablosu")
st.dataframe(
    f_df.style.applymap(renk_kodla, subset=['Net Kar Oranı'])
    .format({'Net Kar Oranı': '{:.2%}', 'Alış Fiyatı': '{:.2f}₺', 'Satış Fiyatı': '{:.2f}₺'}),
    use_container_width=True
)

# Bölüm 4: Yan Menü
st.sidebar.header("⚙️ Veri Yönetimi")
if st.sidebar.button("💾 Verileri Yenile"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("Bu panel, müşteri vadesi ile tedarikçi vadesi arasındaki farkı karlılıktan düşerek **gerçek karınızı** gösterir.")
