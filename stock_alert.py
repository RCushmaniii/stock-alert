"""
StockAlert - Phase 2
Multi-stock monitoring with JSON configuration and Windows Toast notifications
"""

import time
import json
import os
from winotify import Notification, audio
from datetime import datetime
from utils.data_provider import DataProvider


class StockMonitor:
    """Monitors a single stock with configurable thresholds"""
    
    def __init__(self, ticker_config, global_settings, icon_path=None):
        """
        Initialize stock monitor for a single ticker
        
        Args:
            ticker_config: Dictionary with symbol, name, thresholds, enabled
            global_settings: Dictionary with check_interval, cooldown, notifications_enabled
            icon_path: Path to notification icon
        """
        self.symbol = ticker_config['symbol'].upper()
        self.name = ticker_config.get('name', self.symbol)
        self.high_threshold = ticker_config['high_threshold']
        self.low_threshold = ticker_config['low_threshold']
        self.enabled = ticker_config.get('enabled', True)
        
        self.check_interval = global_settings['check_interval']
        self.cooldown_period = global_settings['cooldown']
        self.notifications_enabled = global_settings['notifications_enabled']
        
        self.last_alert_time = None
        self.icon_path = icon_path
        self.data_provider = DataProvider()
    
    def get_current_price(self):
        """
        Fetch current stock price using data provider
        
        Returns:
            float: Current stock price or None if error
        """
        return self.data_provider.get_current_price(self.symbol)
    
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
        if not self.notifications_enabled:
            print(f"🔕 Notifications disabled for {self.symbol}")
            return
            
        if not self.should_alert():
            remaining = self.cooldown_period - (time.time() - self.last_alert_time)
            print(f"⏳ [{self.symbol}] Cooldown active. {remaining:.0f}s remaining")
            return
        
        if alert_type == 'high':
            title = f"📈 Stock Alert - {self.name}"
            message = f"{self.symbol} reached ${price:.2f} (threshold: ${self.high_threshold:.2f})"
        else:
            title = f"📉 Stock Alert - {self.name}"
            message = f"{self.symbol} dropped to ${price:.2f} (threshold: ${self.low_threshold:.2f})"
        
        try:
            toast = Notification(
                app_id="Stock Alert",
                title=title,
                msg=message,
                duration="long",
                icon=self.icon_path
            )
            
            toast.set_audio(audio.Default, loop=False)
            
            toast.add_actions(
                label="View Chart",
                launch=f"https://finance.yahoo.com/quote/{self.symbol}"
            )
            
            toast.show()
            
            self.last_alert_time = time.time()
            print(f"🔔 [{self.symbol}] Alert sent: {message}")
            
        except Exception as e:
            print(f"❌ [{self.symbol}] Failed to send notification: {e}")
    
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


class StockAlert:
    """Multi-stock alert system with JSON configuration"""
    
    def __init__(self, config_path='config.json'):
        """
        Initialize multi-stock alert system
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.monitors = []
        self.icon_path = self.get_icon_path()
        self.initialize_monitors()
    
    def get_icon_path(self):
        """Get path to notification icon"""
        icon_path = os.path.join(os.path.dirname(__file__), 'stock_alert.ico')
        if os.path.exists(icon_path):
            return icon_path
        
        # Try assets folder
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            return icon_path
            
        return None
    
    def load_config(self):
        """
        Load configuration from JSON file
        
        Returns:
            dict: Configuration dictionary
        """
        try:
            if not os.path.exists(self.config_path):
                print(f"⚠️  Config file not found: {self.config_path}")
                print(f"📝 Creating default config from config.example.json...")
                
                example_path = 'config.example.json'
                if os.path.exists(example_path):
                    with open(example_path, 'r') as f:
                        config = json.load(f)
                    
                    with open(self.config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    print(f"✅ Created {self.config_path}")
                    return config
                else:
                    raise FileNotFoundError(f"Neither {self.config_path} nor {example_path} found")
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.validate_config(config)
            return config
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {self.config_path}: {e}")
            raise
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            raise
    
    def validate_config(self, config):
        """
        Validate configuration structure
        
        Args:
            config: Configuration dictionary
        """
        required_settings = ['check_interval', 'cooldown', 'notifications_enabled']
        required_ticker_fields = ['symbol', 'high_threshold', 'low_threshold']
        
        if 'settings' not in config:
            raise ValueError("Config missing 'settings' section")
        
        for field in required_settings:
            if field not in config['settings']:
                raise ValueError(f"Config missing required setting: {field}")
        
        if 'tickers' not in config:
            raise ValueError("Config missing 'tickers' section")
        
        if not isinstance(config['tickers'], list):
            raise ValueError("'tickers' must be a list")
        
        for idx, ticker in enumerate(config['tickers']):
            for field in required_ticker_fields:
                if field not in ticker:
                    raise ValueError(f"Ticker {idx} missing required field: {field}")
    
    def initialize_monitors(self):
        """Create StockMonitor instances for each enabled ticker"""
        settings = self.config['settings']
        tickers = self.config['tickers']
        
        for ticker in tickers:
            if ticker.get('enabled', True):
                monitor = StockMonitor(ticker, settings, self.icon_path)
                self.monitors.append(monitor)
        
        if not self.monitors:
            print("⚠️  No enabled tickers found in configuration")
    
    def run(self):
        """Main monitoring loop for all stocks"""
        if not self.monitors:
            print("❌ No stocks to monitor. Please enable tickers in config.json")
            return
        
        print(f"🚀 Starting StockAlert - Phase 2")
        print(f"📊 Monitoring {len(self.monitors)} stock(s)")
        print(f"⏱️  Check interval: {self.config['settings']['check_interval']}s")
        print(f"⏳ Cooldown period: {self.config['settings']['cooldown']}s")
        print(f"{'='*60}\n")
        
        for monitor in self.monitors:
            print(f"  • {monitor.symbol} ({monitor.name})")
            print(f"    High: ${monitor.high_threshold:.2f} | Low: ${monitor.low_threshold:.2f}")
        
        print(f"\n{'='*60}\n")
        
        retry_counts = {monitor.symbol: 0 for monitor in self.monitors}
        max_retries = 3
        
        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for monitor in self.monitors:
                    if not monitor.enabled:
                        continue
                    
                    price = monitor.get_current_price()
                    
                    if price is not None:
                        print(f"[{timestamp}] {monitor.symbol}: ${price:.2f}")
                        monitor.check_thresholds(price)
                        retry_counts[monitor.symbol] = 0
                    else:
                        retry_counts[monitor.symbol] += 1
                        if retry_counts[monitor.symbol] >= max_retries:
                            print(f"⚠️  [{monitor.symbol}] Failed to fetch price {max_retries} times")
                            retry_counts[monitor.symbol] = 0
                
                time.sleep(self.config['settings']['check_interval'])
                
            except KeyboardInterrupt:
                print(f"\n\n🛑 StockAlert stopped by user")
                break
                
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(60)


def main():
    """Entry point for Phase 2"""
    try:
        alert = StockAlert(config_path='config.json')
        alert.run()
    except Exception as e:
        print(f"❌ Failed to start StockAlert: {e}")
        print(f"\n💡 Make sure config.json exists and is valid")
        print(f"   You can copy config.example.json to config.json to get started")


if __name__ == "__main__":
    main()