import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import os
import pytz
from streamlit_javascript import st_javascript
import time
import re

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń
COLOR_SECONDARY = "#004d26" # Ciemniejsza zieleń dla kontrastu
COLOR_BG = "#F1F8E9"        # Bardzo jasne zielone tło
COLOR_TEXT = "#1B5E20"      # Ciemnozielony tekst
PL_TZ = pytz.timezone('Europe/Warsaw')

# --- DEFINICJA GRUP TRENINGOWYCH ---
SLOWNIK_GRUP = {
    "Grupa A": [
        "Dima Avdieiev", "Leo Przybylak", "Michał Smoczyński", "Bartosz Piechowiak", 
        "Filip Jakubowski", "Jan Niedzielski", "Kacper Lepczyński", 
        "Kacper Rychert", "Kamil Kumoch", "Karol Łysiak", "Marcel Stefaniak", 
        "Mateusz Stanek", "Patryk Kusztal", "Paweł Kwiatkowski", "Oskar Mazurkiewicz", 
        "Szymon Zalewski", "Tomasz Wojcinowicz"
    ],
    "Grupa B": [
        "Igor Kornobis", "Marcel Zylla"
    ],
    "Grupa C": [
        "Bartosz Lelito", "Jakub Kendzia", "Sebastian Steblecki"
    ]
}

