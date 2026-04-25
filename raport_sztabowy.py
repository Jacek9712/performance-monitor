import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar
import plotly.express as px
import plotly.graph_objects as px_go

# --- KONFIGURACJA WIZUALNA ---
COLOR_PRIMARY = "#006633"   # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024"

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
    </style>
    """, unsafe_allow_html=True)

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

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    return conn.read(worksheet="Arkusz1", ttl=0)

st.markdown(f"<h1>📊 PERFORMANCE ANALYTICS</h1>", unsafe_allow_html=True)

try:
    df = load_data()
    
    if df.empty:
        st.info("Brak danych w arkuszu.")
    else:
        df['Data'] = pd.to_datetime(df['Data'])
        df['Dzień'] = df['Data'].dt.date
        
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=80)
            st.header("NAWIGACJA")
            widok = st.radio("Wybierz raport:", ["Drużynowy", "Indywidualny", "Surowe Dane"])
            wybrany_miesiac = st.selectbox("Miesiąc:", range(1, 13), index=datetime.now().month-1)
            
            if st.button("🔄 Odśwież dane"):
                st.cache_data.clear()
                st.rerun()
            
            if st.button("Wyloguj"):
                st.session_state["auth_staff"] = False
                st.rerun()

        df_month = df[df['Data'].dt.month == wybrany_miesiac]

        if widok == "Drużynowy":
            st.subheader("🟢 READINESS SCORE (Pkt / 20)")
            
            # Obliczanie Readiness dla każdego zawodnika
            df_well = df_month[df_month['Typ_Raportu'] == 'Wellness'].copy()
            df_well['Readiness'] = df_well[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
            
            # Grupowanie po zawodniku (ostatni raport)
            latest_readiness = df_well.sort_values('Data').groupby('Zawodnik').last().reset_index()
            
            fig_readiness = px.bar(
                latest_readiness, 
                x='Zawodnik', 
                y='Readiness',
                color='Readiness',
                range_y=[0, 20],
                color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'], # Czerwony -> Żółty -> Zielony
                title="Aktualna Gotowość Drużyny (Ostatni raport)"
            )
            fig_readiness.add_hline(y=12, line_dash="dash", line_color="orange", annotation_text="Limit ostrożności")
            fig_readiness.add_hline(y=8, line_dash="dash", line_color="red", annotation_text="Krytyczna regeneracja")
            st.plotly_chart(fig_readiness, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Średni Wellness Miesiąca")
                avg_trend = df_well.groupby('Dzień')['Readiness'].mean().reset_index()
                fig_trend = px.line(avg_trend, x='Dzień', y='Readiness', markers=True)
                fig_trend.update_layout(yaxis_range=[0, 20])
                st.plotly_chart(fig_trend, use_container_width=True)
            
            with col2:
                st.subheader("🔥 Średnie RPE")
                rpe_df = df_month[df_month['Typ_Raportu'] == 'RPE'].groupby('Zawodnik')['RPE'].mean().reset_index()
                fig_rpe = px.bar(rpe_df, x='Zawodnik', y='RPE', color_discrete_sequence=[COLOR_PRIMARY])
                st.plotly_chart(fig_rpe, use_container_width=True)

        elif widok == "Indywidualny":
            zawodnik = st.selectbox("Wybierz zawodnika:", LISTA_ZAWODNIKOW)
            p_data = df_month[df_month['Zawodnik'] == zawodnik]
            
            if p_data.empty:
                st.warning("Brak danych dla tego zawodnika w wybranym miesiącu.")
            else:
                well_p = p_data[p_data['Typ_Raportu'] == 'Wellness']
                
                if not well_p.empty:
                    ostatni = well_p.sort_values('Data').iloc[-1]
                    readiness_score = ostatni[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum()
                    
                    # Dashboard górny
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Ostatni Readiness", f"{readiness_score} / 20")
                    with c2:
                        avg_p = well_p[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1).mean()
                        st.metric("Średni Readiness (Miesiąc)", f"{avg_p:.1f}")
                    with c3:
                        st.metric("Liczba Raportów", len(well_p))

                    # Wykres Radarowy (Pająk)
                    st.subheader("🎯 Profil Wellness (Ostatni)")
                    categories = ['Sen', 'Zmęczenie', 'Bolesność', 'Stres']
                    values = [ostatni['Sen'], ostatni['Zmeczenie'], ostatni['Bolesnosc'], ostatni['Stres']]
                    
                    fig_radar = px_go.Figure()
                    fig_radar.add_trace(px_go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name=zawodnik,
                        line_color=COLOR_PRIMARY
                    ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                        showlegend=False
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

                    # Trend indywidualny
                    well_p['Readiness'] = well_p[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                    st.subheader("📅 Trend Readiness")
                    fig_ind_trend = px.area(well_p, x='Data', y='Readiness', color_discrete_sequence=['#81C784'])
                    fig_ind_trend.update_layout(yaxis_range=[0, 20])
                    st.plotly_chart(fig_ind_trend, use_container_width=True)

                    if ostatni['Komentarz']:
                        st.info(f"💬 Ostatni komentarz: {ostatni['Komentarz']}")
                else:
                    st.info("Brak raportów Wellness dla tego zawodnika.")

        elif widok == "Surowe Dane":
            st.subheader("📄 Wszystkie wpisy z arkusza")
            st.dataframe(df_month.sort_values('Data', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Problem z bazą danych: {e}")
