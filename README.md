# 🤖 Autonomous Trading Bot

A Python-based trading bot that uses AI to analyze market data and execute trades on Indian stocks. Built with a Streamlit dashboard for easy monitoring and control.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Dhan trading account (if you want to integrate with any other broker you can do so with minimal changes)
- Krutrim Cloud API access

### Quick Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/Shashwat-Akhilesh-Shukla/AutoTrader
   cd AutoTrader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file:
   ```
   CLIENT=your_dhan_client_id
   TOKEN=your_dhan_access_token
   API_KEY=your_krutrim_api_key
   DATABASE_URL=postgresql://username:password@localhost:5432/trading_data
   ```

4. Run the dashboard:
   ```bash
   streamlit run app.py
   ```

## 🔧 How It Works

This trading bot combines market data, AI analysis, and automated execution:

1. **Market Data**: Fetches OHLCV data from TradingView for stocks on your watchlist
2. **Database Storage**: Stores market data in PostgreSQL for analysis and backtesting
3. **AI Analysis**: Uses DeepSeek model via Krutrim Cloud to analyze patterns and generate trade signals
4. **Trade Execution**: Executes trades via Dhan's API with risk management

## 🖥️ Dashboard Features

### Dashboard
- Market overview with key indices
- Watchlist performance summary
- Bot connection status
- Auto-execution toggle
- Recent trade signals

### Market Data
- Interactive stock charts (candlestick patterns)
- Technical indicators (SMA 20, SMA 50)
- Manual data refresh controls
- Recent price data table

### Trade Signals
- AI-generated buy/sell recommendations
- Entry price, stop loss, and take profit levels
- Risk and confidence scores
- Signal history tracking

### Trade Execution
- Manual execution of generated signals
- Risk assessment before execution
- Execution status tracking

### Bot Settings
- API configuration
- Watchlist management
- Auto-execution parameters
- Risk management settings

### Account
- Funds overview
- Portfolio summary
- Active positions tracking
- Holdings summary

## 🔨 Customizing Your Setup

### Adding New Stocks

Edit the `WATCHLIST` and `SEC_DICT` variables in the code to add new stocks:

```python
WATCHLIST = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "SBIN", "YOUR_NEW_STOCK"]
SEC_DICT = {
    'RELIANCE':'500325', 
    'HDFCBANK':'1333', 
    'INFY': '500209', 
    'SBIN':'3045', 
    'TCS': '11536',
    'YOUR_NEW_STOCK': 'SECURITY_ID'
}
```

### Modifying the AI Prompt

The AI analysis can be customized by editing the `generate_trading_prompt()` function to include additional indicators or different analysis parameters.

## 📝 TO-DO

- [ ] Add backtesting functionality
- [ ] Implement more technical indicators
- [ ] Add email/SMS notifications for trade signals
- [ ] Create historical performance tracking
- [ ] Add portfolio optimization suggestions

## 🤝 Contributing

Contributions welcome! Feel free to submit PRs or open issues.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

Questions or feedback? Reach shashwatakhileshshukla@gmail.com
