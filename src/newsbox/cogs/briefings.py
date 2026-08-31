"""Briefings Cog - 8:00 AM macro briefing, market watch, and AI Trader Advisory."""

from datetime import datetime
import discord
from discord.ext import commands

from newsbox.config import get_settings
from newsbox.services.calendar_service import CalendarService
from newsbox.services.gemini_service import GeminiService
from newsbox.services.market_service import MarketService
from newsbox.services.news_service import NewsService
from newsbox.utils.embeds import (
    create_calendar_embed,
    create_error_embed,
    create_trader_advisory_embed,
)
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class BriefingsCog(commands.Cog, name="Briefings & Trader Advisory"):
    """Commands and automated dispatch for morning macro reports and trading guidance."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.market_service = MarketService()
        self.calendar_service = CalendarService()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()

    async def compile_and_send_macro_briefing(self, channel: discord.abc.Messageable) -> None:
        """Fetch market data, calendar, news, generate AI advisory, and send Discord Embed."""
        try:
            date_str = datetime.utcnow().strftime("%A, %d.%m.%Y")
            logger.info("Generating morning macro briefing and trader advisory for %s...", date_str)

            market_data = await self.market_service.fetch_market_snapshot()
            calendar_events = await self.calendar_service.fetch_todays_events()
            news_headlines = await self.news_service.fetch_regional_news("ALL", limit=8)

            # Generate Trader Advisory (What to trade, what not to trade, market regime)
            advisory_text = await self.gemini_service.generate_trader_advisory(
                market_data=market_data,
                economic_events=calendar_events,
                news_headlines=news_headlines,
            )

            embed = create_trader_advisory_embed(
                date_str=date_str,
                market_data=market_data,
                advisory_text=advisory_text,
            )
            await channel.send(embed=embed)
            logger.info("Successfully sent macro briefing to channel %s", channel)

        except Exception as e:
            logger.error("Failed to generate macro briefing: %s", e, exc_info=True)
            await channel.send(
                embed=create_error_embed(
                    "Błąd Generowania Briefingu",
                    f"Wystąpił błąd podczas generowania porannego raportu: {e}",
                )
            )

    async def compile_and_send_calendar_briefing(self, channel: discord.abc.Messageable) -> None:
        """Fetch economic calendar, generate AI risk assessment, and send Discord Embed."""
        try:
            date_str = datetime.utcnow().strftime("%A, %d.%m.%Y")
            calendar_events = await self.calendar_service.fetch_todays_events()
            calendar_advice = await self.gemini_service.generate_calendar_advisory(calendar_events)

            embed = create_calendar_embed(
                date_str=date_str,
                calendar_events=calendar_events,
                calendar_advice=calendar_advice,
            )
            await channel.send(embed=embed)
        except Exception as e:
            logger.error("Failed to send calendar briefing: %s", e, exc_info=True)

    @commands.command(name="briefing", aliases=["macro", "morning", "poranek"])
    async def briefing_command(self, ctx: commands.Context) -> None:
        """Wygeneruj pełny poranny raport makro i rekomendacje AI (co handlować / czego unikać)."""
        async with ctx.typing():
            await self.compile_and_send_macro_briefing(ctx.channel)

    @commands.command(name="calendar", aliases=["kalendarz", "wydarzenia"])
    async def calendar_command(self, ctx: commands.Context) -> None:
        """Wyświetl dzisiejszy kalendarz ekonomiczny wraz z zaleceniami AI."""
        async with ctx.typing():
            await self.compile_and_send_calendar_briefing(ctx.channel)

    @commands.command(name="market", aliases=["rynek", "notowania"])
    async def market_command(self, ctx: commands.Context) -> None:
        """Pobierz szybki podgląd aktualnych notowań śledzonych aktywów (DXY, EUR/USD, DAX, BTC...)."""
        async with ctx.typing():
            market_data = await self.market_service.fetch_market_snapshot()
            date_str = datetime.utcnow().strftime("%H:%M UTC - %d.%m.%Y")
            embed = create_trader_advisory_embed(
                date_str=date_str,
                market_data=market_data,
                advisory_text="*Aktualne notowania instrumentów bazowych na żywo.*",
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(BriefingsCog(bot))
