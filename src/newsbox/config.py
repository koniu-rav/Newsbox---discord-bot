"""Application configuration management with environment variable loading, multi-channel routing, and portfolio settings."""

from __future__ import annotations

import os
from datetime import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Default assets mapping
DEFAULT_TICKERS_STR = "DXY=DX-Y.NYB,EUR/USD=EURUSD=X,DAX=^GDAXI,BTC=BTC-USD,GBP/USD=GBPUSD=X,USD/JPY=USDJPY=X"
DEFAULT_PORTFOLIO_STR = "CDR.WA,PKN.WA,NVDA,TSLA,AAPL"
DEFAULT_QUIET_WINDOWS = ""


def parse_tickers(tickers_raw: str) -> Dict[str, str]:
    """Parse comma-separated TICKERS string into a symbol:yahoo_ticker dictionary."""
    if not tickers_raw:
        tickers_raw = DEFAULT_TICKERS_STR
    result = {}
    for item in tickers_raw.split(","):
        item = item.strip()
        if "=" in item:
            name, sym = item.split("=", 1)
            result[name.strip()] = sym.strip()
        elif item:
            result[item] = item
    return result


def parse_portfolio(portfolio_raw: str) -> List[str]:
    """Parse comma-separated portfolio tickers string into a list of clean symbols."""
    if not portfolio_raw:
        return [t.strip() for t in DEFAULT_PORTFOLIO_STR.split(",") if t.strip()]
    return [t.strip() for t in portfolio_raw.split(",") if t.strip()]


def parse_quiet_windows(raw_windows: str) -> List[Tuple[time, time]]:
    """Parse string of time intervals e.g. '08:50-09:15,15:20-15:45' into (start_time, end_time) tuples."""
    results = []
    if not raw_windows:
        raw_windows = DEFAULT_QUIET_WINDOWS
    for interval in raw_windows.split(","):
        interval = interval.strip()
        if "-" in interval:
            start_str, end_str = interval.split("-", 1)
            try:
                sh, sm = map(int, start_str.strip().split(":"))
                eh, em = map(int, end_str.strip().split(":"))
                results.append((time(sh, sm), time(eh, em)))
            except Exception:
                pass
    return results


