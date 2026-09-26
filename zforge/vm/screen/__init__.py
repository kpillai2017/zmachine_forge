"""§8 The screen model.

    base.py           GridScreen: THE model (windows, cursor, styles, wrap)
    virtual.py        VirtualScreen: GridScreen + scripted input (tests, CI)
    curses_screen.py  CursesScreen: GridScreen drawn with curses
    plain.py          PlainScreen: stream text to stdout (pipes, dumb terminals)
"""
from zforge.vm.screen.base import GridScreen, ScriptInput  # noqa: F401
