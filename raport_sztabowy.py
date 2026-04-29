import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz

# --- KONFIGURACJA ---
COLOR_PRIMARY = "#006633"
COLOR_SECONDARY = "#004d26"
COLOR_WARNING = "#D32F2F"
PL_TZ = pytz.timezone('Europe/Warsaw')
PASSWORD_TRENER = "WartaSztab2024"
GODZINA_GRANICZNA = 10 

st.set_page_config(
    page_title="Warta Poznań - PANEL TRENERA",
    page_icon="📋",
    layout="wide"
)

# --- STYLIZACJA ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
    .stApp {{ background-color: #F8F9FA !important; }}
    h1, h2, h3, p, span, label {{ font-family: 'Anton', sans-serif !important; color: {COLOR_SECONDARY}; }}
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
        border-left: 8px solid {COLOR_WARNING};
        margin-bottom: 10px;
        border: 1px solid #FFCDD2;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LOGOWANIE ---
if "auth_staff" not in st.session_state:
    st.session_state["auth_staff"] = False

def check_auth():
    if not st.session_state["auth_staff"]:
        st.markdown("<h1 style='text-align:center;'>🔐 PANEL SZTABOWY</h1>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col:
            pwd = st.text_input("Hasło:", type="password")
            if st.button("Zaloguj", use_container_width=True):
                if pwd == PASSWORD_TRENER:
                    st.session_state["auth_staff"] = True
                    st.rerun()
                else:
                    st.error("Błędne hasło!")
        return False
    return True

if not check_auth():
    st.stop()

# --- DANE ---
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
        st.error(f"Błąd: {e}")
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.warning("Brak danych w bazie.")
else:
    # --- FILTRY BOCZNE ---
    st.sidebar.header("Ustawienia")
    today = datetime.now(PL_TZ).date()
    date_range = st.sidebar.date_input("Zakres:", value=(today - timedelta(days=7), today))
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        d_start, d_end = date_range
    else:
        d_start = d_end = date_range

    all_players = ["Wszyscy"] + sorted(df_raw['Zawodnik'].unique().tolist())
    selected_player = st.sidebar.selectbox("Zawodnik:", all_players)
    
    mask = (df_raw['Data'].dt.date >= d_start) & (df_raw['Data'].dt.date <= d_end)
    if selected_player != "Wszyscy":
        mask &= (df_raw['Zawodnik'] == selected_player)
    df = df_raw.loc[mask].copy()

    # --- NAGŁÓWEK KPI ---
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="metric-card">WPISY<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="metric-card">ŚR. RPE<br><h2>{df["RPE"].mean():.1f}</h2></div>', unsafe_allow_html=True)
    
    # --- ALERTY BOLESNOŚCI (Na górze) ---
    st.write("### 🚨 AKTYWNE ALERTY BOLESNOŚCI")
    pain_alerts = df[(df['Typ_Raportu'] == 'Wellness') & (df['Bolesnosc'] <= 2)].copy()
    if not pain_alerts.empty:
        for _, row in pain_alerts.sort_values('Data', ascending=False).iterrows():
            st.markdown(f"""
                <div class="alert-box">
                    <b style="color:{COLOR_WARNING}; font-size: 1.1em;">{row['Zawodnik']}</b> | 
                    Bolesność: <b>{row['Bolesnosc']:.0f}/5</b> | 
                    Data: {row['Data'].strftime('%d.%m %H:%M')}<br>
                    <i>Komentarz: {row['Komentarz'] if row['Komentarz'] and str(row['Komentarz']) != 'nan' else 'Brak uwag'}</i>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Brak krytycznych zgłoszeń bólowych w wybranym okresie.")

    # --- ZAKŁADKI ---
    tab_well, tab_freq, tab_ready = st.tabs(["📊 Monitoring Wellness", "⏱️ Frekwencja / Spóźnienia", "📈 Gotowość"])
    
    with tab_well:
        st.subheader("Tabela monitoringu z kolorami")
        df_w = df[df['Typ_Raportu'] == 'Wellness'].copy()
        if not df_w.empty:
            df_disp = df_w.sort_values('Data', ascending=False)[['Data', 'Zawodnik', 'Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']]
            
            def color_w(val):
                if pd.isna(val): return ''
                if val <= 2: return 'background-color: #FFCDD2; color: black;'
                if val >= 4: return 'background-color: #C8E6C9; color: black;'
                return 'background-color: #FFF9C4; color: black;'
            
            st.dataframe(df_disp.style.applymap(color_w, subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']), use_container_width=True)
        else:
            st.info("Brak danych wellness.")

    with tab_freq:
        st.subheader("Punktualność i frekwencja")
        df_f = df_raw.copy()
        df_f['Godzina'] = df_f['Data'].dt.hour
        df_f['Dzien'] = df_f['Data'].dt.date
        
        f_mask = (df_f['Typ_Raportu'] == 'Wellness') & (df_f['Dzien'] >= d_start) & (df_f['Dzien'] <= d_end)
        f_data = df_f.loc[f_mask]
        
        total_days = (d_end - d_start).days + 1
        stats = []
        for p in sorted(df_raw['Zawodnik'].unique()):
            p_res = f_data[f_data['Zawodnik'] == p]
            on_time = len(p_res[p_res['Godzina'] < GODZINA_GRANICZNA])
            late = len(p_res[p_res['Godzina'] >= GODZINA_GRANICZNA])
            missing = max(0, total_days - len(p_res['Dzien'].unique()))
            
            stats.append({
                "Zawodnik": p,
                "Na czas (<10:00)": on_time,
                "Spóźnione": late,
                "Brak raportu": missing,
                "Dyscyplina %": round((on_time/total_days)*100, 1) if total_days > 0 else 0
            })
            
        st.dataframe(pd.DataFrame(stats).sort_values("Brak raportu", ascending=False), use_container_width=True, hide_index=True)

    with tab_ready:
        st.subheader("Gotowość (Readiness)")
        df_r = df[df['Typ_Raportu'] == 'Wellness'].copy().dropna(subset=['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres'])
        if not df_r.empty:
            df_r['Readiness'] = df_r[['Sen', 'Zmeczenie', 'Bolesnosc', 'Stres']].sum(axis=1)
            latest = df_r.sort_values('Data').groupby('Zawodnik').last().reset_index()
            fig = px.bar(latest, x='Zawodnik', y='Readiness', color='Readiness', 
                         color_continuous_scale='RdYlGn', range_y=[0, 20])
            fig.add_hline(y=latest['Readiness'].mean(), line_dash="dash", line_color="black")
            st.plotly_chart(fig, use_container_width=True)

    st.sidebar.button("Wyloguj", on_click=lambda: st.session_state.update({"auth_staff": False}))
