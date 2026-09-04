"""Scheduler service to manage timed automated dispatches:
- Sunday 10:00 AM: Weekly Strategic Outlook
- Mon-Fri 07:00 AM: London Session Briefing (1h before pre-market)
- Mon-Fri 13:30 PM: New York Session Briefing (1h before pre-market/data)
- Mon-Fri 23:00 PM: Asia Session Briefing (1h before pre-market)
- Mon-Fri Session Accuracy Evaluations (London 17:30, NY 22:00, Asia 07:00)
- Every 30 min (:00, :30): Global Flash News
"""

from datetime import datetime
from typing import Callable, Coroutine, Any, Optional
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

    def schedule_weekly_outlook(
        self,
        weekly_job: Callable[[], Coroutine[Any, Any, None]],
        day_of_week: str = "sun",
        hour: int = 10,
        minute: int = 0,
    ) -> None:
        """Register Sunday 10:00 AM weekly strategic outlook job."""
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )
        self.scheduler.add_job(
            weekly_job,
            trigger=trigger,
            id="weekly_strategic_outlook",
            name="Sunday 10:00 AM Weekly Outlook",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Sunday Weekly Strategic Outlook for %s %02d:%02d (%s)",
            day_of_week.upper(),
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def schedule_session_briefing(
        self,
        session_key: str,
        briefing_job: Callable[[], Coroutine[Any, Any, None]],
        hour: int,
        minute: int,
        day_of_week: str = "mon-fri",
    ) -> None:
        """Register daily session briefing (London 07:00, New York 13:30, Asia 23:00)."""
        s_clean = session_key.lower().strip()
        job_id = f"session_briefing_{s_clean}"
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )
        self.scheduler.add_job(
            briefing_job,
            trigger=trigger,
            id=job_id,
            name=f"Mon-Fri {s_clean.upper()} Session Briefing ({hour:02d}:{minute:02d})",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Mon-Fri %s session briefing for %02d:%02d (%s)",
            s_clean.upper(),
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def schedule_session_evaluation(
        self,
        session_key: str,
        eval_job: Callable[[], Coroutine[Any, Any, None]],
        hour: int,
        minute: int,
        day_of_week: str = "mon-fri",
    ) -> None:
        """Register daily session evaluation job (London 17:30, NY 22:00, Asia 07:00)."""
        s_clean = session_key.lower().strip()
        job_id = f"session_eval_{s_clean}"
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )
        self.scheduler.add_job(
            eval_job,
            trigger=trigger,
            id=job_id,
            name=f"Mon-Fri {s_clean.upper()} Session Evaluation ({hour:02d}:{minute:02d})",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Mon-Fri %s session accuracy evaluation for %02d:%02d (%s)",
            s_clean.upper(),
            hour,
            minute,
            self.settings.briefing_timezone,
        )

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
        """Legacy alias: default daily morning briefing (08:00 or London session)."""
        target_time = time_str or self.settings.briefing_time
        time_parts = target_time.split(":")
        hour = int(time_parts[0]) if len(time_parts) > 0 else 8
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        self.schedule_session_briefing("london", briefing_job, hour=hour, minute=minute)

    def schedule_daily_accuracy(
        self,
        accuracy_job: Callable[[], Coroutine[Any, Any, None]],
        time_str: Optional[str] = None,
    ) -> None:
        """Legacy alias: accuracy evaluation."""
        target_time = time_str or self.settings.accuracy_time
        time_parts = target_time.split(":")
        hour = int(time_parts[0]) if len(time_parts) > 0 else 12
        minute = int(time_parts[1]) if len(time_parts) > 1 else 30

        self.schedule_session_evaluation("london", accuracy_job, hour=hour, minute=minute)

    def schedule_periodic_flash_news(
        self,
        flash_news_job: Callable[[], Coroutine[Any, Any, None]],
        minute_cron: str = "25,55",
    ) -> None:
        """Register periodic global flash news job (every :25 and :55 past the hour)."""
        trigger = CronTrigger(
            minute=minute_cron,
            timezone=self.settings.briefing_timezone,
        )

        self.scheduler.add_job(
            flash_news_job,
            trigger=trigger,
            id="periodic_flash_news",
            name="Global Flash News (:25 and :55)",
            replace_existing=True,
        )
        logger.info("Scheduled Global Flash News at :25 and :55 (%s)", self.settings.briefing_timezone)

    def schedule_weekly_portfolio(
        self,
        portfolio_job: Callable[[], Coroutine[Any, Any, None]],
        day_of_week: str = "sun",
        hour: int = 18,
        minute: int = 0,
    ) -> None:
        """Register weekly portfolio report job (e.g. Sunday 18:00 CET)."""
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )
        self.scheduler.add_job(
            portfolio_job,
            trigger=trigger,
            id="weekly_portfolio_report",
            name=f"Weekly Portfolio Report ({day_of_week.upper()} {hour:02d}:{minute:02d})",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Weekly Portfolio Report for %s %02d:%02d (%s)",
            day_of_week.upper(),
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def schedule_daily_portfolio_news(
        self,
        portfolio_news_job: Callable[[], Coroutine[Any, Any, None]],
        hour: int = 14,
        minute: int = 0,
        day_of_week: str = "*",
    ) -> None:
        """Register daily portfolio company news job (every day at 14:00 CET)."""
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )
        self.scheduler.add_job(
            portfolio_news_job,
            trigger=trigger,
            id="daily_portfolio_news",
            name=f"Daily Portfolio News ({hour:02d}:{minute:02d})",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Daily Portfolio News for %s at %02d:%02d (%s)",
            day_of_week,
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def schedule_weekly_accuracy(
        self,
        accuracy_job: Callable[[], Coroutine[Any, Any, None]],
        day_of_week: str = "sat",
        hour: int = 12,
        minute: int = 0,
    ) -> None:
        """Register Saturday 12:00 PM Weekly Accuracy Summary Report."""
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.settings.briefing_timezone,
        )
        self.scheduler.add_job(
            accuracy_job,
            trigger=trigger,
            id="weekly_accuracy_report",
            name=f"Saturday {hour:02d}:{minute:02d} Weekly Accuracy Report",
            replace_existing=True,
        )
        logger.info(
            "Scheduled Saturday Weekly Accuracy Report for %s %02d:%02d (%s)",
            day_of_week.upper(),
            hour,
            minute,
            self.settings.briefing_timezone,
        )

    def reschedule_cron_job(
        self,
        job_id: str,
        day_of_week: Optional[str] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        minute_cron: Optional[str] = None,
    ) -> bool:
        """Dynamically update an existing job's schedule in APScheduler."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.warning("Job %s not found in scheduler to reschedule", job_id)
                return False

            if minute_cron is not None:
                trigger = CronTrigger(
                    minute=minute_cron,
                    timezone=self.settings.briefing_timezone,
                )
            else:
                trigger = CronTrigger(
                    day_of_week=day_of_week if day_of_week else "*",
                    hour=hour if hour is not None else 0,
                    minute=minute if minute is not None else 0,
                    timezone=self.settings.briefing_timezone,
                )
            job.reschedule(trigger=trigger)
            logger.info("Rescheduled job %s with trigger %s (next: %s)", job_id, trigger, job.next_run_time)
            return True
        except Exception as e:
            logger.error("Failed to reschedule job %s: %s", job_id, e)
            return False

    def get_job_next_run(self, job_id: str) -> Optional[datetime]:
        """Return next run datetime for a scheduled job or None."""
        try:
            job = self.scheduler.get_job(job_id)
            return job.next_run_time if job else None
        except Exception:
            return None

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
