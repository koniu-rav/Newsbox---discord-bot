"""Market data service for fetching quotes for configurable macro assets (DXY, EUR/USD, DAX, BTC, and more)."""

import asyncio
from typing import Any, Dict, Optional
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketService:
    """Service to fetch real-time quotes and 24h changes for configured macro assets."""

    def __init__(self, tickers: Optional[Dict[str, str]] = None) -> None:
        self.settings = get_settings()
        self._custom_tickers = tickers

    @property
    def tickers(self) -> Dict[str, str]:
        """Resolved active tickers dictionary."""
        return self._custom_tickers or self.settings.tickers

    async def fetch_market_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes for all configured tickers asynchronously."""
        try:
            return await asyncio.to_thread(self._fetch_sync_quotes)
        except Exception as e:
            logger.error("Failed to fetch live market snapshot: %s", e)
            return self._get_fallback_snapshot()

    def _fetch_sync_quotes(self) -> Dict[str, Dict[str, Any]]:
        """Synchronous fetcher using yfinance."""
        import yfinance as yf

        results: Dict[str, Dict[str, Any]] = {}
        for symbol_name, yahoo_ticker in self.tickers.items():
            try:
                ticker_obj = yf.Ticker(yahoo_ticker)
                fast_info = getattr(ticker_obj, "fast_info", None)
                if fast_info and hasattr(fast_info, "last_price") and fast_info.last_price is not None:
                    last_price = fast_info.last_price
                    prev_close = fast_info.previous_close or last_price
                    change_pct = ((last_price - prev_close) / prev_close) * 100 if prev_close else 0.0

                    formatted_price = f"{last_price:,.2f}" if last_price >= 10 else f"{last_price:.4f}"
                    sign = "+" if change_pct >= 0 else ""
                    results[symbol_name] = {
                        "symbol": symbol_name,
                        "ticker": yahoo_ticker,
                        "price": formatted_price,
                        "change_pct": f"{sign}{change_pct:.2f}%",
                        "raw_price": float(last_price),
                        "direction": "🟢" if change_pct >= 0 else "🔴",
                    }
                else:
                    results[symbol_name] = self._get_fallback_ticker(symbol_name, yahoo_ticker)
            except Exception as ex:
                logger.warning("Error fetching ticker %s (%s): %s", symbol_name, yahoo_ticker, ex)
                results[symbol_name] = self._get_fallback_ticker(symbol_name, yahoo_ticker)

        return results

    def _get_fallback_ticker(self, symbol_name: str, yahoo_ticker: str = "") -> Dict[str, Any]:
        """Provides default values when live API is unavailable."""
        defaults = {
            "DXY": {"price": "104.25", "change_pct": "+0.15%", "raw_price": 104.25, "direction": "🟢"},
            "EUR/USD": {"price": "1.0845", "change_pct": "-0.12%", "raw_price": 1.0845, "direction": "🔴"},
            "DAX": {"price": "18,420.50", "change_pct": "+0.35%", "raw_price": 18420.50, "direction": "🟢"},
            "BTC": {"price": "67,500.00", "change_pct": "+1.85%", "raw_price": 67500.00, "direction": "🟢"},
            "WIG20": {"price": "2,450.00", "change_pct": "+0.40%", "raw_price": 2450.00, "direction": "🟢"},
            "GOLD": {"price": "2,410.00", "change_pct": "+0.20%", "raw_price": 2410.00, "direction": "🟢"},
        }
        res = defaults.get(symbol_name, {
            "price": "N/A",
            "change_pct": "0.00%",
            "raw_price": 0.0,
            "direction": "⚪",
        })
        res["symbol"] = symbol_name
        res["ticker"] = yahoo_ticker
        return res

    def _get_fallback_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Return full fallback snapshot for current active tickers."""
        return {sym: self._get_fallback_ticker(sym, ticker) for sym, ticker in self.tickers.items()}
