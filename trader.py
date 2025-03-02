from dhanhq import dhanhq
from dotenv import load_dotenv
import os
from krutrim_cloud import KrutrimCloud
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Index
from sqlalchemy.orm import declarative_base, sessionmaker
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import json
import logging

# Configure Logging
logging.basicConfig(
    filename="trading_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load Environment Variables
load_dotenv()

# Initialize Broker API (Dhan)
dhan = dhanhq(client_id=os.getenv('CLIENT'), access_token=os.getenv("TOKEN"))

# Initialize AI Model (DeepSeek via Krutrim)
client = KrutrimCloud(api_key=os.environ.get("API_KEY"))
model_name = "DeepSeek-R1"

# PostgreSQL Database Setup
DATABASE_URL = "postgresql://postgres:shashwat@localhost:5432/trading_data"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class OHLCVData(Base):
    __tablename__ = 'ohlcv_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

# Indexing for faster lookups
Index('idx_ohlcv_symbol_datetime', OHLCVData.symbol, OHLCVData.datetime)

# Create Table
Base.metadata.create_all(engine)

# Initialize TradingView Data API
tv = TvDatafeed()

# User-defined watchlist
WATCHLIST = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "SBIN"]
sec = {'RELIANCE':'500325', 'HDFCBANK':'1333', 'INFY': '500209', 'SBIN':'3045', 'TCS': '11536'}

# Function to Fetch and Store Data
def fetch_and_store_data():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    for stock in WATCHLIST:
        try:
            data = tv.get_hist(stock, exchange='NSE', interval=Interval.in_daily, n_bars=100)
            
            if data is None or data.empty:
                logging.warning(f"No data found for {stock}. Skipping...")
                continue  # Skip this stock if no data is found
            
            data.reset_index(inplace=True)
            
            for _, row in data.iterrows():
                try:
                    ohlcv_entry = OHLCVData(
                        datetime=row['datetime'],
                        symbol=stock,  # Ensure symbol is correctly assigned
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    session.add(ohlcv_entry)
                except Exception as e:
                    logging.error(f"Error inserting data for {stock} at {row['datetime']}: {e}")
            
            session.commit()
            logging.info(f"Data stored successfully for {stock}.")
        
        except Exception as e:
            logging.error(f"Failed to fetch data for {stock}: {e}")
    
    session.close()

# Function to Generate Trade Decisions from AI
def get_trade_decisions():
    prompt = f"""Analyze the following stocks from the watchlist: {WATCHLIST}. Provide trading decisions in JSON format:
    [{{'stock': 'TCS', 'action': 'BUY', 'entry_price': 3500, 'stop_loss': 3475, 'take_profit': 3600, 'order_type': 'INTRADAY'}}, ...]
    """
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(model=model_name, messages=messages)
        
        # Ensure AI response is in correct format
        trade_data = response.choices[0].message.content
        if not trade_data:
            logging.warning("AI response is empty. No trades generated.")
            return []
        
        try:
            trades = json.loads(trade_data)
            return trades
        except json.JSONDecodeError:
            logging.error("AI response is not in valid JSON format.")
            return []
    
    except Exception as e:
        logging.error(f"Error getting trade decisions from AI: {e}")
        return []

# Function to Execute Trades on Dhan
def execute_trades(trades):
    for trade in trades:
        try:
            stock = trade['stock']
            action = trade['action'].upper()
            entry_price = trade['entry_price']
            stop_loss = trade['stop_loss']
            take_profit = trade['take_profit']
            order_type = trade['order_type'].upper()
            
            logging.info(f"Executing trade: {action} {stock} at {entry_price}, SL: {stop_loss}, TP: {take_profit}")
            
            
            dhan.place_order(security_id=sec.stock,
                exchange_segment=dhan.NSE,
                transaction_type=dhan.BUY if action=='BUY' else dhan.SELL,
                quantity=1,
                order_type=dhan.MARKET,
                product_type=dhan.INTRA,
                price=0)
        
        except KeyError as e:
            logging.error(f"Missing key in trade data: {e}")
        except Exception as e:
            logging.error(f"Error executing trade for {trade}: {e}")

# Main Execution
if __name__ == "__main__":
    try:
        fetch_and_store_data()
        trades = get_trade_decisions()
        if trades:
            execute_trades(trades)
        else:
            logging.info("No valid trade signals received.")
    except Exception as e:
        logging.critical(f"Unexpected error in main execution: {e}")
