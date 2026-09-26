"""Robust project paths (proforma Section 11: resolve paths from the project dir)."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = PROJECT_ROOT / "spec"
SPEC_CACHE = SPEC_DIR / "cache"
SPEC_SECTIONS = SPEC_DIR / "sections"
SPEC_FACTS = SPEC_DIR / "facts"
OPCODES_JSON = SPEC_DIR / "opcodes.json"
SPEC_INDEX = SPEC_DIR / "index.json"
BUILD_DIR = PROJECT_ROOT / "build"
STATE_FILE = BUILD_DIR / "state.json"
LOG_DIR = BUILD_DIR / "logs"
TASK_DIR = BUILD_DIR / "tasks"
PLAN_DIR = BUILD_DIR / "plan"
DOCS_DIR = PROJECT_ROOT / "docs"
STORIES_DIR = PROJECT_ROOT / "stories"

DEFAULT_SPEC_URL = "https://inform-fiction.org/zmachine/standards/z1point1/index.html"
ALLOWED_HOSTS = {"inform-fiction.org", "www.inform-fiction.org",
                 "ifarchive.org", "www.ifarchive.org", "mirror.ifarchive.org"}
