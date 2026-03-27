"""
Expert feedback and preference capture for RLHF research.

Two feedback modes:
  1. Scalar rating  — evaluator scores a single agent output (1-5) on
     multiple rubric criteria.
  2. Pairwise preference — evaluator picks the better of two candidate
     outputs and provides a rationale.

Records are persisted as JSON-Lines alongside traces so they can be joined
for reward-model training.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------- rubric definition ----------

RUBRIC_CRITERIA: List[str] = [
    "technical_correctness",
    "protocol_adherence",
    "completeness",
    "clarity",
    "actionability",
    "safety_compliance",
    "role_boundary_compliance",
    "usefulness",
]


# ---------- data classes ----------

@dataclass
class ScalarFeedback:
    feedback_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    trace_id: str = ""
    evaluator_id: str = ""
    timestamp: float = field(default_factory=time.time)
    scores: Dict[str, int] = field(default_factory=dict)
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PairwisePreference:
    preference_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    trace_id: str = ""
    evaluator_id: str = ""
    timestamp: float = field(default_factory=time.time)
    output_a: Dict[str, Any] = field(default_factory=dict)
    output_b: Dict[str, Any] = field(default_factory=dict)
    preferred: str = ""  # "a" or "b"
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------- store ----------

class FeedbackStore:
    """Append-only JSON-Lines store for evaluator feedback."""

    def __init__(self, log_dir: str = "data/feedback") -> None:
        self._dir = Path(log_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._scalar_path = self._dir / "scalar_feedback.jsonl"
        self._pairwise_path = self._dir / "pairwise_preferences.jsonl"

    # ---- write ----

    def record_scalar(self, fb: ScalarFeedback) -> ScalarFeedback:
        with open(self._scalar_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(fb.to_dict(), default=str) + "\n")
        return fb

    def record_preference(self, pref: PairwisePreference) -> PairwisePreference:
        with open(self._pairwise_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(pref.to_dict(), default=str) + "\n")
        return pref

    # ---- read ----

    def load_scalar(self) -> List[Dict[str, Any]]:
        return self._load(self._scalar_path)

    def load_pairwise(self) -> List[Dict[str, Any]]:
        return self._load(self._pairwise_path)

    @staticmethod
    def _load(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
