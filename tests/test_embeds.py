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

    assert "Briefing Makro (Londyn • Nowy Jork • Azja)" in embed.title
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
    """Test generating 30-minute flash news embed."""
    from newsbox.utils.embeds import create_flash_news_embed

    headlines = [
        {"title": "Fed announces policy shift", "url": "https://example.com/news1", "source": "Reuters"},
    ]
    summary = "• **Co się wydarzyło**: Fed ogłosił zmianę polityki.\n• **Kiedy**: Przed chwilą.\n• **Wpływ**: Zmienność na DXY."
    embed = create_flash_news_embed(flash_summary=summary, headlines=headlines, time_str="14:30 CET")

    assert "Flash News Ze Świata (14:30 CET)" in embed.title
    assert "we.trade" in embed.title
    assert "Fed ogłosił zmianę" in embed.description
    assert len(embed.fields) == 1
    assert "example.com/news1" in embed.fields[0].value
