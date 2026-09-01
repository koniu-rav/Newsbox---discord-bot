"""Unit tests for services layer."""

import pytest
from unittest.mock import AsyncMock, patch
from newsbox.services.gemini_service import GeminiService
from newsbox.services.market_service import MarketService
from newsbox.services.calendar_service import CalendarService
from newsbox.services.news_service import NewsService


@pytest.mark.asyncio
async def test_gemini_service_single_asset():
    """Test generating single asset advisory."""
    service = GeminiService(api_key="", prompts_dir="prompts")
    asset_data = {"price": "18,450.00", "change_pct": "+0.45%", "ticker": "^GDAXI"}
    advice = await service.generate_single_asset_advisory("DAX", asset_data, [])
    assert "DAX" in advice
    assert "Byczy" in advice or "Long" in advice or "ANALIZA" in advice


@pytest.mark.asyncio
async def test_market_service_single_asset():
    """Test fetching single asset quote."""
    service = MarketService()
    quote = await service.fetch_single_asset("DAX")
    assert "price" in quote
    assert quote["symbol"] == "DAX"


@pytest.mark.asyncio
async def test_news_service_crypto():
    """Test fetching crypto news feed."""
    service = NewsService()
    crypto_news = await service.fetch_crypto_news(limit=3)
    assert len(crypto_news) > 0
    assert any(n.get("region") == "CRYPTO" for n in crypto_news)


@pytest.mark.asyncio
async def test_news_service_portfolio():
    """Test portfolio news matching."""
    service = NewsService()
    port_news = await service.fetch_portfolio_news(["CDR.WA", "NVDA"], limit=3)
    assert len(port_news) > 0
