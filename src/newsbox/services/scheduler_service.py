"""Scheduler service to manage timed automated dispatches Monday-Friday (7:00 Calendar, 8:00 Briefing, 12:30 Accuracy)."""

from typing import Callable, Coroutine, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class SchedulerService:
    """Async background task scheduler using APScheduler (restricted to trading days Mon-Fri)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def schedule_daily_calendar(
        self,
        calendar_job: Callable[[], Coroutine[Any, Any, None]],
        time_str: Optional[str] = None,
    ) -> None:
        """Register daily economic calendar job (Mon-Fri at 07:00)."""
        target_time = time_str or self.settings.calendar_time
        time_parts = target_time.split(":")
        hour = int(time_parts[0]) if len(time_parts) > 0 else 7
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        trigger = CronTrigger(
            day_of_week="mon-fri",
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )

        self.scheduler.add_job(
            calendar_job,
            trigger=trigger,
            id="daily_economic_calendar",
            name="Mon-Fri 7:00 AM Economic Calendar",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Mon-Fri economic calendar for %02d:%02d (%s)",
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def schedule_daily_briefing(
        self,
        briefing_job: Callable[[], Coroutine[Any, Any, None]],
        time_str: Optional[str] = None,
    ) -> None:
        """Register daily macro briefing job (Mon-Fri at 08:00)."""
        target_time = time_str or self.settings.briefing_time
        time_parts = target_time.split(":")
        hour = int(time_parts[0]) if len(time_parts) > 0 else 8
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        trigger = CronTrigger(
            day_of_week="mon-fri",
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )

        self.scheduler.add_job(
            briefing_job,
            trigger=trigger,
            id="daily_macro_briefing",
            name="Mon-Fri 8:00 AM Macro Briefing",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Mon-Fri macro briefing for %02d:%02d (%s)",
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def schedule_daily_accuracy(
        self,
        accuracy_job: Callable[[], Coroutine[Any, Any, None]],
        time_str: Optional[str] = None,
    ) -> None:
        """Register daily accuracy & performance evaluation job (Mon-Fri at 12:30)."""
        target_time = time_str or self.settings.accuracy_time
        time_parts = target_time.split(":")
        hour = int(time_parts[0]) if len(time_parts) > 0 else 12
        minute = int(time_parts[1]) if len(time_parts) > 1 else 30

        trigger = CronTrigger(
            day_of_week="mon-fri",
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )

        self.scheduler.add_job(
            accuracy_job,
            trigger=trigger,
            id="daily_accuracy_evaluation",
            name="Mon-Fri 12:30 PM Accuracy Evaluation",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Mon-Fri accuracy evaluation for %02d:%02d (%s)",
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def start(self) -> None:
        """Start the scheduler background loop."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Scheduler service started (Mon-Fri active).")

    def shutdown(self) -> None:
        """Gracefully stop the scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler service stopped.")
