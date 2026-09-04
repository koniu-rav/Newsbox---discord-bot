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


@pytest.mark.asyncio
async def test_gemini_service_generate_macro_alert_impact():
    """Test generating short market impact commentary for a macro release."""
    service = GeminiService(api_key="test-key", prompts_dir="prompts")
    with patch.object(service, "_call_gemini", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "Wyższy odczyt NFP wspiera kurs dolara."
        event = {
            "title": "Non-Farm Employment Change",
            "currency": "USD",
            "actual": "+72K",
            "forecast": "55K",
            "previous": "-23K",
            "sentiment_desc": "Wyższy od prognoz",
        }
        res = await service.generate_macro_alert_impact(event)
        assert "wspiera kurs dolara" in res
        mock_call.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_service_generate_macro_batch_impact():
    """Test generating short market impact lines for a batch of events."""
    service = GeminiService(api_key="test-key", prompts_dir="prompts")
    with patch.object(service, "_call_gemini", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "1. Wyższy odczyt z rynku pracy wspiera walutę CAD.\n2. Lepszy odczyt NFP umacnia dolara."
        events = [
            {
                "event_id": "te_cad_1",
                "title": "Employment Change",
                "currency": "CAD",
                "actual": "44.0K",
                "forecast": "15.1K",
                "previous": "75.1K",
                "sentiment_desc": "Wyższy od prognoz",
                "is_speech": False,
            },
            {
                "event_id": "te_usd_1",
                "title": "Non Farm Payrolls",
                "currency": "USD",
                "actual": "162K",
                "forecast": "56K",
                "previous": "21K",
                "sentiment_desc": "Wyższy od prognoz",
                "is_speech": False,
            },
            {
                "event_id": "te_gbp_speech",
                "title": "BOE Gov Bailey Speaks",
                "currency": "GBP",
                "is_speech": True,
                "speech_note": "rozpoczął się (Bailey mówi, dajmy znać ze event sie rozpoczął)",
            },
        ]
        impacts = await service.generate_macro_batch_impact(events)
        assert "te_cad_1" in impacts
        assert "te_usd_1" in impacts
        assert "te_gbp_speech" in impacts
        assert "wspiera walutę CAD" in impacts["te_cad_1"]
        assert "umacnia dolara" in impacts["te_usd_1"]
        assert "Bailey mówi" in impacts["te_gbp_speech"]


@pytest.mark.asyncio
async def test_calendar_service_fetch_live_published_macro_events():
    """Test parsing, speech detection, and filtering of live economic events."""
    from zoneinfo import ZoneInfo
    from datetime import datetime
    WARSAW_TZ = ZoneInfo("Europe/Warsaw")
    today_str = datetime.now(WARSAW_TZ).strftime("%Y-%m-%d")

    mock_html = f"""
    <table id="calendar">
        <tr data-id="101" data-country="united states">
            <td class="{today_str}">12:30 PM</td>
            <td>US</td>
            <td></td>
            <td>US</td>
            <td>Non Farm Payrolls AUG</td>
            <td><span id="actual">72K</span></td>
            <td><span id="previous">-23K</span></td>
            <td><span id="consensus">55K</span></td>
        </tr>
        <tr data-id="102" data-country="united states">
            <td class="{today_str}">12:30 PM</td>
            <td>US</td>
            <td></td>
            <td>US</td>
            <td>Unemployment Rate AUG</td>
            <td><span id="actual"></span></td>
            <td><span id="previous">4.3%</span></td>
            <td><span id="consensus">4.3%</span></td>
        </tr>
        <tr data-id="103" data-country="germany">
            <td class="{today_str}">08:00 AM</td>
            <td>DE</td>
            <td></td>
            <td>DE</td>
            <td>German Factory Orders MoM</td>
            <td><span id="actual">0.3%</span></td>
            <td><span id="previous">3.1%</span></td>
            <td><span id="consensus"></span></td>
        </tr>
        <tr data-id="104" data-country="united kingdom">
            <td class="{today_str}">08:50 AM</td>
            <td>GB</td>
            <td></td>
            <td>GB</td>
            <td>BOE Gov Bailey Speaks</td>
            <td><span id="actual"></span></td>
            <td><span id="previous"></span></td>
            <td><span id="consensus"></span></td>
        </tr>
    </table>
    """

    class MockResponse:
        status = 200
        async def text(self):
            return mock_html
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    class MockSession:
        def get(self, url):
            return MockResponse()
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    service = CalendarService()
    with patch("aiohttp.ClientSession", return_value=MockSession()):
        events = await service.fetch_live_published_macro_events()
        # Event 101 (NFP) is published and 🔴 High impact -> included
        # Event 102 (Unemployment) has empty actual -> excluded
        # Event 103 (German Factory Orders) is excluded (unwanted noise)
        # Event 104 (Bailey Speech) is a 🔴 speech whose time (08:50 UTC = 10:50 CET) has passed -> included as speech
        event_ids = [e["event_id"] for e in events]
        assert "te_101" in event_ids
        assert "te_102" not in event_ids
        assert "te_103" not in event_ids
        assert "te_speech_104" in event_ids

        nfp = next(e for e in events if e["event_id"] == "te_101")
        assert nfp["time"] == "14:30 CET"
        assert nfp["actual"] == "72K"
        assert nfp["impact"] == "🔴"

        speech = next(e for e in events if e["event_id"] == "te_speech_104")
        assert speech["is_speech"] is True
        assert speech["time"] == "10:50 CET"
        assert speech["impact"] == "🔴"
        assert "Bailey" in speech["speech_note"]



def test_state_manager_macro_events():
    """Test recording and deduplication of published macro events."""
    from newsbox.services.state_service import StateManager
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = f"{tmpdir}/state.json"
        sm = StateManager(state_file=state_file)
        assert not sm.is_macro_event_published("te_123")
        sm.mark_macro_event_published("te_123")
        assert sm.is_macro_event_published("te_123")

        # Persistence check
        sm2 = StateManager(state_file=state_file)
        assert sm2.is_macro_event_published("te_123")
        assert not sm2.is_macro_event_published("te_456")



