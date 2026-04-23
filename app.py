import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"  # Główna zieleń klubowa
COLOR_BG = "#F4F7F6"       # Jasne, nowoczesne tło
COLOR_ACCENT = "#004d26"   # Ciemniejsza zieleń dla kontrastu

# --- LISTA ZAWODNIKÓW ---
LISTA_ZAWODNIKOW = sorted([
    "Jan Kowalski", 
    "Adam Nowak", 
    "Piotr Zieliński", 
    "Marek Sportowiec",
    "Tomasz Bramkarz"
])

# Podstawowa konfiguracja strony Streamlit
st.set_page_config(
    page_title="Warta Poznań - Performance Monitor",
    page_icon="⚽",
    layout="centered"
)

# --- STYLIZACJA CSS (CZYTELNOŚĆ I KOLORY) ---
st.markdown(f"""
    <style>
    /* Ogólny styl aplikacji */
    .stApp {{
        background-color: {COLOR_BG};
    }}
    
    /* Nagłówek i napisy */
    h1, h2, h3 {{
        color: {COLOR_PRIMARY};
        text-align: center;
        font-family: 'Arial Black', sans-serif;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}
    
    /* Styl formularza */
    .stForm {{
        background-color: white !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        border: 1px solid #e0e0e0 !important;
    }}
    
    /* Styl przycisku */
    .stButton>button {{
        width: 100%;
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 12px;
        height: 3.5em;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_ACCENT};
        border: none;
    }}

    /* Standardowy wygląd suwaków dla najlepszej czytelności */
    div[data-baseweb="slider"] div {{
        cursor: pointer;
    }}
    
    /* Ukrycie efektów typu śnieg */
    [data-testid="stSnow"] {{
        display: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- WYŚWIETLANIE LOGO I TYTUŁU ---
# Wykorzystujemy stabilny link do logo Warty Poznań
logo_url = "herb.png"
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image(logo_url, width=120)

st.title("PERFORMANCE MONITOR")

# --- INICJALIZACJA POŁĄCZENIA ---
def get_connection():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error("Błąd połączenia. Sprawdź plik Secrets (TOML).")
        return None

conn = get_connection()

def save_to_gsheets(row_data):
    """Funkcja zapisująca dane bez zbędnych efektów wizualnych."""
    if conn is None:
        return
    
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Arkusz1", data=updated_df)
        
        st.success("Raport wysłany pomyślnie!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Błąd podczas zapisu: {e}")

# --- OBSŁUGA ZAWODNIKA (URL / SELECTBOX) ---
query_params = st.query_params
player_from_url = query_params.get("player")

def select_player(key_name):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.info(f"Zalogowany jako: **{player_from_url}**")
        return player_from_url
    return st.selectbox("Wybierz zawodnika z listy", LISTA_ZAWODNIKOW, key=key_name)

# --- ZAKŁADKI INTERFEJSU ---
tab1, tab2 = st.tabs(["☀️ WELLNESS", "🏃‍♂️ RPE"])

with tab1:
    with st.form("form_wellness", clear_on_submit=True):
        st.subheader("Poranny Raport")
        current_player = select_player("well_sel")
        
        st.write("**Oceń swoje samopoczucie (1-5):**")
        sen = st.select_slider("Jakość snu", options=[1, 2, 3, 4, 5], value=3)
        zmeczenie = st.select_slider("Poziom zmęczenia", options=[1, 2, 3, 4, 5], value=3)
        bolesnosc = st.select_slider("Bolesność mięśni", options=[1, 2, 3, 4, 5], value=3)
        stres = st.select_slider("Poziom stresu", options=[1, 2, 3, 4, 5], value=3)
        komentarz = st.text_area("Twoje uwagi (opcjonalnie)")
        
        if st.form_submit_button("ZAPISZ WELLNESS"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "Wellness",
                "Zawodnik": current_player,
                "Sen": sen,
                "Zmeczenie": zmeczenie,
                "Bolesnosc": bolesnosc,
                "Stres": stres,
                "RPE": None,
                "Komentarz": komentarz
            })

with tab2:
    with st.form("form_rpe", clear_on_submit=True):
        st.subheader("Raport Treningowy")
        current_player_rpe = select_player("rpe_sel")
        
        st.write("**Oceń intensywność wysiłku:**")
        rpe_value = st.slider("Skala RPE (0 - brak wysiłku, 10 - max)", 0, 10, 5)
        komentarz_rpe = st.text_area("Uwagi do treningu")
        
        if st.form_submit_button("ZAPISZ RPE"):
            save_to_gsheets({
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Typ_Raportu": "RPE",
                "Zawodnik": current_player_rpe,
                "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None,
                "RPE": rpe_value, "Komentarz": komentarz_rpe
            })

# --- SEKCJA TRENERA (ZABEZPIECZONA HASŁEM) ---
st.divider()
with st.expander("🔐 Panel Trenera"):
    password = st.text_input("Wprowadź hasło, aby zobaczyć wyniki", type="password")
    if password == "Warta1912":
        if conn:
            try:
                view_df = conn.read(worksheet="Arkusz1", ttl=0)
                st.dataframe(view_df.tail(20), use_container_width=True)
                csv = view_df.to_csv(index=False).encode('utf-8')
                st.download_button("Pobierz dane jako CSV", csv, "raporty.csv", "text/csv")
            except:
                st.write("Brak danych do wyświetlenia.")
    elif password != "":
        st.error("Błędne hasło!")
