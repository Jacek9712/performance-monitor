import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
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
    }}
    
    .metric-box {{
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid {COLOR_PRIMARY};
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LOGOWANIE ---
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

# --- HEADER ---
def get_logo():
    if os.path.exists("herb.png"): return "herb.png"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

col_l1, col_l2, col_l3 = st.columns([1, 0.5, 1])
with col_l2:
    st.image(get_logo(), use_container_width=True)

st.markdown("<h1>📊 SZTAB ANALYTICS PANEL</h1>", unsafe_allow_html=True)

df_raw = load_data()

if df_raw.empty or len(df_raw.columns) < 3:
    st.warning("⚠️ Brak danych w arkuszu lub nieprawidłowa struktura.")
    st.info("Upewnij się, że arkusz posiada nagłówki: Data, Typ_Raportu, Zawodnik, Sen, Zmeczenie, Bolesnosc, Stres, RPE, Komentarz")
    if st.button("🔄 Odśwież"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# --- PRZETWARZANIE DANYCH ---
df = df_raw.copy()
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
df = df.dropna(subset=['Data'])
df['Dzień'] = df['Data'].dt.date

# Sidebar
with st.sidebar:
    st.header("⚙️ FILTRY")
    widok = st.radio("WIDOK:", ["Dzienny Raport Readiness", "Trendy Zawodników", "Surowe Dane"])
    wybrana_data = st.date_input("Wybierz datę:", value=datetime.now(PL_TZ).date())
    if st.button("🔄 Odśwież Dane"):
        st.cache_data.clear()
        st.rerun()

# --- WIDOK 1: DZIENNY RAPORT READINESS ---
if widok == "Dzienny Raport Readiness":
    st.subheader(f"📅 RAPORT GOTOWOŚCI: {wybrana_data}")
    
    # Filtrowanie Wellness z danego dnia
    df_well = df[(df['Typ_Raportu'] == 'Wellness') & (df['Dzień'] == wybrana_data)]
    
    if df_well.empty:
        st.info("Brak raportów Wellness na ten dzień.")
    else:
        # Metryki ogólne
        avg_well = df_well[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].mean().mean()
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.markdown(f'<div class="metric-box"><h3>SEN</h3><h2>{df_well["Sen"].mean():.1f}</h2></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="metric-box"><h3>ZMĘCZENIE</h3><h2>{df_well["Zmeczenie"].mean():.1f}</h2></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-box"><h3>BOLESNOŚĆ</h3><h2>{df_well["Bolesnosc"].mean():.1f}</h2></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown(f'<div class="metric-box"><h3>STRES</h3><h2>{df_well["Stres"].mean():.1f}</h2></div>', unsafe_allow_html=True)

        st.markdown("---")
        
        # Tabela szczegółowa
        df_display = df_well.copy()
        df_display['Suma (Readiness)'] = df_display[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
        
        # Kolorowanie wierszy na podstawie bolesności lub zmęczenia (uproszczone)
        def highlight_low(s):
            return ['background-color: #ffcccc' if val <= 2 else '' for val in s]

        st.dataframe(
            df_display[['Zawodnik', 'Sen', 'Zmeczenie', 'Bolesnosc', 'Stres', 'Suma (Readiness)', 'Komentarz']]
            .sort_values('Suma (Readiness)', ascending=True),
            use_container_width=True,
            hide_index=True
        )

# --- WIDOK 2: TRENDY ZAWODNIKÓW ---
elif widok == "Trendy Zawodników":
    st.subheader("📈 ANALIZA TRENDÓW")
    wybrany_zawodnik = st.selectbox("Wybierz zawodnika:", sorted(df['Zawodnik'].unique()))
    
    df_z = df[df['Zawodnik'] == wybrany_zawodnik].sort_values('Data')
    
    if df_z.empty:
        st.info("Brak danych dla tego zawodnika.")
    else:
        tab_t1, tab_t2 = st.tabs(["Wellness (Trend)", "Obciążenie RPE"])
        
        with tab_t1:
            df_w_z = df_z[df_z['Typ_Raportu'] == 'Wellness']
            if not df_w_z.empty:
                fig = px.line(df_w_z, x='Data', y=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'],
                              title=f"Trend Wellness: {wybrany_zawodnik}",
                              color_discrete_sequence=["#2E7D32", "#1976D2", "#D32F2F", "#FBC02D"])
                fig.update_layout(yaxis_range=[0, 6])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Brak danych Wellness dla tego zawodnika.")
                
        with tab_t2:
            df_r_z = df_z[df_z['Typ_Raportu'] == 'RPE']
            if not df_r_z.empty:
                fig_rpe = px.bar(df_r_z, x='Data', y='RPE', title=f"Obciążenie RPE: {wybrany_zawodnik}",
                                 color_discrete_sequence=[COLOR_PRIMARY])
                fig_rpe.update_layout(yaxis_range=[0, 11])
                st.plotly_chart(fig_rpe, use_container_width=True)
            else:
                st.info("Brak danych RPE dla tego zawodnika.")

# --- WIDOK 3: SUROWE DANE ---
elif widok == "Surowe Dane":
    st.subheader("📄 WSZYSTKIE WPISY")
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
