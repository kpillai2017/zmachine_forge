"""Tier 9: `zforge run --ui curses` in a REAL terminal - a pseudo-terminal
made by pty.fork(), so this runs anywhere Unix does, with no screen attached.
Nothing is mocked: the child is the real CLI, real curses, real signals.

It plays, resizes the terminal (TIOCSWINSZ + SIGWINCH, what a terminal
emulator does when you drag its corner), and then kills zforge the two ways
a user's session dies - `kill` (SIGTERM) and a closed window (SIGHUP). Each
time zforge must exit normally and put the terminal back: curses' endwin
leaves the alternate screen with xterm's rmcup, ESC [ ? 1049 l.

Measured without zforge's signal handlers: SIGHUP killed Python and left
the terminal in curses mode (this test fails); SIGTERM was cleaned up by
ncurses itself, but around zforge's own shutdown rather than through it."""
from __future__ import annotations

import os
import select
import shutil
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("curses")
pty = pytest.importorskip("pty")
fcntl = pytest.importorskip("fcntl")
termios = pytest.importorskip("termios")

from zforge.compiler.driver import compile_zil       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LEAVE_ALTERNATE_SCREEN = b"\x1b[?1049l"          # `tput -T xterm rmcup`


def _have_xterm_terminfo() -> bool:
    tput = shutil.which("tput")
    if not tput:
        return False
    done = subprocess.run([tput, "-T", "xterm", "rmcup"], capture_output=True)
    return done.returncode == 0 and done.stdout == LEAVE_ALTERNATE_SCREEN


pytestmark = pytest.mark.skipif(
    not hasattr(os, "fork") or not _have_xterm_terminfo(),
    reason="needs fork() and the xterm terminfo entry")


def window_size(rows: int, columns: int) -> bytes:
    return struct.pack("HHHH", rows, columns, 0, 0)


def spawn(story: Path, rows: int = 24, columns: int = 80) -> tuple[int, int]:
    """Start `zforge run story --ui curses` on a new pseudo-terminal."""
    pid, fd = pty.fork()
    if pid == 0:                                 # the child: the pty is its terminal
        try:
            fcntl.ioctl(0, termios.TIOCSWINSZ, window_size(rows, columns))
            os.chdir(ROOT)
            env = dict(os.environ, TERM="xterm")
            os.execve(sys.executable, [sys.executable, "-m", "zforge", "run", str(story),
                                       "--ui", "curses"], env)
        finally:
            os._exit(127)
    return pid, fd


def read_until(fd: int, needle: bytes, timeout: float = 20.0) -> bytes:
    """Read the terminal until `needle` has been drawn."""
    out = b""
    deadline = time.monotonic() + timeout
    while needle not in out:
        left = deadline - time.monotonic()
        if left <= 0:
            raise AssertionError(f"timed out waiting for {needle!r}; last output {out[-200:]!r}")
        ready, _, _ = select.select([fd], [], [], left)
        if ready:
            try:
                chunk = os.read(fd, 65536)
            except OSError:                      # EIO: the child has closed the terminal
                chunk = b""
            if not chunk:
                raise AssertionError(f"terminal closed before {needle!r}; got {out[-200:]!r}")
            out += chunk
    return out


def wait_for_exit(pid: int, timeout: float = 20.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        done, status = os.waitpid(pid, os.WNOHANG)
        if done:
            return status
        time.sleep(0.05)
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)
    raise AssertionError("zforge did not exit")


def kill_and_check_the_terminal_is_restored(pid: int, fd: int, how: int) -> None:
    os.kill(pid, how)
    read_until(fd, LEAVE_ALTERNATE_SCREEN)       # endwin ran
    status = wait_for_exit(pid)
    assert os.WIFEXITED(status), "killed by the signal: the terminal was left in curses mode"
    assert os.WEXITSTATUS(status) == 0
    os.close(fd)


def build(tmp_path: Path, name: str, version: int) -> Path:
    story = tmp_path / f"{name}.z{version}"
    source = (ROOT / "examples" / f"{name}.zil").read_text()
    story.write_bytes(compile_zil(source, f"{name}.zil", version).story)
    return story


def test_play_resize_and_kill(tmp_path):
    pid, fd = spawn(build(tmp_path, "cloak", 5))
    read_until(fd, b"Foyer")
    os.write(fd, b"inventory\r")
    read_until(fd, b"carrying")
    fcntl.ioctl(fd, termios.TIOCSWINSZ, window_size(30, 100))     # drag the corner
    os.kill(pid, signal.SIGWINCH)
    os.write(fd, b"help\r")
    read_until(fd, b"Try LOOK")                   # still playing, at the new size
    kill_and_check_the_terminal_is_restored(pid, fd, signal.SIGTERM)


def test_a_v6_story_and_a_closed_window(tmp_path):
    pid, fd = spawn(build(tmp_path, "v6_windows", 6))
    read_until(fd, b"demo")
    os.write(fd, b"xyzzy\r")
    read_until(fd, b"WRAP or QUIT")
    kill_and_check_the_terminal_is_restored(pid, fd, signal.SIGHUP)
