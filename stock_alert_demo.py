"""
StockAlert - Phase 1 MVP (Demo Mode)
Single-stock monitoring with Windows Toast notifications
Uses simulated price data for testing when Yahoo Finance is unavailable
"""

import time
import random
from win10toast import ToastNotifier
from datetime import datetime


class StockAlertDemo:
    """Core stock monitoring and alert system with demo mode"""
    
    def __init__(self, symbol, high_threshold, low_threshold, check_interval=60, demo_mode=True):
        """
        Initialize stock alert monitor
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            high_threshold: Price threshold for upward alert
            low_threshold: Price threshold for downward alert
            check_interval: Seconds between price checks (default: 60)
            demo_mode: Use simulated prices for testing (default: True)
        """
        self.symbol = symbol.upper()
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.check_interval = check_interval
        self.demo_mode = demo_mode
        self.toaster = ToastNotifier()
        self.last_alert_time = None
        self.cooldown_period = 300  # 5 minutes between alerts
        
        # Demo mode settings
        self.base_price = 256.83  # Starting price for AAPL
        self.price_volatility = 0.5  # Price can move +/- $0.50 per check
        
    def get_current_price(self):
        """
        Fetch current stock price (simulated in demo mode)
        
        Returns:
            float: Current stock price or None if error
        """
        if self.demo_mode:
            # Simulate realistic price movement
            change = random.uniform(-self.price_volatility, self.price_volatility)
            self.base_price += change
            
            # Keep price in reasonable range
            self.base_price = max(250.0, min(265.0, self.base_price))
            
            return round(self.base_price, 2)
        else:
            # Real API implementation would go here
            try:
                import yfinance as yf
                import requests
                
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                ticker = yf.Ticker(self.symbol, session=session)
                data = ticker.history(period="1d")
                
                if not data.empty:
                    return float(data['Close'].iloc[-1])
                else:
                    print(f"⚠️  No data available for {self.symbol}")
                    return None
                    
            except Exception as e:
                print(f"❌ Error fetching price for {self.symbol}: {e}")
                return None
    
    def should_alert(self):
        """
        Check if enough time has passed since last alert (cooldown)
        
        Returns:
            bool: True if alert can be sent
        """
        if self.last_alert_time is None:
            return True
            
        elapsed = time.time() - self.last_alert_time
        return elapsed >= self.cooldown_period
    
    def send_alert(self, alert_type, price):
        """
        Send Windows Toast notification
        
        Args:
            alert_type: 'high' or 'low'
            price: Current stock price
        """
        if not self.should_alert():
            remaining = self.cooldown_period - (time.time() - self.last_alert_time)
            print(f"⏳ Cooldown active. {remaining:.0f}s remaining")
            return
        
        if alert_type == 'high':
            title = "📈 Stock Alert - Price High"
            message = f"{self.symbol} reached ${price:.2f} (threshold: ${self.high_threshold:.2f})"
        else:
            title = "📉 Stock Alert - Price Low"
            message = f"{self.symbol} dropped to ${price:.2f} (threshold: ${self.low_threshold:.2f})"
        
        try:
            self.toaster.show_toast(
                title,
                message,
                duration=10,
                threaded=True
            )
            self.last_alert_time = time.time()
            print(f"🔔 Alert sent: {message}")
            
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
    
    def check_thresholds(self, price):
        """
        Check if price breaches thresholds and trigger alerts
        
        Args:
            price: Current stock price
        """
        if price >= self.high_threshold:
            self.send_alert('high', price)
        elif price <= self.low_threshold:
            self.send_alert('low', price)
    
    def run(self):
        """Main monitoring loop"""
        mode_text = "DEMO MODE" if self.demo_mode else "LIVE MODE"
        print(f"🚀 Starting StockAlert for {self.symbol} ({mode_text})")
        print(f"📊 High threshold: ${self.high_threshold:.2f}")
        print(f"📊 Low threshold: ${self.low_threshold:.2f}")
        print(f"⏱️  Check interval: {self.check_interval}s")
        
        if self.demo_mode:
            print(f"💡 Demo mode: Simulating price movements around ${self.base_price:.2f}")
            print(f"   Price will fluctuate ±${self.price_volatility} per check")
        
        print(f"{'='*50}\n")
        
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                price = self.get_current_price()
                
                if price is not None:
                    print(f"[{timestamp}] {self.symbol}: ${price:.2f}")
                    self.check_thresholds(price)
                    retry_count = 0  # Reset retry counter on success
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"⚠️  Failed to fetch price {max_retries} times. Continuing to retry...")
                        retry_count = 0  # Reset to continue monitoring
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print(f"\n\n🛑 StockAlert stopped by user")
                break
                
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                retry_count += 1
                
                if retry_count >= max_retries:
                    print(f"⚠️  Multiple errors occurred. Waiting 60s before retry...")
                    time.sleep(60)
                    retry_count = 0
                else:
                    time.sleep(self.check_interval)


def main():
    """Entry point for Phase 1 MVP"""
    print("=" * 50)
    print("StockAlert - Phase 1 MVP Demo")
    print("=" * 50)
    print("\nℹ️  Yahoo Finance is currently rate-limiting requests.")
    print("   Running in DEMO MODE with simulated prices.\n")
    
    # Demo configuration for AAPL
    # Thresholds set to trigger alerts during simulation
    alert = StockAlertDemo(
        symbol="AAPL",
        high_threshold=257.5,  # Alert if price rises above $257.50
        low_threshold=256.0,   # Alert if price drops below $256.00
        check_interval=10,     # Check every 10 seconds for faster demo
        demo_mode=True
    )
    
    alert.run()


if __name__ == "__main__":
    main()
