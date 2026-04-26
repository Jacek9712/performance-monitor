import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633" # Zieleń Warty
PL_TZ = pytz.timezone('Europe/Warsaw')

LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Raport", page_icon="⚽", layout="centered")

# --- STYLE CSS (Przywrócenie klasycznego wyglądu z optymalizacją) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: white; }}
    .stButton>button {{ 
        width: 100%; 
        background-color: {COLOR_PRIMARY}; 
        color: white; 
        border-radius: 5px;
    }}
    h2 {{ color: {COLOR_PRIMARY}; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# --- ŁADOWANIE DANYCH (Zoptymalizowane - ROZWIĄZUJE PROBLEM WOLNEGO STARTU) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def get_existing_data():
    # Pobieramy dane z cache przez 60 sekund zamiast ttl=0
    return conn.read(worksheet="Arkusz1")

# --- LOGIKA LINKÓW INDYWIDUALNYCH ---
query_params = st.query_params
url_player = query_params.get("player", None)

# --- NAGŁÓWEK ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=120)

st.markdown(f"<h2>RAPORT DNIA</h2>", unsafe_allow_html=True)

# --- WYBÓR ZAWODNIKA ---
if url_player in LISTA_ZAWODNIKOW:
    st.success(f"✅ ZALOGOWANY: **{url_player}**")
    wybrany_zawodnik = url_player
    if st.button("To nie ja? Zmień zawodnika"):
        st.query_params.clear()
        st.rerun()
else:
    wybrany_zawodnik = st.selectbox("Wybierz swoje nazwisko:", [""] + LISTA_ZAWODNIKOW)

if wybrany_zawodnik:
    # Powrót do klasycznego układu z ekspanderami
    with st.expander("☀️ PORANEK (Wellness)", expanded=True):
        with st.form("wellness_form", clear_on_submit=True):
            sen = st.select_slider("Jakość snu (1=źle, 5=świetnie)", options=[1, 2, 3, 4, 5], value=3)
            zmeczenie = st.select_slider("Poziom zmęczenia (1=duże, 5=brak)", options=[1, 2, 3, 4, 5], value=3)
            bolesnosc = st.select_slider("Bolesność mięśni (1=duża, 5=brak)", options=[1, 2, 3, 4, 5], value=5)
            stres = st.select_slider("Poziom stresu (1=duży, 5=brak)", options=[1, 2, 3, 4, 5], value=5)
            komentarz_w = st.text_input("Uwagi (opcjonalnie):")
            
            if st.form_submit_button("WYŚLIJ RAPORT WELLNESS"):
                now = datetime.now(PL_TZ)
                new_data = pd.DataFrame([{
                    "Data": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "Typ_Raportu": "Wellness",
                    "Zawodnik": wybrany_zawodnik,
                    "Sen": sen,
                    "Zmeczenie": zmeczenie,
                    "Bolesnosc": bolesnosc,
                    "Stres": stres,
                    "RPE": "",
                    "Komentarz": komentarz_w
                }])
                
                old_df = get_existing_data()
                updated_df = pd.concat([old_df, new_data], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=updated_df)
                st.cache_data.clear()
                st.balloons()
                st.success("Wysłano!")

    with st.expander("💪 PO TRENINGU (RPE)", expanded=False):
        with st.form("rpe_form", clear_on_submit=True):
            rpe = st.select_slider("Intensywność treningu (1-10)", options=list(range(1, 11)), value=5)
            komentarz_r = st.text_input("Komentarz do treningu:")
            
            if st.form_submit_button("WYŚLIJ RAPORT RPE"):
                now = datetime.now(PL_TZ)
                new_data_r = pd.DataFrame([{
                    "Data": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "Typ_Raportu": "RPE",
                    "Zawodnik": wybrany_zawodnik,
                    "Sen": "", "Zmeczenie": "", "Bolesnosc": "", "Stres": "",
                    "RPE": rpe,
                    "Komentarz": komentarz_r
                }])
                
                old_df = get_existing_data()
                updated_df = pd.concat([old_df, new_data_r], ignore_index=True)
                conn.update(worksheet="Arkusz1", data=updated_df)
                st.cache_data.clear()
                st.success("Wysłano RPE!")

else:
    st.info("Proszę wybrać zawodnika lub skorzystać z linku.")
