"""Discord Embed message builders with strict character limits and we.trade community branding."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import discord

MAX_FIELD_LENGTH = 1000
MAX_DESCRIPTION_LENGTH = 4000
BRAND_FOOTER = "Newsbox by we.trade • Społeczność Inwestorów & Traderów"


def truncate(text: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """Safely truncate text to avoid Discord 1024 field / 4096 description limit."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def create_trader_advisory_embed(
    date_str: str,
    market_data: Dict[str, Any],
    advisory_text: str,
) -> discord.Embed:
    """Build the primary 8:00 AM Trader Advisory embed (London, New York, Asia sessions)."""
    embed = discord.Embed(
        title=f"🌅 Briefing Makro (Londyn • Nowy Jork • Azja) — {date_str}",
        description=truncate(advisory_text, MAX_DESCRIPTION_LENGTH),
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
            value=truncate("\n".join(market_lines), MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
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
        description=truncate(advisory_text, MAX_DESCRIPTION_LENGTH),
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

    embed.set_footer(text=BRAND_FOOTER)
    return embed


def create_portfolio_embed(
    portfolio_data: Dict[str, Any],
    advisory_text: str,
    portfolio_news: List[Dict[str, Any]],
) -> discord.Embed:
    """Build user investment portfolio overview embed."""
    embed = discord.Embed(
        title="💼 Twój Portfel Inwestycyjny & Wiadomości Spółek",
        description=truncate(advisory_text, MAX_DESCRIPTION_LENGTH),
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
            value=truncate("\n".join(quote_lines), MAX_FIELD_LENGTH),
            inline=False,
        )

    # Headlines
    news_lines = []
    for h in portfolio_news[:5]:
        title = truncate(h.get("title", ""), 120)
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
            value=truncate("\n".join(news_lines), MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
    return embed


def create_crypto_news_embed(
    headlines: List[Dict[str, Any]],
    summary_text: Optional[str] = None,
) -> discord.Embed:
    """Build dedicated Crypto / Blockchain news embed."""
    embed = discord.Embed(
        title="⚡ Crypto & Blockchain Pulse (#crypto-chat)",
        description=truncate(summary_text or "", MAX_DESCRIPTION_LENGTH) if summary_text else None,
        color=0xF39C12,  # Bitcoin Gold / Orange
        timestamp=datetime.utcnow(),
    )

    items_text = []
    for h in headlines[:5]:
        item_title = truncate(h.get("title", ""), 120)
        url = h.get("url", "")
        source = h.get("source", "Crypto")
        if url:
            items_text.append(f"• [{item_title}]({url}) *({source})*")
        else:
            items_text.append(f"• {item_title} *({source})*")

    if items_text:
        embed.add_field(
            name="🪙 Najnowsze Wydarzenia Krypto",
            value=truncate("\n".join(items_text), MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
    return embed


def create_calendar_embed(
    date_str: str,
    calendar_events: List[Dict[str, Any]],
    calendar_advice: Optional[str] = None,
) -> discord.Embed:
    """Build the Economic Calendar & Risk Assessment embed (24h window: 07:00 today to 07:00 tomorrow)."""
    embed = discord.Embed(
        title=f"📅 24-godzinny Kalendarz Makro (07:00 ➡️ 07:00) — {date_str}",
        color=0xE67E22,  # Orange
        timestamp=datetime.utcnow(),
    )

    event_lines = []
    for event in calendar_events[:12]:
        time = event.get("time", "")
        currency = event.get("currency", "")
        title = truncate(event.get("title", ""), 85)
        impact = event.get("impact", "🟡")
        event_lines.append(f"{impact} `{time}` **[{currency}]** {title}")

    embed.add_field(
        name="⏰ Publikacje Dnia & Nocy (07:00 Dzisiaj ➡️ 07:00 Jutro)",
        value=truncate("\n".join(event_lines), MAX_FIELD_LENGTH) if event_lines else "Brak istotnych publikacji w tym oknie czasowym.",
        inline=False,
    )

    if calendar_advice:
        embed.add_field(
            name="💡 Zalecenia AI dla Tradera (Londyn • Nowy Jork • Azja)",
            value=truncate(calendar_advice, MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
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
        description=truncate(summary_text or "", MAX_DESCRIPTION_LENGTH) if summary_text else None,
        color=0x3498DB,  # Blue
        timestamp=datetime.utcnow(),
    )

    items_text = []
    for h in headlines[:5]:
        item_title = truncate(h.get("title", ""), 120)
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
            value=truncate("\n".join(items_text), MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
    return embed


def create_error_embed(title: str, description: str) -> discord.Embed:
    """Build standardized error notification embed."""
    embed = discord.Embed(
        title=f"⚠️ {truncate(title, 200)}",
        description=truncate(description, MAX_DESCRIPTION_LENGTH),
        color=0xE74C3C,  # Red
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=BRAND_FOOTER)
    return embed


def create_accuracy_embed(
    evaluation_result: Dict[str, Any],
    global_stats: Dict[str, Any],
) -> discord.Embed:
    """Build the 12:30 PM Accuracy & Performance Tracker embed."""
    score = evaluation_result.get("score", 0)
    status = evaluation_result.get("status", "neutralna")
    eval_date = evaluation_result.get("date", "Wczoraj")
    breakdown = evaluation_result.get("breakdown", "")
    conclusions = evaluation_result.get("conclusions", "")

    # Status badges and color
    if score > 75:
        badge = "🎯 **Analiza udana**"
        color = 0x2ECC71  # Emerald Green
    elif score > 25:
        badge = "⚖️ **Analiza neutralna**"
        color = 0xF39C12  # Amber/Yellow
    else:
        badge = "❌ **Analiza nieudana**"
        color = 0xE74C3C  # Crimson Red

    embed = discord.Embed(
        title="📊 Raport Skuteczności Briefingu (Ewaluacja 12:30)",
        color=color,
        timestamp=datetime.utcnow(),
    )

    # 1. Globalny Counter
    total = global_stats.get("total", 0)
    successful = global_stats.get("successful", 0)
    neutral = global_stats.get("neutral", 0)
    failed = global_stats.get("failed", 0)
    avg_score = global_stats.get("average_score", 0.0)
    win_rate = global_stats.get("win_rate", 0.0)

    counter_value = (
        f"• **Skuteczność (Win-Rate)**: `{win_rate}%` (Średnia: `{avg_score}/100`)\n"
        f"• **Łącznie analiz**: `{total}`\n"
        f"• **Rozkład**: 🎯 Udane: `{successful}` | ⚖️ Neutralne: `{neutral}` | ❌ Nieudane: `{failed}`"
    )
    embed.add_field(
        name="🏆 Globalny Counter Skuteczności",
        value=counter_value,
        inline=False,
    )

    # 2. Wynik wczorajszego briefu
    eval_value = (
        f"• **Data analizy**: `{eval_date}`\n"
        f"• **Wynik punktowy**: `{score}/100` ({badge})\n"
        f"• **Rozbicie na rynki**:\n{breakdown}"
    )
    embed.add_field(
        name="📅 Wynik Ostatniego Briefu",
        value=truncate(eval_value, MAX_FIELD_LENGTH),
        inline=False,
    )

    # 3. Wnioski
    if conclusions:
        embed.add_field(
            name="💡 Wnioski i Lekcje Rynkowe",
            value=truncate(conclusions, MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
    return embed
