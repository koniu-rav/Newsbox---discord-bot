"""Unit tests for Discord embed builders."""

from newsbox.utils.embeds import (
    create_calendar_embed,
    create_crypto_news_embed,
    create_error_embed,
    create_portfolio_embed,
    create_regional_news_embed,
    create_single_asset_embed,
    create_trader_advisory_embed,
)


def test_create_trader_advisory_embed(sample_market_data):
    """Test generating a Trader Advisory embed with FX/DAX focus."""
    embed = create_trader_advisory_embed(
        date_str="Wtorek, 01.09.2026",
        market_data=sample_market_data,
        advisory_text="🧭 **MARKET REGIME**: Risk-on.\n🟢 **CO HANDLOWAĆ**: DAX Long.\n⛔ **CZEGO UNIKAĆ**: EUR/USD.",
    )

    assert "Briefing Sesji Londyńskiej" in embed.title
    assert "Wtorek, 01.09.2026" in embed.title
    assert "Risk-on" in embed.description
    assert len(embed.fields) >= 1
    assert "Notowania" in embed.fields[0].name


def test_create_single_asset_embed():
    """Test generating single asset embed."""
    asset_data = {
        "symbol": "DAX",
        "ticker": "^GDAXI",
        "price": "18,450.00",
        "change_pct": "+0.45%",
        "direction": "🟢",
    }
    embed = create_single_asset_embed(
        symbol="DAX",
        asset_data=asset_data,
        advisory_text="🎯 **ANALIZA DLA DAX**: Byczy sentyment na otwarciu sesji.",
    )

    assert "Raport dla Waloru: DAX" in embed.title
    assert "18,450.00" in embed.fields[0].value
    assert "+0.45%" in embed.fields[0].value


def test_create_portfolio_embed():
    """Test generating portfolio embed."""
    portfolio_data = {
        "CDR.WA": {"price": "162.40", "change_pct": "+1.20%", "direction": "🟢"},
        "NVDA": {"price": "128.50", "change_pct": "+2.40%", "direction": "🟢"},
    }
    portfolio_news = [
        {"title": "CD Projekt zapowiada nową aktualizację", "source": "Bankier", "matched_symbol": "CDR.WA"}
    ]
    embed = create_portfolio_embed(
        portfolio_data=portfolio_data,
        advisory_text="Pozycje stabilne.",
        portfolio_news=portfolio_news,
    )

    assert "Twój Portfel Inwestycyjny" in embed.title
    assert len(embed.fields) == 2
    assert "CDR.WA" in embed.fields[0].value


def test_create_crypto_news_embed(sample_headlines):
    """Test generating crypto news embed."""
    embed = create_crypto_news_embed(
        headlines=sample_headlines,
        summary_text="Bitcoin testuje lokalne wsparcie.",
    )

    assert "Crypto & Blockchain Pulse" in embed.title
    assert "Bitcoin testuje lokalne wsparcie." in embed.description
    assert len(embed.fields) == 1


def test_create_flash_news_embed():
    """Test generating minimalist flash news embed with no title, no footer, and grouped portal sources."""
    from newsbox.utils.embeds import create_flash_news_embed

    headlines = [
        {"title": "US pounds Iran, Tehran strikes back at bases in biggest exchange since July", "url": "https://www.investing.com/news1", "source": "Investing.com"},
        {"title": "Explainer-Why is Senegal reworking its debt and what makes it different?", "url": "https://www.investing.com/news2", "source": "Investing.com"},
    ]
    summary = "📰 Doniesienia o eskalacji na Bliskim Wschodzie.\n🎯 Możliwy wzrost zmienności na `Ropa`, `Złoto` oraz `DXY`."
    embed = create_flash_news_embed(flash_summary=summary, headlines=headlines)

    # Must NOT have title or footer
    assert embed.title is None
    assert embed.footer.text is None
    assert embed.timestamp is None

    # Description must contain concise summary
    assert "Doniesienia o eskalacji" in embed.description
    assert len(embed.fields) == 1
    assert "Źródła & Doniesienia" in embed.fields[0].name

    # Grouped sources check: (Investing.com) should appear once at the end of the group
    field_val = embed.fields[0].value
    assert "https://www.investing.com/news1" in field_val
    assert "https://www.investing.com/news2" in field_val
    assert field_val.count("(Investing.com)") == 1


