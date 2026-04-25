import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import pytz

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń
COLOR_SECONDARY = "#004d26" # Ciemniejsza zieleń dla kontrastu
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

# --- ZAAWANSOWANA STYLIZACJA CSS (FIX DLA TRYBU CIEMNEGO) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    /* Wymuszenie jasnego tła aplikacji, by tryb ciemny nie psuł czytelności */
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Globalne wymuszenie kolorów czcionek */
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT} !important;
    }}
    
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
    
    /* Zakładki - Poprawa kontrastu */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        justify-content: center;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: #f0f0f0 !important;
        border-radius: 12px 12px 0px 0px;
        padding: 10px 25px;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
    }}
    
    .stTabs [aria-selected="true"] p {{
        color: white !important;
    }}
    
    /* Formularz - Wymuszenie białej karty */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 30px !important; 
        border-radius: 20px !important; 
        border: 2px solid #e0e0e0 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
    }}

    /* PRZYCISK WYŚLIJ - EKSTREMALNA WIDOCZNOŚĆ */
    div.stButton > button {{
        width: 100% !important; 
        background-color: {COLOR_PRIMARY} !important;
        color: #FFFFFF !important;
        height: 4em !important; 
        font-size: 1.4rem !important; 
        border-radius: 15px !important;
        text-transform: uppercase !important;
        border: 3px solid #FFFFFF !important; /* Biała ramka dla kontrastu w dark mode */
        font-weight: 900 !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.4) !important;
        margin-top: 25px !important;
        display: block !important;
    }}

    /* Naprawa kolorów wewnątrz przycisku dla trybów przeglądarki */
    div.stButton > button * {{
        color: #FFFFFF !important;
    }}
    
    div.stButton > button:hover {{
        background-color: #00331a !important;
        border-color: #FFD700 !important; /* Złoty akcent przy najechaniu */
        transform: scale(1.02);
    }}

    /* POLA TEKSTOWE - WYRAŹNE I CZYTELNE */
    .stTextArea textarea {{
        border: 2px solid {COLOR_PRIMARY} !important;
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        color: #000000 !important;
        font-size: 1.1rem !important;
        padding: 15px !important;
    }}

    .stTextArea label p {{
        font-weight: bold !important;
        font-size: 1.1rem !important;
        background-color: #E8F5E9;
        padding: 5px 10px;
        border-radius: 5px;
        display: inline-block;
    }}

    /* Legenda wellness */
    .wellness-legend {{
        background-color: #ffffff;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid {COLOR_PRIMARY};
        margin-bottom: 20px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
    }}

    .legend-item {{
        font-size: 1rem;
        text-align: center;
        color: #000000 !important;
    }}

    /* Informacja o zalogowaniu */
    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: #FFFFFF !important;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #FFFFFF;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
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

# Logo
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image(LOGO_PATH, width=220) 
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

query_params = st.query_params
player_from_url = query_params.get("player", None)

zawodnik = None

if player_from_url in LISTA_ZAWODNIKOW:
    st.markdown(f'<div class="login-info">ZALOGOWANO JAKO:<br><span style="font-size: 1.5rem;">{player_from_url.upper()}</span></div>', unsafe_allow_html=True)
    zawodnik = player_from_url
else:
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
            
            st.markdown("""
                <div class="wellness-legend">
                    <div style="display: flex; justify-content: space-around;">
                        <div class="legend-item"><span style="font-size:1.5rem;">🔴</span><br>1<br><b>BARDZO ŹLE</b></div>
                        <div class="legend-item"><span style="font-size:1.5rem;">🟡</span><br>3<br><b>PRZECIĘTNIE</b></div>
                        <div class="legend-item"><span style="font-size:1.5rem;">🟢</span><br>5<br><b>IDEALNIE</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            s1 = st.select_slider("JAKOŚĆ SNU", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("ZMĘCZENIE OGÓLNE", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("BOLESNOŚĆ MIĘŚNI", options=[1,2,3,4,5], value=3)
            s4 = st.select_slider("POZIOM STRESU", options=[1,2,3,4,5], value=3)
            
            k = st.text_area("DODATKOWE UWAGI (NP. URAZY)", placeholder="Opisz swoje samopoczucie lub ewentualny ból...", height=120)
            
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
            
            k_rpe = st.text_area("UWAGI DO TRENINGU", placeholder="Wpisz swoje uwagi...", height=120)
            
            if st.form_submit_button("WYŚLIJ RPE"):
                save_to_gsheets({
                    "Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik, 
                    "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, 
                    "RPE": rpe, "Komentarz": k_rpe
                })
