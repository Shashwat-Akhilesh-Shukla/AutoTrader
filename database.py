from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st
from models import Base
import os

@st.cache_resource
def get_database_engine():
    try:
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:shashwat@localhost:5432/trading_data")
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        return engine
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None