"""Application configuration management with environment variable loading and multi-channel routing."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

# Default assets mapping
DEFAULT_TICKERS_STR = "DXY=DX-Y.NYB,EUR/USD=EURUSD=X,DAX=^GDAXI,BTC=BTC-USD"


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


try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator

    class Settings(BaseSettings):
        """Application settings loaded from environment or .env file."""

        # Discord Bot Tokens & Gateway
        discord_bot_token: str = Field(default="", alias="DISCORD_BOT_TOKEN")
        discord_guild_id: Optional[int] = Field(default=None, alias="DISCORD_GUILD_ID")
        discord_command_prefix: str = Field(default="!", alias="DISCORD_COMMAND_PREFIX")

        # Multi-Channel Routing (IDs of specific target channels)
        discord_macro_channel_id: Optional[int] = Field(default=None, alias="DISCORD_MACRO_CHANNEL_ID")
        discord_calendar_channel_id: Optional[int] = Field(default=None, alias="DISCORD_CALENDAR_CHANNEL_ID")
        discord_news_pl_channel_id: Optional[int] = Field(default=None, alias="DISCORD_NEWS_PL_CHANNEL_ID")
        discord_news_global_channel_id: Optional[int] = Field(default=None, alias="DISCORD_NEWS_GLOBAL_CHANNEL_ID")

        # Backward compatibility alias
        discord_briefing_channel_id: Optional[int] = Field(default=None, alias="DISCORD_BRIEFING_CHANNEL_ID")

        @field_validator(
            "discord_guild_id",
            "discord_macro_channel_id",
            "discord_calendar_channel_id",
            "discord_news_pl_channel_id",
            "discord_news_global_channel_id",
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
        gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
        prompts_dir: str = Field(default="prompts", alias="PROMPTS_DIR")

        # Configurable Asset Tickers
        tickers_config: str = Field(default=DEFAULT_TICKERS_STR, alias="TICKERS")

        # Schedule Configuration
        briefing_time: str = Field(default="08:00", alias="BRIEFING_TIME")
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

            # Gemini & Prompts
            self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
            self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            self.prompts_dir: str = os.getenv("PROMPTS_DIR", "prompts")

            # Tickers
            self.tickers_config: str = os.getenv("TICKERS", DEFAULT_TICKERS_STR)

            # Schedule
            self.briefing_time: str = os.getenv("BRIEFING_TIME", "08:00")
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
        def macro_channel_id(self) -> Optional[int]:
            """Resolved macro briefing channel ID."""
            return self.discord_macro_channel_id or self.discord_briefing_channel_id


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton settings instance."""
    return Settings()
