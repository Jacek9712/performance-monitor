import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import os
import pytz
from streamlit_javascript import st_javascript
import time
import re
import plotly.express as px

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń
COLOR_SECONDARY = "#004d26" # Ciemniejsza zieleń dla kontrastu
COLOR_BG = "#F1F8E9"        # Bardzo jasne zielone tło
COLOR_TEXT = "#1B5E20"      # Ciemnozielony tekst
PL_TZ = pytz.timezone('Europe/Warsaw')

# --- DEFINICJA GRUP TRENINGOWYCH (AWARYJNY FALLBACK) ---
SLOWNIK_GRUP = {
    "Grupa A": [
        "Dima Avdieiev", "Leo Przybylak", "Michał Smoczyński", "Bartosz Piechowiak", 
        "Filip Jakubowski", "Jan Niedzielski", "Kacper Lepczyński", 
        "Kacper Rychert", "Kamil Kumoch", "Karol Łysiak", "Marcel Stefaniak", 
        "Mateusz Stanek", "Patryk Kusztal", "Paweł Kwiatkowski", "Oskar Mazurkiewicz", 
        "Sebastian Steblecki", "Szymon Zalewski", "Tomasz Wojcinowicz"
    ],
    "Grupa B": ["Igor Kornobis", "Marcel Zylla"],
    "Grupa C": ["Bartosz Lelito", "Jakub Kendzia"]
}

# --- GLOBALNA FUNKCJA DO USUWANIA POLSKICH ZNAKÓW ---
def usun_polskie_znaki(s):
    if not isinstance(s, str): return ""
    s = s.strip().lower()
    replacements = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
    for k, v in replacements.items(): s = s.replace(k, v)
    return s

# --- EKSTRAKCJA SERII I LINKÓW DLA TRENINGU SIŁOWEGO ---
def pobierz_liczbe_serii(cwiczenie_str):
    text_normalized = usun_polskie_znaki(cwiczenie_str)
    szukana_prosta = re.search(r"serie\s*:\s*(\d+)", text_normalized)
    if szukana_prosta: return int(szukana_prosta.group(1))
    szukana_tekst = re.search(r"(\d+)\s*(?:serii|serie|seria)", text_normalized)
    if szukana_tekst: return int(szukana_tekst.group(1))
    szukana_s = re.search(r"\b(\d+)\s*s\b", text_normalized)
    if szukana_s: return int(szukana_s.group(1))
    szukana_x = re.search(r"\b(\d+)\s*x", text_normalized)
    if szukana_x: return int(szukana_x.group(1))
    return 4

def pobierz_link_wideo(cwiczenie_str):
    szukana = re.search(r"\[LINK\s*:\s*(.*?)\]", cwiczenie_str, flags=re.IGNORECASE)
    if szukana: return szukana.group(1).strip()
    return ""

def oczysc_nazwe_cwiczenia(cwiczenie_str):
    temp = re.sub(r"\[?SERIE\s*:\s*\d+\]?", "", cwiczenie_str, flags=re.IGNORECASE)
    temp = re.sub(r"\[?LINK\s*:.*?\]", "", temp, flags=re.IGNORECASE)
    temp = re.sub(r"\[?GLOWNE\]?", "", temp, flags=re.IGNORECASE)
    temp = re.sub(r"\b\d+\s*(?:serii|serie|seria|s|x)\b.*", "", temp, flags=re.IGNORECASE)
    return temp.strip()

# --- INTELIGENTNA NORMALIZACJA KOLUMN ARKUSZA ---
def normalizuj_df_arkusza(df):
    if df is None or df.empty: return df
    df = df.copy()
    new_cols = []
    for col in df.columns:
        norm_col = re.sub(r'[^a-z0-9]', '', usun_polskie_znaki(col))
        if "data" in norm_col or "date" in norm_col or "time" in norm_col: new_cols.append("Data")
        elif "typ" in norm_col: new_cols.append("Typ_Raportu")
        elif "zawod" in norm_col or "gracz" in norm_col or "player" in norm_col or "nazw" in norm_col: new_cols.append("Zawodnik")
        elif "sen" in norm_col or "sleep" in norm_col: new_cols.append("Sen")
        elif "zmec" in norm_col or "fatigue" in norm_col: new_cols.append("Zmeczenie")
        elif "bol" in norm_col or "sore" in norm_col or "zakwas" in norm_col: new_cols.append("Bolesnosc")
        elif "stres" in norm_col or "stress" in norm_col: new_cols.append("Stres")
        elif "rpe" in norm_col or "intens" in norm_col: new_cols.append("RPE")
        elif "komen" in norm_col or "uwag" in norm_col or "note" in norm_col: new_cols.append("Komentarz")
        else: new_cols.append(col)
    df.columns = new_cols
    return df

# Logo
def get_logo():
    possible_files = ["herb.png", "logo.png", "logo.jpg", "image_b1bd1c.png"]
    for f in possible_files:
        if os.path.exists(f): return f
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
if "manual_selection" not in st.session_state: st.session_state.manual_selection = None
if "week_offset" not in st.session_state: st.session_state.week_offset = 0

conn = st.connection("gsheets", type=GSheetsConnection)

