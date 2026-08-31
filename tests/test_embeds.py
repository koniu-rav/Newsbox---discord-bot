"""Unit tests for Discord embed builders."""

from newsbox.utils.embeds import (
    create_calendar_embed,
    create_error_embed,
    create_regional_news_embed,
    create_trader_advisory_embed,
)


def test_create_trader_advisory_embed(sample_market_data):
    """Test generating a Trader Advisory embed."""
    embed = create_trader_advisory_embed(
        date_str="Poniedziałek, 31.08.2026",
        market_data=sample_market_data,
        advisory_text="🧭 **MARKET REGIME**: Risk-on.\n🟢 **CO HANDLOWAĆ**: DAX Long.\n⛔ **CZEGO UNIKAĆ**: EUR/USD.",
    )

    assert "Raport Makro & Trader Advisory" in embed.title
    assert "Poniedziałek, 31.08.2026" in embed.title
    assert "Risk-on" in embed.description
    assert len(embed.fields) >= 1
    assert "Notowania Rynkowe" in embed.fields[0].name


def test_create_calendar_embed(sample_calendar_events):
    """Test generating an Economic Calendar embed."""
    embed = create_calendar_embed(
        date_str="Poniedziałek, 31.08.2026",
        calendar_events=sample_calendar_events,
        calendar_advice="Zalecenie: zredukuj pozycje przed 14:30.",
    )

    assert "Kalendarz Ekonomiczny" in embed.title
    assert len(embed.fields) == 2
    assert "Zaplanowane Publikacje" in embed.fields[0].name
    assert "Zalecenia AI dla Tradera" in embed.fields[1].name


def test_create_regional_news_embed(sample_headlines):
    """Test generating regional news embed."""
    embed = create_regional_news_embed(
        region="PL",
        headlines=sample_headlines,
        summary_text="Podsumowanie rynków w Polsce.",
    )

    assert "Polska / GPW" in embed.title
    assert "Podsumowanie rynków w Polsce." in embed.description
    assert len(embed.fields) == 1
    assert "Najważniejsze Nagłówki" in embed.fields[0].name


def test_create_error_embed():
    """Test generating an error notification embed."""
    embed = create_error_embed(
        title="Błąd połączenia",
        description="Nie udało się połączyć z API.",
    )

    assert "Błąd połączenia" in embed.title
    assert "Nie udało się połączyć z API." in embed.description
