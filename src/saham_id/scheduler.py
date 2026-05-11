"""Scheduler — automated periodic scanning and alerting.

Run screeners and watchlist checks on a schedule, then notify via backends.

Usage:
    from saham_id.scheduler import Scheduler, ScheduledTask

    scheduler = Scheduler()
    scheduler.add_task(ScheduledTask(
        name="morning_scan",
        interval_minutes=30,
        action="screen_bpjs",
        params={"universe": "LQ45"},
    ))
    scheduler.add_task(ScheduledTask(
        name="watchlist_check",
        interval_minutes=5,
        action="check_alerts",
        params={"watchlist": "default"},
    ))

    # Run once (for cron/systemd integration)
    results = scheduler.run_due_tasks()

    # Or run loop (for standalone daemon)
    scheduler.run_forever()
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from saham_id.config import settings
from saham_id.notifications import NotificationManager, create_manager_from_env

logger = logging.getLogger(__name__)

ActionType = Literal[
    "check_alerts",
    "screen_bpjs",
    "screen_bsjp",
    "screen_breakout",
    "screen_pullback",
    "screen_reversal",
    "screen_scalping",
    "generate_signals",
    "market_breadth",
]


@dataclass
class ScheduledTask:
    """A task to run on a schedule."""

    name: str
    interval_minutes: int
    action: ActionType
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run: Optional[datetime] = None
    last_result: str = ""
    notify_on_results: bool = True  # send notifications when results found

    @property
    def is_due(self) -> bool:
        """Check if this task is due to run."""
        if not self.enabled:
            return False
        if self.last_run is None:
            return True
        elapsed = (datetime.utcnow() - self.last_run).total_seconds()
        return elapsed >= self.interval_minutes * 60


@dataclass
class TaskResult:
    """Result of running a scheduled task."""

    task_name: str
    success: bool
    message: str = ""
    data: Any = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class Scheduler:
    """Manages scheduled tasks for automated scanning.

    Can be used with:
        - Cron: `scheduler.run_due_tasks()` in a cron script
        - Systemd: `scheduler.run_forever()` as a daemon
        - Streamlit: check `is_due` and run in dashboard
    """

    def __init__(self, notification_manager: Optional[NotificationManager] = None):
        self.tasks: list[ScheduledTask] = []
        self.notifier = notification_manager or create_manager_from_env()
        self._state_file = settings.cache_dir / "scheduler_state.json"

    def add_task(self, task: ScheduledTask) -> None:
        """Add a scheduled task."""
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove task by name."""
        self.tasks = [t for t in self.tasks if t.name != name]

    def get_due_tasks(self) -> list[ScheduledTask]:
        """Get all tasks that are due to run."""
        return [t for t in self.tasks if t.is_due]

    def run_task(self, task: ScheduledTask) -> TaskResult:
        """Execute a single task."""
        try:
            result = _execute_action(task.action, task.params)
            task.last_run = datetime.utcnow()
            task.last_result = "success"

            # Notify if results found
            if task.notify_on_results and result.data:
                self._notify_results(task, result)

            return result
        except Exception as exc:
            task.last_run = datetime.utcnow()
            task.last_result = f"error: {exc}"
            logger.error(f"Task '{task.name}' failed: {exc}")
            return TaskResult(task_name=task.name, success=False, message=str(exc))

    def run_due_tasks(self) -> list[TaskResult]:
        """Run all tasks that are due. Returns results."""
        results: list[TaskResult] = []
        for task in self.get_due_tasks():
            logger.info(f"Running task: {task.name}")
            result = self.run_task(task)
            results.append(result)
        self._save_state()
        return results

    def run_forever(self, check_interval_seconds: int = 30) -> None:
        """Run scheduler in a loop. Blocks forever.

        For production use, run this as a systemd service or Docker container.
        """
        logger.info(f"Scheduler started with {len(self.tasks)} tasks")
        try:
            while True:
                self.run_due_tasks()
                time.sleep(check_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped")

    def _notify_results(self, task: ScheduledTask, result: TaskResult) -> None:
        """Send notifications for task results."""
        if not result.data:
            return

        if task.action == "check_alerts":
            self.notifier.notify_alert_results(result.data)
        elif task.action == "generate_signals":
            self.notifier.notify_signals(result.data)
        elif task.action.startswith("screen_"):
            # Notify top screener results
            screen_result = result.data
            if hasattr(screen_result, 'rows') and screen_result.rows:
                top_tickers = [r.ticker for r in screen_result.rows[:5]]
                self.notifier.notify(
                    title=f"Screener: {task.action} found {len(screen_result.rows)} results",
                    message=f"Top: {', '.join(top_tickers)}",
                    level="info",
                    extra={"strategy": screen_result.strategy, "count": len(screen_result.rows)},
                )

    def _save_state(self) -> None:
        """Save scheduler state for persistence across restarts."""
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "saved_at": datetime.utcnow().isoformat(),
                "tasks": [
                    {
                        "name": t.name,
                        "last_run": t.last_run.isoformat() if t.last_run else None,
                        "last_result": t.last_result,
                    }
                    for t in self.tasks
                ],
            }
            self._state_file.write_text(json.dumps(state, indent=2))
        except Exception as exc:
            logger.warning(f"Could not save scheduler state: {exc}")

    def load_state(self) -> None:
        """Load scheduler state from disk."""
        if not self._state_file.exists():
            return
        try:
            state = json.loads(self._state_file.read_text())
            task_states = {t["name"]: t for t in state.get("tasks", [])}
            for task in self.tasks:
                if task.name in task_states:
                    ts = task_states[task.name]
                    if ts.get("last_run"):
                        task.last_run = datetime.fromisoformat(ts["last_run"])
                    task.last_result = ts.get("last_result", "")
        except Exception as exc:
            logger.warning(f"Could not load scheduler state: {exc}")


