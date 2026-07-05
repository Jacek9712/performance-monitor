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

# --- GLOBALNA FUNKCJA DO USUWANIA POLSKICH ZNAKÓW ---
def usun_polskie_znaki(s):
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s

# --- EKSTRAKCJA SERII DLA TRENINGU SIŁOWEGO ---
def pobierz_liczbe_serii(cwiczenie_str):
    """
    Wyciąga liczbę serii z tekstu (np. [SERIE:4], 3 serie, 4s, 3x8).
    Jeśli brak dopisku, domyślnie przyjmuje 4 serie dla treningu siłowego.
    """
    text_normalized = usun_polskie_znaki(cwiczenie_str)
    
    szukana_prosta = re.search(r"serie\s*:\s*(\d+)", text_normalized)
    if szukana_prosta:
        return int(szukana_prosta.group(1))
        
    szukana_tekst = re.search(r"(\d+)\s*(?:serii|serie|seria)", text_normalized)
    if szukana_tekst:
        return int(szukana_tekst.group(1))
        
    szukana_s = re.search(r"\b(\d+)\s*s\b", text_normalized)
    if szukana_s:
        return int(szukana_s.group(1))
        
    szukana_x = re.search(r"\b(\d+)\s*x", text_normalized)
    if szukana_x:
        return int(szukana_x.group(1))
        
    return 4

def oczysc_nazwe_cwiczenia(cwiczenie_str):
    """
    Usuwa techniczne dopiski o seriach, by estetycznie wyświetlić nazwę ćwiczenia.
    """
    temp = re.sub(r"\[?SERIE\s*:\s*\d+\]?", "", cwiczenie_str, flags=re.IGNORECASE)
    temp = re.sub(r"\b\d+\s*(?:serii|serie|seria|s|x)\b.*", "", temp, flags=re.IGNORECASE)
    return temp.strip()

# --- INTELIGENTNA NORMALIZACJA KOLUMN ARKUSZA (ZAPIS WELLNESS/RPE) ---
def normalizuj_df_arkusza(df):
    if df is None or df.empty:
        return df
    
    df = df.copy()
    new_cols = []
    for col in df.columns:
        norm_col = re.sub(r'[^a-z0-9]', '', usun_polskie_znaki(col))
        
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
    return "Grupa Dynamiczna / Moc"

# Logo
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

# --- REJESTRACJA ZAWODNIKA ---
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

    /* --- POZIOMY KALENDARZ (CSS GRID) --- */
    .calendar-grid {{
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        width: 100%;
        margin-bottom: 20px;
    }}
    @media (max-width: 900px) {{
        .calendar-grid {{
            grid-template-columns: repeat(4, 1fr);
        }}
    }}
    @media (max-width: 600px) {{
        .calendar-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}
    
    .calendar-cell {{
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        transition: transform 0.2s, box-shadow 0.2s, border 0.2s;
    }}
    .calendar-cell:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}
    .calendar-cell.today {{
        border: 2px solid #D32F2F !important;
        background-color: #FFFDE7 !important;
    }}
    .calendar-cell-header {{
        font-size: 0.85rem;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        text-transform: uppercase;
        margin-bottom: 2px;
    }}
    .calendar-cell-header.today-text {{
        color: #D32F2F !important;
    }}
    .calendar-cell-date {{
        font-size: 0.72rem;
        color: #666;
        margin-bottom: 8px;
    }}
    .calendar-cell-content {{
        display: flex;
        flex-direction: column;
        gap: 4px;
        align-items: stretch;
        text-align: left;
    }}
    
    /* Małe kafelki aktywności w kalendarzu */
    .cal-exercise-tag {{
        background: #E8F5E9;
        color: #2E7D32;
        font-size: 0.68rem;
        padding: 3px 6px;
        border-radius: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-weight: bold;
        border: 1px solid #C8E6C9;
    }}
    .cal-rec-tag {{
        background: #E3F2FD;
        color: #1565C0;
        font-size: 0.68rem;
        padding: 3px 6px;
        border-radius: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-weight: bold;
        border: 1px solid #BBDEFB;
    }}
    .cal-empty-tag {{
        color: #999;
        font-size: 0.68rem;
        text-align: center;
        margin-top: 15px;
        font-style: italic;
    }}
    
    .recovery-activity-box {{
        background-color: #E3F2FD;
        border: 1px solid #BBDEFB;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        color: #0D47A1;
    }}
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

