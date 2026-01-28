"""
Market hours detection and US stock market holiday calendar.

Provides utilities for checking if the US stock market is currently open,
calculating time until market opens, and detecting market holidays.

Holiday dates are generated algorithmically for any year.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from functools import lru_cache

import pytz

logger = logging.getLogger(__name__)


def _observe_holiday(d: date) -> date:
    """Adjust holiday for weekend observance (NYSE rules).

    If holiday falls on Saturday, observe on Friday.
    If holiday falls on Sunday, observe on Monday.

    Args:
        d: The actual holiday date

    Returns:
        The observed holiday date
    """
    if d.weekday() == 5:  # Saturday
        return d - timedelta(days=1)  # Observe on Friday
    elif d.weekday() == 6:  # Sunday
        return d + timedelta(days=1)  # Observe on Monday
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a month.

    Args:
        year: Year
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)
        n: Which occurrence (1=first, 2=second, etc.)

    Returns:
        The date of the nth weekday
    """
    first_day = date(year, month, 1)
    # Find first occurrence of weekday
    days_ahead = weekday - first_day.weekday()
    if days_ahead < 0:
        days_ahead += 7
    first_occurrence = first_day + timedelta(days=days_ahead)
    # Add weeks to get nth occurrence
    return first_occurrence + timedelta(weeks=n - 1)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Get the last occurrence of a weekday in a month.

    Args:
        year: Year
        month: Month (1-12)
        weekday: Weekday (0=Monday, 6=Sunday)

    Returns:
        The date of the last weekday
    """
    # Start from last day of month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Find last occurrence of weekday
    days_back = last_day.weekday() - weekday
    if days_back < 0:
        days_back += 7
    return last_day - timedelta(days=days_back)


def _easter_sunday(year: int) -> date:
    """Calculate Easter Sunday using the Anonymous Gregorian algorithm.

    Args:
        year: Year to calculate Easter for

    Returns:
        Date of Easter Sunday
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


@lru_cache(maxsize=20)
def get_market_holidays_for_year(year: int) -> frozenset[str]:
    """Generate all NYSE market holidays for a given year.

    Args:
        year: The year to generate holidays for

    Returns:
        Frozenset of holiday dates as "YYYY-MM-DD" strings
    """
    holidays = []

    # New Year's Day (January 1, observed)
    new_years = _observe_holiday(date(year, 1, 1))
    holidays.append(new_years)

    # Martin Luther King Jr. Day (3rd Monday in January)
    mlk_day = _nth_weekday(year, 1, 0, 3)  # 0=Monday
    holidays.append(mlk_day)

    # Presidents' Day (3rd Monday in February)
    presidents_day = _nth_weekday(year, 2, 0, 3)
    holidays.append(presidents_day)

    # Good Friday (Friday before Easter Sunday)
    easter = _easter_sunday(year)
    good_friday = easter - timedelta(days=2)
    holidays.append(good_friday)

    # Memorial Day (Last Monday in May)
    memorial_day = _last_weekday(year, 5, 0)
    holidays.append(memorial_day)

    # Juneteenth (June 19, observed) - Federal holiday since 2021
    juneteenth = _observe_holiday(date(year, 6, 19))
    holidays.append(juneteenth)

    # Independence Day (July 4, observed)
    independence_day = _observe_holiday(date(year, 7, 4))
    holidays.append(independence_day)

    # Labor Day (1st Monday in September)
    labor_day = _nth_weekday(year, 9, 0, 1)
    holidays.append(labor_day)

    # Thanksgiving (4th Thursday in November)
    thanksgiving = _nth_weekday(year, 11, 3, 4)  # 3=Thursday
    holidays.append(thanksgiving)

    # Christmas Day (December 25, observed)
    christmas = _observe_holiday(date(year, 12, 25))
    holidays.append(christmas)

    return frozenset(d.strftime("%Y-%m-%d") for d in holidays)


def is_market_holiday_date(check_date: date) -> bool:
    """Check if a specific date is a market holiday.

    Args:
        check_date: The date to check

    Returns:
        True if it's a market holiday
    """
    date_str = check_date.strftime("%Y-%m-%d")

    # Check current year's holidays
    year_holidays = get_market_holidays_for_year(check_date.year)
    if date_str in year_holidays:
        return True

    # Check for observed New Year's from next year (when Jan 1 falls on Saturday)
    # This affects Dec 31 of current year
    if check_date.month == 12 and check_date.day == 31:
        next_year_holidays = get_market_holidays_for_year(check_date.year + 1)
        if date_str in next_year_holidays:
            return True

    return False


