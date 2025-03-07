import streamlit as st
from apis import initialize_dhan_and_krutrim

def get_account_summary() -> dict:
    dhan, _, missing_keys = initialize_dhan_and_krutrim()
    if missing_keys:
        return None
    
    try:
        return {
            'funds': dhan.get_fund_limits(),
            'positions': dhan.get_positions(),
            'holdings': dhan.get_holdings()
        }
    except Exception as e:
        st.error(f"Error fetching account details: {e}")
        return None