# --- TWARDA SEPARACJA (SIŁOWNIA VS REGENERACJA) ---
def get_gym_plan_for_date(nazwisko_gracza, target_date):
    """
    Pobiera i fizycznie rozdziela plan treningowy opierając się w 100% na nazwach kolumn z Google Sheets:
    - silownia: TYLKO to co wpisano w kolumny zawierające "Cwiczenie"
    - regeneracja: TYLKO to co wpisano w kolumny zawierające "Regeneracja" lub "Odnowa"
    """
    pusty_plan = {"silownia": [], "regeneracja": []}
    
    try:
        df_plans = conn.read(worksheet="Plany", ttl=10)
        if df_plans is None or df_plans.empty:
            return pusty_plan
        
        df_plans['Data_dt'] = pd.to_datetime(df_plans['Data'], errors='coerce').dt.date
        plany_dnia = df_plans[df_plans['Data_dt'] == target_date]
        if plany_dnia.empty:
            return pusty_plan
            
        grupa_gracza = pobierz_grupe_zawodnika(nazwisko_gracza)
        
        if 'Grupa_lub_Zawodnik' not in plany_dnia.columns:
            plan_wybrany = plany_dnia.iloc[0]
        else:
            plan_indywidualny = plany_dnia[plany_dnia['Grupa_lub_Zawodnik'] == nazwisko_gracza]
            if not plan_indywidualny.empty:
                plan_wybrany = plan_indywidualny.iloc[0]
            else:
                plan_grupowy = plany_dnia[plany_dnia['Grupa_lub_Zawodnik'] == grupa_gracza]
                if not plan_grupowy.empty:
                    plan_wybrany = plan_grupowy.iloc[0]
                else:
                    plan_ogolny = plany_dnia[
                        (plany_dnia['Grupa_lub_Zawodnik'].isna()) | 
                        (plany_dnia['Grupa_lub_Zawodnik'] == "Wszyscy") | 
                        (plany_dnia['Grupa_lub_Zawodnik'] == "")
                    ]
                    if not plan_ogolny.empty:
                        plan_wybrany = plan_ogolny.iloc[0]
                    else:
                        return pusty_plan
        
        silownia_list = []
        regeneracja_list = []
        
        # Skanujemy nazwy wszystkich kolumn w Twoim arkuszu
        for col in df_plans.columns:
            val = plan_wybrany[col]
            if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
                continue
                
            col_norm = usun_polskie_znaki(str(col)).replace(" ", "").replace("_", "")
            val_str = str(val).strip()
            
            # Jeśli wpisałeś to do kolumny Cwiczenie_1, Cwiczenie_2 itd.
            if "cwiczenie" in col_norm:
                silownia_list.append(val_str)
                
            # Jeśli wpisałeś to do nowej kolumny "Regeneracja", "Odnowa"
            elif "regeneracja" in col_norm or "odnowa" in col_norm:
                # Rozdzielamy po przecinku lub plusie, jeśli wpisałeś w komórce np. "Sauna + Basen"
                czesci = re.split(r',|;|\|\||\+', val_str)
                for czesc in czesci:
                    if czesc.strip():
                        regeneracja_list.append(czesc.strip())
                        
        return {"silownia": silownia_list, "regeneracja": regeneracja_list}
    except Exception as e:
        pass
    return pusty_plan

def get_today_gym_plan(nazwisko_gracza):
    dzisiaj = datetime.now(PL_TZ).date()
    return get_gym_plan_for_date(nazwisko_gracza, dzisiaj)

def save_to_gsheets(row_data):
    try:
        df_original = conn.read(worksheet="Arkusz1", ttl=0)
        if df_original is None or df_original.empty:
            st.error("⚠️ Błąd bazy danych. Spróbuj ponownie.")
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
            st.warning("⚠️ Twój raport został już wysłany!")
            return True
            
        row_data_cleaned = {k: ("" if v is None else v) for k, v in row_data.items()}
        new_row = pd.DataFrame([row_data_cleaned])
        updated_df_internal = pd.concat([df_internal, new_row], ignore_index=True)
        
        standard_to_original = {}
        for orig_col in oryginalne_kolumny:
            norm = usun_polskie_znaki(orig_col)
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
        st.error(f"❌ BŁĄD ZAPISU: {e}")
        return False

# Nagłówek i Logo
col1, col2, col3 = st.columns([1.5, 1, 1.5])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