class MarketHours:
    """Utility class for checking US stock market hours."""

    # Market hours in Eastern Time
    MARKET_OPEN: time = time(9, 30)   # 9:30 AM ET
    MARKET_CLOSE: time = time(16, 0)  # 4:00 PM ET

    # Extended hours (optional)
    PREMARKET_OPEN: time = time(4, 0)     # 4:00 AM ET
    AFTERHOURS_CLOSE: time = time(20, 0)  # 8:00 PM ET

    def __init__(self) -> None:
        """Initialize market hours utility."""
        self.eastern = pytz.timezone("US/Eastern")

    def is_market_open(self, include_extended_hours: bool = False) -> bool:
        """Check if the market is currently open.

        Args:
            include_extended_hours: Include pre-market and after-hours trading

        Returns:
            True if market is open, False otherwise
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

        # Regular market hours only
        return self.MARKET_OPEN <= current_time < self.MARKET_CLOSE

    def is_market_holiday(self, dt: datetime | None = None) -> bool:
        """Check if a given date is a market holiday.

        Args:
            dt: datetime object (defaults to today in ET)

        Returns:
            True if it's a market holiday
        """
        if dt is None:
            dt = datetime.now(self.eastern)

        return is_market_holiday_date(dt.date())

    def seconds_until_market_open(self) -> int:
        """Calculate seconds until next market open.

        Returns:
            Seconds until market opens (0 if already open)
        """
        if self.is_market_open():
            return 0

        now_et = datetime.now(self.eastern)

        # If it's during market hours today but market is closed (holiday)
        if (
            now_et.weekday() < 5
            and now_et.time() < self.MARKET_CLOSE
            and self.is_market_holiday(now_et)
        ):
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
                    microsecond=0,
                )
                return int((market_open_today - now_et).total_seconds())

        # Otherwise, wait for next trading day
        return self._seconds_to_next_trading_day(now_et)

    def _seconds_to_next_trading_day(self, current_time: datetime) -> int:
        """Calculate seconds to next trading day's market open."""
        next_day = current_time + timedelta(days=1)
        next_day = next_day.replace(
            hour=self.MARKET_OPEN.hour,
            minute=self.MARKET_OPEN.minute,
            second=0,
            microsecond=0,
        )

        # Keep advancing until we find a trading day
        max_attempts = 10  # Prevent infinite loop
        attempts = 0

        while (
            next_day.weekday() >= 5 or self.is_market_holiday(next_day)
        ) and attempts < max_attempts:
            next_day += timedelta(days=1)
            attempts += 1

        return int((next_day - current_time).total_seconds())

    def get_market_status_message(self) -> str:
        """Get a human-readable market status message.

        Returns:
            Status message string
        """
        now_et = datetime.now(self.eastern)

        if self.is_market_open():
            close_time = self.MARKET_CLOSE.strftime("%I:%M %p")
            return f"Market is OPEN (closes at {close_time} ET)"

        if now_et.weekday() >= 5:
            return "Market is CLOSED (weekend)"

        if self.is_market_holiday(now_et):
            return "Market is CLOSED (holiday)"

        if now_et.time() < self.MARKET_OPEN:
            open_time = self.MARKET_OPEN.strftime("%I:%M %p")
            return f"Market opens at {open_time} ET"

        if now_et.time() >= self.MARKET_CLOSE:
            return "Market is CLOSED (after hours)"

        return "Market status unknown"

    def get_current_time_et(self) -> datetime:
        """Get current time in Eastern timezone.

        Returns:
            Current datetime in US/Eastern
        """
        return datetime.now(self.eastern)


def main() -> None:
    """Test market hours detection."""
    market = MarketHours()

    print("Market Hours Utility Test")
    print("=" * 50)
    print(f"Current time (ET): {market.get_current_time_et().strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
    print(f"Status: {market.get_market_status_message()}")
    print(f"Is market open? {market.is_market_open()}")

    if not market.is_market_open():
        seconds = market.seconds_until_market_open()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        print(f"Time until market opens: {hours}h {minutes}m")

    # Show holidays for current and next year
    current_year = market.get_current_time_et().year
    print(f"\n{current_year} Market Holidays:")
    for holiday in sorted(get_market_holidays_for_year(current_year)):
        print(f"  {holiday}")

    print(f"\n{current_year + 1} Market Holidays:")
    for holiday in sorted(get_market_holidays_for_year(current_year + 1)):
        print(f"  {holiday}")


if __name__ == "__main__":
    main()
