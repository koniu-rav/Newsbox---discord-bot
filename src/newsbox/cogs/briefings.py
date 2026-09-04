"""Briefings Cog - handles Sunday Weekly Outlook, 3 Daily Session Briefings (London, New York, Asia), Single-Asset Advisory, and Multi-Tier Accuracy Tracking."""

import asyncio
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands

from newsbox.config import get_settings
from newsbox.services.accuracy_service import AccuracyService, VALID_SESSIONS, SESSION_NAMES
from newsbox.services.calendar_service import CalendarService
from newsbox.services.gemini_service import GeminiService
from newsbox.services.market_service import MarketService
from newsbox.services.news_service import NewsService
from newsbox.services.state_service import get_state_manager
from newsbox.utils.embeds import (
    create_accuracy_embed,
    create_calendar_embed,
    create_error_embed,
    create_session_advisory_embed,
    create_single_asset_embed,
    create_weekly_outlook_embed,
    format_accuracy_message,
    format_calendar_message,
    format_error_message,
    format_macro_alert_message,
    format_macro_alerts_batch_message,
    format_session_advisory_message,
    format_single_asset_message,
    format_weekly_accuracy_message,
    format_weekly_outlook_message,
    send_full_message,
)
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)
WARSAW_TZ = ZoneInfo("Europe/Warsaw")


