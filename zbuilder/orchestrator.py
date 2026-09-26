"""The Orchestrator: a DETERMINISTIC state machine (not an LLM).

For each tier, in order, for each task not yet DONE:

    Spec Analyst.brief ─► Implementer ─► Verifier (tools decide pass/fail)
                              ▲              │ fail: Verifier.diagnose
                              └── feedback ◄─┘   (at most MAX_ATTEMPTS)
    pass ─► Reviewer ─► approve ─► DONE        revise ─► feedback, retry
    attempts used up ─► BLOCKED (with the last failure attached)

STOP rule: a tier starts only when every task of the previous tier is DONE.
Offline ("brief" provider): the Implementer writes build/tasks/<id>.md
instead, and the Verifier then checks whether the work is already there -
so the same loop verifies code written by a human or by Rovo Dev.
"""
from __future__ import annotations

import os

from zbuilder.agents.architect import Architect
from zbuilder.agents.base import Budget, BudgetExceeded
from zbuilder.agents.implementer import Implementer
from zbuilder.agents.reviewer import Reviewer
from zbuilder.agents.spec_analyst import SpecAnalyst
from zbuilder.agents.verifier import Verifier
from zbuilder.llm.provider import Provider, ProviderError
from zbuilder.plan import Task, tiers
from zbuilder.state import BuildState, RunLog

MAX_ATTEMPTS = 3


class Orchestrator:
    def __init__(self, provider: Provider, max_calls: int | None = None, echo=print):
        self.provider = provider
        self.log = RunLog()
        self.budget = Budget(max_calls or int(os.environ.get("ZB_MAX_CALLS", "60")))
        args = (provider, self.log, self.budget)
        self.spec = SpecAnalyst(*args)
        self.architect = Architect(*args)
        self.implementer = Implementer(*args)
        self.verifier = Verifier(*args)
        self.reviewer = Reviewer(*args)
        self.state = BuildState()
        self.echo = echo

    # ------------------------------------------------------------------ build
    def build(self, only_tier: int | None = None, only_task: str | None = None) -> bool:
        self.echo(f"provider: {self.provider.name}"
                  f"{' (offline: briefs + verification only)' if self.provider.offline else ''}")
        for tier, tasks in tiers().items():
            if only_tier is not None and tier != only_tier:
                continue
            if only_task is None and not self._previous_tiers_done(tier):
                self.echo(f"STOP: tier {tier} waits until every earlier task is DONE")
                return False
            for task in tasks:
                if only_task and task.id != only_task:
                    continue
                if self.state.status(task.id) == "DONE" and not only_task:
                    self.echo(f"  {'[DONE]':<9} {task.id}")
                    continue
                try:
                    status = self.run_task(task)
                except BudgetExceeded as exc:
                    self.echo(f"STOP: {exc}")
                    return False
                self.echo(f"  {'[' + status + ']':<9} {task.id}")
                if status != "DONE" and only_task is None:
                    self.echo(f"STOP: {task.id} is {status}; fix it before continuing")
                    return False
        return True

    def _previous_tiers_done(self, tier: int) -> bool:
        return all(self.state.status(t.id) == "DONE"
                   for earlier, tasks in tiers().items() if earlier < tier for t in tasks)

    def run_task(self, task: Task) -> str:
        brief = self.spec.brief(task)
        if self.provider.offline:
            return self._offline(task, brief)
        feedback = ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.state.set(task.id, "IN_PROGRESS", attempt=attempt)
            try:
                written = self.implementer.implement(task, brief, feedback)
            except ProviderError as exc:
                self.state.set(task.id, "BLOCKED", reason=f"provider error: {exc}")
                return "BLOCKED"
            report = self.verifier.verify(task)
            if not report["passed"]:
                feedback = self.verifier.diagnose(task, report, brief)
                continue
            review = self.reviewer.review(task)
            if review["verdict"] == "approve":
                self.state.set(task.id, "DONE", files=written, review_issues=review["issues"])
                return "DONE"
            feedback = "Reviewer asked for changes:\n" + "\n".join(review["issues"])
        self.state.set(task.id, "BLOCKED", reason=feedback[-2000:])
        return "BLOCKED"

    def _offline(self, task: Task, brief: str) -> str:
        report = self.verifier.verify(task)
        if report["passed"]:
            issues = self.reviewer.audit(task)
            self.state.set(task.id, "DONE", verified_offline=True, review_issues=issues)
            return "DONE"
        feedback = self.verifier.diagnose(task, report, brief)
        path = self.implementer.write_brief(task, brief, feedback)
        self.state.set(task.id, "BRIEFED", brief=path)
        return "BRIEFED"

    # ----------------------------------------------------------------- status
    def status_table(self) -> str:
        rows = []
        for tier, tasks in tiers().items():
            for t in tasks:
                entry = self.state.data["tasks"].get(t.id, {})
                rows.append(f"  tier {tier}  {entry.get('status', 'TODO'):<11} {t.id:<22} "
                            f"{t.title}")
        return "\n".join(rows)
