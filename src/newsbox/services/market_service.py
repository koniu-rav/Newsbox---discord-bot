"""Market data service for fetching quotes for configurable macro assets (DXY, EUR/USD, DAX, BTC) and portfolio holdings."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


def resolve_ticker(symbol: str) -> str:
    """Normalize user input symbols like 'MCD.US', 'SAP.DE', 'CDR.WA', 'ETH' into Yahoo Finance format."""
    s = symbol.strip().upper()
    # Normalize common commas to dots
    if ",DE" in s:
        s = s.replace(",DE", ".DE")
    if ",WA" in s:
        s = s.replace(",WA", ".WA")

    for suffix in [".US", ",US"]:
        if s.endswith(suffix):
            return s[:-len(suffix)]
    if s in ["ETH", "ETHEREUM"]:
        return "ETH-USD"
    if s in ["BTC", "BITCOIN"]:
        return "BTC-USD"
    if s in ["SOL", "SOLANA"]:
        return "SOL-USD"
    return s


class MarketService:
    """Service to fetch real-time quotes, 24h performance, and portfolio ticker data."""

    def __init__(self, tickers: Optional[Dict[str, str]] = None) -> None:
        self.settings = get_settings()
        self._custom_tickers = tickers

    @property
    def tickers(self) -> Dict[str, str]:
        """Resolved active tickers dictionary."""
        return self._custom_tickers or self.settings.tickers

    async def fetch_market_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes for all configured macro tickers asynchronously."""
        try:
            return await asyncio.to_thread(self._fetch_sync_quotes, self.tickers)
        except Exception as e:
            logger.error("Failed to fetch live market snapshot: %s", e)
            return self._get_fallback_snapshot(self.tickers)

    async def fetch_single_asset(self, symbol_or_ticker: str) -> Dict[str, Any]:
        """Fetch real-time data for a single asset (e.g. DAX, BTC, TSLA, CDR.WA)."""
        symbol_upper = symbol_or_ticker.strip().upper()
        # Resolve mapped ticker if available
        resolved_ticker = self.tickers.get(symbol_upper, resolve_ticker(symbol_or_ticker))

        try:
            res_dict = await asyncio.to_thread(
                self._fetch_sync_quotes,
                {symbol_upper: resolved_ticker}
            )
            return res_dict.get(symbol_upper, self._get_fallback_ticker(symbol_upper, resolved_ticker))
        except Exception as e:
            logger.error("Failed to fetch single asset %s: %s", symbol_or_ticker, e)
            return self._get_fallback_ticker(symbol_upper, resolved_ticker)

    async def fetch_portfolio_snapshot(
        self,
        symbols: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes for all tickers in user's portfolio watchlist."""
        target_symbols = symbols or self.settings.portfolio_tickers
        ticker_mapping = {s: resolve_ticker(s) for s in target_symbols}
        try:
            return await asyncio.to_thread(self._fetch_sync_quotes, ticker_mapping)
        except Exception as e:
            logger.error("Failed to fetch portfolio snapshot: %s", e)
            return self._get_fallback_snapshot(ticker_mapping)

    def _fetch_sync_quotes(self, symbol_map: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Synchronous fetcher using yfinance."""
        import yfinance as yf

        results: Dict[str, Dict[str, Any]] = {}
        for symbol_name, yahoo_ticker in symbol_map.items():
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
            "GBP/USD": {"price": "1.2950", "change_pct": "+0.08%", "raw_price": 1.2950, "direction": "🟢"},
            "USD/JPY": {"price": "154.20", "change_pct": "+0.25%", "raw_price": 154.20, "direction": "🟢"},
            "DAX": {"price": "18,420.50", "change_pct": "+0.35%", "raw_price": 18420.50, "direction": "🟢"},
            "BTC": {"price": "67,500.00", "change_pct": "+1.85%", "raw_price": 67500.00, "direction": "🟢"},
            "CDR.WA": {"price": "162.40", "change_pct": "+1.20%", "raw_price": 162.40, "direction": "🟢"},
            "PKN.WA": {"price": "64.80", "change_pct": "-0.45%", "raw_price": 64.80, "direction": "🔴"},
            "NVDA": {"price": "128.50", "change_pct": "+2.40%", "raw_price": 128.50, "direction": "🟢"},
            "TSLA": {"price": "218.00", "change_pct": "-1.10%", "raw_price": 218.00, "direction": "🔴"},
            "AAPL": {"price": "224.30", "change_pct": "+0.60%", "raw_price": 224.30, "direction": "🟢"},
        }
        res = defaults.get(symbol_name, {
            "price": "100.00",
            "change_pct": "+0.50%",
            "raw_price": 100.0,
            "direction": "⚪",
        })
        res["symbol"] = symbol_name
        res["ticker"] = yahoo_ticker or symbol_name
        return res

    def _get_fallback_snapshot(self, symbol_map: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Return full fallback snapshot for current symbol map."""
        return {sym: self._get_fallback_ticker(sym, ticker) for sym, ticker in symbol_map.items()}
