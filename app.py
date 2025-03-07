import streamlit as st
import logging
from datetime import datetime
from ui.dashboard import render_dashboard
from ui.market_data import render_market_data
from ui.trade_signals import render_trade_signals
from ui.execute_trades import render_execute_trades
from ui.bot_settings import render_bot_settings
from ui.account import render_account

st.set_page_config(
    page_title="Trading Bot Dashboard",
    page_icon="📈",
    layout="wide"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

if 'last_data_refresh' not in st.session_state:
    st.session_state.last_data_refresh = None

if 'auto_execute' not in st.session_state:
    st.session_state.auto_execute = False

st.sidebar.header("Navigation")
page = st.sidebar.radio("", ["Dashboard", "Market Data", "Trade Signals", "Execute Trades", "Bot Settings", "Account"])

if page == "Dashboard":
    render_dashboard()
elif page == "Market Data":
    render_market_data()
elif page == "Trade Signals":
    render_trade_signals()
elif page == "Execute Trades":
    render_execute_trades()
elif page == "Bot Settings":
    render_bot_settings()
elif page == "Account":
    render_account()

st.divider()
st.caption("Trading Bot Dashboard | © 2025 | Disclaimer: Use at your own risk.")