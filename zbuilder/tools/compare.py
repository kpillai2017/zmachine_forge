"""Compare the current compiler with an earlier commit: `zbuilder compare <commit>`.

For every Inform 7 example (examples/*.ni), build it with the old version and
with the current one, and - where it has a walkthrough
(examples/<name>_walkthrough.txt) - play it through with each version's own
interpreter. The report says, per game, whether the story files are byte for
byte the same and whether the transcripts match. It fails if any transcript
differs, or a game compiles with one version and not the other.

The old version is exported with `git archive` into build/compare/<commit>/
and run *from that folder*. That matters: `python -m zforge` imports the
package in the current folder before anything on PYTHONPATH, so pointing
PYTHONPATH at an old copy from the project folder silently runs the current
code (ADR-056). The tool checks which code each side imports before using it.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from zbuilder.paths import BUILD_DIR, PROJECT_ROOT

EXAMPLES = PROJECT_ROOT / "examples"


@dataclass
class GameResult:
    name: str
    old_built: bool
    new_built: bool
    same_story: bool = False
    old_size: int = 0
    new_size: int = 0
    walkthrough: bool = False
    same_transcript: bool = False
    first_difference: str = ""        # the first differing line, for the report

    @property
    def ok(self) -> bool:
        """Good enough: both built, and the walkthrough (if any) plays the same."""
        if self.old_built != self.new_built:
            return False
        return not self.walkthrough or self.same_transcript


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def export(commit: str) -> Path:
    """The commit's files in build/compare/<sha>/ (exported once, then reused)."""
    sha = _git("rev-parse", "--verify", commit + "^{commit}")[:12]
    folder = BUILD_DIR / "compare" / sha
    if not (folder / "zforge").is_dir():
        folder.mkdir(parents=True, exist_ok=True)
        archive = subprocess.run(["git", "archive", sha], cwd=PROJECT_ROOT, check=True,
                                 capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", str(folder)], input=archive, check=True)
    return folder


def imports_from(folder: Path) -> Path:
    """Which zforge package Python imports when run in this folder."""
    out = subprocess.run([sys.executable, "-c", "import zforge; print(zforge.__file__)"],
                         cwd=folder, check=True, capture_output=True, text=True).stdout
    return Path(out.strip()).resolve().parent.parent


def _zforge(folder: Path, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run `python -m zforge ...` from folder, so it uses that folder's code."""
    return subprocess.run([sys.executable, "-m", "zforge", *args], cwd=folder,
                          capture_output=True, text=True, timeout=timeout)


def _build_and_play(folder: Path, source: Path, walkthrough: Path | None,
                    out: Path) -> tuple[Path | None, str]:
    story = out.with_suffix(".z8")
    built = _zforge(folder, "compile", str(source), "-o", str(story)).returncode == 0
    if not built:
        return None, ""
    if walkthrough is None:
        return story, ""
    played = _zforge(folder, "run", str(story), "--script", str(walkthrough),
                     "--ui", "plain", "--seed", "1")
    return story, played.stdout


def compare(commit: str, games: list[str] | None = None) -> list[GameResult]:
    old = export(commit)
    for folder in (old, PROJECT_ROOT):          # the mistake this tool exists to avoid
        if imports_from(folder) != folder.resolve():
            raise RuntimeError(f"python run in {folder} imports zforge from "
                               f"{imports_from(folder)}, not its own copy")
    work = old / "_compare"
    work.mkdir(exist_ok=True)
    results = []
    for source in sorted(EXAMPLES.glob("*.ni")):
        name = source.stem
        if games and name not in games:
            continue
        walk = EXAMPLES / f"{name}_walkthrough.txt"
        walk = walk if walk.exists() else None
        old_story, old_text = _build_and_play(old, source, walk, work / f"old_{name}")
        new_story, new_text = _build_and_play(PROJECT_ROOT, source, walk, work / f"new_{name}")
        r = GameResult(name, old_story is not None, new_story is not None,
                       walkthrough=walk is not None)
        if old_story and new_story:
            a, b = old_story.read_bytes(), new_story.read_bytes()
            r.same_story, r.old_size, r.new_size = a == b, len(a), len(b)
            r.same_transcript = old_text == new_text
            if walk and not r.same_transcript:
                r.first_difference = next(
                    (f"line {i + 1}: {x!r} -> {y!r}" for i, (x, y) in
                     enumerate(zip(old_text.splitlines(), new_text.splitlines(), strict=False))
                     if x != y),
                    f"lengths differ ({len(old_text.splitlines())} -> "
                    f"{len(new_text.splitlines())} lines)")
        results.append(r)
    return results


def report(commit: str, results: list[GameResult]) -> list[str]:
    lines = [f"compare {commit} -> working tree"]
    for r in results:
        if not (r.old_built and r.new_built):
            yes = {True: "yes", False: "NO"}
            state = f"compiles: old {yes[r.old_built]}, new {yes[r.new_built]}"
        else:
            story = ("story identical" if r.same_story
                     else f"story differs ({r.old_size} -> {r.new_size} bytes)")
            play = ("no walkthrough" if not r.walkthrough else
                    "walkthrough identical" if r.same_transcript
                    else f"WALKTHROUGH DIFFERS at {r.first_difference}")
            state = f"{story}; {play}"
        lines.append(f"  {'ok  ' if r.ok else 'FAIL'} {r.name}: {state}")
    return lines
