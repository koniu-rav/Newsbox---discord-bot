"""Discord Embed message builders for trader briefings, calendar alerts, and regional news."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import discord


def create_trader_advisory_embed(
    date_str: str,
    market_data: Dict[str, Any],
    advisory_text: str,
) -> discord.Embed:
    """Build the primary 8:00 AM Trader Advisory embed."""
    embed = discord.Embed(
        title=f"🌅 Raport Makro & Trader Advisory — {date_str}",
        description=advisory_text,
        color=0x1F8B4C,  # Green / Finance
        timestamp=datetime.utcnow(),
    )

    # Market Watch Field
    market_lines = []
    for symbol, info in market_data.items():
        price = info.get("price", "N/A")
        change = info.get("change_pct", "0.00%")
        direction = info.get("direction", "⚪")
        market_lines.append(f"**{symbol}**: `{price}` ({direction} {change})")

    if market_lines:
        embed.add_field(
            name="📊 Notowania Rynkowe",
            value="\n".join(market_lines),
            inline=False,
        )

    embed.set_footer(
        text="Newsbox Trading Advisory • Gemini AI",
        icon_url="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/trending_up/materialicons/48dp/2x/baseline_trending_up_black_48dp.png",
    )
    return embed


def create_calendar_embed(
    date_str: str,
    calendar_events: List[Dict[str, Any]],
    calendar_advice: Optional[str] = None,
) -> discord.Embed:
    """Build the Economic Calendar & Risk Assessment embed."""
    embed = discord.Embed(
        title=f"📅 Kalendarz Ekonomiczny & Ryzyka Sesji — {date_str}",
        color=0xE67E22,  # Orange / Warning
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
