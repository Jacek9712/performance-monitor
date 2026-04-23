import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA KLUBU ---
COLOR_PRIMARY = "#006633"  # Główna zieleń Warty
COLOR_ACCENT = "#009944"   # Jaśniejsza zieleń akcentowa
COLOR_BG = "#F4F7F6"       # Jasne, czyste tło
COLOR_TEXT = "#1A1A1A"     # Ciemny tekst

# --- LISTA ZAWODNIKÓW (TUTAJ EDYTUJ SKŁAD) ---
LISTA_ZAWODNIKOW = sorted([
    "Kamil Kumoch", 
    "Marcel Stefaniak", 
    "Kacper Szymanek", 
    "Kacper Lepczyński",
    "Tomasz Wojcinowicz"
])

# Konfiguracja strony
st.set_page_config(
    page_title="Warta Poznań - Performance Monitor",
    page_icon="🟢",
    layout="centered"
)

# --- ZAAWANSOWANA STYLIZACJA UI ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1 {{
        color: {COLOR_PRIMARY};
        font-family: 'Arial Black', sans-serif;
        font-weight: 900;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: -1px;
        margin-top: -20px;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; justify-content: center; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #ffffff;
        border-radius: 8px 8px 0px 0px;
        padding: 12px 24px;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        border: 1px solid #dee2e6;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
    }}
    .stForm {{
        background-color: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,102,51,0.1);
        border: 1px solid #edf2f0 !important;
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 12px;
        height: 3.8em;
        background-color: {COLOR_PRIMARY};
        color: white;
        font-weight: bold;
        text-transform: uppercase;
    }}
    .stButton>button:hover {{ background-color: {COLOR_ACCENT}; color: white; }}
    .logo-container {{ display: flex; justify-content: center; padding-top: 20px; margin-bottom: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- LOGO WARTY POZNAŃ ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Warta_Poznan_logo.svg/1200px-Warta_Poznan_logo.svg.png", width=120)
st.markdown('</div>', unsafe_allow_html=True)

st.title("PERFORMANCE MONITOR")

# Obsługa parametrów URL (Indywidualne linki)
query_params = st.query_params
player_from_url = query_params.get("player")

# Funkcja wyboru zawodnika (blokuje wybór jeśli podano w URL)
def get_player_selector(key_suffix):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.info(f"Zalogowany jako: **{player_from_url}**")
        return player_from_url
    else:
        return st.selectbox("Wybierz zawodnika", LISTA_ZAWODNIKOW, key=f"select_{key_suffix}")

# Połączenie z Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Błąd konfiguracji połączenia. Sprawdź plik Secrets.")

# Zakładki
tab1, tab2 = st.tabs(["☀️ PORANNY WELLNESS", "🏃‍♂️ RAPORT RPE"])

def save_to_gsheets(new_row_dict):
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
    except Exception:
        df = pd.DataFrame(columns=["Data", "Typ_Raportu", "Zawodnik", "Sen", "Zmeczenie", "Bolesnosc", "Stres", "RPE", "Komentarz"])
    
    new_row = pd.DataFrame([new_row_dict])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    
    try:
        conn.update(worksheet="Arkusz1", data=updated_df)
        st.success("Dane zapisane pomyślnie!")
        st.balloons()
    except Exception as e:
        st.error("Błąd zapisu. Sprawdź uprawnienia arkusza (Edytor).")

# --- TAB 1: WELLNESS ---
with tab1:
    with st.form("wellness_form", clear_on_submit=True):
        st.markdown(f"<h3 style='color:{COLOR_PRIMARY}; text-align:center;'>Poranny Wellness</h3>", unsafe_allow_html=True)
        current_player_w = get_player_selector("w")
        st.write("---")
        sen = st.select_slider("Jakość snu (1-5)", options=[1, 2, 3, 4, 5], value=3)
        zmeczenie = st.select_slider("Ogólne zmęczenie (1-5)", options=[1, 2, 3, 4, 5], value=3)
        bolesnosc = st.select_slider("Bolesność mięśni (1-5)", options=[1, 2, 3, 4, 5], value=3)
        stres = st.select_slider("Poziom stresu (1-5)", options=[1, 2, 3, 4, 5], value=3)
        st.write("---")
        komentarz_w = st.text_area("Uwagi dodatkowe / Dolegliwości", height=100, placeholder="Np. ból w stawie skokowym...")
        submit_w = st.form_submit_button("ZAPISZ WELLNESS")

    if submit_w:
        save_to_gsheets({
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Typ_Raportu": "Wellness",
            "Zawodnik": current_player_w,
            "Sen": sen,
            "Zmeczenie": zmeczenie,
            "Bolesnosc": bolesnosc,
            "Stres": stres,
            "RPE": None,
            "Komentarz": komentarz_w
        })

# --- TAB 2: RPE ---
with tab2:
    with st.form("rpe_form", clear_on_submit=True):
        st.markdown(f"<h3 style='color:{COLOR_PRIMARY}; text-align:center;'>Raport po treningu</h3>", unsafe_allow_html=True)
        current_player_r = get_player_selector("r")
        st.write("---")
        rpe = st.slider("Intensywność (RPE 0-10)", 0, 10, 5)
        komentarz_r = st.text_area("Uwagi do treningu", height=100, placeholder="Np. wykonano pełny plan...")
        submit_r = st.form_submit_button("ZAPISZ RPE")

    if submit_r:
        save_to_gsheets({
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Typ_Raportu": "RPE",
            "Zawodnik": current_player_r,
            "Sen": None,
            "Zmeczenie": None,
            "Bolesnosc": None,
            "Stres": None,
            "RPE": rpe,
            "Komentarz": komentarz_r
        })

# Widok Administracyjny
if st.checkbox("⚙️ Panel Zarządzania"):
    try:
        df_view = conn.read(worksheet="Arkusz1", ttl=0)
        st.dataframe(df_view.tail(10))
    except:
        st.warning("Baza danych jest obecnie pusta.")
