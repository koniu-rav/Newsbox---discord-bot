"""Unit tests for Accuracy & Performance Tracking Service with multi-tier and session rules."""

from datetime import date
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


def test_multi_session_accuracy_lifecycle(tmp_path):
    """Test saving and evaluating multiple sessions (London, New York, Asia)."""
    history_file = tmp_path / "test_sessions_history.json"
    service = AccuracyService(history_file=history_file)

    # 1. Record London, NY, and Asia session briefings
    day_str = "2026-09-02"
    service.save_session_briefing("london", "DAX Long", {"DAX": {"price": "18400"}}, briefing_date=day_str)
    service.save_session_briefing("newyork", "S&P 500 Short", {"SPX": {"price": "5500"}}, briefing_date=day_str)
    service.save_session_briefing("asia", "USD/JPY Long", {"USD/JPY": {"price": "154.00"}}, briefing_date=day_str)

    # 2. Evaluate London session
    eval_lon = service.record_session_evaluation("london", day_str, score=85, breakdown="DAX +1.2%", conclusions="Udany DAX")
    assert eval_lon["status"] == "udana"

    # 3. Evaluate New York session
    eval_ny = service.record_session_evaluation("newyork", day_str, score=90, breakdown="SPX -0.8%", conclusions="Udany Short")
    assert eval_ny["status"] == "udana"

    # 4. Evaluate Asia session
    eval_asia = service.record_session_evaluation("asia", day_str, score=20, breakdown="USD/JPY -0.5%", conclusions="Zanegowany ruch")
    assert eval_asia["status"] == "nieudana"

    # Check multi-tier stats
    stats = service.get_multi_tier_stats()
    assert stats["global"]["total"] == 3
    assert stats["global"]["successful"] == 2
    assert stats["global"]["failed"] == 1
    assert stats["global"]["win_rate"] == 66.7

    # Check session breakdown stats
    assert stats["sessions"]["london"]["total"] == 1
    assert stats["sessions"]["london"]["successful"] == 1
    assert stats["sessions"]["london"]["win_rate"] == 100.0

    assert stats["sessions"]["newyork"]["total"] == 1
    assert stats["sessions"]["newyork"]["successful"] == 1
    assert stats["sessions"]["newyork"]["win_rate"] == 100.0

    assert stats["sessions"]["asia"]["total"] == 1
    assert stats["sessions"]["asia"]["failed"] == 1
    assert stats["sessions"]["asia"]["win_rate"] == 0.0


def test_create_multi_tier_accuracy_embed():
    """Test building the Multi-Tier Accuracy embed."""
    eval_result = {
        "date": "2026-09-02",
        "session": "london",
        "score": 85,
        "status": "udana",
        "breakdown": "• DAX: Trafny Long\n• EUR/USD: Płasko",
        "conclusions": "Słaby dolar wspomógł byków na indeksach.",
    }
    stats = {
        "global": {
            "total": 10,
            "successful": 8,
            "neutral": 1,
            "failed": 1,
            "win_rate": 80.0,
            "average_score": 82.5,
        },
        "weekly": {
            "week_number": "2026-W36",
            "total": 5,
            "successful": 4,
            "neutral": 1,
            "failed": 0,
            "win_rate": 80.0,
            "average_score": 84.0,
        },
        "sessions": {
            "london": {"total": 4, "successful": 4, "neutral": 0, "failed": 0, "win_rate": 100.0, "average_score": 88.0},
            "newyork": {"total": 3, "successful": 2, "neutral": 1, "failed": 0, "win_rate": 66.7, "average_score": 78.0},
            "asia": {"total": 3, "successful": 2, "neutral": 0, "failed": 1, "win_rate": 66.7, "average_score": 72.0},
        },
    }

    embed = create_accuracy_embed(eval_result, stats)
    assert "Wielopoziomowy Raport Skuteczności" in embed.title
    assert "we.trade" in embed.title
    assert len(embed.fields) == 5
    assert "80.0%" in embed.fields[0].value
    assert "2026-W36" in embed.fields[1].value
    assert "Londyn" in embed.fields[2].value
    assert "85/100" in embed.fields[3].value
    assert "Słaby dolar" in embed.fields[4].value
