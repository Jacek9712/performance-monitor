import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time
import pytz
import calendar
import matplotlib # Wymagane przez Pandas do kolorowania tabel

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"
COLOR_TEXT = "#1a1a1a"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_SZTAB = "WartaSztab2024"
GODZINA_GRANICZNA = 10 # Raporty do 10:00 są "o czasie"

# Pełna lista zawodników
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

# Wymuszenie konfiguracji strony
st.set_page_config(
    page_title="Warta Poznań - Panel Sztabu", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SYSTEM LOGOWANIA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]:
        return True
    
    st.markdown(f"<h1 style='color: {COLOR_PRIMARY};'>🔐 PANEL SZTABU - LOGOWANIE</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        pwd = st.text_input("Hasło dostępu:", type="password")
        if st.button("Zaloguj"):
            if pwd == PASSWORD_SZTAB:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Błędne hasło!")
    return False

if not check_password():
    st.stop()

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa !important; color: {COLOR_TEXT} !important; }}
    h1, h2, h3, h4 {{ color: {COLOR_PRIMARY} !important; text-align: center !important; text-transform: uppercase !important; font-weight: bold !important; }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {COLOR_TEXT} !important; }}
    div[data-testid="stDataFrame"] {{ background-color: white !important; border-radius: 10px !important; padding: 5px !important; border: 1px solid #e0e0e0 !important; }}
    [data-testid="stSidebar"] {{ background-color: white !important; border-right: 3px solid {COLOR_PRIMARY} !important; }}
    [data-testid="stSidebar"] * {{ color: {COLOR_TEXT} !important; }}
    .stAlert {{ background-color: white !important; border: 1px solid {COLOR_PRIMARY} !important; }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=100)
    st.markdown(f"<h3 style='text-align: center;'>SYSTEM ANALIZY</h3>", unsafe_allow_html=True)
    st.write("---")
    if st.button("Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

st.title("📊 Monitorowanie Miesięczne")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Arkusz1", ttl="1s")
    
    if df is None or df.empty:
        st.warning("Brak danych w arkuszu.")
    else:
        df['Data'] = pd.to_datetime(df['Data'], format='mixed')
        df['Dzien'] = df['Data'].dt.date
        df['Godzina'] = df['Data'].dt.hour
        
        teraz = datetime.now(PL_TZ)
        biezacy_miesiac = teraz.month
        biezacy_rok = teraz.year
        dni_w_miesiacu = calendar.monthrange(biezacy_rok, biezacy_miesiac)[1]

        st.header(f"📅 Miesiąc: {teraz.strftime('%m / %Y')}")
        st.info(f"Raporty Wellness uznawane za 'punktualne' do godziny {GODZINA_GRANICZNA}:00.")

        df_miesiac = df[(df['Data'].dt.month == biezacy_miesiac) & (df['Data'].dt.year == biezacy_rok)]

        stats_data = []
        for zawodnik in LISTA_ZAWODNIKOW:
            player_data = df_miesiac[df_miesiac['Zawodnik'] == zawodnik]
            
            # Wellness
            well_data = player_data[player_data['Typ_Raportu'] == 'Wellness']
            # O czasie vs Spóźnione
            well_on_time = well_data[well_data['Godzina'] < GODZINA_GRANICZNA]['Dzien'].nunique()
            well_late = well_data[well_data['Godzina'] >= GODZINA_GRANICZNA]['Dzien'].nunique()
            well_total = well_data['Dzien'].nunique()
            
            well_cols = ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']
            for col in well_cols:
                if col in well_data.columns:
                    well_data[col] = pd.to_numeric(well_data[col], errors='coerce')
            well_avg = well_data[well_cols].mean().mean()
            
            # RPE
            rpe_data = player_data[player_data['Typ_Raportu'] == 'RPE']
            if not rpe_data.empty:
                rpe_data['RPE'] = pd.to_numeric(rpe_data['RPE'], errors='coerce')
            rpe_count = int(rpe_data['Dzien'].nunique())
            rpe_avg = rpe_data['RPE'].mean()

            stats_data.append({
                "Zawodnik": zawodnik,
                "Wellness (Suma)": f"{well_total} / {dni_w_miesiacu}",
                "O czasie": well_on_time,
                "Spóźnione": well_late,
                "Wellness_Suma": well_total,
                "Śr. Wellness": round(well_avg, 2) if not pd.isna(well_avg) else 0.0,
                "RPE (%)": f"{rpe_count} / {dni_w_miesiacu}",
                "RPE_Suma": rpe_count,
                "Śr. RPE": round(rpe_avg, 2) if not pd.isna(rpe_avg) else 0.0
            })

        df_final = pd.DataFrame(stats_data)

        # Sekcja Wellness
        st.subheader("📋 Poranki (Wellness)")
        well_disp = df_final[['Zawodnik', 'Wellness (Suma)', 'O czasie', 'Spóźnione', 'Śr. Wellness', 'Wellness_Suma']].sort_values(by="O czasie", ascending=False)
        
        st.dataframe(
            well_disp[['Zawodnik', 'Wellness (Suma)', 'O czasie', 'Spóźnione', 'Śr. Wellness']].style.background_gradient(
                subset=['Śr. Wellness'], cmap="RdYlGn", vmin=1, vmax=5
            ).background_gradient(
                subset=['O czasie'], cmap="Greens"
            ).background_gradient(
                subset=['Spóźnione'], cmap="Oranges"
            ), 
            use_container_width=True, 
            hide_index=True
        )

        st.write("---")

        # Sekcja RPE
        st.subheader("🏃 Treningi (RPE)")
        rpe_disp = df_final[['Zawodnik', 'RPE (%)', 'Śr. RPE', 'RPE_Suma']].sort_values(by="RPE_Suma", ascending=False)
        st.dataframe(
            rpe_disp[['Zawodnik', 'RPE (%)', 'Śr. RPE']].style.background_gradient(
                subset=['Śr. RPE'], cmap="YlOrRd", vmin=0, vmax=10
            ), 
            use_container_width=True, 
            hide_index=True
        )

        with st.expander("🔍 Podgląd wszystkich wpisów (Miesiąc)"):
            st.dataframe(df_miesiac.sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Błąd podczas przetwarzania danych: {e}")
