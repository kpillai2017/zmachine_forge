"""§7 Output streams.

    1  the screen                         (on by default)
    2  the transcript (a file)            (mirrors bit 0 of Flags 2, §7.3)
    3  a table in memory                  (nests up to 16 deep, §7.1.2.1)
    4  the command script (player input)  (§7.1.2.3)

While stream 3 is selected, text goes ONLY to the table (§7.1.2.2).
"""
from __future__ import annotations

from dataclasses import dataclass

from zforge.common.errors import ZMachineError
from zforge.common.memory import Memory

MAX_MEMORY_STREAMS = 16


@dataclass
class MemoryStream:
    """A memory-based output stream (stream 3): counts characters written to a table."""
    table: int
    count: int = 0


class OutputStreams:
    """Manage §7 output streams: screen, transcript, memory, and command script."""
    def __init__(self, mem: Memory, screen, text_to_zscii, transcript_path=None):
        """Initialise output streams with access to memory, screen, and transcript path."""
        self.mem = mem
        self.screen = screen
        self.text_to_zscii = text_to_zscii
        self.screen_on = True
        self.transcript_on = False
        self.transcript_path = transcript_path
        self._transcript_file = None
        self.memory_streams: list[MemoryStream] = []
        self.command_script = None

    # -- selecting (§15 output_stream) ---------------------------------------
    def select(self, number: int, table: int = 0) -> None:
        """§15 output_stream: select or deselect an output stream.

        Positive numbers turn a stream on, negative turn it off.
        Stream 3 (memory) nests up to 16 deep (§7.1.2.1).
        """
        # Stream 1: the screen
        if number == 1:
            self.screen_on = True
        elif number == -1:
            self.screen_on = False
        # Stream 2: the transcript (file)
        elif number == 2:
            self.set_transcript(True)
        elif number == -2:
            self.set_transcript(False)
        # Stream 3: memory table (can nest)
        elif number == 3:
            if len(self.memory_streams) >= MAX_MEMORY_STREAMS:
                raise ZMachineError("Output stream 3 nested more than 16 deep (§7.1.2.1)")
            self.memory_streams.append(MemoryStream(table))
        elif number == -3:
            if self.memory_streams:
                stream = self.memory_streams.pop()
                self.mem.write_word(stream.table, stream.count)   # length word
        elif number in (4, -4):
            pass   # command script: we record input via --transcript instead

    def set_transcript(self, on: bool) -> None:
        """Enable or disable transcript output to a file."""
        self.transcript_on = on
        if on and self._transcript_file is None and self.transcript_path:
            self._transcript_file = open(self.transcript_path, "a", encoding="utf-8")

    # -- writing ---------------------------------------------------------------
    def write(self, text: str, window: int = 0) -> None:
        """Write text to the selected output stream(s).

        If stream 3 is active, write ONLY to it (§7.1.2.2).
        Otherwise write to screen (if on) and transcript (if on).
        """
        # Stream 3 (memory) is exclusive: write only to it
        if self.memory_streams:
            stream = self.memory_streams[-1]
            for code in self.text_to_zscii(text):
                self.mem.write_byte(stream.table + 2 + stream.count, code)
                stream.count += 1
            return
        # Write to screen (stream 1) if it's on
        if self.screen_on:
            self.screen.print(text)
        # Write to transcript (stream 2) if it's on and this is from the lower window
        if self.transcript_on and self._transcript_file and window == 0:
            self._transcript_file.write(text)

    def echo_input(self, text: str) -> None:
        """Player input is copied to the transcript (§7.1.2.3)."""
        if self.transcript_on and self._transcript_file:
            self._transcript_file.write(text + "\n")

    def close(self) -> None:
        """Close the transcript file if it is open."""
        if self._transcript_file:
            self._transcript_file.close()
            self._transcript_file = None
