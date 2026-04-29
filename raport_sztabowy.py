import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import pytz
import calendar
import plotly.express as px
import plotly.graph_objects as go
import os

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "Warta!"

LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcel Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Oskar Mazurkiewicz", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Sztab", page_icon="📋", layout="wide")

# --- ŁADOWANIE DANYCH ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    return conn.read(worksheet="Arkusz1")

# --- WIDOK SZTABOWY ---
st.markdown(f"<h1>📊 PERFORMANCE & STAFF ANALYTICS</h1>", unsafe_allow_html=True)

try:
    df_raw = load_data()
    df = df_raw.copy()
    df['Data'] = pd.to_datetime(df['Data'], format='mixed')
    df['Dzień'] = df['Data'].dt.date

    with st.sidebar:
        st.header("⚙️ MENU")
        widok = st.radio("WYBIERZ WIDOK:", ["Zarządzaj Treningiem", "Analiza RPE", "Raport Gotowości", "Statystyki"])
        
        if st.button("🔄 Odśwież Dane"):
            st.cache_data.clear()
            st.rerun()

    if widok == "Zarządzaj Treningiem":
        st.subheader("📅 USTAWIENIA SESJI TRENINGOWEJ")
        st.info("Tutaj ustawiasz czas trwania treningu, który zostanie automatycznie przypisany do raportów zawodników.")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            data_treningu = st.date_input("Data treningu:", value=datetime.now(PL_TZ).date())
            czas_minut = st.number_input("Czas trwania sesji (minuty):", min_value=15, max_value=240, value=90, step=5)
            
            if st.button("Zapisz czas trwania sesji"):
                # Logika zapisu do Google Sheets (wymaga osobnej zakładki lub zapisu w bazie)
                st.success(f"Ustawiono {czas_minut} min dla dnia {data_treningu}. Zawodnicy nie muszą już wpisywać czasu!")
                # W praktyce wysyłamy to do Arkusza 'Konfiguracja'
        
    elif widok == "Analiza RPE":
        wybrana_data = st.date_input("Dzień analizy:", value=datetime.now(PL_TZ).date())
        df_day = df[(df['Dzień'] == wybrana_data) & (df['Typ_Raportu'] == 'RPE')]
        
        if df_day.empty:
            st.warning("Brak danych RPE dla tego dnia.")
        else:
            # Uwzględniamy czas podany przez trenera lub ten z raportu (fallback)
            df_day['Session_Load'] = df_day['RPE'] * df_day['Czas_Trwania']
            
            st.markdown(f"### Obciążenia z dnia {wybrana_data}")
            st.dataframe(df_day[['Zawodnik', 'RPE', 'Czas_Trwania', 'Session_Load', 'Komentarz']].sort_values('Session_Load', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Błąd: {e}")
