import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"  # Zielony Warty
COLOR_TEXT = "#1a1a1a"    # Ciemny tekst dla kontrastu
PL_TZ = pytz.timezone('Europe/Warsaw')

# Pełna lista zawodników
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Monitor Obciążeń", page_icon="⚽")

# --- ZAAWANSOWANA STYLIZACJA CSS (FIX DLA TRYBU NOCNEGO) ---
st.markdown(f"""
    <style>
    /* Wymuszenie jasnego tła dla całej aplikacji zawodnika */
    .stApp {{
        background-color: #ffffff !important;
        color: {COLOR_TEXT} !important;
    }}
    
    /* Nagłówki */
    h1, h2, h3 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center;
    }}

    /* Stylizacja pól formularza i tekstów pomocniczych */
    label, p, span, div {{
        color: {COLOR_TEXT} !important;
    }}
    
    /* Stylizacja Selectboxa i Inputów */
    div[data-baseweb="select"] > div {{
        background-color: #f0f2f6 !important;
        color: {COLOR_TEXT} !important;
    }}

    /* Przycisk wysyłania */
    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
        border: none;
    }}
    
    /* Radio buttons i suwaki */
    div[class*="stSlider"] > div {{
        color: {COLOR_PRIMARY} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIKA LINKÓW (ZALOGOWANIE) ---
query_params = st.query_params
auto_player = query_params.get("player", None)

st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=100)
st.title("MONITORING ZAWODNIKA")

# Połączenie
conn = st.connection("gsheets", type=GSheetsConnection)

# Wybór zawodnika (z blokadą jeśli link jest personalny)
if auto_player and auto_player in LISTA_ZAWODNIKOW:
    st.success(f"✅ ZALOGOWANY: **{auto_player}**")
    zawodnik = auto_player
else:
    zawodnik = st.selectbox("Wybierz swoje nazwisko:", [""] + LISTA_ZAWODNIKOW)

if zawodnik:
    typ_raportu = st.radio("Co chcesz zaraportować?", ["Wellness (Rano)", "RPE (Po treningu)"], horizontal=True)

    with st.form("ankieta_form"):
        data_dzis = datetime.now(PL_TZ).date()
        
        if typ_raportu == "Wellness (Rano)":
            st.subheader("📊 Poranny Raport Wellness")
            sen = st.select_slider("Jakość snu (1-5)", options=[1,2,3,4,5], value=3)
            zmeczenie = st.select_slider("Poziom zmęczenia (1-5)", options=[1,2,3,4,5], value=3)
            bolesnosc = st.select_slider("Bolesność mięśni (1-5)", options=[1,2,3,4,5], value=3)
            stres = st.select_slider("Poziom stresu (1-5)", options=[1,2,3,4,5], value=3)
            rpe = None
        else:
            st.subheader("🏃 Raport Po Treningu")
            rpe = st.select_slider("Intensywność treningu (RPE 1-10)", options=list(range(1,11)), value=5)
            sen = zmeczenie = bolesnosc = stres = None

        submit = st.form_submit_button("WYŚLIJ RAPORT")

        if submit:
            now = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            new_data = pd.DataFrame([{
                "Data": now,
                "Zawodnik": zawodnik,
                "Typ_Raportu": "Wellness" if typ_raportu == "Wellness (Rano)" else "RPE",
                "Sen": sen,
                "Zmeczenie": zmeczenie,
                "Bolesnosc": bolesnosc,
                "Stres": stres,
                "RPE": rpe
            }])
            
            old_data = conn.read(worksheet="Arkusz1")
            updated_df = pd.concat([old_data, new_data], ignore_index=True)
            conn.update(worksheet="Arkusz1", data=updated_df)
            
            st.balloons()
            st.success("Dziękujemy! Raport został zapisany.")
else:
    st.info("Wybierz nazwisko z listy lub użyj swojego linku, aby zacząć.")
