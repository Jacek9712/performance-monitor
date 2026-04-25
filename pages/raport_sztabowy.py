import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_SZTAB = "Warta2024"  # Możesz zmienić hasło tutaj

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

# Wymuszenie konfiguracji strony i widoczności sidebar
st.set_page_config(
    page_title="Warta Poznań - Analiza Sztabu", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SYSTEM LOGOWANIA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]:
        return True
    
    st.markdown(f"<h1>🔐 PANEL SZTABU - LOGOWANIE</h1>", unsafe_allow_html=True)
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

# Jeśli niezalogowany, przerwij wykonywanie reszty skryptu
if not check_password():
    st.stop()

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    .main {{ background-color: #f0f2f6; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY} !important; text-align: center; text-transform: uppercase; font-weight: bold; }}
    .stMetric {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    div[data-testid="stDataFrame"] {{ background-color: white; border-radius: 10px; padding: 10px; }}
    
    [data-testid="stSidebar"] {{
        background-color: white !important;
        border-right: 3px solid {COLOR_PRIMARY};
    }}
    </style>
    """, unsafe_allow_html=True)

# Pasek boczny
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=100)
    st.markdown(f"<h3 style='text-align: center;'>SZTAB ANALIZA</h3>", unsafe_allow_html=True)
    if st.button("Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

st.title("📊 Monitoring Miesięczny")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Arkusz1", ttl="1s")
    
    if df is None or df.empty:
        st.warning("Brak danych w arkuszu.")
    else:
        df['Data'] = pd.to_datetime(df['Data'])
        df['Dzien'] = df['Data'].dt.date
        
        teraz = datetime.now(PL_TZ)
        biezacy_miesiac = teraz.month
        biezacy_rok = teraz.year
        dni_w_miesiacu = calendar.monthrange(biezacy_rok, biezacy_miesiac)[1]

        st.header(f"📅 Miesiąc: {teraz.strftime('%m / %Y')}")
        st.info(f"Skala miesiąca: {dni_w_miesiacu} dni.")

        df_miesiac = df[(df['Data'].dt.month == biezacy_miesiac) & (df['Data'].dt.year == biezacy_rok)]

        stats_data = []
        for zawodnik in LISTA_ZAWODNIKOW:
            player_data = df_miesiac[df_miesiac['Zawodnik'] == zawodnik]
            
            well_data = player_data[player_data['Typ_Raportu'] == 'Wellness']
            well_count = well_data['Dzien'].nunique()
            well_avg = well_data[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].mean().mean()
            
            rpe_data = player_data[player_data['Typ_Raportu'] == 'RPE']
            rpe_count = rpe_data['Dzien'].nunique()
            rpe_avg = rpe_data['RPE'].mean()

            stats_data.append({
                "Zawodnik": zawodnik,
                "Wellness (%)": f"{well_count} / {dni_w_miesiacu}",
                "Wellness_Suma": well_count,
                "Śr. Wellness": round(well_avg, 2) if not pd.isna(well_avg) else 0,
                "RPE (%)": f"{rpe_count} / {dni_w_miesiacu}",
                "RPE_Suma": rpe_count,
                "Śr. RPE": round(rpe_avg, 2) if not pd.isna(rpe_avg) else 0
            })

        df_final = pd.DataFrame(stats_data)

        # Wyświetlanie tabel
        st.subheader("📋 Poranki (Wellness)")
        well_disp = df_final[['Zawodnik', 'Wellness (%)', 'Śr. Wellness']].sort_values(by="Wellness (%)")
        st.dataframe(well_disp.style.background_gradient(subset=['Śr. Wellness'], cmap="RdYlGn"), use_container_width=True, hide_index=True)

        st.write("---")

        st.subheader("🏃 Treningi (RPE)")
        rpe_disp = df_final[['Zawodnik', 'RPE (%)', 'Śr. RPE']].sort_values(by="RPE (%)")
        st.dataframe(rpe_disp.style.background_gradient(subset=['Śr. RPE'], cmap="YlOrRd"), use_container_width=True, hide_index=True)

        with st.expander("🔍 Surowe dane"):
            st.dataframe(df_miesiac.sort_values(by="Data", ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Błąd: {e}")
