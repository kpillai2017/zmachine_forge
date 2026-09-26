"""Spec Analyst: owns the spec knowledge base. Building it is deterministic
(fetch, index, §14 table); briefing a task is deterministic retrieval; only
free-form questions use the LLM - and then only over retrieved passages."""
from __future__ import annotations

import json

from zbuilder.agents.base import Agent
from zbuilder.paths import OPCODES_JSON, SPEC_INDEX
from zbuilder.plan import Task
from zbuilder.tools.spec_index import SpecIndex
from zbuilder.tools.spec_pipeline import build_spec

BRIEF_LIMIT = 14_000


class SpecAnalyst(Agent):
    role = "spec_analyst"

    def build(self, force: bool = False) -> dict:
        report = build_spec(force=force)
        self.log.event(self.role, "-", "build_spec", **{k: v for k, v in report.items()
                                                      if k != "changed"})
        return report

    def _index(self) -> SpecIndex:
        if not SPEC_INDEX.exists():
            self.build()
        return SpecIndex()

    def brief(self, task: Task) -> str:
        """The spec passages a task needs, each with its locator."""
        index = self._index()
        parts, used = [f"# Spec brief for task {task.id}\n"], 0
        for ref in task.spec_refs:
            for hit in index.lookup(ref, k=12):
                block = f"\n## [{hit['locator']}]\n{hit['text']}\n"
                if used + len(block) > BRIEF_LIMIT:
                    parts.append("\n(... brief truncated; use `zforge spec` for more)\n")
                    return "".join(parts)
                parts.append(block)
                used += len(block)
        if any(r.startswith("§15") or r == "§14" for r in task.spec_refs) and OPCODES_JSON.exists():
            ops = json.loads(OPCODES_JSON.read_text())["opcodes"]
            table = "\n".join(f"  {o['kind']}:{o['number']:<3} {o['name']:<16} "
                              f"store={o['store']!s:<5} branch={o['branch']!s:<5} {o['syntax']}"
                              for o in ops)
            parts.append(f"\n## v5 opcode table (from §14)\n{table}\n")
        self.log.event(self.role, task.id, "brief", refs=task.spec_refs, chars=used)
        return "".join(parts)

    def answer(self, question: str) -> str:
        """Q&A grounded in retrieved passages; offline = the passages."""
        hits = self._index().lookup(question, k=6)
        if not hits:
            return "not in spec: no passage matches that question."
        context = "\n\n".join(f"[{h['locator']}]\n{h['text']}" for h in hits)
        if self.offline:
            return context
        return self.ask("-", f"Passages:\n{context}\n\nQuestion: {question}")
