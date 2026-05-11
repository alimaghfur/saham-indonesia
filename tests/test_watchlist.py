"""Tests for watchlist system."""
from saham_id.watchlist import AlertCondition, Watchlist, WatchlistItem


class TestAlertCondition:
    def test_less_than(self):
        alert = AlertCondition(field="rsi", op="<", value=30)
        assert alert.evaluate(25) is True
        assert alert.evaluate(30) is False
        assert alert.evaluate(50) is False

    def test_greater_than(self):
        alert = AlertCondition(field="change_pct", op=">", value=0.05)
        assert alert.evaluate(0.06) is True
        assert alert.evaluate(0.05) is False
        assert alert.evaluate(0.03) is False

    def test_less_equal(self):
        alert = AlertCondition(field="last", op="<=", value=9000)
        assert alert.evaluate(9000) is True
        assert alert.evaluate(8999) is True
        assert alert.evaluate(9001) is False

    def test_greater_equal(self):
        alert = AlertCondition(field="volume", op=">=", value=50_000_000)
        assert alert.evaluate(50_000_000) is True
        assert alert.evaluate(100_000_000) is True
        assert alert.evaluate(49_999_999) is False

    def test_describe(self):
        alert = AlertCondition(field="rsi", op="<", value=30)
        assert "rsi" in alert.describe()
        assert "<" in alert.describe()
        assert "30" in alert.describe()

    def test_custom_message(self):
        alert = AlertCondition(field="rsi", op="<", value=30, message="Oversold!")
        assert alert.describe() == "Oversold!"


class TestWatchlist:
    def test_add_ticker(self):
        wl = Watchlist("test")
        wl.add("BBCA", notes="Banking leader")
        assert "BBCA" in wl
        assert len(wl) == 1

    def test_add_case_insensitive(self):
        wl = Watchlist("test")
        wl.add("bbca")
        assert "BBCA" in wl

    def test_remove_ticker(self):
        wl = Watchlist("test")
        wl.add("BBCA")
        assert wl.remove("BBCA") is True
        assert "BBCA" not in wl
        assert wl.remove("BBCA") is False  # already removed

    def test_get_ticker(self):
        wl = Watchlist("test")
        wl.add("BBCA", notes="Test note", tags=["bank", "bluechip"])
        item = wl.get("BBCA")
        assert item is not None
        assert item.notes == "Test note"
        assert "bank" in item.tags

    def test_tickers_list(self):
        wl = Watchlist("test")
        wl.add("BBCA")
        wl.add("BBRI")
        wl.add("TLKM")
        assert sorted(wl.tickers) == ["BBCA", "BBRI", "TLKM"]

    def test_update_notes(self):
        wl = Watchlist("test")
        wl.add("BBCA", notes="old")
        wl.update_notes("BBCA", "new notes")
        assert wl.get("BBCA").notes == "new notes"

    def test_add_alert(self):
        wl = Watchlist("test")
        wl.add("BBCA")
        wl.add_alert("BBCA", AlertCondition(field="rsi", op="<", value=30))
        item = wl.get("BBCA")
        assert len(item.alerts) == 1
        assert item.alerts[0].field == "rsi"

    def test_clear_alerts(self):
        wl = Watchlist("test")
        wl.add("BBCA", alerts=[AlertCondition(field="rsi", op="<", value=30)])
        wl.clear_alerts("BBCA")
        assert len(wl.get("BBCA").alerts) == 0

    def test_filter_by_tag(self):
        wl = Watchlist("test")
        wl.add("BBCA", tags=["bank", "bluechip"])
        wl.add("BBRI", tags=["bank"])
        wl.add("TLKM", tags=["telco"])
        banks = wl.filter_by_tag("bank")
        assert len(banks) == 2

    def test_target_prices(self):
        wl = Watchlist("test")
        wl.add("BBCA", target_buy=9000, target_sell=11000, stop_loss=8500)
        item = wl.get("BBCA")
        assert item.target_buy == 9000
        assert item.target_sell == 11000
        assert item.stop_loss == 8500


class TestWatchlistPersistence:
    def test_save_and_load(self):
        import tempfile
        import json
        from pathlib import Path

        tmp_path = Path(tempfile.mkdtemp())

        wl = Watchlist("test_persist")
        wl._storage_dir = tmp_path / "watchlists"
        wl.add("BBCA", notes="Leader", tags=["bank"])
        wl.add("TLKM", target_buy=3500)
        wl.save()

        # Verify file was created
        filepath = tmp_path / "watchlists" / "test_persist.json"
        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert "BBCA" in data["items"]
        assert data["items"]["BBCA"]["notes"] == "Leader"
        assert data["items"]["TLKM"]["target_buy"] == 3500
