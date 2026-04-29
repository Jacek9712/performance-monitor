import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"   # Zielony Warty
COLOR_SECONDARY = "#004d26" # Ciemny zielony
COLOR_WARNING = "#D32F2F"   # Czerwony alert
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024"
GODZINA_GRANICZNA = 10  # Raporty po 10:00 są uznawane za spóźnione

st.set_page_config(
    page_title="Warta Poznań - PANEL TRENERA",
    page_icon="📋",
    layout="wide"
)

# --- STYLIZACJA UI ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    .stApp {{ background-color: #F8F9FA !important; }}
    h1, h2, h3, p, span, label {{ font-family: 'Anton', sans-serif !important; color: {COLOR_SECONDARY}; }}
    .stDataFrame {{ background-color: white; border-radius: 10px; }}
    .metric-card {{
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid {COLOR_PRIMARY};
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .alert-box {{
        background-color: #FFEBEE;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid {COLOR_WARNING};
        margin-bottom: 15px;
        border: 1px solid #FFCDD2;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
    }}
    .stTabs [aria-selected="true"] {{ background-color: {COLOR_PRIMARY} !important; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- SYSTEM LOGOWANIA ---
if "auth_staff" not in st.session_state:
    st.session_state["auth_staff"] = False

def check_auth():
    if not st.session_state["auth_staff"]:
        st.markdown("<h1 style='text-align:center;'>🔐 PANEL SZTABOWY - LOGOWANIE</h1>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col:
            pwd = st.text_input("Hasło dostępu:", type="password")
            if st.button("Zaloguj do bazy", use_container_width=True):
                if pwd == PASSWORD_TRENER:
                    st.session_state["auth_staff"] = True
                    st.rerun()
                else:
                    st.error("Nieprawidłowe hasło!")
        return False
    return True

if not check_auth():
    st.stop()

# --- POŁĄCZENIE I DANE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = conn.read(worksheet="Arkusz1", ttl=0)
        if df is not None and not df.empty:
            df['Data'] = pd.to_datetime(df['Data'])
            # Konwersja na liczby dla poprawnego formatowania i wykresów
            numeric_cols = ['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres', 'RPE']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Błąd połączenia z bazą danych: {e}")
        return pd.DataFrame()

# --- GŁÓWNY INTERFEJS ---
st.title("📋 SYSTEM MONITORINGU I ANALIZY")
st.markdown("### Warta Poznań - Sztab Szkoleniowy")

df_raw = load_data()

if df_raw.empty:
    st.warning("Oczekiwanie na dane z serwera... (Aplikacja może się wybudzać)")
    if st.button("🔄 Odśwież połączenie"):
        st.cache_data.clear()
        st.rerun()
else:
    # --- BOCZNY PANEL (FILTRY) ---
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Warta_Pozna%C5%84_logo.svg/1200px-Warta_Pozna%C5%84_logo.svg.png", width=100)
    st.sidebar.header("Ustawienia Analizy")
    
    today = datetime.now(PL_TZ).date()
    start_default = today - timedelta(days=7)
    date_range = st.sidebar.date_input("Zakres dat:", value=(start_default, today))
    
    # Obsługa pojedynczej daty
    if isinstance(date_range, tuple) and len(date_range) == 2:
        date_start, date_end = date_range
    else:
        date_start = date_end = date_range

    all_players = ["Wszyscy"] + sorted(df_raw['Zawodnik'].unique().tolist())
    selected_player = st.sidebar.selectbox("Filtruj zawodnika:", all_players)
    
    if st.sidebar.button("🔓 Wyloguj"):
        st.session_state["auth_staff"] = False
        st.rerun()

    # Filtrowanie danych bazowych
    mask = (df_raw['Data'].dt.date >= date_start) & (df_raw['Data'].dt.date <= date_end)
    if selected_player != "Wszyscy":
        mask &= (df_raw['Zawodnik'] == selected_player)
    
    df = df_raw.loc[mask].copy()

    # --- KPI STATYSTYKI ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f'<div class="metric-card">RAZEM RAPORTÓW<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    with kpi2:
        wellness_count = len(df[df['Typ_Raportu'] == 'Wellness'])
        st.markdown(f'<div class="metric-card">WPISY WELLNESS<br><h2>{wellness_count}</h2></div>', unsafe_allow_html=True)
    with kpi3:
        avg_rpe = df['RPE'].mean() if not df['RPE'].dropna().empty else 0
        st.markdown(f'<div class="metric-card">ŚREDNIE RPE<br><h2>{avg_rpe:.2f}</h2></div>', unsafe_allow_html=True)
    with kpi4:
        # Alert: Sen <= 2 lub Bolesność <= 2 (w skali 1-5, gdzie 1-2 to negatywne)
        alerts = df[(df['Sen'] <= 2) | (df['Bolesnosc'] <= 2)]
        st.markdown(f'<div class="metric-card">ALERTY KRYTYCZNE<br><h2 style="color:{COLOR_WARNING}">{len(alerts)}</h2></div>', unsafe_allow_html=True)

    # --- ALERTY BOLESNOŚCI (Sekcja natychmiastowa) ---
    st.write("---")
    critical_pain = df[(df['Typ_Raportu'] == 'Wellness') & (df['Bolesnosc'] <= 2)].copy()
    
    if not critical_pain.empty:
        st.error("🚨 ZIDENTYFIKOWANO ZGŁOSZENIA BÓLOWE")
        for _, row in critical_pain.sort_values('Data', ascending=False).iterrows():
            st.markdown(f"""
                <div class="alert-box">
                    <span style="font-size:1.2rem; color:{COLOR_WARNING}; font-weight:bold;">{row['Zawodnik']}</span> 
                    | Bolesność: <b>{row['Bolesnosc']:.0f}/5</b> 
                    | Data: {row['Data'].strftime('%d.%m %H:%M')}<br>
                    <span style="color:#555;">Komentarz: {row['Komentarz'] if row['Komentarz'] and str(row['Komentarz']) != 'nan' else 'Brak uwag'}</span>
                </div>
            """, unsafe_allow_html=True)

    # --- ZAKŁADKI ANALITYCZNE ---
    tab_mon, tab_freq, tab_ready, tab_comm = st.tabs([
        "📈 Monitoring i Tabela", 
        "⏱️ Frekwencja i Spóźnienia", 
        "🟢 Gotowość Drużyny", 
        "📝 Komentarze"
    ])
    
    with tab_mon:
        st.subheader("Tabela monitoringu wellness")
        df_well = df[df['Typ_Raportu'] == 'Wellness'].copy()
        if not df_well.empty:
            df_well_display = df_well.sort_values('Data', ascending=False).head(30)[
                ['Data', 'Zawodnik', 'Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']
            ]
            
            # Funkcja kolorowania komórek
            def style_wellness(val):
                if pd.isna(val): return ''
                if val <= 2: color = '#FFCDD2' # Czerwony (źle)
                elif val >= 4: color = '#C8E6C9' # Zielony (dobrze)
                else: color = '#FFF9C4' # Żółty (neutralnie)
                return f'background-color: {color}; color: black;'
            
            st.dataframe(
                df_well_display.style.applymap(style_wellness, subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']),
                use_container_width=True,
                height=450
            )
        else:
            st.info("Brak raportów wellness w wybranym zakresie.")

    with tab_freq:
        st.subheader("Analiza dyscypliny raportowania")
        
        # Obliczenia dla frekwencji
        df_freq = df_raw.copy()
        df_freq['Godzina'] = df_freq['Data'].dt.hour
        df_freq['Data_Dnia'] = df_freq['Data'].dt.date
        
        # Filtrujemy tylko wellness z wybranego okresu
        mask_freq = (df_freq['Typ_Raportu'] == 'Wellness') & \
                    (df_freq['Data_Dnia'] >= date_start) & \
                    (df_freq['Data_Dnia'] <= date_end)
        curr_freq = df_freq.loc[mask_freq]
        
        delta_days = (date_end - date_start).days + 1
        players = sorted(df_raw['Zawodnik'].unique().tolist())
        
        freq_stats = []
        for p in players:
            p_data = curr_freq[curr_freq['Zawodnik'] == p]
            na_czas = len(p_data[p_data['Godzina'] < GODZINA_GRANICZNA])
            spoznione = len(p_data[p_data['Godzina'] >= GODZINA_GRANICZNA])
            braki = max(0, delta_days - len(p_data['Data_Dnia'].unique()))
            
            freq_stats.append({
                "Zawodnik": p,
                "Na czas (<10:00)": na_czas,
                "Spóźnione": spoznione,
                "Brak raportu": braki,
                "Dyscyplina %": round((na_czas / delta_days) * 100, 1) if delta_days > 0 else 0
            })
            
        df_stats = pd.DataFrame(freq_stats).sort_values("Brak raportu", ascending=False)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
        st.caption(f"Raport generowany dla okresu {delta_days} dni.")

    with tab_ready:
        st.subheader("Wskaźnik Gotowości (Readiness Score)")
        # Readiness = suma 4 parametrów wellness (max 20)
        df_r = df[df['Typ_Raportu'] == 'Wellness'].copy().dropna(subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'])
        
        if not df_r.empty:
            df_r['Readiness'] = df_r[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
            
            # Bierzemy ostatni wynik każdego zawodnika
            latest_r = df_r.sort_values('Data').groupby('Zawodnik').last().reset_index()
            avg_team = latest_r['Readiness'].mean()
            
            fig_r = px.bar(
                latest_r, x='Zawodnik', y='Readiness', color='Readiness',
                color_continuous_scale=['#D32F2F', '#FBC02D', '#388E3C'],
                range_y=[0, 21],
                title="Aktualna Gotowość Drużyny (Suma 0-20)"
            )
            
            # Linia średniej
            fig_r.add_hline(
                y=avg_team, 
                line_dash="dash", 
                line_color="black", 
                annotation_text=f"ŚREDNIA: {avg_team:.2f}",
                annotation_position="top right"
            )
            
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info("Brak wystarczających danych do wyliczenia gotowości.")

    with tab_comm:
        st.subheader("Uwagi i komentarze zawodników")
        df_comm = df[df['Komentarz'].notna() & (df['Komentarz'] != "")].copy()
        if not df_comm.empty:
            st.table(df_comm.sort_values('Data', ascending=False)[['Data', 'Zawodnik', 'Typ_Raportu', 'Komentarz']])
        else:
            st.write("Brak uwag w wybranym okresie.")

    # --- EKSPORT DANYCH ---
    st.write("---")
    st.subheader("Archiwum i Eksport")
    with st.expander("Pokaż surowe dane"):
        st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
        
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Pobierz wyfiltrowane dane (Excel/CSV)",
        data=csv,
        file_name=f"Warta_Poznan_Raport_{date_start}_{date_end}.csv",
        mime="text/csv",
    )
