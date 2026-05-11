"""Tests for trading journal."""
from saham_id.trading_journal import TradingJournal, JournalEntry


class TestJournalEntry:
    def test_create(self):
        entry = JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10,
                            reason="RSI oversold", strategy="swing_reversal")
        assert entry.ticker == "BBCA"
        assert entry.status == "open"
        assert entry.is_winner is None

    def test_close(self):
        entry = JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10)
        entry.close(exit_price=10000, lesson="Good trade", rating=4)
        assert entry.status == "closed"
        assert entry.pnl == (10000 - 9500) * 1000
        assert entry.pnl_pct > 0
        assert entry.is_winner is True
        assert entry.lesson == "Good trade"

    def test_close_loser(self):
        entry = JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10)
        entry.close(exit_price=9000, lesson="Cut loss too late")
        assert entry.is_winner is False
        assert entry.pnl < 0


class TestTradingJournal:
    def test_add_entry(self):
        journal = TradingJournal("test")
        journal.add_entry(JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10))
        assert len(journal.entries) == 1

    def test_close_trade(self):
        journal = TradingJournal("test")
        journal.add_entry(JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10))
        result = journal.close_trade("BBCA", exit_price=10000, lesson="Good")
        assert result is not None
        assert result.status == "closed"

    def test_open_closed(self):
        journal = TradingJournal("test")
        journal.add_entry(JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10))
        journal.add_entry(JournalEntry(ticker="BBRI", side="buy", price=5000, lots=20))
        journal.close_trade("BBCA", exit_price=10000)
        assert len(journal.open_trades()) == 1
        assert len(journal.closed_trades()) == 1

    def test_stats(self):
        journal = TradingJournal("test")
        journal.add_entry(JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10))
        journal.add_entry(JournalEntry(ticker="BBRI", side="buy", price=5000, lots=10))
        journal.close_trade("BBCA", exit_price=10000)
        journal.close_trade("BBRI", exit_price=4500)
        stats = journal.stats()
        assert stats["closed"] == 2
        assert stats["winners"] == 1
        assert stats["losers"] == 1
        assert stats["win_rate"] == 0.5

    def test_lessons(self):
        journal = TradingJournal("test")
        journal.add_entry(JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10))
        journal.close_trade("BBCA", exit_price=10000, lesson="Always set trailing stop")
        lessons = journal.lessons()
        assert "Always set trailing stop" in lessons

    def test_by_strategy(self):
        journal = TradingJournal("test")
        journal.add_entry(JournalEntry(ticker="BBCA", side="buy", price=9500, lots=10, strategy="breakout"))
        journal.add_entry(JournalEntry(ticker="BBRI", side="buy", price=5000, lots=10, strategy="reversal"))
        journal.add_entry(JournalEntry(ticker="TLKM", side="buy", price=3500, lots=10, strategy="breakout"))
        by_strat = journal.by_strategy()
        assert len(by_strat["breakout"]) == 2
        assert len(by_strat["reversal"]) == 1
