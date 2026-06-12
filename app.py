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

# Słownik pomocniczy skali RPE dla lepszego zrozumienia przez zawodnika
RPE_DESC = {
    0: "0 - Brak wysiłku (odpoczynek)",
    1: "1 - Bardzo, bardzo lekki",
    2: "2 - Bardzo lekki",
    3: "3 - Lekki wysiłek",
    4: "4 - Umiarkowany",
    5: "5 - Średni / Dość ciężki",
    6: "6 - Ciężki",
    7: "7 - Bardzo ciężki",
    8: "8 - Ekstremalnie ciężki",
    9: "9 - Prawie maksymalny",
    10: "10 - Maksymalny (całkowite wyczerpanie)"
}

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

# --- MECHANIZM ZAPAMIĘTYWANIA ZAWODNIKA (PWA FIX) ---
query_params = st.query_params
player_from_url = query_params.get("player", None)

# Pobranie wartości z localStorage za pomocą JS
stored_player = st_javascript("localStorage.getItem('warta_player_name');")

zawodnik = None

# Logika wyboru zawodnika (odporna na opóźnienia JS)
if st.session_state.manual_selection:
    zawodnik = st.session_state.manual_selection
elif not st.session_state.logout_triggered:
    if player_from_url in LISTA_ZAWODNIKOW:
        zawodnik = player_from_url
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik}');")
    elif isinstance(stored_player, str) and stored_player in LISTA_ZAWODNIKOW:
        zawodnik = stored_player

