"""§15 The eighteen opcodes version 6 adds, and the v6 forms of five others.

Version 6 takes no opcode away, so everything in the other modules still
runs; these are the extras. Most are thin wrappers over the §8.8 window
model in vm/screen/v6.py, which is where the rules live.

Three of them ask for things a character terminal has not got:

  picture_data   §8.8.5   there is no picture file, so it reports "none
                          available" and does not branch - which is
                          exactly what the Standard says to do
  read_mouse     §15      no mouse: zeros, and no buttons held
  make_menu      §15      no menus: it does not branch (§15 "the branch
                          is made if the menu was created")

The Standard allows all three: §7.1.3 says pictures need not be
available, and Flags 1 / Flags 2 are cleared to say so (vm/machine.py).
"""
from __future__ import annotations

from zforge.common.errors import ZMachineError
from zforge.common.numbers import to_signed


# ------------------------------------------------------------------ windows
def op_get_wind_prop(vm, window, property_number):
    """§15 get_wind_prop (EXT:19): read one of the eighteen properties."""
    vm.store_result(vm.screen.get_window_property(to_signed(window), property_number) & 0xFFFF)


def op_put_wind_prop(vm, window, property_number, value):
    """§15 put_wind_prop (EXT:25): write one (§8.8.3.2 limits which)."""
    vm.screen.put_window_property(to_signed(window), property_number, to_signed(value))


def op_window_style(vm, window, flags, operation=0):
    """§15 window_style (EXT:18): set/or/clear/flip the four attributes."""
    vm.screen.window_style(to_signed(window), flags, operation)


def op_window_size(vm, window, y, x):
    """§15 window_size (EXT:17): resize a window, in units."""
    vm.screen.window_size(to_signed(window), to_signed(y), to_signed(x))


def op_move_window(vm, window, y, x):
    """§15 move_window (EXT:16): move it; what was printed stays put."""
    vm.screen.move_window(to_signed(window), to_signed(y), to_signed(x))


def op_scroll_window(vm, window, pixels):
    """§15 scroll_window (EXT:20): scroll any window, up or down."""
    vm.screen.scroll_window(to_signed(window), to_signed(pixels))


def op_set_margins(vm, left, right, window=-3):
    """§15 set_margins (EXT:8): left and right margins, in units."""
    vm.screen.set_margins(to_signed(left), to_signed(right), to_signed(window))


def op_mouse_window(vm, window):
    """§15 mouse_window (EXT:23): keep the pointer inside a window. There is
    no pointer on a character terminal; the choice is remembered so
    get_wind_prop and read_mouse stay consistent."""
    vm.mouse_window = to_signed(window)


def op_read_mouse(vm, array):
    """§15 read_mouse (EXT:22): y, x, buttons, menu word. With no mouse the
    pointer is reported at the top left of its window, no buttons held."""
    for i, value in enumerate((1, 1, 0, 0)):
        vm.mem.write_word(array + 2 * i, value)


def op_make_menu(vm, number, table):
    """§15 make_menu (EXT:27): branches if the menu was made. zforge has no
    menus (Flags 2 bit 8 is cleared), so it never branches."""
    vm.branch(False)


# ----------------------------------------------------------------- pictures
def op_picture_data(vm, picture_number, array):
    """§15 picture_data (EXT:6): branch if the picture exists. With no
    picture file: picture 0 writes 0 pictures and release 0 and does not
    branch; any other number does not branch either (§8.8.5)."""
    if picture_number == 0:
        vm.mem.write_word(array, 0)          # number of pictures available
        vm.mem.write_word(array + 2, 0)      # release number of the picture file
    vm.branch(False)


def op_draw_picture(vm, picture_number, y=0, x=0):
    """§15 draw_picture (EXT:5): nothing to draw (§8.8.5). A game should
    have asked picture_data first, which said there are none."""
    vm.warn(f"draw_picture {picture_number}: this interpreter has no pictures (§8.8.5)")


