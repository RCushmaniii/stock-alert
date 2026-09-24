"""Tests for the once-per-trading-day alert ledger."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytz

from stockalert.core.alert_history import DailyAlertLedger, trading_day

UTC = pytz.utc


class TestTradingDay:
    def test_uses_the_eastern_calendar_not_utc(self) -> None:
        # 01:30 UTC on the 25th is still the evening of the 24th in New York.
        # A UTC date would hand a ticker a second alert the same trading day.
        assert trading_day(UTC.localize(datetime(2026, 9, 25, 1, 30))) == "2026-09-24"

    def test_rolls_over_at_eastern_midnight(self) -> None:
        assert trading_day(UTC.localize(datetime(2026, 9, 25, 4, 30))) == "2026-09-25"


class TestDailyAlertLedger:
    def test_blocks_a_second_alert_on_the_same_day(self) -> None:
        ledger = DailyAlertLedger()
        morning = UTC.localize(datetime(2026, 9, 24, 14, 0))
        afternoon = UTC.localize(datetime(2026, 9, 24, 19, 0))

        assert not ledger.alerted_today("ALB", morning)
        ledger.record(["ALB"], morning)
        assert ledger.alerted_today("ALB", afternoon)

    def test_allows_the_next_trading_day(self) -> None:
        ledger = DailyAlertLedger()
        ledger.record(["ALB"], UTC.localize(datetime(2026, 9, 24, 14, 0)))
        assert not ledger.alerted_today("ALB", UTC.localize(datetime(2026, 9, 25, 14, 0)))

    def test_is_per_symbol(self) -> None:
        ledger = DailyAlertLedger()
        now = UTC.localize(datetime(2026, 9, 24, 14, 0))
        ledger.record(["ALB"], now)
        assert not ledger.alerted_today("RTX", now)

    def test_survives_a_restart(self, tmp_path: Path) -> None:
        # The old cooldown lived in memory; a reboot reset it and re-alerted.
        path = tmp_path / "alert_history.json"
        now = UTC.localize(datetime(2026, 9, 24, 14, 0))
        DailyAlertLedger(path).record(["ALB"], now)

        assert DailyAlertLedger(path).alerted_today("ALB", now)

    def test_corrupt_file_does_not_silence_alerts(self, tmp_path: Path) -> None:
        path = tmp_path / "alert_history.json"
        path.write_text("{not json", encoding="utf-8")

        ledger = DailyAlertLedger(path)
        assert not ledger.alerted_today("ALB")
