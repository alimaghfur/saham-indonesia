"""Tests for notification system."""
from saham_id.notifications import (
    ConsoleBackend, DiscordBackend, Notification, NotificationManager,
    TelegramBackend, WebhookBackend, create_manager_from_env,
)


class TestNotification:
    def test_create(self):
        n = Notification(title="Test", message="Hello", level="info")
        assert n.title == "Test"
        assert n.level == "info"
        assert n.timestamp is not None

    def test_emoji(self):
        assert Notification(title="", message="", level="info").emoji == "ℹ️"
        assert Notification(title="", message="", level="alert").emoji == "⚠️"
        assert Notification(title="", message="", level="critical").emoji == "🚨"

    def test_format_plain(self):
        n = Notification(title="Price Alert", message="BBCA hit target", level="alert", ticker="BBCA")
        plain = n.format_plain()
        assert "ALERT" in plain
        assert "BBCA" in plain
        assert "Price Alert" in plain

    def test_format_markdown(self):
        n = Notification(title="Buy Signal", message="RSI oversold", level="alert", ticker="BBCA")
        md = n.format_markdown()
        assert "**" in md
        assert "BBCA" in md


class TestConsoleBackend:
    def test_send(self):
        backend = ConsoleBackend()
        n = Notification(title="Test", message="hello", level="info")
        assert backend.send(n) is True
        assert backend.name == "console"


class TestNotificationManager:
    def test_add_backend(self):
        manager = NotificationManager()
        manager.add_backend(ConsoleBackend())
        assert "console" in manager.backends

    def test_remove_backend(self):
        manager = NotificationManager()
        manager.add_backend(ConsoleBackend())
        manager.remove_backend("console")
        assert "console" not in manager.backends

    def test_notify(self):
        manager = NotificationManager()
        manager.add_backend(ConsoleBackend())
        results = manager.notify("Test", message="Hello")
        assert results == [True]

    def test_history(self):
        manager = NotificationManager()
        manager.add_backend(ConsoleBackend())
        manager.notify("First")
        manager.notify("Second")
        assert len(manager.history) == 2
        assert manager.history[0].title == "First"

    def test_notify_with_extra(self):
        manager = NotificationManager()
        manager.add_backend(ConsoleBackend())
        results = manager.notify("Alert", ticker="BBCA", level="alert", extra={"rsi": 28.5})
        assert results == [True]


class TestTelegramBackend:
    def test_name(self):
        backend = TelegramBackend(bot_token="fake", chat_id="123")
        assert backend.name == "telegram"


class TestDiscordBackend:
    def test_name(self):
        backend = DiscordBackend(webhook_url="https://fake.url")
        assert backend.name == "discord"


class TestWebhookBackend:
    def test_name(self):
        backend = WebhookBackend(url="https://fake.url")
        assert backend.name == "webhook"


class TestCreateFromEnv:
    def test_default_has_console(self):
        manager = create_manager_from_env()
        assert "console" in manager.backends
