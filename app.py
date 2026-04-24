import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633" 
COLOR_BG = "#F0F7F4"
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

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

# Ustawienie layout="wide" rozciąga panel na całą szerokość i usuwa błędy typu "narrow"
st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="wide")

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    /* Główne fonty - wyłączone dla ikon i elementów systemowych */
    html, body, [class*="st-"] {{ 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    h1, h2, h3, .stButton>button, .metric-card b {{ 
        font-family: 'Anton', sans-serif !important;
        text-transform: uppercase;
    }}
    
    .stApp {{ 
        background-color: {COLOR_BG} !important; 
    }}
    
    h1, h2, h3 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-align: center; 
        margin-top: 10px;
        letter-spacing: 1px;
    }}
    
    .logo-container {{
        display: flex;
        justify-content: center;
        padding-top: 20px;
    }}
    
    .logo-img {{
        width: 100px;
    }}
    
    /* Naprawa błędu "arrow_right" - reset czcionki dla nagłówka expandera */
    .st-emotion-cache-p6495z, .st-emotion-cache-p6495z p, summary {{
        font-family: 'Segoe UI', sans-serif !important;
        font-weight: 600 !important;
    }}
    
    /* Stylizacja listy zawodników (Selectbox) */
    div[data-baseweb="select"] {{
        background-color: white !important;
        border-radius: 10px !important;
    }}

    /* Centrowanie i stylizacja formularzy */
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 30px !important; 
        border-radius: 20px !important; 
        border-top: 10px solid {COLOR_PRIMARY} !important;
        max-width: 800px;
        margin: 0 auto;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }}
    
    /* Suwaki */
    div[data-baseweb="slider"] [role="presentation"] div,
    div[data-baseweb="slider"] [data-testid="stSliderTickBar"] div {{
        background-color: transparent !important;
        color: #000000 !important;
        font-size: 1.1rem !important;
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
        font-size: 1.2rem !important;
        border-radius: 12px !important;
        border: none !important;
    }}
    
    /* Karty statystyk w panelu trenera */
    .metric-card {{
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #eee;
        border-bottom: 4px solid {COLOR_PRIMARY};
    }}

    /* Usuwanie zbędnych marginesów w expanderach */
    .st-expanderContent {{
        background-color: #ffffff !important;
        border-radius: 0 0 15px 15px !important;
        padding: 20px !important;
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

# Parametry URL
query_params = st.query_params
player_from_url = query_params.get("player", None)

def select_player(key):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"""
            <div style='text-align:center; padding:15px; background:white; border:2px solid {COLOR_PRIMARY}; border-radius:15px; margin-bottom:20px;'>
                <span style='font-size:0.9rem; color:gray; text-transform:uppercase;'>Zalogowany jako:</span><br>
                <span style='font-size:1.6rem; color:{COLOR_PRIMARY}; font-weight:bold;'>{player_from_url}</span>
            </div>
        """, unsafe_allow_html=True)
        return player_from_url
    return st.selectbox("WYBIERZ ZAWODNIKA:", LISTA_ZAWODNIKOW, key=key)

# --- HEADER ---
st.markdown(f'<div class="logo-container"><img src="{LOGO_URL}" class="logo-img"></div>', unsafe_allow_html=True)
st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

# --- LAYOUT DLA ZAWODNIKA ---
_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    tab1, tab2 = st.tabs(["☀️ WELLNESS", "🏃‍♂️ RPE"])

    with tab1:
        with st.form("wellness_form", clear_on_submit=True):
            p = select_player("w_player")
            s1 = st.select_slider("SEN (1-Fatalny, 5-Idealny)", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("ZMĘCZENIE (1-Brak, 5-Bardzo duże)", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("BOLESNOŚĆ (1-Brak, 5-Silna)", options=[1,2,3,4,5], value=3)
            s4 = st.select_slider("STRES (1-Brak, 5-Bardzo duży)", options=[1,2,3,4,5], value=3)
            k = st.text_area("UWAGI / DOLEGLIWOŚCI")
            if st.form_submit_button("WYSYŁAM WELLNESS"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "Wellness", "Zawodnik": p, "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k})

    with tab2:
        with st.form("rpe_form", clear_on_submit=True):
            p = select_player("r_player")
            r = st.slider("INTENSYWNOŚĆ TRENINGU (0-Lekki, 10-Maksymalny)", 0, 10, 5)
            k = st.text_area("KOMENTARZ DO TRENINGU")
            if st.form_submit_button("WYSYŁAM RPE"):
                save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "RPE", "Zawodnik": p, "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": r, "Komentarz": k})

# --- PANEL SZTABU (ADMIN) ---
st.write("<br><br>", unsafe_allow_html=True)
with st.expander("🔐 PANEL SZTABU SZKOLENIOWEGO", expanded=False):
    # Używamy session_state, aby po zalogowaniu formularz zniknął
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        admin_pass = st.text_input("PODAJ HASŁO:", type="password")
        if st.button("ZALOGUJ DO SYSTEMU"):
            if admin_pass == "Warta1912":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("BŁĘDNE HASŁO")
    else:
        # INTERFEJS PO ZALOGOWANIU
        col_out1, col_out2 = st.columns([5, 1])
        with col_out2:
            if st.button("WYLOGUJ"):
                st.session_state["authenticated"] = False
                st.rerun()
            
        try:
            df_data = conn.read(worksheet="Arkusz1", ttl=0)
            
            if not df_data.empty:
                # Statystyki szybkiego podglądu
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f'<div class="metric-card">RAZEM WPISÓW<br><b>{len(df_data)}</b></div>', unsafe_allow_html=True)
                with m2:
                    avg_rpe = df_data[df_data['Typ_Raportu'] == 'RPE']['RPE'].mean()
                    st.markdown(f'<div class="metric-card">ŚR. RPE<br><b>{avg_rpe:.1f if not pd.isna(avg_rpe) else "---"}</b></div>', unsafe_allow_html=True)
                with m3:
                    active = df_data['Zawodnik'].nunique()
                    st.markdown(f'<div class="metric-card">ZAWODNIKÓW<br><b>{active}</b></div>', unsafe_allow_html=True)
                with m4:
                    st.markdown(f'<div class="metric-card">STATUS<br><b style="color:{COLOR_PRIMARY}">ONLINE</b></div>', unsafe_allow_html=True)
                
                st.markdown("### HISTORIA RAPORTÓW")
                st.dataframe(df_data.sort_index(ascending=False), use_container_width=True, height=450)
                
                csv_file = df_data.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 POBIERZ DANE (CSV/EXCEL)",
                    data=csv_file,
                    file_name=f"Warta_Performance_{datetime.now().strftime('%d_%m_%Y')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("Baza danych jest aktualnie pusta.")
        except Exception as err:
            st.error(f"Błąd połączenia z bazą: {err}")
