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

# Funkcja do znalezienia logo na serwerze
def get_logo():
    possible_files = ["herb.png", "logo.png", "logo.jpg", "image_b1bd1c.png"]
    for f in possible_files:
        if os.path.exists(f):
            return f
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

LOGO_PATH = get_logo()

# --- AKTUALNA LISTA ZAWODNIKÓW ---
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
    
    .stApp {{ 
        background-color: {COLOR_BG} !important; 
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT} !important;
    }}
    
    h1, h2, h3 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        text-transform: uppercase;
        margin-top: 0.5rem;
        letter-spacing: 1px;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        padding: 20px; 
        margin-bottom: 5px;
    }}
    
    /* Stylizacja zakładek (Tabs) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        justify-content: center;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        font-weight: bold;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
    }}
    
    /* Formularz */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 35px !important; 
        border-radius: 20px !important; 
        border: none !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
    }}

    /* Przycisk */
    .stButton>button {{
        width: 100%; 
        background-color: {COLOR_PRIMARY} !important; 
        color: #FFFFFF !important;
        height: 3.5em !important; 
        font-size: 1.2rem !important; 
        border-radius: 12px !important;
        text-transform: uppercase;
        border: none !important;
        transition: 0.3s ease;
        margin-top: 20px;
    }}
    
    .stButton>button:hover {{
        background-color: #004d26 !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }}

    /* Ukrycie legendy RPE (tekstu informacyjnego pod suwakiem) */
    .stSlider > div > div > div > div {{
        color: {COLOR_PRIMARY};
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_gsheets(row_data):
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Arkusz1", data=updated_df)
        st.balloons()
        st.success("✔ RAPORT ZOSTAŁ WYSŁANY POMYŚLNIE!")
    except Exception as e:
        st.error(f"❌ BŁĄD ZAPISU: {e}")

# Nagłówek z powiększonym logo
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image(LOGO_PATH, width=150) # Zwiększono ze 100 na 150
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

# Parametry URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

# Wybór zawodnika
default_index = 0
if player_from_url in LISTA_ZAWODNIKOW:
    default_index = LISTA_ZAWODNIKOW.index(player_from_url)
    st.info(f"ZALOGOWANY JAKO: **{player_from_url}**")

zawodnik = st.selectbox("POTWIERDŹ SWOJE NAZWISKO:", LISTA_ZAWODNIKOW, index=default_index)

if zawodnik:
    st.write("")
    # Zakładki (Tabs) do wyboru raportu
    tab_well, tab_rpe = st.tabs(["📊 WELLNESS (RANO)", "🏃 RPE (PO TRENINGU)"])

    with tab_well:
        with st.form("wellness_form", clear_on_submit=True):
            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            st.subheader("PORANNA ANKIETA")
            
            s1 = st.select_slider("JAKOŚĆ SNU", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("BOLESNOŚĆ MIĘŚNI", options=[1,2,3,4,5], value=3)
            s4 = st.select_slider("POZIOM STRESU", options=[1,2,3,4,5], value=3)
            k = st.text_area("DODATKOWE UWAGI / CO CIĘ BOLI?")
            
            if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
                save_to_gsheets({
                    "Data": timestamp, 
                    "Typ_Raportu": "Wellness", 
                    "Zawodnik": zawodnik, 
                    "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, 
                    "RPE": None, "Komentarz": k
                })

    with tab_rpe:
        with st.form("rpe_form", clear_on_submit=True):
            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            st.subheader("INTENSYWNOŚĆ TRENINGU")
            
            rpe = st.slider("OCENA WYSIŁKU (RPE)", 0, 10, 5)
            # Legenda została usunięta
            k_rpe = st.text_area("KOMENTARZ DO TRENINGU")
            
            if st.form_submit_button("WYŚLIJ RAPORT RPE"):
                save_to_gsheets({
                    "Data": timestamp, 
                    "Typ_Raportu": "RPE", 
                    "Zawodnik": zawodnik, 
                    "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, 
                    "RPE": rpe, "Komentarz": k_rpe
                })

# PANEL SZTABU
st.write("<br><br><br>", unsafe_allow_html=True)
with st.expander("🔐 PANEL SZTABU"):
    admin_pass = st.text_input("Hasło:", type="password")
    if admin_pass == "Warta1912":
        df_data = conn.read(worksheet="Arkusz1", ttl=0)
        st.dataframe(df_data.sort_index(ascending=False), use_container_width=True)
