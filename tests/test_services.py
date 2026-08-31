"""Unit tests for services layer."""

import pytest
from unittest.mock import AsyncMock, patch
from newsbox.services.gemini_service import GeminiService
from newsbox.services.market_service import MarketService
from newsbox.services.calendar_service import CalendarService
from newsbox.services.news_service import NewsService


@pytest.mark.asyncio
async def test_gemini_service_prompt_loading():
    """Test loading and caching prompt templates."""
    service = GeminiService(api_key="", prompts_dir="prompts")
    template = service.get_prompt_template("trader_advisory", default="")
    assert len(template) > 0
    assert "MARKET REGIME" in template


@pytest.mark.asyncio
async def test_gemini_service_trader_advisory_fallback(sample_market_data, sample_calendar_events, sample_headlines):
    """Test fallback trader advisory when client is uninitialized."""
    service = GeminiService(api_key="")
    advice = await service.generate_trader_advisory(
        market_data=sample_market_data,
        economic_events=sample_calendar_events,
        news_headlines=sample_headlines,
    )
    assert "MARKET REGIME" in advice
    assert "CO MOŻNA DZISIAJ HANDLOWAĆ" in advice
    assert "CZEGO DZISIAJ NIE HANDLOWAĆ" in advice


@pytest.mark.asyncio
async def test_market_service_dynamic_tickers():
    """Test market service with custom tickers."""
    custom = {"WIG20": "WIG20.WA", "GOLD": "GC=F"}
    service = MarketService(tickers=custom)
    snapshot = service._get_fallback_snapshot()
    assert "WIG20" in snapshot
    assert "GOLD" in snapshot
    assert snapshot["WIG20"]["symbol"] == "WIG20"


@pytest.mark.asyncio
async def test_news_service_regional_fallback():
    """Test regional news fetching and fallback."""
    service = NewsService()
    pl_news = await service.fetch_regional_news("PL", limit=3)
    assert len(pl_news) > 0
    assert any(n.get("region") == "PL" for n in pl_news)