# --- SYSTEM DYNAMICZNEGO POBIERANIA GRUP Z ARKUSZA ---
# Zmieniono ttl na 600 (10 minut) i ukryto spinner, by nie blokował aplikacji!
@st.cache_data(ttl=600, show_spinner=False)
def pobierz_dynamiczne_grupy():
    try:
        df_grupy = conn.read(worksheet="Grupy", ttl=600)
        if df_grupy is not None and not df_grupy.empty:
            kolumny_male = [str(c).strip().lower() for c in df_grupy.columns]
            df_grupy.columns = kolumny_male
            if "zawodnik" in kolumny_male and "grupa" in kolumny_male:
                df_clean = df_grupy.dropna(subset=["zawodnik", "grupa"])
                return dict(zip(df_clean["zawodnik"].astype(str).str.strip(), df_clean["grupa"].astype(str).str.strip()))
    except Exception:
        pass
    return {}

def pobierz_grupe_zawodnika(nazwisko_gracza):
    dynamiczne_grupy = pobierz_dynamiczne_grupy()
    if nazwisko_gracza in dynamiczne_grupy:
        surowe = str(dynamiczne_grupy[nazwisko_gracza])
        return [g.strip() for g in re.split(r',|;', surowe) if g.strip()]
        
    for nazwa_grupy, lista_graczy in SLOWNIK_GRUP.items():
        if nazwisko_gracza in lista_graczy: return [nazwa_grupy]
    return ["Grupa Dynamiczna / Moc"]

# --- ZAPIS I ODCZYT WELLNESS / RPE (ARKUSZ 1) ---
# Zmieniono ttl na 60 i ukryto spinner
@st.cache_data(ttl=60, show_spinner=False)
def get_data_cached(worksheet_name="Arkusz1"):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=60)
        if worksheet_name == "Arkusz1" and df is not None: df = normalizuj_df_arkusza(df)
        return df
    except Exception as e:
        return None

def check_today_report(zawodnik, typ):
    try:
        df = get_data_cached("Arkusz1")
        if df is None or df.empty: return False
        df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        exists = df[(df['Zawodnik'] == zawodnik) & (df['Typ_Raportu'] == typ) & (df['Data_dt'].dt.date == dzisiaj)]
        return not exists.empty
    except:
        return False

def save_to_gsheets(row_data):
    try:
        # Przy zapisie lepiej odczytać świeżą wersję żeby nic nie nadpisać, tutaj ttl=0 jest akceptowalne bo wywoływane tylko po kliknięciu wyślij
        df_original = conn.read(worksheet="Arkusz1", ttl=0)
        if df_original is None or df_original.empty: return False
        oryginalne_kolumny = list(df_original.columns)
        df_internal = normalizuj_df_arkusza(df_original)
        df_internal['Data_dt'] = pd.to_datetime(df_internal['Data'], errors='coerce')
        dzisiaj = datetime.now(PL_TZ).date()
        
        juz_jest = df_internal[(df_internal['Zawodnik'] == row_data['Zawodnik']) & (df_internal['Typ_Raportu'] == row_data['Typ_Raportu']) & (df_internal['Data_dt'].dt.date == dzisiaj)]
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
            if "data" in norm or "date" in norm or "time" in norm: standard_to_original["Data"] = orig_col
            elif "typ" in norm: standard_to_original["Typ_Raportu"] = orig_col
            elif "zawod" in norm or "gracz" in norm or "player" in norm or "nazw" in norm: standard_to_original["Zawodnik"] = orig_col
            elif "sen" in norm or "sleep" in norm: standard_to_original["Sen"] = orig_col
            elif "zmec" in norm or "fatigue" in norm: standard_to_original["Zmeczenie"] = orig_col
            elif "bol" in norm or "sore" in norm or "zakwas" in norm: standard_to_original["Bolesnosc"] = orig_col
            elif "stres" in norm or "stress" in norm: standard_to_original["Stres"] = orig_col
            elif "rpe" in norm or "intens" in norm: standard_to_original["RPE"] = orig_col
            elif "komen" in norm or "uwag" in norm or "note" in norm: standard_to_original["Komentarz"] = orig_col
            
        final_cols = []
        for col in updated_df_internal.columns:
            if col in standard_to_original: final_cols.append(standard_to_original[col])
            else: final_cols.append(col)
        updated_df_internal.columns = final_cols
        
        conn.update(worksheet="Arkusz1", data=updated_df_internal)
        st.cache_data.clear()
        st.success("✔ RAPORT WYSŁANY!")
        return True
    except Exception as e:
        st.error(f"❌ BŁĄD ZAPISU: {e}")
        return False

# --- ODCZYT I ZAPIS SIŁOWNI ---
def check_today_gym_report(zawodnik):
    try:
        # Zmieniono ttl na 60
        df = conn.read(worksheet="Wyniki_Silownia", ttl=60)
        if df is None or df.empty: return False
        if 'Data' in df.columns and 'Zawodnik' in df.columns:
            df['Data_dt'] = pd.to_datetime(df['Data'], errors='coerce')
            exists = df[(df['Zawodnik'] == zawodnik) & (df['Data_dt'].dt.date == datetime.now(PL_TZ).date())]
            return not exists.empty
        return False
    except:
        return False