def _execute_action(action: ActionType, params: dict) -> TaskResult:
    """Execute a scheduled action."""
    from saham_id.data.sources import get_source

    source_name = params.get("source")
    src = get_source(source_name)
    universe = params.get("universe", "LQ45")

    if action == "check_alerts":
        from saham_id.watchlist import Watchlist
        wl_name = params.get("watchlist", "default")
        wl = Watchlist.load(wl_name)
        alerts = wl.check_alerts(source=src)
        return TaskResult(
            task_name=action,
            success=True,
            message=f"{len(alerts)} alerts triggered",
            data=alerts if alerts else None,
        )

    elif action == "screen_bpjs":
        from saham_id.screener.intraday.bpjs import screen
        result = screen(universe=universe, source=src, top_n=params.get("top_n", 10))
        return TaskResult(task_name=action, success=True,
                         message=f"{len(result.rows)} results", data=result if result.rows else None)

    elif action == "screen_bsjp":
        from saham_id.screener.intraday.bsjp import screen
        result = screen(universe=universe, source=src, top_n=params.get("top_n", 10))
        return TaskResult(task_name=action, success=True,
                         message=f"{len(result.rows)} results", data=result if result.rows else None)

    elif action == "screen_breakout":
        from saham_id.screener.swing.breakout import screen
        result = screen(universe=universe, source=src, top_n=params.get("top_n", 10))
        return TaskResult(task_name=action, success=True,
                         message=f"{len(result.rows)} results", data=result if result.rows else None)

    elif action == "screen_pullback":
        from saham_id.screener.swing.pullback import screen
        result = screen(universe=universe, source=src, top_n=params.get("top_n", 10))
        return TaskResult(task_name=action, success=True,
                         message=f"{len(result.rows)} results", data=result if result.rows else None)

    elif action == "screen_reversal":
        from saham_id.screener.swing.reversal import screen
        result = screen(universe=universe, source=src, top_n=params.get("top_n", 10))
        return TaskResult(task_name=action, success=True,
                         message=f"{len(result.rows)} results", data=result if result.rows else None)

    elif action == "screen_scalping":
        from saham_id.screener.intraday.scalping import screen
        result = screen(universe=universe, source=src, top_n=params.get("top_n", 10))
        return TaskResult(task_name=action, success=True,
                         message=f"{len(result.rows)} results", data=result if result.rows else None)

    elif action == "generate_signals":
        from saham_id.signals import generate_signals, swing_buy_engine, Action
        from saham_id.data.universe import get_universe
        tickers = get_universe(universe)
        engine = swing_buy_engine()
        signals = generate_signals(tickers, engine=engine, source=src)
        actionable = [s for s in signals if s.action != Action.HOLD]
        return TaskResult(task_name=action, success=True,
                         message=f"{len(actionable)} actionable signals",
                         data=actionable if actionable else None)

    elif action == "market_breadth":
        from saham_id.market.breadth import snapshot
        snap = snapshot(universe=universe, source=src)
        return TaskResult(task_name=action, success=True,
                         message=f"A/D={snap.ad_ratio:.2f}, adv={snap.advancers}",
                         data=snap)

    else:
        return TaskResult(task_name=action, success=False, message=f"Unknown action: {action}")


# --- Quick setup helpers ---


def create_default_scheduler() -> Scheduler:
    """Create a scheduler with sensible default tasks.

    Tasks:
        - Watchlist alerts: every 5 minutes
        - BPJS scan: every 30 minutes (during trading hours)
        - Swing breakout: every hour
        - Signal generation: every 2 hours
    """
    scheduler = Scheduler()

    scheduler.add_task(ScheduledTask(
        name="watchlist_alerts",
        interval_minutes=5,
        action="check_alerts",
        params={"watchlist": "default"},
    ))
    scheduler.add_task(ScheduledTask(
        name="bpjs_scan",
        interval_minutes=30,
        action="screen_bpjs",
        params={"universe": "LQ45"},
    ))
    scheduler.add_task(ScheduledTask(
        name="breakout_scan",
        interval_minutes=60,
        action="screen_breakout",
        params={"universe": "LQ45"},
    ))
    scheduler.add_task(ScheduledTask(
        name="signal_gen",
        interval_minutes=120,
        action="generate_signals",
        params={"universe": "IDX30"},
    ))

    return scheduler
