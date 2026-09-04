"""Discord Embed message builders with strict character limits and we.trade community branding."""

from datetime import datetime
import re
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


def create_weekly_outlook_embed(
    date_str: str,
    market_data: Dict[str, Any],
    outlook_text: str,
) -> discord.Embed:
    """Build the Sunday 10:00 AM Strategic Weekly Outlook embed."""
    embed = discord.Embed(
        title=f"🗓️ Strategiczny Plan & Horyzont Tygodniowy — {date_str}",
        description=truncate(outlook_text, MAX_DESCRIPTION_LENGTH),
        color=0x8E44AD,  # Deep Purple / Royal Strategy
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
            name="📊 Notowania Otwarcia Tygodnia (FX • Indeksy • Krypto • Surowce)",
            value=truncate("\n".join(market_lines), MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
    return embed


def create_session_advisory_embed(
    session_key: str,
    date_str: str,
    market_data: Dict[str, Any],
    advisory_text: str,
) -> discord.Embed:
    """Build tailored Session Advisory embed (London, New York, Asia)."""
    s_clean = session_key.lower().strip()
    session_config = {
        "london": {
            "title": f"🇬🇧 Briefing Sesji Londyńskiej (07:00 CET) — {date_str}",
            "color": 0x1F8B4C,  # Emerald Green
            "headline": "📊 Notowania Przed Otwarcie Europy (DAX • FX Majors)",
        },
        "newyork": {
            "title": f"🇺🇸 Briefing Sesji Nowojorskiej (13:30 CET) — {date_str}",
            "color": 0x2980B9,  # Strong Blue
            "headline": "📊 Notowania Przed Wall Street (S&P 500 • DXY • Krypto • Złoto)",
        },
        "asia": {
            "title": f"🇯🇵 Briefing Sesji Azjatyckiej (23:00 CET) — {date_str}",
            "color": 0xD35400,  # Orange / Rust
            "headline": "📊 Notowania Przed Sesją Azji (USD/JPY • AUD • Nikkei • BTC)",
        },
    }

    cfg = session_config.get(s_clean, session_config["london"])

    embed = discord.Embed(
        title=cfg["title"],
        description=truncate(advisory_text, MAX_DESCRIPTION_LENGTH),
        color=cfg["color"],
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
            name=cfg["headline"],
            value=truncate("\n".join(market_lines), MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
    return embed


def create_trader_advisory_embed(
    date_str: str,
    market_data: Dict[str, Any],
    advisory_text: str,
) -> discord.Embed:
    """Build legacy / default Trader Advisory embed."""
    return create_session_advisory_embed("london", date_str, market_data, advisory_text)


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


def format_grouped_source_links(headlines: List[Dict[str, Any]]) -> str:
    """Group article links by news portal and format cleanly without repeating source names unnecessarily."""
    from collections import defaultdict

    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for h in headlines:
        source = h.get("source", "").strip() or "Global News"
        title = truncate(h.get("title", "").strip(), 120)
        url = h.get("url", "").strip()
        if title:
            grouped[source].append({"title": title, "url": url})

    formatted_sections = []
    for source, items in grouped.items():
        if len(items) == 1:
            it = items[0]
            if it["url"]:
                formatted_sections.append(f"[{it['title']}]({it['url']}) ({source})")
            else:
                formatted_sections.append(f"• {it['title']} ({source})")
        else:
            lines = []
            for i, it in enumerate(items):
                if i == len(items) - 1:
                    # Last item in portal group includes the source tag
                    if it["url"]:
                        lines.append(f"[{it['title']}]({it['url']}) ({source})")
                    else:
                        lines.append(f"• {it['title']} ({source})")
                else:
                    if it["url"]:
                        lines.append(f"[{it['title']}]({it['url']})")
                    else:
                        lines.append(f"• {it['title']}")
            formatted_sections.append("\n".join(lines))

    return "\n".join(formatted_sections)


def create_flash_news_embed(
    flash_summary: str,
    headlines: List[Dict[str, Any]],
    header: Optional[str] = None,
    importance: str = "MEDIUM",
    time_str: Optional[str] = None,
) -> discord.Embed:
    """Build Global Flash News embed.
    - If HIGH (or header provided): distinctive alert header with 🚨 and urgent red color (0xE74C3C).
    - If MEDIUM: clean minimalist embed with no title and cyan color (0x00B4D8).
    - No footer, no timestamp, grouped portal sources.
    """
    is_high = importance.upper() == "HIGH" or bool(header)
    title = header if (is_high and header) else ("🚨 PILNE • BREAKING NEWS" if is_high else None)
    color = 0xE74C3C if is_high else 0x00B4D8

    embed = discord.Embed(
        title=title,
        description=truncate(flash_summary, MAX_DESCRIPTION_LENGTH),
        color=color,
    )

    if headlines:
        sources_text = format_grouped_source_links(headlines[:4])
        if sources_text:
            embed.add_field(
                name="🌐 Źródła & Doniesienia",
                value=truncate(sources_text, MAX_FIELD_LENGTH),
                inline=False,
            )

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
    stats: Dict[str, Any],
) -> discord.Embed:
    """Build the Multi-Tier Accuracy & Performance Tracker embed (Global, Weekly, Daily, Sessions)."""
    score = evaluation_result.get("score", 0)
    status = evaluation_result.get("status", "neutralna")
    eval_date = evaluation_result.get("date", "Wczoraj")
    session_key = evaluation_result.get("session", "london")
    breakdown = evaluation_result.get("breakdown", "")
    conclusions = evaluation_result.get("conclusions", "")

    session_name = {
        "london": "🇬🇧 Londyn (Europa)",
        "newyork": "🇺🇸 Nowy Jork (Wall St)",
        "asia": "🇯🇵 Azja (Tokio/Sydney)",
    }.get(session_key, "Sesja Handlowa")

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
        title="📊 Wielopoziomowy Raport Skuteczności • we.trade",
        color=color,
        timestamp=datetime.utcnow(),
    )

    # Extract multi-tier buckets
    global_st = stats.get("global", stats)
    sessions_st = stats.get("sessions", {})
    weekly_st = stats.get("weekly", {})

    # 1. Globalny Counter
    g_total = global_st.get("total", 0)
    g_successful = global_st.get("successful", 0)
    g_neutral = global_st.get("neutral", 0)
    g_failed = global_st.get("failed", 0)
    g_avg = global_st.get("average_score", 0.0)
    g_winrate = global_st.get("win_rate", 0.0)

    global_val = (
        f"• **Globalny Win-Rate**: `{g_winrate}%` (Średnia: `{g_avg}/100`)\n"
        f"• **Wszystkie ewaluacje**: `{g_total}`\n"
        f"• **Rozkład**: 🎯 `{g_successful}` | ⚖️ `{g_neutral}` | ❌ `{g_failed}`"
    )
    embed.add_field(
        name="🏆 1. Skuteczność Globalna (All-Time)",
        value=global_val,
        inline=False,
    )

    # 2. Skuteczność Tygodniowa
    w_num = weekly_st.get("week_number", "Bieżący tydzień")
    w_total = weekly_st.get("total", 0)
    w_winrate = weekly_st.get("win_rate", 0.0)
    w_avg = weekly_st.get("average_score", 0.0)
    w_success = weekly_st.get("successful", 0)

    weekly_val = (
        f"• **Tydzień `{w_num}`**: Win-Rate `{w_winrate}%` | Średnia `{w_avg}/100`\n"
        f"• **Wynik tygodnia**: `{w_success}/{w_total}` udanych analiz"
    )
    embed.add_field(
        name="🗓️ 2. Skuteczność Tygodniowa",
        value=weekly_val,
        inline=False,
    )

    # 3. Rozbicie Sesyjne
    lon_st = sessions_st.get("london", {})
    ny_st = sessions_st.get("newyork", {})
    asia_st = sessions_st.get("asia", {})

    sessions_val = (
        f"• 🇬🇧 **Londyn**: Win-Rate `{lon_st.get('win_rate', 0.0)}%` (Śr: `{lon_st.get('average_score', 0.0)}` | `{lon_st.get('successful', 0)}/{lon_st.get('total', 0)}`)\n"
        f"• 🇺🇸 **Nowy Jork**: Win-Rate `{ny_st.get('win_rate', 0.0)}%` (Śr: `{ny_st.get('average_score', 0.0)}` | `{ny_st.get('successful', 0)}/{ny_st.get('total', 0)}`)\n"
        f"• 🇯🇵 **Azja**: Win-Rate `{asia_st.get('win_rate', 0.0)}%` (Śr: `{asia_st.get('average_score', 0.0)}` | `{asia_st.get('successful', 0)}/{asia_st.get('total', 0)}`)"
    )
    embed.add_field(
        name="🎯 3. Skuteczność w Rozbiciu na Sesje",
        value=sessions_val,
        inline=False,
    )

    # 4. Ostatnia Ewaluacja
    eval_value = (
        f"• **Sesja**: {session_name} (`{eval_date}`)\n"
        f"• **Wynik punktowy**: `{score}/100` ({badge})\n"
        f"• **Weryfikacja rynkowa**:\n{breakdown}"
    )
    embed.add_field(
        name="📅 4. Wynik Ostatniej Ewaluowanej Sesji",
        value=truncate(eval_value, MAX_FIELD_LENGTH),
        inline=False,
    )

    # 5. Wnioski
    if conclusions:
        embed.add_field(
            name="💡 Wnioski i Lekcje Rynkowe",
            value=truncate(conclusions, MAX_FIELD_LENGTH),
            inline=False,
        )

    embed.set_footer(text=BRAND_FOOTER)
    return embed


def clean_markdown_text(text: str) -> str:
    """Clean up markdown text: completely strip blockquote markers ('>'), horizontal rules ('---', '***'), and lone '>'."""
    if not text:
        return ""
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Filter out horizontal divider lines
        if stripped in ["---", "***", "___", ">---", "> ---", ">***", "> ***", "- - -"]:
            continue
        # Remove leading blockquote markers
        if stripped.startswith("> "):
            line = stripped[2:].strip()
        elif stripped == ">":
            continue
        lines.append(line)

    cleaned = "\n".join(lines)
    # Collapse multiple consecutive blank lines into at most 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def quote_text(text: str) -> str:
    """Clean markdown text without any '>' blockquotes or '---' dividers."""
    return clean_markdown_text(text)


async def send_full_message(
    target: discord.abc.Messageable,
    content: str,
) -> List[discord.Message]:
    """Send a full-width text message to Discord, chunking safely if content exceeds 2000 chars."""
    clean_content = content.strip()
    if not clean_content:
        return []

    if len(clean_content) <= 2000:
        msg = await target.send(clean_content)
        return [msg]

    chunks: List[str] = []
    current_chunk = ""
    lines = clean_content.split("\n")

    for line in lines:
        if len(current_chunk) + len(line) + 1 > 1950:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            while len(line) > 1950:
                chunks.append(line[:1950])
                line = line[1950:]
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk.strip())

    sent_messages: List[discord.Message] = []
    for chk in chunks:
        if chk:
            msg = await target.send(chk)
            sent_messages.append(msg)
    return sent_messages


def format_flash_news_message(
    flash_summary: str,
    headlines: List[Dict[str, Any]],
    header: Optional[str] = None,
    importance: str = "MEDIUM",
    time_str: Optional[str] = None,
) -> str:
    """Format Global Flash News as a clean full-width Discord markdown message."""
    is_high = importance.upper() == "HIGH" or bool(header)
    parts = []

    if is_high:
        h_text = header.strip() if header else "🚨 PILNE • BREAKING NEWS"
        if not h_text.startswith("###"):
            h_text = f"### {h_text}"
        parts.append(h_text)

    if flash_summary:
        parts.append(clean_markdown_text(flash_summary))

    if headlines:
        sources_text = format_grouped_source_links(headlines[:4])
        if sources_text:
            parts.append(f"**🌐 Źródła & Doniesienia:**\n{sources_text}")

    return "\n\n".join(parts)


def format_weekly_outlook_message(
    date_str: str,
    market_data: Dict[str, Any],
    outlook_text: str,
) -> str:
    """Format Sunday Strategic Weekly Outlook as a clean full-width Discord markdown message."""
    parts = [f"## 🗓️ Strategiczny Plan & Horyzont Tygodniowy — {date_str}"]

    if outlook_text:
        parts.append(clean_markdown_text(outlook_text))

    market_lines = []
    for symbol, info in market_data.items():
        price = info.get("price", "N/A")
        change = info.get("change_pct", "0.00%")
        direction = info.get("direction", "⚪")
        market_lines.append(f"• **{symbol}**: `{price}` ({direction} {change})")

    if market_lines:
        parts.append(
            "### 📊 Notowania Otwarcia Tygodnia (FX • Indeksy • Krypto • Surowce)\n"
            + "\n".join(market_lines)
        )

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_session_advisory_message(
    session_key: str,
    date_str: str,
    market_data: Dict[str, Any],
    advisory_text: str,
) -> str:
    """Format Session Advisory (London, New York, Asia) as a clean full-width Discord markdown message."""
    s_clean = session_key.lower().strip()
    session_config = {
        "london": {
            "title": f"## 🇬🇧 Briefing Sesji Londyńskiej (07:00 CET) — {date_str}",
            "headline": "### 📊 Notowania Przed Otwarciem Europy (DAX • FX Majors)",
        },
        "newyork": {
            "title": f"## 🇺🇸 Briefing Sesji Nowojorskiej (13:30 CET) — {date_str}",
            "headline": "### 📊 Notowania Przed Wall Street (S&P 500 • DXY • Krypto • Złoto)",
        },
        "asia": {
            "title": f"## 🇯🇵 Briefing Sesji Azjatyckiej (23:00 CET) — {date_str}",
            "headline": "### 📊 Notowania Przed Sesją Azji (USD/JPY • AUD • Nikkei • BTC)",
        },
    }

    cfg = session_config.get(s_clean, session_config["london"])
    parts = [cfg["title"]]

    if advisory_text:
        parts.append(clean_markdown_text(advisory_text))

    market_lines = []
    for symbol, info in market_data.items():
        price = info.get("price", "N/A")
        change = info.get("change_pct", "0.00%")
        direction = info.get("direction", "⚪")
        market_lines.append(f"• **{symbol}**: `{price}` ({direction} {change})")

    if market_lines:
        parts.append(f"{cfg['headline']}\n" + "\n".join(market_lines))

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_single_asset_message(
    symbol: str,
    asset_data: Dict[str, Any],
    advisory_text: str,
) -> str:
    """Format Single Asset advisory as a clean full-width Discord markdown message."""
    price = asset_data.get("price", "N/A")
    change = asset_data.get("change_pct", "0.00%")
    direction = asset_data.get("direction", "⚪")
    ticker = asset_data.get("ticker", "")
    ticker_str = f" • Ticker: `{ticker}`" if ticker else ""

    parts = [
        f"## 🎯 Raport dla Waloru: {symbol.upper()}",
        f"📈 **Aktualny kurs:** `{price}` ({direction} **{change}**){ticker_str}",
    ]

    if advisory_text:
        parts.append(clean_markdown_text(advisory_text))

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_calendar_message(
    date_str: str,
    calendar_events: List[Dict[str, Any]],
    calendar_advice: Optional[str] = None,
) -> str:
    """Format 24-hour Economic Calendar as a clean full-width Discord markdown message."""
    parts = [f"## 📅 24-godzinny Kalendarz Makro (07:00 ➡️ 07:00) — {date_str}"]

    event_lines = []
    for event in calendar_events[:15]:
        time = event.get("time", "")
        currency = event.get("currency", "")
        title = event.get("title", "")
        impact = event.get("impact", "🟡")
        event_lines.append(f"• {impact} `{time}` **[{currency}]** {title}")

    if event_lines:
        parts.append("### ⏰ Publikacje Dnia & Nocy (07:00 Dzisiaj ➡️ 07:00 Jutro)\n" + "\n".join(event_lines))
    else:
        parts.append("### ⏰ Publikacje Dnia & Nocy\n*Brak istotnych publikacji w tym oknie czasowym.*")

    if calendar_advice:
        parts.append(f"### 💡 Zalecenia AI dla Tradera (Londyn • Nowy Jork • Azja)\n{clean_markdown_text(calendar_advice)}")

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_regional_news_message(
    region: str,
    headlines: List[Dict[str, Any]],
    summary_text: Optional[str] = None,
) -> str:
    """Format Regional News Digest as a clean full-width Discord markdown message."""
    flags = {
        "PL": "🇵🇱 Polska / GPW & Biznes",
        "USA": "🇺🇸 Rynki USA & Gospodarka",
        "EU": "🇪🇺 Strefa Euro & EBC",
        "GLOBAL": "🌐 Rynki Globalne & Surowce",
        "CRYPTO": "🪙 Świat Kryptowalut & Web3",
        "ALL": "📰 Przegląd Wiadomości Ze Świata (PL, EU, USA)",
    }
    title = flags.get(region.upper(), f"📰 Wiadomości: {region}")
    parts = [f"## {title}"]

    if summary_text:
        parts.append(clean_markdown_text(summary_text))

    items_text = []
    for h in headlines[:6]:
        item_title = h.get("title", "").strip()
        url = h.get("url", "").strip()
        source = h.get("source", "News")
        reg = h.get("region", "")
        reg_badge = f"`[{reg}]` " if reg and region.upper() == "ALL" else ""
        if url:
            items_text.append(f"• {reg_badge}[{item_title}]({url}) *({source})*")
        else:
            items_text.append(f"• {reg_badge}{item_title} *({source})*")

    if items_text:
        parts.append("### 🔥 Najważniejsze Nagłówki\n" + "\n".join(items_text))

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_crypto_news_message(
    headlines: List[Dict[str, Any]],
    summary_text: Optional[str] = None,
) -> str:
    """Format Crypto & Blockchain Pulse as a clean full-width Discord markdown message."""
    return format_regional_news_message("CRYPTO", headlines, summary_text)


def format_portfolio_message(
    portfolio_data: Dict[str, Any],
    advisory_text: str,
    portfolio_news: List[Dict[str, Any]],
) -> str:
    """Format User Portfolio Overview as a clean full-width Discord markdown message."""
    parts = ["## 💼 Twój Portfel Inwestycyjny & Wiadomości Spółek"]

    quote_lines = []
    for sym, info in portfolio_data.items():
        price = info.get("price", "N/A")
        change = info.get("change_pct", "0.00%")
        direction = info.get("direction", "⚪")
        quote_lines.append(f"• **{sym}**: `{price}` ({direction} {change})")

    if quote_lines:
        parts.append("### 📊 Notowania Twoich Spółek\n" + "\n".join(quote_lines))

    if advisory_text:
        parts.append(f"### 💡 Podsumowanie & Komentarz Portfelowy\n{clean_markdown_text(advisory_text)}")

    news_lines = []
    for h in portfolio_news[:6]:
        title = h.get("title", "").strip()
        url = h.get("url", "").strip()
        source = h.get("source", "News")
        match = h.get("matched_symbol", "")
        badge = f"`[{match}]` " if match else ""
        if url:
            news_lines.append(f"• {badge}[{title}]({url}) *({source})*")
        else:
            news_lines.append(f"• {badge}{title} *({source})*")

    if news_lines:
        parts.append("### 📰 Ostatnie Komunikaty dla Twoich Spółek\n" + "\n".join(news_lines))

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_macro_alert_message(
    event: Dict[str, Any],
    ai_commentary: Optional[str] = None,
) -> str:
    """Format real-time published economic event alert as a clean full-width Discord markdown message."""
    title = event.get("title", "Publikacja Makro")
    currency = event.get("currency", "USD")
    flag = event.get("flag", "🌐")
    country = event.get("country", currency)
    time_str = event.get("time", "")
    impact = event.get("impact", "🔴")
    actual = event.get("actual", "Brak")
    forecast = event.get("forecast", "Brak")
    previous = event.get("previous", "Brak")
    revised = event.get("revised", "")
    sentiment_badge = event.get("sentiment_badge", "⚪")
    sentiment_desc = event.get("sentiment_desc", "")

    header = f"## ⚡ ODCZYT MAKROEKONOMICZNY [{currency}] {flag}"

    # Previous line with optional revision
    prev_str = f"`{previous}`"
    if revised:
        prev_str += f" *({revised})*"

    # Forecast line
    fcast_str = f"`{forecast}`"

    # Actual line with deviation badge
    act_str = f"`{actual}` {sentiment_badge} *({sentiment_desc})*" if sentiment_desc else f"`{actual}`"

    parts = [
        header,
        (
            f"### {impact} {title} • {time_str}\n"
            f"• **Kraj / Obszar**: {country} ({currency})\n"
            f"• **Odczyt (Aktualny)**: {act_str}\n"
            f"• **Prognoza (Konsensus)**: {fcast_str}\n"
            f"• **Poprzednia wartość**: {prev_str}"
        ),
    ]

    if ai_commentary:
        parts.append(f"### 💡 Wpływ Rynkowy & Interpretacja\n{clean_markdown_text(ai_commentary)}")

    parts.append(f"-# {BRAND_FOOTER} • Live Macro Pulse")
    return "\n\n".join(parts)


def format_accuracy_message(
    evaluation_result: Dict[str, Any],
    stats: Dict[str, Any],
) -> str:
    """Format Multi-Tier Accuracy & Performance Tracker as a clean full-width Discord markdown message."""
    score = evaluation_result.get("score", 0)
    eval_date = evaluation_result.get("date", "Wczoraj")
    session_key = evaluation_result.get("session", "london")
    breakdown = clean_markdown_text(evaluation_result.get("breakdown", ""))
    conclusions = clean_markdown_text(evaluation_result.get("conclusions", ""))

    session_name = {
        "london": "🇬🇧 Londyn (Europa)",
        "newyork": "🇺🇸 Nowy Jork (Wall St)",
        "asia": "🇯🇵 Azja (Tokio/Sydney)",
    }.get(session_key, "Sesja Handlowa")

    badge = "🎯 Analiza udana" if score > 75 else ("⚖️ Analiza neutralna" if score > 25 else "❌ Analiza nieudana")

    global_st = stats.get("global", stats)
    sessions_st = stats.get("sessions", {})
    weekly_st = stats.get("weekly", {})

    lon_st = sessions_st.get("london", {})
    ny_st = sessions_st.get("newyork", {})
    asia_st = sessions_st.get("asia", {})

    parts = [
        "## 📊 Wielopoziomowy Raport Skuteczności • we.trade",
        (
            "### 🏆 1. Skuteczność Globalna (All-Time)\n"
            f"• **Globalny Win-Rate**: `{global_st.get('win_rate', 0.0)}%` (Średnia: `{global_st.get('average_score', 0.0)}/100`)\n"
            f"• **Wszystkie ewaluacje**: `{global_st.get('total', 0)}` (🎯 `{global_st.get('successful', 0)}` | ⚖️ `{global_st.get('neutral', 0)}` | ❌ `{global_st.get('failed', 0)}`)"
        ),
        (
            f"### 🗓️ 2. Skuteczność Tygodniowa (Tydzień `{weekly_st.get('week_number', 'Bieżący')}`)\n"
            f"• **Win-Rate tygodnia**: `{weekly_st.get('win_rate', 0.0)}%` | Średnia: `{weekly_st.get('average_score', 0.0)}/100`\n"
            f"• **Wynik**: `{weekly_st.get('successful', 0)}/{weekly_st.get('total', 0)}` udanych analiz"
        ),
        (
            "### 🎯 3. Skuteczność w Rozbiciu na Sesje\n"
            f"• 🇬🇧 **Londyn**: Win-Rate `{lon_st.get('win_rate', 0.0)}%` (Śr: `{lon_st.get('average_score', 0.0)}` | `{lon_st.get('successful', 0)}/{lon_st.get('total', 0)}`)\n"
            f"• 🇺🇸 **Nowy Jork**: Win-Rate `{ny_st.get('win_rate', 0.0)}%` (Śr: `{ny_st.get('average_score', 0.0)}` | `{ny_st.get('successful', 0)}/{ny_st.get('total', 0)}`)\n"
            f"• 🇯🇵 **Azja**: Win-Rate `{asia_st.get('win_rate', 0.0)}%` (Śr: `{asia_st.get('average_score', 0.0)}` | `{asia_st.get('successful', 0)}/{asia_st.get('total', 0)}`)"
        ),
        (
            "### 📅 4. Wynik Ostatniej Ewaluowanej Sesji\n"
            f"• **Sesja**: {session_name} (`{eval_date}`) — Wynik: `{score}/100` ({badge})\n"
            f"• **Weryfikacja rynkowa**:\n{breakdown}"
        ),
    ]

    if conclusions:
        parts.append(f"### 💡 Wnioski i Lekcje Rynkowe\n{conclusions}")

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_weekly_accuracy_message(
    stats: Dict[str, Any],
    week_evaluations: List[Dict[str, Any]],
    conclusions: Optional[str] = None,
) -> str:
    """Format Saturday Comprehensive Weekly Accuracy Report as a clean full-width Discord markdown message."""
    global_st = stats.get("global", {})
    sessions_st = stats.get("sessions", {})
    weekly_st = stats.get("weekly", {})

    lon_st = sessions_st.get("london", {})
    ny_st = sessions_st.get("newyork", {})
    asia_st = sessions_st.get("asia", {})

    week_label = weekly_st.get("week_number", "Bieżący")

    parts = [
        f"## 📊 Tygodniowy Raport Skuteczności AI • we.trade (Tydzień `{week_label}`)",
        "Podsumowanie trafności prognoz, poziomów i sygnałów sesyjnych z minionego tygodnia handlowego.",
        (
            "### 🏆 1. Skuteczność w Minionym Tygodniu\n"
            f"• **Win-Rate Tygodnia**: `{weekly_st.get('win_rate', 0.0)}%` (Średnia ocena: `{weekly_st.get('average_score', 0.0)}/100`)\n"
            f"• **Bilans sesji**: `{weekly_st.get('successful', 0)}/{weekly_st.get('total', 0)}` udanych analiz "
            f"(🎯 `{weekly_st.get('successful', 0)}` | ⚖️ `{weekly_st.get('neutral', 0)}` | ❌ `{weekly_st.get('failed', 0)}`)"
        ),
        (
            "### 🎯 2. Skuteczność w Rozbiciu na Sesje\n"
            f"• 🇬🇧 **Londyn**: Win-Rate `{lon_st.get('win_rate', 0.0)}%` (Śr: `{lon_st.get('average_score', 0.0)}/100` | `{lon_st.get('successful', 0)}/{lon_st.get('total', 0)}`)\n"
            f"• 🇺🇸 **Nowy Jork**: Win-Rate `{ny_st.get('win_rate', 0.0)}%` (Śr: `{ny_st.get('average_score', 0.0)}/100` | `{ny_st.get('successful', 0)}/{ny_st.get('total', 0)}`)\n"
            f"• 🇯🇵 **Azja**: Win-Rate `{asia_st.get('win_rate', 0.0)}%` (Śr: `{asia_st.get('average_score', 0.0)}/100` | `{asia_st.get('successful', 0)}/{asia_st.get('total', 0)}`)"
        ),
        (
            "### 🌐 3. Wyniki Globalne (All-Time)\n"
            f"• **Globalny Win-Rate**: `{global_st.get('win_rate', 0.0)}%` (Średnia: `{global_st.get('average_score', 0.0)}/100`)\n"
            f"• **Łączna liczba ewaluacji**: `{global_st.get('total', 0)}` sesji"
        ),
    ]

    if week_evaluations:
        eval_lines = []
        for e in week_evaluations[-7:]:
            s_name = {"london": "🇬🇧 Londyn", "newyork": "🇺🇸 NY", "asia": "🇯🇵 Azja"}.get(e.get("session", ""), e.get("session", "").upper())
            score = e.get("score", 0)
            badge = "🎯" if score > 75 else ("⚖️" if score > 25 else "❌")
            date_str = e.get("date", "")
            raw_breakdown = clean_markdown_text(e.get("breakdown", "")).split("\n")[0] if e.get("breakdown") else "Zrealizowano"
            eval_lines.append(f"• `{date_str}` **{s_name}**: {badge} `{score}/100` — {raw_breakdown}")
        parts.append("### 📋 4. Przegląd Sesji Minionego Tygodnia\n" + "\n".join(eval_lines))

    if conclusions:
        parts.append(f"### 💡 Kluczowe Wnioski i Lekcje Tygodnia\n{clean_markdown_text(conclusions)}")
    elif week_evaluations and week_evaluations[-1].get("conclusions"):
        parts.append(f"### 💡 Kluczowe Wnioski i Lekcje Tygodnia\n{clean_markdown_text(week_evaluations[-1].get('conclusions', ''))}")

    parts.append(f"-# {BRAND_FOOTER}")
    return "\n\n".join(parts)


def format_error_message(title: str, description: str) -> str:
    """Format error notification as a clean full-width Discord markdown message."""
    return f"### ⚠️ {title}\n{clean_markdown_text(description)}"
