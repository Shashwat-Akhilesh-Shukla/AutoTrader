import streamlit as st
import pandas as pd
from services.account_service import get_account_summary

def render_account():
    st.header("Account Overview")
    account_data = get_account_summary()
    
    if not account_data:
        st.error("Unable to fetch account information")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Funds")
        if 'funds' in account_data and account_data['funds']:
            funds = account_data['funds']
            st.metric("Available Cash", f"₹{funds.get('limit', 0):,.2f}")
            st.metric("Margin Used", f"₹{funds.get('used', 0):,.2f}")
            st.metric("Net Balance", f"₹{funds.get('net', 0):,.2f}")
        else:
            st.warning("Fund data not available")
    
    with col2:
        st.subheader("Portfolio Summary")
        if 'holdings' in account_data and account_data['holdings']:
            holdings = account_data['holdings']
            total_investment = sum(h.get('buyAvg', 0) * h.get('quantity', 0) for h in holdings)
            current_value = sum(h.get('ltp', 0) * h.get('quantity', 0) for h in holdings)
            profit_loss = current_value - total_investment
            
            st.metric("Total Investment", f"₹{total_investment:,.2f}")
            st.metric("Current Value", f"₹{current_value:,.2f}")
            st.metric("Profit/Loss", f"₹{profit_loss:,.2f}")
        else:
            st.warning("Holdings data not available")
    
    st.subheader("Current Positions")
    if 'positions' in account_data and account_data['positions']:
        positions_df = pd.DataFrame(account_data['positions'])
        st.dataframe(positions_df)
    else:
        st.info("No active positions")
    
    st.subheader("Holdings")
    if 'holdings' in account_data and account_data['holdings']:
        holdings_df = pd.DataFrame(account_data['holdings'])
        st.dataframe(holdings_df)
    else:
        st.info("No holdings data available")