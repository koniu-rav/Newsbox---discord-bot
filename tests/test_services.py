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


@pytest.mark.asyncio
async def test_gemini_service_session_advisory_filters_macro_events():
    """Test that session advisory strictly includes 🔴 and 🟡 events and excludes ⚪."""
    service = GeminiService(api_key="test-key", prompts_dir="prompts")
    service._client = AsyncMock()

    with patch.object(service, "_call_gemini", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "Briefing OK"
        events = [
            {"time": "09:00", "currency": "EUR", "title": "German CPI", "impact": "🔴", "weight": 1},
            {"time": "10:30", "currency": "GBP", "title": "UK Services PMI", "impact": "🟡", "weight": 2},
            {"time": "11:00", "currency": "EUR", "title": "Minor Survey", "impact": "⚪", "weight": 3},
            {"time": "12:00", "currency": "USD", "title": "Low Impact Stat", "impact": "⚪", "weight": 3},
        ]
        res = await service.generate_session_advisory(
            session_key="london",
            market_data={"EUR/USD": {"price": "1.0850", "change_pct": "+0.1%"}},
            economic_events=events,
            news_headlines=[],
        )
        assert res == "Briefing OK"
        mock_call.assert_called_once()
        prompt_arg = mock_call.call_args[0][0]
        assert "German CPI" in prompt_arg
        assert "UK Services PMI" in prompt_arg
        assert "Minor Survey" not in prompt_arg
        assert "Low Impact Stat" not in prompt_arg


@pytest.mark.asyncio
async def test_gemini_service_model_fallback_on_error():
    """Test that _call_gemini tries candidate fallback models when primary model fails."""
    from unittest.mock import MagicMock
    service = GeminiService(api_key="test-key", model_name="failing-model", prompts_dir="prompts")
    mock_client = MagicMock()
    service._client = mock_client

    class MockResponse:
        text = "Odpowiedź z modelu zapasowego"
        candidates = []

    # First call (failing-model) raises Exception; second call (fallback candidate) succeeds
    mock_client.models.generate_content.side_effect = [
        Exception("503 UNAVAILABLE"),
        MockResponse(),
    ]

    result = await service._call_gemini("test prompt", fallback_msg="BŁĄD")
    assert result == "Odpowiedź z modelu zapasowego"
    assert mock_client.models.generate_content.call_count == 2


