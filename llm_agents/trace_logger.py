"""
Structured trace logging for AIM-V agent interactions.

Every orchestrator invocation produces a TraceRecord that captures the full
decision path: user request, context, routing decision, candidate outputs,
final output, timing, and downstream QA outcome.  Records are persisted as
JSON-Lines so they can later feed supervised fine-tuning and preference
datasets for RLHF research.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TraceRecord:
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)

    # --- request ---
    user_message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    # --- routing ---
    chosen_route: str = ""
    route_candidates: List[str] = field(
        default_factory=lambda: ["strategy", "analytics", "documentation"]
    )

    # --- agent execution ---
    agent_name: str = ""
    agent_output: Dict[str, Any] = field(default_factory=dict)
    candidate_outputs: List[Dict[str, Any]] = field(default_factory=list)

    # --- timing ---
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0

    # --- downstream QA ---
    qa_outcome: Optional[Dict[str, Any]] = None

    # --- evaluator feedback (filled asynchronously) ---
    evaluator_rating: Optional[int] = None
    evaluator_override_reason: Optional[str] = None
    evaluator_edits: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TraceLogger:
    """Append-only JSON-Lines trace store."""

    def __init__(self, log_dir: str = "data/traces") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._log_dir / "traces.jsonl"

    # ---- lifecycle helpers ----

    def begin(self, message: str, context: Dict[str, Any]) -> TraceRecord:
        record = TraceRecord(
            user_message=message,
            context=context,
            start_time=time.time(),
        )
        return record

    def end(self, record: TraceRecord) -> TraceRecord:
        record.end_time = time.time()
        record.duration_ms = (record.end_time - record.start_time) * 1000.0
        self._persist(record)
        return record

    # ---- persistence ----

    def _persist(self, record: TraceRecord) -> None:
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), default=str) + "\n")

    # ---- query helpers (for research notebooks) ----

    def load_all(self) -> List[Dict[str, Any]]:
        if not self._log_path.exists():
            return []
        records: List[Dict[str, Any]] = []
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def load_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        for rec in self.load_all():
            if rec.get("trace_id") == trace_id:
                return rec
        return None
