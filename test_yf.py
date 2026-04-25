import yfinance as yf
print(yf.download('TCS.NS', period='100d', interval='1d', progress=False).head())
