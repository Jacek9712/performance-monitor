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

# --- ZAAWANSOWANA STYLIZACJA CSS (NAPRAWA KOLORÓW SUWAKÓW) ---
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
    
    /* Styl formularza (White Card z zielonym akcentem) */
    .stForm {{
        background-color: {COLOR_WHITE} !important;
        padding: 40px !important;
        border-radius: 25px !important;
        box-shadow: 0 10px 30px rgba(0, 102, 51, 0.1) !important;
        border-top: 5px solid {COLOR_PRIMARY} !important;
    }}
    
    /* Styl przycisku - Warta Style */
    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 15px;
        height: 3.5em;
        font-weight: bold;
        font-size: 1.1rem;
        border: 2px solid {COLOR_PRIMARY};
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .stButton>button:hover {{
        background-color: {COLOR_ACCENT};
        border-color: {COLOR_ACCENT};
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }}

    /* --- NOWA STYLIZACJA SUWAKÓW (BIEL I ZIELEŃ) --- */
    
    /* Szyna suwaka - teraz biała z zielonym obramowaniem dla kontrastu */
    div[data-baseweb="slider"] > div {{
        background-color: #FFFFFF !important;
        height: 12px !important;
        border-radius: 6px !important;
        border: 1px solid #d1d1d1 !important;
    }}

    /* Kolor wypełnienia (aktywnej części) suwaka - mocna zieleń */
    div[data-baseweb="slider"] > div > div {{
        background: {COLOR_PRIMARY} !important;
    }}
    
    /* Wygląd kółka (uchwytu) suwaka - BIAŁE, DUŻE, ZIELONY RANT */
    div[data-baseweb="slider"] button {{
        background-color: #FFFFFF !important;
        border: 4px solid {COLOR_PRIMARY} !important;
        width: 28px !important;
        height: 28px !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }}

    /* Etykieta wartości nad suwakiem - CZYSTA BIEL I CZARNY TEKST */
    div[data-testid="stThumbValue"] {{
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
        background-color: #FFFFFF !important;
        padding: 5px 12px !important;
        border-radius: 10px !important;
        border: 3px solid {COLOR_PRIMARY} !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
        transform: translateY(-12px) !important;
    }}

    /* --- WYMUSZENIE KOLORÓW DLA TRYBU CIEMNEGO --- */
    @media (prefers-color-scheme: dark) {{
        .stForm {{
            background-color: #FFFFFF !important;
        }}
        /* Teksty muszą być ciemne na białym formularzu */
        div[data-testid="stMarkdownContainer"] p, 
        div[data-testid="stMarkdownContainer"] span,
        label, .stTabs button p {{
            color: #000000 !important;
        }}
        /* Naprawiamy suwaki w Dark Mode */
        div[data-baseweb="slider"] {{
            background-color: transparent !important;
        }}
        div[data-baseweb="slider"] > div {{
            background-color: #FFFFFF !important;
        }}
    }}

    /* Pole tekstowe i Inputy */
    textarea {{
        border: 2px solid #c8e6c9 !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }}
    
    /* Podpowiedzi pod suwakami */
    .slider-hint {{
        font-size: 0.9rem;
        color: #333333;
        margin-top: -12px;
        margin-bottom: 25px;
        font-weight: 600;
        background-color: #FFFFFF;
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #eee;
    }}

    /* Stylizacja zakładek (Tabs) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: #FFFFFF;
        border: 1px solid #e0e0e0;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: {COLOR_PRIMARY};
        font-weight: 600;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        border-color: {COLOR_PRIMARY} !important;
    }}

    /* Ukrycie zbędnych elementów */
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- WYŚWIETLANIE LOGO I TYTUŁU ---
logo_path = "herb.png"
col1, col2, col3 = st.columns([1, 0.8, 1])
with col2:
    try:
        st.image(logo_path, use_container_width=True)
    except:
        st.markdown(f"<h2 style='color:{COLOR_PRIMARY}'>WARTA POZNAŃ</h2>", unsafe_allow_html=True)

st.markdown("<h1>PERFORMANCE MONITOR</h1>", unsafe_allow_html=True)

# --- INICJALIZACJA POŁĄCZENIA ---
def get_connection():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error("Błąd połączenia z Google Sheets.")
        return None

conn = get_connection()

def save_to_gsheets(row_data):
    if conn is None: return
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Arkusz1", data=updated_df)
        st.success("Raport został wysłany do bazy danych!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Wystąpił błąd zapisu: {e}")

# --- OBSŁUGA ZAWODNIKA (URL / SELECTBOX) ---
query_params = st.query_params
player_from_url = query_params.get("player")

def select_player(key_name):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"<div style='padding:15px; background-color:#FFFFFF; border:2px solid {COLOR_PRIMARY}; border-left:8px solid {COLOR_PRIMARY}; border-radius:10px; margin-bottom:20px; color:#000000; font-weight:bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>"
                    f"Zalogowany zawodnik: <span style='color:{COLOR_PRIMARY}; font-size:1.2rem;'>{player_from_url}</span></div>", unsafe_allow_html=True)
        return player_from_url
    return st.selectbox("Wybierz zawodnika z listy", LISTA_ZAWODNIKOW, key=key_name)

# --- ZAKŁADKI INTERFEJSU ---
tab1, tab2 = st.tabs(["☀️ PORANNY WELLNESS", "🏃‍♂️ RAPORT RPE"])

with tab1:
    with st.form("form_wellness", clear_on_submit=True):
        st.subheader("Wellness")
        current_player = select_player("well_sel")
        
        st.write("**Oceń parametry poranne (1-5):**")
        
        sen = st.select_slider("Jakość snu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - bardzo słabo / 5 - idealnie</p>', unsafe_allow_html=True)
        
        zmeczenie = st.select_slider("Ogólne zmęczenie", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - wyczerpany / 5 - pełen energii</p>', unsafe_allow_html=True)
        
        bolesnosc = st.select_slider("Bolesność mięśni", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - bardzo boli / 5 - brak bólu</p>', unsafe_allow_html=True)
        
        stres = st.select_slider("Poziom stresu", options=[1, 2, 3, 4, 5], value=3)
        st.markdown('<p class="slider-hint">1 - wysoki stres / 5 - pełen spokój</p>', unsafe_allow_html=True)
        
        komentarz = st.text_area("Twoje uwagi do samopoczucia")
        
        if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "Wellness",
                "Zawodnik": current_player,
                "Sen": sen, "Zmeczenie": zmeczenie, "Bolesnosc": bolesnosc, "Stres": stres,
                "RPE": None, "Komentarz": komentarz
            })

with tab2:
    with st.form("form_rpe", clear_on_submit=True):
        st.subheader("Obciążenie Treningowe")
        current_player_rpe = select_player("rpe_sel")
        
        st.write("**Oceń intensywność jednostki (Skala RPE):**")
        rpe_value = st.slider("Poziom zmęczenia (0 - nic, 10 - max)", 0, 10, 5)
        st.markdown('<p class="slider-hint">Wartość 10 oznacza ekstremalny wysiłek</p>', unsafe_allow_html=True)
        
        komentarz_rpe = st.text_area("Opisz krótko dzisiejszy trening")
        
        if st.form_submit_button("WYŚLIJ RAPORT RPE"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE",
                "Zawodnik": current_player_rpe,
                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None,
                "RPE": rpe_value, "Komentarz": komentarz_rpe
            })

# --- SEKCJA TRENERA ---
st.divider()
with st.expander("🔐 Panel Analizy (Trener)"):
    pass_input = st.text_input("Hasło dostępu", type="password")
    if pass_input == "Warta1912":
        if conn:
            try:
                view_df = conn.read(worksheet="Arkusz1", ttl=0)
                st.dataframe(view_df.tail(20), use_container_width=True)
                csv = view_df.to_csv(index=False).encode('utf-8')
                st.download_button("Pobierz arkusz .csv", csv, "raporty_warta.csv", "text/csv")
            except:
                st.info("Baza danych jest obecnie pusta.")
    elif pass_input:
        st.error("Nieprawidłowe hasło.")
