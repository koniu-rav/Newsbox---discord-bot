from typing import Optional
import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChannelsCog(commands.Cog, name="Channel Routing"):
    """Manage which Discord channels receive specific reports and news feeds."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()

    @commands.command(name="set_channel", aliases=["ustaw_kanal"])
    @commands.has_permissions(administrator=True)
    async def set_channel(
        self,
        ctx: commands.Context,
        channel_type: str,
        channel: Optional[discord.TextChannel] = None,
    ) -> None:
        """Przypisz dany kanał Discord do wybranego typu powiadomień.

        Typy:
        - `macro` (lub `briefing`): Poranny raport 8:00 AM + Trader Advisory
        - `calendar` (lub `kalendarz`): Kalendarz ekonomiczny i ryzyka
        - `news_pl` (lub `pl`): Newsy z Polski / GPW / Parkiet
        - `news_global` (lub `global`, `us`): Newsy światowe i USA

        Przykład: `!set_channel macro #raport-makro`
        """
        target = channel or ctx.channel
        if not isinstance(target, discord.TextChannel):
            await ctx.send("❌ Proszę wskazać poprawny kanał tekstowy.")
            return

        c_type = channel_type.lower().strip()

        if c_type in ["macro", "briefing", "poranek"]:
            self.settings.discord_macro_channel_id = target.id
            self.settings.discord_briefing_channel_id = target.id
            desc = "🌅 Poranny Raport Makro & Trader Advisory (8:00)"
        elif c_type in ["calendar", "kalendarz"]:
            self.settings.discord_calendar_channel_id = target.id
            desc = "📅 Kalendarz Ekonomiczny & Ryzyka Sesji"
        elif c_type in ["news_pl", "pl", "polska", "gpw", "parkiet"]:
            self.settings.discord_news_pl_channel_id = target.id
            desc = "🇵🇱 Wiadomości z Polski & Parkiet GPW"
        elif c_type in ["news_global", "global", "us", "usa", "swiat"]:
            self.settings.discord_news_global_channel_id = target.id
            desc = "🌐 Wiadomości Światowe & USA"
        else:
            await ctx.send(
                "❌ Nieznany typ kanału. Dostępne: `macro`, `calendar`, `news_pl`, `news_global`."
            )
            return

        await ctx.send(f"✅ Kanał {target.mention} został ustawiony dla: **{desc}**.")
        logger.info("Routing updated: %s -> #%s (%s)", c_type, target.name, target.id)

    @commands.command(name="channels", aliases=["kanaly"])
    async def list_channels(self, ctx: commands.Context) -> None:
        """Pokaż aktualne przypisanie kanałów Discord."""
        embed = discord.Embed(
            title="📡 Konfiguracja Kanałów Powiadomień",
            color=0x3498DB,
        )

        def ch_mention(ch_id: Optional[int]) -> str:
            return f"<#{ch_id}>" if ch_id else "*Brak (nieustawiony)*"

        embed.add_field(
            name="🌅 Raport Makro (8:00 AM)",
            value=ch_mention(self.settings.macro_channel_id),
            inline=False,
        )
        embed.add_field(
            name="📅 Kalendarz Ekonomiczny",
            value=ch_mention(self.settings.discord_calendar_channel_id),
            inline=False,
        )
        embed.add_field(
            name="🇵🇱 Newsy Polska / GPW",
            value=ch_mention(self.settings.discord_news_pl_channel_id),
            inline=False,
        )
        embed.add_field(
            name="🌐 Newsy Globalne & USA",
            value=ch_mention(self.settings.discord_news_global_channel_id),
            inline=False,
        )

        embed.set_footer(text="Użyj !set_channel <typ> #kanal aby zmienić przypisanie.")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(ChannelsCog(bot))