# Panel logowania
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
            st.markdown(
                f'<div class="already-sent">'
                f'<p style="font-size: 1.2rem; margin-bottom: 10px;">✅ CZEŚĆ {zawodnik.split()[0]}!</p>'
                f'<p>TWÓJ DZISIEJSZY RAPORT WELLNESS ZOSTAŁ JUŻ WYSŁANY.</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="wellness-legend">'
                f'<div style="display: flex; justify-content: space-around;">'
                f'<div class="legend-item">🔴 1<br><b>ŹLE</b></div>'
                f'<div class="legend-item">🟡 3<br><b>ŚREDNIO</b></div>'
                f'<div class="legend-item">🟢 5<br><b>SUPER</b></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

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
            st.markdown(
                f'<div class="already-sent">'
                f'<p style="font-size: 1.2rem; margin-bottom: 10px;">✅ CZEŚĆ {zawodnik.split()[0]}!</p>'
                f'<p>TWÓJ DZISIEJSZY RAPORT RPE ZOSTAŁ JUŻ WYSŁANY.</p>'
                f'</div>',
                unsafe_allow_html=True
            )
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
            st.markdown(
                f'<div class="already-sent">'
                f'<p style="font-size: 1.2rem; margin-bottom: 10px;">🏋️ WITAJ {zawodnik.split()[0]}!</p>'
                f'<p>TWÓJ RAPORT Z TRENINGU SIŁOWEGO ZOSTAŁ JUŻ ZAPISANY.</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            full_plan = get_today_gym_plan(zawodnik)
            silowe = full_plan["silownia"]
            
            if not silowe:
                st.markdown(
                    f'<div class="recovery-activity-box" style="background-color: #E3F2FD; border: 1px solid #BBDEFB; color: #0D47A1;">'
                    f'<h3 style="margin-top:0px; color:#0D47A1;">🌿 BRAK SIŁOWNI W DNIU DZISIEJSZYM</h3>'
                    f'<p>Dziś nie masz zaplanowanego tradycyjnego treningu siłowego.</p>'
                    f'<p style="font-weight: bold; margin-bottom: 0px;">Przejdź do zakładki "📅 PLAN TYGODNIA", aby sprawdzić ewentualną regenerację!</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                with st.form("gym_form", border=True):
                    st.markdown("<p style='text-align: center; font-size:1.4rem; margin-bottom: 20px;'>📋 TWÓJ DZIENNIK TRENINGU SIŁOWEGO</p>", unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 0.85rem; color: #555; margin-bottom: 15px;'>Wpisz obciążenie w kilogramach (kg) dla każdej serii:</p>", unsafe_allow_html=True)
                    
                    wyniki_cwiczen = []
                    
                    for i, cwiczenie in enumerate(silowe):
                        liczba_serii = pobierz_liczbe_serii(cwiczenie)
                        czysta_nazwa_cw = oczysc_nazwe_cwiczenia(cwiczenie)
                        
                        st.markdown(f"#### 💪 {i+1}. {czysta_nazwa_cw.upper()}")
                        
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
                                
                        czyste_liczby_serii = ",".join([str(x) for x in wpisy_serii])
                        wyniki_cwiczen.append(f"{czysta_nazwa_cw} -> Serie: {czyste_liczby_serii}")
                        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    rpe_gym = st.slider("OGÓLNA INTENSYWNOŚĆ TRENINGU (RPE 0-10)", 0, 10, 5, key="gym_rpe_slider")
                    k_gym = st.text_area("OGÓLNE UWAGI DO TRENINGU", placeholder="Np. dobry trening, zapas siły...")
                    
                    if st.form_submit_button("WYŚLIJ RAPORT SIŁOWY"):
                        kompletny_raport_elementy = [f"🏋️ {wynik}" for wynik in wyniki_cwiczen]
                        kompletny_raport_silowy = " || ".join(kompletny_raport_elementy)
                        if k_gym:
                            kompletny_raport_silowy += f" || Ogólne uwagi: {k_gym}"
                            
                        timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                        if save_to_gsheets({
                            "Data": timestamp, "Typ_Raportu": "Silownia", "Zawodnik": zawodnik,
                            "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe_gym, "Komentarz": kompletny_raport_silowy
                        }):
                            st.rerun()

    with tab_cal:
        st.markdown("### 📋 PLAN TYGODNIA")
        st.write("Sprawdź rozkład zajęć, regeneracji i siłowni w tym tygodniu.")
        
        dzis_data = datetime.now(PL_TZ).date()
        dzien_tygodnia_index = dzis_data.weekday()
        poniedzialek_mikrocyklu = dzis_data - timedelta(days=dzien_tygodnia_index)
        
        dni_tygodnia_pl = [
            "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"
        ]
        
        # --- GENEROWANIE POZIOMEGO PREZENTACYJNEGO KALENDARZA ---
        grid_html = '<div class="calendar-grid">'
        
        for i, nazwa_dnia in enumerate(dni_tygodnia_pl):
            aktywny_dzien = poniedzialek_mikrocyklu + timedelta(days=i)
            data_str = aktywny_dzien.strftime("%d.%m")
            
            czy_dzis = (aktywny_dzien == dzis_data)
            cell_class = "calendar-cell today" if czy_dzis else "calendar-cell"
            header_class = "calendar-cell-header today-text" if czy_dzis else "calendar-cell-header"
            dzien_label = f"{nazwa_dnia} (DZIŚ)" if czy_dzis else nazwa_dnia
            
            plan_dnia = get_gym_plan_for_date(zawodnik, aktywny_dzien)
            silowe_dnia = plan_dnia["silownia"]
            regen_dnia = plan_dnia["regeneracja"]
            
            content_tags = ""
            tag_count = 0
            
            # Kafelki regeneracji (🌿)
            for rg in regen_dnia:
                if tag_count >= 3: break
                czysta_nazwa_rg = oczysc_nazwe_cwiczenia(rg)
                if len(czysta_nazwa_rg) > 18: czysta_nazwa_rg = czysta_nazwa_rg[:15] + "..."
                content_tags += f'<div class="cal-rec-tag">🌿 {czysta_nazwa_rg}</div>'
                tag_count += 1
                
            # Kafelki siłowni (🏋️)
            for sl in silowe_dnia:
                if tag_count >= 3: break
                czysta_nazwa_sl = oczysc_nazwe_cwiczenia(sl)
                if len(czysta_nazwa_sl) > 18: czysta_nazwa_sl = czysta_nazwa_sl[:15] + "..."
                content_tags += f'<div class="cal-exercise-tag">🏋️ {czysta_nazwa_sl}</div>'
                tag_count += 1
                
            total_elements = len(silowe_dnia) + len(regen_dnia)
            if total_elements > 3:
                content_tags += f'<div style="font-size:0.65rem; color:#666; text-align:center; margin-top:2px;">+ {total_elements - 3} więcej</div>'
            elif total_elements == 0:
                content_tags = '<div class="cal-empty-tag">Brak planu (Wolne)</div>'
                
            grid_html += f'<div class="{cell_class}"><div class="{header_class}">{dzien_label}</div><div class="calendar-date">{data_str}</div><div class="calendar-cell-content">{content_tags}</div></div>'
            
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)
        
        # --- SZCZEGÓŁOWY PODGLĄD AKTYWNEGO DNIA ---
        st.markdown("<br><h4>🔍 SZCZEGÓŁOWY PODGLĄD DNIA</h4>", unsafe_allow_html=True)
        wybrany_dzien_pl = st.selectbox(
            "WYBIERZ DZIEŃ Z MIKROCYKLU, ABY ZOBACZYĆ PEŁNY PLAN:",
            dni_tygodnia_pl,
            index=dzien_tygodnia_index,
            key="day_selector_microcycle"
        )
        
        wybrany_index = dni_tygodnia_pl.index(wybrany_dzien_pl)
        wybrany_dzien_date = poniedzialek_mikrocyklu + timedelta(days=wybrany_index)
        pelny_plan_dnia = get_gym_plan_for_date(zawodnik, wybrany_dzien_date)
        
        silowe_dnia = pelny_plan_dnia["silownia"]
        regen_dnia = pelny_plan_dnia["regeneracja"]
        
        if silowe_dnia or regen_dnia:
            if regen_dnia:
                st.success("🌿 Zaplanowana regeneracja / odnowa biologiczna / inne:")
                for idx, akt in enumerate(regen_dnia):
                    st.markdown(f"**{idx+1}.** {oczysc_nazwe_cwiczenia(akt)}")
            
            if silowe_dnia:
                st.info("🏋️ Zaplanowany trening siłowy:")
                for idx, cwiczenie in enumerate(silowe_dnia):
                    liczba_serii = pobierz_liczbe_serii(cwiczenie)
                    czysta_nazwa = oczysc_nazwe_cwiczenia(cwiczenie)
                    st.markdown(f"**{idx+1}. {czysta_nazwa}** (Serii do wykonania: {liczba_serii})")
        else:
            st.info("ℹ️ Brak zaplanowanych jednostek w tym dniu. Odpoczywaj!")
