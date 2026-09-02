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

        # 1. Schedule Sunday 10:00 AM Weekly Strategic Outlook
        self.scheduler.schedule_weekly_outlook(self.dispatch_scheduled_weekly_outlook, day_of_week="sun", hour=10, minute=0)

        # 2. Schedule Mon-Fri 07:00 AM Economic Calendar & London Session Briefing (1h before pre-market)
        self.scheduler.schedule_daily_calendar(self.dispatch_scheduled_calendar)
        self.scheduler.schedule_session_briefing("london", self.dispatch_scheduled_london_briefing, hour=7, minute=0)

        # 3. Schedule Mon-Fri 13:30 PM New York Session Briefing (1h before pre-market/data)
        self.scheduler.schedule_session_briefing("newyork", self.dispatch_scheduled_ny_briefing, hour=13, minute=30)

        # 4. Schedule Mon-Fri 23:00 PM Asia Session Briefing (1h before pre-market)
        self.scheduler.schedule_session_briefing("asia", self.dispatch_scheduled_asia_briefing, hour=23, minute=0)

        # 5. Schedule Mon-Fri Session Accuracy Evaluations
        # London evaluated at 17:30 CET (close of European cash)
        self.scheduler.schedule_session_evaluation("london", self.dispatch_scheduled_london_eval, hour=17, minute=30)
        # New York evaluated at 22:00 CET (Wall St close)
        self.scheduler.schedule_session_evaluation("newyork", self.dispatch_scheduled_ny_eval, hour=22, minute=0)
        # Asia evaluated at 07:00 CET next morning
        self.scheduler.schedule_session_evaluation("asia", self.dispatch_scheduled_asia_eval, hour=7, minute=0)

        # 6. Schedule Periodic 30-Minute Global Flash News (:00 and :30)
        self.scheduler.schedule_periodic_flash_news(self.dispatch_scheduled_flash_news)

        self.scheduler.start()

    async def on_ready(self) -> None:
        """Event triggered when Discord gateway connection is established."""
        logger.info("Connected to Discord as %s (ID: %s) • we.trade", self.user.name, self.user.id)
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
        """Executed at 17:30 PM to evaluate London session accuracy."""
        logger.info("Triggering scheduled 17:30 PM London session accuracy evaluation...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return
        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_session_accuracy(channel, session_key="london")

    async def dispatch_scheduled_ny_eval(self) -> None:
        """Executed at 22:00 PM to evaluate New York session accuracy."""
        logger.info("Triggering scheduled 22:00 PM New York session accuracy evaluation...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return
        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_session_accuracy(channel, session_key="newyork")

    async def dispatch_scheduled_asia_eval(self) -> None:
        """Executed at 07:00 AM to evaluate Asia session accuracy."""
        logger.info("Triggering scheduled 07:00 AM Asia session accuracy evaluation...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            return
        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_session_accuracy(channel, session_key="asia")

    async def dispatch_scheduled_calendar(self) -> None:
        """Executed automatically at 7:00 AM to dispatch Economic Calendar to designated channel."""
        logger.info("Triggering scheduled 7:00 AM economic calendar dispatch...")
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

    async def dispatch_scheduled_flash_news(self) -> None:
        """Executed automatically every 30 minutes to dispatch 2-3 sentence global flash news to channel 1544598484961722409."""
        logger.info("Triggering periodic 30-minute global flash news dispatch...")
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
        from newsbox.utils.embeds import create_error_embed

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
            await ctx.send(embed=create_error_embed(err_title, err_msg))
        except Exception:
            pass
