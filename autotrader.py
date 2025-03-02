import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from dhanhq import dhanhq
from dotenv import load_dotenv
from krutrim_cloud import KrutrimCloud
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from tvDatafeed import TvDatafeed, Interval
import json
import logging
import time
from datetime import datetime, timedelta
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Trading Bot Dashboard",
    page_icon="📈",
    layout="wide"
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Database setup
@st.cache_resource
def get_database_engine():
    try:
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:shashwat@localhost:5432/trading_data")
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

        # Create table if it doesn't exist
        Base.metadata.create_all(engine)
        return engine, OHLCVData
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None, None

# Initialize APIs
@st.cache_resource
def initialize_apis():
    load_dotenv()
    
    # Check for API keys in environment
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

# Initialize TradingView Data API
@st.cache_resource
def get_tv_data():
    try:
        return TvDatafeed()
    except Exception as e:
        st.error(f"Error initializing TradingView data feed: {e}")
        return None

# Constants
WATCHLIST = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "SBIN"]
SEC_DICT = {'RELIANCE':'500325', 'HDFCBANK':'1333', 'INFY': '500209', 'SBIN':'3045', 'TCS': '11536'}

# Functions
def fetch_and_store_data(symbols=None):
    if symbols is None:
        symbols = WATCHLIST
    
    engine, OHLCVData = get_database_engine()
    if not engine:
        return False, "Database connection failed"
    
    tv = get_tv_data()
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
                    # Check if entry already exists
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

def get_data_from_db(symbol, days=30):
    engine, _ = get_database_engine()
    if not engine:
        return None
    
    query = f"""
    SELECT * FROM ohlcv_data 
    WHERE symbol = '{symbol}' 
    AND datetime >= CURRENT_DATE - INTERVAL '{days} days'
    ORDER BY datetime
    """
    
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def generate_trading_prompt(symbol):
    # Get recent data
    df = get_data_from_db(symbol, days=30)
    if df is None or df.empty:
        return f"Insufficient data for {symbol}"
    
    # Calculate some basic indicators
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # Get recent price action
    last_price = df['close'].iloc[-1]
    prev_price = df['close'].iloc[-2]
    price_change = (last_price - prev_price) / prev_price * 100
    
    # Format the data for the prompt
    recent_data = df.tail(5).to_dict('records')
    data_str = json.dumps(recent_data)
    
    prompt = f"""Analyze the following stock: {symbol}
    
Current price: {last_price}
Daily change: {price_change:.2f}%
20-day SMA: {df['sma_20'].iloc[-1]:.2f}
50-day SMA: {df['sma_50'].iloc[-1]:.2f}
    
Recent price data:
{data_str}
    
Based on the above data, provide a trading decision in the following JSON format:
{{
    "stock": "{symbol}",
    "action": "BUY or SELL or HOLD",
    "reasoning": "Brief explanation for your decision",
    "entry_price": float,
    "stop_loss": float,
    "take_profit": float,
    "order_type": "INTRADAY or DELIVERY",
    "risk_score": integer (1-10, with 10 being highest risk),
    "confidence": integer (1-10, with 10 being highest confidence)
}}
    
Ensure your response contains only valid JSON.
"""
    return prompt

def get_trade_decision(symbol):
    _, client, missing_keys = initialize_apis()
    if missing_keys:
        return None, f"Missing API keys: {', '.join(missing_keys)}"
    
    prompt = generate_trading_prompt(symbol)
    
    try:
        model_name = "DeepSeek-R1"
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(model=model_name, messages=messages)
        
        # Extract and parse JSON
        trade_data = response.choices[0].message.content
        try:
            # Find JSON in the response
            start_idx = trade_data.find('{')
            end_idx = trade_data.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = trade_data[start_idx:end_idx]
                trade = json.loads(json_str)
                return trade, None
            else:
                return None, "No valid JSON found in AI response"
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON format: {e}"
    
    except Exception as e:
        return None, f"Error getting trade decision: {e}"

