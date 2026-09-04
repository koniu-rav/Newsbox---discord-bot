import pytest
from unittest.mock import AsyncMock, MagicMock
from newsbox.cogs.schedules import SchedulesCog, DAY_MAP, JOB_DEFINITIONS
from newsbox.services.state_service import StateManager

def test_schedules_day_mapping():
    assert DAY_MAP["sobota"] == "sat"
    assert DAY_MAP["niedziela"] == "sun"
    assert DAY_MAP["pon-pt"] == "mon-fri"
    assert DAY_MAP["codziennie"] == "*"

def test_resolve_canonical_key():
    bot = MagicMock()
    cog = SchedulesCog(bot)
    assert cog._resolve_canonical_key("accuracy") == "accuracy"
    assert cog._resolve_canonical_key("skutecznosc") == "accuracy"
    assert cog._resolve_canonical_key("londyn") == "london"
    assert cog._resolve_canonical_key("portfel") == "portfolio"
    assert cog._resolve_canonical_key("portfel_news") == "portfolio_news"
    assert cog._resolve_canonical_key("flash") == "flash_news"
    assert cog._resolve_canonical_key("nieznany") is None

def test_parse_time_and_day():
    bot = MagicMock()
    cog = SchedulesCog(bot)
    curr = {"day_of_week": "sat", "hour": 12, "minute": 0}

    # Time only, keeping existing day
    d, h, m, err = cog._parse_time_and_day("accuracy", ("14:30",), curr)
    assert err is None
    assert d == "sat"
    assert h == 14
    assert m == 30

    # Day and time
    d, h, m, err = cog._parse_time_and_day("accuracy", ("sobota", "11:00"), curr)
    assert err is None
    assert d == "sat"
    assert h == 11
    assert m == 0

    # English day
    d, h, m, err = cog._parse_time_and_day("portfolio", ("sun", "19:00"), curr)
    assert err is None
    assert d == "sun"
    assert h == 19
    assert m == 0

@pytest.mark.asyncio
async def test_list_schedules_command():
    bot = MagicMock()
    bot.scheduler = MagicMock()
    bot.scheduler.get_job_next_run.return_value = None
    cog = SchedulesCog(bot)

    ctx = MagicMock()
    ctx.channel = AsyncMock()

    await cog.list_schedules.callback(cog, ctx)
    assert ctx.channel.send.called
    sent_text = ctx.channel.send.call_args[0][0]
    assert "Harmonogram Publikacji Wiadomości" in sent_text
    assert "accuracy" in sent_text
    assert "portfolio" in sent_text
    assert "london" in sent_text
