import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import pytz

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń
COLOR_SECONDARY = "#2E7D32" # Średnia zieleń
COLOR_BG = "#F1F8E9"        # Bardzo jasne zielone tło
COLOR_TEXT = "#1B5E20"      # Ciemnozielony tekst
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

# --- ZAAWANSOWANA STYLIZACJA CSS (NOWOCZESNY LOOK) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    /* Tło z gradientem */
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}
    
    /* Nagłówek spójny z kartą */
    .custom-header {{
        text-align: center;
        margin-bottom: 20px;
    }}

    h1 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 2px;
        font-size: 2.8rem !important;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        padding: 20px 0;
    }}
    
    /* Stylizacja zakładek */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        justify-content: center;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 12px 12px 0px 0px;
        padding: 10px 25px;
        font-weight: bold;
    }}

    /* Poprawka widoczności napisu na aktywnej zakładce */
    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
    }}
    
    .stTabs [aria-selected="true"] p {{
        color: white !important;
    }}
    
    /* Formularz - Spójna Biała Karta */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 40px !important; 
        border-radius: 20px !important; 
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
    }}

    /* Przycisk akcji - WYMUSZENIE BIAŁEGO TEKSTU */
    .stButton>button {{
        width: 100%; 
        background: {COLOR_PRIMARY} !important;
        color: white !important;
        height: 3.5em !important; 
        font-size: 1.2rem !important; 
        border-radius: 12px !important;
        text-transform: uppercase;
        border: none !important;
        transition: 0.3s;
        margin-top: 20px;
    }}
    
    .stButton>button p, .stButton>button span {{
        color: white !important;
    }}
    
    .stButton>button:hover {{
        background: {COLOR_SECONDARY} !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }}

    /* Opisy skali wellness */
    .scale-info {{
        font-size: 0.85rem;
        color: #555 !important;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 15px;
        font-weight: normal;
    }}

    /* Informacja o zalogowaniu */
    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        margin: 0 auto 20px auto;
        max-width: 400px;
        font-weight: bold;
        font-size: 1.2rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
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
        st.success("✔ RAPORT WYSŁANY!")
    except Exception as e:
        st.error(f"❌ BŁĄD: {e}")

# Logo (Powiększone i wyśrodkowane)
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image(LOGO_PATH, width=220) 
st.markdown('</div>', unsafe_allow_html=True)

# Nagłówek spójny wizualnie
st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

# Logika blokowania zawodnika z URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

zawodnik = None

if player_from_url in LISTA_ZAWODNIKOW:
    # Ukrywamy całkowicie wybór, jeśli zawodnik jest w URL
    st.markdown(f'<div class="login-info">ZALOGOWANO JAKO:<br>{player_from_url.upper()}</div>', unsafe_allow_html=True)
    zawodnik = player_from_url
else:
    # Wyświetlamy wybór tylko gdy brak parametru w linku
    zawodnik = st.selectbox(
        "WYBIERZ SWOJE NAZWISKO:", 
        LISTA_ZAWODNIKOW,
        index=None,
        placeholder="Kliknij, aby wybrać..."
    )

if zawodnik:
    st.markdown("<br>", unsafe_allow_html=True)
    tab_well, tab_rpe = st.tabs(["📊 WELLNESS", "🏃 RPE"])

    with tab_well:
        with st.form("wellness_form", clear_on_submit=True):
            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(f"<h3 style='text-align:center;'>RAPORT PORANNY</h3>", unsafe_allow_html=True)
            
            s1 = st.select_slider("JAKOŚĆ SNU", options=[1,2,3,4,5], value=3)
            st.markdown('<p class="scale-info">1: BARDZO SŁABO | 5: REWELACJA</p>', unsafe_allow_html=True)
            
            s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
            st.markdown('<p class="scale-info">1: BARDZO DUŻE | 5: BRAK ZMĘCZENIA</p>', unsafe_allow_html=True)
            
            s3 = st.select_slider("BOLESNOŚĆ MIĘŚNI", options=[1,2,3,4,5], value=3)
            st.markdown('<p class="scale-info">1: BARDZO BOLI | 5: NIC NIE BOLI</p>', unsafe_allow_html=True)
            
            s4 = st.select_slider("POZIOM STRESU", options=[1,2,3,4,5], value=3)
            st.markdown('<p class="scale-info">1: DUŻY STRES | 5: PEŁEN SPOKÓJ</p>', unsafe_allow_html=True)
            
            k = st.text_area("CZY COŚ CIĘ BOLI? (OPISZ)", placeholder="Miejsce bólu, uwagi...")
            
            if st.form_submit_button("WYŚLIJ WELLNESS"):
                save_to_gsheets({
                    "Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik, 
                    "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, 
                    "RPE": None, "Komentarz": k
                })

    with tab_rpe:
        with st.form("rpe_form", clear_on_submit=True):
            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(f"<h3 style='text-align:center;'>PO TRENINGU</h3>", unsafe_allow_html=True)
            
            rpe = st.slider("INTENSYWNOŚĆ (RPE)", 0, 10, 5)
            
            k_rpe = st.text_area("DODATKOWE UWAGI", placeholder="Wpisz swoje uwagi...")
            
            if st.form_submit_button("WYŚLIJ RPE"):
                save_to_gsheets({
                    "Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik, 
                    "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, 
                    "RPE": rpe, "Komentarz": k_rpe
                })
