import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import pytz
from streamlit_javascript import st_javascript
import time
import re

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń Warty
COLOR_SECONDARY = "#004d26" # Ciemniejsza zieleń dla kontrastu
COLOR_BG = "#F1F8E9"        # Bardzo jasne zielone tło
COLOR_TEXT = "#1B5E20"      # Ciemnozielony tekst
PL_TZ = pytz.timezone('Europe/Warsaw')

# --- DEFINICJA GRUP TRENINGOWYCH ---
SLOWNIK_GRUP = {
    "Bramkarze": ["Dima Avdieiev", "Leo Przybylak", "Michał Smoczyński"],
    "Grupa Siła / Rebuilding": ["Bartosz Lelito", "Jakub Kendzia", "Sebastian Steblecki"],
    "Grupa Prewencja / Powrót po kontuzji": ["Igor Kornobis", "Marcel Zylla"],
    "Grupa Dynamiczna / Moc": [
        "Adrian Wnuk", "Bartosz Piechowiak", "Bartosz Wiktoruk", "Filip Jakubowski", 
        "Filip Tonder", "Filip Waluś", "Iwo Wojciechowski", "Jakub Kosiorek", 
        "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", "Kacper Szymanek", 
        "Kamil Kumoch", "Karol Dziedzic", "Karol Łysiak", "Marcel Stefaniak", 
        "Mateusz Stanek", "Patryk Kusztal", "Paweł Kwiatkowski", "Oskar Mazurkiewicz", 
        "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
    ]
}

# Funkcja do znalezienia grupy zawodnika
def pobierz_grupe_zawodnika(nazwisko_gracza):
    for nazwa_grupy, lista_graczy in SLOWNIK_GRUP.items():
        if nazwisko_gracza in lista_graczy:
            return nazwa_grupy
    return "Grupa Dynamiczna / Moc" # Domyślna grupa

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
    "Adrian Wnuk", "Bartosz Lelito", "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
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

# Bezpieczny odczyt z localStorage za pomocą JS
stored_player = st_javascript("localStorage.getItem('warta_player_name');")

zawodnik = None

# Logika wyboru zawodnika (zapobiega nieskończonym pętlom przy braku gotowości JS)
if st.session_state.manual_selection:
    zawodnik = st.session_state.manual_selection
elif not st.session_state.logout_triggered:
    if player_from_url in LISTA_ZAWODNIKOW:
        zawodnik = player_from_url
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik}');")
    elif stored_player and isinstance(stored_player, str) and stored_player in LISTA_ZAWODNIKOW:
        zawodnik = stored_player

