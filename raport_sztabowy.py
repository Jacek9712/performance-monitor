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
    # Wybór widoku
    widok = st.radio("Wybierz widok:", ["Wykresy Drużynowe (Dzień)", "Dyscyplina (Miesiąc)", "Alert Bolesności"])
    
    st.write("---")
    teraz = datetime.now(PL_TZ)
    
    # Filtry zależne od widoku
    if widok == "Wykresy Drużynowe (Dzień)":
        data_wykres = st.date_input("Wybierz dzień do analizy:", value=teraz.date())
    else:
        st.subheader("🗓️ Wybierz Miesiąc")
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
        # Konwersja dat
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.dropna(subset=['Data'])
        df['Dzień'] = df['Data'].dt.date
        df['Miesiac_Nr'] = df['Data'].dt.month
        df['Rok_Nr'] = df['Data'].dt.year
        df['Godzina_H'] = df['Data'].dt.hour

        if widok == "Wykresy Drużynowe (Dzień)":
            st.title(f"📈 Wykres Gotowości: {data_wykres}")
            
            # Filtrowanie pod wybrany dzień (tylko Wellness)
            df_day = df[(df['Dzień'] == data_wykres) & (df['Typ_Raportu'] == 'Wellness')].copy()
            
            if df_day.empty:
                st.warning(f"Brak raportów Wellness dla dnia {data_wykres}. Wybierz inną datę w panelu bocznym.")
            else:
                # Obliczanie wskaźnika Readiness
                df_day['Readiness'] = df_day[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
                
                # Tworzenie wykresu słupkowego
                fig = px.bar(
                    df_day.sort_values('Readiness', ascending=True), 
                    x='Zawodnik', 
                    y='Readiness', 
                    color='Readiness',
                    color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'], # Od czerwonego do zielonego
                    range_y=[0, 20],
                    text='Readiness'
                )
                fig.update_traces(textposition='outside')
                fig.add_hline(y=12, line_dash="dash", line_color="gray", annotation_text="Próg uwagi (12 pkt)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela pod wykresem
                st.subheader("Szczegóły wpisów")
                st.dataframe(
                    df_day[['Zawodnik', 'Sen', 'Zmeczenie', 'Bolesnosc', 'Stres', 'Readiness', 'Komentarz']]
                    .sort_values('Readiness'),
                    hide_index=True, use_container_width=True
                )

        elif widok == "Dyscyplina (Miesiąc)":
            st.title(f"📊 Raport Dyscypliny: {wybrany_miesiac_nazwa} {wybrany_rok}")
            df_okres = df[(df['Miesiac_Nr'] == wybrany_miesiac) & (df['Rok_Nr'] == wybrany_rok)].copy()
            
            # Obliczanie dni do analizy
            dni_max = calendar.monthrange(wybrany_rok, wybrany_miesiac)[1]
            dni_analizy = teraz.day if (wybrany_rok == teraz.year and wybrany_miesiac == teraz.month) else dni_max

            stats_total = []
            for z in LISTA_ZAWODNIKOW:
                z_data = df_okres[df_okres['Zawodnik'] == z]
                
                # Wellness stats
                well = z_data[z_data['Typ_Raportu'] == 'Wellness']
                well_on_time = well[well['Godzina_H'] < GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_late = well[well['Godzina_H'] >= GODZINA_WELLNESS]['Data'].dt.date.nunique()
                well_missing = max(0, dni_analizy - well['Data'].dt.date.nunique())
                
                stats_total.append({
                    "Zawodnik": z,
                    "Wellness O czasie": well_on_time,
                    "Wellness Spóźnione": well_late,
                    "Wellness Braki": well_missing,
                    "SUMA KARNA": well_late + well_missing
                })
            
            df_dyscyplina = pd.DataFrame(stats_total).sort_values("SUMA KARNA", ascending=False)
            
            # Export do Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_dyscyplina.to_excel(writer, index=False, sheet_name='Dyscyplina')
            btn_container.download_button(label="📥 Pobierz XLSX", data=output.getvalue(), file_name=f"Warta_Dyscyplina_{wybrany_miesiac_nazwa}.xlsx")

            st.dataframe(df_dyscyplina.style.background_gradient(subset=['SUMA KARNA'], cmap="Reds"), use_container_width=True, hide_index=True)

        elif widok == "Alert Bolesności":
            st.title("🚩 Alert Bolesności (Wysoki Ból)")
            df_okres = df[(df['Miesiac_Nr'] == wybrany_miesiac) & (df['Rok_Nr'] == wybrany_rok)].copy()
            
            # Alert: Bolesność <= 2 (w skali 1-5, gdzie 1 to bardzo duży ból)
            df_alerts = df_okres[(df_okres['Typ_Raportu'] == 'Wellness') & (df_okres['Bolesnosc'] <= 2)].copy()
            
            if not df_alerts.empty:
                st.error(f"Zidentyfikowano {len(df_alerts)} raportów zgłaszających ból!")
                st.dataframe(df_alerts[['Data', 'Zawodnik', 'Bolesnosc', 'Komentarz']].sort_values('Data', ascending=False), use_container_width=True, hide_index=True)
            else:
                st.success("Brak alertów bolesności w wybranym miesiącu.")
            
            st.write("---")
            st.subheader("Średnia bolesność zawodników (Ranking)")
            avg_bolesnosc = df_okres[df_okres['Typ_Raportu'] == 'Wellness'].groupby('Zawodnik')['Bolesnosc'].mean().reset_index()
            st.dataframe(avg_bolesnosc.sort_values('Bolesnosc').style.background_gradient(subset=['Bolesnosc'], cmap="RdYlGn"), use_container_width=True, hide_index=True)

    else:
        st.info("Brak danych w bazie.")

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
