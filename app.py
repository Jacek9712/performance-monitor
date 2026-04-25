import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"  # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')

LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Player App", page_icon="⚽", layout="centered")

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    .stApp {{
        background-color: {COLOR_BG};
    }}
    
    html, body, [class*="st-"], .stMarkdown, label, p, span {{
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}

    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        border-radius: 10px;
        height: 3em;
        font-size: 1.2em;
        border: none;
    }}

    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        text-align: center;
        text-transform: uppercase;
    }}

    .stSelectbox label, .stSlider label {{
        font-size: 1.1em !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z ARKUSZEM ---
conn = st.connection("gsheets", type=GSheetsConnection)

def check_submission(player_name, report_type):
    """Sprawdza czy zawodnik wysłał już raport danego dnia."""
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        if df.empty:
            return False
        
        today = datetime.now(PL_TZ).date().strftime("%Y-%m-%d")
        df['Data_Day'] = pd.to_datetime(df['Data']).dt.strftime("%Y-%m-%d")
        
        submitted = df[
            (df['Zawodnik'] == player_name) & 
            (df['Typ_Raportu'] == report_type) & 
            (df['Data_Day'] == today)
        ]
        return not submitted.empty
    except:
        return False

# --- UI APLIKACJI ---
st.markdown(f"<h1>WARTA POZNAŃ</h1>", unsafe_allow_html=True)
st.markdown("### PANEL ZAWODNIKA")

selected_player = st.selectbox("WYBIERZ SWOJE NAZWISKO:", [""] + LISTA_ZAWODNIKOW)

if selected_player:
    tab1, tab2 = st.tabs(["☀️ PORANNY WELLNESS", "⏱️ RPE PO TRENINGU"])

    # --- TAB 1: WELLNESS ---
    with tab1:
        if check_submission(selected_player, "Wellness"):
            st.success(f"DZIĘKUJEMY! TWOJA PORANNA OCENA ZOSTAŁA JUŻ ZAPISANA.")
        else:
            with st.form("wellness_form"):
                st.markdown("#### OCENA PORANNA")
                sen = st.select_slider("JAKOŚĆ SNU (1-ZŁA, 5-ŚWIETNA):", options=[1, 2, 3, 4, 5], value=3)
                zmeczenie = st.select_slider("POZIOM ZMĘCZENIA (1-BARDZO DUŻE, 5-WYPOCZĘTY):", options=[1, 2, 3, 4, 5], value=3)
                bolesnosc = st.select_slider("BOLESNOŚĆ MIĘŚNI (1-BARDZO DUŻA, 5-BRAK):", options=[1, 2, 3, 4, 5], value=3)
                stres = st.select_slider("POZIOM STRESU (1-DUŻY, 5-BRAK):", options=[1, 2, 3, 4, 5], value=3)
                komentarz = st.text_input("DODATKOWE UWAGI (OPCJONALNIE):")
                
                submitted_well = st.form_submit_button("WYŚLIJ RAPORT WELLNESS")
                
                if submitted_well:
                    new_data = pd.DataFrame([{
                        "Data": datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "Zawodnik": selected_player,
                        "Typ_Raportu": "Wellness",
                        "Sen": sen,
                        "Zmeczenie": zmeczenie,
                        "Bolesnosc": bolesnosc,
                        "Stres": stres,
                        "Komentarz": komentarz,
                        "RPE": None,
                        "Czas_Treningu": None
                    }])
                    
                    try:
                        existing_df = conn.read(worksheet="Arkusz1", ttl=0)
                        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                        conn.update(worksheet="Arkusz1", data=updated_df)
                        st.success("RAPORT WELLNESS ZAPISANY POMYŚLNIE.")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"BŁĄD ZAPISU: {e}")

    # --- TAB 2: RPE ---
    with tab2:
        if check_submission(selected_player, "RPE"):
            st.success(f"TWOJA OCENA WYSIŁKU PO TRENINGU ZOSTAŁA JUŻ ZAPISANA.")
        else:
            with st.form("rpe_form"):
                st.markdown("#### OCENA WYSIŁKU (RPE)")
                rpe_score = st.select_slider(
                    "INTENSYWNOŚĆ TRENINGU (1-BARDZO LEKKI, 10-MAKSYMALNY):", 
                    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                    value=5
                )
                czas_treningu = st.number_input("CZAS TRWANIA TRENINGU (W MINUTACH):", min_value=0, max_value=300, value=90, step=5)
                
                submitted_rpe = st.form_submit_button("WYŚLIJ RAPORT RPE")
                
                if submitted_rpe:
                    new_rpe_data = pd.DataFrame([{
                        "Data": datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "Zawodnik": selected_player,
                        "Typ_Raportu": "RPE",
                        "Sen": None,
                        "Zmeczenie": None,
                        "Bolesnosc": None,
                        "Stres": None,
                        "Komentarz": None,
                        "RPE": rpe_score,
                        "Czas_Treningu": czas_treningu
                    }])
                    
                    try:
                        existing_df = conn.read(worksheet="Arkusz1", ttl=0)
                        updated_df = pd.concat([existing_df, new_rpe_data], ignore_index=True)
                        conn.update(worksheet="Arkusz1", data=updated_df)
                        st.success("RAPORT RPE ZAPISANY POMYŚLNIE.")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"BŁĄD ZAPISU: {e}")

else:
    st.info("PROSZĘ WYBRAĆ ZAWODNIKA Z LISTY POWYŻEJ.")

st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.8em;'>WARTA POZNAŃ © 2024 | SYSTEM MONITOROWANIA OBCIĄŻEŃ</p>", unsafe_allow_html=True)
