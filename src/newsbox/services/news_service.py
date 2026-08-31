"""Multi-region business and macro news aggregator (Poland/Parkiet, EU, USA, World)."""

import asyncio
from typing import Any, Dict, List, Optional
import aiohttp
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)

# Configured multi-region RSS feeds
REGIONAL_FEEDS = {
    "PL": [
        {"name": "Bankier - Gospodarka", "url": "https://www.bankier.pl/rss/gospodarka.xml"},
        {"name": "Bankier - Rynki", "url": "https://www.bankier.pl/rss/wiadomosci.xml"},
        {"name": "Parkiet / GPW", "url": "https://www.parkiet.com/rss"},
    ],
    "USA": [
        {"name": "CNBC Economy", "url": "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=economy&sort=date"},
        {"name": "MarketWatch Top", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    ],
    "EU": [
        {"name": "Euronews Business", "url": "https://www.euronews.com/rss?format=mrss&level=theme&name=business"},
    ],
    "GLOBAL": [
        {"name": "Reuters Macro", "url": "https://feeds.feedburner.com/reuters/businessNews"},
        {"name": "CoinDesk Crypto", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    ],
}


class NewsService:
    """Aggregates and filters news from Polish, European, American, and Global financial outlets."""

    def __init__(self) -> None:
        self.seen_titles: set[str] = set()

    async def fetch_regional_news(self, region: str = "ALL", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch headlines for a specific region (PL, USA, EU, GLOBAL, or ALL)."""
        region_upper = region.upper()
        feeds_to_fetch = []

        if region_upper == "ALL":
            for reg, feeds in REGIONAL_FEEDS.items():
                for f in feeds:
                    feeds_to_fetch.append((reg, f["name"], f["url"]))
        elif region_upper in REGIONAL_FEEDS:
            for f in REGIONAL_FEEDS[region_upper]:
                feeds_to_fetch.append((region_upper, f["name"], f["url"]))
        else:
            logger.warning("Unknown region '%s', falling back to ALL.", region)
            for reg, feeds in REGIONAL_FEEDS.items():
                for f in feeds:
                    feeds_to_fetch.append((reg, f["name"], f["url"]))

        tasks = [self._fetch_feed(reg, name, url) for reg, name, url in feeds_to_fetch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_news: List[Dict[str, Any]] = []
        for res in results:
            if isinstance(res, list):
                all_news.extend(res)

        if not all_news:
            all_news = self._get_fallback_headlines(region_upper)

        # Deduplicate by title
        deduped = []
        seen = set()
        for item in all_news:
            title_key = item["title"].lower().strip()
            if title_key not in seen and len(title_key) > 5:
                seen.add(title_key)
                deduped.append(item)

        return deduped[:limit]

    async def _fetch_feed(self, region: str, source_name: str, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed."""
        import feedparser

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5),
                headers={"User-Agent": "NewsboxBot/0.1.0"},
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        items = []
                        for entry in feed.entries[:5]:
                            title = entry.get("title", "").strip()
                            link = entry.get("link", "")
                            summary = entry.get("summary", "")
                            published = entry.get("published", "")
                            if title:
                                items.append({
                                    "title": title,
                                    "url": link,
                                    "summary": summary[:200] if summary else "",
                                    "source": source_name,
                                    "region": region,
                                    "published": published,
                                })
                        return items
        except Exception as ex:
            logger.debug("Failed fetching feed %s: %s", url, ex)
        return []

    def _get_fallback_headlines(self, region: str) -> List[Dict[str, Any]]:
        """Fallback mock headlines."""
        fallbacks = [
            {
                "title": "WIG20 otwiera się z lekkim plusem, sektor bankowy na fali",
                "url": "https://www.bankier.pl",
                "source": "Parkiet / GPW",
                "region": "PL",
            },
            {
                "title": "RPP utrzyma stopy procentowe bez zmian – prognozy analityków",
                "url": "https://www.parkiet.com",
                "source": "Bankier",
                "region": "PL",
            },
            {
                "title": "S&P 500 futures steady ahead of key US retail sales data",
                "url": "https://www.cnbc.com",
                "source": "CNBC",
                "region": "USA",
            },
            {
                "title": "ECB signals data-dependent approach for upcoming interest rate decision",
                "url": "https://www.euronews.com",
                "source": "Euronews",
                "region": "EU",
            },
            {
                "title": "Bitcoin holds firm above key support as institutional ETF inflows rebound",
                "url": "https://www.coindesk.com",
                "source": "CoinDesk",
                "region": "GLOBAL",
            },
        ]
        if region == "ALL":
            return fallbacks
        return [f for f in fallbacks if f["region"] == region] or fallbacks
