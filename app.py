import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import pytz

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń
COLOR_BG = "#E8F5E9"        # Jasnozielone tło
COLOR_TEXT = "#121212"      # Ciemny tekst
PL_TZ = pytz.timezone('Europe/Warsaw')

# Funkcja do znalezienia logo
def get_logo():
    possible_files = ["herb.png", "logo.png", "logo.jpg", "image_b1bd1c.png"]
    for f in possible_files:
        if os.path.exists(f):
            return f
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

LOGO_PATH = get_logo()

# --- LISTA ZAWODNIKÓW ---
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Wellness", page_icon="⚽", layout="centered")

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    /* Usunięcie zbędnych marginesów na górze */
    .block-container {{
        padding-top: 1rem !important;
    }}
    
    .stApp {{ 
        background-color: {COLOR_BG} !important; 
    }}

    #MainMenu, footer, header {{visibility: hidden;}}
    
    html, body, [class*="st-"], label, p, span {{ 
        color: {COLOR_TEXT} !important;
    }}
    
    h1 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        text-transform: uppercase;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        margin-bottom: 20px;
    }}
    
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 25px !important; 
        border-radius: 15px !important; 
        border: 2px solid {COLOR_PRIMARY} !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }}

    .stButton>button {{
        width: 100%; 
        background-color: {COLOR_PRIMARY} !important; 
        color: #FFFFFF !important;
        height: 3.5em !important; 
        font-weight: bold;
        border-radius: 10px !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGO I TYTUŁ ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image(LOGO_PATH, width=120)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Ankieta Wellness</h1>", unsafe_allow_html=True)

# Pobieranie parametrów URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

# Wybór zawodnika
default_index = 0
if player_from_url in LISTA_ZAWODNIKOW:
    default_index = LISTA_ZAWODNIKOW.index(player_from_url)
    st.success(f"Zalogowano: **{player_from_url}**")

zawodnik = st.selectbox("POTWIERDŹ NAZWISKO:", LISTA_ZAWODNIKOW, index=default_index)

if zawodnik:
    with st.form("wellness_form", clear_on_submit=True):
        st.subheader("📊 Dzisiejsze samopoczucie")
        
        s1 = st.select_slider("JAKOŚĆ SNU (1-5)", options=[1,2,3,4,5], value=3)
        s2 = st.select_slider("POZIOM ZMĘCZENIA (1-5)", options=[1,2,3,4,5], value=3)
        s3 = st.select_slider("BOLESNOŚĆ MIĘŚNI (1-5)", options=[1,2,3,4,5], value=3)
        s4 = st.select_slider("POZIOM STRESU (1-5)", options=[1,2,3,4,5], value=3)
        komentarz = st.text_area("CZY COŚ CIĘ BOLI? (OPCJONALNIE)")
        
        submit = st.form_submit_button("WYŚLIJ RAPORT")

        if submit:
            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            new_data = {
                "Data": timestamp,
                "Typ_Raportu": "Wellness",
                "Zawodnik": zawodnik,
                "Sen": s1,
                "Zmeczenie": s2,
                "Bolesnosc": s3,
                "Stres": s4,
                "RPE": None,
                "Komentarz": komentarz
            }
            
            try:
                df = conn.read(worksheet="Arkusz1", ttl=0)
                updated_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=updated_df)
                st.balloons()
                st.success("Dziękujemy! Dane zostały zapisane.")
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")

# PANEL SZTABU
st.write("<br><br>", unsafe_allow_html=True)
with st.expander("🔐 PANEL SZTABU"):
    haslo = st.text_input("Hasło:", type="password")
    if haslo == "Warta1912":
        data = conn.read(worksheet="Arkusz1", ttl=0)
        st.dataframe(data.sort_index(ascending=False))
