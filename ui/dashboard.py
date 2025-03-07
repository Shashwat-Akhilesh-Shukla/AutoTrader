import streamlit as st
import pandas as pd
from apis import initialize_dhan_and_krutrim
from config import WATCHLIST
from datetime import datetime
from services.trading_service import get_trade_decision, execute_trade
from services.data_service import fetch_and_store_data, get_data_from_db
from services.account_service import get_account_summary

def render_dashboard():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Market Overview")
        markets = [
            {"Index": "NIFTY 50", "Value": "21,349.50", "Change": "+0.75%"},
            {"Index": "SENSEX", "Value": "70,120.35", "Change": "+0.68%"},
            {"Index": "BANK NIFTY", "Value": "44,712.75", "Change": "+0.42%"}
        ]
        st.dataframe(pd.DataFrame(markets), hide_index=True)
        
        st.subheader("Watchlist Performance")
        performance_data = []
        for symbol in WATCHLIST:
            df = get_data_from_db(symbol, days=7)
            if df is not None and not df.empty:
                change_pct = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
                performance_data.append({
                    "Symbol": symbol,
                    "Current Price": f"₹{df['close'].iloc[-1]:.2f}",
                    "Week Change": f"{change_pct:.2f}%",
                    "Last Updated": df['datetime'].iloc[-1].strftime("%d-%m-%Y")
                })
        
        if performance_data:
            st.dataframe(pd.DataFrame(performance_data), hide_index=True)
        else:
            st.warning("No performance data available")
    
    with col2:
        st.subheader("Bot Status")
        dhan, _, missing_keys = initialize_dhan_and_krutrim()
        if missing_keys:
            st.error(f"⚠️ Missing API keys: {', '.join(missing_keys)}")
        else:
            st.success("✅ APIs Connected")
        
        if st.session_state.last_data_refresh:
            st.info(f"Last Data Refresh: {st.session_state.last_data_refresh.strftime('%d-%m-%Y %H:%M:%S')}")
        else:
            st.warning("Market data not yet refreshed")
        
        st.subheader("Auto Execution")
        st.session_state.auto_execute = st.toggle("Enable Auto-Execute Trades")

        if st.session_state.auto_execute:
            st.write("✅ Auto-execution is ENABLED")
            for symbol in st.session_state.WATCHLIST:
                trade, error = get_trade_decision(symbol)
                if trade:
                    trade['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.trade_history.append(trade)
                    success, message = execute_trade(trade)
                    if success:
                        st.success(f"Trade Executed: {message}")
                        trade['executed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        st.error(f"Trade Execution Failed: {message}")
                else:
                    st.error(f"Trade Signal Error: {error}")
        else:
            st.write("⚠️ Auto-execution is DISABLED")

    
    st.subheader("Recent Trade Signals")
    if st.session_state.trade_history:
        st.dataframe(pd.DataFrame(st.session_state.trade_history[-5:]), hide_index=True)
    else:
        st.info("No recent trade signals")