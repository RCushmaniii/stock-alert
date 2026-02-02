"""
Free tier limits for StockAlert.

Defines the restrictions for the free version based on Finnhub API limits.
Finnhub free tier: 60 API calls/minute, 30 calls/second ceiling.
"""

from __future__ import annotations

# Free tier limits
FREE_TIER_MAX_TICKERS = 15
FREE_TIER_MIN_CHECK_INTERVAL = 90  # seconds
FREE_TIER_NEWS_TICKERS = 5  # max tickers to fetch news for
FREE_TIER_API_CALLS_PER_MINUTE = 60

# Premium tier (for future use)
PREMIUM_TIER_MAX_TICKERS = 100
PREMIUM_TIER_MIN_CHECK_INTERVAL = 30  # seconds


def is_free_tier() -> bool:
    """Check if user is on free tier.

    Returns:
        True if free tier, False if premium
    """
    # TODO: Implement license/subscription check
    return True


def get_max_tickers() -> int:
    """Get maximum allowed tickers for current tier.

    Returns:
        Maximum number of tickers allowed
    """
    if is_free_tier():
        return FREE_TIER_MAX_TICKERS
    return PREMIUM_TIER_MAX_TICKERS


def get_min_check_interval() -> int:
    """Get minimum check interval for current tier.

    Returns:
        Minimum check interval in seconds
    """
    if is_free_tier():
        return FREE_TIER_MIN_CHECK_INTERVAL
    return PREMIUM_TIER_MIN_CHECK_INTERVAL


def get_news_ticker_limit() -> int:
    """Get maximum tickers to fetch news for.

    Returns:
        Maximum number of tickers for news fetching
    """
    return FREE_TIER_NEWS_TICKERS


def can_add_ticker(current_count: int) -> bool:
    """Check if another ticker can be added.

    Args:
        current_count: Current number of tickers

    Returns:
        True if can add, False if at limit
    """
    return current_count < get_max_tickers()


def validate_check_interval(interval: int) -> int:
    """Validate and adjust check interval to meet tier limits.

    Args:
        interval: Requested check interval in seconds

    Returns:
        Adjusted interval (at least minimum for tier)
    """
    min_interval = get_min_check_interval()
    return max(interval, min_interval)
