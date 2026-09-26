"""Comparing two transcripts, response by response.

The Advent case plays the same commands on our I7-lite build and on the real
Inform 7 game and asks that the player sees the same thing. The comparison
is exact - every line and blank line, as wrapped on the same 80-column
screen (the same text always wraps the same way) - with one allowance:

* the banner goes, with the blank lines around it: its serial number and
  compiler name differ, and a story may print it before or after its intro.
"""

from __future__ import annotations

import re


def responses(transcript: str, commands: list[str], banner: list[str]) -> list[list[str]]:
    """[the text before the first command, the response to each command].
    A command's echo is '>command' (or '  command' after a two-space
    prompt, as at a yes/no question)."""
    patterns = [re.compile(p) for p in banner]
    lines = ["\x00" if any(p.fullmatch(line.rstrip()) for p in patterns) else line
             for line in transcript.split("\n")]
    text = re.sub(r"\n*(?:\x00\n*)+", "\n\n", "\n".join(lines)).lstrip("\n")
    out = []
    for command in commands:
        echo = re.search(r"(?m)^(?:>| {2})" + re.escape(command) + r"[ \t]*$", text)
        if echo is None:
            out.append(lines_of(text))
            text = ""
            continue
        out.append(lines_of(text[:echo.start()]))
        text = text[echo.end():]
    out.append(lines_of(text))
    return out


def lines_of(block: str) -> list[str]:
    """The block's lines, trailing spaces gone and the next prompt ('>')
    dropped. Blank lines are kept."""
    block = re.sub(r"\n>[ \t]*$", "\n", block).strip("\n")
    return [line.rstrip() for line in block.split("\n")]


def differences(commands: list[str], real: list[list[str]], ours: list[list[str]]) -> list[str]:
    """One line per response that differs: which command, and the first line that differs."""
    problems = []
    for i, (r, o) in enumerate(zip(real, ours, strict=True)):
        if r != o:
            where = "the opening text" if i == 0 else f"'>{commands[i - 1]}'"
            first = next(n for n in range(max(len(r), len(o)))
                         if (r[n] if n < len(r) else None) != (o[n] if n < len(o) else None))
            want = r[first] if first < len(r) else "(nothing)"
            got = o[first] if first < len(o) else "(nothing)"
            problems.append(f"{where}: Inform 7 printed {want!r}, we printed {got!r}")
    return problems
