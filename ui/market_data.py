import streamlit as st
import pandas as pd
from services.data_service import fetch_and_store_data, get_data_from_db
from services.plot_service import plot_stock_data
from config import WATCHLIST

def render_market_data():
    st.header("Market Data")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_symbol = st.selectbox("Select Stock", WATCHLIST)
        plot_stock_data(selected_symbol)
    
    with col2:
        st.subheader("Data Controls")
        
        if st.button("Refresh All Data"):
            with st.spinner("Updating market data..."):
                success, message = fetch_and_store_data()
                if success:
                    st.success(message)
                    st.session_state.last_data_refresh = pd.Timestamp.now()
                else:
                    st.error(message)
        
        st.divider()
        refresh_symbol = st.selectbox("Refresh Single", WATCHLIST)
        
        if st.button("Refresh Selected"):
            with st.spinner(f"Updating {refresh_symbol}..."):
                success, message = fetch_and_store_data([refresh_symbol])
                if success:
                    st.success(message)
                    st.session_state.last_data_refresh = pd.Timestamp.now()
                else:
                    st.error(message)
    
    st.subheader(f"Recent Data: {selected_symbol}")
    df = get_data_from_db(selected_symbol, days=10)
    if df is not None and not df.empty:
        st.dataframe(df.style.format({
            'open': '{:.2f}',
            'high': '{:.2f}',
            'low': '{:.2f}',
            'close': '{:.2f}',
            'volume': '{:,.0f}'
        }))
    else:
        st.warning("No data available")