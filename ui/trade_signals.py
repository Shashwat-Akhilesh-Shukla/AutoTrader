import streamlit as st
import pandas as pd
import config
from datetime import datetime
from services.trading_service import get_trade_decision

if 'WATCHLIST' not in st.session_state:
    st.session_state.WATCHLIST = config.WATCHLIST

if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

def render_trade_signals():
    st.header("AI Trading Signals")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbol = st.selectbox("Select Stock", st.session_state.get('WATCHLIST', []))
        
        if st.button("Generate Signal"):
            with st.spinner("Analyzing..."):
                trade, error = get_trade_decision(symbol)
                if trade:
                    trade['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.trade_history.append(trade)
                    display_trade_details(trade)
                else:
                    st.error(f"Error: {error}")
    with col2:
        st.subheader("Signal History")
        if st.session_state.trade_history:
            history_df = pd.DataFrame([{
                'Time': t['timestamp'],
                'Symbol': t['stock'],
                'Action': t['action'],
                'Price': t['entry_price']
            } for t in st.session_state.trade_history[-5:]])
            
            st.dataframe(history_df, hide_index=True)
            
            if st.button("Clear History"):
                st.session_state.trade_history = []
                st.experimental_rerun()
        else:
            st.info("No signal history")

def display_trade_details(trade):
    st.subheader("Trade Signal")
    action_color = "green" if trade['action'] == "BUY" else "red"
    
    st.markdown(f"<h3 style='color: {action_color};'>{trade['action']} {trade['stock']}</h3>", 
                unsafe_allow_html=True)
    
    cols = st.columns(3)
    cols[0].metric("Entry", f"₹{trade['entry_price']:.2f}")
    cols[1].metric("Stop Loss", f"₹{trade['stop_loss']:.2f}")
    cols[2].metric("Take Profit", f"₹{trade['take_profit']:.2f}")
    
    with st.expander("Analysis Details"):
        st.write(trade['reasoning'])
        st.progress(trade['confidence']/10, text=f"Confidence: {trade['confidence']}/10")
        st.progress(trade['risk_score']/10, text=f"Risk Score: {trade['risk_score']}/10")