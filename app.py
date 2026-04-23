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

# --- EKSTREMALNA STYLIZACJA CSS (FIX DLA WIDOCZNOŚCI ETYKIET) ---
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
    
    /* WYMUSZENIE JASNEGO FORMULARZA */
    .stForm {{
        background-color: #FFFFFF !important;
        padding: 25px !important;
        border-radius: 15px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e0e0e0 !important;
        border-top: 8px solid {COLOR_PRIMARY} !important;
    }}
    
    /* Kolor tekstu dla etykiet głównych */
    label p {{
        color: #000000 !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }}

    /* --- STYLIZACJA RADIO (WELLNESS) --- */
    /* Zmieniamy Wellness na poziome przyciski dla 100% czytelności */
    div[data-testid="stMarkdownContainer"] p {{
        color: #000000 !important;
    }}
    
    /* --- STYLIZACJA SLIDERA (RPE) --- */
    /* Liczby pod suwakiem 0-10 */
    div[data-baseweb="slider"] [role="presentation"] div {{
        color: #000000 !important;
        font-size: 1.1rem !important;
        font-weight: 900 !important;
        background-color: transparent !important; /* Usuwamy zielone tło */
        margin-top: 12px !important;
        opacity: 1 !important;
    }}

    /* Szyna suwaka - musi być jasna */
    div[data-baseweb="slider"] > div {{
        background-color: #e0e0e0 !important;
        height: 12px !important;
    }}

    /* Pasek postępu - zielony */
    div[data-baseweb="slider"] > div > div {{
        background: {COLOR_PRIMARY} !important;
    }}
    
    /* Uchwyt suwaka */
    div[data-baseweb="slider"] button {{
        background-color: #FFFFFF !important;
        border: 4px solid {COLOR_PRIMARY} !important;
        width: 28px !important;
        height: 28px !important;
    }}

    /* Wartość nad suwakiem */
    div[data-testid="stThumbValue"] {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-size: 1rem !important;
        padding: 5px 10px !important;
        border-radius: 5px !important;
    }}

    /* Przycisk wysyłania */
    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY} !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        height: 3.5em !important;
        border-radius: 10px !important;
        border: none !important;
    }}

    /* Ukrycie zbędnych elementów */
    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- LOGO I TYTUŁ ---
col1, col2, col3 = st.columns([1, 0.7, 1])
with col2:
    try:
        st.image("herb.png", use_container_width=True)
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
p_url = query_params.get("player")

def select_player(key_name):
    if p_url and p_url in LISTA_ZAWODNIKOW:
        st.markdown(f"<div style='text-align:center; color:black; margin-bottom:15px;'>Zawodnik: <b>{p_url}</b></div>", unsafe_allow_html=True)
        return p_url
    return st.selectbox("Wybierz zawodnika:", LISTA_ZAWODNIKOW, key=key_name)

# --- INTERFEJS ---
tab1, tab2 = st.tabs(["☀️ WELLNESS", "🏃‍♂️ RPE"])

with tab1:
    with st.form("form_well", clear_on_submit=True):
        st.subheader("Poranny Wellness")
        p_well = select_player("w_s")
        st.write("---")
        
        # Wellness 1-5 jako poziome przyciski (Radio) - 100% widoczności
        s_sen = st.radio("Jakość snu (1-5)", [1, 2, 3, 4, 5], index=2, horizontal=True)
        s_zme = st.radio("Zmęczenie (1-5)", [1, 2, 3, 4, 5], index=2, horizontal=True)
        s_bol = st.radio("Bolesność mięśni (1-5)", [1, 2, 3, 4, 5], index=2, horizontal=True)
        s_str = st.radio("Poziom stresu (1-5)", [1, 2, 3, 4, 5], index=2, horizontal=True)
        
        kom = st.text_area("Uwagi")
        
        if st.form_submit_button("WYŚLIJ WELLNESS"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "Wellness", "Zawodnik": p_well,
                "Sen": s_sen, "Zmeczenie": s_zme, "Bolesnosc": s_bol, "Stres": s_str,
                "RPE": None, "Komentarz": kom
            })

with tab2:
    with st.form("form_rpe", clear_on_submit=True):
        st.subheader("Raport Treningowy")
        p_rpe = select_player("r_s")
        st.write("---")
        
        # RPE jako suwak 0-10 z poprawionymi etykietami
        r_val = st.slider("Intensywność (RPE 0-10)", 0, 10, 5)
        st.markdown('<p style="color:black; font-size:0.8rem;">0 - brak zmęczenia | 10 - wysiłek maksymalny</p>', unsafe_allow_html=True)
        
        kom_r = st.text_area("Komentarz do treningu")
        
        if st.form_submit_button("WYŚLIJ RPE"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE", "Zawodnik": p_rpe,
                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None,
                "RPE": r_val, "Komentarz": kom_r
            })

# --- PANEL TRENERA ---
with st.expander("🔐 Dane"):
    if st.text_input("Hasło", type="password") == "Warta1912":
        st.dataframe(conn.read(worksheet="Arkusz1", ttl=0).tail(10))
