import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

WATCHLIST = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "SBIN"]
SEC_DICT = {'RELIANCE':'500325', 'HDFCBANK':'1333', 'INFY': '500209', 'SBIN':'3045', 'TCS': '11536'}