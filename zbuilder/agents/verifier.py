"""Verifier: pass/fail is decided by TOOLS (lint, pytest, eval), never by
a model. The LLM is only used to DIAGNOSE a failure into a fix brief."""
from __future__ import annotations

from zbuilder.agents.base import Agent
from zbuilder.plan import Task
from zbuilder.tools.checks import run_eval, run_pytest, run_ruff


class Verifier(Agent):
    role = "verifier"

    def verify(self, task: Task) -> dict:
        checks = [run_ruff()]
        if task.tests:
            checks.append(run_pytest(task.tests))
        if task.eval_cases:
            checks.append(run_eval(task.eval_cases))
        passed = all(c["passed"] for c in checks)
        self.log.event(self.role, task.id, "verify", passed=passed,
                       checks=[{k: c[k] for k in ("command", "exit_code", "passed")}
                               for c in checks])
        return {"passed": passed, "checks": checks}

    def diagnose(self, task: Task, report: dict, spec_brief: str) -> str:
        failures = "\n\n".join(f"$ {c['command']}\n{c['tail']}" for c in report["checks"]
                               if not c["passed"])
        if self.offline:
            return failures
        return self.ask(task.id, f"Task {task.id}: {task.title}\n\nFailing checks:\n"
                                 f"{failures}\n\n{spec_brief[:6000]}")
