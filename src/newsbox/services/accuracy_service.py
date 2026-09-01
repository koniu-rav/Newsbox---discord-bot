"""Accuracy & Performance Tracking Service for evaluating bot trading recommendations."""

from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_HISTORY_FILE = Path("data/briefings_history.json")


def categorize_score(score: float | int) -> str:
    """Categorize numerical score into status according to user guidelines."""
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
    """Manages recording of daily briefings, automated scoring, and global counter stats."""

    def __init__(self, history_file: Path | str = DEFAULT_HISTORY_FILE) -> None:
        self.history_file = Path(history_file)
        self._data: Dict[str, Any] = {
            "pending_briefings": {},
            "evaluations": [],
            "stats": {
                "total": 0,
                "successful": 0,
                "neutral": 0,
                "failed": 0,
                "average_score": 0.0,
            },
        }
        self.load_history()

    def load_history(self) -> None:
        """Load history from JSON file or initialize empty structure."""
        if self.history_file.exists():
            try:
                content = json.loads(self.history_file.read_text(encoding="utf-8"))
                self._data = content
                logger.info("Loaded briefings history from %s (evaluations: %d)", self.history_file, len(self._data.get("evaluations", [])))
                return
            except Exception as e:
                logger.error("Failed to parse %s: %s", self.history_file, e)

        self._ensure_default_structure()
        self.save_history()

    def _ensure_default_structure(self) -> None:
        """Initialize base history structure."""
        if "pending_briefings" not in self._data:
            self._data["pending_briefings"] = {}
        if "evaluations" not in self._data:
            self._data["evaluations"] = []
        if "stats" not in self._data:
            self._data["stats"] = {
                "total": 0,
                "successful": 0,
                "neutral": 0,
                "failed": 0,
                "average_score": 0.0,
            }

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

    def save_briefing(
        self,
        advisory_text: str,
        market_snapshot: Dict[str, Any],
        briefing_date: Optional[str] = None,
    ) -> str:
        """Record today's 08:00 AM briefing for future accuracy evaluation."""
        d_str = briefing_date or datetime.utcnow().strftime("%Y-%m-%d")
        self._data["pending_briefings"][d_str] = {
            "date": d_str,
            "timestamp": datetime.utcnow().isoformat(),
            "advisory_text": advisory_text,
            "market_snapshot": market_snapshot,
        }
        self.save_history()
        logger.info("Saved morning briefing for %s into accuracy history", d_str)
        return d_str

    def get_latest_briefing_to_evaluate(self) -> Optional[Dict[str, Any]]:
        """Get the most recent unevaluated briefing."""
        pending = self._data.get("pending_briefings", {})
        if not pending:
            return None
        # Sort by date ascending to evaluate oldest pending or most recent
        sorted_dates = sorted(pending.keys())
        latest_date = sorted_dates[-1]
        return pending.get(latest_date)

    def record_evaluation(
        self,
        date_str: str,
        score: int,
        breakdown: str,
        conclusions: str,
    ) -> Dict[str, Any]:
        """Record an evaluation result and recalculate global stats."""
        status = categorize_score(score)
        eval_record = {
            "date": date_str,
            "evaluated_at": datetime.utcnow().isoformat(),
            "score": score,
            "status": status,
            "breakdown": breakdown,
            "conclusions": conclusions,
        }

        # Remove from pending
        if date_str in self._data.get("pending_briefings", {}):
            del self._data["pending_briefings"][date_str]

        # Add to evaluations (replace if already exists for same date)
        evals = [e for e in self._data.get("evaluations", []) if e.get("date") != date_str]
        evals.append(eval_record)
        self._data["evaluations"] = evals

        # Recalculate stats
        total = len(evals)
        successful = sum(1 for e in evals if e.get("status") == "udana")
        neutral = sum(1 for e in evals if e.get("status") == "neutralna")
        failed = sum(1 for e in evals if e.get("status") == "nieudana")
        avg_score = round(sum(e.get("score", 0) for e in evals) / total, 1) if total > 0 else 0.0

        self._data["stats"] = {
            "total": total,
            "successful": successful,
            "neutral": neutral,
            "failed": failed,
            "average_score": avg_score,
            "win_rate": round((successful / total) * 100, 1) if total > 0 else 0.0,
        }

        self.save_history()
        logger.info("Recorded evaluation for %s: score=%d (%s)", date_str, score, status)
        return eval_record

    def get_global_stats(self) -> Dict[str, Any]:
        """Retrieve aggregated global accuracy metrics."""
        return dict(self._data.get("stats", {}))

    def get_last_evaluation(self) -> Optional[Dict[str, Any]]:
        """Get the most recently recorded evaluation."""
        evals = self._data.get("evaluations", [])
        return evals[-1] if evals else None
