"""
Debug script to test yfinance API methods
"""
import yfinance as yf

print("Testing yfinance with AAPL...\n")

ticker = yf.Ticker("AAPL")

# Test 1: Basic info
print("=" * 50)
print("Test 1: ticker.info")
print("=" * 50)
try:
    info = ticker.info
    print(f"✅ Success! Current Price from info: ${info.get('currentPrice', 'N/A')}")
    print(f"   Regular Market Price: ${info.get('regularMarketPrice', 'N/A')}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 2: fast_info
print("\n" + "=" * 50)
print("Test 2: ticker.fast_info")
print("=" * 50)
try:
    fast_info = ticker.fast_info
    print(f"✅ Success! Last Price: ${fast_info.get('lastPrice', 'N/A')}")
    print(f"   Available keys: {list(fast_info.keys())}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 3: history with 1 minute interval
print("\n" + "=" * 50)
print("Test 3: ticker.history(period='1d', interval='1m')")
print("=" * 50)
try:
    data = ticker.history(period="1d", interval="1m")
    if not data.empty:
        print(f"✅ Success! Latest price: ${data['Close'].iloc[-1]:.2f}")
        print(f"   Data points: {len(data)}")
        print(f"   Latest timestamp: {data.index[-1]}")
    else:
        print("⚠️  Data is empty")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 4: history with 1 day period (no interval)
print("\n" + "=" * 50)
print("Test 4: ticker.history(period='1d')")
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

# Test 5: history with 5 days
print("\n" + "=" * 50)
print("Test 5: ticker.history(period='5d')")
print("=" * 50)
try:
    data = ticker.history(period="5d")
    if not data.empty:
        print(f"✅ Success! Latest price: ${data['Close'].iloc[-1]:.2f}")
        print(f"   Data points: {len(data)}")
    else:
        print("⚠️  Data is empty")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 6: Using yf.download
print("\n" + "=" * 50)
print("Test 6: yf.download('AAPL', period='1d')")
print("=" * 50)
try:
    data = yf.download("AAPL", period="1d", progress=False)
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
