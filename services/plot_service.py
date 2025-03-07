import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from services.data_service import get_data_from_db

def plot_stock_data(symbol: str) -> None:
    df = get_data_from_db(symbol)
    if df is None or df.empty:
        st.warning(f"No data available for {symbol}")
        return
    
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                       vertical_spacing=0.1, subplot_titles=(f'{symbol} Price', 'Volume'), 
                       row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Candlestick(x=df['datetime'],
                                open=df['open'],
                                high=df['high'],
                                low=df['low'],
                                close=df['close'],
                                name='OHLC'),
                 row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['sma_20'], 
                           line=dict(color='blue', width=1),
                           name='SMA 20'),
                 row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['sma_50'], 
                           line=dict(color='orange', width=1),
                           name='SMA 50'),
                 row=1, col=1)
    
    fig.add_trace(go.Bar(x=df['datetime'], y=df['volume'], name='Volume', marker_color='rgba(0,0,250,0.3)'),
                 row=2, col=1)
    
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    st.plotly_chart(fig, use_container_width=True)