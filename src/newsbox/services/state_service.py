"""Persistent state manager for Discord bot channel routing and portfolio holdings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_STATE_FILE = Path("data/state.json")


class StateManager:
    """Manages persistent JSON storage for runtime changes (channels, portfolio watchlist)."""

    def __init__(self, state_file: Path | str = DEFAULT_STATE_FILE) -> None:
        self.state_file = Path(state_file)
        self.settings = get_settings()
        self._state: Dict[str, Any] = {
            "channels": {},
            "portfolio_tickers": [],
        }
        self.load_state()

    def load_state(self) -> None:
        """Load state from JSON file or initialize with defaults from .env."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self._state["channels"] = data.get("channels", {})
                self._state["portfolio_tickers"] = data.get("portfolio_tickers", [])
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
        }
        self._state["portfolio_tickers"] = list(self.settings.portfolio_tickers)
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

        self.save_state()

    def get_channel(self, channel_type: str) -> Optional[int]:
        """Get persisted channel ID by type."""
        return self._state["channels"].get(channel_type.lower().strip())

    def get_all_channels(self) -> Dict[str, Optional[int]]:
        """Return copy of all mapped channels."""
        return dict(self._state.get("channels", {}))

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