def execute_trade(trade):
    dhan, _, missing_keys = initialize_apis()
    if missing_keys:
        return False, f"Missing API keys: {', '.join(missing_keys)}"
    
    try:
        stock = trade['stock']
        action = trade['action'].upper()
        
        if action == "HOLD":
            return True, "No trade executed as decision was to HOLD"
        
        if stock not in SEC_DICT:
            return False, f"Security ID not found for {stock}"
        
        entry_price = trade.get('entry_price', 0)
        order_type = trade.get('order_type', 'INTRADAY').upper()
        
        # Execute the trade
        response = dhan.place_order(
            security_id=SEC_DICT[stock],
            exchange_segment=dhan.NSE,
            transaction_type=dhan.BUY if action=='BUY' else dhan.SELL,
            quantity=1,  # You might want to calculate this based on risk management
            order_type=dhan.MARKET,
            product_type=dhan.INTRA if order_type == 'INTRADAY' else dhan.DELIVERY,
            price=0
        )
        
        return True, f"Order placed: {json.dumps(response)}"
    
    except Exception as e:
        return False, f"Error executing trade: {e}"

def plot_stock_data(symbol):
    df = get_data_from_db(symbol)
    if df is None or df.empty:
        st.warning(f"No data available for {symbol}")
        return
    
    # Calculate indicators
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # Create subplot with 2 rows
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                   vertical_spacing=0.1, subplot_titles=(f'{symbol} Price', 'Volume'), 
                   row_heights=[0.7, 0.3])
    
    # Add candlestick
    fig.add_trace(go.Candlestick(x=df['datetime'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='OHLC'),
                    row=1, col=1)
    
    # Add Moving averages
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['sma_20'], 
                    line=dict(color='blue', width=1),
                    name='SMA 20'),
                    row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['sma_50'], 
                    line=dict(color='orange', width=1),
                    name='SMA 50'),
                    row=1, col=1)
    
    # Add volume
    fig.add_trace(go.Bar(x=df['datetime'], y=df['volume'], name='Volume', marker_color='rgba(0,0,250,0.3)'),
                row=2, col=1)
    
    # Update layout
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True,
        xaxis_title='Date',
        yaxis_title='Price',
        yaxis2_title='Volume',
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    st.plotly_chart(fig, use_container_width=True)

def get_account_summary():
    dhan, _, missing_keys = initialize_apis()
    if missing_keys:
        return None
    
    try:
        funds = dhan.get_fund()
        positions = dhan.get_positions()
        holdings = dhan.get_holdings()
        
        return {
            'funds': funds,
            'positions': positions,
            'holdings': holdings
        }
    except Exception as e:
        st.error(f"Error fetching account details: {e}")
        return None

# Streamlit UI
st.title("🤖 Autonomous Trading Bot Dashboard")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("", ["Dashboard", "Market Data", "Trade Signals", "Execute Trades", "Bot Settings", "Account"])

# Initialize session state
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

if 'last_data_refresh' not in st.session_state:
    st.session_state.last_data_refresh = None

if 'auto_execute' not in st.session_state:
    st.session_state.auto_execute = False

