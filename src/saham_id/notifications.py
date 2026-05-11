"""Notification system — Telegram, Discord, Webhook, Console alerts.

Provides pluggable notification backends so watchlist alerts and signals
can be delivered to multiple channels.

Usage:
    from saham_id.notifications import NotificationManager, TelegramBackend, WebhookBackend

    manager = NotificationManager()
    manager.add_backend(TelegramBackend(bot_token="...", chat_id="..."))
    manager.add_backend(WebhookBackend(url="https://hooks.slack.com/..."))

    manager.notify("BBCA hit target buy Rp 9000!", level="alert")
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

import httpx

logger = logging.getLogger(__name__)

Level = Literal["info", "alert", "critical"]


@dataclass
class Notification:
    """A single notification message."""

    title: str
    message: str
    level: Level = "info"
    ticker: str = ""
    timestamp: Optional[datetime] = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    @property
    def emoji(self) -> str:
        return {"info": "ℹ️", "alert": "⚠️", "critical": "🚨"}[self.level]

    def format_plain(self) -> str:
        parts = [f"[{self.level.upper()}]"]
        if self.ticker:
            parts.append(f"[{self.ticker}]")
        parts.append(self.title)
        if self.message:
            parts.append(f"— {self.message}")
        return " ".join(parts)

    def format_markdown(self) -> str:
        parts = [f"{self.emoji} **{self.title}**"]
        if self.ticker:
            parts[0] = f"{self.emoji} **[{self.ticker}]** {self.title}"
        if self.message:
            parts.append(self.message)
        if self.extra:
            details = " | ".join(f"{k}: {v}" for k, v in self.extra.items())
            parts.append(f"_{details}_")
        return "\n".join(parts)


class NotificationBackend(ABC):
    """Base class for notification backends."""

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """Send a notification. Returns True on success."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name for logging."""


class ConsoleBackend(NotificationBackend):
    """Print notifications to console (Rich)."""

    @property
    def name(self) -> str:
        return "console"

    def send(self, notification: Notification) -> bool:
        try:
            from rich.console import Console
            console = Console()
            color = {"info": "blue", "alert": "yellow", "critical": "red"}[notification.level]
            console.print(f"[{color}]{notification.format_plain()}[/]")
            return True
        except Exception:
            print(notification.format_plain())
            return True


class TelegramBackend(NotificationBackend):
    """Send notifications to Telegram via Bot API.

    Parameters:
        bot_token: Telegram Bot API token (from @BotFather)
        chat_id: Target chat/group/channel ID

    Setup:
        1. Create bot: https://t.me/BotFather -> /newbot
        2. Get chat_id: send message to bot, then GET https://api.telegram.org/bot{TOKEN}/getUpdates
    """

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str):
        self._token = bot_token
        self._chat_id = chat_id

    @property
    def name(self) -> str:
        return "telegram"

    def send(self, notification: Notification) -> bool:
        url = self.API_URL.format(token=self._token)
        text = notification.format_markdown()

        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("ok", False)
        except Exception as exc:
            logger.error(f"Telegram send failed: {exc}")
            return False


class DiscordBackend(NotificationBackend):
    """Send notifications to Discord via webhook.

    Parameters:
        webhook_url: Discord webhook URL (from channel settings -> Integrations)
    """

    def __init__(self, webhook_url: str):
        self._url = webhook_url

    @property
    def name(self) -> str:
        return "discord"

    def send(self, notification: Notification) -> bool:
        # Discord webhook format
        color_map = {"info": 3447003, "alert": 16776960, "critical": 15158332}

        embed = {
            "title": f"{notification.emoji} {notification.title}",
            "description": notification.message,
            "color": color_map.get(notification.level, 0),
            "timestamp": notification.timestamp.isoformat() if notification.timestamp else None,
        }

        if notification.ticker:
            embed["title"] = f"{notification.emoji} [{notification.ticker}] {notification.title}"

        if notification.extra:
            embed["fields"] = [
                {"name": k, "value": str(v), "inline": True}
                for k, v in list(notification.extra.items())[:5]
            ]

        payload = {"embeds": [embed]}

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self._url, json=payload)
                return response.status_code in (200, 204)
        except Exception as exc:
            logger.error(f"Discord send failed: {exc}")
            return False


class WebhookBackend(NotificationBackend):
    """Send notifications to a generic webhook (Slack, custom, etc).

    Sends a JSON POST with the notification data.
    Compatible with Slack incoming webhooks.

    Parameters:
        url: Webhook URL
        headers: Optional extra headers (e.g. auth)
    """

    def __init__(self, url: str, headers: Optional[dict] = None):
        self._url = url
        self._headers = headers or {}

    @property
    def name(self) -> str:
        return "webhook"

    def send(self, notification: Notification) -> bool:
        # Slack-compatible format
        payload = {
            "text": notification.format_plain(),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": notification.format_markdown(),
                    },
                }
            ],
            # Also include structured data for custom handlers
            "data": {
                "title": notification.title,
                "message": notification.message,
                "level": notification.level,
                "ticker": notification.ticker,
                "timestamp": notification.timestamp.isoformat() if notification.timestamp else None,
                "extra": notification.extra,
            },
        }

        try:
            headers = {"Content-Type": "application/json", **self._headers}
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self._url, json=payload, headers=headers)
                return response.status_code in (200, 201, 204)
        except Exception as exc:
            logger.error(f"Webhook send failed: {exc}")
            return False


