"""Schedules Cog - manages dynamic and persistent cron scheduling for all bot publications."""

import re
from typing import Any, Dict, Optional, Tuple
import discord
from discord.ext import commands

from newsbox.config import get_settings
from newsbox.services.state_service import get_state_manager
from newsbox.utils.logger import setup_logger
from newsbox.utils.embeds import send_full_message

logger = setup_logger(__name__)

DAY_MAP = {
    # Polish
    "pon": "mon",
    "poniedzialek": "mon",
    "poniedziałek": "mon",
    "wt": "tue",
    "wtorek": "tue",
    "sr": "wed",
    "sroda": "wed",
    "środa": "wed",
    "czw": "thu",
    "czwartek": "thu",
    "pt": "fri",
    "piatek": "fri",
    "piątek": "fri",
    "sob": "sat",
    "sobota": "sat",
    "nd": "sun",
    "ndz": "sun",
    "niedziela": "sun",
    "pon-pt": "mon-fri",
    "robocze": "mon-fri",
    "ndz-czw": "sun,mon-thu",
    "codziennie": "*",
    # English
    "mon": "mon",
    "monday": "mon",
    "tue": "tue",
    "tuesday": "tue",
    "wed": "wed",
    "wednesday": "wed",
    "thu": "thu",
    "thursday": "thu",
    "fri": "fri",
    "friday": "fri",
    "sat": "sat",
    "saturday": "sat",
    "sun": "sun",
    "sunday": "sun",
    "mon-fri": "mon-fri",
    "sun-thu": "sun,mon-thu",
    "daily": "*",
    "*": "*",
}

JOB_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "weekly_outlook": {
        "title": "🌅 Raport Tygodniowy (Weekly Outlook)",
        "job_id": "weekly_strategic_outlook",
        "aliases": ["weekly", "outlook", "tydzien", "tydzień"],
        "default_day": "sun",
    },
    "calendar": {
        "title": "📅 Kalendarz Ekonomiczny 24h",
        "job_id": "daily_economic_calendar",
        "aliases": ["kalendarz", "cal"],
        "default_day": "mon-fri",
    },
    "london": {
        "title": "🇬🇧 Sesja Londyńska (Europa)",
        "job_id": "session_briefing_london",
        "aliases": ["londyn", "europa"],
        "default_day": "mon-fri",
    },
    "newyork": {
        "title": "🇺🇸 Sesja Nowojorska (Wall Street)",
        "job_id": "session_briefing_newyork",
        "aliases": ["ny", "nowyjork", "wallstreet"],
        "default_day": "mon-fri",
    },
    "asia": {
        "title": "🇯🇵 Sesja Azjatycka (Tokio/Sydney)",
        "job_id": "session_briefing_asia",
        "aliases": ["azja", "tokio", "tokyo"],
        "default_day": "sun,mon-thu",
    },
    "accuracy": {
        "title": "🎯 Tygodniowy Raport Skuteczności (Accuracy)",
        "job_id": "weekly_accuracy_report",
        "aliases": ["skutecznosc", "skuteczność", "stats", "wyniki"],
        "default_day": "sat",
    },
    "portfolio": {
        "title": "💼 Tygodniowy Raport Portfela",
        "job_id": "weekly_portfolio_report",
        "aliases": ["portfel", "spolki", "spółki"],
        "default_day": "sun",
    },
    "portfolio_news": {
        "title": "📰 Codzienne Wiadomości Spółek Portfela",
        "job_id": "daily_portfolio_news",
        "aliases": ["portfel_news", "wiadomosci_spolki"],
        "default_day": "*",
    },
    "flash_news": {
        "title": "⚡ Global Flash News",
        "job_id": "periodic_flash_news",
        "aliases": ["flash", "flashnews", "news_global"],
        "is_cron": True,
    },
}

POLISH_DAY_NAMES = {
    "mon": "Poniedziałek",
    "tue": "Wtorek",
    "wed": "Środa",
    "thu": "Czwartek",
    "fri": "Piątek",
    "sat": "Sobota",
    "sun": "Niedziela",
    "mon-fri": "Pon-Pt (dni robocze)",
    "sun,mon-thu": "Ndz-Czw (przed rynkiem azjatyckim)",
    "sun-thu": "Ndz-Czw (przed rynkiem azjatyckim)",
    "*": "Codziennie",
}