def test_create_flash_news_embed_high_importance():
    """Test generating high-importance flash news embed with alert header and red color."""
    from newsbox.utils.embeds import create_flash_news_embed

    headlines = [
        {"title": "Fed announces emergency rate cut of 50bps", "url": "https://cnbc.com/news1", "source": "CNBC"},
    ]
    summary = "📰 Fed ogłosił nagłą obniżkę stóp o 50 pb.\n🎯 Gwałtowne osłabienie `DXY` i wzrosty na `Złoto` oraz `S&P 500`."
    header = "🚨 PILNE: Niespodziewana obniżka stóp przez Fed"

    embed = create_flash_news_embed(
        flash_summary=summary,
        headlines=headlines,
        header=header,
        importance="HIGH",
    )

    assert embed.title == "🚨 PILNE: Niespodziewana obniżka stóp przez Fed"
    assert embed.color.value == 0xE74C3C  # Red alert
    assert "50 pb" in embed.description
    assert len(embed.fields) == 1


def test_create_weekly_outlook_embed(sample_market_data):
    """Test generating Sunday Weekly Outlook embed."""
    from newsbox.utils.embeds import create_weekly_outlook_embed

    embed = create_weekly_outlook_embed(
        date_str="Niedziela, 06.09.2026",
        market_data=sample_market_data,
        outlook_text="🌐 **GŁÓWNY MOTYW TYGODNIA**: Risk-on przed danymi NFP.",
    )

    assert "Strategiczny Plan & Horyzont Tygodniowy" in embed.title
    assert "Risk-on" in embed.description
    assert len(embed.fields) == 1
    assert "Notowania" in embed.fields[0].name


def test_create_session_advisory_embed(sample_market_data):
    """Test generating session advisory embeds for London, NY, and Asia."""
    from newsbox.utils.embeds import create_session_advisory_embed

    # London
    lon_embed = create_session_advisory_embed("london", "Środa, 02.09.2026", sample_market_data, "DAX Long")
    assert "Briefing Sesji Londyńskiej" in lon_embed.title

    # New York
    ny_embed = create_session_advisory_embed("newyork", "Środa, 02.09.2026", sample_market_data, "S&P 500 Short")
    assert "Briefing Sesji Nowojorskiej" in ny_embed.title

    # Asia
    asia_embed = create_session_advisory_embed("asia", "Środa, 02.09.2026", sample_market_data, "USD/JPY Long")
    assert "Briefing Sesji Azjatyckiej" in asia_embed.title


def test_format_flash_news_message_medium():
    """Test full-width flash news markdown format for medium importance."""
    from newsbox.utils.embeds import format_flash_news_message

    headlines = [
        {"title": "Headline 1", "url": "https://example.com/1", "source": "Reuters"},
    ]
    summary = "📰 Fakt rynkowy.\n🎯 Wpływ na walory."
    msg = format_flash_news_message(flash_summary=summary, headlines=headlines, importance="MEDIUM")

    assert "### 🚨 PILNE" not in msg
    assert "📰 Fakt rynkowy." in msg
    assert "🎯 Wpływ na walory." in msg
    assert ">" not in msg
    assert "🌐 Źródła & Doniesienia:" in msg
    assert "[Headline 1](https://example.com/1)" in msg


def test_format_flash_news_message_high():
    """Test full-width flash news markdown format for high importance."""
    from newsbox.utils.embeds import format_flash_news_message

    headlines = [
        {"title": "Breaking Headline", "url": "https://example.com/2", "source": "Bloomberg"},
    ]
    summary = "📰 Ważny komunikat.\n🎯 Zmienność na surowcach."
    header = "🚨 PILNE: Nagła eskalacja"
    msg = format_flash_news_message(flash_summary=summary, headlines=headlines, header=header, importance="HIGH")

    assert "### 🚨 PILNE: Nagła eskalacja" in msg
    assert "📰 Ważny komunikat." in msg
    assert ">" not in msg
    assert "[Breaking Headline](https://example.com/2)" in msg


