"""Economic calendar service for fetching daily macro announcements and data releases."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
import aiohttp
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)

CALENDAR_RSS_URL = "https://www.forexfactory.com/rss/calendar.xml"


class CalendarService:
    """Service to fetch scheduled economic events."""

    async def fetch_todays_events(self) -> List[Dict[str, Any]]:
        """Fetch today's scheduled high and medium impact economic events."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=8),
                headers={"User-Agent": "NewsboxDiscordBot/0.1.0"},
            ) as session:
                async with session.get(CALENDAR_RSS_URL) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_calendar_rss(content)
        except Exception as err:
            logger.warning("Could not fetch live calendar RSS: %s. Using default calendar list.", err)

        return self._get_fallback_events()

    def _parse_calendar_rss(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse economic calendar RSS feed."""
        import feedparser

        feed = feedparser.parse(xml_content)
        events: List[Dict[str, Any]] = []

        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            impact = "🔴" if "High" in summary or "high" in title.lower() else "🟡"
            events.append({
                "title": title,
                "time": entry.get("published", datetime.utcnow().strftime("%H:%M UTC")),
                "currency": "USD" if "USD" in title else ("EUR" if "EUR" in title else "GLOBAL"),
                "impact": impact,
                "summary": summary,
            })
        return events or self._get_fallback_events()

    def _get_fallback_events(self) -> List[Dict[str, Any]]:
        """Fallback list of major economic events for today."""
        return [
            {
                "time": "14:30 CET",
                "currency": "USD",
                "title": "Core PCE Price Index m/m (Wskaźnik inflacji Fed)",
                "impact": "🔴",
            },
            {
                "time": "15:45 CET",
                "currency": "USD",
                "title": "US Flash Manufacturing & Services PMI",
                "impact": "🟡",
            },
            {
                "time": "16:00 CET",
                "currency": "EUR",
                "title": "Wystąpienie prezesa EBC (Lagarde)",
                "impact": "🔴",
            },
            {
                "time": "16:30 CET",
                "currency": "USD",
                "title": "Zapasy ropy naftowej wg EIA",
                "impact": "🟡",
            },
        ]
