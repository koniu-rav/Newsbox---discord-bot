"""Economic calendar service for fetching real-time 24h macro announcements (7:00-7:00 and 8:00-8:00 windows)."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
import aiohttp
from bs4 import BeautifulSoup

from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)

FAIR_ECONOMY_JSON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
TRADING_ECONOMICS_URL = "https://tradingeconomics.com/calendar"

WARSAW_TZ = ZoneInfo("Europe/Warsaw")
NY_TZ = ZoneInfo("America/New_York")


class CalendarService:
    """Service to fetch real-time scheduled economic events with dual source redundancy, 24h windowing, and caching."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._cache: Optional[List[Dict[str, Any]]] = None
        self._cache_date: Optional[str] = None
        self._cache_timestamp: float = 0.0

    async def fetch_todays_events(self, start_hour: int = 7) -> List[Dict[str, Any]]:
        """Fetch scheduled events for the 24-hour window from start_hour today (default 07:00) to start_hour tomorrow.
        Events that already took place before start_hour are strictly omitted.
        """
        now = datetime.now(WARSAW_TZ)
        start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        cache_key = f"{start_time.strftime('%Y-%m-%d')}_{start_hour}"
        now_ts = datetime.utcnow().timestamp()

        # Check in-memory cache
        if self._cache and self._cache_date == cache_key and (now_ts - self._cache_timestamp < 1800):
            logger.debug("Returning %d cached economic events for %s", len(self._cache), cache_key)
            return self._cache

        # 1. Try FairEconomy Weekly JSON feed
        events = await self._fetch_from_fair_economy(start_time, end_time)
        if events:
            self._update_cache(cache_key, events)
            return events

        # 2. Try TradingEconomics live scraper
        events = await self._fetch_from_trading_economics(start_time, end_time)
        if events:
            self._update_cache(cache_key, events)
            return events

        # 3. Dynamic day-based fallback
        fallback = self._get_dynamic_fallback(now, start_hour)
        return fallback

    def _update_cache(self, cache_key: str, events: List[Dict[str, Any]]) -> None:
        self._cache = events
        self._cache_date = cache_key
        self._cache_timestamp = datetime.utcnow().timestamp()

    async def _fetch_from_fair_economy(self, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch and parse FairEconomy JSON calendar feed filtering strictly within [start_dt, end_dt)."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6), headers=headers) as session:
                async with session.get(FAIR_ECONOMY_JSON_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        window_events = []
                        for ev in data:
                            raw_date = ev.get("date", "")
                            if not raw_date:
                                continue
                            try:
                                dt = datetime.fromisoformat(raw_date).astimezone(WARSAW_TZ)
                                if start_dt <= dt < end_dt:
                                    raw_impact = ev.get("impact", "Low")
                                    impact_map = {"High": "🔴", "Medium": "🟡", "Low": "⚪"}
                                    impact_emoji = impact_map.get(raw_impact, "🟡")
                                    weight = 1 if raw_impact == "High" else (2 if raw_impact == "Medium" else 3)

                                    title = ev.get("title", "")
                                    forecast = ev.get("forecast", "").strip()
                                    previous = ev.get("previous", "").strip()

                                    details = []
                                    if forecast:
                                        details.append(f"Prognoza: {forecast}")
                                    if previous:
                                        details.append(f"Poprz: {previous}")
                                    details_str = f" ({', '.join(details)})" if details else ""

                                    # Prefix "Jutro " if event occurs past midnight
                                    time_prefix = "Jutro " if dt.date() > start_dt.date() else ""
                                    time_str = f"{time_prefix}{dt.strftime('%H:%M CET')}"

                                    window_events.append({
                                        "title": f"{title}{details_str}",
                                        "time": time_str,
                                        "currency": ev.get("country", "GLOBAL"),
                                        "impact": impact_emoji,
                                        "weight": weight,
                                        "dt": dt,
                                    })
                            except Exception:
                                continue

                        if window_events:
                            window_events.sort(key=lambda x: (x["weight"], x["dt"]))
                            logger.info(
                                "Successfully fetched %d live events from FairEconomy for window %s to %s",
                                len(window_events),
                                start_dt.strftime("%d.%m %H:%M"),
                                end_dt.strftime("%d.%m %H:%M"),
                            )
                            return window_events
        except Exception as e:
            logger.debug("FairEconomy fetch skipped or rate-limited: %s", e)

        return []

    async def _fetch_from_trading_economics(self, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """Fetch and parse TradingEconomics live HTML table within [start_dt, end_dt)."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            today_str = start_dt.strftime("%Y-%m-%d")
            tomorrow_str = end_dt.strftime("%Y-%m-%d")

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8), headers=headers) as session:
                async with session.get(TRADING_ECONOMICS_URL) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        table = soup.find("table", {"id": "calendar"})
                        if not table:
                            return []

                        curr_map = {
                            "UNITED STATES": "USD", "US": "USD",
                            "EURO AREA": "EUR", "GERMANY": "EUR", "FRANCE": "EUR", "ITALY": "EUR", "SPAIN": "EUR", "EA": "EUR", "DE": "EUR",
                            "UNITED KINGDOM": "GBP", "GB": "GBP",
                            "POLAND": "PLN", "PL": "PLN",
                            "JAPAN": "JPY", "JP": "JPY",
                            "CANADA": "CAD", "CA": "CAD",
                            "SWITZERLAND": "CHF", "CH": "CHF",
                            "AUSTRALIA": "AUD", "AU": "AUD",
                            "CHINA": "CNY", "CN": "CNY",
                            "NEW ZEALAND": "NZD", "NZ": "NZD",
                        }

                        high_keywords = [
                            "CPI", "INFLATION", "INTEREST RATE", "FED", "FOMC", "ECB", "NFP", "NON-FARM",
                            "GDP", "PCE", "PMI", "UNEMPLOYMENT", "RATE DECISION", "PAYROLLS", "RETAIL SALES",
                            "SPEECH", "PRESS CONFERENCE"
                        ]
                        med_keywords = [
                            "PPI", "TRADE BALANCE", "CONSUMER CONFIDENCE", "HOUSING", "ORDERS", "INVENTORIES",
                            "BUDGET", "CLAIMS", "AUCTION", "BALANCE OF TRADE", "BEIGE BOOK"
                        ]

                        results = []
                        for r in table.find_all("tr"):
                            first_td = r.find("td")
                            if not first_td:
                                continue
                            classes = first_td.get("class", [])
                            
                            target_date = None
                            if today_str in classes:
                                target_date = today_str
                            elif tomorrow_str in classes:
                                target_date = tomorrow_str
                            if not target_date:
                                continue

                            cells = r.find_all("td")
                            if len(cells) < 5:
                                continue

                            time_val = " ".join(cells[0].text.split())
                            country_raw = r.get("data-country", cells[1].text.strip()).strip().upper()
                            if country_raw not in curr_map:
                                continue

                            # Parse time in EDT and convert to Europe/Warsaw
                            event_dt = None
                            if time_val:
                                try:
                                    t_clean = " ".join(time_val.replace("EST", "").replace("EDT", "").split())
                                    dt_ny = datetime.strptime(f"{target_date} {t_clean}", "%Y-%m-%d %I:%M %p").replace(tzinfo=NY_TZ)
                                    event_dt = dt_ny.astimezone(WARSAW_TZ)
                                except Exception:
                                    pass

                            # Filter out events before start_dt (e.g. before 07:00 / 08:00) or after end_dt
                            if event_dt and not (start_dt <= event_dt < end_dt):
                                continue

                            currency = curr_map[country_raw]
                            event_raw = " ".join(cells[4].text.split()).replace("®", "").strip()
                            forecast = " ".join(cells[6].text.split()).replace("®", "").strip() if len(cells) > 6 else ""
                            previous = " ".join(cells[7].text.split()).replace("®", "").strip() if len(cells) > 7 else ""

                            ev_upper = event_raw.upper()
                            if any(k in ev_upper for k in high_keywords):
                                impact = "🔴"
                                weight = 1
                            elif any(k in ev_upper for k in med_keywords):
                                impact = "🟡"
                                weight = 2
                            else:
                                impact = "⚪"
                                weight = 3

                            details = []
                            if forecast:
                                details.append(f"Prognoza: {forecast}")
                            if previous:
                                details.append(f"Poprz: {previous}")
                            details_str = f" ({', '.join(details)})" if details else ""

                            time_prefix = "Jutro " if event_dt and event_dt.date() > start_dt.date() else ""
                            formatted_time = f"{time_prefix}{event_dt.strftime('%H:%M CET')}" if event_dt else f"{time_val} EST"

                            results.append({
                                "title": f"{event_raw}{details_str}",
                                "time": formatted_time,
                                "currency": currency,
                                "impact": impact,
                                "weight": weight,
                                "dt": event_dt or start_dt,
                            })

                        if results:
                            results.sort(key=lambda x: (x["weight"], x["dt"]))
                            logger.info(
                                "Successfully scraped %d live events from TradingEconomics for window %s to %s",
                                len(results),
                                start_dt.strftime("%d.%m %H:%M"),
                                end_dt.strftime("%d.%m %H:%M"),
                            )
                            return results
        except Exception as e:
            logger.warning("TradingEconomics scraper failed: %s", e)

        return []

    def _get_dynamic_fallback(self, now: datetime, start_hour: int) -> List[Dict[str, Any]]:
        """Fallback list adjusted for the day of the week for events from start_hour onwards."""
        weekday = now.weekday()
        if weekday == 0:  # Monday
            return [
                {"time": "15:45 CET", "currency": "USD", "title": "S&P Global Manufacturing PMI (Final)", "impact": "🟡"},
                {"time": "16:00 CET", "currency": "USD", "title": "ISM Manufacturing PMI & Prices Paid", "impact": "🔴"},
            ]
        elif weekday == 1:  # Tuesday
            return [
                {"time": "16:00 CET", "currency": "USD", "title": "JOLTs Job Openings (Liczba wakatów USA)", "impact": "🔴"},
                {"time": "16:00 CET", "currency": "USD", "title": "Factory Orders m/m", "impact": "🟡"},
            ]
        elif weekday == 2:  # Wednesday
            return [
                {"time": "14:15 CET", "currency": "USD", "title": "ADP Non-Farm Employment Change (Raport o zatrudnieniu)", "impact": "🔴"},
                {"time": "15:45 CET", "currency": "CAD", "title": "BoC Interest Rate Decision & Monetary Policy", "impact": "🔴"},
                {"time": "16:30 CET", "currency": "USD", "title": "Zapasy ropy naftowej wg EIA", "impact": "🟡"},
                {"time": "Jutro 01:30 CET", "currency": "AUD", "title": "Bilans Handlowy Australii & Chiny PMI", "impact": "🟡"},
            ]
        elif weekday == 3:  # Thursday
            return [
                {"time": "14:30 CET", "currency": "USD", "title": "Initial Jobless Claims (Wnioski o zasiłek dla bezrobotnych)", "impact": "🔴"},
                {"time": "15:45 CET", "currency": "USD", "title": "S&P Global Services PMI (Final)", "impact": "🟡"},
                {"time": "16:00 CET", "currency": "USD", "title": "ISM Services PMI (Sektor Usług USA)", "impact": "🔴"},
            ]
        elif weekday == 4:  # Friday
            return [
                {"time": "14:30 CET", "currency": "USD", "title": "Non-Farm Payrolls (NFP) & Stopa Bezrobocia USA", "impact": "🔴"},
                {"time": "14:30 CET", "currency": "USD", "title": "Średnie zarobki godzinowe m/m", "impact": "🔴"},
            ]
        return [
            {"time": "09:00 CET", "currency": "EUR", "title": "Otwarcie sesji europejskiej i publikacje PMI", "impact": "🟡"}
        ]
