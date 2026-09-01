"""Channels Cog - manages multi-channel routing with persistent disk storage."""

from typing import Optional
import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.services.state_service import get_state_manager
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChannelsCog(commands.Cog, name="Channel Routing"):
    """Manage which Discord channels receive specific reports and news feeds."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.state_manager = get_state_manager()

    @commands.command(name="set_channel", aliases=["ustaw_kanal"])
    @commands.has_permissions(administrator=True)
    async def set_channel(
        self,
        ctx: commands.Context,
        channel_type: str,
        channel: Optional[discord.TextChannel] = None,
    ) -> None:
        """Przypisz dany kanał Discord do wybranego typu powiadomień i zapisz trwale.

        Typy:
        - `macro` (lub `briefing`): Poranny raport 8:00 AM + FX/DAX Advisory
        - `calendar` (lub `kalendarz`): Kalendarz ekonomiczny i ryzyka
        - `news_pl` (lub `pl`): Newsy z Polski / GPW / Parkiet
        - `news_global` (lub `global`, `us`): Newsy światowe i USA
        - `crypto` (lub `krypto`): Dedykowany kanał krypto (#crypto-chat)
        - `portfolio` (lub `portfel`): Alerty i komunikaty dla Twoich spółek

        Przykład: `!set_channel crypto #crypto-chat`
        """
        target = channel or ctx.channel
        if not isinstance(target, discord.TextChannel):
            await ctx.send("❌ Proszę wskazać poprawny kanał tekstowy.")
            return

        c_type = channel_type.lower().strip()

        type_descriptions = {
            "macro": "🌅 Poranny Raport Makro & FX/DAX Advisory (8:00)",
            "briefing": "🌅 Poranny Raport Makro & FX/DAX Advisory (8:00)",
            "poranek": "🌅 Poranny Raport Makro & FX/DAX Advisory (8:00)",
            "calendar": "📅 Kalendarz Ekonomiczny & Ryzyka Sesji",
            "kalendarz": "📅 Kalendarz Ekonomiczny & Ryzyka Sesji",
            "news_pl": "🇵🇱 Wiadomości z Polski & Parkiet GPW",
            "pl": "🇵🇱 Wiadomości z Polski & Parkiet GPW",
            "polska": "🇵🇱 Wiadomości z Polski & Parkiet GPW",
            "gpw": "🇵🇱 Wiadomości z Polski & Parkiet GPW",
            "parkiet": "🇵🇱 Wiadomości z Polski & Parkiet GPW",
            "news_global": "🌐 Wiadomości Światowe & USA",
            "global": "🌐 Wiadomości Światowe & USA",
            "us": "🌐 Wiadomości Światowe & USA",
            "usa": "🌐 Wiadomości Światowe & USA",
            "swiat": "🌐 Wiadomości Światowe & USA",
            "crypto": "🪙 Dedykowany Kanał Krypto (#crypto-chat)",
            "krypto": "🪙 Dedykowany Kanał Krypto (#crypto-chat)",
            "crypto-chat": "🪙 Dedykowany Kanał Krypto (#crypto-chat)",
            "btc": "🪙 Dedykowany Kanał Krypto (#crypto-chat)",
            "portfolio": "💼 Alerty & Wiadomości Spółek Portfelowych",
            "portfel": "💼 Alerty & Wiadomości Spółek Portfelowych",
            "spolki": "💼 Alerty & Wiadomości Spółek Portfelowych",
        }

        if c_type not in type_descriptions:
            await ctx.send(
                "❌ Nieznany typ kanału. Dostępne: `macro`, `calendar`, `news_pl`, `news_global`, `crypto`, `portfolio`."
            )
            return

        # Canonical key
        canonical_key = "macro"
        if c_type in ["calendar", "kalendarz"]:
            canonical_key = "calendar"
        elif c_type in ["news_pl", "pl", "polska", "gpw", "parkiet"]:
            canonical_key = "news_pl"
        elif c_type in ["news_global", "global", "us", "usa", "swiat"]:
            canonical_key = "news_global"
        elif c_type in ["crypto", "krypto", "crypto-chat", "btc"]:
            canonical_key = "crypto"
        elif c_type in ["portfolio", "portfel", "spolki"]:
            canonical_key = "portfolio"

        self.state_manager.set_channel(canonical_key, target.id)
        desc = type_descriptions[c_type]

        await ctx.send(f"✅ Kanał {target.mention} został przypisany i **trwale zapisany** dla: **{desc}**.")
        logger.info("Routing updated & persisted: %s -> #%s (%s)", canonical_key, target.name, target.id)

    @commands.command(name="channels", aliases=["kanaly"])
    async def list_channels(self, ctx: commands.Context) -> None:
        """Pokaż aktualne przypisanie kanałów Discord."""
        embed = discord.Embed(
            title="📡 Konfiguracja Kanałów Powiadomień (Trwały Zapis)",
            color=0x3498DB,
        )

        channels = self.state_manager.get_all_channels()

        def ch_mention(ch_id: Optional[int]) -> str:
            return f"<#{ch_id}>" if ch_id else "*Brak (nieustawiony)*"

        embed.add_field(
            name="🌅 Raport Makro (8:00 AM)",
            value=ch_mention(channels.get("macro") or self.settings.macro_channel_id),
            inline=False,
        )
        embed.add_field(
            name="📅 Kalendarz Ekonomiczny",
            value=ch_mention(channels.get("calendar")),
            inline=False,
        )
        embed.add_field(
            name="🇵🇱 Newsy Polska / GPW",
            value=ch_mention(channels.get("news_pl")),
            inline=False,
        )
        embed.add_field(
            name="🌐 Newsy Globalne & USA",
            value=ch_mention(channels.get("news_global")),
            inline=False,
        )
        embed.add_field(
            name="🪙 Krypto (#crypto-chat)",
            value=ch_mention(channels.get("crypto")),
            inline=False,
        )
        embed.add_field(
            name="💼 Portfel Spółek",
            value=ch_mention(channels.get("portfolio")),
            inline=False,
        )

        embed.set_footer(text="Użyj !set_channel <typ> #kanal aby zmienić przypisanie (zapis do data/state.json).")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(ChannelsCog(bot))
