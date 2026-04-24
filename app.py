import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633" 
COLOR_BG = "#F0F7F4"

# --- AKTUALNA LISTA ZAWODNIKÓW ---
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak",
    "Bartosz Wiktoruk",
    "Dima Avdieiev",
    "Filip Jakubowski",
    "Filip Tonder",
    "Filip Waluś",
    "Igor Kornobis",
    "Iwo Wojciechowski",
    "Jakub Kosiorek",
    "Jan Niedzielski",
    "Kacper Lepczyński",
    "Kacper Rychert",
    "Kacper Szymanek",
    "Kamil Kumoch",
    "Karol Dziedzic",
    "Leo Przybylak",
    "Marcel Stefaniak",
    "Marcell Zylla",
    "Mateusz Stanek",
    "Michał Smoczyński",
    "Patryk Kusztal",
    "Paweł Kwiatkowski",
    "Sebastian Steblecki",
    "Szymon Michalski",
    "Szymon Zalewski",
    "Tomasz Wojcinowicz"
])

# Ustawienie layout="wide" rozwiązuje problem z napisem "narrow" i rozciąga panel na całą szerokość
st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="wide")

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    html, body, [class*="st-"] {{ 
        font-family: 'Anton', sans-serif !important; 
    }}
    
    .stApp {{ 
        background-color: {COLOR_BG} !important; 
    }}
    
    h1, h2, h3 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        text-transform: uppercase; 
    }}
    
    /* Centrowanie formularzy na dużych ekranach */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 30px !important; 
        border-radius: 20px !important; 
        border-top: 10px solid {COLOR_PRIMARY} !important;
        max-width: 800px;
        margin: 0 auto;
    }}
    
    /* Stylizacja suwaków */
    div[data-baseweb="slider"] [role="presentation"] div,
    div[data-baseweb="slider"] [data-testid="stSliderTickBar"] div {{
        background-color: transparent !important;
        color: #000000 !important;
        font-size: 1.1rem !important;
        margin-top: 8px !important;
    }}
    
    div[data-baseweb="slider"] > div > div {{ 
        background: {COLOR_PRIMARY} !important; 
    }}
    
    /* Przyciski */
    .stButton>button {{
        width: 100%; 
        background-color: {COLOR_PRIMARY} !important; 
        color: #FFFFFF !important;
        height: 3.5em !important; 
        font-family: 'Anton', sans-serif !important; 
        font-size: 1.2rem !important;
        text-transform: uppercase; 
        border-radius: 12px !important;
        transition: 0.3s;
    }}
    
    .stButton>button:hover {{
        background-color: #004d26 !important;
        transform: scale(1.02);
    }}

    /* Panel Admina - Karty statystyk */
    .metric-card {{
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-bottom: 4px solid {COLOR_PRIMARY};
    }}
    
    .admin-container {{
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #ddd;
        margin-top: 20px;
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
        st.success("RAPORT WYSŁANY POMYŚLNIE!")
    except Exception as e:
        st.error(f"BŁĄD ZAPISU: {e}")

# Pobieranie parametrów URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

def select_player(key):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"""
            <div style='text-align:center; padding:15px; background:white; border:2px solid {COLOR_PRIMARY}; border-radius:15px; margin-bottom:20px;'>
                <span style='font-size:0.9rem; color:gray; text-transform:uppercase;'>Zalogowany jako:</span><br>
                <span style='font-size:1.6rem; color:{COLOR_PRIMARY};'>{player_from_url}</span>
            </div>
        """, unsafe_allow_html=True)
        return player_from_url
    return st.selectbox("WYBIERZ ZAWODNIKA:", LISTA_ZAWODNIKOW, key=key)

# --- NAGŁÓWEK ---
st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

# --- SEKCJA GŁÓWNA ---
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    tab1, tab2 = st.tabs(["☀️ WELLNESS", "🏃‍♂️ RPE"])

    with tab1:
        with st.form("well"):
            p = select_player("w_sel")
            s1 = st.select_slider("SEN", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("BOLESNOŚĆ", options=[1,2,3,4,5], value=3)
            s4 = st.select_slider("STRES", options=[1,2,3,4,5], value=3)
            k = st.text_area("UWAGI / DOLEGLIWOŚCI")
            if st.form_submit_button("WYŚLIJ WELLNESS"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "Wellness", "Zawodnik": p, "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k})

    with tab2:
        with st.form("rpe"):
            p = select_player("r_sel")
            r = st.slider("INTENSYWNOŚĆ TRENINGU (0-10)", 0, 10, 5)
            k = st.text_area("UWAGI DO TRENINGU")
            if st.form_submit_button("WYŚLIJ RPE"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "RPE", "Zawodnik": p, "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": r, "Komentarz": k})

# --- NOWOCZESNY PANEL ADMINISTRATORA ---
# Usunięto zbędny tekst i poprawiono wywołanie HTML
st.write("<br><br>", unsafe_allow_html=True)
with st.expander("🔐 PANEL SZTABU SZKOLENIOWEGO"):
    haslo = st.text_input("PODAJ HASŁO DOSTĘPU:", type="password")
    
    if haslo == "Warta1912":
        st.markdown('<div class="admin-container">', unsafe_allow_html=True)
        try:
            data = conn.read(worksheet="Arkusz1", ttl=0)
            
            if not data.empty:
                # Metryki w kartach
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f'<div class="metric-card"><h4>WPISY</h4><h2>{len(data)}</h2></div>', unsafe_allow_html=True)
                with m2:
                    avg_rpe = data[data['Typ_Raportu'] == 'RPE']['RPE'].mean()
                    st.markdown(f'<div class="metric-card"><h4>ŚR. RPE</h4><h2>{avg_rpe:.1f if not pd.isna(avg_rpe) else "---"}</h2></div>', unsafe_allow_html=True)
                with m3:
                    unique_players = data['Zawodnik'].nunique()
                    st.markdown(f'<div class="metric-card"><h4>AKTYWNI</h4><h2>{unique_players}</h2></div>', unsafe_allow_html=True)
                with m4:
                    st.markdown(f'<div class="metric-card"><h4>KLUB</h4><h2>WARTA</h2></div>', unsafe_allow_html=True)
                
                st.write("<br>", unsafe_allow_html=True)
                
                # Tabela danych
                st.markdown("### PRZEGLĄD BAZY DANYCH")
                st.dataframe(data.sort_index(ascending=False), use_container_width=True)
                
                # Eksport
                csv = data.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 EKSPORTUJ DANE DO EXCEL (CSV)",
                    data=csv,
                    file_name=f"Warta_Backup_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("Brak danych w arkuszu.")
        except Exception as e:
            st.error(f"Błąd ładowania danych: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    elif haslo != "":
        st.error("NIEPRAWIDŁOWE HASŁO")
