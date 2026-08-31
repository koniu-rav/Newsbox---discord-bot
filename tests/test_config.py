"""Unit tests for configuration loading and ticker parsing."""

from newsbox.config import get_settings, parse_tickers, Settings


def test_parse_tickers():
    """Test custom ticker string parsing."""
    raw = "DXY=DX-Y.NYB, EUR/USD=EURUSD=X, DAX=^GDAXI, BTC=BTC-USD, WIG20=WIG20.WA"
    parsed = parse_tickers(raw)

    assert "DXY" in parsed
    assert parsed["DXY"] == "DX-Y.NYB"
    assert parsed["EUR/USD"] == "EURUSD=X"
    assert parsed["DAX"] == "^GDAXI"
    assert parsed["BTC"] == "BTC-USD"
    assert parsed["WIG20"] == "WIG20.WA"


def test_default_settings():
    """Test default settings and properties."""
    settings = Settings()
    assert settings.briefing_time == "08:00"
    assert "DXY" in settings.tickers
    assert "BTC" in settings.tickers
    assert settings.prompts_dir == "prompts"


def test_singleton_get_settings():
    """Test cached singleton settings."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
