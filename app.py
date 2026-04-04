import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import calendar
from datetime import datetime, date, timedelta

# Page configuration
st.set_page_config(
    page_title="EaEze | Futuristic Forex Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Futuristic Blue Neon) ---
st.markdown("""
<style>
    /* Dark Mode Base */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Neon Blue Glow Boxes */
    [data-testid="column"] {
        background: rgba(0, 212, 255, 0.05);
        border: 1px solid #00D4FF;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
        margin: 5px;
    }
    
    /* Glow for metrics */
    [data-testid="stMetricValue"] {
        color: #00D4FF !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
        font-weight: bold;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0B0E14 !important;
        border-right: 1px solid #00D4FF;
    }
    
    /* Welcome Header Glow */
    .welcome-header {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #00D4FF, #0056B3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        margin-bottom: 30px;
    }
    
    /* Calendar Card Styling */
    .cal-card {
        background: rgba(0, 212, 255, 0.05);
        border: 1px solid #00D4FF;
        border-radius: 12px;
        padding: 15px 10px;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .cal-card:hover {
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
        transform: scale(1.02);
    }
    
    .cal-date {
        font-size: 0.8rem;
        color: #888;
        position: absolute;
        top: 5px;
        left: 10px;
    }
    
    .cal-profit {
        font-size: 1.8rem;
        font-weight: 800;
        color: #00D4FF;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
    }
    
    .cal-profit-neg {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FF4B4B;
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
    }
    
    .cal-day-header {
        text-align: center;
        font-weight: bold;
        color: #00D4FF;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER: CLEAN NUMERIC ---
def clean_numeric(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        # Remove $, %, and commas
        clean_val = value.replace('$', '').replace('%', '').replace(',', '').strip()
        try:
            return float(clean_val)
        except:
            return 0.0
    return float(value)

# --- DATA CONNECTION ---
@st.cache_data(ttl=60)
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 1. Load Live Data
        df_live = conn.read(ttl=0)
        # Convert Cent to Standard USD for Live Data
        for col in ['Balance', 'Equity']:
            if col in df_live.columns:
                df_live[col] = df_live[col].apply(clean_numeric) / 100.0
        
        # Drawdown is usually a percentage, so keep it as is after cleaning
        if 'CurrentDD %' in df_live.columns:
            df_live['CurrentDD %'] = df_live['CurrentDD %'].apply(clean_numeric)
        
        # 2. Load History Data (Direct CSV Link)
        try:
            sheet_url = st.secrets.connections.gsheets.spreadsheet
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            url_history = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=379227189"
            df_history = pd.read_csv(url_history)
        except Exception as e:
            st.sidebar.error(f"⚠️ History sync error: {str(e)}")
            df_history = pd.DataFrame(columns=["Date", "AccountID", "UserEmail", "ClosedProfit", "TotalLots", "MaxDD_Day %"])
        
        # Convert Cent to Standard for History Data
        if 'ClosedProfit' in df_history.columns:
            df_history['ClosedProfit'] = df_history['ClosedProfit'].apply(clean_numeric) / 100.0
        
        if 'TotalLots' in df_history.columns:
            # Standard Lots = Cent Lots / 100
            df_history['StandardLots'] = df_history['TotalLots'].apply(clean_numeric) / 100.0
            # Rebate calculation ($15 per Standard Lot)
            df_history['Rebate'] = df_history['StandardLots'] * 15.0
            
        if 'MaxDD_Day %' in df_history.columns:
            df_history['MaxDD_Day %'] = df_history['MaxDD_Day %'].apply(clean_numeric)
                
        return df_live, df_history
    except Exception as e:
        st.sidebar.warning("📊 Running in Demo Mode")
        st.sidebar.error(f"Debug: {str(e)}")
        # ... (Mock data with cent-to-standard logic)
        mock_live = pd.DataFrame([
            {"AccountID": "21692434", "UserEmail": "customer@email.com", "LastUpdate": "2024-03-20", "Balance": 737.03, "Equity": 677.75, "CurrentDD %": 8.48},
        ])
        mock_history = pd.DataFrame({
            "Date": ["2024-03-01"], "AccountID": ["21692434"], "UserEmail": ["customer@email.com"], 
            "ClosedProfit": [1.0], "StandardLots": [0.01], "Rebate": [0.15], "MaxDD_Day %": [0.5]
        })
        return mock_live, mock_history

df_live, df_history = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://via.placeholder.com/150/00D4FF/000?text=EaEze+Logo", width=150) # Placeholder for logo
    st.title("🎛 Control Center")
    account_id = st.text_input("🔑 Account ID", placeholder="Enter ID to login...")
    st.markdown("---")
    st.caption("EaEze Forex Terminal v1.0")

# --- MAIN LOGIC ---
if account_id:
    # Check if Account ID exists
    if df_live is not None and account_id in df_live['AccountID'].astype(str).values:
        # Filter Data
        live_info = df_live[df_live['AccountID'].astype(str) == account_id].iloc[0]
        history_info = df_history[df_history['AccountID'].astype(str) == account_id]
        
        # UI: Top Header
        st.markdown(f"<h1 style='color: #00D4FF;'>⚓ PORTFOLIO: {account_id}</h1>", unsafe_allow_html=True)
        st.markdown(f"**Email:** {live_info['UserEmail']} | **Last Update:** {live_info['LastUpdate']}")
        st.markdown("---")

        # TABS FOR DIFFERENT VIEWS
        tabs = st.tabs(["🚀 Dashboard", "📅 Monthly View", "📊 Weekly View"])

        # --- TAB 1: DASHBOARD ---
        with tabs[0]:
            # ROW 1: SCORECARDS
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Balance", f"${live_info['Balance']:,.2f}")
            with col2:
                st.metric("📊 Equity", f"${live_info['Equity']:,.2f}")
            with col3:
                st.metric("📉 Drawdown", f"{live_info['CurrentDD %']}%")
                
            # ROW 2: PROFIT CHART
            st.markdown("### 📈 Cumulative Profit Analysis")
            if not history_info.empty:
                # Calculate cumulative profit
                history_info = history_info.sort_values('Date')
                history_info['CumulativeProfit'] = history_info['ClosedProfit'].cumsum()
                
                fig = px.line(
                    history_info, 
                    x='Date', 
                    y='CumulativeProfit',
                    markers=True,
                    line_shape="spline",
                    color_discrete_sequence=['#00D4FF']
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#E0E0E0',
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    margin=dict(l=0, r=0, t=10, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No history data available for this account.")
            
            # Calculate Net Profit (Profit + Rebate) for the table
            if not history_info.empty:
                history_info['NetProfit'] = history_info['ClosedProfit'] + history_info['Rebate']

            # ROW 3: TRADE HISTORY TABLE
            st.markdown("### 📜 Trading History")
            st.dataframe(
                history_info.iloc[::-1], # Reversed to show latest first
                use_container_width=True,
                column_order=("Date", "StandardLots", "ClosedProfit", "Rebate", "NetProfit", "MaxDD_Day %"),
                column_config={
                    "Date": "Date",
                    "StandardLots": st.column_config.NumberColumn("Lots (Std)", format="%.2f"),
                    "ClosedProfit": st.column_config.NumberColumn("Profit ($)", format="$%.2f"),
                    "Rebate": st.column_config.NumberColumn("Rebate ($)", format="$%.2f"),
                    "NetProfit": st.column_config.NumberColumn("Total ($)", format="$%.2f"),
                    "MaxDD_Day %": st.column_config.NumberColumn("Max DD", format="%.2f%%")
                },
                hide_index=True
            )

        # --- TAB 2: MONTHLY VIEW (Social Share) ---
        with tabs[1]:
            st.markdown("### 🗓️ Monthly Profit Calendar (Shareable)")
            
            # Month Selection
            now = datetime.now()
            month_names = list(calendar.month_name)[1:]
            sel_month = st.selectbox("Select Month", month_names, index=now.month - 1)
            sel_year = st.number_input("Select Year", min_value=2020, max_value=2030, value=now.year)
            
            month_idx = list(calendar.month_name).index(sel_month)
            cal_grid = calendar.monthcalendar(sel_year, month_idx)
            
            # Header
            cols = st.columns(7)
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for i, d in enumerate(days):
                cols[i].markdown(f"<div class='cal-day-header'>{d}</div>", unsafe_allow_html=True)
            
            # Calendar Rendering
            # Convert history dates to strings for easier lookup
            if not history_info.empty:
                history_info['NetProfit'] = history_info['ClosedProfit'] + history_info['Rebate']
                history_info['DateStr'] = pd.to_datetime(history_info['Date']).dt.date
                profit_map = history_info.groupby('DateStr')['NetProfit'].sum().to_dict()
            else:
                profit_map = {}

            for week in cal_grid:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day == 0:
                        cols[i].markdown("<div style='min-height: 100px;'></div>", unsafe_allow_html=True)
                    else:
                        cur_date = date(sel_year, month_idx, day)
                        profit = profit_map.get(cur_date, None)
                        
                        box_class = "cal-profit" if (profit is not None and profit >= 0) else "cal-profit-neg"
                        profit_text = f"${profit:,.2f}" if profit is not None else "-"
                        
                        cols[i].markdown(f"""
                            <div class="cal-card">
                                <div class="cal-date">{day}</div>
                                <div class="{box_class}">{profit_text}</div>
                            </div>
                        """, unsafe_allow_html=True)

        # --- TAB 3: WEEKLY VIEW (Horizontal) ---
        with tabs[2]:
            st.markdown("### 📊 Weekly Performance Overview")
            
            # Get last 7 days of trading
            if not history_info.empty:
                last_7_days = []
                base = date.today()
                for i in range(6, -1, -1):
                    last_7_days.append(base - timedelta(days=i))
                
                cols = st.columns(7)
                for i, cur_date in enumerate(last_7_days):
                    profit = profit_map.get(cur_date, None)
                    box_class = "cal-profit" if (profit is not None and profit >= 0) else "cal-profit-neg"
                    profit_text = f"${profit:,.2f}" if profit is not None else "-"
                    
                    cols[i].markdown(f"""
                        <div class="cal-card">
                            <div class="cal-date">{cur_date.strftime('%d/%m')}</div>
                            <div class="{box_class}">{profit_text}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No activity found in the last 7 days.")

    else:
        # ID NOT FOUND
        st.error("❌ Account ID not found. Please verify your ID.")
        st.info("💡 Make sure your ID is correctly listed in the Dashboard_Live sheet.")
else:
    # WELCOME SCREEN
    st.markdown("<div class='welcome-header'>WELCOME TO EA-EZE DASHBOARD</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### ระบบติดตามผลพอร์ตการลงทุนอัจฉริยะ
        เข้าถึงข้อมูลพอร์ตการเทรดแบบ Real-time ด้วยธีม Futuristic ที่ออกแบบมาเพื่อมืออาชีพเท่านั้น
        
        **ฟีเจอร์หลัก:**
        - 🚀 **Live Metrics**: ติดตาม Balance, Equity และ Drawdown ทันที
        - 📈 **Visual Analytics**: วิเคราะห์กำไรสะสมผ่านกราฟอัจฉริยะ
        - 🔒 **Secure Access**: เข้าถึงเฉพาะพอร์ตของคุณผ่าน Account ID
        
        --- 
        **กรุณาป้อน 'Account ID' ในแถบด้านซ้ายเพื่อเริ่มต้นใช้งาน**
        """)
    
    with col2:
        st.image("https://via.placeholder.com/300/0E1117/00D4FF?text=Futuristic+Forex", use_container_width=True)
    
    st.divider()
    st.info("🔌 กรุณาตรวจสอบสถานะการเชื่อมต่อ Google Sheets ในหน้าตั้งค่าก่อนใช้งาน (secrets.toml)")
