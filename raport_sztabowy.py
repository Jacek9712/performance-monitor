import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar
import io
import os

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"  # Zieleń Warty
COLOR_BG = "#F1F8E9"
COLOR_TEXT = "#1B5E20"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_SZTAB = "WartaSztab2024"
GODZINA_WELLNESS = 10 
GODZINA_RPE = 17

# Lista zawodników (identyczna jak w aplikacji głównej)
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

st.set_page_config(page_title="Warta Poznań - Panel Sztabu", layout="wide")

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    
    .stApp {{ 
        background: linear-gradient(180deg, #FFFFFF 0%, #E8F5E9 100%) !important; 
    }}

    html, body, [class*="st-"], .stMarkdown, label, p, span {{ 
        font-family: 'Anton', sans-serif !important;
        color: {COLOR_TEXT};
    }}

    h1, h2, h3 {{
        color: {COLOR_PRIMARY} !important;
        text-transform: uppercase;
        text-align: center;
    }}
    
    .logo-container {{ 
        display: flex; 
        justify-content: center; 
        padding: 10px 0;
    }}
    
    [data-testid="stDataFrame"] {{
        background-color: white;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- SYSTEM LOGOWANIA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]:
        return True
    st.markdown(f"<h1>🔐 LOGOWANIE SZTABU</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pwd = st.text_input("Hasło:", type="password")
        if st.button("Zaloguj"):
            if pwd == PASSWORD_SZTAB:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Błędne hasło!")
    return False

if not check_password():
    st.stop()

# --- ŁADOWANIE LOGO ---
def get_logo():
    possible_files = ["herb.png", "logo.png", "logo.jpg"]
    for f in possible_files:
        if os.path.exists(f):
            return f
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png"

# Header z Logo
col_l1, col_l2, col_l3 = st.columns([1, 0.5, 1])
with col_l2:
    st.image(get_logo(), use_container_width=True)

# Słownik miesięcy
NAZWY_MIESIECY = {
    1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
    5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
    9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
}

with st.sidebar:
    st.subheader("🗓️ WYBÓR OKRESU")
    teraz = datetime.now(PL_TZ)
    wybrany_rok = st.selectbox("Rok", [2024, 2025, 2026], index=1)
    wybrany_miesiac_nazwa = st.selectbox("Miesiąc", list(NAZWY_MIESIECY.values()), index=teraz.month-1)
    wybrany_miesiac = [k for k, v in NAZWY_MIESIECY.items() if v == wybrany_miesiac_nazwa][0]
    
    st.write("---")
    st.subheader("📥 EKSPORT")
    btn_container = st.empty()
    
    if st.button("Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

st.markdown(f"<h1>RAPORT: {wybrany_miesiac_nazwa} {wybrany_rok}</h1>", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Arkusz1", ttl="1s")
    
    if df is not None and not df.empty:
        # Konwersja i czyszczenie danych
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.dropna(subset=['Data'])
        df['Miesiac_Nr'] = df['Data'].dt.month
        df['Rok_Nr'] = df['Data'].dt.year
        df['Godzina_H'] = df['Data'].dt.hour
        
        # Filtrowanie danych do wybranego okresu
        df_okres = df[(df['Miesiac_Nr'] == wybrany_miesiac) & (df['Rok_Nr'] == wybrany_rok)].copy()
        
        # Obliczanie dni do analizy (jeśli obecny miesiąc, to do dzisiaj)
        dni_max = calendar.monthrange(wybrany_rok, wybrany_miesiac)[1]
        if wybrany_rok == teraz.year and wybrany_miesiac == teraz.month:
            dni_analizy = teraz.day
        else:
            dni_analizy = dni_max

        stats_wellness = []
        stats_rpe = []
        
        for z in LISTA_ZAWODNIKOW:
            p_data = df_okres[df_okres['Zawodnik'] == z]
            
            # Statystyki Wellness
            well = p_data[p_data['Typ_Raportu'] == 'Wellness']
            well_on_time = well[well['Godzina_H'] < GODZINA_WELLNESS]['Data'].dt.date.nunique()
            well_late = well[well['Godzina_H'] >= GODZINA_WELLNESS]['Data'].dt.date.nunique()
            well_braki = max(0, dni_analizy - well['Data'].dt.date.nunique())
            
            stats_wellness.append({
                "Zawodnik": z,
                "O czasie": well_on_time,
                "Spóźnione": well_late,
                "Brak raportu": well_braki,
                "SUMA BRAKÓW": well_braki + well_late
            })
            
            # Statystyki RPE
            rpe_d = p_data[p_data['Typ_Raportu'] == 'RPE']
            rpe_on_time = rpe_d[rpe_d['Godzina_H'] < GODZINA_RPE]['Data'].dt.date.nunique()
            rpe_late = rpe_d[rpe_d['Godzina_H'] >= GODZINA_RPE]['Data'].dt.date.nunique()
            rpe_braki = max(0, dni_analizy - rpe_d['Data'].dt.date.nunique())
            
            stats_rpe.append({
                "Zawodnik": z,
                "O czasie": rpe_on_time,
                "Spóźnione": rpe_late,
                "Brak raportu": rpe_braki,
                "SUMA BRAKÓW": rpe_braki + rpe_late
            })
            
        df_well_final = pd.DataFrame(stats_wellness).sort_values("SUMA BRAKÓW", ascending=False)
        df_rpe_final = pd.DataFrame(stats_rpe).sort_values("SUMA BRAKÓW", ascending=False)

        # Eksport do Excela
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_well_final.to_excel(writer, index=False, sheet_name='Wellness')
                df_rpe_final.to_excel(writer, index=False, sheet_name='RPE')
            
            btn_container.download_button(
                label="📥 Pobierz Raport .xlsx",
                data=output.getvalue(),
                file_name=f"Warta_Raport_{wybrany_miesiac_nazwa}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except:
            pass

        # --- WYŚWIETLANIE TABEL ---
        col_well, col_rpe = st.columns(2)
        
        with col_well:
            st.subheader(f"📋 WELLNESS (LIMI {GODZINA_WELLNESS}:00)")
            st.dataframe(
                df_well_final.style.background_gradient(subset=['SUMA BRAKÓW'], cmap="Reds"),
                use_container_width=True, hide_index=True
            )
        
        with col_rpe:
            st.subheader(f"🏃 RPE (LIMIT {GODZINA_RPE}:00)")
            st.dataframe(
                df_rpe_final.style.background_gradient(subset=['SUMA BRAKÓW'], cmap="Reds"),
                use_container_width=True, hide_index=True
            )
            
    else:
        st.info("Brak danych do wyświetlenia dla wybranego okresu.")

except Exception as e:
    st.error(f"Wystąpił problem z połączeniem lub danymi: {e}")
