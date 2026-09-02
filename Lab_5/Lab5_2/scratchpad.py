"""Demo 2 & 3 (Context Management, S4) - a disk-backed audit trail and
checkpoint store, keyed by claim_id.

Holding pipeline state in memory only is fine until something crashes. This
file does two jobs with one JSON file: (1) record every stage's finding for
audit, and (2) hold each claim's status (new / in_progress / done / failed)
so a restart can skip already-finished work. Every mutation flushes to disk
immediately - that is the contract that makes crash recovery honest.
"""

import json
from pathlib import Path


class Scratchpad:
    """A tiny JSON-on-disk store keyed by claim_id."""

    def __init__(self, path: str = "scratchpad.json"):
        self.path = Path(path)
        self._data: dict = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                # Corrupted file - start fresh but don't delete it
                # (alerting belongs in a real system, not silent deletion).
                self._data = {}

    def status(self, claim_id: str) -> str:
        return self._data.get(claim_id, {}).get("status", "new")

    def log(self, claim_id: str, stage: str, payload) -> None:
        """Record what happened in a given stage for a given claim."""
        entry = self._data.setdefault(
            claim_id, {"status": "in_progress", "findings": []}
        )
        entry["findings"].append({"stage": stage, "payload": payload})
        self._flush()

    def mark_done(self, claim_id: str) -> None:
        entry = self._data.setdefault(claim_id, {"findings": []})
        entry["status"] = "done"
        self._flush()

    def mark_failed(self, claim_id: str, reason: str) -> None:
        entry = self._data.setdefault(claim_id, {"findings": []})
        entry["status"] = "failed"
        entry["failure_reason"] = reason
        self._flush()

    def _flush(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2))
