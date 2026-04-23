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

# --- ZAAWANSOWANA STYLIZACJA CSS (FIX DLA SKRANYCH LICZB I KOLORÓW) ---
st.markdown(f"""
    <style>
    /* Ogólny styl aplikacji */
    .stApp {{
        background-color: {COLOR_BG} !important;
    }}
    
    /* Nagłówki */
    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        text-align: center;
        font-family: 'Arial', sans-serif;
        font-weight: 900;
        text-transform: uppercase;
    }}
    
    /* WYMUSZENIE JASNEGO FORMULARZA - ODPORNOŚĆ NA DARK MODE */
    .stForm {{
        background-color: #FFFFFF !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1) !important;
        border: 2px solid #eeeeee !important;
        border-top: 10px solid {COLOR_PRIMARY} !important;
    }}
    
    /* Wymuszenie koloru tekstu dla etykiet */
    .stForm label, .stForm p, .stForm div, .stForm span {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}

    /* --- STYLIZACJA SUWAKÓW (SLIDERS) --- */
    
    /* NAPRAWA LICZB SKALI (1-5, 0-10) - WYRAŹNE BIAŁE RAMKI */
    div[data-baseweb="slider"] [role="presentation"] div {{
        color: #000000 !important;
        font-size: 1.1rem !important;
        font-weight: 900 !important;
        /* Kluczowa zmiana: białe tło z obramowaniem dla każdej liczby */
        background-color: #FFFFFF !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        border: 2px solid #e0e0e0 !important;
        margin-top: 8px !important; /* Przesunięcie niżej, żeby nie nachodziło na pasek */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        opacity: 1 !important;
    }}

    /* Szyna suwaka - bardzo jasna dla kontrastu */
    div[data-baseweb="slider"] > div {{
        background-color: #f5f5f5 !important;
        height: 16px !important;
        border-radius: 8px !important;
        border: 1px solid #cccccc !important;
    }}

    /* Kolor wypełnienia suwaka (postęp) - ZIELONY */
    div[data-baseweb="slider"] > div > div {{
        background: {COLOR_PRIMARY} !important;
    }}
    
    /* Kółko / Uchwyt suwaka - DUŻE I BIAŁE */
    div[data-baseweb="slider"] button {{
        background-color: #FFFFFF !important;
        border: 5px solid {COLOR_PRIMARY} !important;
        width: 32px !important;
        height: 32px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }}

    /* Dymek z wartością aktualną (nad suwakiem) */
    div[data-testid="stThumbValue"] {{
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
        background-color: {COLOR_PRIMARY} !important;
        padding: 4px 12px !important;
        border-radius: 8px !important;
        border: 2px solid {COLOR_WHITE} !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        transform: translateY(-12px) !important;
    }}

    /* Przycisk wysyłania */
    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY} !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        height: 4em !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border: none !important;
        margin-top: 20px !important;
        box-shadow: 0 5px 15px rgba(0, 102, 51, 0.3) !important;
    }}

    /* Zakładki (Tabs) */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent;
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #FFFFFF;
        border-radius: 10px 10px 0 0;
        border: 1px solid #eeeeee;
        padding: 8px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
    }}
    .stTabs [aria-selected="true"] p {{
        color: white !important;
    }}

    /* Ukrycie zbędnych elementów Streamlit */
    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
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

# --- POŁĄCZENIE Z BAZĄ ---
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
        st.error(f"Błąd zapisu danych: {e}")

# --- WYBÓR ZAWODNIKA ---
query_params = st.query_params
player_from_url = query_params.get("player")

def select_player(key_name):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"""
            <div style='padding:15px; border-radius:12px; border:2px solid {COLOR_PRIMARY}; background-color:#f8fdfa; color:black; margin-bottom:20px; text-align:center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                Zawodnik: <br><b style='font-size:1.4rem; color:{COLOR_PRIMARY};'>{player_from_url}</b>
            </div>
        """, unsafe_allow_html=True)
        return player_from_url
    return st.selectbox("Wybierz zawodnika z listy:", LISTA_ZAWODNIKOW, key=key_name)

# --- INTERFEJS GŁÓWNY ---
tab1, tab2 = st.tabs(["☀️ PORANNY WELLNESS", "🏃‍♂️ RAPORT RPE"])

with tab1:
    with st.form("form_wellness", clear_on_submit=True):
        st.subheader("Wellness")
        p_well = select_player("well_s")
        
        st.write("---")
        # Używamy select_slider dla wellness (1-5)
        s_sen = st.select_slider("Jakość snu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="font-size:0.85rem; color:#666; margin-top:-15px; margin-bottom:20px;">1 - bardzo słabo / 5 - idealnie</p>', unsafe_allow_html=True)
        
        s_zme = st.select_slider("Ogólne zmęczenie", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="font-size:0.85rem; color:#666; margin-top:-15px; margin-bottom:20px;">1 - wyczerpany / 5 - pełen energii</p>', unsafe_allow_html=True)
        
        s_bol = st.select_slider("Bolesność mięśni", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="font-size:0.85rem; color:#666; margin-top:-15px; margin-bottom:20px;">1 - duże ból / 5 - brak bólu</p>', unsafe_allow_html=True)
        
        s_str = st.select_slider("Poziom stresu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="font-size:0.85rem; color:#666; margin-top:-15px; margin-bottom:20px;">1 - wysoki stres / 5 - pełen spokój</p>', unsafe_allow_html=True)
        
        kom = st.text_area("Uwagi (opcjonalnie)")
        
        if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "Wellness",
                "Zawodnik": p_well,
                "Sen": s_sen, "Zmeczenie": s_zme, "Bolesnosc": s_bol, "Stres": s_str,
                "RPE": None, "Komentarz": kom
            })

with tab2:
    with st.form("form_rpe", clear_on_submit=True):
        st.subheader("Obciążenie Treningowe")
        p_rpe = select_player("rpe_s")
        
        st.write("---")
        # Używamy slider dla RPE (0-10)
        r_val = st.slider("Intensywność treningu (RPE 0-10)", 0, 10, 5)
        st.markdown('<p style="font-size:0.85rem; color:#666; margin-top:-15px; margin-bottom:20px;">0 - odpoczynek / 10 - wysiłek maksymalny</p>', unsafe_allow_html=True)
        
        kom_r = st.text_area("Komentarz do treningu")
        
        if st.form_submit_button("WYŚLIJ RAPORT RPE"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE",
                "Zawodnik": p_rpe,
                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None,
                "RPE": r_val, "Komentarz": kom_r
            })

# --- PANEL ADMINISTRACYJNY ---
st.divider()
with st.expander("🔐 Panel Analizy (Dla Trenera)"):
    pswd = st.text_input("Hasło", type="password")
    if pswd == "Warta1912":
        try:
            data = conn.read(worksheet="Arkusz1", ttl=0)
            st.dataframe(data.tail(20), use_container_width=True)
        except:
            st.warning("Brak danych lub błąd połączenia.")
