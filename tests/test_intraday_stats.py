"""Tests for intraday session stats."""
from saham_id.analysis.intraday_stats import SessionStats, session_stats


class TestSessionStats:
    def test_create(self):
        stats = SessionStats(ticker="BBCA", period="3mo", sample_days=60)
        assert stats.ticker == "BBCA"
        assert stats.sample_days == 60

    def test_best_session_morning(self):
        stats = SessionStats(ticker="X", period="3mo",
                           morning_avg_return=0.005, afternoon_avg_return=0.002)
        assert stats.best_session == "morning"

    def test_best_session_afternoon(self):
        stats = SessionStats(ticker="X", period="3mo",
                           morning_avg_return=0.001, afternoon_avg_return=0.004)
        assert stats.best_session == "afternoon"

    def test_best_session_neutral(self):
        stats = SessionStats(ticker="X", period="3mo",
                           morning_avg_return=0.003, afternoon_avg_return=0.003)
        assert stats.best_session == "neutral"


class TestSessionStatsFunction:
    def test_nonexistent_ticker(self):
        stats = session_stats("ZZZZNONEXIST")
        assert stats.sample_days == 0
        assert stats.full_day_avg_return == 0.0
