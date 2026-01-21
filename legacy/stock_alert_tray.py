"""
StockAlert - Background Tray Version
Runs invisibly in system tray, only active during market hours
"""

import time
import json
import os
import shutil
import threading
from datetime import datetime
from winotify import Notification, audio
from utils.data_provider import DataProvider
from utils.market_hours import MarketHours
import pystray
from PIL import Image
import sys


class StockMonitor:
    """Monitors a single stock with configurable thresholds"""
    
    def __init__(self, ticker_config, global_settings, icon_path=None):
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
        return self.data_provider.get_current_price(self.symbol)
    
    def should_alert(self):
        if self.last_alert_time is None:
            return True
        
        time_since_last_alert = time.time() - self.last_alert_time
        return time_since_last_alert >= self.cooldown_period
    
    def send_notification(self, price, threshold_type):
        if not self.notifications_enabled:
            return
        
        if threshold_type == "high":
            title = f"🔺 {self.symbol} High Alert"
            message = f"{self.name} reached ${price:.2f} (threshold: ${self.high_threshold:.2f})"
        else:
            title = f"🔻 {self.symbol} Low Alert"
            message = f"{self.name} dropped to ${price:.2f} (threshold: ${self.low_threshold:.2f})"
        
        toast = Notification(
            app_id="StockAlert",
            title=title,
            msg=message,
            duration="long",
            icon=self.icon_path
        )
        
        toast.set_audio(audio.Default, loop=False)
        toast.add_actions(label="View Chart", launch=f"https://finance.yahoo.com/quote/{self.symbol}")
        toast.show()
        
        self.last_alert_time = time.time()
    
    def check_thresholds(self, current_price):
        if current_price >= self.high_threshold:
            if self.should_alert():
                self.send_notification(current_price, "high")
                return True
        elif current_price <= self.low_threshold:
            if self.should_alert():
                self.send_notification(current_price, "low")
                return True
        return False


