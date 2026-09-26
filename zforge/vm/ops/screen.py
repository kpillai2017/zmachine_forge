"""§15 screen opcodes - thin wrappers over the §8 screen model."""
from __future__ import annotations

from zforge.common.numbers import to_signed


def op_split_window(vm, lines):
    """§15 split_window (VAR:234): upper window gets `lines` rows."""
    vm.screen.split_window(lines)


def op_set_window(vm, window):
    """§15 set_window (VAR:235): 0 = lower, 1 = upper."""
    vm.screen.set_window(window)


def op_erase_window(vm, window):
    """§15 erase_window (VAR:237): -1 unsplit + clear, -2 clear all."""
    vm.screen.erase_window(to_signed(window))


def op_erase_line(vm, value):
    """§15 erase_line (VAR:238): 1 = erase to the end of the line."""
    vm.screen.erase_line(value)


def op_set_cursor(vm, line, column):
    """§15 set_cursor (VAR:239): 1-based, upper window only in v5."""
    vm.screen.set_cursor(to_signed(line), to_signed(column))


def op_get_cursor(vm, array):
    """§15 get_cursor (VAR:240): write line, column words to array."""
    line, column = vm.screen.get_cursor()
    vm.mem.write_word(array, line)
    vm.mem.write_word(array + 2, column)


def op_set_text_style(vm, style):
    """§15 set_text_style (VAR:241): 0 roman, 1 reverse, 2 bold, 4 italic, 8 fixed."""
    vm.screen.set_text_style(style)


def op_buffer_mode(vm, flag):
    """§15 buffer_mode (VAR:242): 1 = word-wrap the lower window."""
    vm.screen.set_buffer_mode(bool(flag))


def op_set_colour(vm, foreground, background):
    """§15 set_colour (2OP:27): colour numbers from §8.3.1."""
    vm.screen.set_colour(foreground, background)


def op_set_true_colour(vm, foreground, background):
    """§15 set_true_colour (EXT:13): 15-bit colours - not supported, ignored
    (we do not set the Flags 1 true-colour capability)."""


def op_set_font(vm, font):
    """§15 set_font (EXT:4): store previous font, or 0 if unavailable."""
    vm.store_result(vm.screen.set_font(font))


def op_sound_effect(vm, number=1, effect=0, volume=0, routine=0):
    """§15 sound_effect (VAR:245): only the two bleeps (1, 2) are supported."""
    if number in (1, 2):
        vm.screen.beep()
