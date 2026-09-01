"""Unit tests for Accuracy & Performance Tracking Service with strict trading days rules."""

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


def test_weekend_skip_and_monday_evaluation(tmp_path):
    """Test Friday-to-Monday transition: Friday briefing is evaluated on Monday."""
    history_file = tmp_path / "test_weekend_history.json"
    service = AccuracyService(history_file=history_file)

    # 1. Friday (2026-09-04): Save official 08:00 AM briefing
    friday_date = "2026-09-04"
    service.save_official_morning_briefing(
        advisory_text="Piątkowe zalecenie: DAX Long przed weekendem",
        market_snapshot={"DAX": {"price": "18500"}},
        briefing_date=friday_date,
    )

    # 2. Weekend (Saturday 2026-09-05 & Sunday 2026-09-06): No scheduled dispatches
    # 3. Monday (2026-09-07): Save Monday 08:00 AM briefing
    monday_date = date(2026, 9, 7)
    service.save_official_morning_briefing(
        advisory_text="Poniedziałkowe zalecenie: EUR/USD Short",
        market_snapshot={"EUR/USD": {"price": "1.0850"}},
        briefing_date="2026-09-07",
    )

    # 4. Monday 12:30 evaluation: Must evaluate FRIDAY'S briefing (2026-09-04)
    target_to_eval = service.get_yesterday_briefing_to_evaluate(reference_date=monday_date)
    assert target_to_eval is not None
    assert target_to_eval["date"] == "2026-09-04"

    # 5. Record evaluation for Friday's briefing
    record = service.record_evaluation(
        date_str="2026-09-04",
        score=90,
        breakdown="• DAX: +1.5% w górę po otwarciu sesji w USA",
        conclusions="Bycze pozycjonowanie na weekend zrealizowane.",
    )
    assert record["status"] == "udana"
    assert record["score"] == 90

    # 6. Check that Monday's brief (2026-09-07) remains pending for Tuesday
    tuesday_date = date(2026, 9, 8)
    tuesday_target = service.get_yesterday_briefing_to_evaluate(reference_date=tuesday_date)
    assert tuesday_target is not None
    assert tuesday_target["date"] == "2026-09-07"


def test_accuracy_service_lifecycle_and_rules(tmp_path):
    """Test strict evaluation rules: yesterday only, no duplicates, official 8:00 saving."""
    history_file = tmp_path / "test_history.json"
    service = AccuracyService(history_file=history_file)

    # 1. Day 1 (2026-09-01): Save official 08:00 AM briefing
    service.save_official_morning_briefing(
        advisory_text="Kupuj DAX, unikaj EUR/USD",
        market_snapshot={"DAX": {"price": "18400"}},
        briefing_date="2026-09-01",
    )

    # On Day 1 at 12:30 (ref date 2026-09-01), there is NO yesterday briefing yet
    pending_day1 = service.get_yesterday_briefing_to_evaluate(reference_date=date(2026, 9, 1))
    assert pending_day1 is None

    # 2. Day 2 (2026-09-02): Morning briefing for Day 2 is saved
    service.save_official_morning_briefing(
        advisory_text="BTC Long, DAX Short",
        market_snapshot={"BTC": {"price": "60000"}},
        briefing_date="2026-09-02",
    )

    # On Day 2 at 12:30 (ref date 2026-09-02), yesterday's briefing (2026-09-01) is ready to evaluate!
    pending_day2 = service.get_yesterday_briefing_to_evaluate(reference_date=date(2026, 9, 2))
    assert pending_day2 is not None
    assert pending_day2["date"] == "2026-09-01"

    # 3. Record evaluation for 2026-09-01
    record = service.record_evaluation(
        date_str="2026-09-01",
        score=85,
        breakdown="• DAX: +1.2% zysk\n• EUR/USD: płasko",
        conclusions="Wysoka korelacja potwierdziła prognozę.",
    )
    assert record["status"] == "udana"
    assert record["score"] == 85

    stats = service.get_global_stats()
    assert stats["total"] == 1
    assert stats["successful"] == 1
    assert stats["win_rate"] == 100.0

    # 4. Idempotency test: If evaluation for 2026-09-01 is re-recorded, stats total MUST NOT increase!
    service.record_evaluation(
        date_str="2026-09-01",
        score=85,
        breakdown="• DAX: +1.2% zysk",
        conclusions="Wnioski powtórzone.",
    )
    stats_after_repeat = service.get_global_stats()
    assert stats_after_repeat["total"] == 1

    # 5. Day 3 (2026-09-03): Evaluate Day 2 (2026-09-02)
    pending_day3 = service.get_yesterday_briefing_to_evaluate(reference_date=date(2026, 9, 3))
    assert pending_day3 is not None
    assert pending_day3["date"] == "2026-09-02"

    service.record_evaluation(
        date_str="2026-09-02",
        score=20,
        breakdown="• BTC: Spadek",
        conclusions="Odwrót na rynku krypto.",
    )

    stats_day3 = service.get_global_stats()
    assert stats_day3["total"] == 2
    assert stats_day3["successful"] == 1
    assert stats_day3["failed"] == 1
    assert stats_day3["win_rate"] == 50.0
    assert stats_day3["average_score"] == 52.5


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
