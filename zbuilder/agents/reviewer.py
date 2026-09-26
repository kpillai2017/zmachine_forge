"""Reviewer: readability + spec fidelity. Deterministic audits always run;
with a model an LLM-judge adds an approve/revise verdict."""
from __future__ import annotations

import ast
import json

from zbuilder.agents.base import Agent
from zbuilder.plan import Task
from zbuilder.tools.files import list_files, read_file

MAX_FUNCTION_LINES = 60


def audit_python(path: str, source: str) -> list[str]:
    """Readability rules a student would thank us for (proforma Section 2)."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"{path}: syntax error line {exc.lineno}"]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > MAX_FUNCTION_LINES:
                issues.append(f"{path}:{node.lineno} {node.name} is {length} lines "
                              f"(> {MAX_FUNCTION_LINES}); split it")
            if "/vm/ops/" in path and node.name.startswith("op_"):
                doc = ast.get_docstring(node) or ""
                if "§" not in doc:
                    issues.append(f"{path}:{node.lineno} {node.name} has no § citation")
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(f"{path}:{node.lineno} bare 'except:' hides bugs")
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("eval", "exec"):
            issues.append(f"{path}:{node.lineno} eval/exec is not allowed")
    return issues


class Reviewer(Agent):
    role = "reviewer"

    def audit(self, task: Task) -> list[str]:
        issues = []
        for pattern in task.files:
            for path in list_files(pattern.rstrip("/"), "*.py"):
                if path.endswith(".py"):
                    issues += audit_python(path, read_file(path))
        return issues

    def review(self, task: Task) -> dict:
        issues = self.audit(task)
        verdict = "approve"
        if not self.offline:
            code = "\n\n".join(f"### {p}\n{read_file(p)[:12000]}"
                               for f in task.files for p in list_files(f.rstrip("/"), "*.py"))
            reply = self.ask(task.id, f"Task {task.id}: {task.title}\n\n{code[:40000]}")
            try:
                judged = json.loads(reply[reply.index("{"):reply.rindex("}") + 1])
                verdict = judged.get("verdict", "approve")
                issues += [f"LLM: {i}" for i in judged.get("issues", [])]
            except ValueError:
                issues.append("LLM reviewer reply was not JSON (ignored)")
        self.log.event(self.role, task.id, "review", verdict=verdict, issues=len(issues))
        return {"verdict": verdict, "issues": issues}
