"""Tests for signal history tracker."""
from saham_id.signal_history import SignalHistoryTracker, RecordedSignal, AccuracyReport
from saham_id.signals import Signal, Action


class TestRecordedSignal:
    def test_was_correct_buy_positive(self):
        rs = RecordedSignal(ticker="BBCA", action="BUY", confidence=0.8, score=0.6,
                           price_at_signal=9500, reasons=[], timestamp="2025-01-06",
                           evaluated=True, return_5d=0.05)
        assert rs.was_correct is True

    def test_was_correct_buy_negative(self):
        rs = RecordedSignal(ticker="BBCA", action="BUY", confidence=0.8, score=0.6,
                           price_at_signal=9500, reasons=[], timestamp="2025-01-06",
                           evaluated=True, return_5d=-0.03)
        assert rs.was_correct is False

    def test_was_correct_sell(self):
        rs = RecordedSignal(ticker="BBCA", action="SELL", confidence=0.7, score=-0.5,
                           price_at_signal=9500, reasons=[], timestamp="2025-01-06",
                           evaluated=True, return_5d=-0.04)
        assert rs.was_correct is True

    def test_not_evaluated(self):
        rs = RecordedSignal(ticker="BBCA", action="BUY", confidence=0.8, score=0.6,
                           price_at_signal=9500, reasons=[], timestamp="2025-01-06")
        assert rs.was_correct is None


class TestSignalHistoryTracker:
    def test_record_signal(self):
        tracker = SignalHistoryTracker("test")
        signal = Signal(ticker="BBCA", action=Action.BUY, confidence=0.8, score=0.6,
                       indicators={"close": 9500.0})
        recorded = tracker.record_signal(signal, engine="swing_buy")
        assert recorded.ticker == "BBCA"
        assert recorded.price_at_signal == 9500.0
        assert len(tracker.signals) == 1

    def test_record_signals_skips_hold(self):
        tracker = SignalHistoryTracker("test")
        signals = [
            Signal(ticker="BBCA", action=Action.BUY, confidence=0.8, score=0.6, indicators={"close": 9500}),
            Signal(ticker="BBRI", action=Action.HOLD, confidence=0.5, score=0.0, indicators={"close": 5000}),
            Signal(ticker="TLKM", action=Action.SELL, confidence=0.7, score=-0.4, indicators={"close": 3500}),
        ]
        count = tracker.record_signals(signals)
        assert count == 2
        assert len(tracker.signals) == 2

    def test_stats(self):
        tracker = SignalHistoryTracker("test")
        tracker.signals = [
            RecordedSignal(ticker="BBCA", action="BUY", confidence=0.8, score=0.6,
                          price_at_signal=9500, reasons=[], timestamp="2025-01-06",
                          evaluated=True, return_5d=0.03),
            RecordedSignal(ticker="BBRI", action="BUY", confidence=0.7, score=0.5,
                          price_at_signal=5000, reasons=[], timestamp="2025-01-06",
                          evaluated=True, return_5d=-0.02),
            RecordedSignal(ticker="TLKM", action="SELL", confidence=0.6, score=-0.4,
                          price_at_signal=3500, reasons=[], timestamp="2025-01-06"),
        ]
        stats = tracker.stats()
        assert stats["total_signals"] == 3
        assert stats["buy_signals"] == 2
        assert stats["sell_signals"] == 1
        assert stats["evaluated"] == 2
        assert stats["correct"] == 1
        assert stats["win_rate"] == 0.5

    def test_evaluate_accuracy(self):
        tracker = SignalHistoryTracker("test")
        tracker.signals = [
            RecordedSignal(ticker="BBCA", action="BUY", confidence=0.8, score=0.6,
                          price_at_signal=9500, reasons=[], timestamp="2025-01-06",
                          evaluated=True, return_5d=0.05),
        ]
        report = tracker.evaluate_accuracy()
        assert report.evaluated_signals == 1
        assert report.correct_signals == 1
        assert report.win_rate == 1.0
        assert report.avg_return_5d == 0.05
