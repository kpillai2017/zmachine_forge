"""§8 The screen model.

    base.py           GridScreen: THE v5 model (two windows, cursor, wrap)
    v6.py             V6Model: the §8.8 model (eight windows), in front of it
    virtual.py        VirtualScreen: GridScreen + scripted input (tests, CI)
    curses_screen.py  CursesScreen: GridScreen drawn with curses
    plain.py          PlainScreen: stream text to stdout (pipes, dumb terminals)

Each renderer has a v6 twin (VirtualV6Screen, ...): the same input and
drawing, with V6Model's window methods in front. `screen_for` picks one.
"""
from zforge.vm.screen.base import GridScreen, ScriptInput  # noqa: F401
from zforge.vm.screen.v6 import V6Model  # noqa: F401


def screen_for(version: int, plain: "type", v6: "type", **kwargs):
    """The screen class a story of this version needs (§8.7 versus §8.8)."""
    from zforge.common.versions import profile_for
    return (v6 if profile_for(version).windows > 2 else plain)(**kwargs)