try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator

    class Settings(BaseSettings):
        """Application settings loaded from environment or .env file."""

        # Discord Bot Tokens & Gateway
        discord_bot_token: str = Field(default="", alias="DISCORD_BOT_TOKEN")
        discord_guild_id: Optional[int] = Field(default=None, alias="DISCORD_GUILD_ID")
        discord_command_prefix: str = Field(default="!", alias="DISCORD_COMMAND_PREFIX")
        vip_role_name: str = Field(default="Newsbox-vip", alias="VIP_ROLE_NAME")

        # Multi-Channel Routing
        discord_macro_channel_id: Optional[int] = Field(default=None, alias="DISCORD_MACRO_CHANNEL_ID")
        discord_calendar_channel_id: Optional[int] = Field(default=None, alias="DISCORD_CALENDAR_CHANNEL_ID")
        discord_news_pl_channel_id: Optional[int] = Field(default=None, alias="DISCORD_NEWS_PL_CHANNEL_ID")
        discord_news_global_channel_id: Optional[int] = Field(default=None, alias="DISCORD_NEWS_GLOBAL_CHANNEL_ID")
        discord_crypto_channel_id: Optional[int] = Field(default=None, alias="DISCORD_CRYPTO_CHANNEL_ID")
        discord_portfolio_channel_id: Optional[int] = Field(default=None, alias="DISCORD_PORTFOLIO_CHANNEL_ID")
        discord_portfolio_news_channel_id: Optional[int] = Field(default=None, alias="DISCORD_PORTFOLIO_NEWS_CHANNEL_ID")
        discord_accuracy_channel_id: Optional[int] = Field(default=None, alias="DISCORD_ACCURACY_CHANNEL_ID")
        discord_macro_alerts_channel_id: Optional[int] = Field(
            default=1545318318204919829, alias="DISCORD_MACRO_ALERTS_CHANNEL_ID"
        )

        # Backward compatibility alias
        discord_briefing_channel_id: Optional[int] = Field(default=None, alias="DISCORD_BRIEFING_CHANNEL_ID")

        @field_validator(
            "discord_guild_id",
            "discord_macro_channel_id",
            "discord_calendar_channel_id",
            "discord_news_pl_channel_id",
            "discord_news_global_channel_id",
            "discord_crypto_channel_id",
            "discord_portfolio_channel_id",
            "discord_portfolio_news_channel_id",
            "discord_accuracy_channel_id",
            "discord_macro_alerts_channel_id",
            "discord_briefing_channel_id",
            mode="before",
        )
        @classmethod
        def empty_str_to_none(cls, v: Any) -> Optional[int]:
            if v == "" or v is None:
                return None
            if isinstance(v, str) and v.strip().isdigit():
                return int(v.strip())
            return v

        # Google Gemini AI Configuration
        gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
        gemini_model: str = Field(default="gemini-3.7-flash", alias="GEMINI_MODEL")
        prompts_dir: str = Field(default="prompts", alias="PROMPTS_DIR")

        # Configurable Asset Tickers
        tickers_config: str = Field(default=DEFAULT_TICKERS_STR, alias="TICKERS")

        # Configurable Portfolio Watchlist
        portfolio_config: str = Field(default=DEFAULT_PORTFOLIO_STR, alias="PORTFOLIO_TICKERS")

        # Market Open Quiet Windows (HH:MM-HH:MM comma-separated)
        session_quiet_windows: str = Field(default=DEFAULT_QUIET_WINDOWS, alias="SESSION_QUIET_WINDOWS")

        # Schedule Configuration
        calendar_time: str = Field(default="07:00", alias="CALENDAR_TIME")
        briefing_time: str = Field(default="08:00", alias="BRIEFING_TIME")
        accuracy_time: str = Field(default="12:30", alias="ACCURACY_TIME")
        briefing_timezone: str = Field(default="Europe/Warsaw", alias="BRIEFING_TIMEZONE")

        # News Stream & Polling Settings
        news_stream_enabled: bool = Field(default=False, alias="NEWS_STREAM_ENABLED")
        news_poll_interval_minutes: int = Field(default=15, alias="NEWS_POLL_INTERVAL_MINUTES")

        # Logging & Environment
        log_level: str = Field(default="INFO", alias="LOG_LEVEL")
        environment: str = Field(default="development", alias="ENVIRONMENT")

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
        )

        @property
        def tickers(self) -> Dict[str, str]:
            """Parsed dictionary of tickers."""
            return parse_tickers(self.tickers_config)

        @property
        def portfolio_tickers(self) -> List[str]:
            """Parsed list of portfolio tickers."""
            return parse_portfolio(self.portfolio_config)

        @property
        def quiet_windows(self) -> List[Tuple[time, time]]:
            """Parsed list of session quiet windows (start_time, end_time)."""
            return parse_quiet_windows(self.session_quiet_windows)

        @property
        def command_prefix(self) -> str:
            """Command prefix alias."""
            return self.discord_command_prefix

        @property
        def bot_token(self) -> str:
            """Bot token alias."""
            return self.discord_bot_token

        @property
        def guild_id(self) -> Optional[int]:
            """Guild ID alias."""
            return self.discord_guild_id

        @property
        def macro_channel_id(self) -> Optional[int]:
            """Resolved macro briefing channel ID."""
            return self.discord_macro_channel_id or self.discord_briefing_channel_id

