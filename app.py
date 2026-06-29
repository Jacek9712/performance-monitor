mport streamlit as st
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
    "Bartosz Lelito", "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", "Jakub Kendzia", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Karol Łysiak", "Leo Przybylak", 
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

# Próba odczytu z localStorage za pomocą JS
stored_player = st_javascript("localStorage.getItem('warta_player_name');")

zawodnik = None

# Logika wyboru zawodnika:
if st.session_state.manual_selection:
    zawodnik = st.session_state.manual_selection
elif not st.session_state.logout_triggered:
    if player_from_url in LISTA_ZAWODNIKOW:
        zawodnik = player_from_url
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik}');")
    elif stored_player in LISTA_ZAWODNIKOW:
        zawodnik = stored_player

# --- ZAAWANSOWANA STYLIZACJA CSS ---
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
    
    .custom-header {{
        text-align: center;
        margin-bottom: 10px;
    }}

    h1 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 1px;
        font-size: 1.8rem !important;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        align-items: center;
        width: 100%;
        margin: 0 auto;
        padding: 10px 0;
    }}
    
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #d1d9e6 !important;
        padding: 25px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }}

    button[kind="formSubmit"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        width: 100% !important;
        border: none !important;
        padding: 10px !important;
        margin-top: 10px !important;
        text-transform: uppercase;
    }}

    .wellness-legend {{
        background: linear-gradient(90deg, #FFEBEE 0%, #FFFDE7 50%, #E8F5E9 100%);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
        text-align: center;
    }}

    .legend-item {{
        flex: 1;
        font-size: 0.8rem;
    }}

    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 8px;
        border-radius: 10px;
        text-align: center;
        margin: 0 auto 15px auto;
        max-width: 300px;
        font-weight: bold;
        font-size: 0.9rem;
    }}

    .already-sent {{
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        font-weight: bold;
        border: 2px solid #C8E6C9;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def get_data_cached(worksheet_name="Arkusz1"):
    try:
        return conn.read(worksheet=worksheet_name)
    except:
        return None

def check_today_report(zawodnik, typ):
    try:
        df = get_data_cached("Arkusz1")
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

# --- DYNAMICZNE POBIERANIE PLANU NA DZIŚ ---
def get_today_gym_plan():
    try:
        df_plans = conn.read(worksheet="Plany", ttl=10)
        if df_plans is None or df_plans.empty:
            return None
        
        # Formatowanie daty dla porównania
        df_plans['Data_dt'] = pd.to_datetime(df_plans['Data'], errors='coerce').dt.date
        dzisiaj = datetime.now(PL_TZ).date()
        
        plan_today = df_plans[df_plans['Data_dt'] == dzisiaj]
        if not plan_today.empty:
            # Pobieramy ćwiczenia z wiersza
            row = plan_today.iloc[0]
            cwiczenia = []
            for col in ['Cwiczenie_1', 'Cwiczenie_2', 'Cwiczenie_3', 'Cwiczenie_4', 'Cwiczenie_5']:
                if col in df_plans.columns and pd.notna(row[col]) and str(row[col]).strip() != "":
                    cwiczenia.append(str(row[col]))
            return cwiczenia
    except Exception as e:
        pass
    return None

def save_to_gsheets(row_data):
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        
        if df is None:
            st.error("⚠️ BŁĄD POŁĄCZENIA: Nie można zweryfikować bazy. Twoje dane NIE zostały wysłane. Spróbuj ponownie za chwilę.")
            return False
            
        if df.empty:
            st.error("⚠️ KRYTYCZNY BŁĄD ODCZYTU: Baza danych tymczasowo zwróciła 0 wierszy (błąd połączenia z Google API). "
                     "Zapis został ZABLOKOWANY, aby CHRONIĆ Twoje dotychczasowe dane przed wymazaniem. Spróbuj ponownie za chwilę!")
            return False
            
        df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        
        juz_jest = df[
            (df['Zawodnik'] == row_data['Zawodnik']) & 
            (df['Typ_Raportu'] == row_data['Typ_Raportu']) & 
            (df['Data_dt'].dt.date == dzisiaj)
        ]
        
        df = df.drop(columns=['Data_dt'], errors='ignore')
        
        if not juz_jest.empty:
            st.warning("⚠️ Twój dzisiejszy raport został już zarejestrowany chwilę temu! Nie musisz wysyłać go ponownie.")
            st.cache_data.clear()
            time.sleep(1.5)
            return True
            
        # Bezpiecznie łączymy i dbamy o dynamiczne kolumny ćwiczeń
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        conn.update(worksheet="Arkusz1", data=updated_df)
        
        st.cache_data.clear()
        st.success("✔ RAPORT WYSŁANY!")
        st.balloons()
        return True
    except Exception as e:
        st.error(f"❌ KRYTYCZNY BŁĄD ZAPISU: {e}")
        return False

# Logo i Nagłówek
col1, col2, col3 = st.columns([1.5, 1, 1.5])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

# Interfejs logowania / wyboru
if zawodnik:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {zawodnik.upper()}</div>', unsafe_allow_html=True)
    if st.button("Wyloguj (Zmień zawodnika)"):
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
        time.sleep(0.5)
        st.rerun()

if zawodnik:
    tab_well, tab_rpe, tab_gym = st.tabs(["📊 WELLNESS", "🏃 RPE", "🏋️ SIŁOWNIA"])

    with tab_well:
        if check_today_report(zawodnik, "Wellness"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.2rem; margin-bottom: 10px;">✅ CZEŚĆ {zawodnik.split()[0]}!</p>
                    <p>TWÓJ DZISIEJSZY RAPORT WELLNESS ZOSTAŁ JUŻ WYSŁANY.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="wellness-legend">
                    <div style="display: flex; justify-content: space-around;">
                        <div class="legend-item">🔴 1<br><b>ŹLE</b></div>
                        <div class="legend-item">🟡 3<br><b>ŚREDNIO</b></div>
                        <div class="legend-item">🟢 5<br><b>SUPER</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            with st.form("wellness_form", border=True):
                s1 = st.select_slider("SEN", options=[1,2,3,4,5], value=3)
                s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
                s3 = st.select_slider("BOLESNOŚĆ", options=[1,2,3,4,5], value=3)
                s4 = st.select_slider("STRES", options=[1,2,3,4,5], value=3)
                k = st.text_area("DODATKOWE UWAGI", placeholder="Np. ból prawego uda...")

                if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik,
                        "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k
                    }):
                        st.rerun()

    with tab_rpe:
        if check_today_report(zawodnik, "RPE"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.2rem; margin-bottom: 10px;">✅ CZEŚĆ {zawodnik.split()[0]}!</p>
                    <p>TWÓJ DZISIEJSZY RAPORT RPE ZOSTAŁ JUŻ WYSŁANY.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            with st.form("rpe_form", border=True):
                st.markdown("<p style='text-align: center;'>PODAJ INTENSYWNOŚĆ TRENINGU</p>", unsafe_allow_html=True)
                rpe = st.slider("SKALA RPE (0-10)", 0, 10, 5)
                k_rpe = st.text_area("UWAGI DO TRENINGU", placeholder="Jak się czułeś?")
                
                if st.form_submit_button("WYŚLIJ RAPORT RPE"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik,
                        "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe, "Komentarz": k_rpe
                    }):
                        st.rerun()

    with tab_gym:
        if check_today_report(zawodnik, "Silownia"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.2rem; margin-bottom: 10px;">🏋️ WITAJ {zawodnik.split()[0]}!</p>
                    <p>TWÓJ RAPORT Z TRENINGU SIŁOWEGO ZOSTAŁ JUŻ ZAPISANY.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            plan_na_dzis = get_today_gym_plan()
            
            if plan_na_dzis is None:
                st.info("ℹ️ BRAK WYMAGANEGO PLANU SIŁOWEGO NA DZIŚ. ODPOCZYWAJ LUB SKONSULTUJ SIĘ Z TRENEREM.")
            else:
                with st.form("gym_form", border=True):
                    st.markdown("<p style='text-align: center; font-size:1.2rem;'>📋 DZISIEJSZY PLAN SIŁOWY</p>", unsafe_allow_html=True)
                    
                    wyniki_cwiczen = []
                    
                    # Generujemy uproszczone, czyste pola na zrealizowany ciężar dla każdego ćwiczenia z planu
                    for i, cwiczenie in enumerate(plan_na_dzis):
                        st.markdown(f"#### 💪 ĆWICZENIE {i+1}")
                        st.markdown(f"**Trening docelowy (narzucony przez Trenera):**\n> {cwiczenie}")
                        
                        col_g1, col_g2 = st.columns([2, 1])
                        with col_g1:
                            obciazenie = st.text_input(f"Zrealizowany ciężar / obciążenie (kg)", placeholder="np. 80, 85, 85, 90 kg", key=f"obc_{i}")
                        with col_g2:
                            uwagi_cw = st.text_input(f"Komentarz / uwagi do ćwiczenia", placeholder="np. zapas 1 powt.", key=f"uw_cw_{i}")
                        
                        # Budowanie czystego, ustrukturyzowanego raportu z jednego ćwiczenia
                        raport_jednego_cwiczenia = (
                            f"{cwiczenie} -> Zrealizowano: {obciazenie if obciazenie else 'Nie podano'} "
                            f"(Uwagi: {uwagi_cw if uwagi_cw else 'Brak'})"
                        )
                        wyniki_cwiczen.append(raport_jednego_cwiczenia)
                        st.markdown("---")
                    
                    rpe_gym = st.slider("OGÓLNA INTENSYWNOŚĆ CAŁEJ SIŁOWNI (RPE 0-10)", 0, 10, 5, key="gym_rpe_slider")
                    k_gym = st.text_area("OGÓLNE UWAGI DO TRENINGU", placeholder="Np. cały trening zrobiony zgodnie z planem, dobre samopoczucie...")
                    
                    if st.form_submit_button("WYŚLIJ RAPORT SIŁOWNI"):
                        # Łączymy wszystkie odpowiedzi do jednej czytelnej notatki
                        kompletny_raport_silowy = " || ".join(wyniki_cwiczen)
                        if k_gym:
                            kompletny_raport_silowy += f" || Ogólne uwagi: {k_gym}"
                            
                        timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                        if save_to_gsheets({
                            "Data": timestamp, "Typ_Raportu": "Silownia", "Zawodnik": zawodnik,
                            "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe_gym, "Komentarz": kompletny_raport_silowy
                        }):
                            st.rerun()