class StockAlertTray:
    """Background stock monitoring with system tray icon"""
    
    def __init__(self, config_path='config.json', icon_path='stock_alert.ico'):
        self.config_path = config_path
        self.icon_path = icon_path if os.path.exists(icon_path) else None
        self.config = self.load_config()
        self.monitors = []
        self.market_hours = MarketHours()
        self.running = False
        self.monitoring_thread = None
        self.tray_icon = None
        
        self.initialize_monitors()
    
    def load_config(self):
        if not os.path.exists(self.config_path):
            if os.path.exists('config.example.json'):
                shutil.copy('config.example.json', self.config_path)
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        self.validate_config(config)
        return config
    
    def validate_config(self, config):
        required_settings = ['check_interval', 'cooldown', 'notifications_enabled']
        required_ticker_fields = ['symbol', 'high_threshold', 'low_threshold']
        
        if 'settings' not in config:
            raise ValueError("Config missing 'settings' section")
        
        for field in required_settings:
            if field not in config['settings']:
                raise ValueError(f"Config missing required setting: {field}")
        
        if 'tickers' not in config:
            raise ValueError("Config missing 'tickers' section")
    
    def initialize_monitors(self):
        settings = self.config['settings']
        tickers = self.config['tickers']
        
        for ticker in tickers:
            if ticker.get('enabled', True):
                monitor = StockMonitor(ticker, settings, self.icon_path)
                self.monitors.append(monitor)
    
    def get_tray_icon_image(self):
        """Load or create tray icon image"""
        if self.icon_path and os.path.exists(self.icon_path):
            try:
                return Image.open(self.icon_path)
            except:
                pass
        
        # Create a simple colored square if no icon
        img = Image.new('RGB', (64, 64), color=(0, 120, 212))
        return img
    
    def create_tray_menu(self):
        """Create system tray menu"""
        return pystray.Menu(
            pystray.MenuItem("StockAlert", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda text: f"Market: {self.market_hours.get_market_status_message()[:20]}...",
                lambda: None,
                enabled=False
            ),
            pystray.MenuItem(
                lambda text: f"Monitoring: {len(self.monitors)} stocks",
                lambda: None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Configuration", self.open_config_editor),
            pystray.MenuItem("Reload Config", self.reload_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_app)
        )
    
    def open_config_editor(self):
        """Launch the configuration GUI"""
        import subprocess
        config_editor_path = os.path.join(os.path.dirname(__file__), "StockAlertConfig.exe")
        if os.path.exists(config_editor_path):
            subprocess.Popen([config_editor_path])
        else:
            # Fallback to Python script
            subprocess.Popen(["python", "config_editor.py"])
    
    def reload_config(self):
        """Reload configuration without restarting"""
        try:
            self.config = self.load_config()
            self.monitors = []
            self.initialize_monitors()
            self.show_notification("Configuration Reloaded", f"Now monitoring {len(self.monitors)} stocks")
        except Exception as e:
            self.show_notification("Config Error", f"Failed to reload: {str(e)}")
    
    def show_notification(self, title, message):
        """Show a system notification"""
        toast = Notification(
            app_id="StockAlert",
            title=title,
            msg=message,
            icon=self.icon_path
        )
        toast.show()
    
    def quit_app(self):
        """Stop monitoring and quit"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
    
    def monitoring_loop(self):
        """Main monitoring loop - only runs during market hours"""
        retry_counts = {monitor.symbol: 0 for monitor in self.monitors}
        max_retries = 3
        
        while self.running:
            try:
                # Check if market is open
                if not self.market_hours.is_market_open():
                    # Market is closed - sleep until it opens
                    seconds_until_open = self.market_hours.seconds_until_market_open()
                    
                    # Log to a file since we're running in background
                    self.log(f"Market closed. Sleeping for {seconds_until_open//3600}h {(seconds_until_open%3600)//60}m")
                    
                    # Sleep in chunks to allow for clean shutdown
                    sleep_chunk = min(300, seconds_until_open)  # 5 min chunks
                    elapsed = 0
                    while elapsed < seconds_until_open and self.running:
                        time.sleep(sleep_chunk)
                        elapsed += sleep_chunk
                    
                    continue
                
                # Market is open - check prices
                for monitor in self.monitors:
                    if not monitor.enabled or not self.running:
                        continue
                    
                    price = monitor.get_current_price()
                    
                    if price is not None:
                        self.log(f"{monitor.symbol}: ${price:.2f}")
                        monitor.check_thresholds(price)
                        retry_counts[monitor.symbol] = 0
                    else:
                        retry_counts[monitor.symbol] += 1
                        if retry_counts[monitor.symbol] >= max_retries:
                            self.log(f"[{monitor.symbol}] Failed to fetch price {max_retries} times")
                            retry_counts[monitor.symbol] = 0
                
                time.sleep(self.config['settings']['check_interval'])
                
            except Exception as e:
                self.log(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def log(self, message):
        """Log message to file (since we're running in background)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Optional: Write to log file
        # Uncomment if you want file logging
        # with open("stockalert.log", "a") as f:
        #     f.write(log_message)
        
        # For now, just print (won't be visible in tray mode)
        print(log_message, end='')
    
    def run(self):
        """Start the system tray application"""
        if not self.monitors:
            self.show_notification("StockAlert Error", "No enabled tickers in configuration")
            return
        
        self.running = True
        
        # Start monitoring in background thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Show startup notification
        market_status = self.market_hours.get_market_status_message()
        self.show_notification(
            "StockAlert Started",
            f"Monitoring {len(self.monitors)} stocks\n{market_status}"
        )
        
        # Create and run system tray icon
        icon_image = self.get_tray_icon_image()
        self.tray_icon = pystray.Icon(
            "StockAlert",
            icon_image,
            "StockAlert - Market Hours Monitor",
            menu=self.create_tray_menu()
        )
        
        self.tray_icon.run()


def main():
    """Entry point for tray version"""
    try:
        # Change to the directory where the executable is located
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        os.chdir(app_dir)
        
        # Auto-create config if needed
        if not os.path.exists('config.json'):
            if os.path.exists('config.example.json'):
                shutil.copy('config.example.json', 'config.json')
        
        app = StockAlertTray(config_path='config.json')
        app.run()
    except Exception as e:
        # Show error notification
        toast = Notification(
            app_id="StockAlert",
            title="StockAlert Error",
            msg=f"Failed to start: {str(e)}"
        )
        toast.show()
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
