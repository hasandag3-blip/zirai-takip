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
    urunler_listesi = [f"Ürün {i}" for i in range(1, 41)]
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    
    data = []
    baslangic = datetime(2025, 2, 1)
    
    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler_listesi)
        t = np.random.choice(tedarikciler)
        
        # Rastgele veriler
        adet = np.random.randint(1, 100)
        alis_f = np.random.randint(200, 800)
        satis_f = alis_f * np.random.uniform(1.20, 1.50)
        stok = np.random.randint(5, 150)
        
        # VADE SİMÜLASYONU (Yeşil ve Kırmızı oluşması için ayarlandı)
        satis_t = baslangic + timedelta(days=np.random.randint(0, 30))
        
        # Müşteri çekleri genelde 200-300 gün vadeli olsun
        m_vade = satis_t + timedelta(days=np.random.randint(150, 300))
        
        # Tedarikçi ödemesi: %50 ihtimalle çekten önce (Kırmızı), %50 ihtimalle çekten sonra (Yeşil)
        if np.random.rand() > 0.5:
            # GÜVENLİ (Yeşil): Ödeme tahsilattan sonra
            t_vade = m_vade + timedelta(days=np.random.randint(10, 60))
        else:
            # RİSKLİ (Kırmızı): Ödeme tahsilattan önce
            t_vade = m_vade - timedelta(days=np.random.randint(10, 60))
        
        # Valörlü Kar Analizi
        vade_gun_farki = (m_vade - t_vade).days
        finans_maliyeti = (alis_f * 0.001) * vade_gun_farki
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

# --- TAB 1: NAKİT AKIŞ ANALİZİ ---
with tab1:
    st.header("📅 Tedarikçi Ödeme ve Çek Eşleşme Analizi")
    
    # Tedarikçi bazında özet
    t_analiz = df.groupby('Tedarikçi').agg({
        'Borç Tutarı': 'sum',
        'Çek Tutarı': 'sum',
        'Tedarikçi Ödeme Vadesi': 'min', # En yakın ödeme tarihimiz
        'Çek Vadesi': 'max'              # Kasadaki en son çek vadesi
    }).reset_index()
    
    # Analiz Sütunları
    t_analiz['Kasa Dengesi'] = t_analiz['Çek Tutarı'] - t_analiz['Borç Tutarı']
    t_analiz['Vade Farkı (Gün)'] = (t_analiz['Tedarikçi Ödeme Vadesi'] - t_analiz['Çek Vadesi']).dt.days

    def nakit_akisi_renkle(row):
        # KRİTER 1: Kasa borcu karşılamıyorsa (Tutar yetersiz)
        # KRİTER 2: Ödeme tarihi (min), tahsilat tarihinden (max) önceyse (Vade yetersiz)
        if row['Kasa Dengesi'] < 0 or row['Vade Farkı (Gün)'] < 0:
            return ['background-color: #f8d7da; color: #721c24'] * len(row) # Kırmızı
        else:
            return ['background-color: #d4edda; color: #155724'] * len(row) # Yeşil

    st.info("💡 **Analiz Mantığı:** Eğer tahsilatlarınızın (çekler) vadesi, borç ödeme tarihinizden sonraya kalıyorsa veya tutar yetersizse satır **Kırmızı** olur. Ödeme rahatsa **Yeşil** olur.")
    
    st.dataframe(
        t_analiz.style.apply(nakit_akisi_renkle, axis=1)
        .format({
            'Borç Tutarı': '{:,.2f}₺', 
            'Çek Tutarı': '{:,.2f}₺', 
            'Kasa Dengesi': '{:,.2f}₺'
        }),
        use_container_width=True
    )

# --- TAB 2: STOK YÖNETİMİ ---
with tab2:
    st.header("🚜 Ürün Stok Durumu")
    stok_df = df[['Ürün', 'Mevcut Stok']].drop_duplicates('Ürün').sort_values(by='Mevcut Stok')
    
    k_limit = 30
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Kritik Ürün Sayısı", len(stok_df[stok_df['Mevcut Stok'] < k_limit]))
        st.dataframe(stok_df[stok_df['Mevcut Stok'] < k_limit], use_container_width=True)
    with col2:
        st.bar_chart(stok_df.set_index('Ürün')['Mevcut Stok'])

# --- TAB 3: KARLILIK ---
with tab3:
    st.header("📊 Müşteri ve Ürün Karlılık Detayları")
    def kar_renkle(val):
        if val >= 0.25: return 'background-color: #28a745; color: white'
        elif 0.12 <= val < 0.25: return 'background-color: #ffc107'
        else: return 'background-color: #dc3545; color: white'

    st.dataframe(
        df.head(100).style.applymap(kar_renkle, subset=['Net Kar Oranı'])
        .format({'Net Kar Oranı': '{:.2%}', 'Borç Tutarı': '{:,.2f}₺', 'Çek Tutarı': '{:,.2f}₺'}),
        use_container_width=True
    )