def test_format_session_advisory_message(sample_market_data):
    """Test full-width session advisory formatting for London session."""
    from newsbox.utils.embeds import format_session_advisory_message

    msg = format_session_advisory_message(
        session_key="london",
        date_str="Czwartek, 03.09.2026",
        market_data=sample_market_data,
        advisory_text="🧭 **REŻIM**: Risk-on.\n🟢 **ZALECENIE**: DAX Long.",
    )

    assert "## 🇬🇧 Briefing Sesji Londyńskiej" in msg
    assert "🧭 **REŻIM**: Risk-on." in msg
    assert "### 📊 Notowania Przed Otwarciem Europy" in msg
    assert "DAX" in msg
    assert "EUR/USD" in msg


def test_format_calendar_message():
    """Test full-width economic calendar message formatting."""
    from newsbox.utils.embeds import format_calendar_message

    events = [
        {"time": "08:00", "currency": "GBP", "title": "PKB Wielkiej Brytanii", "impact": "🔴"},
    ]
    advice = "Uwaga na podwyższoną zmienność na funcie."
    msg = format_calendar_message(date_str="Czwartek, 03.09.2026", calendar_events=events, calendar_advice=advice)

    assert "## 📅 24-godzinny Kalendarz Makro" in msg
    assert "🔴 `08:00` **[GBP]** PKB Wielkiej Brytanii" in msg
    assert "### 💡 Zalecenia AI dla Tradera" in msg
    assert "Uwaga na podwyższoną zmienność" in msg


def test_format_portfolio_message():
    """Test full-width portfolio message formatting."""
    from newsbox.utils.embeds import format_portfolio_message

    p_data = {"NVDA": {"price": "128.50", "change_pct": "+2.40%", "direction": "🟢"}}
    p_news = [{"title": "Nowe chipy AI", "url": "https://example.com/chip", "source": "TechNews", "matched_symbol": "NVDA"}]
    msg = format_portfolio_message(portfolio_data=p_data, advisory_text="Portfel w dobrej kondycji.", portfolio_news=p_news)

    assert "## 💼 Twój Portfel Inwestycyjny" in msg
    assert "• **NVDA**: `128.50` (🟢 +2.40%)" in msg
    assert "Portfel w dobrej kondycji." in msg
    assert "`[NVDA]` [Nowe chipy AI](https://example.com/chip)" in msg


def test_format_accuracy_message():
    """Test full-width accuracy message formatting."""
    from newsbox.utils.embeds import format_accuracy_message

    eval_result = {"score": 85, "date": "Wczoraj", "session": "london", "breakdown": "Trafny kierunek na DAX"}
    stats = {
        "global": {"total": 10, "successful": 8, "neutral": 1, "failed": 1, "win_rate": 80.0, "average_score": 82.0},
        "weekly": {"week_number": "36", "total": 4, "successful": 3, "win_rate": 75.0, "average_score": 78.0},
        "sessions": {"london": {"total": 5, "successful": 4, "win_rate": 80.0, "average_score": 85.0}},
    }
    msg = format_accuracy_message(evaluation_result=eval_result, stats=stats)

    assert "## 📊 Wielopoziomowy Raport Skuteczności" in msg
    assert "Globalny Win-Rate" in msg
    assert "80.0%" in msg
    assert "Trafny kierunek na DAX" in msg


def test_clean_markdown_text():
    """Verify that clean_markdown_text completely strips >, ---, and empty quote lines."""
    from newsbox.utils.embeds import clean_markdown_text

    ugly_input = (
        "> 🧭 **SENTYMENT**\n"
        ">\n"
        "---\n"
        ">\n"
        "> 🎯 **ZALECENIE**: DAX Long\n"
        "***\n"
        "> Finansowy komentarz."
    )
    cleaned = clean_markdown_text(ugly_input)
    assert ">" not in cleaned
    assert "---" not in cleaned
    assert "***" not in cleaned
    assert "🧭 **SENTYMENT**" in cleaned
    assert "🎯 **ZALECENIE**: DAX Long" in cleaned
    assert "Finansowy komentarz." in cleaned

