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

# --- FUNKCJE POMOCNICZE (Oczyszczanie i Normalizacja) ---
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

# --- HEADER Z LOGO ---
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
                "Raport Dzienny", 
                "Zarządzanie i RPE", 
                "Siłownia i Regeneracja", 
                "Raport Sztabowy", 
                "Wykresy Drużynowe", 
                "Profil Indywidualny", 
                "Surowe Dane"
            ])
            
            teraz = datetime.now(PL_TZ)
            
            if widok in ["Raport Dzienny", "Wykresy Drużynowe", "Zarządzanie i RPE", "Siłownia i Regeneracja"]:
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

        df_rpe_all = df[df['Typ_Raportu'] == 'RPE'].copy()
        df_rpe_all['RPE_num'] = pd.to_numeric(df_rpe_all['RPE'], errors='coerce').fillna(0)
        df_rpe_all['Dzień_dt'] = pd.to_datetime(df_rpe_all['Dzień'])

        df_well_all = df[df['Typ_Raportu'] == 'Wellness'].copy()
        for col in ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']:
            if col in df_well_all.columns:
                df_well_all[col] = pd.to_numeric(df_well_all[col], errors='coerce').fillna(0)
        df_well_all['Readiness'] = df_well_all[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
        df_well_all['Dzień_dt'] = pd.to_datetime(df_well_all['Dzień'])

        # --- LOGIKA WIDOKÓW ---
        if widok == "Raport Dzienny":
            st.subheader(f"📅 RAPORT GOTOWOŚCI: {wybrana_data}")
            df_day = df[df['Dzień'] == wybrana_data]
            df_well_day = df_day[df_day['Typ_Raportu'] == 'Wellness'].copy()
            for col in ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']:
                if col in df_well_day.columns:
                    df_well_day[col] = pd.to_numeric(df_well_day[col], errors='coerce').fillna(0)
            
            bolesnosc_alert = df_well_day[df_well_day['Bolesnosc'].isin([1, 2, 1.0, 2.0])]
            z_alerts = []
            dzis_dt = pd.to_datetime(wybrana_data)
            granica_14d = dzis_dt - timedelta(days=14)
            
            for z in df_well_day['Zawodnik'].unique():
                hist_z = df_well_all[(df_well_all['Zawodnik'] == z) & (df_well_all['Dzień_dt'] < dzis_dt) & (df_well_all['Dzień_dt'] >= granica_14d)]
                if len(hist_z) >= 3:
                    srednia_hist = hist_z['Readiness'].mean()
                    std_hist = hist_z['Readiness'].std()
                    wynik_dzis = df_well_day[df_well_day['Zawodnik'] == z].iloc[-1]
                    readiness_dzis = sum([float(wynik_dzis['Sen']), float(wynik_dzis['Zmeczenie']), float(wynik_dzis['Bolesnosc']), float(wynik_dzis['Stres'])])
                    if std_hist > 0:
                        z_score = (readiness_dzis - srednia_hist) / std_hist
                        if z_score < -1.5:
                            z_alerts.append({
                                "Zawodnik": z, "Dzis": readiness_dzis, "Srednia": srednia_hist,
                                "Odchylenie": z_score, "Komentarz": wynik_dzis['Komentarz']
                            })

            if not bolesnosc_alert.empty or z_alerts:
                st.error("🚨 ALERTY SYSTEMOWE (Wymagany kontakt ze sztabem medycznym)")
                col_al1, col_al2 = st.columns(2)
                
                with col_al1:
                    if not bolesnosc_alert.empty:
                        st.markdown("<p style='color:red; font-size:1.1rem;'>🔴 SILNA BOLESNOŚĆ MIĘŚNIOWA:</p>", unsafe_allow_html=True)
                        for _, row in bolesnosc_alert.iterrows():
                            kom = row['Komentarz'] if pd.notna(row['Komentarz']) and row['Komentarz'] != "" else 'Brak uwag'
                            st.markdown(f"""<div style="background-color: #FFEBEE; padding: 10px; border-radius: 10px; border-left: 5px solid red; margin-bottom:10px;"><b style="color:red">{row['Zawodnik']}</b> - Bolesność: {float(row['Bolesnosc']):.0f}/5<br><small>Uwag: {kom}</small></div>""", unsafe_allow_html=True)
                
                with col_al2:
                    if z_alerts:
                        st.markdown("<p style='color:#FF9800; font-size:1.1rem;'>🟡 INDYWIDUALNY SPADEK REGENERACJI (Z-Score):</p>", unsafe_allow_html=True)
                        for al in z_alerts:
                            kom = al['Komentarz'] if pd.notna(al['Komentarz']) and al['Komentarz'] != "" else 'Brak uwag'
                            st.markdown(f"""<div style="background-color: #FFF3E0; padding: 10px; border-radius: 10px; border-left: 5px solid #FF9800; margin-bottom:10px;"><b style="color:#E65100">{al['Zawodnik']}</b> - Spadek o {abs(al['Odchylenie']):.1f} SD poniżej swojej normy!<br>Dziś: {al['Dzis']:.0f}/20 (Średnia: {al['Srednia']:.1f}/20)<br><small>Uwagi: {kom}</small></div>""", unsafe_allow_html=True)

            zawodnicy_raport = df_well_day['Zawodnik'].unique() if not df_well_day.empty else []
            brak_raportu = [z for z in LISTA_ZAWODNIKOW if z not in zawodnicy_raport]
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.success(f"✅ RAPORTY DOTARŁY ({len(zawodnicy_raport)})")
                ready_data = []
                for z in zawodnicy_raport:
                    z_data = df_well_day[df_well_day['Zawodnik'] == z].iloc[-1]
                    status_time = "🟢 O CZASIE" if z_data['Godzina_H'] < GODZINA_WELLNESS else "🟡 SPÓŹNIONY"
                    sen_val = pd.to_numeric(z_data['Sen'], errors='coerce')
                    zmeczenie_val = pd.to_numeric(z_data['Zmeczenie'], errors='coerce')
                    bolesnosc_val = pd.to_numeric(z_data['Bolesnosc'], errors='coerce')
                    stres_val = pd.to_numeric(z_data['Stres'], errors='coerce')
                    readiness_total = sum(filter(pd.notna, [sen_val, zmeczenie_val, bolesnosc_val, stres_val]))
                    
                    ready_data.append({
                        "Zawodnik": z, "Status": status_time, "Sen": int(sen_val) if pd.notna(sen_val) else 0, 
                        "Zmęczenie": int(zmeczenie_val) if pd.notna(zmeczenie_val) else 0, "Bolesność": int(bolesnosc_val) if pd.notna(bolesnosc_val) else 0, 
                        "Stres": int(stres_val) if pd.notna(stres_val) else 0, "READINESS": int(readiness_total)
                    })
                
                if ready_data:
                    df_ready = pd.DataFrame(ready_data).sort_values("READINESS", ascending=True)
                    def color_scale_1_5(val):
                        try:
                            v = float(val)
                            if v <= 2: return 'background-color: #ffcccc; color: black;'
                            if v == 3: return 'background-color: #ffffcc; color: black;'
                            return 'background-color: #ccffcc; color: black;'
                        except: return ''
                    st.dataframe(df_ready.style.map(color_scale_1_5, subset=['Sen', 'Zmęczenie', 'Bolesność', 'Stres']).background_gradient(subset=['READINESS'], cmap="RdYlGn", low=0, high=1).format({"READINESS": "{:d}/20", "Sen": "{:d}", "Zmęczenie": "{:d}", "Bolesność": "{:d}", "Stres": "{:d}"}), hide_index=True, use_container_width=True)
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
                
                # ZMIANA: Szukamy wyników w osobnej zakładce Wyniki_Silownia
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
                        
                        # Budowanie listy ćwiczeń
                        cwiczenia_zrealizowane = []
                        for i in range(1, 6):
                            nazwa_col = f"Cwiczenie_{i}_Nazwa"
                            if nazwa_col in row and pd.notna(row[nazwa_col]) and str(row[nazwa_col]).strip() != "":
                                c_nazwa = str(row[nazwa_col])
                                c_suma = row.get(f"Cwiczenie_{i}_Suma_KG", 0)
                                serie_text = []
                                for s in range(1, 11): # max 10 serii
                                    s_col = f"Cw_{i}_Seria_{s}_KG"
                                    if s_col in row and pd.notna(row[s_col]) and row[s_col] > 0:
                                        serie_text.append(f"{row[s_col]}kg")
                                if serie_text:
                                    cwiczenia_zrealizowane.append(f"🏋️ {c_nazwa} ({', '.join(serie_text)}) -> Suma: {c_suma}kg")
                                else:
                                    cwiczenia_zrealizowane.append(f"🏋️ {c_nazwa} (Brak wpisanych ciężarów)")
                                    
                        gym_results.append({
                            "Zawodnik": zawodnik_wynik, 
                            "Wstępny tonaż (kg)": int(tonaz), 
                            "Zrealizowany trening i ciężary": "\n".join(cwiczenia_zrealizowane),
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
                            for linia in gracz_row['Zrealizowany trening i ciężary'].split("\n"): st.write(f"• {linia}")
                else:
                    st.info(f"Brak zapisanych treningów w dniu {wybrana_data}.")
            
            with tab_plan_gym:
                st.subheader("🏋️ KREATOR PLANU SIŁOWEGO")
                
                df_plans = load_data("Plany")
                df_szablony = pobierz_szablony()
                
                # Inicjalizacja stanu formularza dla szablonów (tylko siłownia)
                if 'form_tytul' not in st.session_state: st.session_state['form_tytul'] = ""
                for i in range(1, 6):
                    if f'form_cw{i}_nazwa' not in st.session_state: st.session_state[f'form_cw{i}_nazwa'] = ""
                    if f'form_cw{i}_serie' not in st.session_state: st.session_state[f'form_cw{i}_serie'] = 4 if i <= 2 else 3
                    if f'form_cw{i}_opis' not in st.session_state: st.session_state[f'form_cw{i}_opis'] = ""
                    if f'form_cw{i}_link' not in st.session_state: st.session_state[f'form_cw{i}_link'] = ""

                # --- PANEL WCZYTYWANIA SZABLONU ---
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
                                else:
                                    serie_match = re.search(r"\[SERIE:(\d+)\]", val, re.IGNORECASE)
                                    serie = int(serie_match.group(1)) if serie_match else 3
                                    
                                    link_match = re.search(r"\[LINK:(.*?)\]", val, re.IGNORECASE)
                                    link_str = link_match.group(1).strip() if link_match else ""
                                    
                                    opis_match = re.search(r"\((.*?)\)", val)
                                    opis_str = opis_match.group(1).strip() if opis_match else ""
                                    
                                    # Oczyszczamy nazwę z serii, opisów i linków
                                    nazwa = re.sub(r"\[SERIE:\d+\].*", "", val, flags=re.IGNORECASE).strip()
                                    
                                    st.session_state[f'form_cw{i}_nazwa'] = nazwa
                                    st.session_state[f'form_cw{i}_serie'] = serie
                                    st.session_state[f'form_cw{i}_opis'] = opis_str
                                    st.session_state[f'form_cw{i}_link'] = link_str
                                    
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
                    
                    st.markdown("### 🏋️ ĆWICZENIA (Z SERIAMI, CIĘŻARAMI I LINKAMI WIDEO)")
                    
                    tytul_planu = st.text_input("Tytuł treningu (widoczny w kalendarzu gracza):", value=st.session_state.get('form_tytul', ''), placeholder="np. Siła Dół A, FBW, Moc przedmeczowa")
                    
                    st.markdown("#### ĆWICZENIE 1")
                    cw1_nazwa = st.text_input("Nazwa ćwiczenia 1:", value=st.session_state['form_cw1_nazwa'], placeholder="np. Przysiad ze sztangą z tyłu")
                    col_p1_1, col_p1_2, col_p1_3 = st.columns([1, 2, 2])
                    with col_p1_1: cw1_serie = st.number_input("Liczba serii (Ćw 1):", min_value=1, max_value=10, value=st.session_state['form_cw1_serie'])
                    with col_p1_2: cw1_opis = st.text_input("Instrukcja (Ćw 1):", value=st.session_state['form_cw1_opis'], placeholder="np. 6 powt., tempo 3010", key="op1")
                    with col_p1_3: cw1_link = st.text_input("Link YT (Ćw 1):", value=st.session_state['form_cw1_link'], placeholder="https://youtu.be/...", key="lk1")
                        
                    st.markdown("#### ĆWICZENIE 2")
                    cw2_nazwa = st.text_input("Nazwa ćwiczenia 2:", value=st.session_state['form_cw2_nazwa'], placeholder="np. Wyciskanie hantli leżąc")
                    col_p2_1, col_p2_2, col_p2_3 = st.columns([1, 2, 2])
                    with col_p2_1: cw2_serie = st.number_input("Liczba serii (Ćw 2):", min_value=1, max_value=10, value=st.session_state['form_cw2_serie'])
                    with col_p2_2: cw2_opis = st.text_input("Instrukcja (Ćw 2):", value=st.session_state['form_cw2_opis'], placeholder="np. 8 powt., przerwa 90s", key="op2")
                    with col_p2_3: cw2_link = st.text_input("Link YT (Ćw 2):", value=st.session_state['form_cw2_link'], placeholder="https://youtu.be/...", key="lk2")

                    st.markdown("#### ĆWICZENIE 3")
                    cw3_nazwa = st.text_input("Nazwa ćwiczenia 3:", value=st.session_state['form_cw3_nazwa'], placeholder="np. Podciąganie na drążku")
                    col_p3_1, col_p3_2, col_p3_3 = st.columns([1, 2, 2])
                    with col_p3_1: cw3_serie = st.number_input("Liczba serii (Ćw 3):", min_value=1, max_value=10, value=st.session_state['form_cw3_serie'])
                    with col_p3_2: cw3_opis = st.text_input("Instrukcja (Ćw 3):", value=st.session_state['form_cw3_opis'], placeholder="np. maks powtórzeń", key="op3")
                    with col_p3_3: cw3_link = st.text_input("Link YT (Ćw 3):", value=st.session_state['form_cw3_link'], placeholder="https://youtu.be/...", key="lk3")

                    st.markdown("#### ĆWICZENIE 4")
                    cw4_nazwa = st.text_input("Nazwa ćwiczenia 4:", value=st.session_state['form_cw4_nazwa'], placeholder="np. Plank z obciążeniem")
                    col_p4_1, col_p4_2, col_p4_3 = st.columns([1, 2, 2])
                    with col_p4_1: cw4_serie = st.number_input("Liczba serii (Ćw 4):", min_value=1, max_value=10, value=st.session_state['form_cw4_serie'])
                    with col_p4_2: cw4_opis = st.text_input("Instrukcja (Ćw 4):", value=st.session_state['form_cw4_opis'], placeholder="np. 45 s, przerwa 60s", key="op4")
                    with col_p4_3: cw4_link = st.text_input("Link YT (Ćw 4):", value=st.session_state['form_cw4_link'], placeholder="https://youtu.be/...", key="lk4")

                    st.markdown("#### ĆWICZENIE 5")
                    cw5_nazwa = st.text_input("Nazwa ćwiczenia 5:", value=st.session_state['form_cw5_nazwa'], placeholder="np. Dead Bug z ciężarem")
                    col_p5_1, col_p5_2, col_p5_3 = st.columns([1, 2, 2])
                    with col_p5_1: cw5_serie = st.number_input("Liczba serii (Ćw 5):", min_value=1, max_value=10, value=st.session_state['form_cw5_serie'])
                    with col_p5_2: cw5_opis = st.text_input("Instrukcja (Ćw 5):", value=st.session_state['form_cw5_opis'], placeholder="np. 10 powt. na stronę", key="op5")
                    with col_p5_3: cw5_link = st.text_input("Link YT (Ćw 5):", value=st.session_state['form_cw5_link'], placeholder="https://youtu.be/...", key="lk5")

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
                                df_plans = pd.DataFrame(columns=["Data", "Grupa_lub_Zawodnik", "Tytul_Treningu", "Regeneracja", "Cwiczenie_1", "Cwiczenie_2", "Cwiczenie_3", "Cwiczenie_4", "Cwiczenie_5"])
                                df_plans['Data_formatted'] = []
                                
                            if 'Tytul_Treningu' not in df_plans.columns:
                                df_plans['Tytul_Treningu'] = ""
                            df_plans['Tytul_Treningu'] = df_plans['Tytul_Treningu'].fillna("")
                            
                            # Logika nowa: Nadpisujemy TYLKO jeśli Tytuł, Grupa i Data są identyczne!
                            mask = (df_plans['Data_formatted'] == plan_date) & \
                                   (df_plans['Grupa_lub_Zawodnik'] == adresat_planu) & \
                                   (df_plans['Tytul_Treningu'] == tytul_planu.strip())
                            
                            istniejace = df_plans[mask]
                            
                            stary_regen = ""
                            if not istniejace.empty:
                                stary_regen = str(istniejace.iloc[0].get("Regeneracja", "")).replace('nan', '')
                            
                            # Pomocnicza funkcja formująca tekst zapisu ćwiczenia
                            def format_cwiczenie(nazwa, serie, opis, link):
                                if not nazwa.strip(): return ""
                                string_cw = f"{nazwa.strip()} [SERIE:{serie}]"
                                if opis.strip(): string_cw += f" ({opis.strip()})"
                                if link.strip(): string_cw += f" [LINK:{link.strip()}]"
                                return string_cw

                            nowy_plan = {
                                "Data": plan_date.strftime("%Y-%m-%d"),
                                "Grupa_lub_Zawodnik": adresat_planu,
                                "Tytul_Treningu": tytul_planu.strip(),
                                "Regeneracja": stary_regen,
                                "Cwiczenie_1": format_cwiczenie(cw1_nazwa, cw1_serie, cw1_opis, cw1_link),
                                "Cwiczenie_2": format_cwiczenie(cw2_nazwa, cw2_serie, cw2_opis, cw2_link),
                                "Cwiczenie_3": format_cwiczenie(cw3_nazwa, cw3_serie, cw3_opis, cw3_link),
                                "Cwiczenie_4": format_cwiczenie(cw4_nazwa, cw4_serie, cw4_opis, cw4_link),
                                "Cwiczenie_5": format_cwiczenie(cw5_nazwa, cw5_serie, cw5_opis, cw5_link)
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
                                
                                st.balloons()
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
                                df_plans = pd.DataFrame(columns=["Data", "Grupa_lub_Zawodnik", "Tytul_Treningu", "Regeneracja", "Cwiczenie_1", "Cwiczenie_2", "Cwiczenie_3", "Cwiczenie_4", "Cwiczenie_5"])
                                df_plans['Data_formatted'] = []
                                
                            mask_reg = (df_plans['Data_formatted'] == plan_date_reg) & \
                                       (df_plans['Grupa_lub_Zawodnik'] == adresat_planu_reg)
                                       
                            istniejace_reg = df_plans[mask_reg]
                            
                            if not istniejace_reg.empty:
                                idx_to_update = istniejace_reg.index[0]
                                df_plans.at[idx_to_update, 'Regeneracja'] = regeneracja_opis.replace("\n", ", ")
                                updated_plans = df_plans.drop(columns=['Data_formatted'], errors='ignore')
                            else:
                                nowy_plan_reg = {
                                    "Data": plan_date_reg.strftime("%Y-%m-%d"),
                                    "Grupa_lub_Zawodnik": adresat_planu_reg,
                                    "Tytul_Treningu": "",
                                    "Regeneracja": regeneracja_opis.replace("\n", ", "),
                                    "Cwiczenie_1": "", "Cwiczenie_2": "", "Cwiczenie_3": "", "Cwiczenie_4": "", "Cwiczenie_5": ""
                                }
                                df_plans = df_plans.drop(columns=['Data_formatted'], errors='ignore')
                                updated_plans = pd.concat([df_plans, pd.DataFrame([nowy_plan_reg])], ignore_index=True)
                            
                            try:
                                conn.update(worksheet="Plany", data=updated_plans)
                                st.success(f"✔ PLAN REGENERACJI DLA {adresat_planu_reg.upper()} ZOSTAŁ ZAPISANY!")
                                st.balloons()
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"Błąd zapisu planu: {e}")

        elif widok == "Raport Sztabowy":
            st.subheader(f"📋 ZESTAWIENIE DYSCYPLINY: {wybrany_miesiac_nazwa.upper()}")
            df_month = df[(df['Data'].dt.month == wybrany_miesiac_nr) & (df['Data'].dt.year == wybrany_rok)]
            dni_max = calendar.monthrange(wybrany_rok, wybrany_miesiac_nr)[1]
            dni_analizy = teraz.day if (wybrany_rok == teraz.year and wybrany_miesiac_nr == teraz.month) else dni_max

            stats_wellness = []
            stats_rpe = []
            
            for z in LISTA_ZAWODNIKOW:
                p_data = df_month[df_month['Zawodnik'] == z]
                well = p_data[p_data['Typ_Raportu'] == 'Wellness']
                well_on_time = well[well['Godzina_H'] < GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_late = well[well['Godzina_H'] >= GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_braki = max(0, dni_analizy - well['Data'].dt.date.nunique())
                stats_wellness.append({"Zawodnik": z, "O czasie": well_on_time, "Spóźnione": well_late, "Braki": well_braki})
                
                rpe_d = p_data[p_data['Typ_Raportu'] == 'RPE']
                rpe_on_time = rpe_d[rpe_d['Godzina_H'] < GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_late = rpe_d[rpe_d['Godzina_H'] >= GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_braki = max(0, dni_analizy - rpe_d['Data'].dt.date.nunique())
                stats_rpe.append({"Zawodnik": z, "O czasie": rpe_on_time, "Spóźnione": rpe_late, "Braki": rpe_braki})

            df_well_f = pd.DataFrame(stats_wellness).sort_values("Braki", ascending=False)
            df_rpe_f = pd.DataFrame(stats_rpe).sort_values("Braki", ascending=False)

            col_w, col_r = st.columns(2)
            with col_w:
                st.markdown(f"### WELLNESS (Limit {GODZINA_WELLNESS}:00)")
                st.dataframe(df_well_f.style.background_gradient(subset=['Braki', 'Spóźnione'], cmap="Reds"), use_container_width=True, hide_index=True)
            with col_r:
                st.markdown(f"### RPE (Limit {GODZINA_RPE}:00)")
                st.dataframe(df_rpe_f.style.background_gradient(subset=['Braki', 'Spóźnione'], cmap="Reds"), use_container_width=True, hide_index=True)

        elif widok == "Wykresy Drużynowe":
            tab_team_well, tab_team_science = st.tabs(["📊 SAMOPOCZUCIE DRUŻYNY", "🏃 SPORTS SCIENCE (ACWR & MONOTONIA)"])
            
            with tab_team_well:
                st.subheader(f"🟢 ANALIZA GOTOWOŚCI DRUŻYNY: {wybrana_data}")
                df_day_well = df[(df['Dzień'] == wybrana_data) & (df['Typ_Raportu'] == 'Wellness')].copy()
                
                if not df_day_well.empty:
                    for col in ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']:
                        df_day_well[col] = pd.to_numeric(df_day_well[col], errors='coerce').fillna(0)
                    
                    df_day_well['Readiness'] = df_day_well[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                    avg_readiness = df_day_well['Readiness'].mean()
                    
                    fig_read = px.bar(
                        df_day_well.sort_values("Readiness", ascending=False), 
                        x='Zawodnik', 
                        y='Readiness', 
                        color='Readiness', 
                        range_y=[0, 20], 
                        color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'],
                        title=f"Gotowość na Dzień {wybrana_data} (Średnia: {avg_readiness:.2f}/20)"
                    )
                    fig_read.add_hline(y=avg_readiness, line_dash="dash", line_color="black", annotation_text=f"Średnia Grupy: {avg_readiness:.2f}", annotation_position="top right")
                    st.plotly_chart(fig_read, use_container_width=True)
                    
                    c_dist1, c_dist2 = st.columns(2)
                    with c_dist1:
                        fig_pie = px.pie(df_day_well, names='Zmeczenie', title="Rozkład Zmęczenia (1-5)", color_discrete_sequence=px.colors.sequential.RdBu)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with c_dist2:
                        fig_pie2 = px.pie(df_day_well, names='Sen', title="Rozkład Jakości Snu (1-5)", color_discrete_sequence=px.colors.sequential.Greens)
                        st.plotly_chart(fig_pie2, use_container_width=True)
                else: 
                    st.warning(f"Brak danych Wellness dla dnia {wybrana_data}. Wybierz inną datę w panelu bocznym.")

            with tab_team_science:
                st.subheader(f"🧠 DRUŻYNOWY PANEL OBCIĄŻEŃ (SPORTS SCIENCE)")
                st.markdown("<p style='text-align: center;'>Analiza ryzyka kontuzji drużyny na podstawie współczynnika ACWR i Monotonii z ostatnich 28 dni.</p>", unsafe_allow_html=True)
                
                science_team_data = []
                dzis_dt = pd.to_datetime(wybrana_data)
                
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
                            "Zawodnik": z,
                            "Ostry (7 dni)": round(acute, 2),
                            "Przewlekły (28 dni)": round(chronic, 2),
                            "ACWR (Wskaźnik)": round(acwr, 2),
                            "Monotonia": round(monotony, 2),
                            "Napięcie (Strain)": int(strain)
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
                        except:
                            return ''
                    
                    st.dataframe(df_science_team.style.map(color_acwr_scale, subset=['ACWR (Wskaźnik)']).background_gradient(subset=['Napięcie (Strain)'], cmap="Oranges"), use_container_width=True, hide_index=True)
                    
                    st.markdown("""
                    <div style="background-color: #FFFFFF; padding: 15px; border-radius: 12px; border: 1px solid #ddd; margin-top:15px;">
                        <h4 style="margin: 0 0 10px 0; font-size: 1rem; color: #006633;">LEGENDA SPORT SCIENCE:</h4>
                        <ul style="font-size: 0.85rem; margin: 0; padding-left: 20px;">
                            <li>🔵 <b>Niedotrenowanie (&lt; 0.80):</b> Brak bodźca fizycznego. Zawodnik traci zbudowaną sprawność.</li>
                            <li>🟢 <b>Sweet Spot (0.80 - 1.30):</b> Optymalne obciążenie treningowe. Sprawność rośnie przy minimalnym ryzyku kontuzji.</li>
                            <li>🟡 <b>Ostrzeżenie (1.31 - 1.50):</b> Szybki wzrost obciążenia. Wymagana czujność i kontrola regeneracji.</li>
                            <li>🔴 <b>Danger Zone (&gt; 1.50):</b> Drastyczny skok obciążeń ostrego tygodnia. Bardzo wysokie ryzyko kontuzji mięśniowej!</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Brak wystarczającej ilości danych historycznych do kalkulacji ACWR zespołu (potrzebne wpisy RPE z ostatnich dni).")

        elif widok == "Profil Indywidualny":
            zawodnik = st.selectbox("Wybierz zawodnika:", LISTA_ZAWODNIKOW)
            df_month = df[(df['Data'].dt.month == teraz.month) & (df['Data'].dt.year == teraz.year)].copy()
            p_data = df_month[df_month['Zawodnik'] == zawodnik]
            
            if p_data.empty: 
                st.warning("Brak danych dla wybranego zawodnika w bieżącym miesiącu.")
            else:
                tab_ind_well, tab_ind_science = st.tabs(["📊 WELLNESS & REGENERACJA", "🧠 OBCIĄŻENIA (SPORTS SCIENCE)"])
                
                with tab_ind_well:
                    well_p = p_data[p_data['Typ_Raportu'] == 'Wellness'].copy()
                    if not well_p.empty:
                        for col in ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']:
                            well_p[col] = pd.to_numeric(well_p[col], errors='coerce').fillna(0)
                        
                        ostatni = well_p.sort_values('Data').iloc[-1]
                        total_readiness = int(ostatni[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum())
                        
                        st.markdown(f"### PROFIL: {zawodnik}")
                        st.metric("Ostatni Readiness", f"{total_readiness} / 20")
                        
                        fig_radar = go.Figure(data=go.Scatterpolar(
                            r=[ostatni['Sen'], ostatni['Zmeczenie'], ostatni['Bolesnosc'], ostatni['Stres']], 
                            theta=['Sen', 'Zmęczenie', 'Bolesność', 'Stres'], 
                            fill='toself', 
                            line_color=COLOR_PRIMARY
                        ))
                        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
                        st.plotly_chart(fig_radar, use_container_width=True)
                        
                        well_p['Sum_Readiness'] = well_p[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
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
                        cur_acute = gracz_daily['Acute_MA'].iloc[-1]
                        cur_chronic = gracz_daily['Chronic_MA'].iloc[-1]
                        
                        last_7 = gracz_daily.iloc[-7:]['RPE_num']
                        std_7 = last_7.std()
                        mean_7 = last_7.mean()
                        cur_monotony = mean_7 / std_7 if std_7 > 0 else 1.0
                        cur_strain = cur_monotony * last_7.sum()
                        
                        c_sci1, c_sci2, c_sci3 = st.columns(3)
                        
                        if cur_acwr < 0.8: acwr_status = "🔵 Niedotrenowanie"
                        elif cur_acwr <= 1.3: acwr_status = "🟢 Sweet Spot"
                        elif cur_acwr <= 1.5: acwr_status = "🟡 Ryzyko"
                        else: acwr_status = "🔴 Danger Zone!"
                        
                        with c_sci1:
                            st.metric("ACWR Wskaźnik", f"{cur_acwr:.2f}", help="Acute-to-Chronic Workload Ratio", delta=acwr_status, delta_color="off")
                        with c_sci2:
                            st.metric("Monotonia Treningowa", f"{cur_monotony:.2f}", help="Średnia / Odchylenie Standardowe z 7 dni.")
                        with c_sci3:
                            st.metric("Napięcie (Strain)", f"{int(cur_strain)}", help="Skumulowany stres fizjologiczny zawodnika z ostatniego tygodnia.")
                            
                        fig_acwr_trend = go.Figure()
                        fig_acwr_trend.add_trace(go.Scatter(x=gracz_daily['Dzień_dt'], y=gracz_daily['ACWR_Ratio'], name='Wskaźnik ACWR', line=dict(color=COLOR_PRIMARY, width=3)))
                        fig_acwr_trend.add_hrect(y0=0.8, y1=1.3, line_width=0, fillcolor="rgba(76, 175, 80, 0.15)", annotation_text="Optymalny Trening (0.8 - 1.3)", annotation_position="top left")
                        fig_acwr_trend.add_hrect(y0=1.5, y1=3.0, line_width=0, fillcolor="rgba(244, 67, 54, 0.15)", annotation_text="Strefa Kontuzji (> 1.5)", annotation_position="top left")
                        
                        fig_acwr_trend.update_layout(title="Krzywa Zmęczenia do Formy (Wskaźnik ACWR)", yaxis_title="Współczynnik Ratio", xaxis_title="Data")
                        st.plotly_chart(fig_acwr_trend, use_container_width=True)
                    else:
                        st.info("Zawodnik musi posiadać co najmniej 3 zgłoszone raporty RPE, aby obliczyć indywidualne trendy ACWR.")

        elif widok == "Surowe Dane":
            st.subheader("📄 DANE Z ARKUSZA")
            st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
