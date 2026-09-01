"""Unit tests for Portfolio tracking and quiet windows."""

from datetime import datetime, time
from newsbox.config import parse_portfolio, parse_quiet_windows, Settings
from newsbox.services.news_service import NewsService


def test_parse_portfolio():
    """Test portfolio ticker string parsing."""
    raw = "CDR.WA, PKN.WA, NVDA, TSLA, AAPL"
    parsed = parse_portfolio(raw)
    assert len(parsed) == 5
    assert "CDR.WA" in parsed
    assert "NVDA" in parsed


def test_parse_quiet_windows():
    """Test quiet windows string parsing."""
    raw = "08:50-09:15, 15:20-15:45"
    windows = parse_quiet_windows(raw)
    assert len(windows) == 2
    assert windows[0] == (time(8, 50), time(9, 15))
    assert windows[1] == (time(15, 20), time(15, 45))


def test_is_in_quiet_window():
    """Test session open quiet window detection."""
    service = NewsService()

    # Time inside European open (09:00)
    inside_eu_open = datetime(2026, 9, 1, 9, 0, 0)
    assert service.is_in_quiet_window(inside_eu_open) is True

    # Time inside US open (15:30)
    inside_us_open = datetime(2026, 9, 1, 15, 30, 0)
    assert service.is_in_quiet_window(inside_us_open) is True

    # Time outside market open (11:30)
    outside_open = datetime(2026, 9, 1, 11, 30, 0)
    assert service.is_in_quiet_window(outside_open) is False
