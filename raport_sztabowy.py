import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import plotly.express as px
import os

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024"

st.set_page_config(page_title="Warta Poznań - Sztab", page_icon="📋", layout="wide")

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    html, body, [class*="st-"], .stMarkdown, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}

    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        text-transform: uppercase;
        text-align: center;
        margin-bottom: 5px;
    }}
    
    .metric-box {{
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid {COLOR_PRIMARY};
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }}
    
    .metric-box h3 {{ font-size: 0.9rem; margin-bottom: 5px; }}
    .metric-box h2 {{ font-size: 1.8rem; margin: 0; color: {COLOR_PRIMARY}; }}
    </style>
    """, unsafe_allow_html=True)

# --- SYSTEM LOGOWANIA ---
if "auth_staff" not in st.session_state:
    st.session_state["auth_staff"] = False

def login():
    if not st.session_state["auth_staff"]:
        st.markdown("<h1>🔐 LOGOWANIE SZTABU</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            haslo = st.text_input("Podaj hasło sztabowe:", type="password")
            if st.button("Zaloguj"):
                if haslo == PASSWORD_TRENER:
                    st.session_state["auth_staff"] = True
                    st.rerun()
                else:
                    st.error("Błędne hasło!")
        st.stop()

login()

# --- ŁADOWANIE DANYCH ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def load_data():
    try:
        data = conn.read(worksheet="Arkusz1", ttl=0)
        return data
    except Exception:
        return pd.DataFrame()

# --- HEADER Z LOGO ---
def get_logo():
    if os.path.exists("herb.png"): return "herb.png"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

col_l1, col_l2, col_l3 = st.columns([1, 0.5, 1])
with col_l2:
    st.image(get_logo(), use_container_width=True)

st.markdown("<h1>📊 PERFORMANCE & STAFF ANALYTICS</h1>", unsafe_allow_html=True)

df_raw = load_data()

if df_raw.empty or len(df_raw.columns) < 3:
    st.error("⚠️ BRAK DANYCH LUB BŁĘDNA STRUKTURA ARKUSZA")
    st.stop()

# Przetwarzanie danych
df = df_raw.copy()
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
df = df.dropna(subset=['Data'])
df['Dzień'] = df['Data'].dt.date

with st.sidebar:
    st.header("⚙️ FILTRY")
    widok = st.radio("WIDOK:", ["Dzienny Raport Readiness", "Trendy Zawodników", "Surowe Dane"])
    wybrana_data = st.date_input("Wybierz datę:", value=datetime.now(PL_TZ).date())
    if st.button("🔄 Odśwież Dane"):
        st.cache_data.clear()
        st.rerun()

# --- WIDOK 1: DZIENNY RAPORT READINESS (PRZYWRÓCONY) ---
if widok == "Dzienny Raport Readiness":
    st.subheader(f"📅 RAPORT GOTOWOŚCI: {wybrana_data}")
    
    # Filtrowanie Wellness z danego dnia
    df_well = df[(df['Typ_Raportu'] == 'Wellness') & (df['Dzień'] == wybrana_data)]
    
    if df_well.empty:
        st.info("Brak raportów Wellness na wybrany dzień.")
    else:
        # 1. Metryki na górze (Średnie drużyny)
        m_sen = df_well['Sen'].mean()
        m_zmeczenie = df_well['Zmeczenie'].mean()
        m_bolesnosc = df_well['Bolesnosc'].mean()
        m_stres = df_well['Stres'].mean()
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f'<div class="metric-box"><h3>ŚR. SEN</h3><h2>{m_sen:.1f}</h2></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="metric-box"><h3>ŚR. ZMĘCZENIE</h3><h2>{m_zmeczenie:.1f}</h2></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-box"><h3>ŚR. BOLESNOŚĆ</h3><h2>{m_bolesnosc:.1f}</h2></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown(f'<div class="metric-box"><h3>ŚR. STRES</h3><h2>{m_stres:.1f}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Tabela Szczegółowa
        df_display = df_well.copy()
        # Obliczanie sumy readiness (max 20 pkt)
        df_display['Suma'] = df_display[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
        
        # Przygotowanie tabeli do wyświetlenia
        final_table = df_display[['Zawodnik', 'Sen', 'Zmeczenie', 'Bolesnosc', 'Stres', 'Suma', 'Komentarz']].copy()
        final_table = final_table.sort_values(by='Suma', ascending=True) # Najniższa gotowość na górze

        # Funkcja do kolorowania krytycznych wartości
        def highlight_readiness(row):
            # Jeśli bolesność lub zmęczenie jest <= 2, kolorujemy na czerwono
            styles = [''] * len(row)
            if row['Bolesnosc'] <= 2 or row['Zmeczenie'] <= 2 or row['Suma'] <= 10:
                return ['background-color: #ffcccc'] * len(row)
            return styles

        st.markdown("### SZCZEGÓŁY ZAWODNIKÓW (Sortowanie: najniższa gotowość na górze)")
        st.dataframe(
            final_table.style.apply(highlight_readiness, axis=1),
            use_container_width=True,
            hide_index=True
        )

# --- WIDOK 2: TRENDY ZAWODNIKÓW ---
elif widok == "Trendy Zawodników":
    st.subheader("📈 ANALIZA TRENDÓW")
    wszyscy_zawodnicy = sorted(df['Zawodnik'].unique())
    wybrany_z = st.selectbox("Wybierz zawodnika:", wszyscy_zawodnicy)
    
    df_z = df[df['Zawodnik'] == wybrany_z].sort_values('Data')
    
    tab_well, tab_rpe = st.tabs(["Wellness", "Obciążenie RPE"])
    
    with tab_well:
        df_w_z = df_z[df_z['Typ_Raportu'] == 'Wellness']
        if not df_w_z.empty:
            fig = px.line(df_w_z, x='Data', y=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'],
                          title=f"Trend Wellness - {wybrany_z}",
                          color_discrete_sequence=["#2E7D32", "#1976D2", "#D32F2F", "#FBC02D"])
            fig.update_layout(yaxis_range=[0, 6])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Brak danych Wellness.")

    with tab_rpe:
        df_r_z = df_z[df_z['Typ_Raportu'] == 'RPE']
        if not df_r_z.empty:
            fig_rpe = px.bar(df_r_z, x='Data', y='RPE', title=f"Obciążenie RPE - {wybrany_z}",
                             color_discrete_sequence=[COLOR_PRIMARY])
            fig_rpe.update_layout(yaxis_range=[0, 11])
            st.plotly_chart(fig_rpe, use_container_width=True)
        else:
            st.info("Brak danych RPE.")

# --- WIDOK 3: SUROWE DANE ---
elif widok == "Surowe Dane":
    st.subheader("📄 PEŁNA HISTORIA WPISÓW")
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
