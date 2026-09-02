"""Utility helper functions and classes."""

from newsbox.utils.logger import setup_logger
from newsbox.utils.embeds import (
    create_weekly_outlook_embed,
    create_session_advisory_embed,
    create_trader_advisory_embed,
    create_single_asset_embed,
    create_portfolio_embed,
    create_crypto_news_embed,
    create_calendar_embed,
    create_regional_news_embed,
    create_error_embed,
    create_accuracy_embed,
    create_flash_news_embed,
)

__all__ = [
    "setup_logger",
    "create_weekly_outlook_embed",
    "create_session_advisory_embed",
    "create_trader_advisory_embed",
    "create_single_asset_embed",
    "create_portfolio_embed",
    "create_crypto_news_embed",
    "create_calendar_embed",
    "create_regional_news_embed",
    "create_error_embed",
    "create_accuracy_embed",
    "create_flash_news_embed",
]
