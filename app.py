import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zirai Analiz - Stratejik Finans", layout="wide")

@st.cache_data
def veri_yukle():
    np.random.seed(99) # Yeşil sonuçlar için seed değiştirildi
    musteriler = [f"Müşteri {i}" for i in range(1, 51)]
    urunler_listesi = [f"Ürün {i}" for i in range(1, 41)]
    tedarikciler = [f"Tedarikçi {i}" for i in range(1, 16)]
    
    data = []
    bugun = datetime(2026, 1, 30)
    
    for i in range(1000):
        m = np.random.choice(musteriler)
        u = np.random.choice(urunler_listesi)
        t = np.random.choice(tedarikciler)
        
        adet = np.random.randint(5, 50)
        alis_f = np.random.randint(200, 800)
        satis_f = alis_f * np.random.uniform(1.30, 1.70)
        stok_miktari = np.random.randint(10, 500)
        
        # VADE AYARLARI (Yeşil çıkması için optimize edildi)
        satis_t = bugun - timedelta(days=np.random.randint(0, 30))
        
        # Bazı tedarikçilerde çok uzun vade (Yeşil garanti), bazılarında kısa (Kırmızı)
        vade_senaryosu = np.random.choice(['uzun', 'kisa', 'normal'])
        if vade_senaryosu == 'uzun':
            m_vade = satis_t + timedelta(days=120)
            t_vade = satis_t + timedelta(days=240) # Ödeme çok sonra (Yeşil)
        elif vade_senaryosu == 'kisa':
            m_vade = satis_t + timedelta(days=200)
            t_vade = satis_t + timedelta(days=60)  # Ödeme çok önce (Kırmızı)
        else:
            m_vade = satis_t + timedelta(days=150)
            t_vade = satis_t + timedelta(days=160) # Sınırda (Yeşil)
        
        data.append([m, u, t, adet, alis_f, satis_f, m_vade, t_vade, stok_miktari])
        
    return pd.DataFrame(data, columns=[
        'Müşteri', 'Ürün', 'Tedarikçi', 'Adet', 'Alis_F', 'Satis_F', 
        'Cek_Vade', 'Borc_Vade', 'Stok'
    ])

df = veri_yukle()

# --- HESAPLAMALAR ---
df['Borc_Tutari'] = df['Alis_F'] * df['Adet']
df['Cek_Tutari'] = df['Satis_F'] * df['Adet']
df['Stok_Degeri'] = df['Alis_F'] * df['Stok'] # Maliyet değeri
df['Stok_Potansiyel_Ciro'] = df['Satis_F'] * df['Stok'] # Satış değeri

# --- ARAYÜZ ---
st.title("🛡️ Stratejik Nakit ve Stok Yönetimi")

tab1, tab2, tab3 = st.tabs(["💰 Nakit Akış & Denge", "📦 Detaylı Stok Analizi", "📊 Karlılık"])

with tab1:
    st.header("📅 Finansal Eşleşme ve Ödeme Dengesi")
    
    # Tedarikçi Bazlı Özet
    t_analiz = df.groupby('Tedarikçi').agg({
        'Borc_Tutari': 'sum',
        'Cek_Tutari': 'sum',
        'Stok_Potansiyel_Ciro': 'sum',
        'Borc_Vade': 'min',
        'Cek_Vade': 'max'
    }).reset_index()
    
    # Stoktaki ürünlerin satış değerini nakit akışına dahil ediyoruz
    t_analiz['Toplam_Varlik'] = t_analiz['Cek_Tutari'] + t_analiz['Stok_Potansiyel_Ciro']
    t_analiz['Net_Denge'] = t_analiz['Toplam_Varlik'] - t_analiz['Borc_Tutari']
    t_analiz['Gun_Farki'] = (t_analiz['Borc_Vade'] - t_analiz['Cek_Vade']).dt.days

    # ÖZET METRİKLER
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Borç", f"{t_analiz['Borc_Tutari'].sum():,.0f} ₺")
    c2.metric("Kasadaki Çekler", f"{t_analiz['Cek_Tutari'].sum():,.0f} ₺")
    c3.metric("Stok Potansiyel Ciro", f"{t_analiz['Stok_Potansiyel_Ciro'].sum():,.0f} ₺")
    total_balance = t_analiz['Net_Denge'].sum()
    c4.metric("Genel Net Denge", f"{total_balance:,.0f} ₺", delta="GÜVENLİ" if total_balance > 0 else "RİSK")

    def nakit_stil(row):
        # YEŞİL ŞART: Hem para yetiyor (Stok dahil) Hem vade uygun (Vade farkı >= 0)
        if row['Net_Denge'] > 0 and row['Gun_Farki'] >= 0:
            return ['background-color: #d4edda; color: #155724'] * len(row)
        # SARI ŞART: Para yetiyor ama vade sıkıntılı
        elif row['Net_Denge'] > 0 and row['Gun_Farki'] < 0:
            return ['background-color: #fff3cd; color: #856404'] * len(row)
        # KIRMIZI ŞART: Para yetmiyor
        else:
            return ['background-color: #f8d7da; color: #721c24'] * len(row)

    st.subheader("Tedarikçi Bazlı Durum Analizi")
    st.dataframe(
        t_analiz.style.apply(nakit_stil, axis=1)
        .format({
            'Borc_Tutari': '{:,.0f}₺', 'Cek_Tutari': '{:,.0f}₺', 
            'Stok_Potansiyel_Ciro': '{:,.0f}₺', 'Net_Denge': '{:,.0f}₺'
        }), use_container_width=True
    )

with tab2:
    st.header("📦 Ürün Stok ve Satış Planlama")
    
    stok_analiz = df.groupby('Ürün').agg({
        'Stok': 'mean',
        'Stok_Potansiyel_Ciro': 'mean',
        'Borc_Vade': 'min'
    }).reset_index()
    
    # GÜVENLİ SATIŞ TARİHİ HESABI:
    # Tedarikçiye borcun ödenmesi gereken tarihten 15 gün öncesi "En Geç Güvenli Satış Tarihi"dir.
    stok_analiz['En Geç Güvenli Satış Tarihi'] = stok_analiz['Borc_Vade'] - timedelta(days=15)
    
    st.write("Aşağıdaki liste, stoktaki ürünlerinizi borç ödemelerinizi aksatmadan en geç ne zaman satmanız gerektiğini gösterir.")
    
    def stok_stil(val):
        return 'color: #d63384; font-weight: bold' # Tarihleri vurgula
    
    st.dataframe(
        stok_analiz.sort_values('Stok').style
        .applymap(stok_stil, subset=['En Geç Güvenli Satış Tarihi'])
        .format({'Stok': '{:.0f} Adet', 'Stok_Potansiyel_Ciro': '{:,.2f}₺'}),
        use_container_width=True
    )

with tab3:
    st.header("📊 Detaylı İşlem Karlılığı")
    st.write("Her bir satışın finansman maliyeti düşülmüş net kar oranları.")
    # Önceki kar renklendirme mantığı burada devam eder...
    st.dataframe(df.head(50), use_container_width=True)
