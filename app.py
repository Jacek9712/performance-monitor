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

# --- ZAAWANSOWANA STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    /* Tło całej aplikacji z delikatnym gradientem */
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
    
    .custom-header {{
        text-align: center;
        margin-bottom: 10px;
    }}

    h1 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 1px;
        font-size: 1.8rem !important;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        align-items: center;
        width: 100%;
        margin: 0 auto;
        padding: 10px 0;
    }}
    
    /* Zakładki */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 5px;
        justify-content: center;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 10px 10px 0px 0px;
        padding: 5px 20px;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
    }}
    
    .stTabs [aria-selected="true"] p {{
        color: white !important;
    }}

    /* Biały obszar formularza (tam gdzie wybieramy) */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #d1d9e6 !important;
        padding: 25px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }}

    /* Stylowanie przycisku wysyłania */
    button[kind="formSubmit"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        width: 100% !important;
        border: none !important;
        padding: 10px !important;
        margin-top: 10px !important;
        text-transform: uppercase;
    }}

    /* Legenda z gradientem */
    .wellness-legend {{
        background: linear-gradient(90deg, #FFEBEE 0%, #FFFDE7 50%, #E8F5E9 100%);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
        text-align: center;
    }}

    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 8px;
        border-radius: 10px;
        text-align: center;
        margin: 0 auto 15px auto;
        max-width: 300px;
        font-weight: bold;
        font-size: 0.9rem;
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
        return True
    except Exception as e:
        st.error(f"❌ BŁĄD: {e}")
        return False

# Logo
col1, col2, col3 = st.columns([1.5, 1, 1.5])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

query_params = st.query_params
player_from_url = query_params.get("player", None)

zawodnik = None

if player_from_url in LISTA_ZAWODNIKOW:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {player_from_url.upper()}</div>', unsafe_allow_html=True)
    zawodnik = player_from_url
else:
    zawodnik = st.selectbox("WYBIERZ NAZWISKO:", LISTA_ZAWODNIKOW, index=None, placeholder="Wybierz...")

if zawodnik:
    tab_well, tab_rpe = st.tabs(["📊 WELLNESS", "🏃 RPE"])

    with tab_well:
        st.markdown("""
            <div class="wellness-legend">
                <div style="display: flex; justify-content: space-around;">
                    <div class="legend-item">🔴 1<br><b>ŹLE</b></div>
                    <div class="legend-item">🟡 3<br><b>ŚREDNIO</b></div>
                    <div class="legend-item">🟢 5<br><b>SUPER</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("wellness_form", border=True):
            s1 = st.select_slider("SEN", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("BOLESNOŚĆ", options=[1,2,3,4,5], value=3)
            s4 = st.select_slider("STRES", options=[1,2,3,4,5], value=3)
            
            k = st.text_area("DODATKOWE UWAGI", placeholder="Np. ból prawego uda, słaba jakość snu...")

            if st.form_submit_button("WYŚLIJ RAPORT"):
                timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                save_to_gsheets({
                    "Data": timestamp,
                    "Typ_Raportu": "Wellness",
                    "Zawodnik": zawodnik,
                    "Sen": s1,
                    "Zmeczenie": s2,
                    "Bolesnosc": s3,
                    "Stres": s4,
                    "RPE": None,
                    "Komentarz": k
                })

    with tab_rpe:
        with st.form("rpe_form", border=True):
            rpe = st.slider("INTENSYWNOŚĆ TRENINGU (RPE 0-10)", 0, 10, 5)
            k_rpe = st.text_area("UWAGI DO TRENINGU", placeholder="Np. ciężki trening siłowy, zmęczenie po meczu...")
            
            if st.form_submit_button("WYŚLIJ RPE"):
                timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                save_to_gsheets({
                    "Data": timestamp,
                    "Typ_Raportu": "RPE",
                    "Zawodnik": zawodnik,
                    "Sen": None,
                    "Zmeczenie": None,
                    "Bolesnosc": None,
                    "Stres": None,
                    "RPE": rpe,
                    "Komentarz": k_rpe
                })