def op_erase_picture(vm, picture_number, y=0, x=0):
    """§15 erase_picture (EXT:7): as draw_picture - nothing is there."""
    vm.warn(f"erase_picture {picture_number}: this interpreter has no pictures (§8.8.5)")


def op_picture_table(vm, table):
    """§15 picture_table (EXT:28): a hint to cache pictures. Nothing to do."""


# -------------------------------------------------------------- user stacks
#
# §6.6: a "user stack" is a table of words in dynamic memory whose FIRST
# word holds the number of free slots. Values are pushed after it.
def op_push_stack(vm, value, stack):
    """§15 push_stack (EXT:24): push onto a user stack, branching if it
    fitted. An overflow is not an error - it just does not branch."""
    free = vm.mem.read_word(stack)
    if free == 0:
        vm.branch(False)
        return
    # Write the value at the end of used space; decrement the free count
    vm.mem.write_word(stack + 2 * free, value)
    vm.mem.write_word(stack, free - 1)
    vm.branch(True)


def op_pop_stack(vm, items, stack=0):
    """§15 pop_stack (EXT:21): throw away `items` values. With no stack
    given it is the game stack."""
    if stack == 0:
        # Pop from the game stack
        for _ in range(items):
            vm.frame.pop()
        return
    # Pop from a user stack: increment the free-slot counter
    vm.mem.write_word(stack, vm.mem.read_word(stack) + items)


def op_pull_v6(vm, stack=None):
    """§15 pull (VAR:233): in v6 it STORES the value it pulled, and may be
    given a user stack to pull from (§6.6)."""
    if stack is None:
        # Pop from the game stack and store
        vm.store_result(vm.frame.pop())
        return
    # Pop from a user stack: read from current top, increment free slots
    free = vm.mem.read_word(stack)
    value = vm.mem.read_word(stack + 2 * (free + 1))
    vm.mem.write_word(stack, free + 1)
    vm.store_result(value)


# ------------------------------------------------------------------ the rest
def op_print_form(vm, formatted_table):
    """§15 print_form (EXT:26): print a table written by output stream 3
    with formatting on: lines of (length word, that many characters),
    ending with a zero word."""
    address = formatted_table
    while True:
        # Read the length of the next formatted line
        length = vm.mem.read_word(address)
        if length == 0:
            # Zero word ends the buffer
            return
        address += 2
        # Read and output the characters
        text = "".join(vm.unicode.zscii_to_str(vm.mem.read_byte(address + i))
                       for i in range(length))
        vm.output(text + "\n")
        address += length


def op_buffer_screen(vm, mode):
    """§15 buffer_screen (EXT:29): ask the interpreter to hold screen
    updates back. zforge draws when it must, so it reports "nothing is
    buffered" (0) as §15 allows, and mode -1 (redraw now) redraws."""
    if to_signed(mode) == -1:
        vm.screen.render()
    vm.store_result(0)


def op_set_colour_v6(vm, foreground, background, window=-3):
    """§15 set_colour (2OP:27): v6 adds the window operand (§8.8.3.2.4)."""
    vm.screen.set_colour(foreground, background, to_signed(window))


def op_set_cursor_v6(vm, line, column=0, window=-3):
    """§15 set_cursor (VAR:239): v6 adds the window, and -1/-2 turn the
    cursor off and on again."""
    vm.screen.set_cursor(to_signed(line), to_signed(column), to_signed(window))


def op_set_font_v6(vm, font, window=-3):
    """§15 set_font (EXT:4): v6 adds the window operand."""
    vm.store_result(vm.screen.set_font(font, to_signed(window)))


def op_sound_effect_v6(vm, number=1, effect=0, volume=0, routine=0):
    """§15 sound_effect (VAR:245): the two bleeps work; sampled sounds do
    not (Flags 1 says so). A finished sound may call a routine, so one that
    never starts must not leave the game waiting: nothing is scheduled."""
    if number in (1, 2):
        vm.screen.beep()
    elif routine:
        raise ZMachineError("sound_effect asked for a sampled sound with a callback, "
                            "which this interpreter cannot play (§15)", vm.pc)
