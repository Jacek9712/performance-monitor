import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import pytz
import calendar
import plotly.express as px
import plotly.graph_objects as px_go
import io
import os

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024"
GODZINA_WELLNESS = 10 
GODZINA_RPE = 17

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
        return conn.read(worksheet="Arkusz1", ttl=0)
    except Exception:
        return pd.DataFrame()

# --- HEADER Z LOGO ---
def get_logo():
    if os.path.exists("herb.png"):
        return "herb.png"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

col_l1, col_l2, col_l3 = st.columns([1, 0.5, 1])
with col_l2:
    st.image(get_logo(), use_container_width=True)

st.markdown(f"<h1>📊 PERFORMANCE & STAFF ANALYTICS</h1>", unsafe_allow_html=True)

try:
    df_raw = load_data()
    
    if df_raw.empty or len(df_raw.columns) < 3:
        st.error("⚠️ BŁĄD STRUKTURY ARKUSZA")
        st.info("""
        Twój Arkusz Google wydaje się pusty lub nie ma wymaganych kolumn. 
        Upewnij się, że w pierwszym wierszu arkusza 'Arkusz1' znajdują się nagłówki:
        **Data, Typ_Raportu, Zawodnik, Sen, Zmeczenie, Bolesnosc, Stres, RPE, Komentarz**
        """)
        if st.button("🔄 Spróbuj odświeżyć po naprawie arkusza"):
            st.cache_data.clear()
            st.rerun()
    else:
        # Przetwarzanie danych
        df = df_raw.copy()
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.dropna(subset=['Data'])
        df['Dzień'] = df['Data'].dt.date
        df['Godzina_H'] = df['Data'].dt.hour
        
        NAZWY_MIESIECY = {1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień", 5: "Maj", 6: "Czerwiec", 
                          7: "Lipiec", 8: "Sierpień", 9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"}

        with st.sidebar:
            st.header("⚙️ USTAWIENIA")
            widok = st.radio("WYBIERZ WIDOK:", ["Raport Dzienny", "Raport Sztabowy", "Surowe Dane"])
            teraz = datetime.now(PL_TZ)
            
            if widok == "Raport Dzienny":
                wybrana_data = st.date_input("Wybierz dzień:", value=teraz.date())
            
            if st.button("🔄 Odśwież Dane"):
                st.cache_data.clear()
                st.rerun()

        # --- WIDOKI ---
        if widok == "Raport Dzienny":
            st.subheader(f"📅 RAPORT: {wybrana_data}")
            df_day = df[df['Dzień'] == wybrana_data]
            df_well_day = df_day[df_day['Typ_Raportu'] == 'Wellness']
            
            if df_well_day.empty:
                st.info("Brak danych na ten dzień.")
            else:
                # Tabela gotowości
                ready_list = []
                for z in df_well_day['Zawodnik'].unique():
                    z_data = df_well_day[df_well_day['Zawodnik'] == z].iloc[-1]
                    readiness_total = z_data[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum()
                    ready_list.append({
                        "Zawodnik": z,
                        "Sen": int(z_data['Sen']),
                        "Zmęczenie": int(z_data['Zmeczenie']),
                        "Bolesność": int(z_data['Bolesnosc']),
                        "Stres": int(z_data['Stres']),
                        "RAZEM": int(readiness_total)
                    })
                st.table(pd.DataFrame(ready_list))

        elif widok == "Surowe Dane":
            st.subheader("📄 PEŁNA HISTORIA")
            st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Wystąpił błąd: {e}")
