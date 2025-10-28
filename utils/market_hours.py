"""
Market hours detection and US stock market holiday calendar
"""

from datetime import datetime, time
import pytz


# US Stock Market Holidays (2024-2026)
# Source: NYSE Holiday Calendar
US_MARKET_HOLIDAYS = [
    # 2024
    "2024-01-01",  # New Year's Day
    "2024-01-15",  # Martin Luther King Jr. Day
    "2024-02-19",  # Presidents' Day
    "2024-03-29",  # Good Friday
    "2024-05-27",  # Memorial Day
    "2024-06-19",  # Juneteenth
    "2024-07-04",  # Independence Day
    "2024-09-02",  # Labor Day
    "2024-11-28",  # Thanksgiving
    "2024-12-25",  # Christmas
    
    # 2025
    "2025-01-01",  # New Year's Day
    "2025-01-20",  # Martin Luther King Jr. Day
    "2025-02-17",  # Presidents' Day
    "2025-04-18",  # Good Friday
    "2025-05-26",  # Memorial Day
    "2025-06-19",  # Juneteenth
    "2025-07-04",  # Independence Day
    "2025-09-01",  # Labor Day
    "2025-11-27",  # Thanksgiving
    "2025-12-25",  # Christmas
    
    # 2026
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # Martin Luther King Jr. Day
    "2026-02-16",  # Presidents' Day
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-06-19",  # Juneteenth
    "2026-07-03",  # Independence Day (observed)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas
]


class MarketHours:
    """Utility class for checking US stock market hours"""
    
    # Market hours in Eastern Time
    MARKET_OPEN = time(9, 30)   # 9:30 AM ET
    MARKET_CLOSE = time(16, 0)  # 4:00 PM ET
    
    # Pre-market and after-hours (optional)
    PREMARKET_OPEN = time(4, 0)    # 4:00 AM ET
    AFTERHOURS_CLOSE = time(20, 0) # 8:00 PM ET
    
    def __init__(self):
        self.eastern = pytz.timezone('US/Eastern')
    
    def is_market_open(self, include_extended_hours=False):
        """
        Check if the market is currently open
        
        Args:
            include_extended_hours: Include pre-market and after-hours
            
        Returns:
            bool: True if market is open, False otherwise
        """
        now_et = datetime.now(self.eastern)
        
        # Check if it's a weekend
        if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        
        # Check if it's a holiday
        if self.is_market_holiday(now_et):
            return False
        
        current_time = now_et.time()
        
        if include_extended_hours:
            # Pre-market to after-hours
            return self.PREMARKET_OPEN <= current_time <= self.AFTERHOURS_CLOSE
        else:
            # Regular market hours only
            return self.MARKET_OPEN <= current_time < self.MARKET_CLOSE
    
    def is_market_holiday(self, date=None):
        """
        Check if a given date is a market holiday
        
        Args:
            date: datetime object (defaults to today)
            
        Returns:
            bool: True if it's a market holiday
        """
        if date is None:
            date = datetime.now(self.eastern)
        
        date_str = date.strftime("%Y-%m-%d")
        return date_str in US_MARKET_HOLIDAYS
    
    def seconds_until_market_open(self):
        """
        Calculate seconds until next market open
        
        Returns:
            int: Seconds until market opens (0 if already open)
        """
        if self.is_market_open():
            return 0
        
        now_et = datetime.now(self.eastern)
        
        # If it's during market hours today but market is closed (holiday)
        if (now_et.weekday() < 5 and 
            now_et.time() < self.MARKET_CLOSE and
            self.is_market_holiday(now_et)):
            # Skip to next trading day
            return self._seconds_to_next_trading_day(now_et)
        
        # If it's before market open today
        if now_et.weekday() < 5 and now_et.time() < self.MARKET_OPEN:
            if not self.is_market_holiday(now_et):
                # Market opens later today
                market_open_today = now_et.replace(
                    hour=self.MARKET_OPEN.hour,
                    minute=self.MARKET_OPEN.minute,
                    second=0,
                    microsecond=0
                )
                return int((market_open_today - now_et).total_seconds())
        
        # Otherwise, wait for next trading day
        return self._seconds_to_next_trading_day(now_et)
    
    def _seconds_to_next_trading_day(self, current_time):
        """Calculate seconds to next trading day's market open"""
        from datetime import timedelta
        
        next_day = current_time + timedelta(days=1)
        next_day = next_day.replace(
            hour=self.MARKET_OPEN.hour,
            minute=self.MARKET_OPEN.minute,
            second=0,
            microsecond=0
        )
        
        # Keep advancing until we find a trading day
        max_attempts = 10  # Prevent infinite loop
        attempts = 0
        
        while (next_day.weekday() >= 5 or self.is_market_holiday(next_day)) and attempts < max_attempts:
            next_day += timedelta(days=1)
            attempts += 1
        
        return int((next_day - current_time).total_seconds())
    
    def get_market_status_message(self):
        """
        Get a human-readable market status message
        
        Returns:
            str: Status message
        """
        now_et = datetime.now(self.eastern)
        
        if self.is_market_open():
            return f"✅ Market is OPEN (closes at {self.MARKET_CLOSE.strftime('%I:%M %p')} ET)"
        
        if now_et.weekday() >= 5:
            return "📅 Market is CLOSED (weekend)"
        
        if self.is_market_holiday(now_et):
            return "🎉 Market is CLOSED (holiday)"
        
        if now_et.time() < self.MARKET_OPEN:
            return f"⏰ Market opens at {self.MARKET_OPEN.strftime('%I:%M %p')} ET"
        
        if now_et.time() >= self.MARKET_CLOSE:
            return "🌙 Market is CLOSED (after hours)"
        
        return "❓ Market status unknown"


def main():
    """Test market hours detection"""
    market = MarketHours()
    
    print("Market Hours Utility Test")
    print("=" * 50)
    print(f"Current time (ET): {datetime.now(market.eastern).strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
    print(f"Status: {market.get_market_status_message()}")
    print(f"Is market open? {market.is_market_open()}")
    
    if not market.is_market_open():
        seconds = market.seconds_until_market_open()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        print(f"Time until market opens: {hours}h {minutes}m")


if __name__ == "__main__":
    main()
