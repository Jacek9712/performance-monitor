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
COLOR_WARNING = "#D32F2F"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024"
GODZINA_GRANICZNA = 10  # Raporty po 10:00 są uznawane za spóźnione

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
            for col in ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres', 'RPE']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
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
    st.warning("Brak danych w bazie...")
    if st.button("Odśwież bazę"):
        st.cache_data.clear()
        st.rerun()
else:
    # --- FILTRY ---
    st.sidebar.header("FILTRY ANALIZY")
    today = datetime.now(PL_TZ).date()
    date_range = st.sidebar.date_input("Zakres dat:", value=(today - timedelta(days=7), today))
    
    all_players = ["Wszyscy"] + sorted(df_raw['Zawodnik'].unique().tolist())
    selected_player = st.sidebar.selectbox("Zawodnik:", all_players)
    
    if st.sidebar.button("Wyloguj"):
        st.session_state["auth_staff"] = False
        st.rerun()

    # Filtrowanie
    mask = (df_raw['Data'].dt.date >= date_range[0]) & (df_raw['Data'].dt.date <= date_range[1])
    if selected_player != "Wszyscy":
        mask &= (df_raw['Zawodnik'] == selected_player)
    
    df = df_raw.loc[mask].copy()

    # --- KPI ---
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
        st.markdown(f'<div class="metric-card">ALERTY (BÓL/SEN)<br><h2 style="color:{COLOR_WARNING}">{alarms_count}</h2></div>', unsafe_allow_html=True)

    # --- SEKCOJA ALERTÓW BOLESNOŚCI (Priorytetowa) ---
    st.write("---")
    bolesnosc_alert = df[(df['Typ_Raportu'] == 'Wellness') & (df['Bolesnosc'].isin([1, 2]))].copy()
    
    if not bolesnosc_alert.empty:
        st.error("🚨 ALERT BOLESNOŚCI (Wymagana konsultacja fizjoterapeutyczna)")
        for _, row in bolesnosc_alert.sort_values('Data', ascending=False).iterrows():
            st.markdown(f"""
                <div class="alert-box">
                    <b style="color:{COLOR_WARNING}">{row['Zawodnik']}</b> | {row['Data'].strftime('%d.%m %H:%M')} | 
                    <b>Bolesność: {row['Bolesnosc']:.0f}/5</b><br>
                    <i>Komentarz: {row['Komentarz'] if row['Komentarz'] else 'Brak uwag'}</i>
                </div>
            """, unsafe_allow_html=True)

    # --- ZAKŁADKI ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Monitoring i Gotowość", "⏱️ Raportowanie i Frekwencja", "📊 Wellness Detale", "📝 Komentarze"])
    
    with tab1:
        # Tabela z kolorowaniem (Conditional Formatting)
        st.subheader("Ostatnie wyniki zawodników")
        df_well_table = df[df['Typ_Raportu'] == 'Wellness'].copy()
        if not df_well_table.empty:
            df_display = df_well_table.sort_values('Data', ascending=False).head(20)[['Data', 'Zawodnik', 'Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']]
            
            def color_cells(val):
                if val <= 2: color = '#ffcccc'
                elif val >= 4: color = '#ccffcc'
                else: color = '#ffffcc'
                return f'background-color: {color}'
            
            st.dataframe(df_display.style.applymap(color_cells, subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']), use_container_width=True)

        st.write("---")
        # Wykres gotowości
        st.subheader("Wskaźnik Gotowości (Readiness Score)")
        df_well = df[df['Typ_Raportu'] == 'Wellness'].copy().dropna(subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'])
        if not df_well.empty:
            df_well['Readiness'] = df_well[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
            latest_readiness = df_well.sort_values('Data').groupby('Zawodnik').last().reset_index()
            avg_readiness = latest_readiness['Readiness'].mean()
            
            fig_read = px.bar(
                latest_readiness, x='Zawodnik', y='Readiness', color='Readiness',
                color_continuous_scale=['#FF4B4B', '#FFEB3B', '#4CAF50'], range_y=[0, 20],
                title="Gotowość (Suma Wellness 0-20)"
            )
            fig_read.add_hline(y=avg_readiness, line_dash="dash", line_color="black", 
                               annotation_text=f"ŚREDNIA DRUŻYNY: {avg_readiness:.2f}")
            st.plotly_chart(fig_read, use_container_width=True)

    with tab2:
        st.subheader("Dyscyplina i Frekwencja Raportowania")
        # Analiza punktualności
        df_freq = df[df['Typ_Raportu'] == 'Wellness'].copy()
        df_freq['Godzina'] = df_freq['Data'].dt.hour
        df_freq['Data_Dnia'] = df_freq['Data'].dt.date
        
        # Wyliczenie statystyk na zawodnika
        players_in_db = sorted(df_raw['Zawodnik'].unique().tolist())
        stats_list = []
        
        # Zakres dni w filtrze
        delta = date_range[1] - date_range[0]
        dni_w_zakresie = delta.days + 1

        for p in players_in_db:
            p_data = df_freq[df_freq['Zawodnik'] == p]
            raporty_o_czasie = len(p_data[p_data['Godzina'] < GODZINA_GRANICZNA])
            raporty_spoznione = len(p_data[p_data['Godzina'] >= GODZINA_GRANICZNA])
            braki = max(0, dni_w_zakresie - len(p_data['Data_Dnia'].unique()))
            
            stats_list.append({
                "Zawodnik": p,
                "Na czas (<10:00)": raporty_o_czasie,
                "Spóźnione": raporty_spoznione,
                "Brak raportu": braki,
                "Dyscyplina %": round((raporty_o_czasie / dni_w_zakresie) * 100, 1) if dni_w_zakresie > 0 else 0
            })
            
        df_stats = pd.DataFrame(stats_list).sort_values("Brak raportu", ascending=False)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
        
        st.info(f"Analiza dla okresu: {date_range[0]} do {date_range[1]} ({dni_w_zakresie} dni)")

    with tab3:
        well_df = df[df['Typ_Raportu'] == 'Wellness'].dropna(subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'])
        if not well_df.empty:
            well_melted = well_df.melt(id_vars=['Data', 'Zawodnik'], value_vars=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'], var_name='Parametr', value_name='Ocena')
            fig_well = px.bar(well_melted, x='Parametr', y='Ocena', color='Parametr', barmode='group', title="Średnie składowe Wellness")
            st.plotly_chart(fig_well, use_container_width=True)

    with tab4:
        comments = df[df['Komentarz'].notna() & (df['Komentarz'] != "")][['Data', 'Zawodnik', 'Typ_Raportu', 'Komentarz']].sort_values(by='Data', ascending=False)
        if not comments.empty:
            st.table(comments)
        else:
            st.write("Brak uwag w wybranym okresie.")

    st.write("---")
    st.subheader("Pełne dane (Surowe)")
    st.dataframe(df.sort_values(by='Data', ascending=False), use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("Pobierz CSV", csv, f"raport_warta_{today}.csv", "text/csv")
