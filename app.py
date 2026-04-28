import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import pytz
from streamlit_javascript import st_javascript
import time

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"
COLOR_SECONDARY = "#004d26"
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')

def get_logo():
    possible_files = ["herb.png", "logo.png", "logo.jpg", "image_b1bd1c.png"]
    for f in possible_files:
        if os.path.exists(f):
            return f
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

LOGO_PATH = get_logo()

LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(
    page_title="Warta Poznań Monitor", 
    page_icon="⚽", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicjalizacja stanu sesji
if "logout_triggered" not in st.session_state:
    st.session_state.logout_triggered = False
if "manual_selection" not in st.session_state:
    st.session_state.manual_selection = None

# --- MECHANIZM ZAPAMIĘTYWANIA ZAWODNIKA ---
query_params = st.query_params
player_from_url = query_params.get("player", None)
stored_player = st_javascript("localStorage.getItem('warta_player_name');")

zawodnik = None

if st.session_state.manual_selection:
    zawodnik = st.session_state.manual_selection
elif not st.session_state.logout_triggered:
    if player_from_url in LISTA_ZAWODNIKOW:
        zawodnik = player_from_url
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik}');")
    elif stored_player in LISTA_ZAWODNIKOW:
        zawodnik = stored_player

# --- STYLIZACJA POD MOBILE (PWA) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    /* Optymalizacja pod ekrany dotykowe */
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    /* Usuwamy zbędne marginesy na mobile */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}

    /* Większe przyciski dla kciuków */
    button {{
        height: 3.5rem !important;
        font-size: 1.1rem !important;
    }}

    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 12px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}

    /* Stylizacja Tabs na mobile */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: #eee;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def get_data_cached():
    try:
        return conn.read(worksheet="Arkusz1")
    except:
        return None

def check_today_report(zawodnik, typ):
    try:
        df = get_data_cached()
        if df is None or df.empty: return False
        df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        exists = df[(df['Zawodnik'] == zawodnik) & (df['Typ_Raportu'] == typ) & (df['Data_dt'].dt.date == dzisiaj)]
        return not exists.empty
    except: return False

def save_to_gsheets(row_data):
    """Bezpieczny zapis z weryfikacją danych przed nadpisaniem arkusza."""
    try:
        # Pobieramy aktualne dane bez cache
        df = conn.read(worksheet="Arkusz1", ttl=0)
        
        # BEZPIECZNIK: Jeśli baza nie została poprawnie odczytana, nie nadpisujemy jej
        if df is None:
            st.error("Błąd połączenia z bazą danych. Twoje dane nie zostały utracone, spróbuj wysłać ponownie za chwilę.")
            return False
            
        updated_df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        conn.update(worksheet="Arkusz1", data=updated_df)
        st.cache_data.clear()
        st.success("✅ WYSŁANO!")
        st.balloons()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu: {e}. Sprawdź połączenie z internetem.")
        return False

# Header
col1, col2, col3 = st.columns([1, 1.2, 1])
with col2:
    st.image(LOGO_PATH, use_container_width=True)

st.markdown(f"<h1 style='text-align:center; color:{COLOR_PRIMARY}; margin-bottom:0;'>WARTA POZNAŃ</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; margin-top:0;'>PERFORMANCE MONITOR</p>", unsafe_allow_html=True)

# Login logic
if zawodnik:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {zawodnik.upper()}</div>', unsafe_allow_html=True)
    if st.button("WYLOGUJ / ZMIEŃ PROFIL"):
        st.query_params.clear()
        st_javascript("localStorage.removeItem('warta_player_name');")
        st.session_state.logout_triggered = True
        st.session_state.manual_selection = None
        st.rerun()
else:
    zawodnik_wybor = st.selectbox("WYBIERZ NAZWISKO:", LISTA_ZAWODNIKOW, index=None, placeholder="Kliknij, aby wybrać...")
    if zawodnik_wybor:
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik_wybor}');")
        st.session_state.manual_selection = zawodnik_wybor
        st.session_state.logout_triggered = False 
        time.sleep(0.5)
        st.rerun()

if zawodnik:
    tab_well, tab_rpe = st.tabs(["📊 WELLNESS", "🏃 RPE"])

    with tab_well:
        if check_today_report(zawodnik, "Wellness"):
            st.info(f"✅ Cześć {zawodnik.split()[0]}, Twój Wellness jest już zapisany.")
        else:
            with st.form("well_form"):
                s1 = st.select_slider("SEN (1-5)", options=[1,2,3,4,5], value=3)
                s2 = st.select_slider("ZMĘCZENIE (1-5)", options=[1,2,3,4,5], value=3)
                s3 = st.select_slider("BOLESNOŚĆ (1-5)", options=[1,2,3,4,5], value=3)
                s4 = st.select_slider("STRES (1-5)", options=[1,2,3,4,5], value=3)
                k = st.text_area("UWAGI / BÓLE", placeholder="Wpisz, jeśli coś Cię boli...")
                if st.form_submit_button("WYŚLIJ WELLNESS"):
                    if save_to_gsheets({
                        "Data": datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "Typ_Raportu": "Wellness", "Zawodnik": zawodnik,
                        "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k
                    }):
                        st.rerun()

    with tab_rpe:
        if check_today_report(zawodnik, "RPE"):
            st.info(f"✅ Cześć {zawodnik.split()[0]}, Twoje RPE jest już zapisane.")
        else:
            with st.form("rpe_form"):
                rpe = st.slider("INTENSYWNOŚĆ (0-10)", 0, 10, 5)
                k_rpe = st.text_area("KOMENTARZ", placeholder="Jak się czułeś na treningu?")
                if st.form_submit_button("WYŚLIJ RPE"):
                    if save_to_gsheets({
                        "Data": datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "Typ_Raportu": "RPE", "Zawodnik": zawodnik,
                        "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe, "Komentarz": k_rpe
                    }):
                        st.rerun()
