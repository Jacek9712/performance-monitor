import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"  # Główna zieleń klubowa
COLOR_BG = "#F0F7F4"       # Bardzo jasny zielony/szary
COLOR_ACCENT = "#004d26"   # Ciemniejsza zieleń (odcień głębi)
COLOR_WHITE = "#FFFFFF"

# --- LISTA ZAWODNIKÓW ---
LISTA_ZAWODNIKOW = sorted([
    "Jan Kowalski", 
    "Adam Nowak", 
    "Piotr Zieliński", 
    "Marek Sportowiec",
    "Tomasz Bramkarz"
])

# Podstawowa konfiguracja strony Streamlit
st.set_page_config(
    page_title="Warta Poznań - Performance Monitor",
    page_icon="⚽",
    layout="centered"
)

# --- ZAAWANSOWANA STYLIZACJA CSS (POPRAWA WIDOCZNOŚCI SKALI I KOLORÓW) ---
st.markdown(f"""
    <style>
    /* Ogólny styl aplikacji i tło gradientowe */
    .stApp {{
        background: linear-gradient(180deg, #E8F5E9 0%, {COLOR_BG} 100%);
    }}
    
    /* Nagłówki */
    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        text-align: center;
        font-family: 'Arial Black', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* Styl formularza (Biała karta) */
    .stForm {{
        background-color: {COLOR_WHITE} !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 30px rgba(0, 102, 51, 0.1) !important;
        border: 1px solid #e0e0e0 !important;
        border-top: 8px solid {COLOR_PRIMARY} !important;
    }}
    
    /* Styl przycisku */
    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 12px;
        height: 3.5em;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 10px rgba(0, 102, 51, 0.2);
    }}

    /* --- STYLIZACJA SUWAKÓW I SKALI --- */
    
    /* Naprawa widoczności liczb pod suwakami (1-5, 0-10) */
    div[data-baseweb="slider"] div {{
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }}

    /* Szyna suwaka */
    div[data-baseweb="slider"] > div {{
        background-color: #f1f1f1 !important;
        height: 12px !important;
        border-radius: 6px !important;
        border: 1px solid #cccccc !important;
    }}

    /* Kolor wypełnienia (postępu) */
    div[data-baseweb="slider"] > div > div {{
        background: {COLOR_PRIMARY} !important;
    }}
    
    /* Uchwyt suwaka */
    div[data-baseweb="slider"] button {{
        background-color: #FFFFFF !important;
        border: 4px solid {COLOR_PRIMARY} !important;
        width: 26px !important;
        height: 26px !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.3) !important;
    }}

    /* Dymek z wartością nad suwakiem */
    div[data-testid="stThumbValue"] {{
        color: #FFFFFF !important;
        font-weight: bold !important;
        background-color: {COLOR_PRIMARY} !important;
        padding: 4px 10px !important;
        border-radius: 5px !important;
        transform: translateY(-10px) !important;
    }}

    /* WYMUSZENIE WIDOCZNOŚCI DLA TRYBU CIEMNEGO */
    @media (prefers-color-scheme: dark) {{
        .stForm {{
            background-color: #FFFFFF !important;
        }}
        /* Czarne napisy na białym tle formularza */
        div[data-testid="stMarkdownContainer"] p, 
        div[data-testid="stMarkdownContainer"] span,
        label, div[data-baseweb="tab"] p, div[data-baseweb="slider"] div {{
            color: #000000 !important;
        }}
        /* Naprawa kontrastu inputów */
        textarea, input {{
            color: #000000 !important;
            background-color: #FFFFFF !important;
            border: 1px solid #cccccc !important;
        }}
    }}

    /* Podpowiedzi pod suwakami */
    .slider-hint {{
        font-size: 0.85rem;
        color: #555555;
        margin-top: -10px;
        margin-bottom: 20px;
        font-style: italic;
    }}

    /* Ukrycie stopki */
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- WYŚWIETLANIE LOGO I TYTUŁU ---
logo_path = "herb.png"
col1, col2, col3 = st.columns([1, 0.7, 1])
with col2:
    try:
        st.image(logo_path, use_container_width=True)
    except:
        st.markdown(f"<h2 style='color:{COLOR_PRIMARY}; text-align:center;'>WARTA POZNAŃ</h2>", unsafe_allow_html=True)

st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

# --- POŁĄCZENIE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_gsheets(row_data):
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Arkusz1", data=updated_df)
        st.success("Raport wysłany pomyślnie!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")

# --- WYBÓR ZAWODNIKA ---
query_params = st.query_params
player_from_url = query_params.get("player")

def select_player(key_name):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"<div style='padding:10px; border-radius:10px; border:2px solid {COLOR_PRIMARY}; background-color:#f9f9f9; color:black; margin-bottom:20px;'>"
                    f"Zawodnik: <b>{player_from_url}</b></div>", unsafe_allow_html=True)
        return player_from_url
    return st.selectbox("Wybierz zawodnika", LISTA_ZAWODNIKOW, key=key_name)

# --- INTERFEJS ---
tab1, tab2 = st.tabs(["☀️ PORANNY WELLNESS", "🏃‍♂️ RAPORT RPE"])

with tab1:
    with st.form("form_wellness", clear_on_submit=True):
        st.subheader("Wellness")
        p_well = select_player("well_s")
        
        st.write("---")
        s_sen = st.select_slider("Jakość snu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - bardzo słabo / 5 - bardzo dobrze</p>', unsafe_allow_html=True)
        
        s_zme = st.select_slider("Ogólne zmęczenie", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - wyczerpany / 5 - wypoczęty</p>', unsafe_allow_html=True)
        
        s_bol = st.select_slider("Bolesność mięśni", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - duże bóle / 5 - brak bólu</p>', unsafe_allow_html=True)
        
        s_str = st.select_slider("Poziom stresu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - zestresowany / 5 - spokojny</p>', unsafe_allow_html=True)
        
        kom = st.text_area("Dodatkowe uwagi")
        
        if st.form_submit_button("WYŚLIJ WELLNESS"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "Wellness",
                "Zawodnik": p_well,
                "Sen": s_sen, "Zmeczenie": s_zme, "Bolesnosc": s_bol, "Stres": s_str,
                "RPE": None, "Komentarz": kom
            })

with tab2:
    with st.form("form_rpe", clear_on_submit=True):
        st.subheader("Raport Treningowy")
        p_rpe = select_player("rpe_s")
        
        st.write("---")
        r_val = st.slider("Intensywność treningu (RPE 0-10)", 0, 10, 5)
        st.markdown('<p class="slider-hint">0 - odpoczynek / 10 - maksymalny wysiłek</p>', unsafe_allow_html=True)
        
        kom_r = st.text_area("Uwagi do treningu")
        
        if st.form_submit_button("WYŚLIJ RPE"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE",
                "Zawodnik": p_rpe,
                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None,
                "RPE": r_val, "Komentarz": kom_r
            })

# --- PANEL TRENERA ---
st.divider()
with st.expander("🔐 Panel Trenera"):
    pswd = st.text_input("Hasło", type="password")
    if pswd == "Warta1912":
        data = conn.read(worksheet="Arkusz1", ttl=0)
        st.dataframe(data.tail(15))
