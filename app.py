import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

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
    
    /* Button & Input Borders */
    .stTextInput > div > div > input {
        border-color: #00D4FF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA CONNECTION ---
@st.cache_data(ttl=60) # Refresh every minute
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 1. Load Live Data (Assume first sheet or Dashboard_Live)
        # Using read() without worksheet name often works better for public sheets
        df_live = conn.read(ttl=0) 
        
        # 2. Load History Data
        # If worksheet name fails, we try to load it specifically or fallback
        try:
            df_history = conn.read(worksheet="History_Daily", ttl=0)
        except:
            # If explicit name fails, use specific logic or empty df
            st.sidebar.error("⚠️ Could not find 'History_Daily' tab specifically.")
            df_history = pd.DataFrame(columns=["Date", "AccountID", "UserEmail", "ClosedProfit", "TotalLots", "MaxDD_Day %"])
            
        return df_live, df_history
    except Exception as e:
        # Fallback to Mock Data if no connection
        st.sidebar.warning("📊 Running in Demo Mode (No Sheet Connected)")
        st.sidebar.error(f"Debug Error: {str(e)}")
        
        # ... (Mock data remains for safety)
        mock_live = pd.DataFrame([
            {"AccountID": "21692434", "UserEmail": "customer@email.com", "LastUpdate": "2024-03-20 12:00:00", "Balance": 379.46, "Equity": 370.00, "CurrentDD %": 2.5},
        ])
        mock_history = pd.DataFrame({
            "Date": pd.date_range(start="2024-03-01", periods=5),
            "AccountID": ["21692434"] * 5,
            "UserEmail": ["customer@email.com"] * 5,
            "ClosedProfit": [10.0, 15.0, -5.0, 20.0, 30.0],
            "TotalLots": [0.01] * 5,
            "MaxDD_Day %": [0.5] * 5
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
            
        # ROW 3: TRADE HISTORY TABLE
        st.markdown("### 📜 Trading History")
        st.dataframe(
            history_info.iloc[::-1], # Reversed to show latest first
            use_container_width=True,
            column_config={
                "Date": "Date",
                "ClosedProfit": st.column_config.NumberColumn("Profit", format="$%.2f"),
                "TotalLots": "Lots",
                "MaxDD_Day %": st.column_config.NumberColumn("Max DD", format="%.2f%%")
            }
        )
        
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
