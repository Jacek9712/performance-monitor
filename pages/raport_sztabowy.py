import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"
PL_TZ = pytz.timezone('Europe/Warsaw')

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

st.set_page_config(page_title="Warta Poznań - Analiza Sztabu", layout="wide")

st.markdown(f"""
    <style>
    .main {{ background-color: #f0f2f6; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; text-align: center; text-transform: uppercase; }}
    .stMetric {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    div[data-testid="stDataFrame"] {{ background-color: white; border-radius: 10px; padding: 10px; }}
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Monitorowanie Miesięczne Sztabu")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Pobieranie danych
    df = conn.read(worksheet="Arkusz1", ttl="1s")
    
    if df.empty:
        st.warning("Brak danych w arkuszu.")
    else:
        # Przygotowanie danych
        df['Data'] = pd.to_datetime(df['Data'])
        df['Dzien'] = df['Data'].dt.date
        
        teraz = datetime.now(PL_TZ)
        biezacy_miesiac = teraz.month
        biezacy_rok = teraz.year
        
        # Liczba dni w całym bieżącym miesiącu
        dni_w_miesiacu = calendar.monthrange(biezacy_rok, biezacy_miesiac)[1]
        nazwa_miesiaca = teraz.strftime('%B %Y')

        st.header(f"📈 Podsumowanie: {nazwa_miesiaca}")
        st.info(f"Statystyki liczone względem pełnego miesiąca ({dni_w_miesiacu} dni).")

        # Filtrowanie tylko bieżącego miesiąca
        df_miesiac = df[(df['Data'].dt.month == biezacy_miesiac) & (df['Data'].dt.year == biezacy_rok)]

        # --- OBLICZENIA FREKWENCJI ---
        stats_data = []

        for zawodnik in LISTA_ZAWODNIKOW:
            player_data = df_miesiac[df_miesiac['Zawodnik'] == zawodnik]
            
            # Wellness: liczba unikalnych dni
            well_data = player_data[player_data['Typ_Raportu'] == 'Wellness']
            well_count = well_data['Dzien'].nunique()
            well_avg = well_data[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].mean().mean() # Ogólna średnia wellness
            
            # RPE: liczba unikalnych dni
            rpe_data = player_data[player_data['Typ_Raportu'] == 'RPE']
            rpe_count = rpe_data['Dzien'].nunique()
            rpe_avg = rpe_data['RPE'].mean()

            stats_data.append({
                "Zawodnik": zawodnik,
                "Wellness (Suma)": well_count,
                "Wellness (%)": f"{well_count}/{dni_w_miesiacu}",
                "Śr. Wellness": round(well_avg, 2) if not pd.isna(well_avg) else 0,
                "RPE (Suma)": rpe_count,
                "RPE (%)": f"{rpe_count}/{dni_w_miesiacu}",
                "Śr. RPE": round(rpe_avg, 2) if not pd.isna(rpe_avg) else 0
            })

        df_final = pd.DataFrame(stats_data)

        # --- WYŚWIETLANIE TABELI ---
        
        # Tabela 1: Frekwencja Wellness
        st.subheader("📋 Poranna Kontrola (Wellness)")
        well_table = df_final[['Zawodnik', 'Wellness (%)', 'Śr. Wellness']].sort_values(by="Wellness (Suma)", ascending=True)
        st.dataframe(
            well_table.style.background_gradient(subset=['Śr. Wellness'], cmap="RdYlGn"),
            use_container_width=True,
            hide_index=True
        )

        st.write("<br>", unsafe_allow_html=True)

        # Tabela 2: Frekwencja RPE
        st.subheader("🏃 Kontrola Po Treningu (RPE)")
        rpe_table = df_final[['Zawodnik', 'RPE (%)', 'Śr. RPE']].sort_values(by="RPE (Suma)", ascending=True)
        st.dataframe(
            rpe_table.style.background_gradient(subset=['Śr. RPE'], cmap="YlOrRd"),
            use_container_width=True,
            hide_index=True
        )

        # --- SEKCJA SZCZEGÓŁOWA ---
        with st.expander("🔍 ZOBACZ SZCZEGÓŁOWE DANE MIESIĘCZNE"):
            st.dataframe(df_miesiac.sort_values(by="Data", ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Wystąpił błąd podczas analizy danych: {e}")
