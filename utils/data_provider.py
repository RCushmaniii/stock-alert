"""
Data Provider - yfinance wrapper for stock price fetching
Centralizes all external API calls for better maintainability
"""

import yfinance as yf


class DataProvider:
    """Wrapper for yfinance API calls with error handling"""
    
    @staticmethod
    def get_current_price(symbol):
        """
        Fetch current stock price using yfinance
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            float: Current stock price or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Method 1: Use fast_info for current price (most reliable)
            try:
                current_price = ticker.fast_info.get('lastPrice')
                if current_price and current_price > 0:
                    return float(current_price)
            except:
                pass
            
            # Method 2: Try intraday data with 2-minute interval
            try:
                data = ticker.history(period="1d", interval="2m")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    return float(current_price)
            except:
                pass
            
            # Method 3: Try regular daily data
            try:
                data = ticker.history(period="1d")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    return float(current_price)
            except:
                pass
            
            # Method 4: Get latest close from recent history
            try:
                data = ticker.history(period="5d")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    return float(current_price)
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching price for {symbol}: {e}")
            return None
    
    @staticmethod
    def validate_symbol(symbol):
        """
        Validate if a stock symbol exists
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            bool: True if symbol is valid
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'symbol' in info or 'shortName' in info
        except:
            return False
