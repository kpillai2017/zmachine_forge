"""`zforge run --ui plain` on version 6 - through the real CLI entry point.

The plain screen is what `run` uses when stdout is not a terminal (a pipe,
a file, CI), so these are the commands a user types. Before this file,
v6 plain play crashed at the first prompt (the v6 model's input hooks were
missing) and streamed the status line's padding as text; the evals did not
notice because they play v6 through the virtual screen."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from zforge.cli import main

ROOT = Path(__file__).resolve().parent.parent


def compile_to(tmp_path: Path, source: str, target: str) -> Path:
    story = tmp_path / f"{Path(source).stem}.{target}"
    assert main(["compile", str(ROOT / source), "--target", target, "-o", str(story)]) == 0
    return story


def run_plain(story: Path, commands: list[str], tmp_path: Path, capsys) -> str:
    script = tmp_path / "commands.txt"
    script.write_text("\n".join(commands) + "\n")
    capsys.readouterr()                                   # drop compile's output
    assert main(["run", str(story), "--ui", "plain", "--script", str(script)]) == 0
    return capsys.readouterr().out


def test_the_same_story_prints_the_same_on_z5_z6_z7_and_z8(tmp_path, capsys):
    commands = ["look", "inventory", "s", "take cloak", "quit", "y"]
    outputs = {}
    for target in ("z5", "z6", "z7", "z8"):
        story = compile_to(tmp_path, "examples/cloak.ni", target)
        outputs[target] = run_plain(story, commands, tmp_path, capsys)
    assert "| Foyer of the Opera House" in outputs["z6"]       # the status line, shown as on v5
    assert outputs["z6"] == outputs["z5"]
    assert outputs["z7"] == outputs["z5"]
    assert outputs["z8"] == outputs["z5"]


def test_z6_reads_commands_piped_to_stdin(tmp_path, capsys, monkeypatch):
    story = compile_to(tmp_path, "examples/cloak.ni", "z6")
    monkeypatch.setattr(sys, "stdin", io.StringIO("inventory\nquit\ny\n"))
    capsys.readouterr()
    assert main(["run", str(story), "--ui", "plain"]) == 0
    assert "You are carrying:" in capsys.readouterr().out


def test_the_v6_demo_shows_painted_windows_as_rows_and_understands_every_command(tmp_path, capsys):
    story = compile_to(tmp_path, "examples/v6_windows.zil", "z6")
    out = run_plain(story, ["scroll", "move", "wrap", "quit"], tmp_path, capsys)
    lines = out.split("\n")
    # Window 2 (the panel) is painted, so it is shown as rows, not streamed:
    assert "| +------------------------------+" in lines
    assert "| | window 2                     |" in lines
    assert "+||" not in out                               # the old run-on stream
    # ... and shown again when it moves (§8.8.3.2: WINPOS).
    assert "| | at (3,46) size 9x32          |" in lines
    assert "| | at (4,46) size 9x32          |" in lines
    # Every command is understood, not just the first (§15 read, byte 1).
    assert "Window 0 scrolled up one line." in out
    assert "The panel moved down one line" in out
    assert "Wrapping is now off." in out


def test_the_help_names_every_version(capsys):
    for command in (["--help"], ["run", "--help"], ["compile", "--help"]):
        with pytest.raises(SystemExit):
            main(command)
        out = capsys.readouterr().out
        assert "v5 " not in out and ".z5 story" not in out
    assert "z5, z6, z7 or z8" in out
