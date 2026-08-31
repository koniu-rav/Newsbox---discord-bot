"""News Cog - handles regional news commands (PL, USA, EU, Global) and streaming."""

import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.services.gemini_service import GeminiService
from newsbox.services.news_service import NewsService
from newsbox.utils.embeds import create_regional_news_embed
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsCog(commands.Cog, name="News Feed"):
    """Commands for browsing business, stock market, and macroeconomic news."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()

    @commands.command(name="news", aliases=["wiadomosci", "parkiet"])
    async def news_command(self, ctx: commands.Context, region: str = "ALL") -> None:
        """Pobierz najświeższe newsy biznesowe i giełdowe.

        Użycie:
        - `!news` lub `!news all` - przegląd ze wszystkich rynków
        - `!news pl` - Polska (Parkiet, Bankier, GPW)
        - `!news us` / `!news usa` - Rynki USA & Wall Street
        - `!news eu` - Strefa Euro & EBC
        - `!news global` - Rynki światowe, surowce i krypto
        """
        async with ctx.typing():
            reg_normalized = region.upper()
            if reg_normalized in ["US", "USA"]:
                reg_key = "USA"
            elif reg_normalized in ["PL", "POLSKA", "GPW", "PARKIET"]:
                reg_key = "PL"
            elif reg_normalized in ["EU", "EUROPA"]:
                reg_key = "EU"
            elif reg_normalized in ["GLOBAL", "SWIAT", "CRYPTO", "KRYPTO"]:
                reg_key = "GLOBAL"
            else:
                reg_key = "ALL"

            headlines = await self.news_service.fetch_regional_news(reg_key, limit=6)
            summary = await self.gemini_service.generate_news_summary(headlines)

            embed = create_regional_news_embed(
                region=reg_key,
                headlines=headlines,
                summary_text=summary,
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(NewsCog(bot))

