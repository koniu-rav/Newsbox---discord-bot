"""Discord Embed message builders for trader briefings, single-asset views, portfolio tracking, and crypto feeds."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import discord


def create_trader_advisory_embed(
    date_str: str,
    market_data: Dict[str, Any],
    advisory_text: str,
) -> discord.Embed:
    """Build the primary 8:00 AM Trader Advisory embed (FX Majors, DXY, DAX)."""
    embed = discord.Embed(
        title=f"🌅 Raport Makro & FX/DAX Advisory — {date_str}",
        description=advisory_text,
        color=0x1F8B4C,  # Emerald Green
        timestamp=datetime.utcnow(),
    )

    market_lines = []
    for symbol, info in market_data.items():
        price = info.get("price", "N/A")
        change = info.get("change_pct", "0.00%")
        direction = info.get("direction", "⚪")
        market_lines.append(f"**{symbol}**: `{price}` ({direction} {change})")

    if market_lines:
        embed.add_field(
            name="📊 Notowania (FX Majors | DXY | DAX | BTC)",
            value="\n".join(market_lines),
            inline=False,
        )

    embed.set_footer(
        text="Newsbox Trading Advisory • Gemini AI",
        icon_url="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/trending_up/materialicons/48dp/2x/baseline_trending_up_black_48dp.png",
    )
    return embed


def create_single_asset_embed(
    symbol: str,
    asset_data: Dict[str, Any],
    advisory_text: str,
) -> discord.Embed:
    """Build targeted embed for a single financial asset (e.g. DAX, BTC, TSLA)."""
    price = asset_data.get("price", "N/A")
    change = asset_data.get("change_pct", "0.00%")
    direction = asset_data.get("direction", "⚪")
    color = 0x2ECC71 if "+" in str(change) or not str(change).startswith("-") else 0xE74C3C

    embed = discord.Embed(
        title=f"🎯 Raport dla Waloru: {symbol.upper()}",
        description=advisory_text,
        color=color,
        timestamp=datetime.utcnow(),
    )

    embed.add_field(
        name="📈 Aktualna Cena & Zmiana",
        value=f"`{price}` ({direction} **{change}**)",
        inline=True,
    )
    if asset_data.get("ticker"):
        embed.add_field(
            name="🏷️ Ticker Źródłowy",
            value=f"`{asset_data.get('ticker')}`",
            inline=True,
        )

    embed.set_footer(text="Newsbox Single Asset Advisory")
    return embed


def create_portfolio_embed(
    portfolio_data: Dict[str, Any],
    advisory_text: str,
    portfolio_news: List[Dict[str, Any]],
) -> discord.Embed:
    """Build user investment portfolio overview embed."""
    embed = discord.Embed(
        title="💼 Twój Portfel Inwestycyjny & Wiadomości Spółek",
        description=advisory_text,
        color=0x9B59B6,  # Amethyst Purple
        timestamp=datetime.utcnow(),
    )

    # Quotes
    quote_lines = []
    for sym, info in portfolio_data.items():
        price = info.get("price", "N/A")
        change = info.get("change_pct", "0.00%")
        direction = info.get("direction", "⚪")
        quote_lines.append(f"**{sym}**: `{price}` ({direction} {change})")

    if quote_lines:
        embed.add_field(
            name="📊 Notowania Twoich Spółek",
            value="\n".join(quote_lines),
            inline=False,
        )

    # Headlines
    news_lines = []
    for h in portfolio_news[:5]:
        title = h.get("title", "")
        url = h.get("url", "")
        source = h.get("source", "News")
        match = h.get("matched_symbol", "")
        badge = f"`[{match}]` " if match else ""
        if url:
            news_lines.append(f"• {badge}[{title}]({url}) *({source})*")
        else:
            news_lines.append(f"• {badge}{title} *({source})*")

    if news_lines:
        embed.add_field(
            name="📰 Ostatnie Komunikaty dla Twoich Spółek",
            value="\n".join(news_lines),
            inline=False,
        )

    embed.set_footer(text="Newsbox Portfolio Tracker")
    return embed


def create_crypto_news_embed(
    headlines: List[Dict[str, Any]],
    summary_text: Optional[str] = None,
) -> discord.Embed:
    """Build dedicated Crypto / Blockchain news embed."""
    embed = discord.Embed(
        title="⚡ Crypto & Blockchain Pulse (#crypto-chat)",
        color=0xF39C12,  # Bitcoin Gold / Orange
        timestamp=datetime.utcnow(),
    )

    if summary_text:
        embed.description = summary_text

    items_text = []
    for h in headlines[:6]:
        item_title = h.get("title", "")
        url = h.get("url", "")
        source = h.get("source", "Crypto")
        if url:
            items_text.append(f"• [{item_title}]({url}) *({source})*")
        else:
            items_text.append(f"• {item_title} *({source})*")

    if items_text:
        embed.add_field(
            name="🪙 Najnowsze Wydarzenia Krypto",
            value="\n".join(items_text),
            inline=False,
        )

    embed.set_footer(text="Newsbox Crypto Feed")
    return embed


def create_calendar_embed(
    date_str: str,
    calendar_events: List[Dict[str, Any]],
    calendar_advice: Optional[str] = None,
) -> discord.Embed:
    """Build the Economic Calendar & Risk Assessment embed."""
    embed = discord.Embed(
        title=f"📅 Kalendarz Ekonomiczny & Ryzyka Sesji — {date_str}",
        color=0xE67E22,  # Orange
        timestamp=datetime.utcnow(),
    )

    event_lines = []
    for event in calendar_events[:8]:
        time = event.get("time", "")
        currency = event.get("currency", "")
        title = event.get("title", "")
        impact = event.get("impact", "🟡")
        event_lines.append(f"{impact} `{time}` **[{currency}]** {title}")

    embed.add_field(
        name="⏰ Zaplanowane Publikacje Dnia",
        value="\n".join(event_lines) if event_lines else "Brak kluczowych wydarzeń o wysokiej zmienności.",
        inline=False,
    )

    if calendar_advice:
        embed.add_field(
            name="💡 Zalecenia AI dla Tradera",
            value=calendar_advice,
            inline=False,
        )

    embed.set_footer(text="Newsbox Economic Calendar")
    return embed


def create_regional_news_embed(
    region: str,
    headlines: List[Dict[str, Any]],
    summary_text: Optional[str] = None,
) -> discord.Embed:
    """Build regional news digest embed (PL, USA, EU, GLOBAL)."""
    flags = {
        "PL": "🇵🇱 Polska / GPW & Biznes",
        "USA": "🇺🇸 Rynki USA & Gospodarka",
        "EU": "🇪🇺 Strefa Euro & EBC",
        "GLOBAL": "🌐 Rynki Globalne & Surowce",
        "CRYPTO": "🪙 Świat Kryptowalut & Web3",
        "ALL": "📰 Przegląd Wiadomości Ze Świata (PL, EU, USA)",
    }
    title = flags.get(region.upper(), f"📰 Wiadomości: {region}")

    embed = discord.Embed(
        title=title,
        color=0x3498DB,  # Blue
        timestamp=datetime.utcnow(),
    )

    if summary_text:
        embed.description = summary_text

    items_text = []
    for h in headlines[:6]:
        item_title = h.get("title", "")
        url = h.get("url", "")
        source = h.get("source", "News")
        reg = h.get("region", "")
        reg_badge = f"`[{reg}]` " if reg and region.upper() == "ALL" else ""
        if url:
            items_text.append(f"• {reg_badge}[{item_title}]({url}) *({source})*")
        else:
            items_text.append(f"• {reg_badge}{item_title} *({source})*")

    if items_text:
        embed.add_field(
            name="🔥 Najważniejsze Nagłówki",
            value="\n".join(items_text),
            inline=False,
        )

    embed.set_footer(text="Newsbox Live Feed")
    return embed


def create_error_embed(title: str, description: str) -> discord.Embed:
    """Build standardized error notification embed."""
    embed = discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=0xE74C3C,  # Red
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text="Newsbox Error Notification")
    return embed
