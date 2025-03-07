import streamlit as st
import os
from config import WATCHLIST

def render_bot_settings():
    st.header("Bot Configuration")
    
    st.subheader("API Settings")
    current_client = os.getenv('CLIENT', '')
    current_token = os.getenv('TOKEN', '')
    current_api_key = os.getenv('API_KEY', '')
    
    with st.form("api_settings"):
        client_id = st.text_input("Dhan Client ID", value=current_client)
        token = st.text_input("Dhan Access Token", value=current_token, type="password")
        api_key = st.text_input("Krutrim API Key", value=current_api_key, type="password")
        
        if st.form_submit_button("Save API Settings"):
            st.success("API settings updated (demo only)")
    
    st.divider()
    
    st.subheader("Watchlist Configuration")
    new_watchlist = st.text_input("Watchlist (comma-separated)", value=",".join(WATCHLIST))
    
    if st.button("Update Watchlist"):
        updated_watchlist = [s.strip() for s in new_watchlist.split(",")]
        st.success(f"Watchlist updated to: {updated_watchlist}")
    
    st.divider()
    
    st.subheader("Risk Parameters")
    col1, col2 = st.columns(2)
    
    with col1:
        min_confidence = st.slider("Minimum Confidence", 1, 10, 7)
        max_daily_trades = st.number_input("Max Daily Trades", 1, 20, 5)
    
    with col2:
        max_risk = st.slider("Maximum Risk Score", 1, 10, 5)
        st.session_state.auto_execute = st.toggle("Auto-Execute Trades", value=st.session_state.auto_execute)
    
    if st.button("Save Risk Parameters"):
        st.success("Risk parameters saved!")