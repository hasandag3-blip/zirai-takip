Python 3.14.2 (tags/v3.14.2:df79316, Dec  5 2025, 17:18:21) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Analiz Pro", layout="wide")

# --- CSS İLE RENKLENDİRME ---
st.markdown("""
    <style>
    .green-zone { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    .yellow-zone { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
    .red-zone { background-color: #f8d7da; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ ÜRETME / ÇEKME FONKSİYONU ---
@st.cache_data
def veri_hazirla():
    # 50 Müşteri, 40 Ürün, 15 Tedarikçi bazlı 1000 satırlık veri
    np.random.seed(42)
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    # Özel örnek ekleme
    musteriler[0] = "Mehmet Gök"
    
    urunler = [f"Ürün {i}" for i in range(1, 41)]
    urunler[0] = "Böcek İlacı 100ml"
    
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    tedarikciler[0] = "MsT Firması"

    data = []
    baslangic_tarihi = datetime(2025, 1, 1)

    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler)
        t = np.random.choice(tedarikciler)
        
        alis_f = np.random.randint(100, 1000)
        satis_f = alis_f * np.random.uniform(1.10, 1.60)
        stok = np.random.randint(0, 100)
        
        # Tarih ve Vade Simülasyonu
        satis_tarihi = baslangic_tarihi + timedelta(days=np.random.randint(0, 60))
        # Örnekteki gibi uzak vadeli çekler
        musteri_vade = satis_tarihi + timedelta(days=np.random.randint(200, 400))
        tedarikci_vade = satis_tarihi + timedelta(days=np.random.randint(30, 200))
        
        # VALÖR HESABI: Finansman Maliyeti (Günlük %0.15 varsayımı)
        vade_gun_farki = (musteri_vade - tedarikci_vade).days
        finansman_yukü = (alis_f * 0.0015) * vade_gun_farki
        net_kar_orani = (satis_f - (alis_f + finansman_yukü)) / alis_f
        
        data.append([m, u, t, alis_f, satis_f, satis_tarihi, musteri_vade, tedarikci_vade, stok, net_kar_orani])

    return pd.DataFrame(data, columns=[
        'Müşteri', 'Ürün', 'Tedarikçi', 'Alış Fiyatı', 'Satış Fiyatı', 
        'Satış Tarihi', 'Müşteri Çek Vadesi', 'Tedarikçi Vade', 'Stok', 'Net Kar Oranı'
    ])

df = veri_hazirla()

# --- ARAYÜZ ---
st.title("🚜 Zirai İlaç Karlılık ve Vade Analiz Sistemi")

# Bölüm 1: Özet Göstergeler ve Stok Uyarıları
st.header("📦 Stok ve Finansal Durum")
col1, col2, col3 = st.columns(3)

azalan_urunler = df[df['Stok'] < 10][['Ürün', 'Stok']].drop_duplicates()
with col1:
    st.error(f"⚠️ Kritik Stokta {len(azalan_urunler)} Ürün Var")
    if st.checkbox("Kritik Stok Listesini Göster"):
        st.write(azalan_urunler)

... with col2:
...     toplam_alacak = df['Satış Fiyatı'].sum()
...     st.metric("Beklenen Toplam Tahsilat", f"{toplam_alacak:,.2f} ₺")
... 
... with col3:
...     st.info("Valör Etkisi: Hesaplamaya Dahil")
... 
... st.divider()
... 
... # Bölüm 2: Filtreleme ve Arama
... st.header("🔍 Detaylı Analiz ve Arama")
... arama = st.text_input("Müşteri Adı veya Ürün Yazın (Örn: Mehmet Gök)", "")
... filtered_df = df[df['Müşteri'].str.contains(arama, case=False) | df['Ürün'].str.contains(arama, case=False)]
... 
... # Bölüm 3: Renkli Tablo Fonksiyonu
... def renk_atama(val):
...     if val >= 0.25: color = 'background-color: #28a745; color: white'
...     elif 0.12 <= val < 0.25: color = 'background-color: #ffc107; color: black'
...     else: color = 'background-color: #dc3545; color: white'
...     return color
... 
... st.subheader("📊 Karlılık Gruplandırması")
... st.caption("Yeşil: >%25 Kar | Sarı: %12-%25 Kar | Kırmızı: <%12 Kar (Vade Farkı Düşülmüş)")
... 
... st.dataframe(
...     filtered_df.style.applymap(renk_atama, subset=['Net Kar Oranı'])
...     .format({'Net Kar Oranı': '{:.2%}', 'Alış Fiyatı': '{:.2f}₺', 'Satış Fiyatı': '{:.2f}₺'}),
...     use_container_width=True
... )
... 
... # Bölüm 4: Veri Aktarımı Paneli
... st.sidebar.header("🔗 Dış Veri Bağlantısı")
... veri_kaynagi = st.sidebar.file_uploader("Diğer Programdan Çıktı Alınan Dosyayı (Excel/CSV) Yükleyin", type=['xlsx', 'csv'])
... 
... if veri_kaynagi:
