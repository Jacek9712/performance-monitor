import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń
COLOR_BG = "#E8F5E9"        # Bardzo jasna zieleń (tło strony)
COLOR_TEXT = "#121212"      # Prawie czarny (tekst)

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

st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="wide")

# --- STYLIZACJA CSS (FIX DLA TRYBU NOCNEGO I KOLORYSTYKI) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    /* Wymuszenie jasnego tła całej strony - nawet w trybie nocnym */
    .stApp {{ 
        background-color: {COLOR_BG} !important; 
    }}

    /* Ukrywanie brandingu Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    [data-testid="stToolbar"] {{visibility: hidden !important;}}
    
    /* Stylizacja czcionek i kolorów tekstu */
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT} !important;
    }}
    
    /* Nagłówki */
    h1, h2, h3 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        text-transform: uppercase;
        margin-bottom: 1rem;
    }}
    
    /* Kontener Logo */
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        padding: 20px; 
        background-color: white;
        border-radius: 0 0 30px 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }}
    
    /* Biały formularz - kontrastuje z zielonym tłem */
    [data-testid="stForm"], .stTabs {{
        background-color: #FFFFFF !important; 
        padding: 25px !important; 
        border-radius: 20px !important; 
        border: 2px solid {COLOR_PRIMARY} !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
        max-width: 700px;
        margin: 0 auto;
    }}

    /* Zakładki (Tabs) */
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        color: {COLOR_TEXT} !important;
        font-size: 1.1rem !important;
    }}
    
    button[aria-selected="true"] {{
        border-bottom: 4px solid {COLOR_PRIMARY} !important;
        color: {COLOR_PRIMARY} !important;
    }}

    /* Przyciski */
    .stButton>button {{
        width: 100%; 
        background-color: {COLOR_PRIMARY} !important; 
        color: #FFFFFF !important;
        height: 3.5em !important; 
        font-size: 1.2rem !important; 
        border-radius: 12px !important;
        text-transform: uppercase;
        border: none !important;
        margin-top: 10px;
    }}

    /* Fix dla suwaków w trybie nocnym */
    div[data-testid="stSlider"] p {{
        color: {COLOR_TEXT} !important;
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
        st.success("✔ RAPORT WYSŁANY POMYŚLNIE!")
    except Exception as e:
        st.error(f"❌ BŁĄD WYSYŁANIA: {e}")

# Pobieranie parametrów URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

def select_player(key):
    default_index = 0
    if player_from_url in LISTA_ZAWODNIKOW:
        default_index = LISTA_ZAWODNIKOW.index(player_from_url)
    return st.selectbox("ZAWODNIK:", LISTA_ZAWODNIKOW, index=default_index, key=key)

# Wyświetlanie Logo na górze
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
col_l1, col_l2, col_l3 = st.columns([3, 1, 3])
with col_l2:
    st.image(LOGO_PATH, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

_, center_col, _ = st.columns([1, 4, 1])

with center_col:
    tab1, tab2 = st.tabs(["☀️ WELLNESS (RANO)", "🏃‍♂️ RPE (PO TRENINGU)"])

    with tab1:
        with st.form("wellness_form", clear_on_submit=True):
            p = select_player("w_player")
            st.write("---")
            s1 = st.select_slider("JAKOŚĆ SNU", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("POZIOM ENERGII", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("STAN MIĘŚNIOWY", options=[1,2,3,4,5], value=3)
            s4 = st.select_slider("NASTRÓJ / STRES", options=[1,2,3,4,5], value=3)
            k = st.text_area("UWAGI LUB DOLEGLIWOŚCI")
            if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "Wellness", "Zawodnik": p, "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k})

    with tab2:
        with st.form("rpe_form", clear_on_submit=True):
            p = select_player("r_player")
            st.write("---")
            r = st.slider("INTENSYWNOŚĆ TRENINGU (RPE)", 0, 10, 5)
            st.info("0: Odpoczynek | 5: Ciężko | 10: Max wysiłek")
            k = st.text_area("KOMENTARZ DO TRENINGU")
            if st.form_submit_button("WYŚLIJ RAPORT RPE"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "RPE", "Zawodnik": p, "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": r, "Komentarz": k})

# --- ADMIN PANEL ---
st.write("<br><br>", unsafe_allow_html=True)
with st.expander("🔐 PANEL SZTABU"):
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        admin_pass = st.text_input("HASŁO:", type="password")
        if st.button("ZALOGUJ"):
            if admin_pass == "Warta1912":
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("BŁĄD")
    else:
        df_data = conn.read(worksheet="Arkusz1", ttl=0)
        st.dataframe(df_data.sort_index(ascending=False), use_container_width=True)
        if st.button("WYLOGUJ"):
            st.session_state["authenticated"] = False
            st.rerun()
