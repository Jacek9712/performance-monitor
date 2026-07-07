import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date, timedelta
import pytz
import calendar
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
import re

# --- KONFIGURACJA KLUBU ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "Warta!"
GODZINA_WELLNESS = 10 
GODZINA_RPE = 17

st.set_page_config(page_title="Warta Poznań - Sztab", page_icon="📋", layout="wide")

# --- LISTY ZAWODNIKÓW I GRUP (AWARYJNY FALLBACK) ---
FALLBACK_LISTA_ZAWODNIKOW = sorted([
    "Adrian Wnuk", "Bartosz Lelito", "Bartosz Piechowiak", "Dima Avdieiev", "Filip Jakubowski", 
    "Igor Kornobis", "Jakub Kendzia", "Jan Niedzielski", 
    "Kacper Lepczyński", "Kacper Rychert", "Kamil Kumoch", 
    "Karol Łysiak", "Leo Przybylak", "Marcel Stefaniak", "Marcel Zylla", 
    "Mateusz Stanek", "Michał Smoczyński", "Patryk Kusztal", "Paweł Kwiatkowski", 
    "Oskar Mazurkiewicz", "Sebastian Steblecki", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

FALLBACK_GRUPY_LISTA = [
    "Grupa A", 
    "Grupa B", 
    "Grupa C",
    "Bramkarze", 
    "Grupa Siła / Rebuilding", 
    "Grupa Prewencja / Powrót po kontuzji", 
    "Grupa Dynamiczna / Moc"
]

# --- ŁADOWANIE DANYCH Z GSHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def pobierz_dynamiczne_grupy_i_zawodnikow():
    try:
        df_grupy = conn.read(worksheet="Grupy", ttl=5)
        if df_grupy is None or df_grupy.empty:
            return FALLBACK_LISTA_ZAWODNIKOW, FALLBACK_GRUPY_LISTA, "Arkusz 'Grupy' jest pusty."
            
        kolumny_male = [str(c).strip().lower() for c in df_grupy.columns]
        df_grupy.columns = kolumny_male
        
        if "zawodnik" in kolumny_male and "grupa" in kolumny_male:
            zawodnicy_czysci = [str(z).strip() for z in df_grupy["zawodnik"].dropna().tolist() if str(z).strip() != ""]
            
            grupy_surowe = [str(g).strip() for g in df_grupy["grupa"].dropna().tolist() if str(g).strip() != ""]
            grupy_czyste = []
            for g_row in grupy_surowe:
                for g_part in re.split(r',|;', g_row):
                    if g_part.strip():
                        grupy_czyste.append(g_part.strip())
            
            zawodnicy = sorted(list(set(zawodnicy_czysci)))
            grupy = sorted(list(set(grupy_czyste)))
            
            if zawodnicy and grupy:
                return zawodnicy, grupy, "OK"
            else:
                return FALLBACK_LISTA_ZAWODNIKOW, FALLBACK_GRUPY_LISTA, "Kolumny są poprawne, brak danych."
        else:
            return FALLBACK_LISTA_ZAWODNIKOW, FALLBACK_GRUPY_LISTA, "Brak kolumn 'Zawodnik' i 'Grupa'."
            
    except Exception as e:
        return FALLBACK_LISTA_ZAWODNIKOW, FALLBACK_GRUPY_LISTA, f"Błąd (Brak zakładki 'Grupy'?): {e}"

LISTA_ZAWODNIKOW, GRUPY_LISTA, STATUS_GRUP = pobierz_dynamiczne_grupy_i_zawodnikow()

# --- ŁADOWANIE SZABLONÓW ---
@st.cache_data(ttl=5)
def pobierz_szablony():
    try:
        df_szablony = conn.read(worksheet="Szablony", ttl=0)
        if df_szablony is not None and not df_szablony.empty and "Nazwa_Szablonu" in df_szablony.columns:
            return df_szablony.dropna(subset=['Nazwa_Szablonu'])
    except:
        pass
    return pd.DataFrame()

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    .stApp {{ background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; }}
    html, body, [class*="st-"], .stMarkdown, label, p, span {{ font-family: 'Anton', sans-serif !important; color: {COLOR_TEXT}; }}
    h1, h2, h3, h4 {{ color: {COLOR_PRIMARY} !important; text-transform: uppercase; text-align: center; }}
    
    [data-testid="stMetric"] {{
        background-color: white; padding: 15px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #e0e0e0;
    }}
    .template-box {{
        background-color: #E8F5E9; padding: 15px; border-radius: 10px; border: 1px solid #C8E6C9; margin-bottom: 20px;
    }}
    .metric-card-red {{ background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); border-left: 5px solid #D32F2F; }}
    .metric-card-orange {{ background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); border-left: 5px solid #F57C00; }}
    .metric-card-green {{ background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); border-left: 5px solid #388E3C; }}
    </style>
    """, unsafe_allow_html=True)

# --- SYSTEM LOGOWANIA ---
if "auth_staff" not in st.session_state:
    st.session_state["auth_staff"] = False

def login():
    if not st.session_state["auth_staff"]:
        st.markdown("<h1>🔐 LOGOWANIE SZTABU</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            haslo = st.text_input("Podaj hasło sztabowe:", type="password")
            if st.button("Zaloguj"):
                if haslo == PASSWORD_TRENER:
                    st.session_state["auth_staff"] = True
                    st.rerun()
                else:
                    st.error("Błędne hasło!")
        st.stop()

login()

# --- FUNKCJE POMOCNICZE ---
def usun_polskie_znaki(s):
    if not isinstance(s, str): return ""
    s = s.strip().lower()
    replacements = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
    for k, v in replacements.items(): s = s.replace(k, v)
    return s

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
        elif "mental" in norm_col or "kognit" in norm_col or "glow" in norm_col: new_cols.append("Zmeczenie_Mentalne")
        elif "rpe" in norm_col or "intens" in norm_col: new_cols.append("RPE")
        elif "komen" in norm_col or "uwag" in norm_col or "note" in norm_col: new_cols.append("Komentarz")
        else: new_cols.append(col)
    df.columns = new_cols
    return df

@st.cache_data(ttl=10)
def load_data(worksheet_name="Arkusz1"):
    try:
        return conn.read(worksheet=worksheet_name, ttl=0)
    except Exception as e:
        st.error(f"Błąd połączenia z Arkuszem {worksheet_name}: {e}")
        return pd.DataFrame()

def get_logo():
    logo_path = "herb.png"
    if os.path.exists(logo_path): return logo_path
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

col_l1, col_l2, col_l3 = st.columns([1, 0.5, 1])
with col_l2:
    st.image(get_logo(), use_container_width=True)

st.markdown(f"<h1>📊 PERFORMANCE & STAFF ANALYTICS</h1>", unsafe_allow_html=True)

try:
    df_raw = load_data("Arkusz1")
    
    if df_raw is None or df_raw.empty:
        st.info("Brak danych w arkuszu lub nie można połączyć się z bazą danych.")
    else:
        df = df_raw.copy()
        df = normalizuj_df_arkusza(df)
        
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], format='mixed', dayfirst=False, errors='coerce')
            df = df.dropna(subset=['Data'])
            df['Dzień'] = df['Data'].dt.date
            df['Godzina_H'] = df['Data'].dt.hour
            df = df.sort_values('Data', ascending=True)
            df = df.drop_duplicates(subset=['Zawodnik', 'Dzień', 'Typ_Raportu'], keep='last')
        else:
            st.error("Błąd: Brak kolumny 'Data' w arkuszu danych.")
            st.stop()
        
        NAZWY_MIESIECY = {
            1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
            5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
            9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
        }

        with st.sidebar:
            st.header("⚙️ USTAWIENIA")
            widok = st.sidebar.radio("WYBIERZ WIDOK:", [
                "Dashboard Główny",
                "Raport Dzienny", 
                "Zarządzanie i RPE", 
                "Siłownia i Regeneracja", 
                "Raport Sztabowy", 
                "Wykresy Drużynowe", 
                "Profil Indywidualny", 
                "🧠 AI & Ryzyko Urazów",
                "Surowe Dane"
            ])
            
            teraz = datetime.now(PL_TZ)
            wybrana_data = teraz.date() # Zabezpieczenie dla widoków bez kalendarza
            
            if widok in ["Dashboard Główny", "Raport Dzienny", "Wykresy Drużynowe", "Zarządzanie i RPE", "Siłownia i Regeneracja", "🧠 AI & Ryzyko Urazów"]:
                wybrana_data = st.date_input("Wybierz dzień analizy:", value=teraz.date())
            else:
                wybrany_rok = st.selectbox("Rok:", [2024, 2025, 2026], index=2 if teraz.year == 2026 else (1 if teraz.year == 2025 else 0))
                wybrany_miesiac_nazwa = st.selectbox("Miesiąc:", list(NAZWY_MIESIECY.values()), index=teraz.month-1)
                wybrany_miesiac_nr = [k for k, v in NAZWY_MIESIECY.items() if v == wybrany_miesiac_nazwa][0]
            
            st.write("---")
            if st.button("🔄 Odśwież Dane"):
                st.cache_data.clear()
                st.rerun()
            
            if st.button("Wyloguj"):
                st.session_state["auth_staff"] = False
                st.rerun()

            st.write("---")
            st.markdown("**STATUS BAZY DANYCH:**")
            if STATUS_GRUP == "OK":
                st.success("✅ Zawodnicy i Grupy zsynchronizowane.")
            else:
                st.error(f"⚠️ **Awaryjny kod.**<br>Powód: {STATUS_GRUP}", icon="🚨")

        # --- PRE-PROCESOWANIE DANYCH ---
        df_rpe_all = df[df['Typ_Raportu'] == 'RPE'].copy()
        df_rpe_all['RPE_num'] = pd.to_numeric(df_rpe_all['RPE'], errors='coerce').fillna(0)
        df_rpe_all['Dzień_dt'] = pd.to_datetime(df_rpe_all['Dzień'])

        df_well_all = df[df['Typ_Raportu'] == 'Wellness'].copy()
        kolumny_do_sumy = ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']
        if 'Zmeczenie_Mentalne' in df_well_all.columns:
            kolumny_do_sumy.append('Zmeczenie_Mentalne')
            
        for col in kolumny_do_sumy:
            if col in df_well_all.columns:
                df_well_all[col] = pd.to_numeric(df_well_all[col], errors='coerce').fillna(0)
                
        df_well_all['Readiness'] = df_well_all[kolumny_do_sumy].sum(axis=1)
        MAX_READINESS = len(kolumny_do_sumy) * 5
        df_well_all['Dzień_dt'] = pd.to_datetime(df_well_all['Dzień'])

        dzis_dt = pd.to_datetime(wybrana_data)
        science_team_data = []
        for z in LISTA_ZAWODNIKOW:
            z_rpe = df_rpe_all[(df_rpe_all['Zawodnik'] == z) & (df_rpe_all['Dzień_dt'] <= dzis_dt) & (df_rpe_all['Dzień_dt'] > dzis_dt - timedelta(days=28))]
            if not z_rpe.empty:
                z_daily = z_rpe.groupby('Dzień_dt')['RPE_num'].mean().reset_index()
                z_daily = z_daily.set_index('Dzień_dt').resample('D').asfreq().fillna(0).reset_index()
                acute = z_daily.iloc[-7:]['RPE_num'].mean() if len(z_daily) >= 7 else z_daily['RPE_num'].mean()
                chronic = z_daily['RPE_num'].mean()
                acwr = acute / chronic if chronic > 0 else 0
                science_team_data.append({"Zawodnik": z, "ACWR": acwr})
        df_acwr_today = pd.DataFrame(science_team_data)

        # --- LOGIKA WIDOKÓW ---
        if widok == "Dashboard Główny":
            st.markdown(f"<h2 style='text-align:left; color:#1B5E20;'>⚡ COMMAND CENTER ({wybrana_data})</h2>", unsafe_allow_html=True)
            
            df_well_day = df[(df['Dzień'] == wybrana_data) & (df['Typ_Raportu'] == 'Wellness')].copy()
            if not df_well_day.empty and 'Bolesnosc' in df_well_day.columns:
                df_well_day['Bolesnosc'] = pd.to_numeric(df_well_day['Bolesnosc'], errors='coerce')
                alerty_bolowe = df_well_day[df_well_day['Bolesnosc'] <= 2]
            else:
                alerty_bolowe = pd.DataFrame()
            liczba_bolowych = len(alerty_bolowe)
            
            zawodnicy_well = df_well_day['Zawodnik'].unique() if not df_well_day.empty else []
            brak_raportow = len(LISTA_ZAWODNIKOW) - len(zawodnicy_well)
            
            liczba_acwr_red = len(df_acwr_today[df_acwr_today['ACWR'] > 1.5]) if not df_acwr_today.empty else 0
            
            col_dash1, col_dash2, col_dash3 = st.columns(3)
            with col_dash1:
                klasa1 = "metric-card-red" if liczba_bolowych > 0 else "metric-card-green"
                st.markdown(f"<div class='{klasa1}' style='padding:20px; border-radius:10px; margin-bottom:15px;'>"
                            f"<h3 style='margin:0; font-size:1rem; color:#424242;'>🔴 ALERTY BÓLOWE</h3>"
                            f"<p style='font-size:2.5rem; font-weight:bold; margin:0; color:#212121;'>{liczba_bolowych}</p>"
                            f"</div>", unsafe_allow_html=True)
            with col_dash2:
                klasa2 = "metric-card-red" if liczba_acwr_red > 0 else "metric-card-green"
                st.markdown(f"<div class='{klasa2}' style='padding:20px; border-radius:10px; margin-bottom:15px;'>"
                            f"<h3 style='margin:0; font-size:1rem; color:#424242;'>⚠️ ACWR > 1.5 (Ryzyko)</h3>"
                            f"<p style='font-size:2.5rem; font-weight:bold; margin:0; color:#212121;'>{liczba_acwr_red}</p>"
                            f"</div>", unsafe_allow_html=True)
            with col_dash3:
                klasa3 = "metric-card-orange" if brak_raportow > 0 else "metric-card-green"
                st.markdown(f"<div class='{klasa3}' style='padding:20px; border-radius:10px; margin-bottom:15px;'>"
                            f"<h3 style='margin:0; font-size:1rem; color:#424242;'>🟡 BRAK RAPORTÓW DZIŚ</h3>"
                            f"<p style='font-size:2.5rem; font-weight:bold; margin:0; color:#212121;'>{brak_raportow}</p>"
                            f"</div>", unsafe_allow_html=True)

            st.write("---")
            col_det1, col_det2 = st.columns(2)
            with col_det1:
                st.markdown("#### SZCZEGÓŁY ALERTÓW BÓLOWYCH")
                if not alerty_bolowe.empty:
                    for _, row in alerty_bolowe.iterrows():
                        kom = row.get('Komentarz', 'Brak uwag')
                        if pd.isna(kom) or kom == "": kom = "Brak uwag"
                        st.error(f"**{row['Zawodnik']}** - Bolesność: {row['Bolesnosc']}/5 | Uwagi: {kom}")
                else:
                    st.success("Brak alertów bólowych w drużynie!")
                    
            with col_det2:
                st.markdown("#### LISTA BRAKUJĄCYCH RAPORTÓW")
                if brak_raportow > 0:
                    braki = [z for z in LISTA_ZAWODNIKOW if z not in zawodnicy_well]
                    st.warning(", ".join(braki))
                else:
                    st.success("Kompletny zespół przesłał raporty!")

        elif widok == "Raport Dzienny":
            st.subheader(f"📅 RAPORT GOTOWOŚCI: {wybrana_data}")
            df_day = df[df['Dzień'] == wybrana_data]
            df_well_day = df_day[df_day['Typ_Raportu'] == 'Wellness'].copy()
            for col in kolumny_do_sumy:
                if col in df_well_day.columns:
                    df_well_day[col] = pd.to_numeric(df_well_day[col], errors='coerce').fillna(0)
            
            bolesnosc_alert = df_well_day[df_well_day['Bolesnosc'].isin([1, 2, 1.0, 2.0])]
            z_alerts = []
            granica_14d = dzis_dt - timedelta(days=14)
            
            for z in df_well_day['Zawodnik'].unique():
                hist_z = df_well_all[(df_well_all['Zawodnik'] == z) & (df_well_all['Dzień_dt'] < dzis_dt) & (df_well_all['Dzień_dt'] >= granica_14d)]
                if len(hist_z) >= 3:
                    srednia_hist = hist_z['Readiness'].mean()
                    std_hist = hist_z['Readiness'].std()
                    wynik_dzis = df_well_day[df_well_day['Zawodnik'] == z].iloc[-1]
                    readiness_dzis = sum([float(wynik_dzis.get(c, 0)) for c in kolumny_do_sumy])
                    if std_hist > 0:
                        z_score = (readiness_dzis - srednia_hist) / std_hist
                        if z_score < -1.5:
                            z_alerts.append({
                                "Zawodnik": z, "Dzis": readiness_dzis, "Srednia": srednia_hist,
                                "Odchylenie": z_score, "Komentarz": wynik_dzis.get('Komentarz', '')
                            })

            if not bolesnosc_alert.empty or z_alerts:
                st.error("🚨 ALERTY SYSTEMOWE (Wymagany kontakt ze sztabem medycznym)")
                col_al1, col_al2 = st.columns(2)
                
                with col_al1:
                    if not bolesnosc_alert.empty:
                        st.markdown("<p style='color:red; font-size:1.1rem;'>🔴 SILNA BOLESNOŚĆ MIĘŚNIOWA:</p>", unsafe_allow_html=True)
                        for _, row in bolesnosc_alert.iterrows():
                            kom = row.get('Komentarz', '')
                            st.markdown(f"""<div style="background-color: #FFEBEE; padding: 10px; border-radius: 10px; border-left: 5px solid red; margin-bottom:10px;"><b style="color:red">{row['Zawodnik']}</b> - Bolesność: {float(row['Bolesnosc']):.0f}/5<br><small>Uwag: {kom}</small></div>""", unsafe_allow_html=True)
                
                with col_al2:
                    if z_alerts:
                        st.markdown("<p style='color:#FF9800; font-size:1.1rem;'>🟡 INDYWIDUALNY SPADEK REGENERACJI (Z-Score):</p>", unsafe_allow_html=True)
                        for al in z_alerts:
                            kom = al['Komentarz']
                            st.markdown(f"""<div style="background-color: #FFF3E0; padding: 10px; border-radius: 10px; border-left: 5px solid #FF9800; margin-bottom:10px;"><b style="color:#E65100">{al['Zawodnik']}</b> - Spadek o {abs(al['Odchylenie']):.1f} SD poniżej swojej normy!<br>Dziś: {al['Dzis']:.0f}/{MAX_READINESS} (Średnia: {al['Srednia']:.1f}/{MAX_READINESS})<br><small>Uwagi: {kom}</small></div>""", unsafe_allow_html=True)

            zawodnicy_raport = df_well_day['Zawodnik'].unique() if not df_well_day.empty else []
            brak_raportu = [z for z in LISTA_ZAWODNIKOW if z not in zawodnicy_raport]
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.success(f"✅ RAPORTY DOTARŁY ({len(zawodnicy_raport)})")
                ready_data = []
                for z in zawodnicy_raport:
                    z_data = df_well_day[df_well_day['Zawodnik'] == z].iloc[-1]
                    status_time = "🟢 O CZASIE" if z_data['Godzina_H'] < GODZINA_WELLNESS else "🟡 SPÓŹNIONY"
                    sen_val = pd.to_numeric(z_data.get('Sen', 0), errors='coerce')
                    zmeczenie_val = pd.to_numeric(z_data.get('Zmeczenie', 0), errors='coerce')
                    bolesnosc_val = pd.to_numeric(z_data.get('Bolesnosc', 0), errors='coerce')
                    stres_val = pd.to_numeric(z_data.get('Stres', 0), errors='coerce')
                    ment_val = pd.to_numeric(z_data.get('Zmeczenie_Mentalne', 0), errors='coerce')
                    
                    readiness_total = sum(filter(pd.notna, [sen_val, zmeczenie_val, bolesnosc_val, stres_val, ment_val]))
                    
                    wynik_dict = {
                        "Zawodnik": z, "Status": status_time, "Sen": int(sen_val) if pd.notna(sen_val) else 0, 
                        "Zmęcz. Fiz.": int(zmeczenie_val) if pd.notna(zmeczenie_val) else 0, 
                        "Bolesność": int(bolesnosc_val) if pd.notna(bolesnosc_val) else 0, 
                        "Stres": int(stres_val) if pd.notna(stres_val) else 0
                    }
                    if 'Zmeczenie_Mentalne' in df_well_day.columns:
                        wynik_dict["Zmęcz. Ment."] = int(ment_val) if pd.notna(ment_val) else 0
                    wynik_dict["READINESS"] = int(readiness_total)
                    ready_data.append(wynik_dict)
                
                if ready_data:
                    df_ready = pd.DataFrame(ready_data).sort_values("READINESS", ascending=True)
                    kol_do_kolorowania = ['Sen', 'Zmęcz. Fiz.', 'Bolesność', 'Stres']
                    if 'Zmęcz. Ment.' in df_ready.columns: kol_do_kolorowania.append('Zmęcz. Ment.')
                    
                    def color_scale_1_5(val):
                        try:
                            v = float(val)
                            if v <= 2: return 'background-color: #ffcccc; color: black;'
                            if v == 3: return 'background-color: #ffffcc; color: black;'
                            return 'background-color: #ccffcc; color: black;'
                        except: return ''
                    
                    format_dict = {"READINESS": "{:d}/"+str(MAX_READINESS)}
                    for k in kol_do_kolorowania: format_dict[k] = "{:d}"
                        
                    st.dataframe(df_ready.style.map(color_scale_1_5, subset=kol_do_kolorowania).background_gradient(subset=['READINESS'], cmap="RdYlGn", low=0, high=1).format(format_dict), hide_index=True, use_container_width=True)
                else:
                    st.info("Brak przesłanych raportów na ten dzień.")

            with c2:
                st.warning(f"❌ BRAKI ({len(brak_raportu)})")
                if brak_raportu:
                    for b_zawodnik in brak_raportu: st.write(f"• {b_zawodnik}")

        elif widok == "Zarządzanie i RPE":
            st.subheader(f"⚙️ ZARZĄDZANIE SESJĄ I ANALIZA RPE: {wybrana_data}")
            df_rpe_raw_day = df[(df['Dzień'] == wybrana_data) & (df['Typ_Raportu'] == 'RPE')]
            
            st.markdown("#### 🛠️ KONFIGURACJA GRUPY")
            c_conf1, c_conf2 = st.columns([1, 2])
            with c_conf1:
                czas_minut = st.number_input("Czas trwania sesji (min):", min_value=15, max_value=240, value=90, step=5)
            with c_conf2:
                zawodnicy_na_treningu = st.multiselect("Odhacz zawodników biorących udział w tej sesji:", options=LISTA_ZAWODNIKOW, default=LISTA_ZAWODNIKOW)

            df_rpe_filtered = df_rpe_raw_day[df_rpe_raw_day['Zawodnik'].isin(zawodnicy_na_treningu)].copy()
            
            st.write("---")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            df_rpe_filtered['RPE_num'] = pd.to_numeric(df_rpe_filtered['RPE'], errors='coerce')
            srednie_rpe = df_rpe_filtered['RPE_num'].mean() if not df_rpe_filtered.empty else 0.0
            liczba_wpisow = len(df_rpe_filtered)
            expected_total = len(zawodnicy_na_treningu)
            
            with col_stat1: st.metric("Średnie RPE Grupy", f"{srednie_rpe:.2f}")
            with col_stat2: st.metric("Status Raportów", f"{liczba_wpisow} / {expected_total}")
            with col_stat3: st.metric("Średni Load (TL)", f"{int(srednie_rpe * czas_minut)}")

            st.markdown("#### 📊 WYNIKI INDYWIDUALNE WYBRANEJ GRUPY")
            if not df_rpe_filtered.empty:
                rpe_summary = []
                for _, row in df_rpe_filtered.iterrows():
                    rpe_val = pd.to_numeric(row['RPE'], errors='coerce')
                    rpe_summary.append({
                        "Zawodnik": row['Zawodnik'], "RPE": int(rpe_val) if pd.notna(rpe_val) else 0, 
                        "Czas": int(czas_minut), "Indywidualny Load": int(rpe_val * czas_minut) if pd.notna(rpe_val) else 0, 
                        "Komentarz": row['Komentarz']
                    })
                df_rpe_summary = pd.DataFrame(rpe_summary)
                
                def color_rpe_scale(val):
                    try:
                        v = float(val)
                        if v <= 3: return 'background-color: #ccffcc; color: black;'
                        if v <= 6: return 'background-color: #ffffcc; color: black;'
                        if v <= 8: return 'background-color: #ffebcc; color: black;'
                        return 'background-color: #ffcccc; color: black;'
                    except: return ''
                        
                st.dataframe(df_rpe_summary.style.map(color_rpe_scale, subset=['RPE']).background_gradient(subset=['Indywidualny Load'], cmap="YlOrRd"), use_container_width=True, hide_index=True)
                braki_w_grupie = [z for z in zawodnicy_na_treningu if z not in df_rpe_filtered['Zawodnik'].values]
                if braki_w_grupie: st.warning(f"⚠️ Oczekiwanie na RPE (Grupa obecna): {', '.join(braki_w_grupie)}")
            else:
                st.info("Brak raportów RPE na ten dzień dla wybranej grupy.")

        # --- PANEL: ANALIZA I KREATOR SIŁOWNI ORAZ REGENERACJI ---
        elif widok == "Siłownia i Regeneracja":
            tab_gym_results, tab_plan_gym, tab_plan_regen = st.tabs(["📊 WYNIKI ZAWODNIKÓW", "🏋️ ZAPLANUJ SIŁOWNIĘ", "🌿 ZAPLANUJ REGENERACJĘ"])
            
            with tab_gym_results:
                st.subheader(f"🏋️ RAPORT TRENINGU Z DNIA: {wybrana_data}")
                
                try:
                    df_wyniki_silownia = conn.read(worksheet="Wyniki_Silownia", ttl=5)
                    if df_wyniki_silownia is not None and not df_wyniki_silownia.empty and 'Data' in df_wyniki_silownia.columns:
                        df_wyniki_silownia['Data_dt'] = pd.to_datetime(df_wyniki_silownia['Data'], errors='coerce')
                        df_gym = df_wyniki_silownia[df_wyniki_silownia['Data_dt'].dt.date == wybrana_data].copy()
                    else:
                        df_gym = pd.DataFrame()
                except:
                    df_gym = pd.DataFrame()
                
                if not df_gym.empty:
                    gym_results = []
                    for _, row in df_gym.iterrows():
                        zawodnik_wynik = row.get('Zawodnik', 'Nieznany')
                        tonaz = row.get('Tonaz_Calkowity_KG', 0.0)
                        uwagi = row.get('Uwagi', 'Brak')
                        if pd.isna(uwagi) or str(uwagi).strip() == "": uwagi = "Brak"
                        
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
                                    cwiczenia_zrealizowane.append(f"🏋️ {c_nazwa} ({', '.join(serie_text)}) -> Suma: {c_suma}kg")
                                else:
                                    # Pomijamy wpisy z 0kg zeby było czyściej
                                    pass
                                    
                        gym_results.append({
                            "Zawodnik": zawodnik_wynik, 
                            "Wstępny tonaż (kg)": int(tonaz), 
                            "Zrealizowany trening (Główne)": "\n".join(cwiczenia_zrealizowane) if cwiczenia_zrealizowane else "Tylko akcesoryjne / Brak pomiarów",
                            "Ogólne uwagi zawodnika": uwagi
                        })
                    
                    if gym_results:
                        df_gym_results = pd.DataFrame(gym_results)
                        st.dataframe(df_gym_results[['Zawodnik', "Wstępny tonaż (kg)", "Ogólne uwagi zawodnika"]], use_container_width=True, hide_index=True)
                        
                        st.write("---")
                        st.markdown("#### 🔍 DETALICZNA ANALIZA WYBRANEJ AKTYWNOŚCI")
                        wybrany_gracz_gym = st.selectbox("Wybierz zawodnika, aby zobaczyć szczegóły:", options=df_gym_results['Zawodnik'].unique())
                        if wybrany_gracz_gym:
                            gracz_row = df_gym_results[df_gym_results['Zawodnik'] == wybrany_gracz_gym].iloc[0]
                            st.info(f"**SUMARYCZNE OBCIĄŻENIE:** {gracz_row['Wstępny tonaż (kg)']} kg  |  **UWAGI ZAWODNIKA:** {gracz_row['Ogólne uwagi zawodnika']}")
                            for linia in gracz_row['Zrealizowany trening (Główne)'].split("\n"): st.write(f"• {linia}")
                else:
                    st.info(f"Brak zapisanych treningów z ciężarem w dniu {wybrana_data}.")
            
            with tab_plan_gym:
                st.subheader("🏋️ KREATOR PLANU SIŁOWEGO")
                
                df_plans = load_data("Plany")
                df_szablony = pobierz_szablony()
                
                if 'form_tytul' not in st.session_state: st.session_state['form_tytul'] = ""
                for i in range(1, 6):
                    if f'form_cw{i}_nazwa' not in st.session_state: st.session_state[f'form_cw{i}_nazwa'] = ""
                    if f'form_cw{i}_serie' not in st.session_state: st.session_state[f'form_cw{i}_serie'] = 4 if i <= 2 else 3
                    if f'form_cw{i}_opis' not in st.session_state: st.session_state[f'form_cw{i}_opis'] = ""
                    if f'form_cw{i}_link' not in st.session_state: st.session_state[f'form_cw{i}_link'] = ""
                    if f'form_cw{i}_glowne' not in st.session_state: st.session_state[f'form_cw{i}_glowne'] = False

                st.markdown('<div class="template-box">', unsafe_allow_html=True)
                st.markdown("#### 📂 WCZYTAJ GOTOWY SZABLON (Tylko siłownia)")
                if not df_szablony.empty:
                    lista_szablonow = df_szablony['Nazwa_Szablonu'].tolist()
                    wybrany_szablon = st.selectbox("Wybierz zapisany szablon z bazy:", ["-- Wybierz szablon --"] + lista_szablonow)
                    
                    if st.button("Pobierz dane z szablonu"):
                        if wybrany_szablon != "-- Wybierz szablon --":
                            szablon_dane = df_szablony[df_szablony['Nazwa_Szablonu'] == wybrany_szablon].iloc[0]
                            
                            val_tytul = str(szablon_dane.get('Tytul_Treningu', ''))
                            st.session_state['form_tytul'] = "" if val_tytul == 'nan' else val_tytul
                            
                            for i in range(1, 6):
                                val = str(szablon_dane.get(f'Cwiczenie_{i}', ''))
                                if val == 'nan' or val == '':
                                    st.session_state[f'form_cw{i}_nazwa'] = ""
                                    st.session_state[f'form_cw{i}_serie'] = 4 if i <= 2 else 3
                                    st.session_state[f'form_cw{i}_opis'] = ""
                                    st.session_state[f'form_cw{i}_link'] = ""
                                    st.session_state[f'form_cw{i}_glowne'] = False
                                else:
                                    serie_match = re.search(r"\[SERIE:(\d+)\]", val, re.IGNORECASE)
                                    serie = int(serie_match.group(1)) if serie_match else 3
                                    
                                    link_match = re.search(r"\[LINK:(.*?)\]", val, re.IGNORECASE)
                                    link_str = link_match.group(1).strip() if link_match else ""
                                    
                                    opis_match = re.search(r"\((.*?)\)", val)
                                    opis_str = opis_match.group(1).strip() if opis_match else ""
                                    
                                    glowne = "[GLOWNE]" in val.upper()
                                    
                                    nazwa = re.sub(r"\[SERIE:\d+\].*", "", val, flags=re.IGNORECASE).strip()
                                    nazwa = re.sub(r"\[GLOWNE\]", "", nazwa, flags=re.IGNORECASE).strip()
                                    
                                    st.session_state[f'form_cw{i}_nazwa'] = nazwa
                                    st.session_state[f'form_cw{i}_serie'] = serie
                                    st.session_state[f'form_cw{i}_opis'] = opis_str
                                    st.session_state[f'form_cw{i}_link'] = link_str
                                    st.session_state[f'form_cw{i}_glowne'] = glowne
                                    
                            st.success(f"Szablon '{wybrany_szablon}' wczytany pomyślnie!")
                            st.rerun()
                else:
                    st.info("Brak zapisanych szablonów w bazie (Zakładka 'Szablony').")
                st.markdown('</div>', unsafe_allow_html=True)
                
                with st.form("gym_only_form", border=True):
                    plan_date = st.date_input("Dzień realizacji treningu siłowego:", value=teraz.date())
                    
                    opcje_adresatow = ["Wszyscy"] + GRUPY_LISTA + LISTA_ZAWODNIKOW
                    adresat_planu = st.selectbox(
                        "Wybierz adresata planu (Grupa z arkusza lub konkretny Zawodnik):",
                        options=opcje_adresatow, index=0
                    )
                    
                    wykluczeni = st.multiselect("Wyklucz zawodników z tego planu (opcjonalnie):", options=LISTA_ZAWODNIKOW)
                    
                    st.markdown("### 🏋️ ĆWICZENIA (Z SERIAMI I CIĘŻARAMI)")
                    
                    tytul_planu = st.text_input("Tytuł treningu (widoczny w kalendarzu gracza):", value=st.session_state.get('form_tytul', ''), placeholder="np. Siła Dół A, FBW, Moc przedmeczowa")
                    
                    st.markdown("#### ĆWICZENIE 1")
                    cw1_nazwa = st.text_input("Nazwa ćwiczenia 1:", value=st.session_state['form_cw1_nazwa'], placeholder="np. Przysiad ze sztangą z tyłu")
                    col_p1_1, col_p1_2, col_p1_3, col_p1_4 = st.columns([1, 1.5, 1.5, 1])
                    with col_p1_1: cw1_serie = st.number_input("Liczba serii (Ćw 1):", min_value=1, max_value=10, value=st.session_state['form_cw1_serie'])
                    with col_p1_2: cw1_opis = st.text_input("Instrukcja (Ćw 1):", value=st.session_state['form_cw1_opis'], placeholder="np. 6 powt., tempo 3010", key="op1")
                    with col_p1_3: cw1_link = st.text_input("Link YT (Ćw 1):", value=st.session_state['form_cw1_link'], placeholder="https://youtu.be/...", key="lk1")
                    with col_p1_4: 
                        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
                        cw1_glowne = st.checkbox("Główne (Raport KG)", value=st.session_state['form_cw1_glowne'], key="gl1")
                        
                    st.markdown("#### ĆWICZENIE 2")
                    cw2_nazwa = st.text_input("Nazwa ćwiczenia 2:", value=st.session_state['form_cw2_nazwa'], placeholder="np. Wyciskanie hantli leżąc")
                    col_p2_1, col_p2_2, col_p2_3, col_p2_4 = st.columns([1, 1.5, 1.5, 1])
                    with col_p2_1: cw2_serie = st.number_input("Liczba serii (Ćw 2):", min_value=1, max_value=10, value=st.session_state['form_cw2_serie'])
                    with col_p2_2: cw2_opis = st.text_input("Instrukcja (Ćw 2):", value=st.session_state['form_cw2_opis'], placeholder="np. 8 powt., przerwa 90s", key="op2")
                    with col_p2_3: cw2_link = st.text_input("Link YT (Ćw 2):", value=st.session_state['form_cw2_link'], placeholder="https://youtu.be/...", key="lk2")
                    with col_p2_4: 
                        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
                        cw2_glowne = st.checkbox("Główne (Raport KG)", value=st.session_state['form_cw2_glowne'], key="gl2")

                    st.markdown("#### ĆWICZENIE 3")
                    cw3_nazwa = st.text_input("Nazwa ćwiczenia 3:", value=st.session_state['form_cw3_nazwa'], placeholder="np. Podciąganie na drążku")
                    col_p3_1, col_p3_2, col_p3_3, col_p3_4 = st.columns([1, 1.5, 1.5, 1])
                    with col_p3_1: cw3_serie = st.number_input("Liczba serii (Ćw 3):", min_value=1, max_value=10, value=st.session_state['form_cw3_serie'])
                    with col_p3_2: cw3_opis = st.text_input("Instrukcja (Ćw 3):", value=st.session_state['form_cw3_opis'], placeholder="np. maks powtórzeń", key="op3")
                    with col_p3_3: cw3_link = st.text_input("Link YT (Ćw 3):", value=st.session_state['form_cw3_link'], placeholder="https://youtu.be/...", key="lk3")
                    with col_p3_4: 
                        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
                        cw3_glowne = st.checkbox("Główne (Raport KG)", value=st.session_state['form_cw3_glowne'], key="gl3")

                    st.markdown("#### ĆWICZENIE 4")
                    cw4_nazwa = st.text_input("Nazwa ćwiczenia 4:", value=st.session_state['form_cw4_nazwa'], placeholder="np. Plank z obciążeniem")
                    col_p4_1, col_p4_2, col_p4_3, col_p4_4 = st.columns([1, 1.5, 1.5, 1])
                    with col_p4_1: cw4_serie = st.number_input("Liczba serii (Ćw 4):", min_value=1, max_value=10, value=st.session_state['form_cw4_serie'])
                    with col_p4_2: cw4_opis = st.text_input("Instrukcja (Ćw 4):", value=st.session_state['form_cw4_opis'], placeholder="np. 45 s, przerwa 60s", key="op4")
                    with col_p4_3: cw4_link = st.text_input("Link YT (Ćw 4):", value=st.session_state['form_cw4_link'], placeholder="https://youtu.be/...", key="lk4")
                    with col_p4_4: 
                        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
                        cw4_glowne = st.checkbox("Główne (Raport KG)", value=st.session_state['form_cw4_glowne'], key="gl4")

                    st.markdown("#### ĆWICZENIE 5")
                    cw5_nazwa = st.text_input("Nazwa ćwiczenia 5:", value=st.session_state['form_cw5_nazwa'], placeholder="np. Dead Bug z ciężarem")
                    col_p5_1, col_p5_2, col_p5_3, col_p5_4 = st.columns([1, 1.5, 1.5, 1])
                    with col_p5_1: cw5_serie = st.number_input("Liczba serii (Ćw 5):", min_value=1, max_value=10, value=st.session_state['form_cw5_serie'])
                    with col_p5_2: cw5_opis = st.text_input("Instrukcja (Ćw 5):", value=st.session_state['form_cw5_opis'], placeholder="np. 10 powt. na stronę", key="op5")
                    with col_p5_3: cw5_link = st.text_input("Link YT (Ćw 5):", value=st.session_state['form_cw5_link'], placeholder="https://youtu.be/...", key="lk5")
                    with col_p5_4: 
                        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
                        cw5_glowne = st.checkbox("Główne (Raport KG)", value=st.session_state['form_cw5_glowne'], key="gl5")

                    st.markdown("---")
                    st.markdown("### 💾 OPCJE ZAPISU SZABLONU")
                    zapisz_jako_szablon = st.checkbox("Zapisz ten układ ćwiczeń jako nowy Szablon na przyszłość")
                    nazwa_nowego_szablonu = st.text_input("Nazwa nowego szablonu (jeśli zapisujesz):", placeholder="np. Siła Dół A")

                    if st.form_submit_button("ZAPISZ PLAN SIŁOWY"):
                        if cw1_nazwa.strip() == "":
                            st.warning("⚠️ Plan musi zawierać przynajmniej jedno ćwiczenie (Ćwiczenie 1)!")
                        else:
                            if df_plans is not None and not df_plans.empty:
                                df_plans['Data_formatted'] = pd.to_datetime(df_plans['Data'], errors='coerce').dt.date
                            else:
                                df_plans = pd.DataFrame(columns=["Data", "Grupa_lub_Zawodnik", "Wykluczenia", "Tytul_Treningu", "Regeneracja", "Cwiczenie_1", "Cwiczenie_2", "Cwiczenie_3", "Cwiczenie_4", "Cwiczenie_5"])
                                df_plans['Data_formatted'] = []
                                
                            if 'Tytul_Treningu' not in df_plans.columns:
                                df_plans['Tytul_Treningu'] = ""
                            if 'Wykluczenia' not in df_plans.columns:
                                df_plans['Wykluczenia'] = ""
                                
                            df_plans['Tytul_Treningu'] = df_plans['Tytul_Treningu'].fillna("")
                            df_plans['Wykluczenia'] = df_plans['Wykluczenia'].fillna("")
                            
                            mask = (df_plans['Data_formatted'] == plan_date) & \
                                   (df_plans['Grupa_lub_Zawodnik'] == adresat_planu) & \
                                   (df_plans['Tytul_Treningu'] == tytul_planu.strip())
                            
                            istniejace = df_plans[mask]
                            
                            stary_regen = ""
                            if not istniejace.empty:
                                stary_regen = str(istniejace.iloc[0].get("Regeneracja", "")).replace('nan', '')
                            
                            def format_cwiczenie(nazwa, serie, opis, link, glowne):
                                if not nazwa.strip(): return ""
                                string_cw = f"{nazwa.strip()} [SERIE:{serie}]"
                                if opis.strip(): string_cw += f" ({opis.strip()})"
                                if link.strip(): string_cw += f" [LINK:{link.strip()}]"
                                if glowne: string_cw += " [GLOWNE]"
                                return string_cw

                            nowy_plan = {
                                "Data": plan_date.strftime("%Y-%m-%d"),
                                "Grupa_lub_Zawodnik": adresat_planu,
                                "Wykluczenia": ", ".join(wykluczeni),
                                "Tytul_Treningu": tytul_planu.strip(),
                                "Regeneracja": stary_regen,
                                "Cwiczenie_1": format_cwiczenie(cw1_nazwa, cw1_serie, cw1_opis, cw1_link, cw1_glowne),
                                "Cwiczenie_2": format_cwiczenie(cw2_nazwa, cw2_serie, cw2_opis, cw2_link, cw2_glowne),
                                "Cwiczenie_3": format_cwiczenie(cw3_nazwa, cw3_serie, cw3_opis, cw3_link, cw3_glowne),
                                "Cwiczenie_4": format_cwiczenie(cw4_nazwa, cw4_serie, cw4_opis, cw4_link, cw4_glowne),
                                "Cwiczenie_5": format_cwiczenie(cw5_nazwa, cw5_serie, cw5_opis, cw5_link, cw5_glowne)
                            }
                            
                            df_plans = df_plans[~mask]
                            df_plans = df_plans.drop(columns=['Data_formatted'], errors='ignore')
                            updated_plans = pd.concat([df_plans, pd.DataFrame([nowy_plan])], ignore_index=True)
                            
                            try:
                                conn.update(worksheet="Plany", data=updated_plans)
                                st.success(f"✔ PLAN SIŁOWY DLA {adresat_planu.upper()} ZOSTAŁ ZAPISANY!")
                                
                                if zapisz_jako_szablon and nazwa_nowego_szablonu.strip() != "":
                                    nowy_szablon_dane = {
                                        "Nazwa_Szablonu": nazwa_nowego_szablonu.strip(),
                                        "Tytul_Treningu": tytul_planu.strip(),
                                        "Regeneracja": "",
                                        "Cwiczenie_1": nowy_plan["Cwiczenie_1"],
                                        "Cwiczenie_2": nowy_plan["Cwiczenie_2"],
                                        "Cwiczenie_3": nowy_plan["Cwiczenie_3"],
                                        "Cwiczenie_4": nowy_plan["Cwiczenie_4"],
                                        "Cwiczenie_5": nowy_plan["Cwiczenie_5"]
                                    }
                                    if df_szablony is not None and not df_szablony.empty:
                                        df_szablony = df_szablony[df_szablony['Nazwa_Szablonu'] != nazwa_nowego_szablonu.strip()]
                                    else:
                                        df_szablony = pd.DataFrame(columns=["Nazwa_Szablonu", "Tytul_Treningu", "Regeneracja", "Cwiczenie_1", "Cwiczenie_2", "Cwiczenie_3", "Cwiczenie_4", "Cwiczenie_5"])
                                    
                                    df_sz_updated = pd.concat([df_szablony, pd.DataFrame([nowy_szablon_dane])], ignore_index=True)
                                    conn.update(worksheet="Szablony", data=df_sz_updated)
                                    st.success(f"✔ Szablon '{nazwa_nowego_szablonu}' został zapisany.")
                                
                                st.cache_data.clear()
                                
                            except Exception as e:
                                st.error(f"Błąd zapisu planu/szablonu: {e}")

            with tab_plan_regen:
                st.subheader("🌿 KREATOR PLANU REGENERACJI / INNE")
                with st.form("regen_only_form", border=True):
                    plan_date_reg = st.date_input("Dzień realizacji odnowy:", value=teraz.date())
                    
                    opcje_adresatow = ["Wszyscy"] + GRUPY_LISTA + LISTA_ZAWODNIKOW
                    adresat_planu_reg = st.selectbox(
                        "Wybierz adresata planu (Grupa z arkusza lub konkretny Zawodnik):",
                        options=opcje_adresatow, index=0
                    )
                    
                    wykluczeni_reg = st.multiselect("Wyklucz zawodników (opcjonalnie):", options=LISTA_ZAWODNIKOW, key="wykl_reg")
                    
                    regeneracja_opis = st.text_area(
                        "Zalecenia odnowy (np. Sauna, Basen, Rozciąganie, Odprawa wideo):", 
                        placeholder="Wpisz aktywności oddzielając je przecinkiem."
                    )
                    
                    if st.form_submit_button("ZAPISZ PLAN REGENERACJI"):
                        if regeneracja_opis.strip() == "":
                            st.warning("⚠️ Pole z regeneracją nie może być puste!")
                        else:
                            if df_plans is not None and not df_plans.empty:
                                df_plans['Data_formatted'] = pd.to_datetime(df_plans['Data'], errors='coerce').dt.date
                            else:
                                df_plans = pd.DataFrame(columns=["Data", "Grupa_lub_Zawodnik", "Wykluczenia", "Tytul_Treningu", "Regeneracja", "Cwiczenie_1", "Cwiczenie_2", "Cwiczenie_3", "Cwiczenie_4", "Cwiczenie_5"])
                                df_plans['Data_formatted'] = []
                                
                            if 'Wykluczenia' not in df_plans.columns:
                                df_plans['Wykluczenia'] = ""
                                
                            mask_reg = (df_plans['Data_formatted'] == plan_date_reg) & \
                                       (df_plans['Grupa_lub_Zawodnik'] == adresat_planu_reg)
                                       
                            istniejace_reg = df_plans[mask_reg]
                            
                            if not istniejace_reg.empty:
                                idx_to_update = istniejace_reg.index[0]
                                df_plans.at[idx_to_update, 'Regeneracja'] = regeneracja_opis.replace("\n", ", ")
                                df_plans.at[idx_to_update, 'Wykluczenia'] = ", ".join(wykluczeni_reg)
                                updated_plans = df_plans.drop(columns=['Data_formatted'], errors='ignore')
                            else:
                                nowy_plan_reg = {
                                    "Data": plan_date_reg.strftime("%Y-%m-%d"),
                                    "Grupa_lub_Zawodnik": adresat_planu_reg,
                                    "Wykluczenia": ", ".join(wykluczeni_reg),
                                    "Tytul_Treningu": "",
                                    "Regeneracja": regeneracja_opis.replace("\n", ", "),
                                    "Cwiczenie_1": "", "Cwiczenie_2": "", "Cwiczenie_3": "", "Cwiczenie_4": "", "Cwiczenie_5": ""
                                }
                                df_plans = df_plans.drop(columns=['Data_formatted'], errors='ignore')
                                updated_plans = pd.concat([df_plans, pd.DataFrame([nowy_plan_reg])], ignore_index=True)
                            
                            try:
                                conn.update(worksheet="Plany", data=updated_plans)
                                st.success(f"✔ PLAN REGENERACJI DLA {adresat_planu_reg.upper()} ZOSTAŁ ZAPISANY!")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"Błąd zapisu planu: {e}")

        elif widok == "Raport Sztabowy":
            st.subheader(f"📋 ZESTAWIENIE DYSCYPLINY: {wybrany_miesiac_nazwa.upper()}")
            df_month = df[(df['Data'].dt.month == wybrany_miesiac_nr) & (df['Data'].dt.year == wybrany_rok)]
            dni_max = calendar.monthrange(wybrany_rok, wybrany_miesiac_nr)[1]
            dni_analizy = teraz.day if (wybrany_rok == teraz.year and wybrany_miesiac_nr == teraz.month) else dni_max

            wszystkie_dni_miesiaca = [date(wybrany_rok, wybrany_miesiac_nr, d) for d in range(1, dni_max + 1)]
            dni_przeszle = [d for d in wszystkie_dni_miesiaca if d <= teraz.date()] if (wybrany_rok == teraz.year and wybrany_miesiac_nr == teraz.month) else wszystkie_dni_miesiaca
            
            dni_tyg_skrot = ["Pon", "Wto", "Śro", "Czw", "Pią", "Sob", "Nie"]
            
            st.markdown("##### 🏖️ Dni wolne (brak obowiązku wypełniania)")
            wybrane_dni_wolne = st.multiselect(
                "Wybierz dni wolne w tym miesiącu (nie będą wliczane jako braki):",
                options=wszystkie_dni_miesiaca,
                format_func=lambda x: f"{x.strftime('%d.%m')} ({dni_tyg_skrot[x.weekday()]})"
            )
            
            oczekiwane_daty = set([d for d in dni_przeszle if d not in wybrane_dni_wolne])

            stats_wellness = []
            stats_rpe = []
            
            for z in LISTA_ZAWODNIKOW:
                p_data = df_month[df_month['Zawodnik'] == z]
                
                well = p_data[p_data['Typ_Raportu'] == 'Wellness']
                well_valid = well[well['Data'].dt.date.isin(oczekiwane_daty)]
                
                well_on_time = well_valid[well_valid['Godzina_H'] < GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_late = well_valid[well_valid['Godzina_H'] >= GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_braki = len(oczekiwane_daty - set(well_valid['Data'].dt.date))
                
                stats_wellness.append({"Zawodnik": z, "O czasie": well_on_time, "Spóźnione": well_late, "Braki": well_braki})
                
                rpe_d = p_data[p_data['Typ_Raportu'] == 'RPE']
                rpe_valid = rpe_d[rpe_d['Data'].dt.date.isin(oczekiwane_daty)]
                
                rpe_on_time = rpe_valid[rpe_valid['Godzina_H'] < GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_late = rpe_valid[rpe_valid['Godzina_H'] >= GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_braki = len(oczekiwane_daty - set(rpe_valid['Data'].dt.date))
                
                stats_rpe.append({"Zawodnik": z, "O czasie": rpe_on_time, "Spóźnione": rpe_late, "Braki": rpe_braki})

            df_well_f = pd.DataFrame(stats_wellness).sort_values("Braki", ascending=False)
            df_rpe_f = pd.DataFrame(stats_rpe).sort_values("Braki", ascending=False)

            def style_o_czasie(val):
                return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold;' if val > 0 else 'color: #9E9E9E;'

            def style_spoznione(val):
                return 'background-color: #FFF59D; color: #E65100; font-weight: bold;' if val > 0 else 'color: #9E9E9E;'

            def style_braki(val):
                return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold;' if val > 0 else 'color: #9E9E9E;'

            styled_well = df_well_f.style.map(style_o_czasie, subset=['O czasie']).map(style_spoznione, subset=['Spóźnione']).map(style_braki, subset=['Braki'])
            styled_rpe = df_rpe_f.style.map(style_o_czasie, subset=['O czasie']).map(style_spoznione, subset=['Spóźnione']).map(style_braki, subset=['Braki'])

            col_w, col_r = st.columns(2)
            with col_w:
                st.markdown(f"### WELLNESS (Limit {GODZINA_WELLNESS}:00)")
                st.dataframe(styled_well, use_container_width=True, hide_index=True)
            with col_r:
                st.markdown(f"### RPE (Limit {GODZINA_RPE}:00)")
                st.dataframe(styled_rpe, use_container_width=True, hide_index=True)

        elif widok == "Wykresy Drużynowe":
            tab_team_well, tab_team_science, tab_korelacja = st.tabs(["📊 SAMOPOCZUCIE", "🏃 SPORTS SCIENCE (ACWR)", "📈 KORELACJA (Load vs Readiness)"])
            
            with tab_team_well:
                st.subheader(f"🟢 ANALIZA GOTOWOŚCI DRUŻYNY: {wybrana_data}")
                df_day_well = df[(df['Dzień'] == wybrana_data) & (df['Typ_Raportu'] == 'Wellness')].copy()
                
                if not df_day_well.empty:
                    for col in kolumny_do_sumy:
                        if col in df_day_well.columns:
                            df_day_well[col] = pd.to_numeric(df_day_well[col], errors='coerce').fillna(0)
                    
                    df_day_well['Readiness'] = df_day_well[kolumny_do_sumy].sum(axis=1)
                    avg_readiness = df_day_well['Readiness'].mean()
                    
                    fig_read = px.bar(
                        df_day_well.sort_values("Readiness", ascending=False), 
                        x='Zawodnik', 
                        y='Readiness', 
                        color='Readiness', 
                        range_y=[0, MAX_READINESS], 
                        color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'],
                        title=f"Gotowość na Dzień {wybrana_data} (Średnia: {avg_readiness:.2f}/{MAX_READINESS})"
                    )
                    fig_read.add_hline(y=avg_readiness, line_dash="dash", line_color="black", annotation_text=f"Średnia Grupy: {avg_readiness:.2f}", annotation_position="top right")
                    st.plotly_chart(fig_read, use_container_width=True)
                    
                    c_dist1, c_dist2 = st.columns(2)
                    with c_dist1:
                        fig_pie = px.pie(df_day_well, names='Zmeczenie', title="Rozkład Zmęczenia Fiz. (1-5)", color_discrete_sequence=px.colors.sequential.RdBu)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with c_dist2:
                        fig_pie2 = px.pie(df_day_well, names='Sen', title="Rozkład Jakości Snu (1-5)", color_discrete_sequence=px.colors.sequential.Greens)
                        st.plotly_chart(fig_pie2, use_container_width=True)
                else: 
                    st.warning(f"Brak danych Wellness dla dnia {wybrana_data}.")

            with tab_team_science:
                st.subheader(f"🧠 DRUŻYNOWY PANEL OBCIĄŻEŃ (SPORTS SCIENCE)")
                st.markdown("<p style='text-align: center;'>Analiza ryzyka kontuzji drużyny na podstawie współczynnika ACWR i Monotonii z ostatnich 28 dni.</p>", unsafe_allow_html=True)
                
                science_team_data = []
                for z in LISTA_ZAWODNIKOW:
                    z_rpe = df_rpe_all[(df_rpe_all['Zawodnik'] == z) & (df_rpe_all['Dzień_dt'] <= dzis_dt) & (df_rpe_all['Dzień_dt'] > dzis_dt - timedelta(days=28))]
                    
                    if not z_rpe.empty:
                        z_daily = z_rpe.groupby('Dzień_dt')['RPE_num'].mean().reset_index()
                        z_daily = z_daily.set_index('Dzień_dt').resample('D').asfreq().fillna(0).reset_index()
                        
                        acute = z_daily.iloc[-7:]['RPE_num'].mean() if len(z_daily) >= 7 else z_daily['RPE_num'].mean()
                        chronic = z_daily['RPE_num'].mean()
                        acwr = acute / chronic if chronic > 0 else 0
                        
                        last_7_days = z_daily.iloc[-7:]['RPE_num']
                        std_7 = last_7_days.std()
                        mean_7 = last_7_days.mean()
                        monotony = mean_7 / std_7 if std_7 > 0 else 1.0
                        strain = monotony * last_7_days.sum()
                        
                        science_team_data.append({
                            "Zawodnik": z, "Ostry (7 dni)": round(acute, 2), "Przewlekły (28 dni)": round(chronic, 2),
                            "ACWR (Wskaźnik)": round(acwr, 2), "Monotonia": round(monotony, 2), "Napięcie (Strain)": int(strain)
                        })
                
                if science_team_data:
                    df_science_team = pd.DataFrame(science_team_data)
                    def color_acwr_scale(val):
                        try:
                            v = float(val)
                            if v < 0.8: return 'background-color: #e3f2fd; color: #1565c0;'
                            if v <= 1.3: return 'background-color: #e8f5e9; color: #2e7d32;'
                            if v <= 1.5: return 'background-color: #fffde7; color: #f57f17;'
                            return 'background-color: #ffebee; color: #c62828; font-weight: bold;'
                        except: return ''
                    st.dataframe(df_science_team.style.map(color_acwr_scale, subset=['ACWR (Wskaźnik)']).background_gradient(subset=['Napięcie (Strain)'], cmap="Oranges"), use_container_width=True, hide_index=True)
                else:
                    st.info("Brak wystarczającej ilości danych historycznych do kalkulacji ACWR zespołu.")
            
            with tab_korelacja:
                st.subheader("📈 KORELACJA KRZYŻOWA: Obciążenie z Wczoraj vs Gotowość na Dziś")
                st.markdown("Wykres punktowy pomagający wyłapać graczy, którzy źle znoszą wysokie obciążenia.")
                
                wczoraj_dt = dzis_dt - timedelta(days=1)
                df_rpe_wczoraj = df_rpe_all[df_rpe_all['Dzień_dt'] == wczoraj_dt].copy()
                df_well_dzis = df_well_all[df_well_all['Dzień_dt'] == dzis_dt].copy()
                
                if not df_rpe_wczoraj.empty and not df_well_dzis.empty:
                    df_rpe_wczoraj['Load_Wczoraj'] = df_rpe_wczoraj['RPE_num'] * 90 
                    
                    df_korelacja = pd.merge(df_well_dzis[['Zawodnik', 'Readiness']], df_rpe_wczoraj[['Zawodnik', 'Load_Wczoraj']], on='Zawodnik', how='inner')
                    
                    if not df_korelacja.empty:
                        fig_scatter = px.scatter(
                            df_korelacja, x="Load_Wczoraj", y="Readiness", text="Zawodnik", 
                            title=f"Gotowość ({wybrana_data}) w stosunku do obciążenia z {wczoraj_dt.date()}",
                            labels={"Load_Wczoraj": "Wczorajszy Load (RPE * Czas)", "Readiness": f"Dzisiejsza Gotowość (0-{MAX_READINESS})"},
                            size_max=60
                        )
                        fig_scatter.update_traces(textposition='top center', marker=dict(size=12, color=COLOR_PRIMARY))
                        fig_scatter.add_hrect(y0=0, y1=MAX_READINESS*0.5, line_width=0, fillcolor="rgba(244, 67, 54, 0.15)", annotation_text="Strefa Zmęczenia", annotation_position="top left")
                        st.plotly_chart(fig_scatter, use_container_width=True)
                    else:
                        st.warning("Brak zawodników, którzy zgłosili RPE wczoraj i Wellness dzisiaj.")
                else:
                    st.info("Brak wystarczających danych (RPE z wczoraj lub Wellness z dziś) do narysowania wykresu korelacji.")

        elif widok == "Profil Indywidualny":
            zawodnik = st.selectbox("Wybierz zawodnika:", LISTA_ZAWODNIKOW)
            df_month = df[(df['Data'].dt.month == teraz.month) & (df['Data'].dt.year == teraz.year)].copy()
            p_data = df_month[df_month['Zawodnik'] == zawodnik]
            
            if p_data.empty: 
                st.warning("Brak danych dla wybranego zawodnika w bieżącym miesiącu.")
            else:
                tab_ind_well, tab_ind_science, tab_heatmap = st.tabs(["📊 WELLNESS & REGENERACJA", "🧠 OBCIĄŻENIA (ACWR ZEGAR)", "📅 HEATMAPA WELLNESS"])
                
                with tab_ind_well:
                    well_p = p_data[p_data['Typ_Raportu'] == 'Wellness'].copy()
                    if not well_p.empty:
                        for col in kolumny_do_sumy:
                            if col in well_p.columns:
                                well_p[col] = pd.to_numeric(well_p[col], errors='coerce').fillna(0)
                        
                        ostatni = well_p.sort_values('Data').iloc[-1]
                        total_readiness = int(sum([ostatni.get(c, 0) for c in kolumny_do_sumy]))
                        
                        st.markdown(f"### PROFIL: {zawodnik}")
                        st.metric("Ostatni Readiness", f"{total_readiness} / {MAX_READINESS}")
                        
                        dostepne_kol = [c for c in kolumny_do_sumy if c in ostatni.index]
                        wartosci = [ostatni[c] for c in dostepne_kol]
                        
                        fig_radar = go.Figure(data=go.Scatterpolar(
                            r=wartosci, theta=dostepne_kol, fill='toself', line_color=COLOR_PRIMARY
                        ))
                        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
                        st.plotly_chart(fig_radar, use_container_width=True)
                        
                        well_p['Sum_Readiness'] = well_p[kolumny_do_sumy].sum(axis=1)
                        fig_line = px.line(well_p.sort_values('Data'), x='Data', y='Sum_Readiness', title="Trend Gotowości (Miesiąc)")
                        st.plotly_chart(fig_line, use_container_width=True)
                    else:
                        st.info("Brak raportów Wellness dla wybranego gracza w tym miesiącu.")
                
                with tab_ind_science:
                    st.subheader(f"📈 ANALIZA OBCIĄŻEŃ GRACZA: {zawodnik.upper()}")
                    gracz_rpe = df_rpe_all[df_rpe_all['Zawodnik'] == zawodnik]
                    
                    if len(gracz_rpe) >= 3:
                        gracz_daily = gracz_rpe.groupby('Dzień_dt')['RPE_num'].mean().reset_index()
                        gracz_daily = gracz_daily.set_index('Dzień_dt').resample('D').asfreq().fillna(0).reset_index()
                        
                        gracz_daily['Acute_MA'] = gracz_daily['RPE_num'].rolling(window=7, min_periods=1).mean()
                        gracz_daily['Chronic_MA'] = gracz_daily['RPE_num'].rolling(window=28, min_periods=1).mean()
                        gracz_daily['ACWR_Ratio'] = gracz_daily['Acute_MA'] / gracz_daily['Chronic_MA'].replace(0, 1)
                        
                        cur_acwr = gracz_daily['ACWR_Ratio'].iloc[-1]
                        last_7 = gracz_daily.iloc[-7:]['RPE_num']
                        std_7 = last_7.std()
                        mean_7 = last_7.mean()
                        cur_monotony = mean_7 / std_7 if std_7 > 0 else 1.0
                        cur_strain = cur_monotony * last_7.sum()
                        
                        c_sci1, c_sci2, c_sci3 = st.columns(3)
                        
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = cur_acwr,
                            title = {'text': "Współczynnik ACWR"},
                            gauge = {
                                'axis': {'range': [0, 2.5], 'tickwidth': 1, 'tickcolor': "darkblue"},
                                'bar': {'color': "black", 'thickness': 0.25},
                                'steps': [
                                    {'range': [0, 0.8], 'color': "#e3f2fd"},
                                    {'range': [0.8, 1.3], 'color': "#c8e6c9"},
                                    {'range': [1.3, 1.5], 'color': "#ffe0b2"},
                                    {'range': [1.5, 2.5], 'color': "#ffcdd2"}
                                ]
                            }
                        ))
                        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                        with c_sci1: st.plotly_chart(fig_gauge, use_container_width=True)
                        with c_sci2: st.metric("Monotonia Treningowa", f"{cur_monotony:.2f}", help="Średnia / Odchylenie Standardowe z 7 dni.")
                        with c_sci3: st.metric("Napięcie (Strain)", f"{int(cur_strain)}", help="Skumulowany stres fizjologiczny zawodnika z ostatniego tygodnia.")
                            
                        fig_acwr_trend = go.Figure()
                        fig_acwr_trend.add_trace(go.Scatter(x=gracz_daily['Dzień_dt'], y=gracz_daily['ACWR_Ratio'], name='Wskaźnik ACWR', line=dict(color=COLOR_PRIMARY, width=3)))
                        fig_acwr_trend.add_hrect(y0=0.8, y1=1.3, line_width=0, fillcolor="rgba(76, 175, 80, 0.15)", annotation_text="Optymalny Trening (0.8 - 1.3)", annotation_position="top left")
                        fig_acwr_trend.add_hrect(y0=1.5, y1=3.0, line_width=0, fillcolor="rgba(244, 67, 54, 0.15)", annotation_text="Strefa Kontuzji (> 1.5)", annotation_position="top left")
                        fig_acwr_trend.update_layout(title="Krzywa Zmęczenia do Formy (Wskaźnik ACWR)", yaxis_title="Współczynnik Ratio", xaxis_title="Data")
                        st.plotly_chart(fig_acwr_trend, use_container_width=True)
                    else:
                        st.info("Zawodnik musi posiadać co najmniej 3 zgłoszone raporty RPE, aby obliczyć indywidualne trendy ACWR.")
                
                with tab_heatmap:
                    st.subheader(f"📅 MIESIĘCZNA HEATMAPA WELLNESS")
                    well_hist = df_well_all[df_well_all['Zawodnik'] == zawodnik].copy()
                    if not well_hist.empty:
                        start_date = dzis_dt - timedelta(days=90)
                        well_hist = well_hist[well_hist['Dzień_dt'] >= start_date].copy()
                        well_hist['Tydzien'] = well_hist['Dzień_dt'].dt.isocalendar().week
                        well_hist['Dzien_Tyg'] = well_hist['Dzień_dt'].dt.dayofweek
                        
                        pivot_well = well_hist.pivot_table(index='Dzien_Tyg', columns='Tydzien', values='Readiness', aggfunc='mean')
                        
                        all_days = list(range(7))
                        for d in all_days:
                            if d not in pivot_well.index: pivot_well.loc[d] = np.nan
                        pivot_well = pivot_well.sort_index()
                        
                        nazwy_dni = ["Pon", "Wto", "Śro", "Czw", "Pią", "Sob", "Nie"]
                        
                        fig_hm = px.imshow(
                            pivot_well, 
                            labels=dict(x="Tydzień Roku", y="Dzień Tygodnia", color="Gotowość"),
                            y=nazwy_dni,
                            color_continuous_scale="RdYlGn",
                            range_color=[0, MAX_READINESS],
                            aspect="auto",
                            title=f"Aktywność (Ostatnie 90 dni) - Skala do {MAX_READINESS}"
                        )
                        fig_hm.update_xaxes(side="top")
                        st.plotly_chart(fig_hm, use_container_width=True)
                    else:
                        st.info("Brak wystarczających danych do wygenerowania heatmapy.")

        elif widok == "🧠 AI & Ryzyko Urazów":
            tab_ai_pred, tab_ai_log = st.tabs(["🔮 PREDYKCJA AI (Algorytm)", "🚑 REJESTR URAZÓW (Baza dla ML)"])
            
            with tab_ai_pred:
                st.markdown(f"<h2 style='text-align:left; color:#1B5E20;'>🧠 MODUŁ AI: PREDYKCJA RYZYKA ({wybrana_data})</h2>", unsafe_allow_html=True)
                st.write("Algorytm krzyżuje aktualny wskaźnik ACWR, dzisiejsze samopoczucie oraz indywidualne odchylenia formy (Z-Score), aby oszacować % ryzyko kontuzji przeciążeniowej.")
                
                dzis_dt = pd.to_datetime(wybrana_data)
                granica_14d = dzis_dt - timedelta(days=14)
                
                ai_results = []
                
                df_well_day = df[(df['Dzień'] == wybrana_data) & (df['Typ_Raportu'] == 'Wellness')].copy()
                for col in kolumny_do_sumy:
                    if col in df_well_day.columns:
                        df_well_day[col] = pd.to_numeric(df_well_day[col], errors='coerce').fillna(0)
                        
                for z in LISTA_ZAWODNIKOW:
                    risk_score = 5 
                    powody = []
                    rekomendacja = "Optymalny stan. Kontynuuj plan treningowy."
                    
                    acwr_val = 1.0
                    z_rpe = df_rpe_all[(df_rpe_all['Zawodnik'] == z) & (df_rpe_all['Dzień_dt'] <= dzis_dt) & (df_rpe_all['Dzień_dt'] > dzis_dt - timedelta(days=28))]
                    if not z_rpe.empty:
                        z_daily = z_rpe.groupby('Dzień_dt')['RPE_num'].mean().reset_index()
                        z_daily = z_daily.set_index('Dzień_dt').resample('D').asfreq().fillna(0).reset_index()
                        acute = z_daily.iloc[-7:]['RPE_num'].mean() if len(z_daily) >= 7 else z_daily['RPE_num'].mean()
                        chronic = z_daily['RPE_num'].mean()
                        acwr_val = acute / chronic if chronic > 0 else 0
                        
                        if acwr_val > 1.5:
                            risk_score += 40
                            powody.append("Krytyczny ACWR (>1.5)")
                            rekomendacja = "🔴 NATYCHMIAST: Zmniejsz obciążenie o 30-40%. Brak ćwiczeń eksplozywnych."
                        elif acwr_val > 1.3:
                            risk_score += 20
                            powody.append("Podwyższony ACWR")
                            if rekomendacja == "Optymalny stan. Kontynuuj plan treningowy.": rekomendacja = "🟡 OSTRZEŻENIE: Uważnie monitoruj mikrourazy. Rozważ lżejszą jednostkę."
                        elif acwr_val < 0.8 and acwr_val > 0:
                            risk_score += 15
                            powody.append("Niedotrenowanie (<0.8)")
                            
                    wynik_dzis = df_well_day[df_well_day['Zawodnik'] == z]
                    if not wynik_dzis.empty:
                        dzis_dane = wynik_dzis.iloc[-1]
                        bolesnosc = float(dzis_dane.get('Bolesnosc', 5))
                        sen = float(dzis_dane.get('Sen', 5))
                        
                        if bolesnosc <= 2:
                            risk_score += 25
                            powody.append("Silna bolesność mięśniowa")
                            rekomendacja = "🔴 INTERWENCJA: Wymagana konsultacja z fizjoterapeutą przed treningiem."
                        elif bolesnosc == 3:
                            risk_score += 10
                            
                        if sen <= 2:
                            risk_score += 15
                            powody.append("Bardzo słaby sen")
                            
                        hist_z = df_well_all[(df_well_all['Zawodnik'] == z) & (df_well_all['Dzień_dt'] < dzis_dt) & (df_well_all['Dzień_dt'] >= granica_14d)]
                        if len(hist_z) >= 5:
                            srednia_hist = hist_z['Readiness'].mean()
                            std_hist = hist_z['Readiness'].std()
                            readiness_dzis = sum([float(dzis_dane.get(c, 0)) for c in kolumny_do_sumy])
                            if std_hist > 0:
                                z_score = (readiness_dzis - srednia_hist) / std_hist
                                if z_score < -1.5:
                                    risk_score += 20
                                    powody.append(f"Nagły spadek formy (Z-Score: {z_score:.1f})")
                    else:
                        powody.append("Brak dzisiejszego raportu")
                        
                    risk_score = min(risk_score, 95)
                    
                    if risk_score >= 60: status = "🔴 WYSOKIE RYZYKO"
                    elif risk_score >= 30: status = "🟡 ŚREDNIE RYZYKO"
                    else: status = "🟢 NISKIE RYZYKO"
                    
                    ai_results.append({
                        "Zawodnik": z,
                        "Ryzyko %": risk_score,
                        "Status": status,
                        "ACWR": round(acwr_val, 2),
                        "Główne Czynniki Ryzyka": " | ".join(powody) if powody else "Brak uwag",
                        "Rekomendacja Systemu": rekomendacja
                    })
                    
                df_ai = pd.DataFrame(ai_results).sort_values("Ryzyko %", ascending=False)
                
                def style_risk(val):
                    if val >= 60: return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold;'
                    if val >= 30: return 'background-color: #FFF9C4; color: #F57F17; font-weight: bold;'
                    return 'background-color: #C8E6C9; color: #1B5E20;'

                st.dataframe(df_ai.style.map(style_risk, subset=['Ryzyko %']).format({"Ryzyko %": "{:.0f}%", "ACWR": "{:.2f}"}), use_container_width=True, hide_index=True)

            with tab_ai_log:
                st.subheader("🚑 REJESTR URAZÓW (Baza treningowa dla Machine Learning)")
                st.write("Wpisuj tutaj każdą kontuzję. Gdy zbierzemy odpowiednią liczbę przypadków, wytrenujemy model AI specyficzny dla Warty Poznań, który zastąpi obecny algorytm szacunkowy.")
                
                with st.form("injury_form", border=True):
                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        zawodnik_uraz = st.selectbox("Poszkodowany zawodnik:", LISTA_ZAWODNIKOW)
                        data_urazu = st.date_input("Data odniesienia urazu:", value=teraz.date())
                    with col_i2:
                        rodzaj_urazu = st.selectbox("Typ Urazu:", ["Mięśniowy (Naciągnięcie/Naderwanie)", "Mechaniczny (Staw/Kość)", "Przeciążeniowy (Ścięgno)", "Choroba / Wirus"])
                        przewidywana_pauza = st.number_input("Estymowany czas pauzy (dni):", min_value=1, max_value=300, value=7)
                        
                    uwagi_uraz = st.text_area("Diagnoza lekarska / Notatki:")
                    
                    if st.form_submit_button("ZAPISZ URAZ W BAZIE ML"):
                        nowy_uraz = {
                            "Data": data_urazu.strftime("%Y-%m-%d"),
                            "Zawodnik": zawodnik_uraz,
                            "Rodzaj": rodzaj_urazu,
                            "Dni_Pauzy": przewidywana_pauza,
                            "Uwagi": uwagi_uraz
                        }
                        
                        try:
                            try:
                                df_urazy = conn.read(worksheet="Urazy", ttl=0)
                            except:
                                df_urazy = pd.DataFrame()
                                
                            if df_urazy is None: df_urazy = pd.DataFrame()
                            
                            updated_urazy = pd.concat([df_urazy, pd.DataFrame([nowy_uraz])], ignore_index=True)
                            conn.update(worksheet="Urazy", data=updated_urazy)
                            st.success(f"✔ Uraz zawodnika {zawodnik_uraz} został zapisany w bazie szkoleniowej AI.")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"Błąd zapisu! Upewnij się, że w Google Sheets istnieje zakładka o nazwie 'Urazy'. Błąd: {e}")
                
                try:
                    df_u = conn.read(worksheet="Urazy", ttl=5)
                    if df_u is not None and not df_u.empty:
                        st.markdown("#### BAZA HISTORYCZNA URAZÓW:")
                        st.dataframe(df_u, use_container_width=True, hide_index=True)
                except:
                    pass

        elif widok == "Surowe Dane":
            st.subheader("📄 DANE Z ARKUSZA")
            st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
