import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import pytz
import calendar
import plotly.express as px
import plotly.graph_objects as go
import os

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "Warta!"
GODZINA_WELLNESS = 10 
GODZINA_RPE = 17

LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcel Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Oskar Mazurkiewicz", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Sztab", page_icon="📋", layout="wide")

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    html, body, [class*="st-"], .stMarkdown, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}

    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        text-transform: uppercase;
        text-align: center;
    }}

    [data-testid="stMetric"] {{
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
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

# --- ŁADOWANIE DANYCH ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    try:
        return conn.read(worksheet="Arkusz1", ttl=0)
    except Exception as e:
        st.error(f"Błąd połączenia z Arkuszem: {e}")
        return pd.DataFrame()

# --- HEADER Z LOGO ---
def get_logo():
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

col_l1, col_l2, col_l3 = st.columns([1, 0.5, 1])
with col_l2:
    st.image(get_logo(), use_container_width=True)

st.markdown(f"<h1>📊 PERFORMANCE & STAFF ANALYTICS</h1>", unsafe_allow_html=True)

try:
    df_raw = load_data()
    
    if df_raw.empty:
        st.info("Brak danych w arkuszu.")
    else:
        df = df_raw.copy()
        df['Data'] = pd.to_datetime(df['Data'], format='mixed', dayfirst=False)
        df['Dzień'] = df['Data'].dt.date
        df['Godzina_H'] = df['Data'].dt.hour
        
        NAZWY_MIESIECY = {
            1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
            5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
            9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
        }

        with st.sidebar:
            st.header("⚙️ USTAWIENIA")
            widok = st.radio("WYBIERZ WIDOK:", [
                "Raport Dzienny", 
                "Zarządzanie i RPE", 
                "Raport Sztabowy", 
                "Wykresy Drużynowe", 
                "Profil Indywidualny", 
                "Surowe Dane"
            ])
            
            teraz = datetime.now(PL_TZ)
            
            if widok == "Raport Dzienny":
                wybrana_data = st.date_input("Wybierz dzień analizy:", value=teraz.date())
            elif widok == "Zarządzanie i RPE":
                data_konfig = st.date_input("Data sesji:", value=teraz.date())
            else:
                wybrany_rok = st.selectbox("Rok:", [2024, 2025, 2026], index=2 if teraz.year == 2026 else (1 if teraz.year == 2025 else 0))
                # Automatyczne ustawienie na aktualny miesiąc
                wybrany_miesiac_nazwa = st.selectbox("Miesiąc:", list(NAZWY_MIESIECY.values()), index=teraz.month-1)
                wybrany_miesiac_nr = [k for k, v in NAZWY_MIESIECY.items() if v == wybrany_miesiac_nazwa][0]
            
            st.write("---")
            if st.button("🔄 Odśwież Dane"):
                st.cache_data.clear()
                st.rerun()
            
            if st.button("Wyloguj"):
                st.session_state["auth_staff"] = False
                st.rerun()

        # --- LOGIKA WIDOKÓW ---

        if widok == "Raport Dzienny":
            st.subheader(f"📅 RAPORT GOTOWOŚCI: {wybrana_data}")
            df_day = df[df['Dzień'] == wybrana_data]
            df_well_day = df_day[df_day['Typ_Raportu'] == 'Wellness']
            
            bolesnosc_alert = df_well_day[df_well_day['Bolesnosc'].isin([1, 2, 1.0, 2.0])]
            if not bolesnosc_alert.empty:
                st.error("🚨 ALERT BOLESNOŚCI (Wymagana konsultacja fizjo)")
                cols_alert = st.columns(min(len(bolesnosc_alert), 4))
                for idx, (_, row) in enumerate(bolesnosc_alert.iterrows()):
                    with cols_alert[idx % 4]:
                        st.markdown(f"""<div style="background-color: #FFEBEE; padding: 10px; border-radius: 10px; border-left: 5px solid red; margin-bottom:10px;"><b style="color:red">{row['Zawodnik']}</b><br>Bolesność: {row['Bolesnosc']:.0f}/5<br><small>{row['Komentarz'] if row['Komentarz'] else 'Brak komentarza'}</small></div>""", unsafe_allow_html=True)
            
            zawodnicy_raport = df_well_day['Zawodnik'].unique()
            brak_raportu = [z for z in LISTA_ZAWODNIKOW if z not in zawodnicy_raport]
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.success(f"✅ RAPORTY DOTARŁY ({len(zawodnicy_raport)})")
                ready_data = []
                for z in zawodnicy_raport:
                    z_data = df_well_day[df_well_day['Zawodnik'] == z].iloc[-1]
                    status_time = "🟢 O CZASIE" if z_data['Godzina_H'] < GODZINA_WELLNESS else "🟡 SPÓŹNIONY"
                    readiness_total = z_data[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum()
                    ready_data.append({"Zawodnik": z, "Status": status_time, "Sen": int(z_data['Sen']), "Zmęczenie": int(z_data['Zmeczenie']), "Bolesność": int(z_data['Bolesnosc']), "Stres": int(z_data['Stres']), "READINESS": int(readiness_total)})
                
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

            with c2:
                st.warning(f"❌ BRAKI ({len(brak_raportu)})")
                if brak_raportu:
                    for b_zawodnik in brak_raportu:
                        st.write(f"• {b_zawodnik}")

        elif widok == "Zarządzanie i RPE":
            st.subheader(f"⚙️ ZARZĄDZANIE SESJĄ I ANALIZA RPE: {data_konfig}")
            df_rpe_raw_day = df[(df['Dzień'] == data_konfig) & (df['Typ_Raportu'] == 'RPE')]
            
            st.markdown("#### 🛠️ KONFIGURACJA GRUPY")
            c_conf1, c_conf2 = st.columns([1, 2])
            with c_conf1:
                czas_minut = st.number_input("Czas trwania sesji (min):", min_value=15, max_value=240, value=90, step=5)
            with c_conf2:
                zawodnicy_na_treningu = st.multiselect("Odhacz zawodników biorących udział w tej sesji:", options=LISTA_ZAWODNIKOW, default=LISTA_ZAWODNIKOW)

            df_rpe_filtered = df_rpe_raw_day[df_rpe_raw_day['Zawodnik'].isin(zawodnicy_na_treningu)]
            
            st.write("---")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            srednie_rpe = df_rpe_filtered['RPE'].mean() if not df_rpe_filtered.empty else 0.0
            liczba_wpisow = len(df_rpe_filtered)
            expected_total = len(zawodnicy_na_treningu)
            
            with col_stat1: st.metric("Średnie RPE Grupy", f"{srednie_rpe:.2f}")
            with col_stat2: st.metric("Status Raportów", f"{liczba_wpisow} / {expected_total}")
            with col_stat3: st.metric("Średni Load (TL)", f"{int(srednie_rpe * czas_minut)}")

            st.markdown("#### 📊 WYNIKI INDYWIDUALNE WYBRANEJ GRUPY")
            if not df_rpe_filtered.empty:
                rpe_summary = [{"Zawodnik": row['Zawodnik'], "RPE": int(row['RPE']), "Czas": int(czas_minut), "Indywidualny Load": int(row['RPE'] * czas_minut), "Komentarz": row['Komentarz']} for _, row in df_rpe_filtered.iterrows()]
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
                st.info("Wybierz zawodników i poczekaj na ich raporty RPE.")

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
            st.subheader("🟢 READINESS SCORE (0-20 PKT)")
            df_month = df[(df['Data'].dt.month == wybrany_miesiac_nr) & (df['Data'].dt.year == wybrany_rok)]
            df_well_charts = df_month[df_month['Typ_Raportu'] == 'Wellness'].copy()
            if not df_well_charts.empty:
                df_well_charts['Readiness'] = df_well_charts[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                latest_r = df_well_charts.sort_values('Data').groupby('Zawodnik').last().reset_index()
                fig_read = px.bar(latest_r, x='Zawodnik', y='Readiness', color='Readiness', range_y=[0, 20], color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'], title="Ostatnia Gotowość Drużyny")
                st.plotly_chart(fig_read, use_container_width=True)
            else: st.warning("Brak danych Wellness w tym miesiącu.")

        elif widok == "Profil Indywidualny":
            zawodnik = st.selectbox("Wybierz zawodnika:", LISTA_ZAWODNIKOW)
            df_month = df[(df['Data'].dt.month == wybrany_miesiac_nr) & (df['Data'].dt.year == wybrany_rok)]
            p_data = df_month[df_month['Zawodnik'] == zawodnik]
            if p_data.empty: st.warning("Brak danych dla wybranego zawodnika w tym miesiącu.")
            else:
                well_p = p_data[p_data['Typ_Raportu'] == 'Wellness']
                if not well_p.empty:
                    ostatni = well_p.sort_values('Data').iloc[-1]
                    st.markdown(f"### PROFIL: {zawodnik}")
                    st.metric("Ostatni Readiness", f"{int(ostatni[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum())} / 20")
                    fig_radar = go.Figure(data=go.Scatterpolar(r=[ostatni['Sen'], ostatni['Zmeczenie'], ostatni['Bolesnosc'], ostatni['Stres']], theta=['Sen', 'Zmęczenie', 'Bolesność', 'Stres'], fill='toself', line_color=COLOR_PRIMARY))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
                    st.plotly_chart(fig_radar, use_container_width=True)
                    well_p['Sum_Readiness'] = well_p[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                    fig_line = px.line(well_p.sort_values('Data'), x='Data', y='Sum_Readiness', title="Trend Gotowości")
                    st.plotly_chart(fig_line, use_container_width=True)

        elif widok == "Surowe Dane":
            st.subheader("📄 DANE Z ARKUSZA")
            st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
