import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar
import io

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"
COLOR_TEXT = "#1a1a1a"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_SZTAB = "WartaSztab2024"
GODZINA_WELLNESS = 10 
GODZINA_RPE = 17

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

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]:
        return True
    st.markdown(f"<h1 style='color: {COLOR_PRIMARY};'>🔐 LOGOWANIE</h1>", unsafe_allow_html=True)
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

# Słownik miesięcy
NAZWY_MIESIECY = {
    1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
    5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
    9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=80)
    st.subheader("🗓️ Wybierz Okres")
    teraz = datetime.now(PL_TZ)
    wybrany_rok = st.selectbox("Rok", [2024, 2025, 2026], index=1)
    wybrany_miesiac_nazwa = st.selectbox("Miesiąc", list(NAZWY_MIESIECY.values()), index=teraz.month-1)
    wybrany_miesiac = [k for k, v in NAZWY_MIESIECY.items() if v == wybrany_miesiac_nazwa][0]
    
    st.write("---")
    st.subheader("📥 Eksport do Excela")
    btn_container = st.empty()

st.title(f"📊 Raport: {wybrany_miesiac_nazwa} {wybrany_rok}")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Arkusz1", ttl="1s")
    
    if df is not None and not df.empty:
        # Konwersja i czyszczenie dat
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.dropna(subset=['Data'])
        
        df['Miesiac_Nr'] = df['Data'].dt.month
        df['Rok_Nr'] = df['Data'].dt.year
        df['Godzina_H'] = df['Data'].dt.hour
        
        # Filtrowanie pod wybrany okres
        df_okres = df[(df['Miesiac_Nr'] == wybrany_miesiac) & (df['Rok_Nr'] == wybrany_rok)].copy()
        
        # Skala czasu
        dni_max = calendar.monthrange(wybrany_rok, wybrany_miesiac)[1]
        if wybrany_rok == teraz.year and wybrany_miesiac == teraz.month:
            dni_analizy = teraz.day
        else:
            dni_analizy = dni_max

        stats_wellness = []
        stats_rpe = []
        
        for z in LISTA_ZAWODNIKOW:
            p_data = df_okres[df_okres['Zawodnik'] == z]
            
            # --- LOGIKA WELLNESS (Limit 10:00) ---
            well = p_data[p_data['Typ_Raportu'] == 'Wellness']
            well_on_time = well[well['Godzina_H'] < GODZINA_WELLNESS]['Data'].dt.date.nunique()
            well_late = well[well['Godzina_H'] >= GODZINA_WELLNESS]['Data'].dt.date.nunique()
            well_dni_raport = well['Data'].dt.date.nunique()
            well_braki = max(0, dni_analizy - well_dni_raport)
            
            stats_wellness.append({
                "Zawodnik": z,
                "O czasie": well_on_time,
                "Spóźnione": well_late,
                "Brak raportu": well_braki,
                "SUMA BRAKÓW": well_braki + well_late
            })
            
            # --- LOGIKA RPE (Limit 17:00) ---
            rpe_data = p_data[p_data['Typ_Raportu'] == 'RPE']
            rpe_on_time = rpe_data[rpe_data['Godzina_H'] < GODZINA_RPE]['Data'].dt.date.nunique()
            rpe_late = rpe_data[rpe_data['Godzina_H'] >= GODZINA_RPE]['Data'].dt.date.nunique()
            rpe_dni_raport = rpe_data['Data'].dt.date.nunique()
            rpe_braki = max(0, dni_analizy - rpe_dni_raport)
            
            stats_rpe.append({
                "Zawodnik": z,
                "O czasie": rpe_on_time,
                "Spóźnione": rpe_late,
                "Brak raportu": rpe_braki,
                "SUMA BRAKÓW": rpe_braki + rpe_late
            })
            
        df_well_final = pd.DataFrame(stats_wellness).sort_values("SUMA BRAKÓW", ascending=False)
        df_rpe_final = pd.DataFrame(stats_rpe).sort_values("SUMA BRAKÓW", ascending=False)

        # PRZYGOTOWANIE PLIKU EXCEL (.xlsx)
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_well_final.to_excel(writer, index=False, sheet_name='Wellness_Dyscyplina')
                df_rpe_final.to_excel(writer, index=False, sheet_name='RPE_Dyscyplina')
            processed_data = output.getvalue()
            
            btn_container.download_button(
                label="📥 Ściągnij plik .xlsx",
                data=processed_data,
                file_name=f"Raport_Warta_{wybrany_miesiac_nazwa}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            csv_data = df_well_final.to_csv(index=False).encode('utf-8-sig')
            btn_container.download_button(label="📥 Ściągnij .csv", data=csv_data, file_name="raport.csv")

        # --- WYŚWIETLANIE TABEL ---
        st.subheader(f"📋 Dyscyplina Poranna (Wellness) - do {GODZINA_WELLNESS}:00")
        st.dataframe(
            df_well_final.style.background_gradient(subset=['SUMA BRAKÓW'], cmap="Reds"),
            use_container_width=True, hide_index=True
        )
        
        st.write("---")
        
        st.subheader(f"🏃 Dyscyplina Raportowania (RPE) - do {GODZINA_RPE}:00")
        st.dataframe(
            df_rpe_final.style.background_gradient(subset=['SUMA BRAKÓW'], cmap="Reds"),
            use_container_width=True, hide_index=True
        )
        
    else:
        st.info("Brak danych do wyświetlenia dla wybranego okresu.")

except Exception as e:
    st.error(f"Wystąpił błąd danych: {e}")
