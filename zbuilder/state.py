"""Build state (build/state.json) and the structured run log
(build/logs/run-<timestamp>.jsonl, proforma Section 8b)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from zbuilder.paths import LOG_DIR, STATE_FILE

STATUSES = ("TODO", "BRIEFED", "IN_PROGRESS", "DONE", "BLOCKED")


class BuildState:
    def __init__(self, path: Path = STATE_FILE):
        self.path = path
        self.data = json.loads(path.read_text()) if path.exists() else {"tasks": {}}

    def status(self, task_id: str) -> str:
        return self.data["tasks"].get(task_id, {}).get("status", "TODO")

    def set(self, task_id: str, status: str, **info) -> None:
        assert status in STATUSES, status
        entry = self.data["tasks"].setdefault(task_id, {})
        entry.update(status=status, updated=time.strftime("%Y-%m-%d %H:%M:%S"), **info)
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2) + "\n")


class RunLog:
    """One JSON object per line: who did what, with which evidence."""

    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.path = LOG_DIR / f"run-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"

    def event(self, agent: str, task: str, action: str, **details) -> None:
        record = {"time": time.strftime("%H:%M:%S"), "agent": agent, "task": task,
                  "action": action, **details}
        with self.path.open("a") as f:
            f.write(json.dumps(record, default=str) + "\n")
