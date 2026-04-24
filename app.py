import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633" 
COLOR_BG = "#F0F7F4"

# --- AKTUALNA LISTA ZAWODNIKÓW (ZGODNIE ZE ZDJĘCIEM) ---
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

st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="centered")

# --- STYLIZACJA CSS (ANTON FONT & SLIDERS & ADMIN PANEL) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    html, body, [class*="st-"] {{ font-family: 'Anton', sans-serif !important; }}
    .stApp {{ background-color: {COLOR_BG} !important; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY} !important; text-align: center; text-transform: uppercase; }}
    .stForm {{ background-color: #FFFFFF !important; padding: 30px !important; border-radius: 20px !important; border-top: 10px solid {COLOR_PRIMARY} !important; }}
    
    /* Naprawa suwaków */
    div[data-baseweb="slider"] [role="presentation"] div,
    div[data-baseweb="slider"] [data-testid="stSliderTickBar"] div {{
        background-color: transparent !important;
        color: #000000 !important;
        font-size: 1.1rem !important;
        margin-top: 8px !important;
        text-shadow: 1px 1px 1px #fff !important;
    }}
    div[data-baseweb="slider"] > div > div {{ background: {COLOR_PRIMARY} !important; }}
    
    /* Przyciski */
    .stButton>button {{
        width: 100%; background-color: {COLOR_PRIMARY} !important; color: #FFFFFF !important;
        height: 4em !important; font-family: 'Anton', sans-serif !important; font-size: 1.4rem !important;
        text-transform: uppercase; border-radius: 12px !important;
    }}

    /* Stylizacja panelu Admina */
    .admin-box {{
        background-color: #e8f0eb;
        padding: 20px;
        border-radius: 15px;
        border: 1px dashed {COLOR_PRIMARY};
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

query_params = st.query_params
player_from_url = query_params.get("player", None)

def select_player(key):
    if player_from_url and player_from_url in LISTA_ZAWODNIKOW:
        st.markdown(f"<div style='text-align:center; padding:10px; border:2px solid {COLOR_PRIMARY}; border-radius:10px; margin-bottom:15px;'>ZAWODNIK: <br><span style='font-size:1.5rem; color:{COLOR_PRIMARY};'>{player_from_url}</span></div>", unsafe_allow_html=True)
        return player_from_url
    return st.selectbox("WYBIERZ ZAWODNIKA:", LISTA_ZAWODNIKOW, key=key)

st.markdown("<h1>Performance Monitor</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["☀️ WELLNESS", "🏃‍♂️ RPE"])

with tab1:
    with st.form("well"):
        p = select_player("w_sel")
        s1 = st.select_slider("SEN", options=[1,2,3,4,5], value=3)
        s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
        s3 = st.select_slider("BOLESNOŚĆ", options=[1,2,3,4,5], value=3)
        s4 = st.select_slider("STRES", options=[1,2,3,4,5], value=3)
        k = st.text_area("UWAGI")
        if st.form_submit_button("WYŚLIJ WELLNESS"):
            save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "Wellness", "Zawodnik": p, "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, "RPE": None, "Komentarz": k})

with tab2:
    with st.form("rpe"):
        p = select_player("r_sel")
        r = st.slider("INTENSYWNOŚĆ (0-10)", 0, 10, 5)
        k = st.text_area("KOMENTARZ")
        if st.form_submit_button("WYŚLIJ RPE"):
            save_to_gsheets({"Data": datetime.now().strftime("%Y-%m-%d"), "Typ_Raportu": "RPE", "Zawodnik": p, "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, "RPE": r, "Komentarz": k})

# --- NOWOCZESNY PANEL ADMINISTRATORA ---
st.write("---")
with st.expander("🔐 PANEL TRENERA (LOGOWANIE)"):
    st.markdown('<div class="admin-box">', unsafe_allow_html=True)
    haslo = st.text_input("PODAJ HASŁO DOSTĘPU:", type="password")
    
    if haslo == "Warta1912":
        st.success("DOSTĘP AUTORYZOWANY")
        try:
            # Pobranie danych bez cache, aby widzieć nowe wpisy
            data = conn.read(worksheet="Arkusz1", ttl=0)
            
            if not data.empty:
                # Podstawowe statystyki w panelu
                c1, c2, c3 = st.columns(3)
                c1.metric("Wszystkie wpisy", len(data))
                
                last_rpe = data[data['Typ_Raportu'] == 'RPE']['RPE'].mean()
                if not pd.isna(last_rpe):
                    c2.metric("Średnie RPE", f"{last_rpe:.1f}")
                
                # Podgląd tabeli
                st.markdown("### OSTATNIE WPISY")
                st.dataframe(data.sort_index(ascending=False).head(50), use_container_width=True)
                
                # Przycisk do pobrania CSV
                csv = data.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="POBIERZ CAŁĄ BAZĘ (CSV)",
                    data=csv,
                    file_name=f"warta_monitor_backup_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("Baza danych jest aktualnie pusta.")
        except Exception as e:
            st.error(f"Problem z połączeniem arkusza: {e}")
    elif haslo != "":
        st.error("BŁĘDNE HASŁO")
    st.markdown('</div>', unsafe_allow_html=True)
