"""Tool 9: append an architecture/spec decision record to docs/DECISIONS.md."""
from __future__ import annotations

import time

from zbuilder.paths import DOCS_DIR


def record_decision(title: str, context: str, decision: str, spec_refs: list[str]) -> str:
    path = DOCS_DIR / "DECISIONS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text() if path.exists() else "# Decision records\n"
    number = existing.count("\n## ADR-") + 1
    entry = (f"\n## ADR-{number:03d}: {title}\n\n*{time.strftime('%Y-%m-%d')}* - "
             f"spec: {', '.join(spec_refs) or 'n/a'}\n\n**Context.** {context}\n\n"
             f"**Decision.** {decision}\n")
    path.write_text(existing.rstrip("\n") + "\n" + entry)
    return f"ADR-{number:03d}"
