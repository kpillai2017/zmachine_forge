"""Architect: renders the plan and (with a model) PROPOSES changes to it.
Proposals go to build/plan/proposed.json - a human decides."""
from __future__ import annotations

import json

from zbuilder.agents.base import Agent
from zbuilder.paths import PLAN_DIR, PROJECT_ROOT
from zbuilder.plan import DEFAULT_PLAN, tiers


class Architect(Agent):
    role = "architect"

    def render_plan(self) -> str:
        lines = ["# zforge build plan", ""]
        for tier, tasks in tiers().items():
            lines.append(f"## Tier {tier}")
            for t in tasks:
                lines.append(f"- **{t.id}** - {t.title}  \n  files: {', '.join(t.files)}  \n"
                             f"  spec: {', '.join(t.spec_refs)}  \n"
                             f"  done when: {', '.join(t.eval_cases + t.tests) or 'review only'}")
            lines.append("")
        PLAN_DIR.mkdir(parents=True, exist_ok=True)
        (PLAN_DIR / "plan.md").write_text("\n".join(lines))
        return "\n".join(lines)

    def propose(self) -> str:
        plan_md = self.render_plan()
        if self.offline:
            return f"offline: wrote {PLAN_DIR / 'plan.md'} (no model to propose changes)"
        design = (PROJECT_ROOT / "docs" / "DESIGN.md")
        reply = self.ask("plan", f"Current plan:\n{plan_md}\n\nDesign notes:\n"
                         f"{design.read_text()[:8000] if design.exists() else '(none)'}\n\n"
                         "Propose improvements as JSON.")
        try:
            proposal = json.loads(reply[reply.index("{"):reply.rindex("}") + 1])
        except ValueError:
            return "the Architect's reply was not valid JSON; nothing written"
        (PLAN_DIR / "proposed.json").write_text(json.dumps(proposal, indent=2))
        return f"wrote {PLAN_DIR / 'proposed.json'} ({len(proposal.get('tasks', []))} tasks)"


__all__ = ["Architect", "DEFAULT_PLAN"]
