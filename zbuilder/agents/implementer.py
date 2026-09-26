"""Implementer: the language/VM expert. With a model it returns whole files
(```file:path blocks) that are written ONLY if they are inside the task's
scope. Offline it writes a self-contained brief to build/tasks/<id>.md for
a human - or Rovo Dev in the editor - to implement."""
from __future__ import annotations

from zbuilder.agents.base import Agent
from zbuilder.paths import TASK_DIR
from zbuilder.persona import system_prompt
from zbuilder.plan import Task
from zbuilder.tools.files import list_files, parse_file_blocks, read_file, write_file

CODE_LIMIT = 40_000


def in_scope(task: Task, path: str) -> bool:
    return path.startswith("tests/") or any(
        path == f or (f.endswith("/") and path.startswith(f)) for f in task.files)


class Implementer(Agent):
    role = "implementer"

    def _prompt(self, task: Task, spec_brief: str, feedback: str) -> str:
        code, used = [], 0
        for pattern in task.files:
            for path in list_files(pattern.rstrip("/"), "*"):
                text = read_file(path)
                if used + len(text) > CODE_LIMIT:
                    code.append(f"\n(file {path} omitted: context budget)\n")
                    continue
                code.append(f"\n```file:{path}\n{text}\n```\n")
                used += len(text)
        checks = ", ".join(task.eval_cases + task.tests) or "review only"
        return (f"# Task {task.id} (tier {task.tier}): {task.title}\n\n"
                f"Files you own: {', '.join(task.files)} (plus tests/)\n"
                f"Done when these pass: {checks}\n"
                f"Run: python -m pytest -q {' '.join(task.tests)}; "
                f"python -m eval.run_eval {' '.join(task.eval_cases)}\n\n"
                f"{_feedback_section(feedback)}"
                f"{spec_brief}\n\n## Current code\n{''.join(code) or '(nothing yet)'}")

    def write_brief(self, task: Task, spec_brief: str, feedback: str = "") -> str:
        TASK_DIR.mkdir(parents=True, exist_ok=True)
        path = TASK_DIR / f"{task.id}.md"
        path.write_text("<!-- paste into Rovo Dev, or implement by hand -->\n\n"
                        + system_prompt(self.role) + "\n\n"
                        + self._prompt(task, spec_brief, feedback))
        self.log.event(self.role, task.id, "brief_written", path=str(path))
        return str(path)

    def implement(self, task: Task, spec_brief: str, feedback: str = "") -> list[str]:
        reply = self.ask(task.id, self._prompt(task, spec_brief, feedback))
        written, rejected = [], []
        for path, body in parse_file_blocks(reply).items():
            if in_scope(task, path):
                write_file(path, body)
                written.append(path)
            else:
                rejected.append(path)
        self.log.event(self.role, task.id, "files_written", written=written, rejected=rejected)
        return written


def _feedback_section(feedback: str) -> str:
    return f"## Feedback from the last attempt\n{feedback}\n" if feedback else ""
