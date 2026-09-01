"""Portfolio Cog - tracks user portfolio holdings, quotes, and company-specific news."""

from typing import Optional
import discord
from discord.ext import commands

from newsbox.config import get_settings
from newsbox.services.gemini_service import GeminiService
from newsbox.services.market_service import MarketService
from newsbox.services.news_service import NewsService
from newsbox.utils.embeds import create_error_embed, create_portfolio_embed
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class PortfolioCog(commands.Cog, name="Portfolio Tracker"):
    """Manage and track news/quotes for companies in your investment portfolio."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.market_service = MarketService()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()
        # In-memory portfolio ticker list initialized from settings
        self.holdings = list(self.settings.portfolio_tickers)

    @commands.group(name="portfolio", aliases=["portfel", "spolki"], invoke_without_command=True)
    async def portfolio_group(self, ctx: commands.Context) -> None:
        """Pokaż aktualne notowania i podsumowanie spółek z Twojego portfela."""
        async with ctx.typing():
            if not self.holdings:
                await ctx.send(
                    "ℹ️ Twój portfel jest pusty. Dodaj spółki komendą: `!portfolio add <symbol>` (np. `!portfolio add CDR.WA` lub `!portfolio add NVDA`)."
                )
                return

            portfolio_data = await self.market_service.fetch_portfolio_snapshot(self.holdings)
            portfolio_news = await self.news_service.fetch_portfolio_news(self.holdings, limit=5)
            summary_text = await self.gemini_service.generate_portfolio_summary(
                portfolio_data=portfolio_data,
                portfolio_news=portfolio_news,
            )

            embed = create_portfolio_embed(
                portfolio_data=portfolio_data,
                advisory_text=summary_text,
                portfolio_news=portfolio_news,
            )
            await ctx.send(embed=embed)

    @portfolio_group.command(name="add", aliases=["dodaj"])
    async def add_symbol(self, ctx: commands.Context, symbol: str) -> None:
        """Dodaj walor lub spółkę do śledzenia w portfelu (np. !portfolio add CDR.WA)."""
        sym_clean = symbol.strip().upper()
        if sym_clean in [h.upper() for h in self.holdings]:
            await ctx.send(f"⚠️ Spółka **{sym_clean}** już znajduje się na liście portfela.")
            return

        self.holdings.append(sym_clean)
        logger.info("Added %s to portfolio watchlist by %s", sym_clean, ctx.author)
        await ctx.send(f"✅ Dodano **{sym_clean}** do Twojego portfela. Aktualna lista: `{', '.join(self.holdings)}`.")

    @portfolio_group.command(name="remove", aliases=["usun", "del"])
    async def remove_symbol(self, ctx: commands.Context, symbol: str) -> None:
        """Usuń spółkę z portfela (np. !portfolio remove TSLA)."""
        sym_clean = symbol.strip().upper()
        matched = [h for h in self.holdings if h.upper() == sym_clean]
        if not matched:
            await ctx.send(f"❌ Nie znaleziono **{sym_clean}** w Twoim portfelu.")
            return

        for m in matched:
            self.holdings.remove(m)
        logger.info("Removed %s from portfolio watchlist by %s", sym_clean, ctx.author)
        await ctx.send(f"🗑️ Usunięto **{sym_clean}** z portfela. Aktualna lista: `{', '.join(self.holdings) or 'Pusto'}`.")

    @portfolio_group.command(name="news", aliases=["wiadomosci"])
    async def portfolio_news_cmd(self, ctx: commands.Context) -> None:
        """Pobierz najświeższe komunikaty i newsy tylko dla spółek z Twojego portfela."""
        async with ctx.typing():
            if not self.holdings:
                await ctx.send("ℹ️ Twój portfel jest pusty. Dodaj spółki komendą: `!portfolio add <symbol>`.")
                return

            portfolio_news = await self.news_service.fetch_portfolio_news(self.holdings, limit=8)
            portfolio_data = await self.market_service.fetch_portfolio_snapshot(self.holdings)
            summary_text = await self.gemini_service.generate_portfolio_summary(
                portfolio_data=portfolio_data,
                portfolio_news=portfolio_news,
            )

            embed = create_portfolio_embed(
                portfolio_data=portfolio_data,
                advisory_text=summary_text,
                portfolio_news=portfolio_news,
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(PortfolioCog(bot))

