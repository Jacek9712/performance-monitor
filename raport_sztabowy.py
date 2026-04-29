import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import calendar

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"
COLOR_SECONDARY = "#004d26"
COLOR_WARNING = "#D32F2F" # Czerwony dla alarmów
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "Warta!"
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

st.set_page_config(
    page_title="Warta Poznań - PANEL TRENERA",
    page_icon="📋",
    layout="wide"
)

# Stylizacja CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    .stApp {{ background-color: #F8F9FA !important; }}
    h1, h2, h3, p, span, label {{ font-family: 'Anton', sans-serif !important; color: {COLOR_SECONDARY}; }}
    .stDataFrame {{ background-color: white; border-radius: 10px; }}
    .metric-card {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid {COLOR_PRIMARY};
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .alert-box {{
        background-color: #FFEBEE;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid {COLOR_WARNING};
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

# System logowania
if "auth_staff" not in st.session_state:
    st.session_state["auth_staff"] = False

def check_password():
    if not st.session_state["auth_staff"]:
        st.markdown("<h1>🔐 LOGOWANIE SZTABU</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            pwd = st.text_input("Hasło sztabowe:", type="password")
            if st.button("Zaloguj"):
                if pwd == PASSWORD_TRENER:
                    st.session_state["auth_staff"] = True
                    st.rerun()
                else:
                    st.error("Błędne hasło!")
        return False
    return True

if not check_password():
    st.stop()

# Połączenie z bazą
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        if df is not None and not df.empty:
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Błąd ładowania danych: {e}")
        return pd.DataFrame()

# --- INTERFEJS ---
st.title("📋 PANEL ANALIZY SZTABOWEJ")
st.subheader("Warta Poznań Performance")

df_raw = load_data()

if df_raw.empty:
    st.warning("Brak danych w bazie lub aplikacja jest w trakcie wybudzania...")
    if st.button("Odśwież bazę"):
        st.cache_data.clear()
        st.rerun()
else:
    # --- FILTRY ---
    st.sidebar.header("FILTRY ANALIZY")
    
    # Wybór zakresu dat
    today = datetime.now(PL_TZ).date()
    date_range = st.sidebar.date_input(
        "Zakres dat:",
        value=(today - timedelta(days=7), today)
    )
    
    # Filtr zawodnika
    all_players = ["Wszyscy"] + sorted(df_raw['Zawodnik'].unique().tolist())
    selected_player = st.sidebar.selectbox("Zawodnik:", all_players)
    
    if st.sidebar.button("Wyloguj"):
        st.session_state["auth_staff"] = False
        st.rerun()

    # Filtrowanie danych
    mask = (df_raw['Data'].dt.date >= date_range[0]) & (df_raw['Data'].dt.date <= date_range[1])
    if selected_player != "Wszyscy":
        mask &= (df_raw['Zawodnik'] == selected_player)
    
    df = df_raw.loc[mask].copy()

    # --- KPI / STATYSTYKI ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card">RAZEM WPISÓW<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    with col2:
        well_count = len(df[df['Typ_Raportu'] == 'Wellness'])
        st.markdown(f'<div class="metric-card">WELLNESS<br><h2>{well_count}</h2></div>', unsafe_allow_html=True)
    with col3:
        rpe_avg = df['RPE'].mean() if not df['RPE'].dropna().empty else 0
        st.markdown(f'<div class="metric-card">ŚREDNIE RPE<br><h2>{rpe_avg:.2f}</h2></div>', unsafe_allow_html=True)
    with col4:
        alarms_count = len(df[(df['Sen'] <= 2) | (df['Bolesnosc'] <= 2)])
        st.markdown(f'<div class="metric-card">ALERTY (DO KONTROLI)<br><h2 style="color:{COLOR_WARNING}">{alarms_count}</h2></div>', unsafe_allow_html=True)

    # --- SEKCOJA ALERTÓW BOLESNOŚCI ---
    st.write("---")
    bolesnosc_alert = df[(df['Typ_Raportu'] == 'Wellness') & (df['Bolesnosc'].isin([1, 2]))].copy()
    
    if not bolesnosc_alert.empty:
        st.error("🚨 ALERT BOLESNOŚCI (Wymagana konsultacja fizjoterapeutyczna)")
        for _, row in bolesnosc_alert.sort_values('Data', ascending=False).iterrows():
            st.markdown(f"""
                <div class="alert-box">
                    <b style="color:{COLOR_WARNING}">{row['Zawodnik']}</b> | Data: {row['Data'].strftime('%Y-%m-%d %H:%M')} | 
                    <b>Bolesność: {row['Bolesnosc']:.0f}/5</b><br>
                    <i>Komentarz: {row['Komentarz'] if row['Komentarz'] else 'Brak uwag'}</i>
                </div>
            """, unsafe_allow_html=True)

    # --- WYKRESY ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trendy", "📊 Wellness Detale", "🟢 Gotowość Drużyny", "📝 Komentarze"])
    
    with tab1:
        st.subheader("Trend RPE w czasie")
        if not df[df['Typ_Raportu'] == 'RPE'].empty:
            fig_rpe = px.line(
                df[df['Typ_Raportu'] == 'RPE'], 
                x='Data', y='RPE', color='Zawodnik',
                title="Obciążenie treningowe (RPE)",
                color_discrete_sequence=px.colors.qualitative.Dark2
            )
            st.plotly_chart(fig_rpe, use_container_width=True)
        else:
            st.info("Brak danych RPE dla wybranego zakresu.")

    with tab2:
        st.subheader("Składowe Wellness")
        well_df = df[df['Typ_Raportu'] == 'Wellness'].dropna(subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'])
        if not well_df.empty:
            well_melted = well_df.melt(
                id_vars=['Data', 'Zawodnik'], 
                value_vars=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'],
                var_name='Parametr', value_name='Ocena'
            )
            fig_well = px.bar(
                well_melted, x='Parametr', y='Ocena', color='Parametr',
                barmode='group', title="Średnie oceny parametrów",
                color_discrete_map={'Sen': '#1f77b4', 'Zmeczenie': '#ff7f0e', 'Bolesnosc': '#d62728', 'Stres': '#9467bd'}
            )
            st.plotly_chart(fig_well, use_container_width=True)
        else:
            st.info("Brak kompletnych danych Wellness.")

    with tab3:
        st.subheader("Wskaźnik Gotowości (Readiness Score)")
        df_well = df[df['Typ_Raportu'] == 'Wellness'].copy()
        if not df_well.empty:
            for col in ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']:
                df_well[col] = pd.to_numeric(df_well[col], errors='coerce')
            
            df_well = df_well.dropna(subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'])
            df_well['Readiness'] = df_well[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
            
            latest_readiness = df_well.sort_values('Data').groupby('Zawodnik').last().reset_index()
            avg_readiness = latest_readiness['Readiness'].mean()
            
            fig_read = px.bar(
                latest_readiness, 
                x='Zawodnik', 
                y='Readiness', 
                color='Readiness',
                color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'],
                range_y=[0, 20],
                title=f"Ostatnia Gotowość Zawodników"
            )
            
            fig_read.add_hline(
                y=avg_readiness, 
                line_dash="dash", 
                line_color="black", 
                annotation_text=f"ŚREDNIA DRUŻYNY: {avg_readiness:.2f}", 
                annotation_position="top right"
            )
            
            st.plotly_chart(fig_read, use_container_width=True)
        else:
            st.info("Brak danych Wellness do obliczenia gotowości.")

    with tab4:
        st.subheader("Ostatnie komentarze zawodników")
        comments = df[df['Komentarz'].notna()][['Data', 'Zawodnik', 'Typ_Raportu', 'Komentarz']].sort_values(by='Data', ascending=False)
        if not comments.empty:
            st.table(comments)
        else:
            st.write("Brak uwag od zawodników.")

    # --- TABELA DANYCH ---
    st.write("---")
    st.subheader("Pełny zbiór danych")
    st.dataframe(df.sort_values(by='Data', ascending=False), use_container_width=True)

    # Export do CSV
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "Pobierz dane jako CSV (Excel)",
        csv,
        "raport_warta_poznan.csv",
        "text/csv",
        key='download-csv'
    )
