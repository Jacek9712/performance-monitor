import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time
import pytz
import calendar
import matplotlib # Wymagane przez Pandas do kolorowania tabel
import io

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"
COLOR_TEXT = "#1a1a1a"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_SZTAB = "WartaSztab2024"
GODZINA_GRANICZNA = 10 # Raporty do 10:00 są "o czasie"

# Pełna lista zawodników
LISTA_ZAWODNIKOW = sorted([
    "Bartosz Piechowiak", "Bartosz Wiktoruk", "Dima Avdieiev", "Filip Jakubowski", 
    "Filip Tonder", "Filip Waluś", "Igor Kornobis", "Iwo Wojciechowski", 
    "Jakub Kosiorek", "Jan Niedzielski", "Kacper Lepczyński", "Kacper Rychert", 
    "Kacper Szymanek", "Kamil Kumoch", "Karol Dziedzic", "Leo Przybylak", 
    "Marcel Stefaniak", "Marcell Zylla", "Mateusz Stanek", "Michał Smoczyński", 
    "Patryk Kusztal", "Paweł Kwiatkowski", "Sebastian Steblecki", 
    "Szymon Michalski", "Szymon Zalewski", "Tomasz Wojcinowicz"
])

# Wymuszenie konfiguracji strony
st.set_page_config(
    page_title="Warta Poznań - Panel Sztabu", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SYSTEM LOGOWANIA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]:
        return True
    
    st.markdown(f"<h1 style='color: {COLOR_PRIMARY};'>🔐 PANEL SZTABU - LOGOWANIE</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        pwd = st.text_input("Hasło dostępu:", type="password")
        if st.button("Zaloguj"):
            if pwd == PASSWORD_SZTAB:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Błędne hasło!")
    return False

if not check_password():
    st.stop()

# --- STYLIZACJA CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa !important; color: {COLOR_TEXT} !important; }}
    h1, h2, h3, h4 {{ color: {COLOR_PRIMARY} !important; text-align: center !important; text-transform: uppercase !important; font-weight: bold !important; }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {COLOR_TEXT} !important; }}
    div[data-testid="stDataFrame"] {{ background-color: white !important; border-radius: 10px !important; padding: 5px !important; border: 1px solid #e0e0e0 !important; }}
    [data-testid="stSidebar"] {{ background-color: white !important; border-right: 3px solid {COLOR_PRIMARY} !important; }}
    [data-testid="stSidebar"] * {{ color: {COLOR_TEXT} !important; }}
    .stAlert {{ background-color: white !important; border: 1px solid {COLOR_PRIMARY} !important; }}
    </style>
    """, unsafe_allow_html=True)

# Słownik nazw miesięcy
NAZWY_MIESIECY = {
    1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
    5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
    9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
}

# --- FUNKCJA EKSPORTU DO EXCELA ---
def to_excel(df_summary, df_raw):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Podsumowanie_Miesiaca')
        df_raw.to_excel(writer, index=False, sheet_name='Wszystkie_Wpisy')
    return output.getvalue()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=100)
    st.markdown(f"<h3 style='text-align: center;'>SYSTEM ANALIZY</h3>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("🗓️ Wybierz okres")
    teraz = datetime.now(PL_TZ)
    wybrany_rok = st.selectbox("Rok", options=[2024, 2025, 2026], index=[2024, 2025, 2026].index(teraz.year))
    wybrany_miesiac_nazwa = st.selectbox("Miesiąc", options=list(NAZWY_MIESIECY.values()), index=teraz.month - 1)
    
    # Konwersja nazwy na numer
    wybrany_miesiac = [k for k, v in NAZWY_MIESIECY.items() if v == wybrany_miesiac_nazwa][0]
    
    st.write("---")
    if st.button("Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

st.title(f"📊 Analiza: {wybrany_miesiac_nazwa} {wybrany_rok}")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Arkusz1", ttl="1s")
    
    if df is None or df.empty:
        st.warning("Brak danych w arkuszu.")
    else:
        df['Data'] = pd.to_datetime(df['Data'], format='mixed')
        df['Dzien'] = df['Data'].dt.date
        df['Godzina'] = df['Data'].dt.hour
        
        # Obliczanie liczby dni w wybranym miesiącu (do dzisiaj, jeśli to obecny miesiąc)
        teraz_data = datetime.now(PL_TZ).date()
        dni_w_miesiacu_max = calendar.monthrange(wybrany_rok, wybrany_miesiac)[1]
        
        # Logika: jeśli patrzymy na przyszłość, skala to pełny miesiąc. 
        # Jeśli na obecny miesiąc, liczymy do dnia dzisiejszego.
        if wybrany_rok == teraz.year and wybrany_miesiac == teraz.month:
            dni_do_analizy = teraz.day
        else:
            dni_do_analizy = dni_w_miesiacu_max

        st.info(f"Analiza punktualności do godziny {GODZINA_GRANICZNA}:00. Skala okresu: {dni_do_analizy} dni.")

        # Filtrowanie danych do WYBRANEGO okresu
        df_okres = df[(df['Data'].dt.month == wybrany_miesiac) & (df['Data'].dt.year == wybrany_rok)]

        stats_data = []
        for zawodnik in LISTA_ZAWODNIKOW:
            player_data = df_okres[df_okres['Zawodnik'] == zawodnik]
            
            # Wellness
            well_data = player_data[player_data['Typ_Raportu'] == 'Wellness']
            well_on_time = well_data[well_data['Godzina'] < GODZINA_GRANICZNA]['Dzien'].nunique()
            well_late = well_data[well_data['Godzina'] >= GODZINA_GRANICZNA]['Dzien'].nunique()
            
            # Wyliczanie braków: dni bez raportu + raporty spóźnione
            dni_bez_raportu = dni_do_analizy - (well_on_time + well_late)
            # Zabezpieczenie przed ujemnymi wartościami (np. gdy ktoś wysłał 2 raporty jednego dnia)
            dni_bez_raportu = max(0, dni_bez_raportu)
            
            laczone_braki = dni_bez_raportu + well_late
            
            # RPE
            rpe_data = player_data[player_data['Typ_Raportu'] == 'RPE']
            rpe_count = int(rpe_data['Dzien'].nunique())
            if not rpe_data.empty:
                rpe_data['RPE'] = pd.to_numeric(rpe_data['RPE'], errors='coerce')
            rpe_avg = rpe_data['RPE'].mean()

            stats_data.append({
                "Zawodnik": zawodnik,
                "O czasie": well_on_time,
                "Spóźnione": well_late,
                "Bez raportu": dni_bez_raportu,
                "SUMA BRAKÓW": laczone_braki,
                "RPE (%)": f"{rpe_count} / {dni_do_analizy}",
                "Śr. RPE": round(rpe_avg, 2) if not pd.isna(rpe_avg) else 0.0,
                "braki_sort": laczone_braki
            })

        df_final = pd.DataFrame(stats_data)

        # PRZYCISK POBIERANIA EXCELA W PASKU BOCZNYM
        with st.sidebar:
            st.write("---")
            st.subheader("📥 Eksportuj dane")
            # Przygotowanie pliku
            excel_data = to_excel(df_final.drop(columns=['braki_sort']), df_okres)
            st.download_button(
                label="📁 Pobierz raport Excel",
                data=excel_data,
                file_name=f"Raport_Warta_{wybrany_miesiac_nazwa}_{wybrany_rok}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Sekcja Wellness
        st.subheader(f"📋 Dyscyplina Poranna (Wellness) - {wybrany_miesiac_nazwa}")
        well_disp = df_final[['Zawodnik', 'O czasie', 'Spóźnione', 'Bez raportu', 'SUMA BRAKÓW', 'braki_sort']].sort_values(by="braki_sort", ascending=False)
        
        st.dataframe(
            well_disp[['Zawodnik', 'O czasie', 'Spóźnione', 'Bez raportu', 'SUMA BRAKÓW']].style.background_gradient(
                subset=['SUMA BRAKÓW'], cmap="Reds"
            ).background_gradient(
                subset=['O czasie'], cmap="Greens", vmin=0, vmax=dni_do_analizy
            ), 
            use_container_width=True, 
            hide_index=True
        )

        st.write("---")

        # Sekcja RPE
        st.subheader(f"🏃 Treningi (RPE) - {wybrany_miesiac_nazwa}")
        rpe_disp = df_final[['Zawodnik', 'RPE (%)', 'Śr. RPE']].sort_values(by="Śr. RPE", ascending=False)
        st.dataframe(
            rpe_disp.style.background_gradient(
                subset=['Śr. RPE'], cmap="YlOrRd", vmin=0, vmax=10
            ), 
            use_container_width=True, 
            hide_index=True
        )

        with st.expander("🔍 Podgląd wszystkich wpisów (Wybrany miesiąc)"):
            st.dataframe(df_okres.sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Błąd podczas przetwarzania danych: {e}")