class SchedulesCog(commands.Cog, name="Schedule Management"):
    """Manage dynamic and persistent schedules for bot publications."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.state_manager = get_state_manager()

    def _resolve_canonical_key(self, raw_type: str) -> Optional[str]:
        """Match user input against known job keys and aliases."""
        clean = raw_type.lower().strip()
        for key, meta in JOB_DEFINITIONS.items():
            if clean == key or clean in meta.get("aliases", []):
                return key
        return None

    def _parse_time_and_day(
        self,
        key: str,
        args: Tuple[str, ...],
        current_config: Dict[str, Any],
    ) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
        """Parse time, day of week, or minute cron expression from arguments."""
        if not args:
            return None, None, None, "Brak argumentów czasu."

        # Case 1: Flash News minute cron
        if JOB_DEFINITIONS[key].get("is_cron"):
            raw_cron = " ".join(args).replace(":", "").replace(" ", "").strip()
            if re.match(r"^[\d,\*/]+$", raw_cron):
                return None, None, None, None
            return None, None, None, "Niepoprawny format minut dla Flash News. Użyj np. `25,55` lub `15,45`."

        # Case 2: Time-based schedules
        text = " ".join(args).lower().strip()
        tokens = text.split()

        parsed_day = None
        parsed_hour = None
        parsed_minute = None

        time_pattern = re.compile(r"^(\d{1,2}):(\d{2})$")
        hour_pattern = re.compile(r"^(\d{1,2})$")

        for token in tokens:
            # Check day of week
            if token in DAY_MAP:
                parsed_day = DAY_MAP[token]
                continue

            # Check time HH:MM
            tm_match = time_pattern.match(token)
            if tm_match:
                h, m = int(tm_match.group(1)), int(tm_match.group(2))
                if 0 <= h <= 23 and 0 <= m <= 59:
                    parsed_hour = h
                    parsed_minute = m
                    continue
                return None, None, None, f"Niepoprawna godzina `{token}`. Zakres to 00:00 - 23:59."

            # Check bare hour
            h_match = hour_pattern.match(token)
            if h_match:
                h = int(h_match.group(1))
                if 0 <= h <= 23:
                    parsed_hour = h
                    parsed_minute = 0
                    continue

        if parsed_hour is None:
            return None, None, None, "Nie rozpoznano godziny. Podaj czas w formacie `HH:MM` (np. `12:00` lub `14:30`)."

        # Fallback to existing configured day or default
        if parsed_day is None:
            parsed_day = current_config.get("day_of_week", JOB_DEFINITIONS[key].get("default_day", "*"))

        return parsed_day, parsed_hour, parsed_minute, None

    @commands.command(name="set_schedule", aliases=["ustaw_harmonogram", "set_time", "ustaw_czas"])
    @commands.has_permissions(administrator=True)
    async def set_schedule(self, ctx: commands.Context, job_type: str, *args: str) -> None:
        """Zmień godzinę i dzień publikacji wybranego raportu i zapisz trwale.

        Dostępne typy:
        - `weekly_outlook` (lub `weekly`, `tydzien`): Strategiczny plan tygodniowy (np. `!set_schedule weekly sun 10:00`)
        - `calendar` (lub `kalendarz`): Kalendarz makro (np. `!set_schedule calendar 07:00`)
        - `london` (lub `londyn`): Briefing sesji europejskiej (np. `!set_schedule london 07:15`)
        - `newyork` (lub `ny`): Briefing Wall Street (np. `!set_schedule ny 13:30`)
        - `asia` (lub `azja`): Briefing azjatycki (np. `!set_schedule asia 23:00`)
        - `accuracy` (lub `skutecznosc`): Tygodniowy raport skuteczności (np. `!set_schedule accuracy sobota 12:00`)
        - `portfolio` (lub `portfel`): Tygodniowy raport portfela (np. `!set_schedule portfolio sun 18:00`)
        - `portfolio_news` (lub `portfel_news`): Wiadomości spółek (np. `!set_schedule portfolio_news 14:00`)
        - `flash_news` (lub `flash`): Cykl minutowy newsów flash (np. `!set_schedule flash 25,55`)

        Przykłady:
        `!set_schedule accuracy sobota 12:00`
        `!set_schedule portfolio_news 15:30`
        `!set_schedule flash 15,45`
        """
        canonical_key = self._resolve_canonical_key(job_type)
        if not canonical_key:
            available = ", ".join([f"`{k}`" for k in JOB_DEFINITIONS.keys()])
            await ctx.send(f"❌ Nieznany typ zadania `{job_type}`.\nDostępne typy: {available}.")
            return

        current_cfg = self.state_manager.get_schedule(canonical_key)

        if JOB_DEFINITIONS[canonical_key].get("is_cron"):
            raw_cron = " ".join(args).replace(":", "").replace(" ", "").strip()
            if not raw_cron or not re.match(r"^[\d,\*/]+$", raw_cron):
                await ctx.send("❌ Dla Flash News podaj minuty po przecinku, np. `!set_schedule flash 25,55` lub `15,45`.")
                return

            new_cfg = {"minute_cron": raw_cron}
            self.state_manager.set_schedule(canonical_key, new_cfg)
            if hasattr(self.bot, "reschedule_job"):
                self.bot.reschedule_job(canonical_key)

            job_id = JOB_DEFINITIONS[canonical_key]["job_id"]
            next_run = None
            if hasattr(self.bot, "scheduler"):
                next_run = self.bot.scheduler.get_job_next_run(job_id)

            next_str = f"`{next_run.strftime('%Y-%m-%d %H:%M:%S')} CET`" if next_run else "*Zgodnie z cyklem*"
            await ctx.send(
                f"✅ **Zaktualizowano i zapisano trwale harmonogram** dla **{JOB_DEFINITIONS[canonical_key]['title']}**!\n"
                f"• **Cykl minutowy:** Co godzinę w minutach `:{raw_cron}`\n"
                f"• **Najbliższa publikacja:** {next_str}"
            )
            return

        # Time-based job
        parsed_day, parsed_h, parsed_m, err = self._parse_time_and_day(canonical_key, args, current_cfg)
        if err:
            await ctx.send(f"❌ {err}")
            return

        new_cfg = {
            "day_of_week": parsed_day,
            "hour": parsed_h,
            "minute": parsed_m,
        }
        self.state_manager.set_schedule(canonical_key, new_cfg)

        if hasattr(self.bot, "reschedule_job"):
            self.bot.reschedule_job(canonical_key)

        job_id = JOB_DEFINITIONS[canonical_key]["job_id"]
        next_run = None
        if hasattr(self.bot, "scheduler"):
            next_run = self.bot.scheduler.get_job_next_run(job_id)

        day_pl = POLISH_DAY_NAMES.get(parsed_day, parsed_day.upper() if parsed_day else "")
        time_fmt = f"{parsed_h:02d}:{parsed_m:02d}"
        next_str = f"`{next_run.strftime('%Y-%m-%d %H:%M:%S')} CET`" if next_run else "*Zgodnie z cyklem*"

        await ctx.send(
            f"✅ **Zaktualizowano i zapisano trwale harmonogram** dla **{JOB_DEFINITIONS[canonical_key]['title']}**!\n"
            f"• **Nowy termin:** {day_pl} o `{time_fmt}` CET\n"
            f"• **Najbliższa publikacja:** {next_str}"
        )
        logger.info("Schedule updated: %s -> %s %s", canonical_key, parsed_day, time_fmt)

    @commands.command(name="schedules", aliases=["harmonogram", "czasy", "schedule"])
    async def list_schedules(self, ctx: commands.Context) -> None:
        """Pokaż aktualny harmonogram wszystkich automatycznych publikacji bota."""
        schedules = self.state_manager.get_all_schedules()

        lines = [
            "## ⏱️ Harmonogram Publikacji Wiadomości • we.trade",
            "Konfiguracja automatycznych cykli raportów (trwały zapis w `data/state.json`).\n",
        ]

        for key, meta in JOB_DEFINITIONS.items():
            cfg = schedules.get(key, {})
            title = meta["title"]
            job_id = meta["job_id"]

            next_run = None
            if hasattr(self.bot, "scheduler"):
                next_run = self.bot.scheduler.get_job_next_run(job_id)
            next_str = next_run.strftime("%Y-%m-%d %H:%M:%S") + " CET" if next_run else "Oczekuje na aktywację"

            if meta.get("is_cron"):
                cron_val = cfg.get("minute_cron", "25,55")
                lines.append(
                    f"• **{title}** (`{key}`):\n"
                    f"  Co godzinę w minutach `:{cron_val}` • Najbliższy: `{next_str}`"
                )
            else:
                day_code = cfg.get("day_of_week", meta.get("default_day", "*"))
                day_pl = POLISH_DAY_NAMES.get(day_code, day_code.upper() if day_code else "")
                h = cfg.get("hour", 0)
                m = cfg.get("minute", 0)
                lines.append(
                    f"• **{title}** (`{key}`):\n"
                    f"  {day_pl} o `{h:02d}:{m:02d}` CET • Najbliższy: `{next_str}`"
                )

        lines.append("\n-# Użyj `!set_schedule <typ> <czas>` aby zmienić termin publikacji (np. `!set_schedule accuracy sobota 12:00`).")
        await send_full_message(ctx.channel, "\n".join(lines))


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(SchedulesCog(bot))
