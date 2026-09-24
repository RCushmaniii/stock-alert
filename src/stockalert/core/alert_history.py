"""
Once-per-day alert ledger.

A stock that crosses its threshold usually STAYS across it. With a 2-hour check
interval and a 5-minute cooldown, a ticker parked below its low threshold was
re-announced on every check — four or five identical WhatsApp messages in one
trading day, none of them news. The cooldown also lived only in memory, so a
reboot or a config reload reset it.

This ledger records the trading day (US/Eastern, the market's own calendar) on
which each symbol last alerted, and persists it next to config.json so the rule
survives restarts: at most one alert per symbol per trading day.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path

import pytz

logger = logging.getLogger(__name__)

_EASTERN = pytz.timezone("US/Eastern")


def trading_day(now: datetime | None = None) -> str:
    """The US/Eastern calendar date for ``now`` (default: current time)."""
    moment = now.astimezone(_EASTERN) if now else datetime.now(_EASTERN)
    return moment.date().isoformat()


class DailyAlertLedger:
    """Remembers which trading day each symbol last alerted on.

    ``path`` None keeps the ledger in memory only — for tests, and for any
    caller that must not touch the user's AppData.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._last_day: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if self._path is None or not self._path.exists():
            return {}
        try:
            with self._path.open(encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("alert history is not a JSON object")
            return {str(k): str(v) for k, v in data.items()}
        except (OSError, ValueError) as e:
            # An unreadable ledger must never stop alerts. Worst case is one
            # extra alert today, not a silent monitor.
            logger.warning(f"Ignoring unreadable alert history {self._path}: {e}")
            return {}

    def _save(self) -> None:
        if self._path is None:
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(self._last_day, f, indent=2, sort_keys=True)
            tmp.replace(self._path)
        except OSError as e:
            logger.error(f"Failed to save alert history {self._path}: {e}")

    def alerted_today(self, symbol: str, now: datetime | None = None) -> bool:
        """True if ``symbol`` already alerted on the current trading day."""
        with self._lock:
            return self._last_day.get(symbol) == trading_day(now)

    def record(self, symbols: list[str], now: datetime | None = None) -> None:
        """Mark ``symbols`` as alerted on the current trading day."""
        if not symbols:
            return
        day = trading_day(now)
        with self._lock:
            for symbol in symbols:
                self._last_day[symbol] = day
            self._save()
