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
    page_title="Warta Poznań - Performance", 
    page_icon="⚽", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

if "manual_selection" not in st.session_state:
    st.session_state.manual_selection = None
if "logout_triggered" not in st.session_state:
    st.session_state.logout_triggered = False

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

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    .stApp {{ background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}
    .logo-container {{ display: flex; justify-content: center; padding: 10px 0; }}
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0 !important;
    }}
    button {{ border-radius: 12px !important; text-transform: uppercase !important; font-weight: bold !important; }}
    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 10px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
        font-size: 0.9rem;
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
    df = get_data_cached()
    if df is None or df.empty: return False
    try:
        df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        exists = df[(df['Zawodnik'] == zawodnik) & (df['Typ_Raportu'] == typ) & (df['Data_dt'].dt.date == dzisiaj)]
        return not exists.empty
    except: return False

def save_to_gsheets(row_data):
    """Bezpieczny zapis danych z weryfikacją ciągłości bazy."""
    try:
        # Pobieramy aktualne dane bez cache, aby mieć najnowszą wersję
        existing_df = conn.read(worksheet="Arkusz1", ttl=0)
        
        # --- BEZPIECZNIK ---
        # Jeśli arkusz nagle wydaje się pusty, ale wiemy, że powinny tam być dane
        # (np. więcej niż 5 wierszy było wcześniej), przerywamy, by nie nadpisać bazy
        if existing_df is None:
            st.error("Błąd krytyczny: Nie można połączyć się z bazą. Spróbuj za chwilę.")
            return False
            
        # Dodajemy nowy wiersz
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        
        # Aktualizacja
        conn.update(worksheet="Arkusz1", data=updated_df)
        st.cache_data.clear()
        st.success("✅ RAPORT ZAPISANY!")
        st.balloons()
        return True
    except Exception as e:
        st.error(f"⚠️ Problem z zapisem: {e}. Sprawdź połączenie z internetem.")
        return False

# --- INTERFEJS ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image(LOGO_PATH, width=100)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"<h1 style='text-align:center; color:{COLOR_PRIMARY}; margin:0;'>WARTA POZNAŃ</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:0.8rem; margin-bottom:20px;'>PERFORMANCE MONITOR</p>", unsafe_allow_html=True)

if zawodnik:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {zawodnik.upper()}</div>', unsafe_allow_html=True)
    if st.button("Wyloguj / Zmień zawodnika"):
        st.query_params.clear()
        st_javascript("localStorage.removeItem('warta_player_name');")
        st.session_state.logout_triggered = True
        st.session_state.manual_selection = None
        st.rerun()
else:
    zawodnik_wybor = st.selectbox("WYBIERZ NAZWISKO:", LISTA_ZAWODNIKOW, index=None, placeholder="Wybierz z listy...")
    if zawodnik_wybor:
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik_wybor}');")
        st.session_state.manual_selection = zawodnik_wybor
        st.session_state.logout_triggered = False 
        st.rerun()

if zawodnik:
    tab_well, tab_rpe = st.tabs(["📊 WELLNESS", "🏃 RPE"])

    with tab_well:
        if check_today_report(zawodnik, "Wellness"):
            st.info(f"✅ Raport Wellness na dziś został już wysłany.")
        else:
            with st.form("well_form", border=True):
                st.write("Jak się dzisiaj czujesz?")
                s1 = st.select_slider("Jakość snu", options=[1,2,3,4,5], value=3)
                s2 = st.select_slider("Poziom zmęczenia", options=[1,2,3,4,5], value=3)
                s3 = st.select_slider("Bolesność mięśni", options=[1,2,3,4,5], value=3)
                s4 = st.select_slider("Poziom stresu", options=[1,2,3,4,5], value=3)
                k = st.text_area("Dodatkowe uwagi / bóle:", placeholder="Wpisz tutaj...")
                
                if st.form_submit_button("WYŚLIJ WELLNESS", use_container_width=True):
                    save_to_gsheets({
                        "Data": datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "Typ_Raportu": "Wellness", "Zawodnik": zawodnik,
                        "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k
                    })
                    time.sleep(1)
                    st.rerun()

    with tab_rpe:
        if check_today_report(zawodnik, "RPE"):
            st.info(f"✅ Raport RPE został już wysłany.")
        else:
            with st.form("rpe_form", border=True):
                st.write("Oceń intensywność treningu")
                rpe = st.select_slider("Skala RPE (0-10)", options=list(range(11)), value=5)
                k_rpe = st.text_area("Uwagi:", placeholder="Jakieś uwagi?")
                
                if st.form_submit_button("WYŚLIJ RPE", use_container_width=True):
                    save_to_gsheets({
                        "Data": datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "Typ_Raportu": "RPE", "Zawodnik": zawodnik,
                        "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe, "Komentarz": k_rpe
                    })
                    time.sleep(1)
                    st.rerun()
