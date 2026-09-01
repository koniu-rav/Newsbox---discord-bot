"""News Cog - handles regional news commands (PL, USA, EU, Crypto, Global) and streaming."""

import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.services.gemini_service import GeminiService
from newsbox.services.news_service import NewsService
from newsbox.utils.embeds import create_crypto_news_embed, create_regional_news_embed
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsCog(commands.Cog, name="News Feed"):
    """Commands for browsing business, stock market, crypto, and macroeconomic news."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()

    @commands.command(name="news", aliases=["wiadomosci", "parkiet"])
    async def news_command(self, ctx: commands.Context, region: str = "ALL") -> None:
        """Pobierz najświeższe newsy biznesowe, giełdowe lub krypto.

        Użycie:
        - `!news` lub `!news all` - przegląd ze wszystkich rynków
        - `!news pl` - Polska (Parkiet, Bankier, GPW)
        - `!news us` / `!news usa` - Rynki USA & Wall Street
        - `!news eu` - Strefa Euro & EBC
        - `!news crypto` - Świat kryptowalut & blockchain (CoinDesk, Cointelegraph)
        - `!news global` - Rynki światowe, surowce i makro
        """
        async with ctx.typing():
            # Check quiet window (e.g. 08:50-09:15 or 15:20-15:45)
            in_quiet = self.news_service.is_in_quiet_window()
            quiet_notice = (
                "\n*⏳ Uwaga: Trwa okno otwarcia sesji giełdowej (Market Open). Zmienność może być podwyższona.*"
                if in_quiet
                else ""
            )

            reg_normalized = region.upper()
            if reg_normalized in ["CRYPTO", "KRYPTO", "BTC"]:
                headlines = await self.news_service.fetch_crypto_news(limit=6)
                summary = await self.gemini_service.generate_crypto_summary(headlines)
                embed = create_crypto_news_embed(
                    headlines=headlines,
                    summary_text=summary + quiet_notice if summary else quiet_notice,
                )
                await ctx.send(embed=embed)
                return

            if reg_normalized in ["US", "USA"]:
                reg_key = "USA"
            elif reg_normalized in ["PL", "POLSKA", "GPW", "PARKIET"]:
                reg_key = "PL"
            elif reg_normalized in ["EU", "EUROPA"]:
                reg_key = "EU"
            elif reg_normalized in ["GLOBAL", "SWIAT"]:
                reg_key = "GLOBAL"
            else:
                reg_key = "ALL"

            headlines = await self.news_service.fetch_regional_news(reg_key, limit=6)
            summary = await self.gemini_service.generate_news_summary(headlines)

            embed = create_regional_news_embed(
                region=reg_key,
                headlines=headlines,
                summary_text=summary + quiet_notice if summary else quiet_notice,
            )
            await ctx.send(embed=embed)

    @commands.command(name="crypto", aliases=["krypto"])
    async def crypto_news_shortcut(self, ctx: commands.Context) -> None:
        """Szybki skrót do najważniejszych newsów ze świata krypto."""
        await self.news_command(ctx, region="crypto")


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(NewsCog(bot))
