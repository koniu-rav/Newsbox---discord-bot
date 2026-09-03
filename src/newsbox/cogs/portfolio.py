"""Portfolio Cog - tracks user portfolio holdings, quotes, and company-specific news with persistent storage."""

from typing import Optional
import discord
from discord.ext import commands

from newsbox.config import get_settings
from newsbox.services.gemini_service import GeminiService
from newsbox.services.market_service import MarketService
from newsbox.services.news_service import NewsService
from newsbox.services.state_service import get_state_manager
from newsbox.utils.embeds import (
    create_error_embed,
    create_portfolio_embed,
    format_portfolio_message,
    send_full_message,
)
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class PortfolioCog(commands.Cog, name="Portfolio Tracker"):
    """Manage and track news/quotes for companies in your investment portfolio."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.state_manager = get_state_manager()
        self.market_service = MarketService()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()

    @commands.group(name="portfolio", aliases=["portfel", "spolki"], invoke_without_command=True)
    async def portfolio_group(self, ctx: commands.Context) -> None:
        """Pokaż aktualne notowania i podsumowanie spółek z Twojego portfela."""
        async with ctx.typing():
            holdings = self.state_manager.get_portfolio_tickers()
            if not holdings:
                await send_full_message(
                    ctx.channel,
                    "ℹ️ Twój portfel jest pusty. Dodaj spółki komendą: `!portfolio add <symbol>` (np. `!portfolio add CDR.WA` lub `!portfolio add NVDA`).",
                )
                return

            portfolio_data = await self.market_service.fetch_portfolio_snapshot(holdings)
            portfolio_news = await self.news_service.fetch_portfolio_news(holdings, limit=5)
            summary_text = await self.gemini_service.generate_portfolio_summary(
                portfolio_data=portfolio_data,
                portfolio_news=portfolio_news,
            )

            msg_text = format_portfolio_message(
                portfolio_data=portfolio_data,
                advisory_text=summary_text,
                portfolio_news=portfolio_news,
            )
            await send_full_message(ctx.channel, msg_text)

    @portfolio_group.command(name="add", aliases=["dodaj"])
    async def add_symbol(self, ctx: commands.Context, symbol: str) -> None:
        """Dodaj walor lub spółkę do śledzenia w portfelu i zapisz trwale (np. !portfolio add CDR.WA)."""
        sym_clean = symbol.strip().upper()
        added = self.state_manager.add_portfolio_ticker(sym_clean)
        if not added:
            await ctx.send(f"⚠️ Spółka **{sym_clean}** już znajduje się na liście portfela.")
            return

        all_holdings = self.state_manager.get_portfolio_tickers()
        logger.info("Added & persisted %s to portfolio watchlist by %s", sym_clean, ctx.author)
        await ctx.send(f"✅ Dodano i **zapisano trwale** **{sym_clean}** w Twoim portfelu. Aktualna lista: `{', '.join(all_holdings)}`.")

    @portfolio_group.command(name="remove", aliases=["usun", "del"])
    async def remove_symbol(self, ctx: commands.Context, symbol: str) -> None:
        """Usuń spółkę z portfela (np. !portfolio remove TSLA)."""
        sym_clean = symbol.strip().upper()
        removed = self.state_manager.remove_portfolio_ticker(sym_clean)
        if not removed:
            await ctx.send(f"❌ Nie znaleziono **{sym_clean}** w Twoim portfelu.")
            return

        all_holdings = self.state_manager.get_portfolio_tickers()
        logger.info("Removed & persisted %s from portfolio watchlist by %s", sym_clean, ctx.author)
        await ctx.send(f"🗑️ Usunięto **{sym_clean}** z portfela. Aktualna lista: `{', '.join(all_holdings) or 'Pusto'}`.")

    @portfolio_group.command(name="news", aliases=["wiadomosci"])
    async def portfolio_news_cmd(self, ctx: commands.Context) -> None:
        """Pobierz najświeższe komunikaty i newsy tylko dla spółek z Twojego portfela."""
        async with ctx.typing():
            holdings = self.state_manager.get_portfolio_tickers()
            if not holdings:
                await ctx.send("ℹ️ Twój portfel jest pusty. Dodaj spółki komendą: `!portfolio add <symbol>`.")
                return

            portfolio_news = await self.news_service.fetch_portfolio_news(holdings, limit=8)
            portfolio_data = await self.market_service.fetch_portfolio_snapshot(holdings)
            summary_text = await self.gemini_service.generate_portfolio_summary(
                portfolio_data=portfolio_data,
                portfolio_news=portfolio_news,
            )

            msg_text = format_portfolio_message(
                portfolio_data=portfolio_data,
                advisory_text=summary_text,
                portfolio_news=portfolio_news,
            )
            await send_full_message(ctx.channel, msg_text)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(PortfolioCog(bot))
