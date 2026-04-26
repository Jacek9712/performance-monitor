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

# --- STYLE CSS (Szybsze renderowanie) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa; }}
    .stButton>button {{ 
        width: 100%; 
        background-color: {COLOR_PRIMARY}; 
        color: white; 
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }}
    div[data-testid="stExpander"] {{ border: none; background: white; border-radius: 15px; }}
    </style>
""", unsafe_allow_html=True)

# --- ŁADOWANIE DANYCH (Zoptymalizowane) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def get_existing_data():
    return conn.read(worksheet="Arkusz1")

# --- LOGIKA LINKÓW INDYWIDUALNYCH ---
# Pobieramy parametry z URL (np. ?player=Jan+Niedzielski)
query_params = st.query_params
url_player = query_params.get("player", None)

# --- NAGŁÓWEK ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=120)

st.markdown(f"<h2 style='text-align: center; color: {COLOR_PRIMARY};'>RAPORT DNIA</h2>", unsafe_allow_html=True)

# --- WYBÓR ZAWODNIKA ---
if url_player in LISTA_ZAWODNIKOW:
    # Jeśli link jest poprawny, blokujemy wybór na tym zawodniku
    st.success(f"📌 ZALOGOWANY: **{url_player}**")
    wybrany_zawodnik = url_player
    if st.button("To nie ja? Zmień zawodnika"):
        st.query_params.clear()
        st.rerun()
else:
    wybrany_zawodnik = st.selectbox("Wybierz swoje nazwisko:", [""] + LISTA_ZAWODNIKOW)

if wybrany_zawodnik:
    tab1, tab2 = st.tabs(["☀️ PORANEK (Wellness)", "💪 PO TRENINGU (RPE)"])
    
    with tab1:
        with st.form("wellness_form", clear_on_submit=True):
            st.markdown("### Monitorowanie Wellness")
            sen = st.select_slider("Jakość snu (1=źle, 5=świetnie)", options=[1, 2, 3, 4, 5], value=3)
            zmeczenie = st.select_slider("Poziom zmęczenia (1=duże, 5=brak)", options=[1, 2, 3, 4, 5], value=3)
            bolesnosc = st.select_slider("Bolesność mięśni (1=duża, 5=brak)", options=[1, 2, 3, 4, 5], value=5)
            stres = st.select_slider("Poziom stresu (1=duży, 5=brak)", options=[1, 2, 3, 4, 5], value=5)
            komentarz_w = st.text_input("Uwagi (opcjonalnie):", placeholder="np. boli mnie łydka")
            
            submit_w = st.form_submit_button("WYŚLIJ RAPORT WELLNESS")
            
            if submit_w:
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
                st.cache_data.clear() # Czyścimy cache po wysłaniu
                st.balloons()
                st.success("Raport Wellness wysłany pomyślnie!")

    with tab2:
        with st.form("rpe_form", clear_on_submit=True):
            st.markdown("### Obciążenie Treningowe")
            rpe = st.select_slider("Intensywność treningu (1-10)", options=list(range(1, 11)), value=5)
            komentarz_r = st.text_input("Komentarz do treningu:", placeholder="np. ciężki trening siłowy")
            
            submit_r = st.form_submit_button("WYŚLIJ RAPORT RPE")
            
            if submit_r:
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
                st.success("Raport RPE wysłany!")

else:
    st.info("Proszę wybrać zawodnika z listy lub skorzystać z indywidualnego linku.")
