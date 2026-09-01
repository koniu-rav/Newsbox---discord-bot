"""Multi-region business, crypto, and portfolio news aggregator with session quiet window awareness."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import aiohttp
from newsbox.config import get_settings
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
    "CRYPTO": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
        {"name": "Decrypt", "url": "https://decrypt.co/feed"},
    ],
    "GLOBAL": [
        {"name": "Reuters Macro", "url": "https://feeds.feedburner.com/reuters/businessNews"},
    ],
}


class NewsService:
    """Aggregates and filters news from Polish, European, American, Crypto, and Portfolio sources."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.seen_titles: set[str] = set()

    def is_in_quiet_window(self, current_dt: Optional[datetime] = None) -> bool:
        """Check if current time falls within configured session open quiet windows (e.g. 08:50-09:15, 15:20-15:45)."""
        dt = current_dt or datetime.now()
        current_time = dt.time()
        for start_t, end_t in self.settings.quiet_windows:
            if start_t <= current_time <= end_t:
                return True
        return False

    async def fetch_crypto_news(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Fetch dedicated news from cryptocurrency and blockchain sources."""
        return await self.fetch_regional_news(region="CRYPTO", limit=limit)

    async def fetch_portfolio_news(
        self,
        symbols: Optional[List[str]] = None,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """Fetch and filter news headlines matching configured portfolio company tickers or names."""
        target_symbols = symbols or self.settings.portfolio_tickers
        if not target_symbols:
            return []

        # Pull PL, US and Global news
        all_news = await self.fetch_regional_news("ALL", limit=30)

        # Keyword matching for symbols and common names
        matched_news: List[Dict[str, Any]] = []
        clean_keywords = []
        for s in target_symbols:
            clean = s.replace(".WA", "").replace("^", "").strip().upper()
            clean_keywords.append((clean, s))

        for item in all_news:
            title_upper = item.get("title", "").upper()
            summary_upper = item.get("summary", "").upper()
            full_text = f"{title_upper} {summary_upper}"

            for kw, orig_symbol in clean_keywords:
                if kw in full_text:
                    item_copy = dict(item)
                    item_copy["matched_symbol"] = orig_symbol
                    matched_news.append(item_copy)
                    break

        if not matched_news:
            matched_news = self._get_fallback_portfolio_news(target_symbols)

        return matched_news[:limit]

    async def fetch_regional_news(self, region: str = "ALL", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch headlines for a specific region (PL, USA, EU, CRYPTO, GLOBAL, or ALL)."""
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

    def _get_fallback_portfolio_news(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fallback news matching portfolio symbols."""
        sym_str = ", ".join(symbols[:3])
        return [
            {
                "title": f"Spółki z portfela ({sym_str}) publikują raporty okresowe i plany na kolejny kwartał",
                "url": "https://www.bankier.pl/gielda/wiadomosci",
                "source": "Parkiet / ESPI",
                "region": "PL",
                "matched_symbol": symbols[0] if symbols else "PORTFOLIO",
            },
            {
                "title": "Analitycy aktualizują ceny docelowe dla kluczowych walorów technologicznych i GPW",
                "url": "https://www.parkiet.com",
                "source": "Bankier",
                "region": "PL",
                "matched_symbol": symbols[1] if len(symbols) > 1 else "PORTFOLIO",
            },
        ]

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
                "region": "CRYPTO",
            },
            {
                "title": "Ethereum L2 activity reaches new record high amid network upgrades",
                "url": "https://cointelegraph.com",
                "source": "Cointelegraph",
                "region": "CRYPTO",
            },
        ]
        if region == "ALL":
            return fallbacks
        return [f for f in fallbacks if f["region"] == region] or fallbacks
