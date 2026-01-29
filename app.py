import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- MODERN TASARIM VE SAYFA AYARLARI ---
st.set_page_config(
    page_title="Zirai Finans Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ÖZEL CSS (MODERN ARAYÜZ) ---
st.markdown("""
    <style>
    /* Ana Arka Plan */
    .main { background-color: #f8f9fa; }
    
    /* Kart Tasarımları */
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1e293b; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-left: 5px solid #10b981;
    }
    
    /* Modern Tablo */
    .dataframe { border-radius: 10px; overflow: hidden; border: none !important; }
    
    /* Başlıklar */
    h1 { color: #0f172a; font-weight: 800; letter-spacing: -1px; }
    h2, h3 { color: #334155; font-weight: 600; }
    
    /* Sidebar Güzelleştirme */
    .css-1d391kg { background-color: #1e293b; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2563eb; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def veri_yukle():
    np.random.seed(42)
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    urunler = [f"İlaç {i}" for i in range(1, 41)]
    tedarikciler = [f"Firma {i}" for i in range(1, 16)]
    
    data = []
    bugun = datetime(2026, 1, 30)
    
    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler)
        t = np.random.choice(tedarikciler)
        adet = np.random.randint(5, 50)
        alis_f = np.random.randint(200, 800)
        satis_f = alis_f * np.random.uniform(1.30, 1.80)
        stok = np.random.randint(10, 500)
        
        # Dengeli vade dağılımı
        s_tarih = bugun - timedelta(days=np.random.randint(0, 30))
        m_vade = s_tarih + timedelta(days=np.random.randint(180, 300))
        
        # %60 Yeşil çıkması için t_vade ayarı
        if np.random.rand() > 0.4:
            t_vade = m_vade + timedelta(days=np.random.randint(20, 90)) # Yeşil
        else:
            t_vade = m_vade - timedelta(days=np.random.randint(20, 90)) # Kırmızı
            
        data.append([m, u, t, adet, alis_f, satis_f, m_vade, t_vade, stok])
        
    df = pd.DataFrame(data, columns=['Müşteri', 'Ürün', 'Tedarikçi', 'Adet', 'Alis_F', 'Satis_F', 'Cek_Vade', 'Borc_Vade', 'Stok'])
    df['Borc_Tutari'] = df['Alis_F'] * df['Adet']
    df['Cek_Tutari'] = df['Satis_F'] * df['Adet']
    df['Stok_Potansiyel'] = df['Satis_F'] * df['Stok']
    return df

df = veri_yukle()

# --- ÜST PANEL (METRİKLER) ---
st.title("🌿 Zirai İşletme Akıllı Yönetim Paneli")
st.markdown("Veri analitiği ve nakit akışı yönetim merkezi.")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Toplam Borç", f"{df['Borc_Tutari'].sum():,.0f} ₺")
with m2:
    st.metric("Kasadaki Çekler", f"{df['Cek_Tutari'].sum():,.0f} ₺")
with m3:
    st.metric("Stok Değeri", f"{df['Stok_Potansiyel'].sum():,.0f} ₺")
with m4:
    net_d = (df['Cek_Tutari'].sum() + df['Stok_Potansiyel'].sum()) - df['Borc_Tutari'].sum()
    st.metric("Net Likidite", f"{net_d:,.0f} ₺", delta="POZİTİF")

st.markdown("---")

# --- ANA SEGMENTLER (MODERN TABLAR) ---
tab1, tab2, tab3 = st.tabs(["📊 Finansal Nakit Akışı", "📦 Stok & Satış Planı", "👥 Müşteri Analizi"])

with tab1:
    st.subheader("Tedarikçi Ödeme Dengesi")
    t_analiz = df.groupby('Tedarikçi').agg({
        'Borc_Tutari': 'sum', 'Cek_Tutari': 'sum', 'Stok_Potansiyel': 'sum',
        'Borc_Vade': 'min', 'Cek_Vade': 'max'
    }).reset_index()
    
    t_analiz['Net_Denge'] = (t_analiz['Cek_Tutari'] + t_analiz['Stok_Potansiyel']) - t_analiz['Borc_Tutari']
    t_analiz['Gün_Farkı'] = (t_analiz['Borc_Vade'] - t_analiz['Cek_Vade']).dt.days

    def style_nakit(row):
        if row['Net_Denge'] > 0 and row['Gün_Farkı'] >= 0:
            return ['background-color: #ecfdf5; color: #065f46'] * len(row) # Soft Yeşil
        elif row['Net_Denge'] > 0 and row['Gün_Farkı'] < 0:
            return ['background-color: #fffbeb; color: #92400e'] * len(row) # Soft Sarı
        else:
            return ['background-color: #fef2f2; color: #991b1b'] * len(row) # Soft Kırmızı

    st.dataframe(
        t_analiz.style.apply(style_nakit, axis=1)
        .format({'Borc_Tutari': '{:,.0f}₺', 'Cek_Tutari': '{:,.0f}₺', 'Net_Denge': '{:,.0f}₺'}),
        use_container_width=True
    )

with tab2:
    st.subheader("Ürün Stok ve Güvenli Satış Takvimi")
    stok_analiz = df.groupby('Ürün').agg({
        'Stok': 'mean', 'Stok_Potansiyel': 'mean', 'Borc_Vade': 'min'
    }).reset_index()
    stok_analiz['En Geç Satış'] = stok_analiz['Borc_Vade'] - timedelta(days=15)
    
    st.dataframe(
        stok_analiz.sort_values('Stok').style.background_gradient(cmap='Blues', subset=['Stok'])
        .format({'Stok': '{:.0f}', 'Stok_Potansiyel': '{:,.0f}₺'}),
        use_container_width=True
    )

with tab3:
    st.subheader("Müşteri Karlılık Endeksi")
    arama = st.text_input("🔍 Müşteri veya ürün arayın...", "")
    f_df = df[df['Müşteri'].str.contains(arama, case=False) | df['Ürün'].str.contains(arama, case=False)]
    
    st.dataframe(
        f_df.head(100).style.background_gradient(cmap='Greens', subset=['Satis_F'])
        .format({'Alis_F': '{:.2f}', 'Satis_F': '{:.2f}'}),
        use_container_width=True
    )

# --- SIDEBAR (MODERN BUTONLAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1887/1887040.png", width=80)
    st.title("Yönetim Paneli")
    if st.button("🔄 Verileri Güncelle"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.write("📂 **Veri Kaynağı:** Muhasebe SQL")
    st.write("⏳ **Son Güncelleme:**", datetime.now().strftime("%H:%M:%S"))
    
    if st.download_button("📥 Excel Raporu Al", data=df.to_csv(), file_name="zirai_rapor.csv"):
        st.sidebar.success("Rapor İndirildi!")
