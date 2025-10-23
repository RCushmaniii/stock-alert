"""
Test yfinance with custom session to bypass rate limiting
"""
import yfinance as yf
import requests

# Configure session with proper headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

print("Testing yfinance with custom session...\n")

ticker = yf.Ticker("AAPL", session=session)

print("=" * 50)
print("Test 1: ticker.fast_info")
print("=" * 50)
try:
    fast_info = ticker.fast_info
    last_price = fast_info.get('lastPrice')
    print(f"✅ Success! Last Price: ${last_price}")
    print(f"   Previous Close: ${fast_info.get('previousClose')}")
    print(f"   Open: ${fast_info.get('open')}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "=" * 50)
print("Test 2: ticker.history(period='1d', interval='2m')")
print("=" * 50)
try:
    data = ticker.history(period="1d", interval="2m")
    if not data.empty:
        print(f"✅ Success! Latest price: ${data['Close'].iloc[-1]:.2f}")
        print(f"   Data points: {len(data)}")
        print(f"   Latest 3 prices:")
        for i in range(min(3, len(data))):
            idx = -(i+1)
            print(f"     {data.index[idx]}: ${data['Close'].iloc[idx]:.2f}")
    else:
        print("⚠️  Data is empty")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "=" * 50)
print("Test 3: ticker.history(period='1d')")
print("=" * 50)
try:
    data = ticker.history(period="1d")
    if not data.empty:
        print(f"✅ Success! Latest price: ${data['Close'].iloc[-1]:.2f}")
        print(f"   Data points: {len(data)}")
    else:
        print("⚠️  Data is empty")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "=" * 50)
print("Testing complete!")
print("=" * 50)
