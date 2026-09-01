"""Main Discord bot client class for Newsbox with VIP role and administrator authorization."""

import asyncio
from typing import Optional
import discord
from discord.ext import commands

from newsbox.cogs import COGS
from newsbox.config import get_settings
from newsbox.services.scheduler_service import SchedulerService
from newsbox.services.state_service import get_state_manager
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsboxBot(commands.Bot):
    """Newsbox Discord bot orchestrating scheduled briefings, calendar dispatches, and accuracy evaluations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.state_manager = get_state_manager()
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=self.settings.discord_command_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )

        self.scheduler = SchedulerService()
        # Register global permission check: Admin or VIP Role required
        self.add_check(self.check_admin_or_vip)

    async def check_admin_or_vip(self, ctx: commands.Context) -> bool:
        """Global authorization check: allow only Administrators and users with the Newsbox-vip role."""
        # 1. Allow application / bot owner
        try:
            if await self.is_owner(ctx.author):
                return True
        except Exception:
            pass

        # 2. In DMs: require server context
        if not ctx.guild:
            raise commands.CheckFailure("⛔ Komendy bota Newsbox można uruchamiać wyłącznie na serwerze Discord.")

        # 3. Allow Server Owner
        if ctx.guild.owner_id == ctx.author.id:
            return True

        # 4. Allow Discord Administrators
        perms = getattr(ctx.author, "guild_permissions", None)
        if perms and getattr(perms, "administrator", False):
            return True

        # 5. Allow users with the configured VIP role (e.g. 'Newsbox-vip')
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

        # 1. Schedule 7:00 AM Economic Calendar (Mon-Fri)
        self.scheduler.schedule_daily_calendar(self.dispatch_scheduled_calendar)

        # 2. Schedule 8:00 AM Macro & FX/DAX Briefing (Mon-Fri)
        self.scheduler.schedule_daily_briefing(self.dispatch_scheduled_macro_briefing)

        # 3. Schedule 12:30 PM Accuracy & Performance Evaluation (Mon-Fri)
        self.scheduler.schedule_daily_accuracy(self.dispatch_scheduled_accuracy)

        self.scheduler.start()

    async def on_ready(self) -> None:
        """Event triggered when Discord gateway connection is established."""
        logger.info("Connected to Discord as %s (ID: %s)", self.user.name, self.user.id)
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Rynki & Makro | {self.settings.discord_command_prefix}briefing",
        )
        await self.change_presence(activity=activity)

    async def dispatch_scheduled_calendar(self) -> None:
        """Executed automatically at 7:00 AM to dispatch Economic Calendar to designated channel."""
        logger.info("Triggering scheduled 7:00 AM economic calendar dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            logger.error("BriefingsCog not found during scheduled calendar dispatch.")
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
        else:
            logger.warning("No channel configured for 7:00 AM calendar dispatch.")

    async def dispatch_scheduled_macro_briefing(self) -> None:
        """Executed automatically at 8:00 AM to dispatch morning macro report to designated channel."""
        logger.info("Triggering scheduled 8:00 AM macro briefing dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            logger.error("BriefingsCog not found during scheduled macro dispatch.")
            return

        macro_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if macro_ch_id:
            channel = await self._resolve_channel(macro_ch_id)
            if channel:
                await briefings_cog.compile_and_send_macro_briefing(channel, is_scheduled=True)
        else:
            logger.warning("No channel configured for 8:00 AM macro briefing dispatch.")

    async def dispatch_scheduled_accuracy(self) -> None:
        """Executed automatically at 12:30 PM to evaluate briefing accuracy and send performance report."""
        logger.info("Triggering scheduled 12:30 PM accuracy evaluation dispatch...")
        briefings_cog = self.get_cog("Briefings & Trader Advisory")
        if not briefings_cog:
            logger.error("BriefingsCog not found during scheduled accuracy dispatch.")
            return

        target_ch_id = self.state_manager.get_channel("macro") or self.settings.macro_channel_id
        if target_ch_id:
            channel = await self._resolve_channel(target_ch_id)
            if channel:
                await briefings_cog.compile_and_send_accuracy_report(channel)
        else:
            logger.warning("No channel configured for 12:30 PM accuracy dispatch.")

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

    async def close(self) -> None:
        """Gracefully shut down scheduler and bot connection."""
        self.scheduler.shutdown()
        await super().close()