def save_gym_to_gsheets(row_data):
    try:
        try:
            df_original = conn.read(worksheet="Wyniki_Silownia", ttl=0)
        except:
            df_original = pd.DataFrame()
            
        if df_original is None: df_original = pd.DataFrame()
            
        dzisiaj = datetime.now(PL_TZ).date()
        if not df_original.empty and 'Data' in df_original.columns and 'Zawodnik' in df_original.columns:
            df_original['Data_dt'] = pd.to_datetime(df_original['Data'], errors='coerce')
            juz_jest = df_original[(df_original['Zawodnik'] == row_data['Zawodnik']) & (df_original['Data_dt'].dt.date == dzisiaj)]
            df_original = df_original.drop(columns=['Data_dt'], errors='ignore')
            if not juz_jest.empty:
                st.warning("⚠️ Twój dzisiejszy raport z siłowni został już zapisany!")
                st.cache_data.clear()
                time.sleep(1.5)
                return True
                
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df_original, new_row], ignore_index=True)
        
        conn.update(worksheet="Wyniki_Silownia", data=updated_df)
        st.cache_data.clear()
        st.success("✔ RAPORT SIŁOWY WYSŁANY DO BAZY POWER BI!")
        return True
    except Exception as e:
        st.error(f"❌ BŁĄD ZAPISU DO 'Wyniki_Silownia'. Upewnij się, że ta zakładka istnieje w arkuszu! {e}")
        return False

def get_gym_plan_for_date(nazwisko_gracza, target_date):
    puste_plany = []
    try:
        # Zmieniono ttl na 60
        df_plans = conn.read(worksheet="Plany", ttl=60)
        if df_plans is None or df_plans.empty: return puste_plany
        
        df_plans['Data_dt'] = pd.to_datetime(df_plans['Data'], errors='coerce').dt.date
        plany_dnia = df_plans[df_plans['Data_dt'] == target_date]
        if plany_dnia.empty: return puste_plany
            
        grupy_gracza = pobierz_grupe_zawodnika(nazwisko_gracza)
        
        pasujace_plany = plany_dnia[
            (plany_dnia['Grupa_lub_Zawodnik'] == nazwisko_gracza) |
            (plany_dnia['Grupa_lub_Zawodnik'].isin(grupy_gracza)) |
            (plany_dnia['Grupa_lub_Zawodnik'].isin(["Wszyscy", ""])) |
            (plany_dnia['Grupa_lub_Zawodnik'].isna())
        ]
        
        wyniki_planow = []
        
        for _, plan_wybrany in pasujace_plany.iterrows():
            # --- SYSTEM WYKLUCZEŃ ---
            wykluczeni = str(plan_wybrany.get('Wykluczenia', '')).strip()
            if nazwisko_gracza in wykluczeni and nazwisko_gracza != "":
                continue # Omijamy ten plan dla tego konkretnego gracza
                
            tytul_treningu = ""
            if 'Tytul_Treningu' in plan_wybrany and pd.notna(plan_wybrany['Tytul_Treningu']) and str(plan_wybrany['Tytul_Treningu']).strip() not in ["", "nan"]:
                tytul_treningu = str(plan_wybrany['Tytul_Treningu']).strip()
                
            zrodlo = str(plan_wybrany.get('Grupa_lub_Zawodnik', 'Wszyscy')).strip()
            if zrodlo in ["", "nan"]: zrodlo = "Wszyscy"
                
            silownia_list = []
            regeneracja_list = []
            
            for col in df_plans.columns:
                val = plan_wybrany[col]
                if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan": continue
                col_norm = usun_polskie_znaki(str(col)).replace(" ", "").replace("_", "")
                val_str = str(val).strip()
                
                if "cwiczenie" in col_norm: silownia_list.append(val_str)
                elif "regeneracja" in col_norm or "odnowa" in col_norm:
                    czesci = re.split(r',|;|\|\||\+', val_str)
                    for czesc in czesci:
                        if czesc.strip(): regeneracja_list.append(czesc.strip())
            
            if silownia_list or regeneracja_list:
                display_title = tytul_treningu if tytul_treningu else ("Plan Indywidualny" if zrodlo == nazwisko_gracza else f"Plan Grupowy")
                wyniki_planow.append({
                    "zrodlo": zrodlo,
                    "tytul": display_title,
                    "silownia": list(dict.fromkeys(silownia_list)), 
                    "regeneracja": list(dict.fromkeys(regeneracja_list))
                })
                        
        return wyniki_planow
    except:
        return puste_plany

def get_today_gym_plan(nazwisko_gracza):
    dzisiaj = datetime.now(PL_TZ).date()
    return get_gym_plan_for_date(nazwisko_gracza, dzisiaj)

# --- REJESTRACJA ZAWODNIKA ---
dynamiczne_grupy = pobierz_dynamiczne_grupy()

wszyscy_zawodnicy = set(LISTA_ZAWODNIKOW)
if dynamiczne_grupy:
    wszyscy_zawodnicy.update(dynamiczne_grupy.keys())

kadra_z_arkusza = sorted(list(wszyscy_zawodnicy))

query_params = st.query_params
player_from_url = query_params.get("player", None)
stored_player = st_javascript("localStorage.getItem('warta_player_name');")

