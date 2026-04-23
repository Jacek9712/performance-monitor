import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Konfiguracja strony
st.set_page_config(
    page_title="Performance Monitor Pro",
    page_icon="👟",
    layout="centered"
)

# Stylizacja UI dla lepszego wyglądu na telefonie
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        height: 3.5em; 
        background-color: #007bff; 
        color: white; 
        font-weight: bold;
        margin-top: 20px;
    }
    .stSlider { padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 System Monitoringu")

# Połączenie z Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Błąd połączenia. Sprawdź konfigurację Secrets w panelu Streamlit.")

# Zakładki
tab1, tab2 = st.tabs(["☀️ Poranny Wellness", "🏃‍♂️ Raport RPE (Trening)"])

# Lista zawodników
lista_zawodnikow = ["Jan Kowalski", "Adam Nowak", "Piotr Zieliński", "Marek Sportowiec"]
# Opisy skali wellness
wellness_options = {1: "1 - Bardzo słabo", 2: "2 - Słabo", 3: "3 - Przeciętnie", 4: "4 - Dobrze", 5: "5 - Bardzo dobrze"}

# --- TAB 1: WELLNESS ---
with tab1:
    with st.form("wellness_form", clear_on_submit=True):
        st.subheader("Ocena samopoczucia (Skala 1-5)")
        zawodnik_w = st.selectbox("Wybierz zawodnika", lista_zawodnikow, key="w_name")
        
        st.write("---")
        # Skala 1-5 z opisami dla jasności
        sen = st.select_slider("Jakość snu", options=[1, 2, 3, 4, 5], value=3, 
                               help="1: Fatalna noc, 5: Doskonały wypoczynek")
        
        zmeczenie = st.select_slider("Ogólne zmęczenie", options=[1, 2, 3, 4, 5], value=3,
                                    help="1: Bardzo zmęczony, 5: Pełen energii")
        
        bolesnosc = st.select_slider("Bolesność mięśniowa (Soreness)", options=[1, 2, 3, 4, 5], value=3,
                                    help="1: Silne zakwasy/ból, 5: Brak bolesności")
        
        stres = st.select_slider("Poziom stresu", options=[1, 2, 3, 4, 5], value=3,
                                help="1: Bardzo wysoki stres, 5: Pełen spokój")
        
        st.write("---")
        komentarz_w = st.text_area("Uwagi dodatkowe / Dolegliwości", 
                                  placeholder="Jak się czujesz? Czy coś Cię boli? (np. ból kolana, ból głowy)",
                                  height=150)
        
        submit_w = st.form_submit_button("WYŚLIJ PORANNY WELLNESS")

    if submit_w:
        try:
            existing_data = conn.read(worksheet="Arkusz1", ttl=0)
            new_row = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "Wellness",
                "Zawodnik": zawodnik_w,
                "Sen": sen,
                "Zmeczenie": zmeczenie,
                "Bolesnosc": bolesnosc,
                "Stres": stres,
                "RPE": None,
                "Komentarz": komentarz_w
            }])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Arkusz1", data=updated_df)
            st.success("Zapisano poranny wellness!")
            st.balloons()
        except Exception as e:
            st.error(f"Błąd zapisu: {e}")

# --- TAB 2: RPE ---
with tab2:
    with st.form("rpe_form", clear_on_submit=True):
        st.subheader("Ocena obciążenia treningowego")
        zawodnik_r = st.selectbox("Wybierz zawodnika", lista_zawodnikow, key="r_name")
        
        st.write("---")
        rpe = st.slider("Intensywność treningu (RPE 0-10)", 0, 10, 5, 
                        help="0: Brak wysiłku, 10: Maksymalny wysiłek")
        
        komentarz_r = st.text_area("Dodatkowe uwagi do treningu", 
                                  placeholder="Opisz jak przebiegł trening lub podaj powód zmiany planu",
                                  height=150)
        
        submit_r = st.form_submit_button("WYŚLIJ RAPORT RPE")

    if submit_r:
        try:
            existing_data = conn.read(worksheet="Arkusz1", ttl=0)
            new_row = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE",
                "Zawodnik": zawodnik_r,
                "Sen": None,
                "Zmeczenie": None,
                "Bolesnosc": None,
                "Stres": None,
                "RPE": rpe,
                "Komentarz": komentarz_r
            }])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Arkusz1", data=updated_df)
            st.success("Zapisano raport RPE!")
            st.balloons()
        except Exception as e:
            st.error(f"Błąd zapisu: {e}")

# Widok administracyjny
if st.checkbox("Pokaż ostatnie wpisy (widok trenera)"):
    df = conn.read(worksheet="Arkusz1", ttl=0)
    st.dataframe(df.tail(10))
