"""Tests for alert CLI helper."""
from saham_id.alert_cli import add_alert, list_alerts, remove_alert


class TestAddAlert:
    def test_basic(self):
        msg = add_alert("BBCA", field="last", op="<", value=9000, watchlist_name="test_alerts")
        assert "BBCA" in msg
        assert "Alert added" in msg

    def test_custom_message(self):
        msg = add_alert("BBRI", field="rsi", op="<", value=30, message="Oversold!", watchlist_name="test_alerts")
        assert "BBRI" in msg


class TestListAlerts:
    def test_returns_list(self):
        add_alert("BBCA", field="last", op="<", value=9000, watchlist_name="test_list")
        alerts = list_alerts(watchlist_name="test_list")
        assert isinstance(alerts, list)
        assert len(alerts) >= 1
        assert alerts[0]["ticker"] == "BBCA"


class TestRemoveAlert:
    def test_existing(self):
        add_alert("TLKM", field="last", op=">", value=4000, watchlist_name="test_remove")
        msg = remove_alert("TLKM", watchlist_name="test_remove")
        assert "cleared" in msg

    def test_nonexistent(self):
        msg = remove_alert("ZZZZZ", watchlist_name="test_remove")
        assert "not in watchlist" in msg
