import yfinance as yf

print("Fetching AAPL data...")
data = yf.Ticker("AAPL")
info = data.fast_info
print("Current price:", info.get("lastPrice"))
