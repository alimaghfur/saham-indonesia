"""Tests for seasonality analysis module."""
from saham_id.analysis.seasonality import (
    MonthlySeasonality, DayOfWeekEffect, MONTH_NAMES, DAY_NAMES,
    sell_in_may_effect, drip_calculator,
)


class TestMonthlySeasonality:
    def test_create(self):
        ms = MonthlySeasonality(ticker="BBCA", period="5y")
        assert ms.ticker == "BBCA"
        assert ms.best_month == ""
        assert ms.worst_month == ""

    def test_best_worst_month(self):
        ms = MonthlySeasonality(
            ticker="BBCA", period="5y",
            monthly_returns={"January": 0.03, "May": -0.02, "December": 0.05},
        )
        assert ms.best_month == "December"
        assert ms.worst_month == "May"


class TestDayOfWeekEffect:
    def test_create(self):
        dow = DayOfWeekEffect(ticker="BBCA", period="5y")
        assert dow.best_day == ""

    def test_best_worst_day(self):
        dow = DayOfWeekEffect(
            ticker="BBCA", period="5y",
            daily_returns={"Monday": -0.001, "Friday": 0.002, "Wednesday": 0.001},
        )
        assert dow.best_day == "Friday"
        assert dow.worst_day == "Monday"


class TestSellInMayEffect:
    def test_no_data(self):
        result = sell_in_may_effect("NONEXISTENT")
        assert result["may_oct_return"] == 0.0
        assert result["effect_exists"] is False


class TestConstants:
    def test_month_names(self):
        assert len(MONTH_NAMES) == 12
        assert MONTH_NAMES[0] == "January"
        assert MONTH_NAMES[11] == "December"

    def test_day_names(self):
        assert len(DAY_NAMES) == 5
        assert DAY_NAMES[0] == "Monday"
        assert DAY_NAMES[4] == "Friday"
