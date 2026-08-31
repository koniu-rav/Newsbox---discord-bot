"""Scheduler service to manage timed briefing dispatches at 8:00 AM."""

import asyncio
from typing import Callable, Coroutine, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class SchedulerService:
    """Async background task scheduler using APScheduler."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def schedule_daily_briefing(self, briefing_job: Callable[[], Coroutine[Any, Any, None]]) -> None:
        """Register daily briefing job based on configured time (default 08:00)."""
        time_parts = self.settings.briefing_time.split(":")
        hour = int(time_parts[0]) if len(time_parts) > 0 else 8
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )

        self.scheduler.add_job(
            briefing_job,
            trigger=trigger,
            id="daily_macro_briefing",
            name="Daily 8:00 AM Macro Briefing",
            replace_existing=True,
        )
        logger.info(
            "Scheduled daily macro briefing for %02d:%02d (%s)",
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def start(self) -> None:
        """Start the scheduler background loop."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Scheduler service started.")

    def shutdown(self) -> None:
        """Gracefully stop the scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler service stopped.")

