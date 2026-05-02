import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import pytz
from streamlit_javascript import st_javascript
import time

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
    "Marcel Stefaniak", "Marcel Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Oskar Mazurkiewicz", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="centered")

# Inicjalizacja stanu sesji
if "logout_triggered" not in st.session_state:
    st.session_state.logout_triggered = False
if "manual_selection" not in st.session_state:
    st.session_state.manual_selection = None

# --- MECHANIZM ZAPAMIĘTYWANIA ZAWODNIKA ---
query_params = st.query_params
player_from_url = query_params.get("player", None)

# Próba odczytu z localStorage za pomocą JS
stored_player = st_javascript("localStorage.getItem('warta_player_name');")

zawodnik = None

# Logika wyboru zawodnika
if st.session_state.manual_selection:
    zawodnik = st.session_state.manual_selection
elif not st.session_state.logout_triggered:
    if player_from_url in LISTA_ZAWODNIKOW:
        zawodnik = player_from_url
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik}');")
    elif stored_player in LISTA_ZAWODNIKOW:
        zawodnik = stored_player

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
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
    
    .custom-header {{ text-align: center; margin-bottom: 10px; }}
    h1 {{ color: {COLOR_PRIMARY} !important; text-transform: uppercase; font-size: 1.8rem !important; }}
    
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #d1d9e6 !important;
        padding: 25px !important;
        border-radius: 20px !important;
    }}

    button[kind="formSubmit"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        width: 100% !important;
        text-transform: uppercase;
    }}

    .wellness-legend {{
        background: linear-gradient(90deg, #FFEBEE 0%, #FFFDE7 50%, #E8F5E9 100%);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
    }}

    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 8px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
        font-weight: bold;
    }}

    .already-sent {{
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #C8E6C9;
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_gsheets(row_data):
    """
    POPRAWIONA FUNKCJA ZAPISU:
    Zabezpiecza przed nadpisaniem bazy 'pustką' w przypadku błędu połączenia.
    """
    try:
        # 1. Odczytujemy aktualne dane (bez cache, aby mieć najświeższą wersję)
        df = conn.read(worksheet="Arkusz1", ttl=0)
        
        # 2. BEZPIECZNIK: Jeśli df jest None, oznacza to błąd API Google
        if df is None:
            st.error("⚠️ BŁĄD KRYTYCZNY: Nie udało się połączyć z bazą danych. Zapis przerwany, aby nie uszkodzić istniejących danych. Spróbuj za chwilę.")
            return False
            
        # 3. Przygotowanie nowego wiersza
        new_row = pd.DataFrame([row_data])
        
        # 4. Łączenie starych danych z nowymi
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # 5. Aktualizacja całego arkusza
        conn.update(worksheet="Arkusz1", data=updated_df)
        
        # 6. Czyszczenie cache, aby inne części aplikacji widziały zmianę
        st.cache_data.clear()
        st.success("✔ RAPORT WYSŁANY POMYŚLNIE!")
        st.balloons()
        return True
    except Exception as e:
        st.error(f"❌ WYSTĄPIŁ BŁĄD PODCZAS ZAPISU: {e}")
        return False

def check_today_report(zawodnik, typ):
    """Sprawdza, czy dany zawodnik wysłał już dzisiaj konkretny raport."""
    try:
        df = conn.read(worksheet="Arkusz1", ttl=5) # Mały cache dla wydajności
        if df is None or df.empty:
            return False
        
        df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        
        exists = df[
            (df['Zawodnik'] == zawodnik) & 
            (df['Typ_Raportu'] == typ) & 
            (df['Data_dt'].dt.date == dzisiaj)
        ]
        return not exists.empty
    except:
        return False

# UI - Nagłówek
st.markdown('<div style="text-align:center;"><img src="'+LOGO_PATH+'" width="80"></div>', unsafe_allow_html=True)
st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

# Logika logowania/wyboru zawodnika
if zawodnik:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {zawodnik.upper()}</div>', unsafe_allow_html=True)
    if st.button("Wyloguj (Zmień zawodnika)"):
        st_javascript("localStorage.removeItem('warta_player_name');")
        st.session_state.manual_selection = None
        st.session_state.logout_triggered = True
        st.rerun()

    tab_well, tab_rpe = st.tabs(["📊 WELLNESS", "🏃 RPE"])

    with tab_well:
        if check_today_report(zawodnik, "Wellness"):
            st.markdown(f'<div class="already-sent">✅ CZEŚĆ {zawodnik.split()[0]}!<br>TWÓJ RAPORT WELLNESS JEST JUŻ W BAZIE.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="wellness-legend">🔴 1 (ŹLE) ... 🟡 3 (ŚREDNIO) ... 🟢 5 (SUPER)</div>', unsafe_allow_html=True)
            with st.form("wellness_form"):
                s1 = st.select_slider("SEN", options=[1,2,3,4,5], value=3)
                s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
                s3 = st.select_slider("BOLESNOŚĆ", options=[1,2,3,4,5], value=3)
                s4 = st.select_slider("STRES", options=[1,2,3,4,5], value=3)
                k = st.text_area("UWAGI", placeholder="Np. ból łydki...")
                if st.form_submit_button("WYŚLIJ WELLNESS"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik,
                        "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k
                    }):
                        time.sleep(1)
                        st.rerun()

    with tab_rpe:
        if check_today_report(zawodnik, "RPE"):
            st.markdown(f'<div class="already-sent">✅ CZEŚĆ {zawodnik.split()[0]}!<br>TWÓJ RAPORT RPE JEST JUŻ W BAZIE.</div>', unsafe_allow_html=True)
        else:
            with st.form("rpe_form"):
                rpe = st.slider("INTENSYWNOŚĆ (0-10)", 0, 10, 5)
                k_rpe = st.text_area("UWAGI DO TRENINGU")
                if st.form_submit_button("WYŚLIJ RPE"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik,
                        "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe, "Komentarz": k_rpe
                    }):
                        time.sleep(1)
                        st.rerun()
else:
    wybor = st.selectbox("WYBIERZ NAZWISKO:", LISTA_ZAWODNIKOW, index=None)
    if wybor:
        st_javascript(f"localStorage.setItem('warta_player_name', '{wybor}');")
        st.session_state.manual_selection = wybor
        st.rerun()
