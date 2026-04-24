import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633" 
COLOR_BG = "#F0F7F4"

# Funkcja do znalezienia logo na serwerze lub użycia backupu
def get_logo():
    # Twoja nazwa pliku to 'herb.png' - dodajemy ją jako priorytet
    possible_files = ["herb.png", "logo.png", "logo.jpg", "image_b1bd1c.png"]
    for f in possible_files:
        if os.path.exists(f):
            return f
    # Backup, gdyby pliku nie było na serwerze
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

LOGO_PATH = get_logo()

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

# --- STYLIZACJA CSS (ANTON + POPRAWKI) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label {{ 
        font-family: 'Anton', sans-serif !important;
    }}
    
    [data-testid="stIcon"], .st-emotion-cache-p6495z, i, svg {{ 
        font-family: 'Source Sans Pro', sans-serif !important; 
    }}
    
    .stApp {{ background-color: {COLOR_BG} !important; }}
    
    h1, h2, h3 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        text-transform: uppercase;
    }}
    
    .logo-container {{ display: flex; justify-content: center; padding-top: 20px; }}
    
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

    .metric-card {{
        background-color: #ffffff; padding: 15px; border-radius: 12px;
        text-align: center; border-bottom: 4px solid {COLOR_PRIMARY};
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
        st.success("RAPORT WYSŁANY!")
    except Exception as e:
        st.error(f"BŁĄD: {e}")

query_params = st.query_params
player_from_url = query_params.get("player", None)

def select_player(key):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"<div style='text-align:center; padding:15px; background:white; border:2px solid {COLOR_PRIMARY}; border-radius:15px; margin-bottom:20px;'>ZALOGOWANY: <br><span style='font-size:1.6rem; color:{COLOR_PRIMARY};'>{player_from_url}</span></div>", unsafe_allow_html=True)
        return player_from_url
    return st.selectbox("WYBIERZ ZAWODNIKA:", LISTA_ZAWODNIKOW, key=key)

# --- WYŚWIETLANIE LOGO ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
with col_l2:
    st.image(LOGO_PATH, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    tab1, tab2 = st.tabs(["☀️ WELLNESS (SAMOPOCZUCIE)", "🏃‍♂️ RPE (OBCIĄŻENIE)"])

    with tab1:
        with st.form("wellness_form", clear_on_submit=True):
            p = select_player("w_player")
            st.write("---")
            s1 = st.select_slider("JAKOŚĆ SNU", options=[1,2,3,4,5], value=3)
            st.caption("1: Bardzo słabo | 5: Idealnie")
            
            s2 = st.select_slider("POZIOM ENERGII", options=[1,2,3,4,5], value=3)
            st.caption("1: Wyczerpany | 5: Pełen energii")
            
            s3 = st.select_slider("STAN MIĘŚNIOWY", options=[1,2,3,4,5], value=3)
            st.caption("1: Silny ból | 5: Brak bólu")
            
            s4 = st.select_slider("NASTRÓJ / STRES", options=[1,2,3,4,5], value=3)
            st.caption("1: Duży stres | 5: Świetny nastrój")
            
            k = st.text_area("UWAGI (OPCJONALNIE)")
            if st.form_submit_button("WYŚLIJ WELLNESS"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "Wellness", "Zawodnik": p, "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k})

    with tab2:
        with st.form("rpe_form", clear_on_submit=True):
            p = select_player("r_player")
            st.write("---")
            r = st.slider("INTENSYWNOŚĆ TRENINGU (RPE)", 0, 10, 5)
            st.caption("0: Bardzo lekko (Odpoczynek) <------------> 10: Maksymalnie ciężko (Zgon)")
            
            k = st.text_area("KOMENTARZ DO TRENINGU")
            if st.form_submit_button("WYŚLIJ RPE"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "RPE", "Zawodnik": p, "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": r, "Komentarz": k})

# --- ADMIN PANEL ---
st.write("<br><br>", unsafe_allow_html=True)
with st.expander("🔐 PANEL SZTABU"):
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        admin_pass = st.text_input("HASŁO:", type="password")
        if st.button("ZALOGUJ"):
            if admin_pass == "Warta1912":
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("BŁĄD")
    else:
        if st.button("WYLOGUJ"):
            st.session_state["authenticated"] = False
            st.rerun()
        df_data = conn.read(worksheet="Arkusz1", ttl=0)
        if not df_data.empty:
            st.dataframe(df_data.sort_index(ascending=False), use_container_width=True)
            csv_file = df_data.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 POBIERZ DANE", data=csv_file, file_name="warta_data.csv", mime="text/csv")
