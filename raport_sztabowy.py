import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import calendar
import io
import plotly.express as px

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
    st.markdown(f"<h1 style='color: {COLOR_PRIMARY}; text-align: center;'>🔐 LOGOWANIE SZTABU</h1>", unsafe_allow_html=True)
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

# Słownik miesięcy
NAZWY_MIESIECY = {
    1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
    5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
    9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=80)
    st.subheader("⚙️ TRYB ANALIZY")
    widok = st.radio("Wybierz widok:", ["Dyscyplina (Miesiąc)", "Wykresy Drużynowe (Dzień)", "Alert Bolesności"])
    
    st.write("---")
    teraz = datetime.now(PL_TZ)
    
    if widok == "Wykresy Drużynowe (Dzień)":
        data_wykres = st.date_input("Wybierz dzień do analizy:", value=teraz.date())
    else:
        st.subheader("🗓️ Wybierz Okres")
        wybrany_rok = st.selectbox("Rok", [2024, 2025, 2026], index=1)
        wybrany_miesiac_nazwa = st.selectbox("Miesiąc", list(NAZWY_MIESIECY.values()), index=teraz.month-1)
        wybrany_miesiac = [k for k, v in NAZWY_MIESIECY.items() if v == wybrany_miesiac_nazwa][0]
    
    st.write("---")
    st.subheader("📥 EKSPORT")
    btn_container = st.empty()
    
    if st.button("Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Arkusz1", ttl="1s")
    
    if df is not None and not df.empty:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.dropna(subset=['Data'])
        df['Dzień'] = df['Data'].dt.date
        df['Miesiac_Nr'] = df['Data'].dt.month
        df['Rok_Nr'] = df['Data'].dt.year
        df['Godzina_H'] = df['Data'].dt.hour
        
        if widok == "Dyscyplina (Miesiąc)":
            st.title(f"📊 Raport Dyscypliny: {wybrany_miesiac_nazwa} {wybrany_rok}")
            df_okres = df[(df['Miesiac_Nr'] == wybrany_miesiac) & (df['Rok_Nr'] == wybrany_rok)].copy()
            
            dni_max = calendar.monthrange(wybrany_rok, wybrany_miesiac)[1]
            dni_analizy = teraz.day if (wybrany_rok == teraz.year and wybrany_miesiac == teraz.month) else dni_max

            stats_wellness = []
            stats_rpe = []
            
            for z in LISTA_ZAWODNIKOW:
                p_data = df_okres[df_okres['Zawodnik'] == z]
                
                well = p_data[p_data['Typ_Raportu'] == 'Wellness']
                well_on_time = well[well['Godzina_H'] < GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_late = well[well['Godzina_H'] >= GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_braki = max(0, dni_analizy - well['Data'].dt.date.nunique())
                stats_wellness.append({"Zawodnik": z, "O czasie": well_on_time, "Spóźnione": well_late, "Brak raportu": well_braki, "SUMA BRAKÓW": well_braki + well_late})
                
                rpe_data = p_data[p_data['Typ_Raportu'] == 'RPE']
                rpe_on_time = rpe_data[rpe_data['Godzina_H'] < GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_late = rpe_data[rpe_data['Godzina_H'] >= GODZINA_RPE]['Data'].dt.date.nunique()
                rpe_braki = max(0, dni_analizy - rpe_data['Data'].dt.date.nunique())
                stats_rpe.append({"Zawodnik": z, "O czasie": rpe_on_time, "Spóźnione": rpe_late, "Brak raportu": rpe_braki, "SUMA BRAKÓW": rpe_braki + rpe_late})
            
            df_well_final = pd.DataFrame(stats_wellness).sort_values("SUMA BRAKÓW", ascending=False)
            df_rpe_final = pd.DataFrame(stats_rpe).sort_values("SUMA BRAKÓW", ascending=False)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_well_final.to_excel(writer, index=False, sheet_name='Wellness')
                df_rpe_final.to_excel(writer, index=False, sheet_name='RPE')
            btn_container.download_button(label="📥 Ściągnij raport .xlsx", data=output.getvalue(), file_name=f"Warta_Dyscyplina_{wybrany_miesiac_nazwa}.xlsx")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"📋 Wellness (do {GODZINA_WELLNESS}:00)")
                st.dataframe(df_well_final.style.background_gradient(subset=['SUMA BRAKÓW'], cmap="Reds"), use_container_width=True, hide_index=True)
            with col2:
                st.subheader(f"🏃 RPE (do {GODZINA_RPE}:00)")
                st.dataframe(df_rpe_final.style.background_gradient(subset=['SUMA BRAKÓW'], cmap="Reds"), use_container_width=True, hide_index=True)

        elif widok == "Wykresy Drużynowe (Dzień)":
            st.title(f"📈 Analiza Gotowości: {data_wykres}")
            df_day = df[(df['Dzień'] == data_wykres) & (df['Typ_Raportu'] == 'Wellness')].copy()
            
            if df_day.empty:
                st.warning(f"Brak danych Wellness dla dnia {data_wykres}.")
            else:
                df_day['Readiness'] = df_day[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                
                fig = px.bar(
                    df_day.sort_values('Readiness'), 
                    x='Zawodnik', y='Readiness', color='Readiness',
                    color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'],
                    range_y=[0, 20],
                    title="Skumulowany Readiness Score (Suma 4 parametrów)"
                )
                fig.add_hline(y=12, line_dash="dash", line_color="red", annotation_text="Alert")
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Szczegóły wpisów")
                st.dataframe(df_day[['Zawodnik', 'Sen', 'Zmeczenie', 'Bolesnosc', 'Stres', 'Readiness', 'Komentarz']].sort_values('Readiness'), hide_index=True, use_container_width=True)

        elif widok == "Alert Bolesności":
            st.title("🚩 Monitoring Bolesności (1-2 pkt)")
            # Tutaj filtrujemy cały wybrany miesiąc w poszukiwaniu "czerwonych" wpisów
            df_okres = df[(df['Miesiac_Nr'] == wybrany_miesiac) & (df['Rok_Nr'] == wybrany_rok)].copy()
            df_alerts = df_okres[(df_okres['Typ_Raportu'] == 'Wellness') & (df_okres['Bolesnosc'] <= 2)].copy()
            
            if not df_alerts.empty:
                st.error(f"Znaleziono {len(df_alerts)} zgłoszeń bólowych w wybranym okresie!")
                st.dataframe(df_alerts[['Data', 'Zawodnik', 'Bolesnosc', 'Komentarz']].sort_values('Data', ascending=False), use_container_width=True, hide_index=True)
                
                st.write("---")
                st.subheader("📉 Średnia Gotowość (Ranking Miesięczny)")
                df_okres['Readiness'] = df_okres[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                avg_r = df_okres[df_okres['Typ_Raportu'] == 'Wellness'].groupby('Zawodnik')['Readiness'].mean().reset_index()
                st.dataframe(avg_r.sort_values('Readiness').style.background_gradient(subset=['Readiness'], cmap="RdYlGn"), use_container_width=True, hide_index=True)
            else:
                st.success("Brak alertów bolesności w tym miesiącu.")

    else:
        st.info("Baza danych jest pusta.")

except Exception as e:
    st.error(f"Błąd: {e}")
