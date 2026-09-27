"""Run a story with no terminal: scripted input, a VirtualScreen, a step
limit. Used by the tests, the eval harness and zbuilder's run_story tool."""
from __future__ import annotations

from dataclasses import dataclass, field

from zforge.common.errors import ZForgeError
from zforge.vm.machine import ZMachine
from zforge.vm.screen import screen_for
from zforge.vm.screen.virtual import VirtualScreen, VirtualV6Screen


@dataclass
class PlayResult:
    """Result of a scripted game playthrough (used by tests and eval)."""
    reason: str                     # "quit", "scripted input exhausted", "error: ..."
    transcript: str                 # everything shown in the lower window + input
    screen: VirtualScreen
    vm: ZMachine
    steps: int
    error_trace: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if the playthrough succeeded without errors."""
        return not self.reason.startswith("error")


def play(story: bytes, script: list[str] | None = None, seed: int = 1,
         max_steps: int = 20_000_000, width: int = 80, height: int = 24) -> PlayResult:
    """Run a story with scripted input and no terminal (for testing and evaluation).

    §8.7 or §8.8: screen is chosen by the story's version byte.
    Returns a PlayResult with the transcript, final VM state, and reason for stopping.
    """
    # §8.7 or §8.8, according to the story's version byte
    screen = screen_for(story[0], VirtualScreen, VirtualV6Screen,
                        script=list(script or []), width=width, height=height)
    vm = ZMachine(story, screen, seed=seed)
    trace: list[str] = []
    try:
        reason = vm.run(max_steps=max_steps)
    except ZForgeError as exc:
        reason, trace = f"error: {exc}", vm.recent_trace()
    screen.flush()
    return PlayResult(reason, screen.transcript_text(), screen, vm, vm.steps, trace)