except ImportError:
    class Settings:  # type: ignore
        """Fallback settings class using standard os.environ."""

        def __init__(self) -> None:
            self.discord_bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
            guild_id = os.getenv("DISCORD_GUILD_ID")
            self.discord_guild_id: Optional[int] = int(guild_id) if guild_id and guild_id.isdigit() else None
            self.discord_command_prefix: str = os.getenv("DISCORD_COMMAND_PREFIX", "!")
            self.vip_role_name: str = os.getenv("VIP_ROLE_NAME", "Newsbox-vip")

            # Channels
            macro_ch = os.getenv("DISCORD_MACRO_CHANNEL_ID") or os.getenv("DISCORD_BRIEFING_CHANNEL_ID")
            self.discord_macro_channel_id: Optional[int] = int(macro_ch) if macro_ch and macro_ch.isdigit() else None
            self.discord_briefing_channel_id = self.discord_macro_channel_id

            cal_ch = os.getenv("DISCORD_CALENDAR_CHANNEL_ID")
            self.discord_calendar_channel_id: Optional[int] = int(cal_ch) if cal_ch and cal_ch.isdigit() else None

            pl_ch = os.getenv("DISCORD_NEWS_PL_CHANNEL_ID")
            self.discord_news_pl_channel_id: Optional[int] = int(pl_ch) if pl_ch and pl_ch.isdigit() else None

            glob_ch = os.getenv("DISCORD_NEWS_GLOBAL_CHANNEL_ID")
            self.discord_news_global_channel_id: Optional[int] = (
                int(glob_ch) if glob_ch and glob_ch.isdigit() else None
            )

            crypto_ch = os.getenv("DISCORD_CRYPTO_CHANNEL_ID")
            self.discord_crypto_channel_id: Optional[int] = (
                int(crypto_ch) if crypto_ch and crypto_ch.isdigit() else None
            )

            port_ch = os.getenv("DISCORD_PORTFOLIO_CHANNEL_ID")
            self.discord_portfolio_channel_id: Optional[int] = (
                int(port_ch) if port_ch and port_ch.isdigit() else None
            )

            port_news_ch = os.getenv("DISCORD_PORTFOLIO_NEWS_CHANNEL_ID")
            self.discord_portfolio_news_channel_id: Optional[int] = (
                int(port_news_ch) if port_news_ch and port_news_ch.isdigit() else None
            )

            macro_alerts_ch = os.getenv("DISCORD_MACRO_ALERTS_CHANNEL_ID", "1545318318204919829")
            self.discord_macro_alerts_channel_id: Optional[int] = (
                int(macro_alerts_ch) if macro_alerts_ch and macro_alerts_ch.isdigit() else None
            )

            # Gemini & Prompts
            self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
            self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
            self.prompts_dir: str = os.getenv("PROMPTS_DIR", "prompts")

            # Tickers & Portfolio
            self.tickers_config: str = os.getenv("TICKERS", DEFAULT_TICKERS_STR)
            self.portfolio_config: str = os.getenv("PORTFOLIO_TICKERS", DEFAULT_PORTFOLIO_STR)
            self.session_quiet_windows: str = os.getenv("SESSION_QUIET_WINDOWS", DEFAULT_QUIET_WINDOWS)

            # Schedule
            self.calendar_time: str = os.getenv("CALENDAR_TIME", "07:00")
            self.briefing_time: str = os.getenv("BRIEFING_TIME", "08:00")
            self.accuracy_time: str = os.getenv("ACCURACY_TIME", "12:30")
            self.briefing_timezone: str = os.getenv("BRIEFING_TIMEZONE", "Europe/Warsaw")

            # News stream
            self.news_stream_enabled: bool = os.getenv("NEWS_STREAM_ENABLED", "false").lower() == "true"
            self.news_poll_interval_minutes: int = int(os.getenv("NEWS_POLL_INTERVAL_MINUTES", "15"))

            # Log level
            self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
            self.environment: str = os.getenv("ENVIRONMENT", "development")

        @property
        def tickers(self) -> Dict[str, str]:
            """Parsed dictionary of tickers."""
            return parse_tickers(self.tickers_config)

        @property
        def portfolio_tickers(self) -> List[str]:
            """Parsed list of portfolio tickers."""
            return parse_portfolio(self.portfolio_config)

        @property
        def quiet_windows(self) -> List[Tuple[time, time]]:
            """Parsed list of session quiet windows (start_time, end_time)."""
            return parse_quiet_windows(self.session_quiet_windows)

        @property
        def command_prefix(self) -> str:
            """Command prefix alias."""
            return self.discord_command_prefix

        @property
        def bot_token(self) -> str:
            """Bot token alias."""
            return self.discord_bot_token

        @property
        def guild_id(self) -> Optional[int]:
            """Guild ID alias."""
            return self.discord_guild_id

        @property
        def macro_channel_id(self) -> Optional[int]:
            """Resolved macro briefing channel ID."""
            return self.discord_macro_channel_id or self.discord_briefing_channel_id


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton settings instance."""
    return Settings()
