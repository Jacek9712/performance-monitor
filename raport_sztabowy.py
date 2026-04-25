import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar
import plotly.express as px

# --- KONFIGURACJA WIZUALNA ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024" # Hasło do panelu

# Pełna lista zawodników (spójna z aplikacją zawodnika)
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

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

    /* Stylizacja kart metryk */
    [data-testid="stMetric"] {{
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }}
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

# --- POŁĄCZENIE Z DANYMI ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    return conn.read(worksheet="Arkusz1", ttl=0)

# --- GŁÓWNA TREŚĆ ---
st.markdown(f"<h1>📊 PANEL ANALITYCZNY SZTABU</h1>", unsafe_allow_html=True)

try:
    df = load_data()
    
    if df.empty:
        st.info("Brak danych do wyświetlenia. Poczekaj na pierwsze raporty zawodników.")
    else:
        df['Data'] = pd.to_datetime(df['Data'])
        df['Dzień'] = df['Data'].dt.date
        
        # Sidebar - Filtry
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=80)
            st.header("USTAWIENIA")
            wybrany_miesiac = st.selectbox("Miesiąc:", range(1, 13), index=datetime.now().month-1)
            
            if st.button("Wyloguj"):
                st.session_state["auth_staff"] = False
                st.rerun()

        # Filtrowanie danych do bieżącego miesiąca
        df_month = df[df['Data'].dt.month == wybrany_miesiac]
        days_in_month = calendar.monthrange(datetime.now().year, wybrany_miesiac)[1]

        # --- KPI ---
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Raporty Wellness", len(df_month[df_month['Typ_Raportu'] == 'Wellness']))
        with c2:
            st.metric("Raporty RPE", len(df_month[df_month['Typ_Raportu'] == 'RPE']))
        with c3:
            avg_well = df_month[df_month['Typ_Raportu'] == 'Wellness'][['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].mean().mean()
            st.metric("Średni Wellness", f"{avg_well:.2f}/5" if not pd.isna(avg_well) else "N/A")
        with c4:
            avg_rpe = df_month[df_month['Typ_Raportu'] == 'RPE']['RPE'].mean()
            st.metric("Średnie RPE", f"{avg_rpe:.2f}/10" if not pd.isna(avg_rpe) else "N/A")

        # --- TABELA ZBIORCZA ---
        st.write("---")
        st.subheader("📋 PODSUMOWANIE ZAWODNIKÓW")
        
        stats = []
        for p in LISTA_ZAWODNIKOW:
            p_data = df_month[df_month['Zawodnik'] == p]
            well_p = p_data[p_data['Typ_Raportu'] == 'Wellness']
            rpe_p = p_data[p_data['Typ_Raportu'] == 'RPE']
            
            w_count = len(well_p)
            r_count = len(rpe_p)
            w_avg = well_p[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].mean().mean()
            
            stats.append({
                "Zawodnik": p,
                "Wellness (dni)": f"{w_count}/{days_in_month}",
                "Śr. Wellness": round(w_avg, 2) if not pd.isna(w_avg) else 0,
                "RPE (dni)": f"{r_count}/{days_in_month}",
                "Ostatni Komentarz": p_data.sort_values('Data', ascending=False)['Komentarz'].iloc[0] if not p_data.empty else ""
            })
        
        df_stats = pd.DataFrame(stats)
        
        # Wyświetlanie tabeli z kolorowaniem
        st.dataframe(
            df_stats.style.background_gradient(subset=['Śr. Wellness'], cmap="RdYlGn", vmin=1, vmax=5),
            use_container_width=True,
            hide_index=True
        )

        # --- WYKRESY ---
        st.write("---")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("📈 TREND WELLNESS DRUŻYNY")
            trend = df_month[df_month['Typ_Raportu'] == 'Wellness'].groupby('Dzień')[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].mean().mean(axis=1).reset_index()
            trend.columns = ['Data', 'Wellness']
            fig = px.line(trend, x='Data', y='Wellness', markers=True, color_discrete_sequence=[COLOR_PRIMARY])
            fig.update_layout(yaxis_range=[1, 5])
            st.plotly_chart(fig, use_container_width=True)
            
        with col_b:
            st.subheader("🔥 OBCIĄŻENIE TRENINGOWE (RPE)")
            rpe_bar = df_month[df_month['Typ_Raportu'] == 'RPE'].groupby('Zawodnik')['RPE'].mean().reset_index()
            fig2 = px.bar(rpe_bar, x='Zawodnik', y='RPE', color='RPE', color_continuous_scale='Greens')
            st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Problem z bazą danych: {e}")

if st.button("🔄 ODŚWIEŻ DANE"):
    st.cache_data.clear()
    st.rerun()