class NotificationManager:
    """Manages multiple notification backends and dispatches messages.

    Usage:
        manager = NotificationManager()
        manager.add_backend(ConsoleBackend())
        manager.add_backend(TelegramBackend(token, chat_id))

        manager.notify("Price alert!", message="BBCA hit Rp 9000", level="alert", ticker="BBCA")
    """

    def __init__(self):
        self._backends: list[NotificationBackend] = []
        self._history: list[Notification] = []
        self._max_history = 100

    def add_backend(self, backend: NotificationBackend) -> None:
        """Register a notification backend."""
        self._backends.append(backend)

    def remove_backend(self, name: str) -> None:
        """Remove backend by name."""
        self._backends = [b for b in self._backends if b.name != name]

    @property
    def backends(self) -> list[str]:
        """List registered backend names."""
        return [b.name for b in self._backends]

    def notify(
        self,
        title: str,
        message: str = "",
        level: Level = "info",
        ticker: str = "",
        extra: Optional[dict] = None,
    ) -> list[bool]:
        """Send notification to all registered backends.

        Returns list of success/failure per backend.
        """
        notification = Notification(
            title=title,
            message=message,
            level=level,
            ticker=ticker,
            extra=extra or {},
        )

        # Store in history
        self._history.append(notification)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Dispatch to all backends
        results: list[bool] = []
        for backend in self._backends:
            try:
                success = backend.send(notification)
                results.append(success)
                if not success:
                    logger.warning(f"Notification failed for backend '{backend.name}'")
            except Exception as exc:
                logger.error(f"Backend '{backend.name}' error: {exc}")
                results.append(False)

        return results

    def notify_alert_results(self, alert_results: list) -> int:
        """Send notifications for watchlist alert results.

        Parameters:
            alert_results: List of AlertResult from Watchlist.check_alerts()

        Returns:
            Number of notifications sent.
        """
        count = 0
        for result in alert_results:
            for alert_desc in result.triggered_alerts:
                self.notify(
                    title=alert_desc,
                    message=f"Current values: {result.current_values}",
                    level="alert",
                    ticker=result.ticker,
                    extra=result.current_values,
                )
                count += 1
        return count

    def notify_signals(self, signals: list, min_confidence: float = 0.6) -> int:
        """Send notifications for generated signals.

        Parameters:
            signals: List of Signal objects
            min_confidence: Only notify signals above this confidence

        Returns:
            Number of notifications sent.
        """
        count = 0
        for signal in signals:
            if signal.confidence < min_confidence:
                continue
            if signal.action.value == "HOLD":
                continue

            level: Level = "critical" if signal.confidence >= 0.8 else "alert"
            self.notify(
                title=f"{signal.action.value} signal (confidence: {signal.confidence:.0%})",
                message="; ".join(signal.reasons[:3]),
                level=level,
                ticker=signal.ticker,
                extra={"score": f"{signal.score:+.3f}", "confidence": f"{signal.confidence:.0%}"},
            )
            count += 1
        return count

    @property
    def history(self) -> list[Notification]:
        """Recent notification history."""
        return list(self._history)


# --- Factory for quick setup from environment ---


def create_manager_from_env() -> NotificationManager:
    """Create a NotificationManager with backends configured from environment.

    Reads:
        SAHAM_ID_TELEGRAM_TOKEN + SAHAM_ID_TELEGRAM_CHAT_ID -> Telegram
        SAHAM_ID_DISCORD_WEBHOOK -> Discord
        SAHAM_ID_WEBHOOK_URL -> Generic webhook
    """
    import os

    manager = NotificationManager()
    manager.add_backend(ConsoleBackend())

    # Telegram
    tg_token = os.environ.get("SAHAM_ID_TELEGRAM_TOKEN", "")
    tg_chat = os.environ.get("SAHAM_ID_TELEGRAM_CHAT_ID", "")
    if tg_token and tg_chat:
        manager.add_backend(TelegramBackend(bot_token=tg_token, chat_id=tg_chat))

    # Discord
    discord_url = os.environ.get("SAHAM_ID_DISCORD_WEBHOOK", "")
    if discord_url:
        manager.add_backend(DiscordBackend(webhook_url=discord_url))

    # Generic webhook
    webhook_url = os.environ.get("SAHAM_ID_WEBHOOK_URL", "")
    if webhook_url:
        manager.add_backend(WebhookBackend(url=webhook_url))

    return manager
