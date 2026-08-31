"""Main Newsbox Discord Bot implementation with multi-channel dispatch."""

import asyncio
import discord
from discord.ext import commands

from newsbox.cogs import COGS
from newsbox.config import get_settings
from newsbox.services.scheduler_service import SchedulerService
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsboxBot(commands.Bot):
    """Core Discord bot class for Newsbox."""

    def __init__(self) -> None:
        self.settings = get_settings()
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix=self.settings.discord_command_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )
        self.scheduler = SchedulerService()

    async def setup_hook(self) -> None:
        """Initialize extensions and background scheduler on bot setup."""
        for extension in COGS:
            try:
                await self.load_extension(extension)
                logger.info("Loaded extension: %s", extension)
            except Exception as e:
                logger.error("Failed to load extension %s: %s", extension, e, exc_info=True)

        # Schedule 8:00 AM daily briefing
        self.scheduler.schedule_daily_briefing(self.dispatch_scheduled_morning_routine)
        self.scheduler.start()

    async def on_ready(self) -> None:
        """Event triggered when Discord gateway connection is established."""
        logger.info("Connected to Discord as %s (ID: %s)", self.user.name, self.user.id)
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Rynki & Makro | {self.settings.discord_command_prefix}briefing",
        )
        await self.change_presence(activity=activity)

    async def dispatch_scheduled_morning_routine(self) -> None:
        """Executed by scheduler to send daily reports to configured Discord channels."""
        logger.info("Triggering scheduled 8:00 AM morning routines...")

        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            logger.error("BriefingsCog not found during scheduled dispatch.")
            return

        # 1. Dispatch Macro Briefing + Trader Advisory
        macro_ch_id = self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_macro_briefing(channel)
        else:
            logger.warning("No macro briefing channel configured.")

        # 2. Dispatch Economic Calendar (if dedicated channel is configured)
        cal_ch_id = self.settings.discord_calendar_channel_id
        if cal_ch_id:
            channel = await self._resolve_channel(cal_ch_id)
            if channel:
                await briefings_cog.compile_and_send_calendar_briefing(channel)

    async def _resolve_channel(self, channel_id: int) -> discord.abc.Messageable | None:
        """Fetch or get channel by ID."""
        channel = self.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception as ex:
                logger.error("Could not fetch channel ID %s: %s", channel_id, ex)
                return None
        return channel

    async def close(self) -> None:
        """Gracefully shut down scheduler and bot connection."""
        self.scheduler.shutdown()
        await super().close()
