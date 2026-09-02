"""Multi-tier Accuracy & Performance Tracking Service for evaluating trading recommendations across Global, Weekly, Daily, and Session levels (London, New York, Asia)."""

from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_HISTORY_FILE = Path("data/briefings_history.json")
WARSAW_TZ = ZoneInfo("Europe/Warsaw")

VALID_SESSIONS = ["london", "newyork", "asia"]
SESSION_NAMES = {
    "london": "🇬🇧 Londyn (Sesja Europejska)",
    "newyork": "🇺🇸 Nowy Jork (Wall Street)",
    "asia": "🇯🇵 Azja (Tokio / Sydney)",
}


def categorize_score(score: float | int) -> str:
    """Categorize numerical score into status according to user guidelines:
    0 - 25%: Analiza nieudana
    25 - 75%: Analiza neutralna
    75 - 100%: Analiza udana
    """
    if score <= 25:
        return "nieudana"
    elif score <= 75:
        return "neutralna"
    return "udana"


def get_status_badge(status: str) -> str:
    """Get emoji badge for status."""
    st = status.lower()
    if st == "udana":
        return "🎯 Analiza udana"
    elif st == "neutralna":
        return "⚖️ Analiza neutralna"
    return "❌ Analiza nieudana"


class AccuracyService:
    """Manages recording of scheduled session briefings, automated multi-tier scoring, and idempotent statistical counters."""

    def __init__(self, history_file: Path | str = DEFAULT_HISTORY_FILE) -> None:
        self.history_file = Path(history_file)
        self._data: Dict[str, Any] = {
            "pending_sessions": {},
            "evaluations": [],
            "stats": self._empty_stats_structure(),
        }
        self.load_history()

    def _empty_stats_structure(self) -> Dict[str, Any]:
        """Generate empty stats schema for global, weekly, daily, and session tiers."""
        empty_counter = {
            "total": 0,
            "successful": 0,
            "neutral": 0,
            "failed": 0,
            "average_score": 0.0,
            "win_rate": 0.0,
        }
        return {
            "global": dict(empty_counter),
            "sessions": {
                "london": dict(empty_counter),
                "newyork": dict(empty_counter),
                "asia": dict(empty_counter),
            },
            "weekly": {
                "week_number": datetime.now(WARSAW_TZ).strftime("%Y-W%U"),
                **empty_counter,
            },
            "daily": {
                "date": datetime.now(WARSAW_TZ).strftime("%Y-%m-%d"),
                **empty_counter,
            },
            # Flat legacy alias for backward compatibility
            **empty_counter,
        }

    def load_history(self) -> None:
        """Load history from JSON file or initialize empty structure."""
        if self.history_file.exists():
            try:
                content = json.loads(self.history_file.read_text(encoding="utf-8"))
                self._data = content
                self._ensure_default_structure()
                logger.info(
                    "Loaded briefings history from %s (evaluations: %d, pending: %d)",
                    self.history_file,
                    len(self._data.get("evaluations", [])),
                    len(self._data.get("pending_sessions", {})),
                )
                return
            except Exception as e:
                logger.error("Failed to parse %s: %s", self.history_file, e)

        self._ensure_default_structure()
        self.save_history()

    def _ensure_default_structure(self) -> None:
        """Ensure all fields and statistical buckets are present and migrates legacy structures."""
        if "pending_sessions" not in self._data:
            self._data["pending_sessions"] = {}

        # Migrate legacy pending_briefings if present
        if "pending_briefings" in self._data and isinstance(self._data["pending_briefings"], dict):
            for d_str, val in self._data["pending_briefings"].items():
                key = f"{d_str}_london"
                if key not in self._data["pending_sessions"]:
                    self._data["pending_sessions"][key] = {
                        "session": "london",
                        "date": d_str,
                        **val,
                    }

        if "evaluations" not in self._data:
            self._data["evaluations"] = []

        if "stats" not in self._data or not isinstance(self._data.get("stats"), dict):
            self._data["stats"] = self._empty_stats_structure()
        else:
            stats = self._data["stats"]
            if "global" not in stats:
                stats["global"] = {
                    "total": stats.get("total", 0),
                    "successful": stats.get("successful", 0),
                    "neutral": stats.get("neutral", 0),
                    "failed": stats.get("failed", 0),
                    "average_score": stats.get("average_score", 0.0),
                    "win_rate": stats.get("win_rate", 0.0),
                }
            if "sessions" not in stats:
                stats["sessions"] = {
                    "london": dict(stats["global"]),
                    "newyork": {"total": 0, "successful": 0, "neutral": 0, "failed": 0, "average_score": 0.0, "win_rate": 0.0},
                    "asia": {"total": 0, "successful": 0, "neutral": 0, "failed": 0, "average_score": 0.0, "win_rate": 0.0},
                }
            if "weekly" not in stats:
                stats["weekly"] = {"week_number": datetime.now(WARSAW_TZ).strftime("%Y-W%U"), **stats["global"]}
            if "daily" not in stats:
                stats["daily"] = {"date": datetime.now(WARSAW_TZ).strftime("%Y-%m-%d"), **stats["global"]}

        self._recalculate_all_stats()

    def save_history(self) -> None:
        """Save history to JSON file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history_file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.debug("Briefings history saved to %s", self.history_file)
        except Exception as e:
            logger.error("Failed to write briefings history: %s", e)

    def save_session_briefing(
        self,
        session: str,
        advisory_text: str,
        market_snapshot: Dict[str, Any],
        briefing_date: Optional[str] = None,
    ) -> str:
        """Record a scheduled session briefing (london, newyork, asia) for future accuracy evaluation."""
        s_clean = session.lower().strip()
        if s_clean not in VALID_SESSIONS:
            s_clean = "london"

        d_str = briefing_date or datetime.now(WARSAW_TZ).strftime("%Y-%m-%d")
        key = f"{d_str}_{s_clean}"

        self._data["pending_sessions"][key] = {
            "key": key,
            "session": s_clean,
            "date": d_str,
            "timestamp": datetime.utcnow().isoformat(),
            "advisory_text": advisory_text,
            "market_snapshot": market_snapshot,
        }
        self.save_history()
        logger.info("Saved scheduled %s session briefing for %s into accuracy history", s_clean, d_str)
        return key

    # Legacy alias for backward compatibility with older tests and commands
    def save_official_morning_briefing(
        self,
        advisory_text: str,
        market_snapshot: Dict[str, Any],
        briefing_date: Optional[str] = None,
    ) -> str:
        """Legacy helper aliasing to London session."""
        return self.save_session_briefing("london", advisory_text, market_snapshot, briefing_date)

    def get_pending_session_to_evaluate(
        self,
        session: Optional[str] = None,
        reference_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the latest unevaluated session briefing ready for evaluation."""
        ref = reference_date or datetime.now(WARSAW_TZ).date()
        ref_str = ref.strftime("%Y-%m-%d")
        pending = self._data.get("pending_sessions", {})

        candidates = []
        for key, val in pending.items():
            s = val.get("session", "london")
            d = val.get("date", "")
            if session and s != session.lower().strip():
                continue
            # Must be prior to reference_date OR if same day, session has concluded
            if d <= ref_str:
                candidates.append((d, key, val))

        if not candidates:
            return None

        # Sort chronologically, pick latest
        candidates.sort(key=lambda x: (x[0], x[1]))
        return candidates[-1][2]

    # Legacy helper for tests
    def get_yesterday_briefing_to_evaluate(
        self,
        reference_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """Legacy helper aliasing to London session from prior day."""
        ref = reference_date or datetime.now(WARSAW_TZ).date()
        ref_str = ref.strftime("%Y-%m-%d")
        pending = self._data.get("pending_sessions", {})

        prior = [v for k, v in pending.items() if v.get("date", "") < ref_str]
        if not prior:
            return None
        prior.sort(key=lambda x: x.get("date", ""))
        return prior[-1]

    def record_session_evaluation(
        self,
        session: str,
        date_str: str,
        score: int,
        breakdown: str,
        conclusions: str,
    ) -> Dict[str, Any]:
        """Record an evaluation result for a specific session idempotently and recalculate all tiers."""
        s_clean = session.lower().strip()
        if s_clean not in VALID_SESSIONS:
            s_clean = "london"

        eval_id = f"{date_str}_{s_clean}"
        status = categorize_score(score)

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            week_number = dt.strftime("%Y-W%U")
        except Exception:
            week_number = datetime.now(WARSAW_TZ).strftime("%Y-W%U")

        eval_record = {
            "id": eval_id,
            "session": s_clean,
            "date": date_str,
            "week_number": week_number,
            "evaluated_at": datetime.utcnow().isoformat(),
            "score": score,
            "status": status,
            "breakdown": breakdown,
            "conclusions": conclusions,
        }

        # Remove from pending queue
        if eval_id in self._data.get("pending_sessions", {}):
            del self._data["pending_sessions"][eval_id]

        # Replace existing or append
        existing_evals = [e for e in self._data.get("evaluations", []) if e.get("id") != eval_id]
        existing_evals.append(eval_record)
        existing_evals.sort(key=lambda x: (x.get("date", ""), x.get("session", "")))
        self._data["evaluations"] = existing_evals

        self._recalculate_all_stats()
        self.save_history()
        logger.info("Recorded %s session evaluation for %s: score=%d (%s)", s_clean, date_str, score, status)
        return eval_record

    # Legacy helper
    def record_evaluation(
        self,
        date_str: str,
        score: int,
        breakdown: str,
        conclusions: str,
    ) -> Dict[str, Any]:
        """Legacy helper for London evaluation."""
        return self.record_session_evaluation("london", date_str, score, breakdown, conclusions)

    def _recalculate_all_stats(self) -> None:
        """Compute aggregate stats across Global, Weekly, Daily, and Session levels."""
        evals = self._data.get("evaluations", [])
        now = datetime.now(WARSAW_TZ)
        current_week = now.strftime("%Y-W%U")
        current_date = now.strftime("%Y-%m-%d")

        def _calc_counter(items: List[Dict[str, Any]]) -> Dict[str, Any]:
            total = len(items)
            successful = sum(1 for e in items if e.get("status") == "udana")
            neutral = sum(1 for e in items if e.get("status") == "neutralna")
            failed = sum(1 for e in items if e.get("status") == "nieudana")
            avg_score = round(sum(e.get("score", 0) for e in items) / total, 1) if total > 0 else 0.0
            win_rate = round((successful / total) * 100, 1) if total > 0 else 0.0
            return {
                "total": total,
                "successful": successful,
                "neutral": neutral,
                "failed": failed,
                "average_score": avg_score,
                "win_rate": win_rate,
            }

        # 1. Global Stats
        global_stats = _calc_counter(evals)

        # 2. Session Stats
        sessions_stats = {}
        for s in VALID_SESSIONS:
            s_evals = [e for e in evals if e.get("session", "london") == s]
            sessions_stats[s] = _calc_counter(s_evals)

        # 3. Current Week Stats
        week_evals = [e for e in evals if e.get("week_number") == current_week]
        # If no evals this week yet, take latest week available
        if not week_evals and evals:
            latest_week = evals[-1].get("week_number", current_week)
            week_evals = [e for e in evals if e.get("week_number") == latest_week]
            week_num_label = latest_week
        else:
            week_num_label = current_week

        weekly_stats = {
            "week_number": week_num_label,
            **_calc_counter(week_evals),
        }

        # 4. Daily Stats
        daily_evals = [e for e in evals if e.get("date") == current_date]
        if not daily_evals and evals:
            latest_date = evals[-1].get("date", current_date)
            daily_evals = [e for e in evals if e.get("date") == latest_date]
            daily_date_label = latest_date
        else:
            daily_date_label = current_date

        daily_stats = {
            "date": daily_date_label,
            **_calc_counter(daily_evals),
        }

        self._data["stats"] = {
            "global": global_stats,
            "sessions": sessions_stats,
            "weekly": weekly_stats,
            "daily": daily_stats,
            # Legacy root keys for backward compatibility
            **global_stats,
        }

    def get_multi_tier_stats(self) -> Dict[str, Any]:
        """Retrieve aggregated accuracy metrics across all tiers (Global, Weekly, Daily, Sessions)."""
        return dict(self._data.get("stats", {}))

    def get_global_stats(self) -> Dict[str, Any]:
        """Retrieve global aggregate metrics (backward-compatible)."""
        stats = self._data.get("stats", {})
        return dict(stats.get("global", stats))

    def get_last_evaluation(self, session: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the most recently completed evaluation (optionally filtered by session)."""
        evals = self._data.get("evaluations", [])
        if not evals:
            return None
        if session:
            s_clean = session.lower().strip()
            s_evals = [e for e in evals if e.get("session", "london") == s_clean]
            return s_evals[-1] if s_evals else None
        return evals[-1]
