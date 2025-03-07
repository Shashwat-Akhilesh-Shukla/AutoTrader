import pandas as pd
import streamlit as st
from tvDatafeed import Interval
from typing import Tuple
from models import OHLCVData
from database import get_database_engine
from apis import get_tv_datafeed
from config import WATCHLIST
from sqlalchemy.orm import sessionmaker

def fetch_and_store_data(symbols=None) -> Tuple[bool, str]:
    if symbols is None:
        symbols = WATCHLIST
    
    engine = get_database_engine()
    if not engine:
        return False, "Database connection failed"
    
    tv = get_tv_datafeed()
    if not tv:
        return False, "TradingView API connection failed"
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    success_count = 0
    error_messages = []
    
    for stock in symbols:
        try:
            with st.spinner(f"Fetching data for {stock}..."):
                data = tv.get_hist(stock, exchange='NSE', interval=Interval.in_daily, n_bars=100)
                
                if data is None or data.empty:
                    error_messages.append(f"No data found for {stock}")
                    continue
                
                data.reset_index(inplace=True)
                
                for _, row in data.iterrows():
                    existing = session.query(OHLCVData).filter_by(
                        datetime=row['datetime'],
                        symbol=stock
                    ).first()
                    
                    if not existing:
                        ohlcv_entry = OHLCVData(
                            datetime=row['datetime'],
                            symbol=stock,
                            open=row['open'],
                            high=row['high'],
                            low=row['low'],
                            close=row['close'],
                            volume=row['volume']
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

def get_data_from_db(symbol: str, days: int = 30) -> pd.DataFrame:
    engine = get_database_engine()
    if not engine:
        return None
    
    query = f"""
    SELECT * FROM ohlcv_data 
    WHERE symbol = '{symbol}' 
    AND datetime >= CURRENT_DATE - INTERVAL '{days} days'
    ORDER BY datetime
    """
    
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None