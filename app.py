import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Analiz - Finans & Stok", layout="wide")

@st.cache_data
def veri_yukle():
    np.random.seed(42)
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    musteriler[0] = "Mehmet Gök"
    urunler_listesi = [f"Ürün {i}" for i in range(1, 41)]
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    
    data = []
    baslangic = datetime(2025, 2, 1)
    
    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler_listesi)
        t = np.random.choice(tedarikciler)
        adet = np.random.randint(1, 150)
        alis_f = np.random.randint(100, 1000)
        satis_f = alis_f * np.random.uniform(1.15, 1.50)
        stok = np.random.randint(0, 200)
        
        satis_t = baslangic + timedelta(days=np.random.randint(0, 30))
        m_vade = satis_t + timedelta(days=np.random.randint(180, 360)) # Müşteri Çeki
        t_vade = satis_t + timedelta(days=np.random.randint(60, 240))  # Tedarikçi Borcu
        
        # Kar Analizi (Valörlü)
        vade_farki = (m_vade - t_vade).days
        finans_maliyeti = (alis_f * 0.001) * vade_farki
        net_kar = (satis_f - (alis_f + finans_maliyeti)) / alis_f
        
        data.append([m, u, t, adet, alis_f * adet, satis_f * adet, m_vade, t_vade, net_kar, stok])
        
    return pd.DataFrame(data, columns=[
        'Müşteri', 'Ürün', 'Tedarikçi', 'Adet', 'Borç Tutarı', 'Çek Tutarı', 
        'Çek Vadesi', 'Tedarikçi Ödeme Vadesi', 'Net Kar Oranı', 'Mevcut Stok'
    ])

df = veri_yukle()

# --- ARAYÜZ ---
st.title("🛡️ Finansal Risk ve Stok Takip Paneli")

tab1, tab2, tab3 = st.tabs(["💰 Nakit Akış Analizi", "📦 Stok Yönetimi", "👥 Müşteri/Ürün Karlılık"])

# --- TAB 1: NAKİT AKIŞ ANALİZİ (Müşteri Çeki vs Tedarikçi Ödemesi) ---
with tab1:
    st.header("📅 Tedarikçi Ödeme ve Çek Eşleşme Analizi")
    
    # Tedarikçi bazında gruplama
    tedarikci_analiz = df.groupby('Tedarikçi').agg({
        'Borç Tutarı': 'sum',
        'Çek Tutarı': 'sum',
        'Tedarikçi Ödeme Vadesi': 'min', # En yakın ödeme
        'Çek Vadesi': 'max'              # En son tahsilat
    }).reset_index()
    
    # Risk Hesaplama: Çekler borcu karşılıyor mu? Ve Vade uygun mu?
    tedarikci_analiz['Finansal Durum'] = tedarikci_analiz['Çek Tutarı'] - tedarikci_analiz['Borç Tutarı']
    tedarikci_analiz['Vade Riski (Gün)'] = (tedarikci_analiz['Tedarikçi Ödeme Vadesi'] - tedarikci_analiz['Çek Vadesi']).dt.days

    def nakit_akisi_renkle(row):
        # Kırmızı: Çek tutarı borçtan azsa VEYA çekin vadesi ödeme tarihinden sonraysa
        if row['Finansal Durum'] < 0 or row['Vade Riski (Gün)'] < 0:
            return ['background-color: #f8d7da'] * len(row)
        return ['background-color: #d4edda'] * len(row)

    st.subheader("Tedarikçi Borç/Kasa Çeki Dengesi")
    st.write("🔴 Kırmızı: Ödeme günü tahsilattan önce veya tutar yetersiz. | 🟢 Yeşil: Ödeme güvenli tarafta.")
    
    st.dataframe(
        tedarikci_analiz.style.apply(nakit_akisi_renkle, axis=1)
        .format({'Borç Tutarı': '{:,.2f}₺', 'Çek Tutarı': '{:,.2f}₺', 'Finansal Durum': '{:,.2f}₺'}),
        use_container_width=True
    )

# --- TAB 2: STOK YÖNETİMİ ---
with tab2:
    st.header("🚜 Ürün Stok Durumu")
    
    stok_df = df[['Ürün', 'Mevcut Stok']].drop_duplicates('Ürün').sort_values(by='Mevcut Stok')
    
    # Kritik stok uyarısı
    kritik_limit = 20
    stok_df['Durum'] = stok_df['Mevcut Stok'].apply(lambda x: '⚠️ KRİTİK' if x < kritik_limit else '✅ YETERLİ')
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Kritik Stoktaki Ürün", len(stok_df[stok_df['Mevcut Stok'] < kritik_limit]))
        st.write("Stok seviyesi 20 adetin altına düşen ürünler:")
        st.dataframe(stok_df[stok_df['Mevcut Stok'] < kritik_limit], use_container_width=True)
    
    with col2:
        st.bar_chart(stok_df.set_index('Ürün')['Mevcut Stok'])

# --- TAB 3: KARLILIK ---
with tab3:
    st.header("📊 Müşteri ve Ürün Karlılık Detayları")
    arama = st.text_input("Müşteri veya Ürün Sorgula...")
    f_df = df[df['Müşteri'].str.contains(arama, case=False) | df['Ürün'].str.contains(arama, case=False)]
    
    def kar_renkle(val):
        if val >= 0.25: return 'background-color: #28a745; color: white'
        elif 0.12 <= val < 0.25: return 'background-color: #ffc107'
        else: return 'background-color: #dc3545; color: white'

    st.dataframe(
        f_df.style.applymap(kar_renkle, subset=['Net Kar Oranı'])
        .format({'Net Kar Oranı': '{:.2%}', 'Borç Tutarı': '{:,.2f}₺', 'Çek Tutarı': '{:,.2f}₺'}),
        use_container_width=True
    )

# --- SİDEBAR ---
st.sidebar.info(f"**Güncelleme Tarihi:**\n{datetime.now().strftime('%d.%m.%Y %H:%M')}")
if st.sidebar.button("Excel Raporu Al (Simüle)"):
    st.sidebar.success("Rapor Hazırlanıyor...")
