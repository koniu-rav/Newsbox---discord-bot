"""Economic calendar service for fetching real-time daily macro announcements and data releases."""

import asyncio
from datetime import datetime, date
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


class CalendarService:
    """Service to fetch real-time scheduled economic events with dual source redundancy and caching."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._cache: Optional[List[Dict[str, Any]]] = None
        self._cache_date: Optional[str] = None
        self._cache_timestamp: float = 0.0

    async def fetch_todays_events(self) -> List[Dict[str, Any]]:
        """Fetch today's scheduled economic events (cached for 30 minutes)."""
        now = datetime.now(WARSAW_TZ)
        today_str = now.strftime("%Y-%m-%d")
        now_ts = datetime.utcnow().timestamp()

        # Check in-memory cache
        if self._cache and self._cache_date == today_str and (now_ts - self._cache_timestamp < 1800):
            logger.debug("Returning %d cached economic events for %s", len(self._cache), today_str)
            return self._cache

        # 1. Try FairEconomy Weekly JSON feed
        events = await self._fetch_from_fair_economy(today_str)
        if events:
            self._update_cache(today_str, events)
            return events

        # 2. Try TradingEconomics live scraper
        events = await self._fetch_from_trading_economics(today_str)
        if events:
            self._update_cache(today_str, events)
            return events

        # 3. Dynamic day-based fallback
        fallback = self._get_dynamic_fallback(now)
        return fallback

    def _update_cache(self, today_str: str, events: List[Dict[str, Any]]) -> None:
        self._cache = events
        self._cache_date = today_str
        self._cache_timestamp = datetime.utcnow().timestamp()

    async def _fetch_from_fair_economy(self, today_str: str) -> List[Dict[str, Any]]:
        """Fetch and parse FairEconomy JSON calendar feed."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6), headers=headers) as session:
                async with session.get(FAIR_ECONOMY_JSON_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        today_events = []
                        for ev in data:
                            raw_date = ev.get("date", "")
                            if not raw_date:
                                continue
                            try:
                                dt = datetime.fromisoformat(raw_date).astimezone(WARSAW_TZ)
                                if dt.strftime("%Y-%m-%d") == today_str:
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

                                    today_events.append({
                                        "title": f"{title}{details_str}",
                                        "time": dt.strftime("%H:%M CET"),
                                        "currency": ev.get("country", "GLOBAL"),
                                        "impact": impact_emoji,
                                        "weight": weight,
                                    })
                            except Exception:
                                continue

                        if today_events:
                            today_events.sort(key=lambda x: (x["weight"], x["time"]))
                            logger.info("Successfully fetched %d live events from FairEconomy for %s", len(today_events), today_str)
                            return today_events
        except Exception as e:
            logger.debug("FairEconomy fetch skipped or rate-limited: %s", e)

        return []

    async def _fetch_from_trading_economics(self, today_str: str) -> List[Dict[str, Any]]:
        """Fetch and parse TradingEconomics live HTML table."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
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
                        }

                        high_keywords = [
                            "CPI", "INFLATION", "INTEREST RATE", "FED", "FOMC", "ECB", "NFP", "NON-FARM",
                            "GDP", "PCE", "PMI", "UNEMPLOYMENT", "RATE DECISION", "PAYROLLS", "RETAIL SALES",
                            "SPEECH", "PRESS CONFERENCE"
                        ]
                        med_keywords = [
                            "PPI", "TRADE BALANCE", "CONSUMER CONFIDENCE", "HOUSING", "ORDERS", "INVENTORIES",
                            "BUDGET", "CLAIMS", "AUCTION", "BALANCE OF TRADE"
                        ]

                        results = []
                        for r in table.find_all("tr"):
                            first_td = r.find("td")
                            if not first_td:
                                continue
                            if today_str not in first_td.get("class", []):
                                continue

                            cells = r.find_all("td")
                            if len(cells) < 5:
                                continue

                            time_val = " ".join(cells[0].text.split())
                            country_raw = r.get("data-country", cells[1].text.strip()).strip().upper()
                            if country_raw not in curr_map:
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

                            results.append({
                                "title": f"{event_raw}{details_str}",
                                "time": f"{time_val} EST" if time_val else "Sesja Dzisiejsza",
                                "currency": currency,
                                "impact": impact,
                                "weight": weight,
                            })

                        if results:
                            results.sort(key=lambda x: (x["weight"], x["time"]))
                            logger.info("Successfully scraped %d live events from TradingEconomics for %s", len(results), today_str)
                            return results
        except Exception as e:
            logger.warning("TradingEconomics scraper failed: %s", e)

        return []

    def _get_dynamic_fallback(self, now: datetime) -> List[Dict[str, Any]]:
        """Fallback list adjusted for the day of the week."""
        weekday = now.weekday()  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday
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
            {"time": "08:00 CET", "currency": "EUR", "title": "Wydarzenia makroekonomiczne i otwarcie sesji europejskiej", "impact": "🟡"}
        ]
