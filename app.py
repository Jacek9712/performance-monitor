import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import pytz
import streamlit.components.v1 as components

# --- KONFIGURACJA KLUBU (BARWY WARTY POZNAŃ) ---
COLOR_PRIMARY = "#006633"   # Głęboka zieleń
COLOR_SECONDARY = "#004d26" # Ciemniejsza zieleń dla kontrastu
COLOR_BG = "#F1F8E9"        # Bardzo jasne zielone tło
COLOR_TEXT = "#1B5E20"      # Ciemnozielony tekst
PL_TZ = pytz.timezone('Europe/Warsaw')

# Funkcja do znalezienia logo na serwerze
def get_logo():
    possible_files = ["herb.png", "logo.png", "logo.jpg", "image_b1bd1c.png"]
    for f in possible_files:
        if os.path.exists(f):
            return f
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

st.set_page_config(page_title="Warta Poznań - Performance", page_icon="⚽", layout="centered")

# --- ZAAWANSOWANA STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    html, body, [class*="st-"], .stMarkdown, .stSelectbox, .stSlider, .stTextArea, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}
    
    .custom-header {{
        text-align: center;
        margin-bottom: 10px;
    }}

    h1 {{ 
        color: {COLOR_PRIMARY} !important; 
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 1px;
        font-size: 1.8rem !important;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        align-items: center;
        width: 100%;
        margin: 0 auto;
        padding: 10px 0;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 5px;
        justify-content: center;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 10px 10px 0px 0px;
        padding: 5px 20px;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_PRIMARY} !important;
    }}
    
    .stTabs [aria-selected="true"] p {{
        color: white !important;
    }}
    
    [data-testid="stForm"] {{
        background-color: #FFFFFF !important; 
        padding: 20px !important;
        border-radius: 15px !important; 
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05) !important;
    }}

    [data-testid="stFormSubmitButton"] > div {{
        background-color: transparent !important;
    }}

    button[kind="formSubmit"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: #FFFFFF !important;
        width: 100% !important;
        height: 3em !important;
        border: 2px solid white !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-top: 10px !important;
    }}

    .wellness-legend {{
        background-color: #f1f8e9;
        padding: 10px;
        border-radius: 8px;
        border: 1px dashed {COLOR_PRIMARY};
        margin-bottom: 10px;
    }}

    .legend-item {{
        font-size: 0.8rem;
        text-align: center;
    }}

    .login-info {{
        background-color: {COLOR_PRIMARY};
        color: white !important;
        padding: 8px;
        border-radius: 10px;
        text-align: center;
        margin: 0 auto 10px auto;
        max-width: 300px;
        font-weight: bold;
        font-size: 0.9rem;
    }}
    
    /* Styl dla mapy ciała */
    .body-map-container {{
        text-align: center;
        background: #f9f9f9;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 15px;
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
        st.success("✔ RAPORT WYSŁANY!")
    except Exception as e:
        st.error(f"❌ BŁĄD: {e}")

# Logo
col1, col2, col3 = st.columns([1.5, 1, 1.5])
with col2:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-header"><h1>Performance Monitor</h1></div>', unsafe_allow_html=True)

query_params = st.query_params
player_from_url = query_params.get("player", None)

zawodnik = None

if player_from_url in LISTA_ZAWODNIKOW:
    st.markdown(f'<div class="login-info">ZALOGOWANO: {player_from_url.upper()}</div>', unsafe_allow_html=True)
    zawodnik = player_from_url
else:
    zawodnik = st.selectbox("WYBIERZ NAZWISKO:", LISTA_ZAWODNIKOW, index=None, placeholder="Wybierz...")

if zawodnik:
    tab_well, tab_rpe = st.tabs(["📊 WELLNESS", "🏃 RPE"])

    with tab_well:
        with st.form("wellness_form", clear_on_submit=True):
            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            
            st.markdown("""
                <div class="wellness-legend">
                    <div style="display: flex; justify-content: space-around;">
                        <div class="legend-item">🔴 1<br><b>ŹLE</b></div>
                        <div class="legend-item">🟡 3<br><b>ŚREDNIO</b></div>
                        <div class="legend-item">🟢 5<br><b>SUPER</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            s1 = st.select_slider("SEN", options=[1,2,3,4,5], value=3)
            s2 = st.select_slider("ZMĘCZENIE", options=[1,2,3,4,5], value=3)
            s3 = st.select_slider("BOLESNOŚĆ OGÓLNA", options=[1,2,3,4,5], value=3)
            
            st.write("**LOKALIZACJA BÓLU (KLIKNIJ NA OBSZAR):**")
            
            # --- INTERAKTYWNA MAPA CIAŁA (HTML/JS) ---
            body_map_html = """
            <div id="body-map-ui" style="display: flex; flex-direction: column; align-items: center; background: #fff; padding: 10px; border-radius: 10px;">
                <svg viewBox="0 0 200 400" width="180" height="300" id="human-body">
                    <!-- Glowa -->
                    <circle cx="100" cy="30" r="20" fill="#e0e0e0" stroke="#333" class="part" data-name="Głowa"/>
                    <!-- Tors -->
                    <rect x="75" y="55" width="50" height="80" rx="10" fill="#e0e0e0" stroke="#333" class="part" data-name="Klatka/Brzuch"/>
                    <!-- Ramiona -->
                    <rect x="50" y="60" width="20" height="90" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Ramię lewe"/>
                    <rect x="130" y="60" width="20" height="90" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Ramię prawe"/>
                    <!-- Biodra -->
                    <rect x="75" y="140" width="50" height="30" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Biodra/Pachwiny"/>
                    <!-- Nogi (Góra) -->
                    <rect x="77" y="175" width="22" height="100" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Udo lewe"/>
                    <rect x="101" y="175" width="22" height="100" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Udo prawe"/>
                    <!-- Nogi (Dół) -->
                    <rect x="77" y="280" width="22" height="80" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Łydka lewa"/>
                    <rect x="101" y="280" width="22" height="80" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Łydka prawa"/>
                    <!-- Stopy -->
                    <rect x="70" y="365" width="30" height="15" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Stopa lewa"/>
                    <rect x="100" y="365" width="30" height="15" rx="5" fill="#e0e0e0" stroke="#333" class="part" data-name="Stopa prawa"/>
                </svg>
                <p id="selected-part-text" style="margin-top:10px; font-weight:bold; color:#006633;">Zaznaczono: Brak</p>
                <input type="hidden" id="part-input" name="part-input" value="Brak">
            </div>

            <script>
                const parts = document.querySelectorAll('.part');
                const text = document.getElementById('selected-part-text');
                const input = document.getElementById('part-input');

                parts.forEach(part => {
                    part.style.cursor = 'pointer';
                    part.addEventListener('click', () => {
                        // Reset kolorów
                        parts.forEach(p => p.setAttribute('fill', '#e0e0e0'));
                        // Zaznacz nowy
                        part.setAttribute('fill', '#006633');
                        const name = part.getAttribute('data-name');
                        text.innerText = "Zaznaczono: " + name;
                        
                        // Przekazanie do Streamlit (używamy mechanizmu window.parent dla komponentów)
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: name
                        }, '*');
                    });
                });
            </script>
            """
            
            # Integracja interaktywnej mapy jako komponentu, który zwraca wartość
            partia_zaznaczona = components.html(body_map_html, height=400)
            
            # Ponieważ standardowy components.html nie zwraca wartości bezpośrednio do formy bez custom component, 
            # użyjemy selectboxa ukrytego lub jako fallback, ale dla lepszego UX zostawmy prosty selectbox pod spodem jako "potwierdzenie"
            partia = st.selectbox("POTWIERDŹ ZAZNACZONY OBSZAR", ["Brak", "Głowa", "Plecy", "Klatka/Brzuch", "Biodra/Pachwiny", "Udo lewe", "Udo prawe", "Dwugłowy lewy", "Dwugłowy prawy", "Łydka lewa", "Łydka prawa", "Stopa lewa", "Stopa prawa"], index=0)
            
            s4 = st.select_slider("STRES", options=[1,2,3,4,5], value=3)
            k = st.text_area("UWAGI", placeholder="Wpisz ewentualne uwagi...", height=60)
            
            if st.form_submit_button("WYŚLIJ WELLNESS"):
                komentarz_z_partia = f"[{partia}] {k}" if partia != "Brak" else k
                save_to_gsheets({
                    "Data": timestamp, "Typ_Raportu": "Wellness", "Zawodnik": zawodnik, 
                    "Sen": s1, "Zmeczenie": s2, "Bolesnosc": s3, "Stres": s4, 
                    "RPE": None, "Komentarz": komentarz_z_partia
                })

    with tab_rpe:
        with st.form("rpe_form", clear_on_submit=True):
            timestamp = datetime.now(PL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            rpe = st.slider("INTENSYWNOŚĆ (0-10)", 0, 10, 5)
            k_rpe = st.text_area("UWAGI", placeholder="Opisz krótko trening...", height=60)
            
            if st.form_submit_button("WYŚLIJ RPE"):
                save_to_gsheets({
                    "Data": timestamp, "Typ_Raportu": "RPE", "Zawodnik": zawodnik, 
                    "Sen": None, "Zmeczenie": None, "Bolesnosc": None, "Stres": None, 
                    "RPE": rpe, "Komentarz": k_rpe
                })