# --- INTELIGENTNA NORMALIZACJA KOLUMN ARKUSZA (ROZWIĄZANIE PROBLEMU ZAPISU) ---
def normalizuj_df_arkusza(df):
    """
    Zaawansowana funkcja normalizująca nagłówki kolumn z Google Sheets do ujednoliconego formatu wewnętrznego.
    Wykrywa słowa kluczowe (np. 'sen', 'zmecz', 'stres'), dzięki czemu kod jest w 100% odporny na 
    niestandardowe nazwy kolumn w arkuszu trenera (np. "Jakość snu", "Sen (1-5)", "Zmęczenie [1-5]").
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    def normalize_string(s):
        if not isinstance(s, str):
            return ""
        s = s.strip().lower()
        replacements = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
        }
        for k, v in replacements.items():
            s = s.replace(k, v)
        return re.sub(r'[^a-z0-9]', '', s)
        
    new_cols = []
    for col in df.columns:
        norm_col = normalize_string(col)
        
        # Elastyczne dopasowanie słów kluczowych (Fuzzy Matching)
        if "data" in norm_col or "date" in norm_col or "time" in norm_col:
            new_cols.append("Data")
        elif "typ" in norm_col:
            new_cols.append("Typ_Raportu")
        elif "zawod" in norm_col or "gracz" in norm_col or "player" in norm_col or "nazw" in norm_col:
            new_cols.append("Zawodnik")
        elif "sen" in norm_col or "sleep" in norm_col:
            new_cols.append("Sen")
        elif "zmec" in norm_col or "fatigue" in norm_col:
            new_cols.append("Zmeczenie")
        elif "bol" in norm_col or "sore" in norm_col or "zakwas" in norm_col:
            new_cols.append("Bolesnosc")
        elif "stres" in norm_col or "stress" in norm_col:
            new_cols.append("Stres")
        elif "rpe" in norm_col or "intens" in norm_col:
            new_cols.append("RPE")
        elif "komen" in norm_col or "uwag" in norm_col or "note" in norm_col:
            new_cols.append("Komentarz")
        else:
            new_cols.append(col)
    
    df.columns = new_cols
    return df

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
    "Adrian Wnuk", "Bartosz Lelito", "Bartosz Piechowiak", "Dima Avdieiev", "Filip Jakubowski", 
    "Igor Kornobis", "Jakub Kendzia", "Jan Niedzielski", 
    "Kacper Lepczyński", "Kacper Rychert", "Kamil Kumoch", 
    "Karol Łysiak", "Leo Przybylak", "Marcel Stefaniak", "Marcel Zylla", 
    "Mateusz Stanek", "Michał Smoczyński", "Patryk Kusztal", "Paweł Kwiatkowski", 
    "Oskar Mazurkiewicz", "Sebastian Steblecki", "Szymon Zalewski", "Tomasz Wojcinowicz"
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

    /* Stylizacja sekcji terminarza */
    .calendar-day-card {{
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-left: 5px solid {COLOR_PRIMARY};
        border-radius: 8px;
        padding: 12px 15px;
        margin-bottom: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }}
    .calendar-day-card.today {{
        border-left: 5px solid #D32F2F; /* Czerwony kolor dla wyróżnienia "DZIŚ" */
        background-color: #FFFDE7;     /* Delikatnie żółte tło dla dzisiejszego dnia */
    }}
    .calendar-date {{
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 4px;
    }}
    .calendar-day-name {{
        font-size: 1.1rem;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        text-transform: uppercase;
    }}
    .calendar-day-name.today-text {{
        color: #D32F2F;
    }}
    
    /* Stylizacja sekcji regeneracji / aktywności alternatywnych */
    .recovery-activity-box {
        background-color: #E8F5E9;
        border: 1px solid #C8E6C9;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        color: #2E7D32;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def get_data_cached(worksheet_name="Arkusz1"):
    try:
        df = conn.read(worksheet=worksheet_name)
        if worksheet_name == "Arkusz1" and df is not None:
            df = normalizuj_df_arkusza(df)
        return df
    except Exception as e:
        st.error(f"⚠️ Błąd pobierania danych z arkusza '{worksheet_name}': {e}")
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
    except Exception as e:
        st.error(f"⚠️ Błąd podczas weryfikacji raportu: {e}")
        return False

# --- ARCHITEKTURA PRIORYTETÓW PLANU NA DANY DZIEŃ (Dla Grup i Indywidualnych) ---
def get_gym_plan_for_date(nazwisko_gracza, target_date):
    try:
        df_plans = conn.read(worksheet="Plany", ttl=10)
        if df_plans is None or df_plans.empty:
            return None
        
        df_plans['Data_dt'] = pd.to_datetime(df_plans['Data'], errors='coerce').dt.date
        
        # Filtrujemy plany na wskazany dzień
        plany_dnia = df_plans[df_plans['Data_dt'] == target_date]
        if plany_dnia.empty:
            return None
            
        grupa_gracza = pobierz_grupe_zawodnika(nazwisko_gracza)
        
        if 'Grupa_lub_Zawodnik' not in plany_dnia.columns:
            plan_wybrany = plany_dnia.iloc[0]
        else:
            # 1. NAJWYŻSZY PRIORYTET: Plan Indywidualny
            plan_indywidualny = plany_dnia[plany_dnia['Grupa_lub_Zawodnik'] == nazwisko_gracza]
            
            if not plan_indywidualny.empty:
                plan_wybrany = plan_indywidualny.iloc[0]
            else:
                # 2. DRUGI PRIORYTET: Plan dla Grupy Treningowej gracza
                plan_grupowy = plany_dnia[plany_dnia['Grupa_lub_Zawodnik'] == grupa_gracza]
                
                if not plan_grupowy.empty:
                    plan_wybrany = plan_grupowy.iloc[0]
                else:
                    # 3. TRZECI PRIORYTET: Plan ogólny ("Wszyscy" lub pusta komórka)
                    plan_ogolny = plany_dnia[
                        (plany_dnia['Grupa_lub_Zawodnik'].isna()) | 
                        (plany_dnia['Grupa_lub_Zawodnik'] == "Wszyscy") | 
                        (plany_dnia['Grupa_lub_Zawodnik'] == "")
                    ]
                    if not plan_ogolny.empty:
                        plan_wybrany = plan_ogolny.iloc[0]
                    else:
                        return None
        
        # Wyciągamy ćwiczenia z wybranego planu
        cwiczenia = []
        for col in ['Cwiczenie_1', 'Cwiczenie_2', 'Cwiczenie_3', 'Cwiczenie_4', 'Cwiczenie_5']:
            if col in df_plans.columns and pd.notna(plan_wybrany[col]) and str(plan_wybrany[col]).strip() != "":
                cwiczenia.append(str(plan_wybrany[col]))
        return cwiczenia
    except Exception as e:
        pass
    return None

def get_today_gym_plan(nazwisko_gracza):
    dzisiaj = datetime.now(PL_TZ).date()
    return get_gym_plan_for_date(nazwisko_gracza, dzisiaj)

def save_to_gsheets(row_data):
    try:
        df_original = conn.read(worksheet="Arkusz1", ttl=0)
        
        if df_original is None:
            st.error("⚠️ BŁĄD POŁĄCZENIA: Nie można zweryfikować bazy. Twoje dane NIE zostały wysłane. Spróbuj ponownie za chwilę.")
            return False
            
        if df_original.empty:
            st.error("⚠️ KRYTYCZNY BŁĄD ODCZYTU: Baza danych tymczasowo zwróciła 0 wierszy (błąd połączenia z Google API). "
                     "Zapis został ZABLOKOWANY, aby CHRONIĆ Twoje dotychczasowe dane przed wymazaniem. Spróbuj ponownie za chwilę!")
            return False
            
        oryginalne_kolumny = list(df_original.columns)
        df_internal = normalizuj_df_arkusza(df_original)
        
        df_internal['Data_dt'] = pd.to_datetime(df_internal['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        
        juz_jest = df_internal[
            (df_internal['Zawodnik'] == row_data['Zawodnik']) & 
            (df_internal['Typ_Raportu'] == row_data['Typ_Raportu']) & 
            (df_internal['Data_dt'].dt.date == dzisiaj)
        ]
        
        df_internal = df_internal.drop(columns=['Data_dt'], errors='ignore')
        
        if not juz_jest.empty:
            st.warning("⚠️ Twój dzisiejszy raport został już zarejestrowany chwilę temu! Nie musisz wysyłać go ponownie.")
            st.cache_data.clear()
            time.sleep(1.5)
            return True
            
        row_data_cleaned = {k: ("" if v is None else v) for k, v in row_data.items()}
        new_row = pd.DataFrame([row_data_cleaned])
        updated_df_internal = pd.concat([df_internal, new_row], ignore_index=True)
        
        standard_to_original = {}
        
        def normalize_string(s):
            if not isinstance(s, str):
                return ""
            s = s.strip().lower()
            replacements = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
            for k, v in replacements.items():
                s = s.replace(k, v)
            return re.sub(r'[^a-z0-9]', '', s)
            
        for orig_col in oryginalne_kolumny:
            norm = normalize_string(orig_col)
            if "data" in norm or "date" in norm or "time" in norm:
                standard_to_original["Data"] = orig_col
            elif "typ" in norm:
                standard_to_original["Typ_Raportu"] = orig_col
            elif "zawod" in norm or "gracz" in norm or "player" in norm or "nazw" in norm:
                standard_to_original["Zawodnik"] = orig_col
            elif "sen" in norm or "sleep" in norm:
                standard_to_original["Sen"] = orig_col
            elif "zmec" in norm or "fatigue" in norm:
                standard_to_original["Zmeczenie"] = orig_col
            elif "bol" in norm or "sore" in norm or "zakwas" in norm:
                standard_to_original["Bolesnosc"] = orig_col
            elif "stres" in norm or "stress" in norm:
                standard_to_original["Stres"] = orig_col
            elif "rpe" in norm or "intens" in norm:
                standard_to_original["RPE"] = orig_col
            elif "komen" in norm or "uwag" in norm or "note" in norm:
                standard_to_original["Komentarz"] = orig_col
        
        final_cols = []
        for col in updated_df_internal.columns:
            if col in standard_to_original:
                final_cols.append(standard_to_original[col])
            else:
                final_cols.append(col)
        updated_df_internal.columns = final_cols
        
        conn.update(worksheet="Arkusz1", data=updated_df_internal)
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
    grupa_zawodnika = pobierz_grupe_zawodnika(zawodnik)
    st.markdown(f'<div class="login-info">ZALOGOWANO: {zawodnik.upper()} ({grupa_zawodnika.upper()})</div>', unsafe_allow_html=True)
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
    tab_well, tab_rpe, tab_gym, tab_cal = st.tabs(["📊 WELLNESS", "🏃 RPE", "🏋️ SIŁOWNIA", "📅 MIKROCYKL"])

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
                s1 = int(st.select_slider("SEN", options=[1,2,3,4,5], value=3))
                s2 = int(st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3))
                s3 = int(st.select_slider("BOLESNOŚĆ", options=[1,2,3,4,5], value=3))
                s4 = int(st.select_slider("STRES", options=[1,2,3,4,5], value=3))
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
            plan_na_dzis = get_today_gym_plan(zawodnik)
            
            if plan_na_dzis is None:
                st.info("ℹ️ BRAK WYMAGANEGO PLANU NA DZIŚ DLA TWOJEJ GRUPY. ODPOCZYWAJ LUB SKONSULTUJ SIĘ Z TRENEREM.")
            else:
                # --- SPRAWDZENIE, CZY DZISIEJSZY PLAN TO TYLKO REGENERACJA / BRAK ĆWICZEŃ SIŁOWYCH ---
                czy_tylko_regeneracja = True
                for cw in plan_na_dzis:
                    if "[SERIE:" in cw:
                        czy_tylko_regeneracja = False
                        break
                
                if czy_tylko_regeneracja:
                    # Jeśli w planie są wpisy, ale bez dopisku serii (czyli np. "Rolowanie", "Rozciąganie")
                    st.markdown("""
                        <div class="recovery-activity-box">
                            <h3 style="margin-top:0px; color:#2E7D32;">🌿 TWÓJ DZISIEJSZY PLAN ODNOWY BIOLOGICZNEJ / REGENERACJI</h3>
                            <p>Dziś nie masz zaplanowanej tradycyjnej siłowni. Wykonaj poniższe zalecenia Sztabu Medycznego:</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    for idx, akt in enumerate(plan_na_dzis):
                        st.markdown(f"**🟢 Zadanie {idx+1}:** {akt}")
                        
                    st.markdown("---")
                    with st.form("recovery_report_form", border=True):
                        st.markdown("<p style='text-align: center; font-size:1rem;'>ZAREJESTRUJ REALIZACJĘ ODNOWY</p>", unsafe_allow_html=True)
                        rpe_rec = st.slider("Jak oceniasz swoje samopoczucie po regeneracji (0-10)?", 0, 10, 5)
                        k_rec = st.text_area("Dodatkowe uwagi do regeneracji", placeholder="Np. czuję lepszą elastyczność w mięśniach...")
                        
                        if st.form_submit_button("POTWIERDŹ REALIZACJĘ REGENERACJI"):
                            zestaw_aktywnosci = " || ".join([f"Regeneracja: {x}" for x in plan_na_dzis])
                            if k_rec:
                                zestaw_aktywnosci += f" || Uwagi: {k_rec}"
                                
                            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                            if save_to_gsheets({
                                "Data": timestamp, "Typ_Raportu": "Silownia", "Zawodnik": zawodnik,
                                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe_rec, "Komentarz": zestaw_aktywnosci
                            }):
                                st.rerun()
                else:
                    # Tradycyjny formularz siłowy, jeśli chociaż jedno ćwiczenie ma zdefiniowane [SERIE:X]
                    with st.form("gym_form", border=True):
                        st.markdown("<p style='text-align: center; font-size:1.2rem;'>📋 DEDYKOWANY RAPORT SIŁOWY</p>", unsafe_allow_html=True)
                        
                        wyniki_cwiczen = []
                        
                        for i, cwiczenie in enumerate(plan_na_dzis):
                            # Jeśli element planu to np. "Odprawa wideo" bez serii
                            szukana = re.search(r"\[SERIE:(\d+)\]", cwiczenie)
                            
                            if not szukana:
                                # Element o charakterze regeneracji / aktywności pomocniczej wewnątrz planu
                                st.markdown(f"#### 🌿 AKTYWNOŚĆ POMOCNICZA / REGENERACJA {i+1}")
                                st.markdown(f"**Zalecenie:** {cwiczenie.upper()}")
                                wyniki_cwiczen.append(f"{cwiczenie} -> Zrealizowano")
                                st.markdown("---")
                                continue
                                
                            liczba_serii = int(szukana.group(1))
                            czysta_nazwa_cw = re.sub(r"\[SERIE:\d+\]", "", cwiczenie).strip()
                            
                            st.markdown(f"#### 💪 ĆWICZENIE {i+1}")
                            st.markdown(f"**Zadanie (cel od Trenera):**\n> {czysta_nazwa_cw.upper()}")
                            
                            seria_cols = st.columns(min(liczba_serii, 5))
                            wpisy_serii = []
                            
                            for s in range(liczba_serii):
                                with seria_cols[s % 5]:
                                    ciezar_serii = st.number_input(
                                        f"S{s+1} (kg)", 
                                        min_value=0.0, 
                                        max_value=350.0, 
                                        value=0.0, 
                                        step=2.5, 
                                        key=f"obc_{i}_{s}"
                                    )
                                    wpisy_serii.append(ciezar_serii)
                                    
                            czyste_liczby_serii = ",".join([str(x) for x in wpisy_serii])
                            raport_jednego_cwiczenia = f"{czysta_nazwa_cw} -> Zrealizowano: {czyste_liczby_serii}"
                            wyniki_cwiczen.append(raport_jednego_cwiczenia)
                            st.markdown("---")
                        
                        rpe_gym = st.slider("OGÓLNA INTENSYWNOŚĆ CAŁEJ JEDNOSTKI (RPE 0-10)", 0, 10, 5, key="gym_rpe_slider")
                        k_gym = st.text_area("OGÓLNE UWAGI DO TRENINGU", placeholder="Np. dobry trening, zapas siły...")
                        
                        if st.form_submit_button("WYŚLIJ RAPORT SIŁOWNI"):
                            kompletny_raport_silowy = " || ".join(wyniki_cwiczen)
                            if k_gym:
                                kompletny_raport_silowy += f" || Ogólne uwagi: {k_gym}"
                                
                            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                            if save_to_gsheets({
                                "Data": timestamp, "Typ_Raportu": "Silownia", "Zawodnik": zawodnik,
                                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe_gym, "Komentarz": kompletny_raport_silowy
                            }):
                                st.rerun()

    with tab_cal:
        st.markdown("### 📋 ROZPIS BIEŻĄCEGO MIKROCYKLU")
        st.write("Sprawdź strukturę treningów siłowych, taktycznych oraz regeneracji rozplanowanych na obecny tydzień.")
        
        # --- LOGIKA WYZNACZANIA PONIEDZIAŁKU AKTYWNEGO MIKROCYKLU ---
        dzis_data = datetime.now(PL_TZ).date()
        dzien_tygodnia_index = dzis_data.weekday()
        poniedzialek_mikrocyklu = dzis_data - timedelta(days=dzien_tygodnia_index)
        
        dni_tygodnia_pl = [
            "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"
        ]
        
        for i, nazwa_dnia in enumerate(dni_tygodnia_pl):
            aktywny_dzien = poniedzialek_mikrocyklu + timedelta(days=i)
            data_str = aktywny_dzien.strftime("%d.%m.%Y")
            
            czy_dzis = (aktywny_dzien == dzis_data)
            
            card_class = "calendar-day-card today" if czy_dzis else "calendar-day-card"
            day_text_class = "calendar-day-name today-text" if czy_dzis else "calendar-day-name"
            dzien_label = f"{nazwa_dnia} (DZIŚ)" if czy_dzis else nazwa_dnia
            
            plan_dnia = get_gym_plan_for_date(zawodnik, aktywny_dzien)
            
            st.markdown(f"""
                <div class="{card_class}">
                    <div class="calendar-date">{data_str}</div>
                    <div class="{day_text_class}">{dzien_label}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if plan_dnia:
                # Sprawdzamy czy ten dzień to tylko regeneracja / inna aktywność
                czy_tylko_reg = True
                for cw in plan_dnia:
                    if "[SERIE:" in cw:
                        czy_tylko_reg = False
                        break
                
                expander_title = "🌿 Zobacz plan odnowy / regeneracji" if czy_tylko_reg else "🏋️ Zobacz plan siłowni"
                
                with st.expander(expander_title, expanded=czy_dzis):
                    for idx, cwiczenie in enumerate(plan_dnia):
                        szukana = re.search(r"\[SERIE:(\d+)\]", cwiczenie)
                        if szukana:
                            liczba_serii = int(szukana.group(1))
                            czysta_nazwa = re.sub(r"\[SERIE:\d+\]", "", cwiczenie).strip()
                            st.markdown(f"**{idx+1}. {czysta_nazwa}** (Serii: {liczba_serii})")
                        else:
                            # Dla regeneracji/aktywności bez serii wyświetla tylko informację tekstową
                            st.markdown(f"**{idx+1}. 🌿 {cwiczenie}**")
            else:
                if i >= 5: # Sobota lub Niedziela
                    st.info("⚽ Dzień meczowy / Wolny od siłowni i regeneracji.")
                else:
                    st.info("ℹ️ Brak zaplanowanej jednostki w tym dniu.")
            
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
