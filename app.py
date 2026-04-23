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

# --- EKSTREMALNA STYLIZACJA CSS (NAPRAWA ETYKIET I ODSTĘPÓW + CZCIONKA ANTON) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');

    /* Ogólny styl aplikacji */
    .stApp {{
        background-color: {COLOR_BG} !important;
    }}
    
    /* Nagłówki z czcionką Anton */
    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        text-align: center;
        font-family: 'Anton', sans-serif !important;
        font-weight: 400; /* Anton ma domyślnie jedną wagę */
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* WYMUSZENIE JASNEGO FORMULARZA */
    .stForm {{
        background-color: #FFFFFF !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #eeeeee !important;
        border-top: 10px solid {COLOR_PRIMARY} !important;
    }}
    
    /* Kolor tekstu dla etykiet głównych */
    label p {{
        color: #000000 !important;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
    }}

    /* --- FINALNA NAPRAWA SLIDERÓW (ETYKIETY 1-5 i 0-10) --- */
    
    /* Usunięcie tła pod cyframi i ich pozycjonowanie */
    div[data-baseweb="slider"] [role="presentation"] div,
    div[data-baseweb="slider"] [data-testid="stSliderTickBar"] div {{
        background-color: transparent !important;
        background: transparent !important;
        color: #000000 !important;
        font-size: 1.1rem !important;
        font-weight: 900 !important;
        opacity: 1 !important;
        /* Subtelne przesunięcie, by nie nachodziło na opis poniżej */
        margin-top: 8px !important;
        text-shadow: 2px 2px 2px #FFFFFF, -2px -2px 2px #FFFFFF, 2px -2px 2px #FFFFFF, -2px 2px 2px #FFFFFF !important;
    }}

    /* Zwiększenie wysokości całego kontenera suwaka, aby zrobić miejsce */
    div[data-baseweb="slider"] {{
        margin-bottom: 25px !important;
    }}

    /* Stylizacja szyny */
    div[data-baseweb="slider"] > div {{
        background-color: #e0e0e0 !important;
        height: 12px !important;
        border-radius: 6px !important;
    }}

    /* Kolor postępu (zielony) */
    div[data-baseweb="slider"] > div > div {{
        background: {COLOR_PRIMARY} !important;
    }}
    
    /* Uchwyt suwaka */
    div[data-baseweb="slider"] button {{
        background-color: #FFFFFF !important;
        border: 4px solid {COLOR_PRIMARY} !important;
        width: 28px !important;
        height: 28px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
    }}

    /* Dymek z wartością nad suwakiem */
    div[data-testid="stThumbValue"] {{
        background-color: #333333 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        padding: 2px 8px !important;
    }}

    /* Przycisk wysyłania z czcionką Anton */
    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY} !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        height: 4em !important;
        font-family: 'Anton', sans-serif !important;
        font-size: 1.3rem !important;
        text-transform: uppercase;
        border: none !important;
        margin-top: 20px !important;
        letter-spacing: 1px;
    }}

    /* Ukrycie elementów Streamlit */
    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- WYŚWIETLANIE LOGO I TYTUŁU ---
col1, col2, col3 = st.columns([1, 0.7, 1])
with col2:
    try:
        st.image("herb.png", use_container_width=True)
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
p_url = query_params.get("player")

def select_player(key_name):
    if p_url and p_url in LISTA_ZAWODNIKOW:
        st.markdown(f"""
            <div style='padding:15px; border-radius:12px; border:2px solid {COLOR_PRIMARY}; background-color:#f0f7f4; color:black; margin-bottom:20px; text-align:center;'>
                Aktualnie wypełnia: <br><b style='font-size:1.4rem; color:{COLOR_PRIMARY};'>{p_url}</b>
            </div>
        """, unsafe_allow_html=True)
        return p_url
    return st.selectbox("Wybierz zawodnika:", LISTA_ZAWODNIKOW, key=key_name)

# --- INTERFEJS GŁÓWNY ---
tab1, tab2 = st.tabs(["☀️ PORANNY WELLNESS", "🏃‍♂️ RAPORT RPE"])

with tab1:
    with st.form("form_wellness", clear_on_submit=True):
        st.subheader("Wellness")
        p_well = select_player("well_s")
        
        st.write("---")
        s_sen = st.select_slider("Jakość snu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="color:#000000; font-size:0.85rem; margin-top:5px; margin-bottom:25px;">1 - bardzo słabo / 5 - idealnie</p>', unsafe_allow_html=True)
        
        s_zme = st.select_slider("Ogólne zmęczenie", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="color:#000000; font-size:0.85rem; margin-top:5px; margin-bottom:25px;">1 - wyczerpany / 5 - pełen energii</p>', unsafe_allow_html=True)
        
        s_bol = st.select_slider("Bolesność mięśni", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="color:#000000; font-size:0.85rem; margin-top:5px; margin-bottom:25px;">1 - duży ból / 5 - brak bólu</p>', unsafe_allow_html=True)
        
        s_str = st.select_slider("Poziom stresu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p style="color:#000000; font-size:0.85rem; margin-top:5px; margin-bottom:25px;">1 - wysoki stres / 5 - pełen spokój</p>', unsafe_allow_html=True)
        
        kom = st.text_area("Uwagi (opcjonalnie)")
        
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
        st.subheader("Obciążenie Treningowe")
        p_rpe = select_player("rpe_s")
        
        st.write("---")
        r_val = st.slider("Intensywność (RPE 0-10)", 0, 10, 5)
        st.markdown('<p style="color:#000000; font-size:0.85rem; margin-top:5px; margin-bottom:25px;">0 - odpoczynek / 10 - wysiłek ekstremalny</p>', unsafe_allow_html=True)
        
        kom_r = st.text_area("Komentarz do treningu")
        
        if st.form_submit_button("WYŚLIJ RPE"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE",
                "Zawodnik": p_rpe,
                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None,
                "RPE": r_val, "Komentarz": kom_r
            })

# --- PANEL ADMINISTRACYJNY ---
st.divider()
with st.expander("🔐 Dane"):
    if st.text_input("Hasło", type="password") == "Warta1912":
        try:
            data = conn.read(worksheet="Arkusz1", ttl=0)
            st.dataframe(data.tail(20), use_container_width=True)
        except:
            st.warning("Baza danych jest pusta.")
