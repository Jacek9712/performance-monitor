import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA WIZUALNA (Warta Poznań) ---
STYL_KLUBU = {
    "primary": "#006633",
    "accent": "#009944",
    "bg": "#F4F7F6"
}

# --- LISTA ZAWODNIKÓW ---
LISTA_ZAWODNIKOW = sorted([
    "Jan Kowalski", 
    "Adam Nowak", 
    "Piotr Zieliński", 
    "Marek Sportowiec",
    "Tomasz Bramkarz"
])

st.set_page_config(
    page_title="Warta Poznań - Performance Monitor",
    page_icon="🟢",
    layout="centered"
)

# --- CSS - WYGLĄD ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {STYL_KLUBU['bg']}; }}
    h1 {{ color: {STYL_KLUBU['primary']}; text-align: center; font-family: 'Arial Black', sans-serif; }}
    .stForm {{ background-color: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
    .stButton>button {{ width: 100%; background-color: {STYL_KLUBU['primary']}; color: white; border-radius: 10px; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Warta_Poznan_logo.svg/1200px-Warta_Poznan_logo.svg.png", width=100)
st.title("WARTA POZNAŃ - MONITORING")

# --- INICJALIZACJA POŁĄCZENIA ---
def init_connection():
    try:
        # Próba połączenia z Google Sheets przy użyciu sekretów
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Nie udało się zainicjować połączenia. Sprawdź 'Secrets' w Streamlit Cloud.")
        st.exception(e)
        return None

conn = init_connection()

def save_data(data_dict):
    """Zapisuje dane do arkusza."""
    if conn is None:
        st.error("Brak aktywnego połączenia z bazą danych.")
        return

    try:
        # Odczytujemy aktualny stan arkusza
        existing_data = conn.read(worksheet="Arkusz1", ttl=0)
        
        # Tworzymy nowy wiersz
        new_row = pd.DataFrame([data_dict])
        
        # Łączymy dane i aktualizujemy arkusz
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        conn.update(worksheet="Arkusz1", data=updated_df)
        
        st.success("Dane zostały zapisane pomyślnie!")
        st.balloons()
        # Czyścimy cache, aby kolejne odczyty były świeże
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Wystąpił błąd podczas zapisu danych.")
        st.info("Upewnij się, że adres email konta serwisowego ma uprawnienia EDYTORA w arkuszu Google.")
        st.error(str(e))

# --- LOGIKA WYBORU ZAWODNIKA (URL / SELECTBOX) ---
query_params = st.query_params
player_from_url = query_params.get("player")

def select_player(tab_name):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.info(f"Zawodnik: **{player_from_url}**")
        return player_from_url
    return st.selectbox("Wybierz zawodnika", LISTA_ZAWODNIKOW, key=f"sel_{tab_name}")

# --- INTERFEJS UŻYTKOWNIKA ---
tab1, tab2 = st.tabs(["☀️ Wellness (Rano)", "🏃‍♂️ Trening (RPE)"])

with tab1:
    with st.form("wellness_form", clear_on_submit=True):
        st.subheader("Poranny Raport Wellness")
        z_name = select_player("well")
        
        col1, col2 = st.columns(2)
        with col1:
            sen = st.select_slider("Jakość snu", options=[1,2,3,4,5], value=3)
            zmeczenie = st.select_slider("Zmęczenie", options=[1,2,3,4,5], value=3)
        with col2:
            bolesnosc = st.select_slider("Bolesność", options=[1,2,3,4,5], value=3)
            stres = st.select_slider("Stres", options=[1,2,3,4,5], value=3)
            
        uwagi = st.text_area("Dodatkowe uwagi (wellness)")
        
        submit_well = st.form_submit_button("WYŚLIJ RAPORT WELLNESS")
        
        if submit_well:
            save_data({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "Wellness",
                "Zawodnik": z_name,
                "Sen": sen,
                "Zmeczenie": zmeczenie,
                "Bolesnosc": bolesnosc,
                "Stres": stres,
                "RPE": None,
                "Komentarz": uwagi
            })

with tab2:
    with st.form("rpe_form", clear_on_submit=True):
        st.subheader("Raport Po-Treningowy")
        z_name_rpe = select_player("rpe")
        
        rpe_val = st.slider("Intensywność treningu (0-10)", 0, 10, 5)
        uwagi_rpe = st.text_area("Uwagi do treningu")
        
        submit_rpe = st.form_submit_button("WYŚLIJ RAPORT RPE")
        
        if submit_rpe:
            save_data({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE",
                "Zawodnik": z_name_rpe,
                "Sen": None,
                "Zmeczenie": None,
                "Bolesnosc": None,
                "Stres": None,
                "RPE": rpe_val,
                "Komentarz": uwagi_rpe
            })

# Widok danych dla administratora (opcjonalny podgląd)
if st.checkbox("Pokaż ostatnie wpisy (tylko trener)"):
    if conn:
        try:
            df_view = conn.read(worksheet="Arkusz1", ttl=0)
            st.dataframe(df_view.tail(10))
        except:
            st.warning("Nie można załadować podglądu danych")