# --- ZAAWANSOWANA STYLIZACJA CSS (POŁĄCZENIE ANTON & INTER DLA WYSOKIEJ CZYTELNOŚCI) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #F1F8E9 100%) !important; 
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Globalna czcionka Inter dla maksymalnej czytelności formularzy i etykiet */
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Inter', sans-serif !important;
        color: {COLOR_TEXT};
    }}
    
    /* Anton dla elementów sportowych, nagłówków i akcentów */
    h1, h2, h3, h4, .custom-header h1, .login-info, button[kind="formSubmit"], .anton-heading {{
        font-family: 'Anton', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
    
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        padding: 25px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }}

    button[kind="formSubmit"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        width: 100% !important;
        border: none !important;
        padding: 12px !important;
        margin-top: 15px !important;
        font-size: 1.1rem !important;
        transition: all 0.2s ease-in-out !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(0, 102, 51, 0.15);
    }}
    
    button[kind="formSubmit"]:hover {{
        background-color: {COLOR_SECONDARY} !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 102, 51, 0.25);
    }}

    button[kind="formSubmit"]:active {{
        transform: translateY(1px);
        box-shadow: 0 2px 4px rgba(0, 102, 51, 0.2);
    }}

    .wellness-legend {{
        background: linear-gradient(90deg, #FFEBEE 0%, #FFFDE7 50%, #E8F5E9 100%);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E0E0E0;
        margin-bottom: 20px;
        text-align: center;
    }}

    .legend-item {{
        flex: 1;
        font-size: 0.85rem;
        font-weight: 600;
    }}

    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 10px;
        border-radius: 12px;
        text-align: center;
        margin: 0 auto 15px auto;
        max-width: 340px;
        font-size: 1.05rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .already-sent {{
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        font-weight: bold;
        border: 2px solid #C8E6C9;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def get_data_cached(worksheet_name="Arkusz1"):
    try:
        return conn.read(worksheet=worksheet_name)
    except Exception as e:
        st.sidebar.error(f"Błąd odczytu bazy: {e}")
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
    except Exception:
        return False

# --- ARCHITEKTURA PRIORYTETÓW PLANU NA DZIŚ ---
def get_today_gym_plan(nazwisko_gracza):
    try:
        df_plans = conn.read(worksheet="Plany", ttl=10)
        if df_plans is None or df_plans.empty:
            return None
        
        df_plans['Data_dt'] = pd.to_datetime(df_plans['Data'], errors='coerce').dt.date
        dzisiaj = datetime.now(PL_TZ).date()
        
        plany_dzis = df_plans[df_plans['Data_dt'] == dzisiaj]
        if plany_dzis.empty:
            return None
            
        grupa_gracza = pobierz_grupe_zawodnika(nazwisko_gracza)
        
        if 'Grupa_lub_Zawodnik' not in plany_dzis.columns:
            plan_wybrany = plany_dzis.iloc[0]
        else:
            # 1. PRIORYTET I: Plan Indywidualny (dedykowany dla konkretnego nazwiska)
            plan_indywidualny = plany_dzis[plany_dzis['Grupa_lub_Zawodnik'] == nazwisko_gracza]
            
            if not plan_indywidualny.empty:
                plan_wybrany = plan_indywidualny.iloc[0]
            else:
                # 2. PRIORYTET II: Plan dla Grupy Treningowej
                plan_grupowy = plany_dzis[plany_dzis['Grupa_lub_Zawodnik'] == grupa_gracza]
                
                if not plan_grupowy.empty:
                    plan_wybrany = plan_grupowy.iloc[0]
                else:
                    # 3. PRIORYTET III: Plan Ogólny ("Wszyscy" lub pusty wpis)
                    plan_ogolny = plany_dzis[
                        (plany_dzis['Grupa_lub_Zawodnik'].isna()) | 
                        (plany_dzis['Grupa_lub_Zawodnik'] == "Wszyscy") | 
                        (plany_dzis['Grupa_lub_Zawodnik'] == "")
                    ]
                    if not plan_ogolny.empty:
                        plan_wybrany = plan_ogolny.iloc[0]
                    else:
                        return None
        
        cwiczenia = []
        for col in ['Cwiczenie_1', 'Cwiczenie_2', 'Cwiczenie_3', 'Cwiczenie_4', 'Cwiczenie_5']:
            if col in df_plans.columns and pd.notna(plan_wybrany[col]) and str(plan_wybrany[col]).strip() != "":
                cwiczenia.append(str(plan_wybrany[col]))
        return cwiczenia
    except Exception as e:
        st.sidebar.warning(f"Nie udało się pobrać dzisiejszego planu siłowni: {e}")
    return None

def save_to_gsheets(row_data):
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        
        if df is None:
            st.error("⚠️ BŁĄD POŁĄCZENIA: Nie można zweryfikować bazy. Spróbuj ponownie.")
            return False
            
        if df.empty:
            st.error("⚠️ KRYTYCZNY BŁĄD ODCZYTU: Baza danych tymczasowo zwróciła 0 wierszy. "
                     "Zapis został zablokowany w celu ochrony istniejących wpisów przed wymazaniem.")
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
            st.warning("⚠️ Twój dzisiejszy raport został już zarejestrowany! Nie musisz wysyłać go ponownie.")
            st.cache_data.clear()
            time.sleep(1.5)
            return True
            
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        conn.update(worksheet="Arkusz1", data=updated_df)
        
        st.cache_data.clear()
        st.success("✔ RAPORT WYSŁANY POMYŚLNIE!")
        st.balloons()
        return True
    except Exception as e:
        st.error(f"❌ KRYTYCZNY BŁĄD ZAPISU: {e}")
        return False

# --- UKŁAD STRONY ---
col1, col2, col3 = st.columns([1.5, 1, 1.5])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

# Interfejs logowania / wyboru zawodnika
if zawodnik:
    grupa_zawodnika = pobierz_grupe_zawodnika(zawodnik)
    st.markdown(f'<div class="login-info">ZALOGOWANO: {zawodnik.upper()}<br><span style="font-size:0.8rem; font-weight:normal;">({grupa_zawodnika.upper()})</span></div>', unsafe_allow_html=True)
    if st.button("Wyloguj (Zmień zawodnika)", use_container_width=True):
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
        time.sleep(0.3)
        st.rerun()

if zawodnik:
    tab_well, tab_rpe, tab_gym = st.tabs(["📊 WELLNESS", "🏃 RPE", "🏋️ SIŁOWNIA"])

    # --- KARTA: WELLNESS ---
    with tab_well:
        if check_today_report(zawodnik, "Wellness"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.4rem; margin-bottom: 10px;" class="anton-heading">✅ Cześć {zawodnik.split()[0]}!</p>
                    <p>Twój dzisiejszy raport WELLNESS został już pomyślnie wysłany.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="wellness-legend">
                    <div style="display: flex; justify-content: space-around;">
                        <div class="legend-item">🔴 1<br>BARDZO ŹLE</div>
                        <div class="legend-item">🟡 3<br>PRZECIĘTNIE</div>
                        <div class="legend-item">🟢 5<br>REWELACYJNIE</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            with st.form("wellness_form", border=True):
                s1 = st.select_slider("JAKOŚĆ SNU (1 - brak snu / bardzo słaby, 5 - głęboki, długi sen)", options=[1,2,3,4,5], value=3)
                s2 = st.select_slider("ZMĘCZENIE OGÓLNE (1 - wycieńczony, 5 - pełen energii)", options=[1,2,3,4,5], value=3)
                s3 = st.select_slider("BOLESNOŚĆ MIĘŚNI / DOMS (1 - silny ból mięśni, 5 - brak dolegliwości)", options=[1,2,3,4,5], value=3)
                s4 = st.select_slider("POZIOM STRESU (1 - silny stres / napięcie, 5 - pełen spokój / relaks)", options=[1,2,3,4,5], value=3)
                k = st.text_area("DODATKOWE UWAGI / MIEJSCE BOLESNOŚCI", placeholder="Np. lekkie kłucie w prawym dwugłowym, zmęczenie po podróży...")

                if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik,
                        "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k
                    }):
                        st.rerun()

    # --- KARTA: RPE ---
    with tab_rpe:
        if check_today_report(zawodnik, "RPE"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.4rem; margin-bottom: 10px;" class="anton-heading">✅ Cześć {zawodnik.split()[0]}!</p>
                    <p>Twój dzisiejszy raport intensywności RPE został już zarejestrowany.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            with st.form("rpe_form", border=True):
                st.markdown("<h4 style='text-align: center; margin-bottom:15px;'>PODAJ INTENSYWNOŚĆ TRENINGU</h4>", unsafe_allow_html=True)
                rpe = st.slider("SKALA RPE (0 - brak wysiłku, 10 - maksymalny wysiłek)", 0, 10, 5)
                k_rpe = st.text_area("UWAGI DO TRENINGU LUB SAMOPOCZUCIA", placeholder="Jak oceniasz dzisiejsze obciążenie?")
                
                if st.form_submit_button("WYŚLIJ RAPORT RPE"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({
                        "Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik,
                        "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe, "Komentarz": k_rpe
                    }):
                        st.rerun()

    # --- KARTA: SIŁOWNIA ---
    with tab_gym:
        if check_today_report(zawodnik, "Silownia"):
            st.markdown(f"""
                <div class="already-sent">
                    <p style="font-size: 1.4rem; margin-bottom: 10px;" class="anton-heading">🏋️ Witaj {zawodnik.split()[0]}!</p>
                    <p>Twój raport z dzisiejszego treningu siłowego został pomyślnie zapisany.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            plan_na_dzis = get_today_gym_plan(zawodnik)
            
            if plan_na_dzis is None:
                st.info("ℹ️ Brak przypisanego planu siłowego na dziś dla Twojej grupy. Odpocznij lub skonsultuj się ze sztabem przygotowania fizycznego.")
            else:
                with st.form("gym_form", border=True):
                    st.markdown("<h3 style='text-align: center; color:#006633;'>📋 DEDYKOWANY RAPORT SIŁOWY</h3>", unsafe_allow_html=True)
                    st.markdown("---")
                    
                    wyniki_cwiczen = []
                    
                    for i, cwiczenie in enumerate(plan_na_dzis):
                        # Wyciągamy liczbę serii z zapisu planu np. "[SERIE:4]"
                        liczba_serii = 4 # Wartość domyślna
                        szukana = re.search(r"\[SERIE:(\d+)\]", cwiczenie)
                        if szukana:
                            liczba_serii = int(szukana.group(1))
                        
                        # Czyścimy techniczną nazwę do wyświetlenia zawodnikowi
                        czysta_nazwa_cw = re.sub(r"\[SERIE:\d+\]", "", cwiczenie).strip()
                        
                        st.markdown(f"#### 💪 ĆWICZENIE {i+1}")
                        st.markdown(f"**Zadanie:** <span style='font-size:1.1rem; color:#006633;'>{czysta_nazwa_cw.upper()}</span>", unsafe_allow_html=True)
                        
                        # Dynamiczne kolumny dla wprowadzania obciążeń
                        seria_cols = st.columns(min(liczba_serii, 5))
                        wpisy_serii = []
                        
                        for s in range(liczba_serii):
                            with seria_cols[s % 5]:
                                ciezar_serii = st.number_input(
                                    f"Seria {s+1} (kg)", 
                                    min_value=0.0, 
                                    max_value=350.0, 
                                    value=0.0, 
                                    step=2.5, 
                                    key=f"obc_{i}_{s}"
                                )
                                wpisy_serii.append(ciezar_serii)
                                
                        # Formatowanie pod PowerBI (np. 80,82.5,85,90)
                        czyste_liczby_serii = ",".join([str(x) for x in wpisy_serii])
                        raport_jednego_cwiczenia = f"{czysta_nazwa_cw} -> Serie: {czyste_liczby_serii}"
                        wyniki_cwiczen.append(raport_jednego_cwiczenia)
                        st.markdown("---")
                    
                    rpe_gym = st.slider("OGÓLNE RPE DLA CAŁEGO TRENINGU SIŁOWEGO (0-10)", 0, 10, 5, key="gym_rpe_slider")
                    k_gym = st.text_area("UWAGI DO DZISIEJSZEJ SESJI", placeholder="Np. świetny flow ruchowy, lekki zapas na przysiadzie...")
                    
                    if st.form_submit_button("WYŚLIJ RAPORT SIŁOWNI"):
                        kompletny_raport_silowy = " || ".join(wyniki_cwiczen)
                        if k_gym:
                            kompletny_raport_silowy += f" || Uwagi zawodnika: {k_gym}"
                            
                        timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                        if save_to_gsheets({
                            "Data": timestamp, "Typ_Raportu": "Silownia", "Zawodnik": zawodnik,
                            "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe_gym, "Komentarz": kompletny_raport_silowy
                        }):
                            st.rerun()
