"""Subscriptions Cog - manages server briefing channel assignments."""

import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class SubscriptionsCog(commands.Cog, name="Subscriptions"):
    """Cog for configuring channel subscriptions for automatic morning briefings."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()

    @commands.command(name="set_briefing_channel")
    @commands.has_permissions(administrator=True)
    async def set_briefing_channel(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set the target text channel for scheduled 8:00 AM daily briefings."""
        target_channel = channel or ctx.channel
        if not isinstance(target_channel, discord.TextChannel):
            await ctx.send("❌ Please specify a valid text channel.")
            return

        # Update in-memory setting
        self.settings.discord_briefing_channel_id = target_channel.id
        logger.info("Briefing channel set to #%s (ID: %s)", target_channel.name, target_channel.id)

        await ctx.send(
            f"✅ Daily briefings will now be automatically posted in {target_channel.mention} at "
            f"**{self.settings.briefing_time} {self.settings.briefing_timezone}**."
        )


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(SubscriptionsCog(bot))

