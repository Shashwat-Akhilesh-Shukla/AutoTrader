import streamlit as st
import pandas as pd
from datetime import datetime
from services.trading_service import execute_trade

def render_execute_trades():
    st.header("Trade Execution")
    
    if not st.session_state.trade_history:
        st.warning("No trade signals available")
        return
    
    recent_trades = st.session_state.trade_history[-5:]
    trade_options = [f"{t['timestamp']} | {t['action']} {t['stock']} @ ₹{t['entry_price']:.2f}" 
                    for t in recent_trades]
    
    selected_idx = st.selectbox("Select Trade", range(len(recent_trades)), 
                               format_func=lambda x: trade_options[x])
    trade = recent_trades[selected_idx]
    
    st.subheader("Trade Details")
    col1, col2 = st.columns(2)
    
    with col1:
        action_color = "green" if trade['action'] == "BUY" else "red"
        st.markdown(f"<h3 style='color: {action_color};'>{trade['action']} {trade['stock']}</h3>",
                    unsafe_allow_html=True)
        st.metric("Entry Price", f"₹{trade['entry_price']:.2f}")
        st.metric("Stop Loss", f"₹{trade['stop_loss']:.2f}")
        st.metric("Take Profit", f"₹{trade['take_profit']:.2f}")
    
    with col2:
        st.subheader("Risk Analysis")
        st.progress(trade['confidence']/10, text=f"Confidence: {trade['confidence']}/10")
        st.progress(trade['risk_score']/10, text=f"Risk Score: {trade['risk_score']}/10")
        st.write(trade['reasoning'])
    
    if st.button("Execute Trade"):
        success, message = execute_trade(trade)
        if success:
            st.success(message)
            trade['executed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            st.error(message)