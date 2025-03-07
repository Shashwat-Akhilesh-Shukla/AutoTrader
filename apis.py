import os
import streamlit as st
from dhanhq import dhanhq
from krutrim_cloud import KrutrimCloud
from tvDatafeed import TvDatafeed

@st.cache_resource
def initialize_dhan_and_krutrim():
    missing_keys = []
    if not os.getenv('CLIENT'):
        missing_keys.append("CLIENT (Dhan Client ID)")
    if not os.getenv('TOKEN'):
        missing_keys.append("TOKEN (Dhan Access Token)")
    if not os.getenv('API_KEY'):
        missing_keys.append("API_KEY (Krutrim API Key)")
    
    if missing_keys:
        return None, None, missing_keys
    
    try:
        dhan = dhanhq(client_id=os.getenv('CLIENT'), access_token=os.getenv("TOKEN"))
        client = KrutrimCloud(api_key=os.environ.get("API_KEY"))
        return dhan, client, []
    except Exception as e:
        return None, None, [str(e)]

@st.cache_resource
def get_tv_datafeed():
    try:
        return TvDatafeed()
    except Exception as e:
        st.error(f"Error initializing TradingView data feed: {e}")
        return None