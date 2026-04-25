import os
import streamlit as st
from dhanhq import dhanhq
from krutrim_cloud import KrutrimCloud

@st.cache_resource
def initialize_dhan_and_krutrim():
    missing_keys = []
    dhan = None
    
    if os.getenv('CLIENT') and os.getenv('TOKEN'):
        try:
            dhan = dhanhq(client_id=os.getenv('CLIENT'), access_token=os.getenv("TOKEN"))
        except Exception as e:
            st.warning(f"Failed to initialize Dhan: {e}")
    
    client = None
    if not os.getenv('API_KEY'):
        missing_keys.append("API_KEY (Krutrim API Key)")
    else:
        try:
            client = KrutrimCloud(api_key=os.environ.get("API_KEY"))
        except Exception as e:
            missing_keys.append(f"Krutrim Cloud Error: {e}")
            
    return dhan, client, missing_keys