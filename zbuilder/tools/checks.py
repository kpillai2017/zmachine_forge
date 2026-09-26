"""Tool 6: run ALLOWLISTED checks only (ruff, pytest, the eval harness)."""
from __future__ import annotations

import shutil
import subprocess
import sys

from zbuilder.paths import PROJECT_ROOT

TAIL = 3000


def _run(argv: list[str], timeout: int) -> dict:
    try:
        p = subprocess.run(argv, cwd=PROJECT_ROOT, capture_output=True, text=True,
                           timeout=timeout)
        out = (p.stdout + p.stderr)[-TAIL:]
        return {"command": " ".join(argv), "exit_code": p.returncode,
                "passed": p.returncode == 0, "tail": out}
    except subprocess.TimeoutExpired as exc:
        tail = ((exc.stdout or "") if isinstance(exc.stdout, str) else "")[-TAIL:]
        return {"command": " ".join(argv), "exit_code": -1, "passed": False,
                "tail": f"TIMEOUT after {timeout}s\n{tail}"}


def run_ruff(timeout: int = 60) -> dict:
    if shutil.which("ruff") is None:
        return {"command": "ruff", "exit_code": 0, "passed": True,
                "tail": "ruff not installed - lint skipped", "skipped": True}
    return _run(["ruff", "check", "zforge", "zbuilder", "eval", "tests"], timeout)


def run_pytest(tests: list[str] | None = None, timeout: int = 600) -> dict:
    targets = [t for t in (tests or []) if (PROJECT_ROOT / t).exists()] or ["tests"]
    return _run([sys.executable, "-m", "pytest", "-q", *targets], timeout)


def run_eval(case_ids: list[str] | None = None, timeout: int = 900) -> dict:
    result = _run([sys.executable, "-m", "eval.run_eval", *(case_ids or [])], timeout)
    lines = result["tail"].splitlines()
    result["failed_cases"] = [ln.split()[1] for ln in lines if ln.startswith("FAIL")]
    return result


CHECKS = {"ruff": run_ruff, "pytest": run_pytest, "eval": run_eval}
