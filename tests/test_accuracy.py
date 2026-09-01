"""Unit tests for Accuracy & Performance Tracking Service."""

from newsbox.services.accuracy_service import AccuracyService, categorize_score, get_status_badge
from newsbox.utils.embeds import create_accuracy_embed


def test_categorize_score():
    """Test accuracy score categorization according to user rules."""
    # 0 - 25%: nieudana
    assert categorize_score(0) == "nieudana"
    assert categorize_score(25) == "nieudana"

    # 25 - 75%: neutralna
    assert categorize_score(26) == "neutralna"
    assert categorize_score(50) == "neutralna"
    assert categorize_score(75) == "neutralna"

    # 75 - 100%: udana
    assert categorize_score(76) == "udana"
    assert categorize_score(85) == "udana"
    assert categorize_score(100) == "udana"


def test_get_status_badge():
    """Test status string badges."""
    assert "Analiza udana" in get_status_badge("udana")
    assert "Analiza neutralna" in get_status_badge("neutralna")
    assert "Analiza nieudana" in get_status_badge("nieudana")


def test_accuracy_service_lifecycle(tmp_path):
    """Test saving briefings, evaluating, and calculating global stats."""
    history_file = tmp_path / "test_history.json"
    service = AccuracyService(history_file=history_file)

    # 1. Save morning briefing
    service.save_briefing(
        advisory_text="Kupuj DAX, unikaj EUR/USD",
        market_snapshot={"DAX": {"price": "18400"}},
        briefing_date="2026-08-31",
    )

    pending = service.get_latest_briefing_to_evaluate()
    assert pending is not None
    assert pending["date"] == "2026-08-31"

    # 2. Record successful evaluation (score 85%)
    record = service.record_evaluation(
        date_str="2026-08-31",
        score=85,
        breakdown="• DAX: +1.2% zysk\n• EUR/USD: płasko",
        conclusions="Wysoka korelacja potwierdziła prognozę.",
    )
    assert record["status"] == "udana"
    assert record["score"] == 85

    # 3. Check stats
    stats = service.get_global_stats()
    assert stats["total"] == 1
    assert stats["successful"] == 1
    assert stats["failed"] == 0
    assert stats["win_rate"] == 100.0
    assert stats["average_score"] == 85.0

    # 4. Add a failed evaluation (score 20%)
    service.record_evaluation(
        date_str="2026-09-01",
        score=20,
        breakdown="• DAX: Ruch przeciwny do zalecenia",
        conclusions="Niespodziewany odczyt inflacji.",
    )

    stats2 = service.get_global_stats()
    assert stats2["total"] == 2
    assert stats2["successful"] == 1
    assert stats2["failed"] == 1
    assert stats2["win_rate"] == 50.0
    assert stats2["average_score"] == 52.5


def test_create_accuracy_embed():
    """Test building the Accuracy embed."""
    eval_result = {
        "date": "2026-08-31",
        "score": 85,
        "status": "udana",
        "breakdown": "• DAX: Trafny Long\n• EUR/USD: Płasko",
        "conclusions": "Słaby dolar wspomógł byków na indeksach.",
    }
    global_stats = {
        "total": 10,
        "successful": 8,
        "neutral": 1,
        "failed": 1,
        "win_rate": 80.0,
        "average_score": 82.5,
    }

    embed = create_accuracy_embed(eval_result, global_stats)
    assert "Raport Skuteczności" in embed.title
    assert len(embed.fields) == 3
    assert "80.0%" in embed.fields[0].value
    assert "85/100" in embed.fields[1].value
    assert "Słaby dolar" in embed.fields[2].value