# Dashboard Page
if page == "Dashboard":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Market Overview")
        
        # Quick overview
        markets = [
            {"Index": "NIFTY 50", "Value": "21,349.50", "Change": "+0.75%"},
            {"Index": "SENSEX", "Value": "70,120.35", "Change": "+0.68%"},
            {"Index": "BANK NIFTY", "Value": "44,712.75", "Change": "+0.42%"}
        ]
        
        st.dataframe(pd.DataFrame(markets), hide_index=True)
        
        # Watchlist performance
        st.subheader("Watchlist Performance")
        
        performance_data = []
        for symbol in WATCHLIST:
            df = get_data_from_db(symbol, days=7)
            if df is not None and not df.empty:
                start_price = df['close'].iloc[0]
                end_price = df['close'].iloc[-1]
                change_pct = (end_price - start_price) / start_price * 100
                
                performance_data.append({
                    "Symbol": symbol,
                    "Current Price": f"₹{end_price:.2f}",
                    "Week Change": f"{change_pct:.2f}%",
                    "Last Updated": df['datetime'].iloc[-1].strftime("%d-%m-%Y")
                })
        
        if performance_data:
            df_perf = pd.DataFrame(performance_data)
            st.dataframe(df_perf, hide_index=True)
        else:
            st.warning("No performance data available. Please refresh market data.")
    
    with col2:
        st.subheader("Bot Status")
        
        # Connection status
        dhan, client, missing_keys = initialize_apis()
        
        if missing_keys:
            st.error(f"⚠️ API Configuration Missing: {', '.join(missing_keys)}")
        else:
            st.success("✅ APIs Connected")
        
        # Data status
        if st.session_state.last_data_refresh:
            st.info(f"Last Data Refresh: {st.session_state.last_data_refresh.strftime('%d-%m-%Y %H:%M:%S')}")
        else:
            st.warning("Market data not yet refreshed")
        
        # Auto-execution toggle
        st.subheader("Auto Execution")
        st.session_state.auto_execute = st.toggle("Enable Auto-Execute Trades", value=st.session_state.auto_execute)
        
        if st.session_state.auto_execute:
            st.success("Auto-execution is ENABLED")
        else:
            st.info("Auto-execution is DISABLED")
    
    # Recent trade signals
    st.subheader("Recent Trade Signals")
    if st.session_state.trade_history:
        # Convert to DataFrame for display
        trade_df = pd.DataFrame(st.session_state.trade_history[-5:])
        st.dataframe(trade_df, hide_index=True)
    else:
        st.info("No recent trade signals. Generate signals in the Trade Signals tab.")

# Market Data Page
elif page == "Market Data":
    st.header("Market Data")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_symbol = st.selectbox("Select Stock", WATCHLIST)
        
        if selected_symbol:
            plot_stock_data(selected_symbol)
    
    with col2:
        st.subheader("Data Controls")
        
        if st.button("Refresh All Market Data"):
            with st.spinner("Fetching latest market data..."):
                success, message = fetch_and_store_data()
                if success:
                    st.success(message)
                    st.session_state.last_data_refresh = datetime.now()
                else:
                    st.error(message)
        
        st.divider()
        
        # Select specific stock to refresh
        refresh_symbol = st.selectbox("Refresh Single Stock", WATCHLIST, key="refresh_single")
        
        if st.button("Refresh Selected Stock"):
            with st.spinner(f"Fetching latest data for {refresh_symbol}..."):
                success, message = fetch_and_store_data([refresh_symbol])
                if success:
                    st.success(message)
                    st.session_state.last_data_refresh = datetime.now()
                else:
                    st.error(message)
    
    # Data preview
    st.subheader(f"Data Preview: {selected_symbol}")
    df = get_data_from_db(selected_symbol, days=10)
    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.warning(f"No data available for {selected_symbol}")