class BriefingsCog(commands.Cog, name="Briefings & Trader Advisory"):
    """Commands and automated dispatchers for Sunday Weekly Outlook, 3 Session Briefings, and Multi-Tier Accuracy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.state_manager = get_state_manager()
        self.market_service = MarketService()
        self.calendar_service = CalendarService()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()
        self.accuracy_service = AccuracyService()

    def _determine_current_session(self) -> str:
        """Determine the upcoming/active session based on Warsaw local time."""
        now_h = datetime.now(WARSAW_TZ).hour
        if 6 <= now_h < 13:
            return "london"
        elif 13 <= now_h < 21:
            return "newyork"
        else:
            return "asia"

    async def compile_and_send_weekly_outlook(self, channel: discord.abc.Messageable) -> None:
        """Fetch weekly calendar, market snapshot, and generate Sunday 10:00 AM Strategic Weekly Outlook."""
        try:
            date_str = datetime.now(WARSAW_TZ).strftime("%A, %d.%m.%Y")
            logger.info("Generating Strategic Weekly Outlook for %s...", date_str)

            market_data = await self.market_service.fetch_market_snapshot()
            weekly_calendar = await self.calendar_service.fetch_weekly_events()
            news_headlines = await self.news_service.fetch_regional_news("ALL", limit=8)

            outlook_text = await self.gemini_service.generate_weekly_outlook(
                calendar_events=weekly_calendar,
                market_data=market_data,
                news_headlines=news_headlines,
            )

            msg_text = format_weekly_outlook_message(
                date_str=date_str,
                market_data=market_data,
                outlook_text=outlook_text,
            )
            await send_full_message(channel, msg_text)
            logger.info("Successfully sent Weekly Strategic Outlook to %s", channel)
        except Exception as e:
            logger.error("Failed to generate weekly outlook: %s", e, exc_info=True)
            await send_full_message(
                channel,
                format_error_message(
                    "Błąd Planu Tygodniowego",
                    f"Nie udało się wygenerować planu tygodniowego: {e}",
                ),
            )

    async def compile_and_send_session_briefing(
        self,
        channel: discord.abc.Messageable,
        session_key: str = "london",
        is_scheduled: bool = False,
    ) -> None:
        """Fetch market data, calendar, news for a specific session (london, newyork, asia) and send full-width Discord message.
        Scheduled dispatches (1h before pre-market) save baseline prices for accuracy tracking.
        """
        try:
            s_clean = session_key.lower().strip()
            if s_clean not in VALID_SESSIONS:
                s_clean = "london"

            now_warsaw = datetime.now(WARSAW_TZ)
            date_str = now_warsaw.strftime("%A, %d.%m.%Y")
            iso_date = now_warsaw.strftime("%Y-%m-%d")

            # Determine calendar start hour for the session
            start_hour = 7 if s_clean == "london" else (13 if s_clean == "newyork" else 23)

            logger.info("Generating %s session briefing (is_scheduled=%s) for %s...", s_clean, is_scheduled, date_str)

            market_data = await self.market_service.fetch_market_snapshot()
            calendar_events = await self.calendar_service.fetch_todays_events(start_hour=start_hour)
            # Filter strictly High (🔴) and Medium (🟡) macro events; omit Low (⚪) / minor
            important_events = [
                e for e in calendar_events
                if e.get("impact") in ["🔴", "🟡"] or e.get("weight") in [1, 2]
            ]

            news_region = "EU" if s_clean == "london" else ("USA" if s_clean == "newyork" else "GLOBAL")
            news_headlines = await self.news_service.fetch_regional_news(news_region, limit=8)

            advisory_text = await self.gemini_service.generate_session_advisory(
                session_key=s_clean,
                market_data=market_data,
                economic_events=important_events,
                news_headlines=news_headlines,
            )

            # Record baseline for scheduled dispatches
            if is_scheduled:
                self.accuracy_service.save_session_briefing(
                    session=s_clean,
                    advisory_text=advisory_text,
                    market_snapshot=market_data,
                    briefing_date=iso_date,
                )

            msg_text = format_session_advisory_message(
                session_key=s_clean,
                date_str=date_str,
                market_data=market_data,
                advisory_text=advisory_text,
            )
            await send_full_message(channel, msg_text)
            logger.info("Successfully sent %s session briefing to %s", s_clean, channel)
        except Exception as e:
            logger.error("Failed to generate %s session briefing: %s", session_key, e, exc_info=True)
            await send_full_message(
                channel,
                format_error_message(
                    f"Błąd Briefingu Sesji ({session_key.upper()})",
                    f"Wystąpił błąd podczas generowania analizy sesyjnej: {e}",
                ),
            )

    # Legacy helper aliased to London session
    async def compile_and_send_macro_briefing(
        self,
        channel: discord.abc.Messageable,
        is_scheduled: bool = False,
    ) -> None:
        """Legacy helper aliasing to London session briefing."""
        await self.compile_and_send_session_briefing(channel, session_key="london", is_scheduled=is_scheduled)

    async def compile_and_send_session_accuracy(
        self,
        channel: discord.abc.Messageable,
        session_key: str = "london",
    ) -> None:
        """Evaluate a specific concluded session's recommendations and send report."""
        try:
            s_clean = session_key.lower().strip()
            logger.info("Processing accuracy evaluation for session: %s...", s_clean)

            pending = self.accuracy_service.get_pending_session_to_evaluate(session=s_clean)
            current_market = await self.market_service.fetch_market_snapshot()

            if pending:
                eval_date = pending.get("date", "Wczoraj")
                start_snapshot = pending.get("market_snapshot", {})
                advisory = pending.get("advisory_text", "")

                eval_dict = await self.gemini_service.evaluate_session_performance(
                    session_key=s_clean,
                    session_advisory=advisory,
                    start_prices=start_snapshot,
                    end_prices=current_market,
                )

                record = self.accuracy_service.record_session_evaluation(
                    session=s_clean,
                    date_str=eval_date,
                    score=eval_dict.get("score", 75),
                    breakdown=eval_dict.get("breakdown", ""),
                    conclusions=eval_dict.get("conclusions", ""),
                )

                multi_tier_stats = self.accuracy_service.get_multi_tier_stats()
                msg_text = format_accuracy_message(record, multi_tier_stats)
                await send_full_message(channel, msg_text)
                logger.info("Evaluated and sent new accuracy report for %s (%s)", eval_date, s_clean)
                return

            # If no pending session, check last evaluation
            last_eval = self.accuracy_service.get_last_evaluation(session=s_clean) or self.accuracy_service.get_last_evaluation()
            if last_eval:
                multi_tier_stats = self.accuracy_service.get_multi_tier_stats()
                msg_text = format_accuracy_message(last_eval, multi_tier_stats)
                await send_full_message(channel, msg_text)
            else:
                empty_record = {
                    "score": 0,
                    "status": "neutralna",
                    "date": "Brak danych",
                    "session": s_clean,
                    "breakdown": "Brak zarejestrowanych wcześniejszych sesji do ewaluacji.",
                    "conclusions": "Statystyki zostaną zaktualizowane po zakończeniu najbliższej sesji.",
                }
                msg_text = format_accuracy_message(empty_record, self.accuracy_service.get_multi_tier_stats())
                await send_full_message(channel, msg_text)
        except Exception as e:
            logger.error("Failed to compile session accuracy report: %s", e, exc_info=True)
            await send_full_message(
                channel,
                format_error_message("Błąd Raportu Skuteczności", f"Nie udało się wygenerować raportu dla sesji {session_key}: {e}"),
            )

    async def evaluate_session_quietly(self, session_key: str = "london") -> None:
        """Evaluate a concluded session and record into history quietly without sending any Discord message."""
        try:
            s_clean = session_key.lower().strip()
            pending = self.accuracy_service.get_pending_session_to_evaluate(session=s_clean)
            if not pending:
                return

            current_market = await self.market_service.fetch_market_snapshot()
            eval_date = pending.get("date", "Wczoraj")
            start_snapshot = pending.get("market_snapshot", {})
            advisory = pending.get("advisory_text", "")

            eval_dict = await self.gemini_service.evaluate_session_performance(
                session_key=s_clean,
                session_advisory=advisory,
                start_prices=start_snapshot,
                end_prices=current_market,
            )

            self.accuracy_service.record_session_evaluation(
                session=s_clean,
                date_str=eval_date,
                score=eval_dict.get("score", 75),
                breakdown=eval_dict.get("breakdown", ""),
                conclusions=eval_dict.get("conclusions", ""),
            )
            logger.info("Quietly evaluated and recorded %s session for %s (score=%d)", s_clean, eval_date, eval_dict.get("score", 75))
        except Exception as e:
            logger.warning("Quiet session evaluation failed for %s: %s", session_key, e)

    async def compile_and_send_weekly_accuracy(self, channel: discord.abc.Messageable) -> None:
        """Compile and dispatch Saturday 12:00 PM comprehensive weekly accuracy report."""
        try:
            # 1. Evaluate any leftover pending sessions
            for s_key in ["london", "newyork", "asia"]:
                await self.evaluate_session_quietly(s_key)

            multi_tier_stats = self.accuracy_service.get_multi_tier_stats()
            evals = self.accuracy_service._data.get("evaluations", [])

            # Current or latest week evals
            current_week = multi_tier_stats.get("weekly", {}).get("week_number")
            week_evals = [e for e in evals if e.get("week_number") == current_week]
            if not week_evals and evals:
                week_evals = evals[-7:]

            msg_text = format_weekly_accuracy_message(
                stats=multi_tier_stats,
                week_evaluations=week_evals,
            )
            await send_full_message(channel, msg_text)
            logger.info("Successfully dispatched Weekly Accuracy Report to %s", channel)
        except Exception as e:
            logger.error("Failed to compile weekly accuracy report: %s", e, exc_info=True)
            await send_full_message(
                channel,
                format_error_message("Błąd Raportu Skuteczności", f"Nie udało się wygenerować raportu tygodniowego: {e}"),
            )

    async def compile_and_send_accuracy_report(self, channel: discord.abc.Messageable) -> None:
        """Legacy / general accuracy command: evaluates the latest pending session or displays multi-tier report."""
        try:
            pending = self.accuracy_service.get_pending_session_to_evaluate()
            if pending:
                s_key = pending.get("session", "london")
                await self.compile_and_send_session_accuracy(channel, session_key=s_key)
            else:
                last_eval = self.accuracy_service.get_last_evaluation()
                if last_eval:
                    multi_tier_stats = self.accuracy_service.get_multi_tier_stats()
                    msg_text = format_accuracy_message(last_eval, multi_tier_stats)
                    await send_full_message(channel, msg_text)
                else:
                    await self.compile_and_send_session_accuracy(channel, session_key="london")
        except Exception as e:
            logger.error("Failed to compile accuracy report: %s", e, exc_info=True)
            await send_full_message(
                channel,
                format_error_message("Błąd Raportu Skuteczności", f"Wystąpił błąd podczas generowania statystyk: {e}"),
            )

    async def compile_and_send_single_asset(
        self,
        channel: discord.abc.Messageable,
        symbol: str,
    ) -> None:
        """Fetch quotes and dedicated AI analysis for 1 specific financial asset."""
        try:
            resolved_ticker = self.market_service.resolve_ticker(symbol)
            asset_data = await self.market_service.fetch_single_asset(resolved_ticker)
            matching_news = await self.news_service.fetch_asset_news(symbol, limit=4)

            advisory_text = await self.gemini_service.generate_single_asset_advisory(
                symbol=symbol,
                asset_data=asset_data,
                news_headlines=matching_news,
            )

            msg_text = format_single_asset_message(
                symbol=symbol,
                asset_data=asset_data,
                advisory_text=advisory_text,
            )
            await send_full_message(channel, msg_text)
        except Exception as e:
            logger.error("Failed to generate single asset brief for %s: %s", symbol, e)
            await send_full_message(
                channel,
                format_error_message("Błąd Analizy Waloru", f"Nie udało się pobrać danych dla {symbol}: {e}"),
            )

    async def compile_and_send_calendar_briefing(self, channel: discord.abc.Messageable) -> None:
        """Fetch economic calendar, generate AI risk assessment, and send full-width Discord message."""
        try:
            now = datetime.now(WARSAW_TZ)
            polish_days = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
            day_pl = polish_days[now.weekday()]
            date_str = f"{day_pl} {now.strftime('%d.%m.%Y')}"
            calendar_events = await self.calendar_service.fetch_todays_events(start_hour=7)
            calendar_advice = await self.gemini_service.generate_calendar_advisory(calendar_events)

            msg_text = format_calendar_message(
                date_str=date_str,
                calendar_events=calendar_events,
                calendar_advice=calendar_advice,
            )
            await send_full_message(channel, msg_text)
        except Exception as e:
            logger.error("Failed to send calendar briefing: %s", e, exc_info=True)

    async def check_and_dispatch_macro_alerts(self, channel: discord.abc.Messageable) -> int:
        """Poll for newly published high/medium macro releases, dispatch combined batch alert, and mark as seen.
        Returns count of dispatched alerts.
        """
        now = datetime.now(WARSAW_TZ)
        published_events = await self.calendar_service.fetch_live_published_macro_events()
        if not published_events:
            return 0

        pending_events: List[Dict[str, Any]] = []
        for ev in published_events:
            ev_id = ev.get("event_id")
            if not ev_id:
                continue

            if self.state_manager.is_macro_event_published(ev_id):
                continue

            # Protection against spamming historical events on startup/redeploy:
            # If the event scheduled time was more than 35 minutes ago, mark as published without sending alert.
            ev_dt = ev.get("dt")
            if ev_dt and (now - ev_dt).total_seconds() > 35 * 60:
                logger.debug("Skipping historical macro alert (%s, %s): older than 35 mins", ev_id, ev.get("title"))
                self.state_manager.mark_macro_event_published(ev_id)
                continue

            pending_events.append(ev)

        if not pending_events:
            return 0

        # Generate concise market impacts in one batch call (with instant fallback)
        impacts = await self.gemini_service.generate_macro_batch_impact(pending_events)

        # Chunk pending events into batches of max 8 to safely fit Discord limit
        chunk_size = 8
        for i in range(0, len(pending_events), chunk_size):
            chunk = pending_events[i : i + chunk_size]
            msg_text = format_macro_alerts_batch_message(chunk, impacts=impacts)
            await send_full_message(channel, msg_text)
            for ev in chunk:
                ev_id = ev.get("event_id")
                if ev_id:
                    self.state_manager.mark_macro_event_published(ev_id)
            if i + chunk_size < len(pending_events):
                await asyncio.sleep(1.0)

        dispatched_count = len(pending_events)
        logger.info("Dispatched %d real-time macro alerts in batch to %s", dispatched_count, channel)
        return dispatched_count

    @commands.command(name="macro_alerts", aliases=["alerts", "odczyty", "dane"])
    async def macro_alerts_command(self, ctx: commands.Context, limit: Optional[str] = "5") -> None:
        """Sprawdź ostatnio opublikowane odczyty makroekonomiczne z dzisiaj lub wymuś sprawdzenie.

        Użycie:
        - `!odczyty` - wyświetla 5 ostatnich odczytów
        - `!odczyty 10` - wyświetla 10 ostatnich odczytów
        """
        try:
            n = int(limit) if limit and limit.isdigit() else 5
            n = max(1, min(n, 15))
        except Exception:
            n = 5

        async with ctx.typing():
            dispatched = await self.check_and_dispatch_macro_alerts(ctx.channel)
            if dispatched == 0:
                events = await self.calendar_service.fetch_live_published_macro_events()
                if events:
                    recent = events[-n:]
                    impacts = await self.gemini_service.generate_macro_batch_impact(recent)
                    msg_text = format_macro_alerts_batch_message(recent, impacts=impacts)
                    await send_full_message(ctx.channel, f"ℹ️ *Brak nowych odczytów w tej minucie. Ostatnie {len(recent)} odczytów z dzisiaj:*\n\n{msg_text}")
                else:
                    await ctx.send("ℹ️ Brak opublikowanych odczytów o wadze 🔴 lub 🟡 w dniu dzisiejszym.")


    @commands.command(name="briefing", aliases=["macro", "morning", "poranek"])
    async def briefing_command(self, ctx: commands.Context, target: Optional[str] = None) -> None:
        """Wygeneruj plan tygodniowy, briefing sesyjny lub analizę 1 waloru.

        Użycie:
        - `!briefing` - generuje briefing dla aktualnie nadchodzącej sesji
        - `!briefing weekly` / `!weekly` - niedzielny plan na cały nadchodzący tydzień
        - `!briefing london` / `!london` - briefing sesji europejskiej (DAX, FX)
        - `!briefing ny` / `!ny` - briefing sesji amerykańskiej (Wall St, DXY, US Data)
        - `!briefing asia` / `!asia` - briefing sesji azjatyckiej (Tokio, AUD, BoJ)
        - `!briefing DAX` / `!briefing BTC` - dedykowana analiza dla 1 waloru
        """
        async with ctx.typing():
            if not target:
                session = self._determine_current_session()
                await self.compile_and_send_session_briefing(ctx.channel, session_key=session)
                return

            t_lower = target.lower().strip()
            if t_lower in ["weekly", "tydzien", "week", "plan"]:
                await self.compile_and_send_weekly_outlook(ctx.channel)
            elif t_lower in ["london", "londyn", "eu", "europa"]:
                await self.compile_and_send_session_briefing(ctx.channel, session_key="london")
            elif t_lower in ["ny", "usa", "us", "nowyjork", "wallstreet"]:
                await self.compile_and_send_session_briefing(ctx.channel, session_key="newyork")
            elif t_lower in ["asia", "azja", "tokyo", "tokio"]:
                await self.compile_and_send_session_briefing(ctx.channel, session_key="asia")
            else:
                # Target is an asset ticker
                await self.compile_and_send_single_asset(ctx.channel, target)

    @commands.command(name="weekly", aliases=["tydzien"])
    async def weekly_command(self, ctx: commands.Context) -> None:
        """Szybki skrót: Wygeneruj strategiczny plan na nadchodzący tydzień."""
        async with ctx.typing():
            await self.compile_and_send_weekly_outlook(ctx.channel)

    @commands.command(name="london", aliases=["londyn"])
    async def london_command(self, ctx: commands.Context) -> None:
        """Szybki skrót: Briefing Sesji Londyńskiej (Europa)."""
        async with ctx.typing():
            await self.compile_and_send_session_briefing(ctx.channel, session_key="london")

    @commands.command(name="ny", aliases=["nowyjork"])
    async def ny_command(self, ctx: commands.Context) -> None:
        """Szybki skrót: Briefing Sesji Nowojorskiej (Wall Street)."""
        async with ctx.typing():
            await self.compile_and_send_session_briefing(ctx.channel, session_key="newyork")

    @commands.command(name="asia", aliases=["azja"])
    async def asia_command(self, ctx: commands.Context) -> None:
        """Szybki skrót: Briefing Sesji Azjatyckiej (Tokio / Sydney)."""
        async with ctx.typing():
            await self.compile_and_send_session_briefing(ctx.channel, session_key="asia")

    @commands.command(name="calendar", aliases=["kalendarz", "wydarzenia"])
    async def calendar_command(self, ctx: commands.Context) -> None:
        """Wyświetl kalendarz makroekonomiczny na najbliższe 24h z oceną ryzyk AI."""
        async with ctx.typing():
            await self.compile_and_send_calendar_briefing(ctx.channel)

    @commands.command(name="accuracy", aliases=["skutecznosc", "wyniki", "stats"])
    async def accuracy_command(self, ctx: commands.Context, session: Optional[str] = None) -> None:
        """Wyświetl raport skuteczności AI (Domyślnie Tygodniowy lub w rozbiciu na sesję: london, ny, asia)."""
        async with ctx.typing():
            if session and session.lower().strip() in VALID_SESSIONS:
                await self.compile_and_send_session_accuracy(ctx.channel, session_key=session.lower().strip())
            else:
                await self.compile_and_send_weekly_accuracy(ctx.channel)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(BriefingsCog(bot))
