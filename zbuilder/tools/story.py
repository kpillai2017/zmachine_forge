"""Tool 7: run a story headless in zforge; optionally the same script in
dfrotz (if installed) and diff the two transcripts (differential testing)."""
from __future__ import annotations

import difflib
import shutil
import subprocess
from pathlib import Path

from zforge.vm.headless import play


def run_story(story_path: str, script: list[str] | None = None, seed: int = 1,
              max_steps: int = 20_000_000, differential: bool = False) -> dict:
    story = Path(story_path).read_bytes()
    result = play(story, script or [], seed=seed, max_steps=max_steps)
    report = {"exit_reason": result.reason, "steps": result.steps,
              "transcript": result.transcript[-6000:], "trace_tail": result.error_trace,
              "warnings": result.vm.warnings[:20]}
    if differential:
        report["diff"] = _differential(story_path, script or [], result.transcript)
    return report


def _differential(story_path: str, script: list[str], ours: str) -> str:
    dfrotz = shutil.which("dfrotz")
    if dfrotz is None:
        return "dfrotz not installed - differential test skipped"
    p = subprocess.run([dfrotz, "-m", "-p", "-w", "80", story_path],
                       input="\n".join(script) + "\n", capture_output=True, text=True,
                       timeout=120)
    theirs = p.stdout
    norm = lambda s: [ln.rstrip() for ln in s.replace(">", "").splitlines() if ln.strip()]
    diff = list(difflib.unified_diff(norm(theirs), norm(ours), "dfrotz", "zforge", lineterm=""))
    return "identical (ignoring prompts and blank lines)" if not diff else "\n".join(diff[:200])
