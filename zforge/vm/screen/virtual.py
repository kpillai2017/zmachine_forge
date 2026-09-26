"""VirtualScreen: the GridScreen with scripted input and no drawing.
Used by tests, the eval harness and `zforge run --ui virtual`."""
from __future__ import annotations

from zforge.vm.screen.base import GridScreen, ScriptInput
from zforge.vm.screen.v6 import V6Model


class VirtualScreen(GridScreen):
    def __init__(self, script: list[str] | None = None, width: int = 80, height: int = 24):
        super().__init__(width, height)
        self.input = ScriptInput(script or [])

    def _input_line(self, max_length: int) -> str:
        return self.input.next_line()

    def _input_key(self) -> int:
        return self.input.next_char()


class VirtualV6Screen(V6Model, VirtualScreen):
    """The same, with the §8.8 window model in front of it (v6 stories)."""
