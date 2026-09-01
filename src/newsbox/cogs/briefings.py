"""Briefings Cog - 8:00 AM macro briefing, 12:30 PM accuracy evaluation, and on-demand advisory."""

from datetime import datetime, date
from typing import Optional
import discord
from discord.ext import commands

from newsbox.config import get_settings
from newsbox.services.accuracy_service import AccuracyService
from newsbox.services.calendar_service import CalendarService
from newsbox.services.gemini_service import GeminiService
from newsbox.services.market_service import MarketService
from newsbox.services.news_service import NewsService
from newsbox.utils.embeds import (
    create_accuracy_embed,
    create_calendar_embed,
    create_error_embed,
    create_single_asset_embed,
    create_trader_advisory_embed,
)
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class BriefingsCog(commands.Cog, name="Briefings & Trader Advisory"):
    """Commands and automated dispatch for morning macro reports, accuracy tracking, and asset briefs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.market_service = MarketService()
        self.calendar_service = CalendarService()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()
        self.accuracy_service = AccuracyService()

    async def compile_and_send_macro_briefing(
        self,
        channel: discord.abc.Messageable,
        is_scheduled: bool = False,
    ) -> None:
        """Fetch market data, calendar, news, generate AI advisory (FX Majors, DXY, DAX), and send Discord Embed.
        Only the official 08:00 AM scheduled dispatch records baseline prices for future accuracy evaluation.
        """
        try:
            date_str = datetime.utcnow().strftime("%A, %d.%m.%Y")
            iso_date = date.today().strftime("%Y-%m-%d")
            logger.info("Generating morning macro briefing (is_scheduled=%s) for %s...", is_scheduled, date_str)

            market_data = await self.market_service.fetch_market_snapshot()
            calendar_events = await self.calendar_service.fetch_todays_events()
            news_headlines = await self.news_service.fetch_regional_news("ALL", limit=8)

            advisory_text = await self.gemini_service.generate_trader_advisory(
                market_data=market_data,
                economic_events=calendar_events,
                news_headlines=news_headlines,
            )

            # ONLY save to accuracy history if this is the official scheduled 08:00 AM briefing
            if is_scheduled:
                self.accuracy_service.save_official_morning_briefing(
                    advisory_text=advisory_text,
                    market_snapshot=market_data,
                    briefing_date=iso_date,
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

    async def compile_and_send_accuracy_report(self, channel: discord.abc.Messageable) -> None:
        """Evaluate yesterday's official 08:00 AM briefing against current market prices and send report.
        Idempotent: If yesterday was already evaluated, displays the existing record without duplicating stats.
        """
        try:
            logger.info("Processing accuracy and performance evaluation (yesterday's briefing focus)...")
            yesterday_pending = self.accuracy_service.get_yesterday_briefing_to_evaluate()
            current_market = await self.market_service.fetch_market_snapshot()

            if yesterday_pending:
                # We have yesterday's unevaluated brief -> Run Gemini evaluation
                eval_date = yesterday_pending.get("date", "Wczoraj")
                start_snapshot = yesterday_pending.get("market_snapshot", {})
                advisory = yesterday_pending.get("advisory_text", "")

                eval_dict = await self.gemini_service.evaluate_briefing_performance(
                    yesterday_advisory=advisory,
                    start_prices=start_snapshot,
                    current_prices=current_market,
                )

                record = self.accuracy_service.record_evaluation(
                    date_str=eval_date,
                    score=eval_dict.get("score", 75),
                    breakdown=eval_dict.get("breakdown", ""),
                    conclusions=eval_dict.get("conclusions", ""),
                )

                global_stats = self.accuracy_service.get_global_stats()
                embed = create_accuracy_embed(record, global_stats)
                await channel.send(embed=embed)
                logger.info("Evaluated and sent new accuracy report for %s", eval_date)
                return

            # If no pending yesterday briefing, check if yesterday was already evaluated
            last_eval = self.accuracy_service.get_last_evaluation()
            if last_eval:
                global_stats = self.accuracy_service.get_global_stats()
                embed = create_accuracy_embed(last_eval, global_stats)
                await channel.send(embed=embed)
                logger.info("Sent existing accuracy report for %s (idempotent view)", last_eval.get("date"))
                return

            # Day 1 initial state: no previous days available yet
            today_str = date.today().strftime("%Y-%m-%d")
            embed = discord.Embed(
                title="📊 Raport Skuteczności Briefingu (Inicjalizacja)",
                description=(
                    "ℹ️ **Trwa zbieranie danych dla pierwszego cyklu ewaluacji.**\n\n"
                    f"• Dzisiejszy oficjalny brief z 08:00 (`{today_str}`) zostanie zweryfikowany **jutro o 12:30** po pełnej sesji giełdowej.\n"
                    "• Zasady oceny: `0-25%` Nieudana | `25-75%` Neutralna | `75-100%` Udana."
                ),
                color=0x3498DB,
                timestamp=datetime.utcnow(),
            )
            embed.set_footer(text="Newsbox Accuracy Tracker • Gemini AI")
            await channel.send(embed=embed)

        except Exception as e:
            logger.error("Failed to compile accuracy report: %s", e, exc_info=True)
            await channel.send(
                embed=create_error_embed(
                    "Błąd Ewaluacji Skuteczności",
                    f"Nie udało się wygenerować raportu skuteczności: {e}",
                )
            )

    async def compile_and_send_single_asset(self, channel: discord.abc.Messageable, symbol: str) -> None:
        """Fetch single asset quote and generate focused AI advice."""
        try:
            asset_data = await self.market_service.fetch_single_asset(symbol)
            news_headlines = await self.news_service.fetch_regional_news("ALL", limit=10)
            matching_news = [h for h in news_headlines if symbol.upper() in h.get("title", "").upper()] or news_headlines[:4]

            advisory_text = await self.gemini_service.generate_single_asset_advisory(
                symbol=symbol,
                asset_data=asset_data,
                news_headlines=matching_news,
            )

            embed = create_single_asset_embed(
                symbol=symbol,
                asset_data=asset_data,
                advisory_text=advisory_text,
            )
            await channel.send(embed=embed)
        except Exception as e:
            logger.error("Failed to generate single asset brief for %s: %s", symbol, e)
            await channel.send(
                embed=create_error_embed("Błąd Analizy Waloru", f"Nie udało się pobrać danych dla {symbol}: {e}")
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
    async def briefing_command(self, ctx: commands.Context, target_asset: Optional[str] = None) -> None:
        """Wygeneruj poranny raport makro lub analizę dla 1 wybranego waloru (np. !briefing DAX)."""
        async with ctx.typing():
            if target_asset:
                await self.compile_and_send_single_asset(ctx.channel, target_asset)
            else:
                # Manual invocation: is_scheduled=False
                await self.compile_and_send_macro_briefing(ctx.channel, is_scheduled=False)

    @commands.command(name="accuracy", aliases=["skutecznosc", "stats", "wyniki", "counter"])
    async def accuracy_command(self, ctx: commands.Context) -> None:
        """Sprawdź skuteczność wczorajszego briefu (globalny counter, wynik wczorajszego briefu, wnioski)."""
        async with ctx.typing():
            await self.compile_and_send_accuracy_report(ctx.channel)

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
