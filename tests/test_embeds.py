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
