"""Tool 5: workspace-scoped file I/O. Agents can only touch files inside
the project folder, and never the spec cache, stories or .env."""
from __future__ import annotations

import re
from pathlib import Path

from zbuilder.paths import PROJECT_ROOT

FORBIDDEN = ("spec/cache", "stories", ".env", ".git", "build/state.json",
             "tests/golden")        # golden hashes: humans only (zbuilder golden --record)


class FileToolError(Exception):
    pass


def _resolve(relative: str) -> Path:
    path = (PROJECT_ROOT / relative).resolve()
    if PROJECT_ROOT not in path.parents and path != PROJECT_ROOT:
        raise FileToolError(f"{relative}: outside the project folder")
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    if any(rel == f or rel.startswith(f + "/") for f in FORBIDDEN):
        raise FileToolError(f"{relative}: agents may not write here")
    return path


def read_file(relative: str, max_chars: int = 60_000) -> str:
    path = (PROJECT_ROOT / relative).resolve()
    if PROJECT_ROOT not in path.parents:
        raise FileToolError(f"{relative}: outside the project folder")
    if not path.exists():
        return ""
    return path.read_text()[:max_chars]


def write_file(relative: str, content: str) -> Path:
    path = _resolve(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def list_files(relative_dir: str, pattern: str = "*.py") -> list[str]:
    base = (PROJECT_ROOT / relative_dir).resolve()
    if base.is_file():
        return [relative_dir]
    return sorted(p.relative_to(PROJECT_ROOT).as_posix() for p in base.rglob(pattern)
                  if "__pycache__" not in p.parts)


FENCE = re.compile(r"```file:(?P<path>[^\n`]+)\n(?P<body>.*?)\n```", re.S)


def parse_file_blocks(reply: str) -> dict[str, str]:
    """Implementer output protocol: ```file:path ... ``` blocks."""
    return {m.group("path").strip(): m.group("body") + "\n" for m in FENCE.finditer(reply)}
