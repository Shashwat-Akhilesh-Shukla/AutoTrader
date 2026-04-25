import pandas as pd
import streamlit as st
import yfinance as yf
from typing import Tuple
from models import OHLCVData
from database import get_database_engine
from config import WATCHLIST
from sqlalchemy.orm import sessionmaker

def fetch_and_store_data(symbols=None) -> Tuple[bool, str]:
    if symbols is None:
        symbols = WATCHLIST
    
    engine = get_database_engine()
    if not engine:
        return False, "Database connection failed"
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    success_count = 0
    error_messages = []
    
    for stock in symbols:
        try:
            with st.spinner(f"Fetching data for {stock}..."):
                # yfinance expects Indian stocks to end with .NS
                yf_symbol = f"{stock}.NS"
                data = yf.download(yf_symbol, period="100d", interval="1d", progress=False)
                
                if data is None or data.empty:
                    error_messages.append(f"No data found for {stock}")
                    continue
                
                data.reset_index(inplace=True)
                
                # Check for 'Date' or 'Datetime' column in yfinance response
                date_col = 'Date' if 'Date' in data.columns else 'Datetime'
                if date_col not in data.columns:
                    # sometimes yfinance index reset results in level_0 or similar if multi-index
                    # To be safe, let's normalize it
                    pass
                
                # yfinance >= 0.2.30 returns multi-index columns if downloaded as a string but we passed a single symbol
                # the columns are Price, Ticker or just Price. 
                # To handle both, we map the columns to lower case
                data.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in data.columns]
                
                # the date column is usually 'date' or 'datetime' now
                dt_col = 'date' if 'date' in data.columns else 'datetime'
                
                for _, row in data.iterrows():
                    # Handle NaNs
                    if pd.isna(row['open']) or pd.isna(row['close']):
                        continue
                        
                    existing = session.query(OHLCVData).filter_by(
                        datetime=row[dt_col],
                        symbol=stock
                    ).first()
                    
                    if not existing:
                        ohlcv_entry = OHLCVData(
                            datetime=row[dt_col],
                            symbol=stock,
                            open=float(row['open']),
                            high=float(row['high']),
                            low=float(row['low']),
                            close=float(row['close']),
                            volume=float(row['volume'])
                        )
                        session.add(ohlcv_entry)
                
                session.commit()
                success_count += 1
        except Exception as e:
            error_messages.append(f"Error processing {stock}: {str(e)}")
    
    session.close()
    
    if success_count == 0:
        return False, "Failed to fetch data for all stocks"
    elif success_count < len(symbols):
        return True, f"Partially successful: {success_count}/{len(symbols)} stocks updated. Errors: {', '.join(error_messages)}"
    else:
        return True, f"All {success_count} stocks updated successfully"

from sqlalchemy import select
from datetime import datetime, timedelta

def get_data_from_db(symbol: str, days: int = 30) -> pd.DataFrame:
    engine = get_database_engine()
    if not engine:
        return None
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = select(OHLCVData).where(
            OHLCVData.symbol == symbol,
            OHLCVData.datetime >= cutoff_date
        ).order_by(OHLCVData.datetime)
        
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None