"""Pytest fixtures and configuration."""

import pytest
from unittest.mock import MagicMock
from newsbox.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Provide isolated mock settings."""
    settings = Settings()
    settings.discord_bot_token = "mock_test_token"
    settings.discord_briefing_channel_id = 123456789
    settings.gemini_api_key = "mock_gemini_key"
    settings.gemini_model = "gemini-1.5-flash"
    settings.briefing_time = "08:00"
    settings.briefing_timezone = "UTC"
    return settings


@pytest.fixture
def sample_market_data():
    """Sample market snapshot for tests."""
    return {
        "DXY": {"price": "104.25", "change_pct": "+0.15%", "raw_price": 104.25},
        "EUR/USD": {"price": "1.0845", "change_pct": "-0.12%", "raw_price": 1.0845},
        "DAX": {"price": "18,420.50", "change_pct": "+0.35%", "raw_price": 18420.50},
        "BTC": {"price": "67,500.00", "change_pct": "+1.85%", "raw_price": 67500.00},
    }


@pytest.fixture
def sample_calendar_events():
    """Sample economic calendar events for tests."""
    return [
        {
            "time": "14:30 CET",
            "currency": "USD",
            "title": "Core PCE Price Index m/m",
            "impact": "🔴",
        },
        {
            "time": "15:45 CET",
            "currency": "USD",
            "title": "Flash Manufacturing PMI",
            "impact": "🟡",
        },
    ]


@pytest.fixture
def sample_headlines():
    """Sample news headlines for tests."""
    return [
        {
            "title": "Fed Holds Rates Steady as Inflation Cools",
            "url": "https://example.com/fed",
            "source": "Macro News",
        },
        {
            "title": "ECB Evaluates Balance Sheet Reductions",
            "url": "https://example.com/ecb",
            "source": "Europe Finance",
        },
    ]