# --- ZAAWANSOWANA STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;600;800&display=swap');
    
    /* Główne tło i bazowy font */
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Globalny, czytelny krój pisma dla formularzy i opisów */
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span, li {{ 
        font-family: 'Inter', sans-serif !important;
        color: {COLOR_TEXT};
    }}
    
    /* Nagłówki z czcionką Anton (efekt plakatu sportowego) */
    .custom-header h1, .anton-title, .login-info {{
        font-family: 'Anton', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .custom-header {{
        text-align: center;
        margin-bottom: 10px;
    }}

    h1 {{ 
        color: {COLOR_PRIMARY} !important; 
        margin: 0;
        font-size: 2.2rem !important;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        align-items: center;
        width: 100%;
        margin: 0 auto;
        padding: 10px 0;
    }}
    
    /* Stylizacja formularza mobilnego */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #d1d9e6 !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }}

    /* Przyciski wysyłania */
    button[kind="formSubmit"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        font-family: 'Anton', sans-serif !important;
        font-size: 1.2rem !important;
        border-radius: 12px !important;
        width: 100% !important;
        border: none !important;
        padding: 12px !important;
        margin-top: 15px !important;
        text-transform: uppercase;
        transition: background 0.3s ease;
    }}
    
    button[kind="formSubmit"]:hover {{
        background-color: {COLOR_SECONDARY} !important;
    }}

    /* Legenda Wellness */
    .wellness-legend {{
        background: linear-gradient(90deg, #FFEBEE 0%, #FFFDE7 50%, #E8F5E9 100%);
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #C8E6C9;
        margin-bottom: 20px;
        text-align: center;
    }}

    .legend-item {{
        flex: 1;
        font-size: 0.75rem;
        font-weight: 600;
    }}

    /* Informacja o zalogowanym zawodniku */
    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 10px;
        border-radius: 12px;
        text-align: center;
        margin: 0 auto 15px auto;
        max-width: 340px;
        font-size: 1.1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}

    /* Karta potwierdzenia */
    .already-sent {{
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        font-weight: 600;
        border: 2px solid #C8E6C9;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# Połączenie z Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def get_data_cached():
    """Krótki cache zapobiegający przeciążeniu API przy przeładowaniach."""
    try:
        return conn.read(worksheet="Arkusz1")
    except Exception:
        return None

def check_today_report(zawodnik_nazwa, typ_raportu):
    """Sprawdza, czy dzisiaj wysłano już dany typ raportu."""
    try:
        df = get_data_cached()
        if df is None or df.empty:
            return False
        
        # Bezpieczna konwersja daty
        df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        
        exists = df[
            (df['Zawodnik'] == zawodnik_nazwa) & 
            (df['Typ_Raportu'] == typ_raportu) & 
            (df['Data_dt'].dt.date == dzisiaj)
        ]
        
        return not exists.empty
    except Exception:
        return False

def save_to_gsheets(row_data):
    """Bezpieczny mechanizm zapisu z weryfikacją struktury przed aktualizacją."""
    try:
        # Pobieramy aktualne dane w trybie real-time (bez cache)
        df = conn.read(worksheet="Arkusz1", ttl=0)
        
        # Jeżeli arkusz jest pusty, tworzymy pusty DataFrame z odpowiednimi kolumnami
        if df is None or df.empty:
            df = pd.DataFrame(columns=[
                "Data", "Typ_Raportu", "Zawodnik", 
                "Sen", "Zmeczenie", "Bolesnosc", "Stres", "RPE", "Komentarz"
            ])
            
        # Dodajemy nowy rekord
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Wypychamy zmiany
        conn.update(worksheet="Arkusz1", data=updated_df)
        
        # Czyszczenie pamięci cache i sukces
        st.cache_data.clear()
        st.success("✔ RAPORT ZOSTAŁ WYSŁANY POMYŚLNIE!")
        st.balloons()
        return True
    except Exception as e:
        st.error(f"❌ KRYTYCZNY BŁĄD ZAPISU: {e}. Zgłoś problem trenerowi.")
        return False

# --- LOGO I NAGŁÓWEK ---
col1, col2, col3 = st.columns([1.5, 1.2, 1.5])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

# --- PANEL WYBORU ZAWODNIKA / LOGOWANIA ---
if zawodnik:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {zawodnik.upper()}</div>', unsafe_allow_html=True)
    
    # Przycisk wylogowania ze zmniejszonym, estetycznym stylem pod informacją
    col_out_1, col_out_2, col_out_3 = st.columns([1, 1.2, 1])
    with col_out_2:
        if st.button("Zmień zawodnika", use_container_width=True):
            st.query_params.clear()
            st_javascript("localStorage.removeItem('warta_player_name');")
            st.session_state.logout_triggered = True
            st.session_state.manual_selection = None
            st.rerun()
else:
    # Stylizowane okno logowania
    st.markdown("<p style='text-align: center; font-weight: 600;'>Witaj w panelu monitoringu. Wybierz swój profil:</p>", unsafe_allow_html=True)
    zawodnik_wybor = st.selectbox("WYBIERZ NAZWISKO:", LISTA_ZAWODNIKOW, index=None, placeholder="Wybierz z listy...")
    
    if zawodnik_wybor:
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik_wybor}');")
        st.session_state.manual_selection = zawodnik_wybor
        st.session_state.logout_triggered = False 
        time.sleep(0.3)
        st.rerun()

# --- FORMULARZE ZGŁOSZENIOWE (DLA ZALOGOWANEGO GRACZA) ---
if zawodnik:
    tab_well, tab_rpe = st.tabs(["📊 WELLNESS", "🏃 RPE"])

    # --- KARTA WELLNESS ---
    with tab_well:
        if check_today_report(zawodnik, "Wellness"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.3rem; font-family: 'Anton', sans-serif; margin-bottom: 10px;">CZEŚĆ {zawodnik.split()[0].upper()}!</p>
                    <p>Twój dzisiejszy raport <b>WELLNESS</b> został już zarejestrowany. Odpoczywaj!</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="wellness-legend">
                    <div style="display: flex; justify-content: space-around;">
                        <div class="legend-item">🔴 1<br>Bardzo źle</div>
                        <div class="legend-item">🟡 3<br>Średnio</div>
                        <div class="legend-item">🟢 5<br>Doskonale</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            with st.form("wellness_form", border=True):
                s1 = st.select_slider("JAKOŚĆ SNU", options=[1,2,3,4,5], value=3)
                s2 = st.select_slider("POZIOM ZMĘCZENIA", options=[1,2,3,4,5], value=3)
                s3 = st.select_slider("BOLESNOŚĆ MIĘŚNIOWA (DOMS)", options=[1,2,3,4,5], value=3)
                s4 = st.select_slider("POZIOM STRESU / SAMOPOCZUCIE", options=[1,2,3,4,5], value=3)
                k = st.text_area("DODATKOWE UWAGI / DOLEGLIWOŚCI", placeholder="Np. lekki ból w przywodzicielu lewym, słabszy sen...")

                if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik,
                        "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k
                    }):
                        st.rerun()

    # --- KARTA RPE ---
    with tab_rpe:
        if check_today_report(zawodnik, "RPE"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.3rem; font-family: 'Anton', sans-serif; margin-bottom: 10px;">CZEŚĆ {zawodnik.split()[0].upper()}!</p>
                    <p>Twój dzisiejszy raport <b>RPE (obciążenie treningowe)</b> został pomyślnie wysłany.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            with st.form("rpe_form", border=True):
                st.markdown("<p style='text-align: center; font-weight: 600;'>OCEŃ INTENSYWNOŚĆ DZISIEJSZEGO TRENINGU</p>", unsafe_allow_html=True)
                
                # Suwak RPE
                rpe_val = st.slider("SKALA RPE (0 - 10)", 0, 10, 5)
                
                # Dynamiczna, tekstowa interpretacja RPE pod suwakiem
                st.info(f"Wybrałeś poziom: **{RPE_DESC[rpe_val]}**")
                
                k_rpe = st.text_area("UWAGI DO TRENINGU / CZAS TRWANIA (MIN)", placeholder="Np. Trening wyrównawczy, 60 minut...")
                
                if st.form_submit_button("WYŚLIJ RAPORT RPE"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik,
                        "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe_val, "Komentarz": k_rpe
                    }):
                        st.rerun()
