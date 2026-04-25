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

st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="centered")

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');

    /* Marginesy */
    .block-container {{
        padding-top: 1.5rem !important;
    }}
    
    /* Tło strony */
    .stApp {{ 
        background-color: {COLOR_BG} !important; 
    }}

    /* Ukrycie elementów Streamlit */
    #MainMenu, footer, header {{visibility: hidden;}}
    
    /* Czcionka i kolory */
    html, body, [class*="st-"], label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT} !important;
    }}
    
    h1 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        text-transform: uppercase;
        margin-top: 0.5rem;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        padding: 10px;
        margin-bottom: 20px;
    }}
    
    /* Biały blok formularza */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 30px !important; 
        border-radius: 20px !important; 
        border: 2px solid {COLOR_PRIMARY} !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
    }}

    /* Styl przycisku */
    .stButton>button {{
        width: 100%; 
        background-color: {COLOR_PRIMARY} !important; 
        color: #FFFFFF !important;
        height: 3.5em !important; 
        font-size: 1.2rem !important;
        text-transform: uppercase;
        border-radius: 12px !important;
        border: none !important;
        transition: 0.3s;
    }}
    
    .stButton>button:hover {{
        opacity: 0.9;
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- NAGŁÓWEK ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image(LOGO_PATH, width=110)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

# Obsługa parametrów URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

# Logika wyboru zawodnika
default_index = 0
if player_from_url in LISTA_ZAWODNIKOW:
    default_index = LISTA_ZAWODNIKOW.index(player_from_url)
    st.info(f"Zalogowano jako: **{player_from_url}**")

zawodnik = st.selectbox("WYBIERZ ZAWODNIKA Z LISTY:", LISTA_ZAWODNIKOW, index=default_index)

if zawodnik:
    st.write("---")
    # Wybór raportu (Wellness rano / RPE po południu)
    typ_raportu = st.radio("CO CHCESZ RAPORTOWAĆ?", ["Wellness (Rano)", "RPE (Po treningu)"], horizontal=True)

    with st.form("main_form", clear_on_submit=True):
        timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
        
        if "Wellness" in typ_raportu:
            st.subheader("📊 Poranny Raport Wellness")
            s1 = st.select_slider("JAKOŚĆ SNU (1-5)", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("POZIOM ZMĘCZENIA (1-5)", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("BOLESNOŚĆ MIĘŚNI (1-5)", options=[1,2,3,4,5], value=3)
            s4 = st.select_slider("POZIOM STRESU (1-5)", options=[1,2,3,4,5], value=3)
            k = st.text_area("CZY COŚ CI DOLEGA? (OPCJONALNIE)")
            
            if st.form_submit_button("WYŚLIJ WELLNESS"):
                try:
                    df = conn.read(worksheet="Arkusz1", ttl=0)
                    new_row = {"Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik, "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k}
                    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(worksheet="Arkusz1", data=updated_df)
                    st.balloons()
                    st.success("Raport Wellness wysłany!")
                except Exception as e:
                    st.error(f"Błąd: {e}")
        
        else:
            st.subheader("🏃‍♂️ Raport Intensywności (RPE)")
            rpe_val = st.slider("JAK OCENIASZ TRUDNOŚĆ TRENINGU?", 0, 10, 5)
            st.info("0: Odpoczynek | 5: Średnio | 10: Maksymalny wysiłek")
            k_rpe = st.text_area("KOMENTARZ DO TRENINGU")
            
            if st.form_submit_button("WYŚLIJ RPE"):
                try:
                    df = conn.read(worksheet="Arkusz1", ttl=0)
                    new_row = {"Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik, "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe_val, "Komentarz": k_rpe}
                    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(worksheet="Arkusz1", data=updated_df)
                    st.balloons()
                    st.success("Raport RPE wysłany!")
                except Exception as e:
                    st.error(f"Błąd: {e}")

# PANEL ADMINISTRACYJNY
st.write("<br><br><br>", unsafe_allow_html=True)
with st.expander("🔐 DOSTĘP DLA SZTABU"):
    haslo = st.text_input("HASŁO:", type="password")
    if haslo == "Warta1912":
        data = conn.read(worksheet="Arkusz1", ttl=0)
        st.dataframe(data.sort_index(ascending=False), use_container_width=True)