# Trade Signals Page
elif page == "Trade Signals":
    st.header("AI-Generated Trade Signals")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        signal_symbol = st.selectbox("Select Stock for Analysis", WATCHLIST)
        
        if st.button("Generate Trading Signal"):
            with st.spinner("Analyzing market data and generating signal..."):
                trade, error = get_trade_decision(signal_symbol)
                
                if trade:
                    st.success("Trade signal generated successfully!")
                    
                    # Add timestamp to trade and save to history
                    trade['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.trade_history.append(trade)
                    
                    # Display the trade details
                    st.subheader("Trade Signal Details")
                    
                    # Color code based on action
                    action_color = "green" if trade['action'] == "BUY" else "red" if trade['action'] == "SELL" else "orange"
                    
                    st.markdown(f"""
                    <h3 style='color: {action_color};'>{trade['action']} {trade['stock']}</h3>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Entry Price", f"₹{trade['entry_price']:.2f}")
                    with col_b:
                        st.metric("Stop Loss", f"₹{trade['stop_loss']:.2f}")
                    with col_c:
                        st.metric("Take Profit", f"₹{trade['take_profit']:.2f}")
                    
                    st.info(f"Order Type: {trade['order_type']}")
                    
                    st.progress(trade['confidence']/10, text=f"Confidence: {trade['confidence']}/10")
                    st.progress(trade['risk_score']/10, text=f"Risk Score: {trade['risk_score']}/10")
                    
                    st.subheader("Analysis")
                    st.write(trade['reasoning'])
                    
                else:
                    st.error(f"Failed to generate signal: {error}")
    
    with col2:
        st.subheader("Trade History")
        
        if st.session_state.trade_history:
            # Simplified history view
            history_df = pd.DataFrame([
                {"Time": t['timestamp'], 
                 "Stock": t['stock'], 
                 "Action": t['action'],
                 "Price": t['entry_price']}
                for t in st.session_state.trade_history
            ])
            
            st.dataframe(history_df, hide_index=True)
            
            if st.button("Clear History"):
                st.session_state.trade_history = []
                st.experimental_rerun()
        else:
            st.info("No trade history available")

# Execute Trades Page
elif page == "Execute Trades":
    st.header("Trade Execution")
    
    # Get recent signals
    if not st.session_state.trade_history:
        st.warning("No trade signals available. Generate signals in the Trade Signals tab.")
    else:
        recent_trades = st.session_state.trade_history[-5:]
        
        # Select a trade
        trade_options = [f"{t['timestamp']} | {t['action']} {t['stock']} @ ₹{t['entry_price']:.2f}" for t in recent_trades]
        selected_trade_idx = st.selectbox("Select Trade to Execute", range(len(trade_options)), format_func=lambda x: trade_options[x])
        
        selected_trade = recent_trades[selected_trade_idx]
        
        # Display trade details
        st.subheader("Trade Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            action_color = "green" if selected_trade['action'] == "BUY" else "red" if selected_trade['action'] == "SELL" else "orange"
            st.markdown(f"""
            <h3 style='color: {action_color};'>{selected_trade['action']} {selected_trade['stock']}</h3>
            """, unsafe_allow_html=True)
            
            st.write(f"Entry Price: ₹{selected_trade['entry_price']:.2f}")
            st.write(f"Stop Loss: ₹{selected_trade['stop_loss']:.2f}")
            st.write(f"Take Profit: ₹{selected_trade['take_profit']:.2f}")
            st.write(f"Order Type: {selected_trade['order_type']}")
            
        with col2:
            st.subheader("Risk Analysis")
            st.progress(selected_trade['confidence']/10, text=f"Confidence: {selected_trade['confidence']}/10")
            st.progress(selected_trade['risk_score']/10, text=f"Risk Score: {selected_trade['risk_score']}/10")
        
        st.info(selected_trade['reasoning'])
        
        # Execute button
        if st.button("Execute Trade"):
            with st.spinner("Executing trade..."):
                success, message = execute_trade(selected_trade)
                
                if success:
                    st.success(message)
                    
                    # Add execution status to trade history
                    selected_trade['executed'] = True
                    selected_trade['execution_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    selected_trade['execution_status'] = message
                    
                    # Update in history
                    st.session_state.trade_history[-(len(recent_trades) - selected_trade_idx)] = selected_trade
                else:
                    st.error(message)

# Bot Settings Page
elif page == "Bot Settings":
    st.header("Bot Configuration")
    
    st.subheader("API Settings")
    
    # Getting current values
    current_client = os.getenv('CLIENT', '')
    current_token = os.getenv('TOKEN', '')
    current_api_key = os.getenv('API_KEY', '')
    
    with st.form("api_settings"):
        client_id = st.text_input("Dhan Client ID", value=current_client)
        token = st.text_input("Dhan Access Token", value=current_token, type="password")
        api_key = st.text_input("Krutrim API Key", value=current_api_key, type="password")
        
        if st.form_submit_button("Save API Settings"):
            # In a real app, you would save these to .env or a secure config
            # For this example, we'll just acknowledge the input
            st.success("API settings saved! (Note: In a production app, these would be securely stored)")
    
    st.divider()
    
    st.subheader("Watchlist Configuration")
    
    # Edit watchlist
    watchlist_input = st.text_input("Watchlist (comma-separated)", value=",".join(WATCHLIST))
    
    if st.button("Update Watchlist"):
        new_watchlist = [s.strip() for s in watchlist_input.split(",")]
        st.success(f"Watchlist updated to: {new_watchlist}")
        # In a real app, you would save this to config
    
    st.divider()
    
    st.subheader("Auto-Execution Settings")
    
    # Trading parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.toggle("Enable Auto-Execution", value=st.session_state.auto_execute, key="auto_exec_toggle")
        max_trades_per_day = st.number_input("Max Trades Per Day", min_value=1, max_value=20, value=5)
        
    with col2:
        min_confidence = st.slider("Minimum Confidence Score", min_value=1, max_value=10, value=7)
        max_risk = st.slider("Maximum Risk Score", min_value=1, max_value=10, value=5)
    
    if st.button("Save Auto-Execution Settings"):
        st.session_state.auto_execute = st.session_state.auto_exec_toggle
        st.success("Auto-execution settings saved!")

# Account Page
elif page == "Account":
    st.header("Account Overview")
    
    account_data = get_account_summary()
    
    if account_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Funds")
            # Format funds data for display
            if 'funds' in account_data and account_data['funds']:
                funds = account_data['funds']
                st.metric("Available Cash", f"₹{funds.get('limit', 0):,.2f}")
                st.metric("Margin Used", f"₹{funds.get('used', 0):,.2f}")
                st.metric("Net Balance", f"₹{funds.get('net', 0):,.2f}")
            else:
                st.warning("Fund data not available")
        
        with col2:
            st.subheader("Portfolio Summary")
            # Format holdings summary
            if 'holdings' in account_data and account_data['holdings']:
                holdings = account_data['holdings']
                total_investment = sum(h.get('buyAvg', 0) * h.get('quantity', 0) for h in holdings)
                current_value = sum(h.get('ltp', 0) * h.get('quantity', 0) for h in holdings)
                profit_loss = current_value - total_investment
                pl_percent = (profit_loss / total_investment * 100) if total_investment else 0
                
                st.metric("Total Investment", f"₹{total_investment:,.2f}")
                st.metric("Current Value", f"₹{current_value:,.2f}")
                st.metric("Profit/Loss", f"₹{profit_loss:,.2f} ({pl_percent:.2f}%)", 
                         delta=f"{pl_percent:.2f}%")
            else:
                st.warning("Holdings data not available")
        
        # Positions Table
        st.subheader("Current Positions")
        if 'positions' in account_data and account_data['positions']:
            positions = account_data['positions']
            positions_df = pd.DataFrame(positions)
            
            if not positions_df.empty:
                st.dataframe(positions_df)
            else:
                st.info("No active positions")
        else:
            st.info("No positions data available")
        
        # Holdings Table
        st.subheader("Holdings")
        if 'holdings' in account_data and account_data['holdings']:
            holdings = account_data['holdings']
            holdings_df = pd.DataFrame(holdings)
            
            if not holdings_df.empty:
                st.dataframe(holdings_df)
            else:
                st.info("No holdings")
        else:
            st.info("No holdings data available")
    
    else:
        st.error("Unable to fetch account information. Please check API settings.")

# Footer
st.divider()
st.caption("Trading Bot Dashboard | © 2025 | Disclaimer: Use at your own risk. Trading involves risks. Past performance does not guarantee future results.")