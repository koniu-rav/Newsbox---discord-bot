"""Main Discord Bot application class for Newsbox with multi-session dispatching and authorization."""

import sys
from typing import Optional
import discord
from discord.ext import commands

from newsbox.config import get_settings
from newsbox.services.scheduler_service import SchedulerService
from newsbox.services.state_service import StateManager
from newsbox.utils.logger import setup_logger

logger = setup_logger("newsbox")

COGS = [
    "newsbox.cogs.briefings",
    "newsbox.cogs.news",
    "newsbox.cogs.portfolio",
    "newsbox.cogs.channels",
    "newsbox.cogs.schedules",
    "newsbox.cogs.admin",
]


class NewsboxBot(commands.Bot):
    """Newsbox automated market analysis, economic calendar, and news Discord bot."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.state_manager = StateManager()

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(self.settings.command_prefix),
            intents=intents,
            help_command=None,
            description="Newsbox by we.trade • Społeczność Inwestorów & Traderów",
        )

        self.scheduler = SchedulerService()

        # Add global authorization check
        self.add_check(self.check_admin_or_vip)

    async def check_admin_or_vip(self, ctx: commands.Context) -> bool:
        """Global check restricting bot usage to Administrators and users with the Newsbox-vip role."""
        if await self.is_owner(ctx.author):
            return True

        if ctx.guild is None:
            return True

        if ctx.author == ctx.guild.owner:
            return True

        permissions = getattr(ctx.author, "guild_permissions", None)
        if permissions and (permissions.administrator or permissions.manage_guild):
            return True

        vip_target = self.settings.vip_role_name.lower().strip()
        user_roles = getattr(ctx.author, "roles", [])
        if any(r.name.lower().strip() == vip_target for r in user_roles):
            return True

        raise commands.CheckFailure(
            f"Dostęp do komend bota Newsbox mają wyłącznie Administratorzy oraz użytkownicy z rolą `{self.settings.vip_role_name}`."
        )

    async def setup_hook(self) -> None:
        """Executed during bot startup to load cogs and start automated schedule."""
        for extension in COGS:
            try:
                await self.load_extension(extension)
                logger.info("Loaded extension: %s", extension)
            except Exception as e:
                logger.error("Failed to load extension %s: %s", extension, e, exc_info=True)

        # Load persisted schedules from state_manager
        sched = self.state_manager.get_all_schedules()

        # 1. Schedule Weekly Strategic Outlook
        wo = sched.get("weekly_outlook", {"day_of_week": "sun", "hour": 10, "minute": 0})
        self.scheduler.schedule_weekly_outlook(
            self.dispatch_scheduled_weekly_outlook,
            day_of_week=wo.get("day_of_week", "sun"),
            hour=wo.get("hour", 10),
            minute=wo.get("minute", 0),
        )

        # 2. Schedule Daily Economic Calendar
        cal = sched.get("calendar", {"day_of_week": "mon-fri", "hour": 7, "minute": 0})
        self.scheduler.schedule_daily_calendar(
            self.dispatch_scheduled_calendar,
            time_str=f"{cal.get('hour', 7):02d}:{cal.get('minute', 0):02d}",
        )

        # 3. Schedule 3-Tier Multi-Session Trader Advisory Briefings
        lon = sched.get("london", {"day_of_week": "mon-fri", "hour": 7, "minute": 0})
        self.scheduler.schedule_session_briefing(
            "london",
            self.dispatch_scheduled_london_briefing,
            hour=lon.get("hour", 7),
            minute=lon.get("minute", 0),
            day_of_week=lon.get("day_of_week", "mon-fri"),
        )

        ny = sched.get("newyork", {"day_of_week": "mon-fri", "hour": 13, "minute": 30})
        self.scheduler.schedule_session_briefing(
            "newyork",
            self.dispatch_scheduled_ny_briefing,
            hour=ny.get("hour", 13),
            minute=ny.get("minute", 30),
            day_of_week=ny.get("day_of_week", "mon-fri"),
        )

        asia = sched.get("asia", {"day_of_week": "sun-thu", "hour": 23, "minute": 0})
        self.scheduler.schedule_session_briefing(
            "asia",
            self.dispatch_scheduled_asia_briefing,
            hour=asia.get("hour", 23),
            minute=asia.get("minute", 0),
            day_of_week=asia.get("day_of_week", "sun-thu"),
        )

        # 4. Quiet Background Session Accuracy Evaluations
        self.scheduler.schedule_session_evaluation("london", self.dispatch_scheduled_london_eval, hour=17, minute=30)
        self.scheduler.schedule_session_evaluation("newyork", self.dispatch_scheduled_ny_eval, hour=22, minute=0)
        self.scheduler.schedule_session_evaluation("asia", self.dispatch_scheduled_asia_eval, hour=7, minute=0)

        # 5. Schedule Weekly Accuracy Report
        acc = sched.get("accuracy", {"day_of_week": "sat", "hour": 12, "minute": 0})
        self.scheduler.schedule_weekly_accuracy(
            self.dispatch_scheduled_weekly_accuracy,
            day_of_week=acc.get("day_of_week", "sat"),
            hour=acc.get("hour", 12),
            minute=acc.get("minute", 0),
        )

        # 6. Schedule Periodic Global Flash News
        flash = sched.get("flash_news", {"minute_cron": "5,35"})
        self.scheduler.schedule_periodic_flash_news(
            self.dispatch_scheduled_flash_news,
            minute_cron=flash.get("minute_cron", "5,35"),
        )

        # 7. Schedule Weekly Portfolio Report
        port = sched.get("portfolio", {"day_of_week": "sun", "hour": 18, "minute": 0})
        self.scheduler.schedule_weekly_portfolio(
            self.dispatch_scheduled_weekly_portfolio,
            day_of_week=port.get("day_of_week", "sun"),
            hour=port.get("hour", 18),
            minute=port.get("minute", 0),
        )

        # 8. Schedule Daily Portfolio News
        pnews = sched.get("portfolio_news", {"day_of_week": "*", "hour": 14, "minute": 0})
        self.scheduler.schedule_daily_portfolio_news(
            self.dispatch_scheduled_daily_portfolio_news,
            day_of_week=pnews.get("day_of_week", "*"),
            hour=pnews.get("hour", 14),
            minute=pnews.get("minute", 0),
        )

        # 9. Schedule Real-Time Macro Alerts Monitor (every 45 seconds)
        self.scheduler.schedule_realtime_macro_alerts(
            self.dispatch_realtime_macro_alerts,
            interval_seconds=45,
        )

        self.scheduler.start()


    async def on_ready(self) -> None:
        """Event triggered when Discord gateway connection is established."""
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="we.trade • Społeczność Traderów | !briefing",
        )
        await self.change_presence(activity=activity)

    async def dispatch_scheduled_weekly_outlook(self) -> None:
        """Executed automatically on Sunday at 10:00 AM to dispatch Strategic Weekly Outlook."""
        logger.info("Triggering scheduled Sunday 10:00 AM Weekly Strategic Outlook dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return
        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_weekly_outlook(channel)

    async def dispatch_scheduled_london_briefing(self) -> None:
        """Executed automatically at 07:00 AM to dispatch London session briefing."""
        logger.info("Triggering scheduled 07:00 AM London session briefing dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return
        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_session_briefing(channel, session_key="london", is_scheduled=True)

    async def dispatch_scheduled_ny_briefing(self) -> None:
        """Executed automatically at 13:30 PM to dispatch New York session briefing."""
        logger.info("Triggering scheduled 13:30 PM New York session briefing dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return
        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_session_briefing(channel, session_key="newyork", is_scheduled=True)

    async def dispatch_scheduled_asia_briefing(self) -> None:
        """Executed automatically at 23:00 PM to dispatch Asia session briefing."""
        logger.info("Triggering scheduled 23:00 PM Asia session briefing dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return
        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_session_briefing(channel, session_key="asia", is_scheduled=True)

    async def dispatch_scheduled_london_eval(self) -> None:
        """Executed at 17:30 PM to evaluate London session accuracy quietly into history."""
        logger.info("Executing quiet background evaluation for London session...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if briefings_cog:
            await briefings_cog.evaluate_session_quietly(session_key="london")

    async def dispatch_scheduled_ny_eval(self) -> None:
        """Executed at 22:00 PM to evaluate New York session accuracy quietly into history."""
        logger.info("Executing quiet background evaluation for New York session...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if briefings_cog:
            await briefings_cog.evaluate_session_quietly(session_key="newyork")

    async def dispatch_scheduled_asia_eval(self) -> None:
        """Executed at 07:00 AM to evaluate Asia session accuracy quietly into history."""
        logger.info("Executing quiet background evaluation for Asia session...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if briefings_cog:
            await briefings_cog.evaluate_session_quietly(session_key="asia")

    async def dispatch_scheduled_weekly_accuracy(self) -> None:
        """Executed automatically on Saturday at 12:00 PM to dispatch the single Weekly Accuracy Report."""
        logger.info("Triggering scheduled Saturday 12:00 PM Weekly Accuracy Report dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")

        acc_ch_id = (
            self.state_manager.get_channel("accuracy")
            or self.settings.discord_accuracy_channel_id
        )
        if acc_ch_id:
            channel = await self._resolve_channel(acc_ch_id)
            if channel:
                await briefings_cog.compile_and_send_weekly_accuracy(channel)

    async def dispatch_scheduled_calendar(self) -> None:
        """Executed automatically to dispatch Economic Calendar to designated channel."""
        logger.info("Triggering scheduled economic calendar dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return

        cal_ch_id = (
            self.state_manager.get_channel("calendar")
            or self.settings.discord_calendar_channel_id
            or self.state_manager.get_channel("macro")
            or self.settings.macro_channel_id
        )
        if cal_ch_id:
            channel = await self._resolve_channel(cal_ch_id)
            if channel:
                await briefings_cog.compile_and_send_calendar_briefing(channel)

    async def dispatch_realtime_macro_alerts(self) -> None:
        """Executed periodically (every 45s) to check for newly published high/medium macro releases."""
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return

        target_ch_id = (
            self.state_manager.get_channel("macro_alerts")
            or self.settings.discord_macro_alerts_channel_id
        )
        if not target_ch_id:
            return

        channel = await self._resolve_channel(target_ch_id)
        if not channel:
            return

        try:
            await briefings_cog.check_and_dispatch_macro_alerts(channel)
        except Exception as e:
            logger.error("Error in realtime macro alerts dispatch: %s", e, exc_info=True)

    async def dispatch_scheduled_flash_news(self) -> None:
        """Executed automatically to dispatch 2-3 sentence global flash news."""
        logger.info("Triggering periodic global flash news dispatch...")
        news_cog = self.get_cog("News Feed")
        if not news_cog:
            return

        flash_ch_id = (
            self.state_manager.get_channel("news_global")
            or self.settings.discord_news_global_channel_id
            or 1544598484961722409
        )
        if flash_ch_id:
            channel = await self._resolve_channel(flash_ch_id)
            if channel:
                await news_cog.compile_and_send_flash_news(channel)
    async def dispatch_scheduled_weekly_portfolio(self) -> None:
        """Executed weekly (Sunday 18:00 CET) to dispatch portfolio summary report."""
        logger.info("Triggering scheduled weekly portfolio report dispatch...")
        portfolio_cog = self.get_cog("Portfolio Tracker")
        if not portfolio_cog:
            return

        port_ch_id = (
            self.state_manager.get_channel("portfolio")
            or self.settings.discord_portfolio_channel_id
            or 1544262150455955516
        )
        if port_ch_id:
            channel = await self._resolve_channel(port_ch_id)
            if channel:
                await portfolio_cog.compile_and_send_portfolio_report(channel)

    async def dispatch_scheduled_daily_portfolio_news(self) -> None:
        """Executed daily at 14:00 CET to dispatch company news for portfolio tickers to channel 1544262150455955516."""
        logger.info("Triggering scheduled 14:00 CET daily portfolio news dispatch...")
        portfolio_cog = self.get_cog("Portfolio Tracker")
        if not portfolio_cog:
            return

        news_ch_id = (
            self.state_manager.get_channel("portfolio_news")
            or self.settings.discord_portfolio_news_channel_id
            or 1544262150455955516
        )
        if news_ch_id:
            channel = await self._resolve_channel(news_ch_id)
            if channel:
                await portfolio_cog.compile_and_send_portfolio_news(channel)

    def reschedule_job(self, schedule_key: str) -> bool:
        """Dynamically reschedule an existing job from persistent state."""
        key_to_job_id = {
            "weekly_outlook": "weekly_strategic_outlook",
            "calendar": "daily_economic_calendar",
            "london": "session_briefing_london",
            "newyork": "session_briefing_newyork",
            "asia": "session_briefing_asia",
            "accuracy": "weekly_accuracy_report",
            "portfolio": "weekly_portfolio_report",
            "portfolio_news": "daily_portfolio_news",
            "flash_news": "periodic_flash_news",
        }
        job_id = key_to_job_id.get(schedule_key.lower().strip())
        if not job_id:
            return False

        config = self.state_manager.get_schedule(schedule_key)
        if not config:
            return False

        if schedule_key.lower().strip() == "flash_news":
            return self.scheduler.reschedule_cron_job(
                job_id=job_id,
                minute_cron=config.get("minute_cron", "5,35"),
            )
        else:
            return self.scheduler.reschedule_cron_job(
                job_id=job_id,
                day_of_week=config.get("day_of_week", "*"),
                hour=config.get("hour", 12),
                minute=config.get("minute", 0),
            )

    async def _resolve_channel(self, channel_id: int) -> Optional[discord.abc.Messageable]:
        """Fetch or get channel by ID."""
        channel = self.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception as ex:
                logger.error("Could not fetch channel ID %s: %s", channel_id, ex)
                return None
        return channel

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Global error handler for bot commands."""
        logger.warning("Command '%s' error for user %s: %s", ctx.command, ctx.author, error)
        from newsbox.utils.embeds import format_error_message, send_full_message

        if isinstance(error, commands.CheckFailure):
            err_title = "Brak Uprawnień"
            err_msg = str(error)
        elif isinstance(error, commands.CommandNotFound):
            return
        else:
            err_title = "Błąd wykonania komendy"
            err_msg = str(error)
            if hasattr(error, "original"):
                err_msg = str(error.original)

        try:
            await send_full_message(ctx.channel, format_error_message(err_title, err_msg))
        except Exception:
            pass