# Inicjalizacja dodatkowego stanu dla wylogowania
if "logout_triggered" not in st.session_state: st.session_state.logout_triggered = False

# Określenie, kto jest aktualnie "zalogowany"
current_player = None
if st.session_state.manual_selection:
    current_player = st.session_state.manual_selection
elif not st.session_state.logout_triggered:
    if player_from_url in kadra_z_arkusza:
        current_player = player_from_url
    elif stored_player in kadra_z_arkusza:
        current_player = stored_player

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    .stApp {{ background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    
    /* Główne stylowanie tekstu czcionką Anton */
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ font-family: 'Anton', sans-serif !important; color: {COLOR_TEXT}; }}
    
    /* NAPRAWA: Zabezpieczenie ikon systemowych Streamlit (np. strzałek rozwijania) przed nadpisaniem czcionki */
    [data-testid="stIconMaterial"], [data-testid="stExpander"] summary span, .material-symbols-rounded, .streamlit-expander-icon {{ 
        font-family: 'Material Symbols Rounded', sans-serif !important; 
    }}
    
    .custom-header {{ text-align: center; margin-bottom: 10px; }}
    h1 {{ color: {COLOR_PRIMARY} !important; text-transform: uppercase; margin: 0; letter-spacing: 1px; font-size: 1.8rem !important; }}
    .logo-container {{ display: flex; justify-content: center; align-items: center; width: 100%; margin: 0 auto; padding: 10px 0; }}
    [data-testid="stForm"] {{ background-color: #FFFFFF !important; border: 1px solid #d1d9e6 !important; padding: 25px !important; border-radius: 20px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
    button[kind="formSubmit"], .nav-button button, .logout-btn button {{ background-color: {COLOR_PRIMARY} !important; color: white !important; font-weight: bold !important; border-radius: 10px !important; width: 100% !important; border: none !important; padding: 10px !important; margin-top: 10px !important; text-transform: uppercase; }}
    .wellness-legend {{ background: linear-gradient(90deg, #FFEBEE 0%, #FFFDE7 50%, #E8F5E9 100%); padding: 15px; border-radius: 12px; border: 1px solid #ddd; margin-bottom: 20px; text-align: center; }}
    .legend-item {{ flex: 1; font-size: 0.8rem; }}
    .login-info {{ background-color: {COLOR_PRIMARY}; color: white !important; padding: 8px; border-radius: 10px; text-align: center; margin: 0 auto 5px auto; max-width: 300px; font-weight: bold; font-size: 0.9rem; }}
    .already-sent {{ background-color: #E8F5E9; color: #2E7D32; padding: 25px; border-radius: 20px; text-align: center; font-weight: bold; border: 2px solid #C8E6C9; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
    .calendar-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; width: 100%; margin-bottom: 20px; }}
    @media (max-width: 900px) {{ .calendar-grid {{ grid-template-columns: repeat(4, 1fr); }} }}
    @media (max-width: 600px) {{ .calendar-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    .calendar-cell {{ background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; padding: 10px; text-align: center; min-height: 150px; display: flex; flex-direction: column; justify-content: flex-start; transition: transform 0.2s, box-shadow 0.2s, border 0.2s; }}
    .calendar-cell:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
    .calendar-cell.today {{ border: 2px solid #D32F2F !important; background-color: #FFFDE7 !important; }}
    .calendar-cell-header {{ font-size: 0.85rem; font-weight: bold; color: {COLOR_PRIMARY}; text-transform: uppercase; margin-bottom: 2px; }}
    .calendar-cell-header.today-text {{ color: #D32F2F !important; }}
    .calendar-cell-date {{ font-size: 0.72rem; color: #666; margin-bottom: 8px; }}
    .calendar-cell-content {{ display: flex; flex-direction: column; gap: 4px; align-items: stretch; text-align: left; }}
    .cal-exercise-tag {{ background: #E8F5E9; color: #2E7D32; font-size: 0.68rem; padding: 3px 6px; border-radius: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; border: 1px solid #C8E6C9; }}
    .cal-rec-tag {{ background: #E3F2FD; color: #1565C0; font-size: 0.68rem; padding: 3px 6px; border-radius: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; border: 1px solid #BBDEFB; }}
    .cal-empty-tag {{ color: #999; font-size: 0.68rem; text-align: center; margin-top: 15px; font-style: italic; }}
    .recovery-activity-box {{ background-color: #E3F2FD; border: 1px solid #BBDEFB; border-radius: 12px; padding: 15px; margin-bottom: 15px; color: #0D47A1; }}
    </style>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 1, 1.5])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

# SYSTEM LOGOWANIA Z PRZYCISKIEM WYLOGUJ
if current_player:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {current_player.upper()}</div>', unsafe_allow_html=True)
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("Wyloguj (Zmień zawodnika)", use_container_width=True):
        st.query_params.clear()
        st.session_state.logout_triggered = True
        st.session_state.manual_selection = None
        st.session_state.week_offset = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    zawodnik = current_player
else:
    # Wysłanie komendy do przeglądarki, aby NA PEWNO usunęła zawodnika po wylogowaniu
    if st.session_state.logout_triggered:
        st_javascript("localStorage.removeItem('warta_player_name');")
        
    zawodnik_wybor = st.selectbox("👤 WYBIERZ SWOJE NAZWISKO:", kadra_z_arkusza, index=None, placeholder="Wybierz z listy...")
    if zawodnik_wybor:
        # Zapisz wybór w pamięci przeglądarki na stałe
        st_javascript(f"localStorage.setItem('warta_player_name', '{zawodnik_wybor}');")
        st.session_state.manual_selection = zawodnik_wybor
        st.session_state.logout_triggered = False
        st.session_state.week_offset = 0
        time.sleep(0.5)
        st.rerun()
    zawodnik = None

if zawodnik:
    tab_well, tab_rpe, tab_gym, tab_cal, tab_hist = st.tabs(["📊 WELLNESS", "🏃 RPE", "🏋️ SIŁOWNIA", "📅 MIKROCYKL", "📈 HISTORIA"])

    with tab_well:
        if check_today_report(zawodnik, "Wellness"):
            st.markdown(f'<div class="already-sent"><p style="font-size: 1.2rem; margin-bottom: 10px;">✅ CZEŚĆ {zawodnik.split()[0]}!</p><p>TWÓJ DZISIEJSZY RAPORT WELLNESS ZOSTAŁ JUŻ WYSŁANY.</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="wellness-legend"><div style="display: flex; justify-content: space-around;"><div class="legend-item">🔴 1<br><b>ŹLE</b></div><div class="legend-item">🟡 3<br><b>ŚREDNIO</b></div><div class="legend-item">🟢 5<br><b>SUPER</b></div></div></div>', unsafe_allow_html=True)
            with st.form("wellness_form", border=True):
                s1 = int(st.select_slider("SEN", options=[1,2,3,4,5], value=3))
                s2 = int(st.select_slider("ZMĘCZENIE FIZYCZNE", options=[1,2,3,4,5], value=3))
                s3 = int(st.select_slider("BOLESNOŚĆ", options=[1,2,3,4,5], value=3))
                s4 = int(st.select_slider("STRES OGÓLNY", options=[1,2,3,4,5], value=3))
                
                k = st.text_area("DODATKOWE UWAGI", placeholder="Np. ból prawego uda...")
                if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({"Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik, "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k}):
                        st.rerun()

    with tab_rpe:
        if check_today_report(zawodnik, "RPE"):
            st.markdown(f'<div class="already-sent"><p style="font-size: 1.2rem; margin-bottom: 10px;">✅ CZEŚĆ {zawodnik.split()[0]}!</p><p>TWÓJ DZISIEJSZY RAPORT RPE ZOSTAŁ JUŻ WYSŁANY.</p></div>', unsafe_allow_html=True)
        else:
            with st.form("rpe_form", border=True):
                st.markdown("<p style='text-align: center;'>PODAJ INTENSYWNOŚĆ TRENINGU BOISKOWEGO</p>", unsafe_allow_html=True)
                rpe = st.slider("SKALA RPE (0-10)", 0, 10, 5)
                k_rpe = st.text_area("UWAGI DO TRENINGU", placeholder="Jak się czułeś?")
                if st.form_submit_button("WYŚLIJ RAPORT RPE"):
                    timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    if save_to_gsheets({"Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik, "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": rpe, "Komentarz": k_rpe}):
                        st.rerun()

    with tab_gym:
        juz_wyslano = check_today_gym_report(zawodnik)
        plany_na_dzis = get_today_gym_plan(zawodnik)
        has_gym = any(p.get("silownia", []) for p in plany_na_dzis)
        
        if juz_wyslano:
            st.markdown(f'<div class="already-sent"><p style="font-size: 1.2rem; margin-bottom: 10px;">🏋️ WITAJ {zawodnik.split()[0]}!</p><p>TWÓJ RAPORT Z TRENINGU SIŁOWEGO ZOSTAŁ JUŻ ZAPISANY.</p></div>', unsafe_allow_html=True)
            
            if has_gym:
                st.markdown("<br><h3 style='text-align: center; color: #006633;'>📋 TWÓJ DZISIEJSZY PLAN</h3>", unsafe_allow_html=True)
                for plan in plany_na_dzis:
                    silowe = plan.get("silownia", [])
                    if not silowe: continue
                    
                    rodzaj_tag = "🔴 TRENING INDYWIDUALNY" if plan["zrodlo"] == zawodnik else f"🟢 {plan['zrodlo'].upper()}"
                    st.markdown(f"""
                    <div style="background-color: #E8F5E9; padding: 10px 15px; border-left: 5px solid {COLOR_PRIMARY}; border-radius: 5px; margin-bottom: 15px; margin-top: 15px;">
                        <span style="font-size: 0.75rem; font-weight: bold; color: {COLOR_PRIMARY};">{rodzaj_tag}</span><br>
                        <span style="font-size: 1.2rem; font-weight: bold; color: #1B5E20;">{plan['tytul'].upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for idx, cwiczenie in enumerate(silowe):
                        liczba_serii = pobierz_liczbe_serii(cwiczenie)
                        czysta_nazwa_cw = oczysc_nazwe_cwiczenia(cwiczenie)
                        link_wideo = pobierz_link_wideo(cwiczenie)
                        czy_glowne = "[GLOWNE]" in cwiczenie.upper()
                        
                        typ_cwiczenia = "Główne" if czy_glowne else "Akcesoryjne"
                        link_html = f" <br><a href='{link_wideo}' target='_blank' style='display: inline-block; margin-top: 5px; padding: 3px 8px; background-color: #D32F2F; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 0.75rem;'>▶️ OBEJRZYJ WIDEO</a>" if link_wideo else ""
                        
                        st.markdown(f"**{idx+1}. {czysta_nazwa_cw}** <br><span style='font-size:0.85rem; color:#555;'>Serie: {liczba_serii} | Typ: {typ_cwiczenia}</span>{link_html}", unsafe_allow_html=True)
                        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
                        
        else:
            if not plany_na_dzis or not has_gym:
                st.markdown(
                    f'<div class="recovery-activity-box" style="background-color: #E3F2FD; border: 1px solid #BBDEFB; color: #0D47A1;">'
                    f'<h3 style="margin-top:0px; color:#0D47A1;">🌿 BRAK SIŁOWNI W DNIU DZISIEJSZYM</h3>'
                    f'<p>Dziś nie masz zaplanowanego tradycyjnego treningu siłowego.</p>'
                    f'<p style="font-weight: bold; margin-bottom: 0px;">Przejdź do zakładki "📅 MIKROCYKL", aby sprawdzić, czy sztab zaplanował odnowę lub inną aktywność!</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                with st.form("gym_form", border=True):
                    st.markdown(f"<p style='text-align: center; font-size:1.6rem; margin-bottom: 5px; color:{COLOR_PRIMARY};'>🏋️ TWÓJ DZIENNIK TRENINGU SIŁOWEGO</p>", unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 0.85rem; color: #555; margin-bottom: 20px; text-align: center;'>Zrealizuj poniższe plany i wpisz obciążenia w kilogramach dla głównej części:</p>", unsafe_allow_html=True)
                    
                    wyniki_do_powerbi = {}
                    tonaz_calkowity = 0.0
                    global_cw_idx = 1
                    
                    for plan in plany_na_dzis:
                        silowe = plan.get("silownia", [])
                        if not silowe: continue
                        
                        rodzaj_tag = "🔴 TRENING INDYWIDUALNY" if plan["zrodlo"] == zawodnik else f"🟢 {plan['zrodlo'].upper()}"
                        st.markdown(f"""
                        <div style="background-color: #E8F5E9; padding: 10px 15px; border-left: 5px solid {COLOR_PRIMARY}; border-radius: 5px; margin-bottom: 15px;">
                            <span style="font-size: 0.75rem; font-weight: bold; color: {COLOR_PRIMARY};">{rodzaj_tag}</span><br>
                            <span style="font-size: 1.2rem; font-weight: bold; color: #1B5E20;">{plan['tytul'].upper()}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for cwiczenie in silowe:
                            liczba_serii = pobierz_liczbe_serii(cwiczenie)
                            czysta_nazwa_cw = oczysc_nazwe_cwiczenia(cwiczenie)
                            link_wideo = pobierz_link_wideo(cwiczenie)
                            czy_glowne = "[GLOWNE]" in cwiczenie.upper()
                            
                            st.markdown(f"#### 💪 {global_cw_idx}. {czysta_nazwa_cw.upper()}")
                            wyniki_do_powerbi[f"Cwiczenie_{global_cw_idx}_Nazwa"] = f"[{plan['tytul']}] {czysta_nazwa_cw}"
                            
                            if link_wideo:
                                st.markdown(f"<a href='{link_wideo}' target='_blank' style='display: inline-block; margin-bottom: 10px; padding: 4px 10px; background-color: #D32F2F; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 0.8rem;'>▶️ OBEJRZYJ WIDEO INSTRUKTAŻOWE</a>", unsafe_allow_html=True)
                                
                            if czy_glowne:
                                seria_cols = st.columns(min(liczba_serii, 5))
                                suma_cwiczenia = 0.0
                                
                                for s in range(liczba_serii):
                                    with seria_cols[s % 5]:
                                        ciezar_serii = st.number_input(
                                            f"S{s+1} (kg)", 
                                            min_value=0.0, max_value=350.0, value=0.0, step=2.5, 
                                            key=f"obc_{global_cw_idx}_{s}"
                                        )
                                        suma_cwiczenia += ciezar_serii
                                        wyniki_do_powerbi[f"Cw_{global_cw_idx}_Seria_{s+1}_KG"] = float(ciezar_serii)
                                        
                                wyniki_do_powerbi[f"Cwiczenie_{global_cw_idx}_Suma_KG"] = float(suma_cwiczenia)
                                tonaz_calkowity += suma_cwiczenia
                            else:
                                st.markdown(f"**Zaplanowane serie:** {liczba_serii}")
                                st.markdown("<span style='color:#666; font-size:0.85rem;'>*Ćwiczenie akcesoryjne - wykonaj zgodnie z zaleceniami, bez wpisywania ciężaru.*</span>", unsafe_allow_html=True)
                                wyniki_do_powerbi[f"Cwiczenie_{global_cw_idx}_Suma_KG"] = 0.0
                            
                            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
                            global_cw_idx += 1
                    
                    st.markdown("---")
                    k_gym = st.text_area("UWAGI DO TRENINGU (Opcjonalnie)", placeholder="Np. ból w barku przy 3 serii...")
                    
                    if st.form_submit_button("WYŚLIJ RAPORT SIŁOWY"):
                        timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        pelny_raport = {
                            "Data": timestamp,
                            "Zawodnik": zawodnik,
                            "Tonaz_Calkowity_KG": float(tonaz_calkowity),
                            "Uwagi": k_gym
                        }
                        pelny_raport.update(wyniki_do_powerbi)
                        
                        save_gym_to_gsheets(pelny_raport)

    with tab_cal:
        st.markdown("### 📋 PLAN TYGODNIA")
        st.write("Sprawdź rozkład zajęć, regeneracji i siłowni w poszczególnych tygodniach.")
        
        col_prev, col_curr, col_next = st.columns([1, 2, 1])
        with col_prev:
            st.markdown('<div class="nav-button">', unsafe_allow_html=True)
            if st.button("⬅️ Poprzedni", use_container_width=True):
                st.session_state.week_offset -= 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_next:
            st.markdown('<div class="nav-button">', unsafe_allow_html=True)
            if st.button("Następny ➡️", use_container_width=True):
                st.session_state.week_offset += 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        dzis_prawdziwe = datetime.now(PL_TZ).date()
        offset_dni = st.session_state.week_offset * 7
        
        poniedzialek_mikrocyklu = (dzis_prawdziwe - timedelta(days=dzis_prawdziwe.weekday())) + timedelta(days=offset_dni)
        niedziela_mikrocyklu = poniedzialek_mikrocyklu + timedelta(days=6)
        
        with col_curr:
            st.markdown(f"<p style='text-align: center; font-weight: bold; font-size: 1.1rem; margin-top: 15px;'>{poniedzialek_mikrocyklu.strftime('%d.%m')} - {niedziela_mikrocyklu.strftime('%d.%m.%Y')}</p>", unsafe_allow_html=True)
            if st.session_state.week_offset != 0:
                st.markdown('<div class="nav-button">', unsafe_allow_html=True)
                if st.button("🔄 Wróć do obecnego", use_container_width=True):
                    st.session_state.week_offset = 0
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        dni_tygodnia_pl = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        
        grid_html = '<div class="calendar-grid">'
        for i, nazwa_dnia in enumerate(dni_tygodnia_pl):
            aktywny_dzien = poniedzialek_mikrocyklu + timedelta(days=i)
            data_str = aktywny_dzien.strftime("%d.%m")
            czy_dzis = (aktywny_dzien == dzis_prawdziwe)
            
            cell_class = "calendar-cell today" if czy_dzis else "calendar-cell"
            header_class = "calendar-cell-header today-text" if czy_dzis else "calendar-cell-header"
            dzien_label = f"{nazwa_dnia} (DZIŚ)" if czy_dzis else nazwa_dnia
            
            plany_dnia = get_gym_plan_for_date(zawodnik, aktywny_dzien)
            
            content_tags = ""
            total_elements = 0
            
            for plan in plany_dnia:
                for rg in plan.get("regeneracja", []):
                    cz_rg = oczysc_nazwe_cwiczenia(rg)
                    content_tags += f'<div class="cal-rec-tag">🌿 {cz_rg[:15]+"..." if len(cz_rg)>18 else cz_rg}</div>'
                    total_elements += 1
                    
                if plan.get("silownia", []):
                    tytul_dnia = plan.get("tytul", "")
                    if tytul_dnia and "Plan Grupowy" not in tytul_dnia and "Plan Indywidualny" not in tytul_dnia:
                        content_tags += f'<div class="cal-exercise-tag">🏋️ {tytul_dnia[:20]+"..." if len(tytul_dnia)>22 else tytul_dnia}</div>'
                        total_elements += 1
                    else:
                        for sl in plan["silownia"]:
                            cz_sl = oczysc_nazwe_cwiczenia(sl)
                            content_tags += f'<div class="cal-exercise-tag">🏋️ {cz_sl[:15]+"..." if len(cz_sl)>18 else cz_sl}</div>'
                            total_elements += 1
                
            if total_elements == 0: 
                content_tags = '<div class="cal-empty-tag">Brak planu (Wolne)</div>'
                
            grid_html += f'<div class="{cell_class}"><div class="{header_class}">{dzien_label}</div><div class="calendar-date">{data_str}</div><div class="calendar-cell-content">{content_tags}</div></div>'
            
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)
        
        st.markdown("<br><h4>🔍 SZCZEGÓŁOWY PODGLĄD DNIA</h4>", unsafe_allow_html=True)
        
        default_index = dzis_prawdziwe.weekday() if st.session_state.week_offset == 0 else 0
        wybrany_dzien_pl = st.selectbox("WYBIERZ DZIEŃ Z WIDOCZNEGO TYGODNIA, ABY ZOBACZYĆ PEŁNY PLAN:", dni_tygodnia_pl, index=default_index, key="day_selector_microcycle")
        
        wybrany_index = dni_tygodnia_pl.index(wybrany_dzien_pl)
        wybrany_dzien_date = poniedzialek_mikrocyklu + timedelta(days=wybrany_index)
        plany_dnia = get_gym_plan_for_date(zawodnik, wybrany_dzien_date)
        
        has_any = any(p.get("silownia", []) or p.get("regeneracja", []) for p in plany_dnia)
        
        if has_any:
            for plan in plany_dnia:
                rodzaj_tag = "🔴 TRENING INDYWIDUALNY" if plan["zrodlo"] == zawodnik else f"🟢 {plan['zrodlo'].upper()}"
                st.markdown(f"#### 📌 {plan['tytul'].upper()} <br><span style='font-size:0.8rem; color:#666;'>{rodzaj_tag}</span>", unsafe_allow_html=True)
                
                if plan.get("regeneracja", []):
                    st.success("🌿 Zaplanowana regeneracja / odnowa biologiczna / inne:")
                    for idx, akt in enumerate(plan["regeneracja"]): st.markdown(f"**{idx+1}.** {oczysc_nazwe_cwiczenia(akt)}")
                if plan.get("silownia", []):
                    st.info("🏋️ Zaplanowany trening siłowy:")
                    for idx, cwiczenie in enumerate(plan["silownia"]):
                        liczba_serii = pobierz_liczbe_serii(cwiczenie)
                        czysta_nazwa = oczysc_nazwe_cwiczenia(cwiczenie)
                        
                        st.markdown(f"**{idx+1}. {czysta_nazwa}** (Serii do wykonania: {liczba_serii})")
                st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        else:
            st.info(f"ℹ️ Brak zaplanowanych jednostek na dzień {wybrany_dzien_date.strftime('%d.%m.%Y')}. Odpoczywaj!")

    with tab_hist:
        st.markdown(f"<h3 style='text-align: center; color: {COLOR_PRIMARY};'>📈 TWOJA HISTORIA WYNIKÓW</h3>", unsafe_allow_html=True)
        st.write("Prześledź swoje postępy z poprzednich treningów siłowych.")
        
        try:
            df_wyniki_silownia = conn.read(worksheet="Wyniki_Silownia", ttl=60)
            if df_wyniki_silownia is not None and not df_wyniki_silownia.empty and 'Zawodnik' in df_wyniki_silownia.columns:
                df_moje = df_wyniki_silownia[df_wyniki_silownia['Zawodnik'] == zawodnik].copy()
                
                if not df_moje.empty:
                    df_moje['Data_dt'] = pd.to_datetime(df_moje['Data'], errors='coerce')
                    df_moje = df_moje.dropna(subset=['Data_dt']).sort_values('Data_dt', ascending=True) 
                    
                    if 'Tonaz_Calkowity_KG' in df_moje.columns:
                        fig = px.bar(
                            df_moje, x='Data_dt', y='Tonaz_Calkowity_KG', 
                            title="Całkowite obciążenie (kg) na sesji",
                            labels={'Data_dt': 'Data Treningu', 'Tonaz_Calkowity_KG': 'Suma obciążeń (kg)'},
                            text_auto='.0f'
                        )
                        fig.update_traces(marker_color=COLOR_PRIMARY)
                        fig.update_layout(xaxis_tickformat="%d.%m.%y")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("#### 🔍 DETALE OSTATNICH TRENINGÓW")
                    df_moje_desc = df_moje.sort_values('Data_dt', ascending=False)
                    
                    for idx, row in df_moje_desc.head(10).iterrows():
                        data_treningu = row['Data_dt'].strftime('%d.%m.%Y')
                        tonaz = row.get('Tonaz_Calkowity_KG', 0.0)
                        
                        with st.expander(f"🏋️ Trening z {data_treningu} | Tonaż: {tonaz} kg"):
                            cwiczenia_zrealizowane = []
                            for i in range(1, 6):
                                nazwa_col = f"Cwiczenie_{i}_Nazwa"
                                if nazwa_col in row and pd.notna(row[nazwa_col]) and str(row[nazwa_col]).strip() != "":
                                    c_nazwa = str(row[nazwa_col])
                                    c_suma = row.get(f"Cwiczenie_{i}_Suma_KG", 0)
                                    serie_text = []
                                    for s in range(1, 11):
                                        s_col = f"Cw_{i}_Seria_{s}_KG"
                                        if s_col in row and pd.notna(row[s_col]) and row[s_col] > 0:
                                            serie_text.append(f"{row[s_col]}kg")
                                    if serie_text:
                                        cwiczenia_zrealizowane.append(f"**{c_nazwa}**: {', '.join(serie_text)} *(Suma: {c_suma}kg)*")
                            
                            if cwiczenia_zrealizowane:
                                for cz in cwiczenia_zrealizowane:
                                    st.markdown(f"• {cz}")
                            else:
                                st.write("Brak zapisanych ciężarów dla głównych ćwiczeń (tylko akcesoryjne).")
                                
                            uwagi = row.get('Uwagi', '')
                            if pd.notna(uwagi) and str(uwagi).strip() != "":
                                st.info(f"📝 Twoje uwagi: {uwagi}")
                else:
                    st.info("Brak historii treningów siłowych w bazie. Wypełnij pierwszy raport!")
            else:
                st.info("Brak tabeli z wynikami w bazie danych.")
        except Exception as e:
            st.error(f"Nie udało się załadować historii: {e}")
