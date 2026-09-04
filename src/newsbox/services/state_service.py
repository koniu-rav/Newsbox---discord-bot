"""Persistent state manager for Discord bot channel routing and portfolio holdings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_STATE_FILE = Path("data/state.json")

DEFAULT_SCHEDULES: Dict[str, Dict[str, Any]] = {
    "weekly_outlook": {"day_of_week": "sun", "hour": 10, "minute": 0},
    "calendar": {"day_of_week": "mon-fri", "hour": 7, "minute": 0},
    "london": {"day_of_week": "mon-fri", "hour": 7, "minute": 0},
    "newyork": {"day_of_week": "mon-fri", "hour": 13, "minute": 30},
    "asia": {"day_of_week": "sun,mon-thu", "hour": 23, "minute": 0},
    "accuracy": {"day_of_week": "sat", "hour": 12, "minute": 0},
    "portfolio": {"day_of_week": "sun", "hour": 18, "minute": 0},
    "portfolio_news": {"day_of_week": "*", "hour": 14, "minute": 0},
    "flash_news": {"minute_cron": "25,55"},
}


class StateManager:
    """Manages persistent JSON storage for runtime changes (channels, portfolio watchlist, schedules)."""

    def __init__(self, state_file: Path | str = DEFAULT_STATE_FILE) -> None:
        self.state_file = Path(state_file)
        self.settings = get_settings()
        self._state: Dict[str, Any] = {
            "channels": {},
            "portfolio_tickers": [],
            "schedules": {},
        }
        self.load_state()

    def load_state(self) -> None:
        """Load state from JSON file or initialize with defaults from .env."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self._state["channels"] = data.get("channels", {})
                self._state["portfolio_tickers"] = data.get("portfolio_tickers", [])
                self._state["schedules"] = data.get("schedules", {})
                self._state["published_macro_events"] = data.get("published_macro_events", [])

                # Merge default schedules if any are missing
                modified = False
                for k, v in DEFAULT_SCHEDULES.items():
                    if k not in self._state["schedules"]:
                        self._state["schedules"][k] = dict(v)
                        modified = True

                if "macro_alerts" not in self._state["channels"]:
                    self._state["channels"]["macro_alerts"] = self.settings.discord_macro_alerts_channel_id
                    modified = True

                if modified:
                    self.save_state()

                logger.info("Loaded persistent state from %s", self.state_file)
                return
            except Exception as e:
                logger.error("Failed to parse state file %s: %s. Using environment defaults.", self.state_file, e)

        # Fallback initialization from settings (.env)
        self._state["channels"] = {
            "macro": self.settings.macro_channel_id,
            "calendar": self.settings.discord_calendar_channel_id,
            "news_pl": self.settings.discord_news_pl_channel_id,
            "news_global": self.settings.discord_news_global_channel_id,
            "crypto": self.settings.discord_crypto_channel_id,
            "portfolio": self.settings.discord_portfolio_channel_id,
            "portfolio_news": self.settings.discord_portfolio_news_channel_id,
            "accuracy": self.settings.discord_accuracy_channel_id,
            "macro_alerts": self.settings.discord_macro_alerts_channel_id,
        }
        self._state["portfolio_tickers"] = list(self.settings.portfolio_tickers)
        self._state["schedules"] = {k: dict(v) for k, v in DEFAULT_SCHEDULES.items()}
        self._state["published_macro_events"] = []
        self.save_state()

    def save_state(self) -> None:
        """Persist current state to JSON file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(
                json.dumps(self._state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.debug("Persistent state saved to %s", self.state_file)
        except Exception as e:
            logger.error("Failed to write persistent state to %s: %s", self.state_file, e)

    # ---------------- Channel Management ---------------- #

    def set_channel(self, channel_type: str, channel_id: int) -> None:
        """Assign and save channel ID for a specific notification type."""
        c_type = channel_type.lower().strip()
        self._state["channels"][c_type] = channel_id
        # Also sync in-memory settings for compatibility
        if c_type in ["macro", "briefing"]:
            self.settings.discord_macro_channel_id = channel_id
            self.settings.discord_briefing_channel_id = channel_id
        elif c_type in ["calendar", "kalendarz"]:
            self.settings.discord_calendar_channel_id = channel_id
        elif c_type in ["news_pl", "pl"]:
            self.settings.discord_news_pl_channel_id = channel_id
        elif c_type in ["news_global", "global", "us"]:
            self.settings.discord_news_global_channel_id = channel_id
        elif c_type in ["crypto", "krypto"]:
            self.settings.discord_crypto_channel_id = channel_id
        elif c_type in ["portfolio", "portfel"]:
            self.settings.discord_portfolio_channel_id = channel_id
        elif c_type in ["portfolio_news", "portfel_news"]:
            self.settings.discord_portfolio_news_channel_id = channel_id
        elif c_type in ["accuracy", "skutecznosc", "stats", "wyniki"]:
            self.settings.discord_accuracy_channel_id = channel_id
        elif c_type in ["macro_alerts", "alerts", "odczyty", "dane_macro", "macro_dane", "live_macro"]:
            self.settings.discord_macro_alerts_channel_id = channel_id

        self.save_state()

    def get_channel(self, channel_type: str) -> Optional[int]:
        """Get persisted channel ID by type."""
        return self._state["channels"].get(channel_type.lower().strip())

    def get_all_channels(self) -> Dict[str, Optional[int]]:
        """Return copy of all mapped channels."""
        return dict(self._state.get("channels", {}))

    # ---------------- Real-Time Macro Events Tracking ---------------- #

    def is_macro_event_published(self, event_id: str) -> bool:
        """Check if a macro event has already been published/alerted."""
        events = self._state.get("published_macro_events", [])
        return event_id in events

    def mark_macro_event_published(self, event_id: str) -> None:
        """Record macro event ID to avoid duplicate alerts."""
        events = self._state.setdefault("published_macro_events", [])
        if event_id not in events:
            events.append(event_id)
            # Retain last 300 event IDs to prevent unbounded state growth
            if len(events) > 300:
                self._state["published_macro_events"] = events[-300:]
            self.save_state()

    def get_published_macro_events(self) -> List[str]:
        """Get list of published macro event IDs."""
        return list(self._state.get("published_macro_events", []))

    # ---------------- Schedule Management ---------------- #

    def get_schedule(self, schedule_type: str) -> Dict[str, Any]:
        """Get schedule configuration for a given job type."""
        s_type = schedule_type.lower().strip()
        schedules = self._state.get("schedules", {})
        if s_type in schedules:
            return dict(schedules[s_type])
        return dict(DEFAULT_SCHEDULES.get(s_type, {}))

    def set_schedule(self, schedule_type: str, schedule_data: Dict[str, Any]) -> None:
        """Assign and save schedule parameters for a specific job."""
        s_type = schedule_type.lower().strip()
        if "schedules" not in self._state:
            self._state["schedules"] = {}
        self._state["schedules"][s_type] = dict(schedule_data)
        self.save_state()
        logger.info("Schedule updated & persisted: %s -> %s", s_type, schedule_data)

    def get_all_schedules(self) -> Dict[str, Dict[str, Any]]:
        """Return all persisted schedules with defaults filled in."""
        current = dict(self._state.get("schedules", {}))
        for k, v in DEFAULT_SCHEDULES.items():
            if k not in current:
                current[k] = dict(v)
        return current

    # ---------------- Portfolio Management ---------------- #

    def get_portfolio_tickers(self) -> List[str]:
        """Get active list of portfolio tickers."""
        return list(self._state.get("portfolio_tickers", []))

    def add_portfolio_ticker(self, ticker: str) -> bool:
        """Add ticker to persistent portfolio watchlist. Returns True if added."""
        clean = ticker.strip().upper()
        current = self.get_portfolio_tickers()
        if clean in [t.upper() for t in current]:
            return False
        current.append(clean)
        self._state["portfolio_tickers"] = current
        self.save_state()
        return True

    def remove_portfolio_ticker(self, ticker: str) -> bool:
        """Remove ticker from persistent portfolio watchlist. Returns True if removed."""
        clean = ticker.strip().upper()
        current = self.get_portfolio_tickers()
        matched = [t for t in current if t.upper() == clean]
        if not matched:
            return False
        for m in matched:
            current.remove(m)
        self._state["portfolio_tickers"] = current
        self.save_state()
        return True


# Global singleton instance
_state_manager_instance: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Return singleton StateManager instance."""
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateManager()
    return _state_manager_instance
