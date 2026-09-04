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
    service.settings.session_quiet_windows = "08:50-09:15, 15:20-15:45"

    # Time inside European open (09:00)
    inside_eu_open = datetime(2026, 9, 1, 9, 0, 0)
    assert service.is_in_quiet_window(inside_eu_open) is True

    # Time inside US open (15:30)
    inside_us_open = datetime(2026, 9, 1, 15, 30, 0)
    assert service.is_in_quiet_window(inside_us_open) is True

    # Time outside market open (11:30)
    outside_open = datetime(2026, 9, 1, 11, 30, 0)
    assert service.is_in_quiet_window(outside_open) is False


def test_state_manager(tmp_path):
    """Test StateManager persistence."""
    from newsbox.services.state_service import StateManager
    state_file = tmp_path / "test_state.json"
    mgr = StateManager(state_file=state_file)

    # Set channel and portfolio
    mgr.set_channel("crypto", 123456789)
    assert mgr.get_channel("crypto") == 123456789

    added = mgr.add_portfolio_ticker("NVDA")
    assert "NVDA" in mgr.get_portfolio_tickers()

    # Re-instantiate from same file to test persistence
    mgr2 = StateManager(state_file=state_file)
    assert mgr2.get_channel("crypto") == 123456789
    assert "NVDA" in mgr2.get_portfolio_tickers()

    # Remove
    mgr2.remove_portfolio_ticker("NVDA")
    assert "NVDA" not in mgr2.get_portfolio_tickers()


def test_state_manager_flash_news_migration(tmp_path):
    """Test StateManager automatically migrates legacy 25,55 minute_cron to 5,35."""
    import json
    from newsbox.services.state_service import StateManager

    state_file = tmp_path / "legacy_state.json"
    legacy_data = {
        "channels": {},
        "portfolio_tickers": [],
        "schedules": {
            "flash_news": {"minute_cron": "25,55"}
        }
    }
    state_file.write_text(json.dumps(legacy_data), encoding="utf-8")

    mgr = StateManager(state_file=state_file)
    flash_cfg = mgr.get_schedule("flash_news")
    assert flash_cfg["minute_cron"] == "5,35"

    # Verify persisted to file
    saved_data = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved_data["schedules"]["flash_news"]["minute_cron"] == "5,35"

