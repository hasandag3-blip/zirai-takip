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
        
        # Karlılık senaryoları
        kar_sans = np.random.rand()
        if kar_sans > 0.7: satis_f = alis_f * np.random.uniform(1.40, 1.60)
        elif kar_sans > 0.4: satis_f = alis_f * np.random.uniform(1.20, 1.30)
        else: satis_f = alis_f * np.random.uniform(1.05, 1.15)
        
        stok = np.random.randint(10, 500)
        satis_t = bugun - timedelta(days=np.random.randint(0, 30))
        
        v_senaryo = np.random.choice(['uzun', 'kisa', 'normal'])
        if v_senaryo == 'uzun':
            m_vade, t_vade = satis_t + timedelta(days=120), satis_t + timedelta(days=240)
        elif v_senaryo == 'kisa':
            m_vade, t_vade = satis_t + timedelta(days=200), satis_t + timedelta(days=60)
        else:
            m_vade, t_vade = satis_t + timedelta(days=150), satis_t + timedelta(days=160)
        
        data.append([m, u, t, adet, alis_f, satis_f, m_vade, t_vade, stok])
        
    df = pd.DataFrame(data, columns=['Müşteri', 'Ürün', 'Tedarikçi', 'Adet', 'Alis_F', 'Satis_F', 'Cek_Vade', 'Borc_Vade', 'Stok'])
    df['Borc_Tutari'] = df['Alis_F'] * df['Adet']
    df['Tahsilat_Tutari'] = df['Satis_F'] * df['Adet']
    df['Stok_Potansiyel_Ciro'] = df['Satis_F'] * df['Stok']
    
    v_farki = (df['Cek_Vade'] - df['Borc_Vade']).dt.days
    df['Net_Kar_Orani'] = ((df['Satis_F'] - df['Alis_F']) - (df['Alis_F'] * 0.001 * v_farki)) / df['Alis_F']
    
    return df

df = veri_yukle_stratejik()

# --- 3. ÜST PANEL (METRİKLER) ---
st.title("🛡️ Zirai Finans ve Müşteri Karlılık Yönetimi")

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
m5.metric("Genel Ortalama Net Kar", f"{genel_net_kar:.2%}")

st.divider()

# --- 4. ANA SEKMELER ---
tab1, tab2, tab3 = st.tabs(["👥 Müşteri Net Karlılık", "💰 Nakit Akış & Denge", "📦 Stok Takvimi"])

# --- TAB 1: MÜŞTERİ NET KARLILIK ---
with tab1:
    st.subheader("Müşteri Bazlı Konsolide Net Karlılık Raporu")
    m_ozet = df.groupby('Müşteri').agg({'Tahsilat_Tutari': 'sum', 'Net_Kar_Orani': 'mean'}).reset_index()
    m_ozet = m_ozet.rename(columns={'Net_Kar_Orani': 'Net Karlılık'})

    def musteri_stil(row):
        val = row['Net Karlılık']
        color = '#d4edda' if val >= 0.25 else '#fff3cd' if val >= 0.12 else '#f8d7da'
        return [f'background-color: {color}'] * len(row)

    st.dataframe(m_ozet.sort_values('Net Karlılık', ascending=False).style.apply(musteri_stil, axis=1).format({'Net Karlılık': '{:.2%}', 'Tahsilat_Tutari': '{:,.0f}₺'}), use_container_width=True)

# --- TAB 2: NAKİT AKIŞ ANALİZİ ---
with tab2:
    st.subheader("Tedarikçi ve Vade Denge Analizi")
    t_analiz = df.groupby('Tedarikçi').agg({'Borc_Tutari': 'sum', 'Tahsilat_Tutari': 'sum', 'Stok_Potansiyel_Ciro': 'sum', 'Borc_Vade': 'min', 'Cek_Vade': 'max'}).reset_index()
    t_analiz['Net_Denge'] = (t_analiz['Tahsilat_Tutari'] + t_analiz['Stok_Potansiyel_Ciro']) - t_analiz['Borc_Tutari']
    t_analiz['Gun_Farki'] = (t_analiz['Borc_Vade'] - t_analiz['Cek_Vade']).dt.days

    def nakit_stil(row):
        color = '#d1fae5' if (row['Net_Denge'] > 0 and row['Gun_Farki'] >= 0) else '#fef3c7' if row['Net_Denge'] > 0 else '#fee2e2'
        return [f'background-color: {color}'] * len(row)

    st.dataframe(t_analiz.style.apply(nakit_stil, axis=1).format({'Borc_Tutari': '{:,.0f}₺', 'Tahsilat_Tutari': '{:,.0f}₺', 'Net_Denge': '{:,.0f}₺'}), use_container_width=True)

# --- TAB 3: STOK TAKVİMİ ---
with tab3:
    st.subheader("Güvenli Stok ve Satış Planı")
    stok_analiz = df.groupby('Ürün').agg({'Stok': 'mean', 'Stok_Potansiyel_Ciro': 'sum', 'Borc_Vade': 'min'}).reset_index()
    stok_analiz['En Geç Güvenli Satış'] = stok_analiz['Borc_Vade'] - timedelta(days=15)
    
    # Tarihleri stringe çevirerek hata riskini sıfırlıyoruz
    stok_analiz['En Geç Güvenli Satış'] = stok_analiz['En Geç Güvenli Satış'].dt.strftime('%d.%m.%Y')
    
    st.dataframe(
        stok_analiz.sort_values('Stok').style.format({
            'Stok': '{:.0f}',
            'Stok_Potansiyel_Ciro': '{:,.0f}₺'
        }), 
        use_container_width=True
    )

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Yönetim")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()
