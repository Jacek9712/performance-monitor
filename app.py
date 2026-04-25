import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import os

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633" 
COLOR_BG = "#F0F7F4"

# Funkcja do znalezienia logo
def get_logo():
    possible_files = ["herb.png", "logo.png", "logo.jpg", "image_b1bd1c.png"]
    for f in possible_files:
        if os.path.exists(f):
            return f
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

LOGO_PATH = get_logo()

# Ustawienie strefy czasowej dla Polski
PL_TZ = pytz.timezone('Europe/Warsaw')

# --- AKTUALNA LISTA ZAWODNIKÓW ---
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="wide")

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    [data-testid="stToolbar"] {{visibility: hidden !important;}}
    [data-testid="stDecoration"] {{display:none;}}
    [data-testid="stStatusWidget"] {{display:none;}}
    .stDeployButton {{display:none;}}
    
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }}

    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label {{ 
        font-family: 'Anton', sans-serif !important;
    }}
    
    .stApp {{ background-color: {COLOR_BG} !important; }}
    
    h1, h2, h3 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        text-transform: uppercase;
        margin-bottom: 1rem;
    }}
    
    .player-locked {{
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid {COLOR_PRIMARY};
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}

    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 30px !important; 
        border-radius: 20px !important; 
        border-top: 10px solid {COLOR_PRIMARY} !important;
        max-width: 800px;
        margin: 0 auto;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }}
    
    .stButton>button {{
        width: 100%; background-color: {COLOR_PRIMARY} !important; color: #FFFFFF !important;
        height: 3.5em !important; font-size: 1.2rem !important; border-radius: 12px !important;
        text-transform: uppercase;
    }}
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_gsheets(row_data):
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        new_row = pd.DataFrame([row_data])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Arkusz1", data=updated_df)
        st.success("✔ RAPORT WYSŁANY POMYŚLNIE!")
    except Exception as e:
        st.error(f"❌ BŁĄD WYSYŁANIA: {e}")

# Logika sprawdzania zawodnika w URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

def get_active_player():
    # Jeśli zawodnik z URL jest na liście, blokujemy wybór i wyświetlamy status "zalogowany"
    if player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"""
            <div class='player-locked'>
                👤 ZALOGOWANY: {player_from_url.upper()}
            </div>
            """, unsafe_allow_html=True)
        return player_from_url
    # W przeciwnym razie dajemy listę rozwijaną
    return st.selectbox("WYBIERZ ZAWODNIKA:", [""] + LISTA_ZAWODNIKOW)

# Wyświetlanie interfejsu
col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
with col_l2:
    st.image(LOGO_PATH, use_container_width=True)

st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    tab1, tab2 = st.tabs(["☀️ WELLNESS (RANO)", "🏃‍♂️ RPE (PO TRENINGU)"])

    with tab1:
        with st.form("wellness_form", clear_on_submit=True):
            p = get_active_player()
            st.write("---")
            s1 = st.select_slider("JAKOŚĆ SNU", options=[1,2,3,4,5], value=3)
            st.caption("1: Bardzo słabo | 5: Idealnie")
            s2 = st.select_slider("POZIOM ENERGII", options=[1,2,3,4,5], value=3)
            st.caption("1: Wyczerpany | 5: Pełen energii")
            s3 = st.select_slider("STAN MIĘŚNIOWY", options=[1,2,3,4,5], value=3)
            st.caption("1: Silny ból | 5: Brak bólu")
            s4 = st.select_slider("NASTRÓJ / STRES", options=[1,2,3,4,5], value=3)
            st.caption("1: Duży stres | 5: Świetny nastrój")
            k = st.text_area("UWAGI LUB DOLEGLIWOŚCI")
            
            submit = st.form_submit_button("WYŚLIJ RAPORT WELLNESS")
            if submit:
                if p == "":
                    st.warning("Proszę wybrać zawodnika!")
                else:
                    # Zapisujemy datę i dokładną godzinę w polskiej strefie czasowej
                    current_time = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    save_to_gsheets({
                        "Data": current_time, 
                        "Typ_Raportu": "Wellness", 
                        "Zawodnik": p, 
                        "Sen": s1, 
                        "Zmeczenie": s2, 
                        "Bolesnosc": s3, 
                        "Stres": s4, 
                        "RPE": None, 
                        "Komentarz": k
                    })

    with tab2:
        with st.form("rpe_form", clear_on_submit=True):
            p = get_active_player()
            st.write("---")
            r = st.slider("INTENSYWNOŚĆ TRENINGU (RPE)", 0, 10, 5)
            k = st.text_area("KOMENTARZ DO TRENINGU")
            
            submit = st.form_submit_button("WYŚLIJ RAPORT RPE")
            if submit:
                if p == "":
                    st.warning("Proszę wybrać zawodnika!")
                else:
                    # Zapisujemy datę i dokładną godzinę w polskiej strefie czasowej
                    current_time = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    save_to_gsheets({
                        "Data": current_time, 
                        "Typ_Raportu": "RPE", 
                        "Zawodnik": p, 
                        "Sen": None, 
                        "Zmeczenie": None, 
                        "Bolesnosc": None, 
                        "Stres": None, 
                        "RPE": r, 
                        "Komentarz": k
                    })

# --- ADMIN PANEL ---
st.write("<br><br>", unsafe_allow_html=True)
with st.expander("🔐 PANEL SZTABU"):
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        admin_pass = st.text_input("HASŁO DOSTĘPU:", type="password")
        if st.button("ZALOGUJ DO PANELU"):
            if admin_pass == "Warta1912":
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("NIEPOPRAWNE HASŁO")
    else:
        if st.button("WYLOGUJ"):
            st.session_state["authenticated"] = False
            st.rerun()
        df_data = conn.read(worksheet="Arkusz1", ttl=0)
        if not df_data.empty:
            st.dataframe(df_data.sort_index(ascending=False), use_container_width=True)
            csv_file = df_data.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 EKSPORTUJ DANE DO CSV", data=csv_file, file_name=f"raport_warta_{datetime.now(PL_TZ).strftime('%Y%m%d')}.csv", mime="text/csv")
