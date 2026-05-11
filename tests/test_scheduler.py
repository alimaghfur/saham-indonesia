"""Tests for scheduler module."""
from datetime import datetime, timedelta

from saham_id.scheduler import Scheduler, ScheduledTask, TaskResult, create_default_scheduler


class TestScheduledTask:
    def test_is_due_never_run(self):
        task = ScheduledTask(name="test", interval_minutes=5, action="check_alerts")
        assert task.is_due is True

    def test_is_due_recently_run(self):
        task = ScheduledTask(name="test", interval_minutes=5, action="check_alerts")
        task.last_run = datetime.utcnow()
        assert task.is_due is False

    def test_is_due_expired(self):
        task = ScheduledTask(name="test", interval_minutes=5, action="check_alerts")
        task.last_run = datetime.utcnow() - timedelta(minutes=10)
        assert task.is_due is True

    def test_disabled_not_due(self):
        task = ScheduledTask(name="test", interval_minutes=5, action="check_alerts", enabled=False)
        assert task.is_due is False


class TestTaskResult:
    def test_create(self):
        result = TaskResult(task_name="test", success=True, message="ok")
        assert result.success is True
        assert result.timestamp is not None


class TestScheduler:
    def test_add_task(self):
        scheduler = Scheduler()
        scheduler.add_task(ScheduledTask(name="t1", interval_minutes=5, action="check_alerts"))
        assert len(scheduler.tasks) == 1

    def test_remove_task(self):
        scheduler = Scheduler()
        scheduler.add_task(ScheduledTask(name="t1", interval_minutes=5, action="check_alerts"))
        scheduler.remove_task("t1")
        assert len(scheduler.tasks) == 0

    def test_get_due_tasks(self):
        scheduler = Scheduler()
        scheduler.add_task(ScheduledTask(name="due", interval_minutes=5, action="check_alerts"))
        scheduler.add_task(ScheduledTask(name="not_due", interval_minutes=5, action="check_alerts",
                                        enabled=False))
        due = scheduler.get_due_tasks()
        assert len(due) == 1
        assert due[0].name == "due"


class TestCreateDefaultScheduler:
    def test_has_tasks(self):
        scheduler = create_default_scheduler()
        assert len(scheduler.tasks) >= 4
        names = [t.name for t in scheduler.tasks]
        assert "watchlist_alerts" in names
        assert "bpjs_scan" in names
        assert "breakout_scan" in names
        assert "signal_gen" in names
