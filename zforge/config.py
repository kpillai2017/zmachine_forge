"""Settings that choose WHAT zforge builds - for now, the target version.

The target is taken from the first of these that is set (proforma v2 §1):

    1. the command line          --target z8
    2. zforge.toml               target = "z8"   (in the current directory)
    3. the environment           ZFORGE_TARGET=z8
    4. the source itself         <VERSION ...> in a .zil file (default 5)

`resolve_target` returns the version AND where it came from, so the build
banner can say "target z8 (from --target)". Nobody has to guess why a file
came out as z7.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from zforge.common.errors import UnsupportedTarget
from zforge.common.versions import supported_versions

CONFIG_FILE = "zforge.toml"
ENV_VAR = "ZFORGE_TARGET"


@dataclass(frozen=True)
class Target:
    version: int
    origin: str               # "--target", "zforge.toml", "ZFORGE_TARGET" or "the source"

    def describe(self) -> str:
        return f"target z{self.version} (from {self.origin})"


def parse_target(text: str) -> int:
    """'z8', 'Z8' or '8' -> 8, for a version zforge can build."""
    cleaned = text.strip().lower().removeprefix("z")
    choices = ", ".join(f"z{v}" for v in supported_versions())
    if not cleaned.isdigit() or int(cleaned) not in supported_versions():
        raise UnsupportedTarget(f"Unsupported target {text.strip() or '?'} (choose {choices})")
    return int(cleaned)


def _from_config_file(directory: Path) -> str | None:
    path = directory / CONFIG_FILE
    if not path.exists():
        return None
    with path.open("rb") as f:
        data = tomllib.load(f)
    value = data.get("target", data.get("build", {}).get("target"))
    return str(value) if value is not None else None


def resolve_target(cli_value: str | None, source_default: int,
                   directory: Path | None = None) -> Target:
    """Apply the order in the module docstring."""
    if cli_value:
        return Target(parse_target(cli_value), "--target")
    configured = _from_config_file(directory or Path.cwd())
    if configured:
        return Target(parse_target(configured), CONFIG_FILE)
    if os.environ.get(ENV_VAR):
        return Target(parse_target(os.environ[ENV_VAR]), ENV_VAR)
    return Target(source_default, "the source")
