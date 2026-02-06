"""
Exchange rate service for currency conversion.

Fetches USD to MXN exchange rate from exchangerate-api.com
with intelligent caching to minimize API calls.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Cache settings
CACHE_DURATION_SECONDS = 3600  # 1 hour
API_BASE_URL = "https://v6.exchangerate-api.com/v6"

# Module-level cache
_cached_rate: float | None = None
_cache_timestamp: float = 0.0
_api_key: str | None = None


def set_api_key(api_key: str) -> None:
    """Set the exchange rate API key.

    Args:
        api_key: The exchangerate-api.com API key
    """
    global _api_key
    _api_key = api_key
    logger.info("Exchange rate API key configured")


def get_usd_to_mxn_rate(force_refresh: bool = False) -> float | None:
    """Get the current USD to MXN exchange rate.

    Uses cached value if available and not expired.

    Args:
        force_refresh: If True, bypass cache and fetch fresh rate

    Returns:
        Exchange rate (USD to MXN), or None if unavailable
    """
    global _cached_rate, _cache_timestamp

    # Check cache validity
    now = time.time()
    cache_age = now - _cache_timestamp

    if not force_refresh and _cached_rate is not None and cache_age < CACHE_DURATION_SECONDS:
        logger.debug(f"Using cached exchange rate: {_cached_rate:.4f} (age: {cache_age:.0f}s)")
        return _cached_rate

    # Fetch fresh rate
    rate = _fetch_exchange_rate()
    if rate is not None:
        _cached_rate = rate
        _cache_timestamp = now
        logger.info(f"Updated exchange rate: 1 USD = {rate:.4f} MXN")

    return rate if rate is not None else _cached_rate


def _fetch_exchange_rate() -> float | None:
    """Fetch fresh exchange rate from API.

    Returns:
        Exchange rate (USD to MXN), or None on error
    """
    if not _api_key:
        logger.warning("Exchange rate API key not configured")
        return None

    url = f"{API_BASE_URL}/{_api_key}/latest/USD"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("result") != "success":
            logger.error(f"Exchange rate API error: {data.get('error-type', 'unknown')}")
            return None

        rates = data.get("conversion_rates", {})
        mxn_rate = rates.get("MXN")

        if mxn_rate is None:
            logger.error("MXN rate not found in API response")
            return None

        return float(mxn_rate)

    except requests.exceptions.Timeout:
        logger.warning("Exchange rate API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Exchange rate API request failed: {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse exchange rate response: {e}")
        return None


def get_cache_info() -> dict:
    """Get information about the exchange rate cache.

    Returns:
        Dict with cache status information
    """
    now = time.time()
    cache_age = now - _cache_timestamp if _cache_timestamp > 0 else None

    return {
        "cached_rate": _cached_rate,
        "cache_age_seconds": cache_age,
        "cache_valid": cache_age is not None and cache_age < CACHE_DURATION_SECONDS,
        "api_key_configured": _api_key is not None,
    }


def clear_cache() -> None:
    """Clear the cached exchange rate."""
    global _cached_rate, _cache_timestamp
    _cached_rate = None
    _cache_timestamp = 0.0
    logger.info("Exchange rate cache cleared")
