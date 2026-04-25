import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar
import plotly.express as px
import plotly.graph_objects as px_go
import io
import os

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024"
GODZINA_WELLNESS = 10 
GODZINA_RPE = 17

LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
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

    [data-testid="stDataFrame"] {{
        background-color: white;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
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
    return conn.read(worksheet="Arkusz1", ttl=0)

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
        # Przetwarzanie daty
        df = df_raw.copy()
        df['Data'] = pd.to_datetime(df['Data'], format='mixed', dayfirst=False)
        df['Dzień'] = df['Data'].dt.date
        df['Godzina_H'] = df['Data'].dt.hour
        
        # Słownik miesięcy dla UI
        NAZWY_MIESIECY = {
            1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
            5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
            9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
        }

        with st.sidebar:
            st.header("⚙️ USTAWIENIA")
            widok = st.radio("WYBIERZ WIDOK:", ["Raport Sztabowy", "Wykresy Drużynowe", "Profil Indywidualny", "Surowe Dane"])
            
            teraz = datetime.now(PL_TZ)
            wybrany_rok = st.selectbox("Rok:", [2024, 2025, 2026], index=1)
            wybrany_miesiac_nazwa = st.selectbox("Miesiąc:", list(NAZWY_MIESIECY.values()), index=teraz.month-1)
            wybrany_miesiac_nr = [k for k, v in NAZWY_MIESIECY.items() if v == wybrany_miesiac_nazwa][0]
            
            st.write("---")
            if st.button("🔄 Odśwież Dane"):
                st.cache_data.clear()
                st.rerun()
            
            if st.button("Wyloguj"):
                st.session_state["auth_staff"] = False
                st.rerun()

        # Filtrowanie danych na wybrany okres
        df_month = df[(df['Data'].dt.month == wybrany_miesiac_nr) & (df['Data'].dt.year == wybrany_rok)]
        
        # --- LOGIKA WIDOKÓW ---

        if widok == "Raport Sztabowy":
            st.subheader(f"📋 ZESTAWIENIE DYSCYPLINY: {wybrany_miesiac_nazwa.upper()}")
            
            dni_max = calendar.monthrange(wybrany_rok, wybrany_miesiac_nr)[1]
            dni_analizy = teraz.day if (wybrany_rok == teraz.year and wybrany_miesiac_nr == teraz.month) else dni_max

            stats_wellness = []
            stats_rpe = []
            
            for z in LISTA_ZAWODNIKOW:
                p_data = df_month[df_month['Zawodnik'] == z]
                
                # Wellness
                well = p_data[p_data['Typ_Raportu'] == 'Wellness']
                well_on_time = well[well['Godzina_H'] < GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_late = well[well['Godzina_H'] >= GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_braki = max(0, dni_analizy - well['Data'].dt.date.nunique())
                stats_wellness.append({"Zawodnik": z, "O czasie": well_on_time, "Spóźnione": well_late, "Braki": well_braki, "SUMA": well_late + well_braki})
                
                # RPE
                rpe_d = p_data[p_data['Typ_Raportu'] == 'RPE']
                rpe_on_time = rpe_d[rpe_d['Godzina_H'] < GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_late = rpe_d[rpe_d['Godzina_H'] >= GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_braki = max(0, dni_analizy - rpe_d['Data'].dt.date.nunique())
                stats_rpe.append({"Zawodnik": z, "O czasie": rpe_on_time, "Spóźnione": rpe_late, "Braki": rpe_braki, "SUMA": rpe_late + rpe_braki})

            df_well_f = pd.DataFrame(stats_wellness).sort_values("SUMA", ascending=False)
            df_rpe_f = pd.DataFrame(stats_rpe).sort_values("SUMA", ascending=False)

            # Export Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_well_f.to_excel(writer, index=False, sheet_name='Wellness')
                df_rpe_f.to_excel(writer, index=False, sheet_name='RPE')
            
            st.download_button(label="📥 Pobierz Raport Miesięczny (.xlsx)", data=output.getvalue(), file_name=f"Warta_Raport_{wybrany_miesiac_nazwa}.xlsx")

            col_w, col_r = st.columns(2)
            with col_w:
                st.markdown(f"### WELLNESS (Limit {GODZINA_WELLNESS}:00)")
                st.dataframe(df_well_f.style.background_gradient(subset=['SUMA'], cmap="Reds"), use_container_width=True, hide_index=True)
            with col_r:
                st.markdown(f"### RPE (Limit {GODZINA_RPE}:00)")
                st.dataframe(df_rpe_f.style.background_gradient(subset=['SUMA'], cmap="Reds"), use_container_width=True, hide_index=True)

        elif widok == "Wykresy Drużynowe":
            st.subheader("🟢 READINESS SCORE (0-20 PKT)")
            
            df_well_charts = df_month[df_month['Typ_Raportu'] == 'Wellness'].copy()
            if not df_well_charts.empty:
                df_well_charts['Readiness'] = df_well_charts[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                latest_r = df_well_charts.sort_values('Data').groupby('Zawodnik').last().reset_index()
                
                fig_read = px.bar(latest_r, x='Zawodnik', y='Readiness', color='Readiness', range_y=[0, 20],
                                 color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'], title="Ostatnia Gotowość Drużyny")
                fig_read.add_hline(y=12, line_dash="dash", line_color="orange")
                st.plotly_chart(fig_read, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    avg_t = df_well_charts.groupby('Dzień')['Readiness'].mean().reset_index()
                    st.plotly_chart(px.line(avg_t, x='Dzień', y='Readiness', markers=True, title="Trend Drużynowy"), use_container_width=True)
                with col2:
                    rpe_avg = df_month[df_month['Typ_Raportu'] == 'RPE'].groupby('Zawodnik')['RPE'].mean().reset_index()
                    st.plotly_chart(px.bar(rpe_avg, x='Zawodnik', y='RPE', title="Średnie Obciążenie RPE"), use_container_width=True)
            else:
                st.warning("Brak danych Wellness w tym miesiącu.")

        elif widok == "Profil Indywidualny":
            zawodnik = st.selectbox("Wybierz zawodnika:", LISTA_ZAWODNIKOW)
            p_data = df_month[df_month['Zawodnik'] == zawodnik]
            
            if p_data.empty:
                st.warning("Brak danych.")
            else:
                well_p = p_data[p_data['Typ_Raportu'] == 'Wellness']
                if not well_p.empty:
                    ostatni = well_p.sort_values('Data').iloc[-1]
                    r_score = ostatni[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Ostatni Readiness", f"{r_score} / 20")
                    c2.metric("Średnia Miesiąca", f"{well_p[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1).mean():.1f}")
                    c3.metric("Liczba Raportów", len(well_p))

                    # Radar
                    st.subheader("🎯 Profil Ostatniego Raportu")
                    fig_radar = px_go.Figure(data=px_go.Scatterpolar(
                        r=[ostatni['Sen'], ostatni['Zmeczenie'], ostatni['Bolesnosc'], ostatni['Stres']],
                        theta=['Sen', 'Zmęczenie', 'Bolesność', 'Stres'], fill='toself', line_color=COLOR_PRIMARY
                    ))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
                    st.plotly_chart(fig_radar, use_container_width=True)
                else:
                    st.info("Zawodnik nie wysłał raportów Wellness.")

        elif widok == "Surowe Dane":
            st.subheader("📄 DANE Z ARKUSZA (FILTROWANE)")
            st.dataframe(df_month.sort_values('Data', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
