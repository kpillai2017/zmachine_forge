"""§11 The header: the first 64 bytes of every story file.

Offsets are named constants so code reads `H_DICTIONARY` rather than 0x08.
Only the fields that matter to a version-5 interpreter are listed.
"""
from __future__ import annotations

from dataclasses import dataclass

from zforge.common.errors import StoryFileError
from zforge.common.versions import VersionProfile, profile_for

HEADER_SIZE = 64

H_VERSION = 0x00          # Version number (1 to 6)
H_FLAGS1 = 0x01           # Flags 1 (v4+ meaning: interpreter capabilities)
H_RELEASE = 0x02          # Release number (word)
H_HIGH_MEMORY = 0x04      # Base of high memory
H_INITIAL_PC = 0x06       # Initial PC (byte address in v1-5)
H_DICTIONARY = 0x08       # Location of dictionary
H_OBJECTS = 0x0A          # Location of object table
H_GLOBALS = 0x0C          # Location of global variables table
H_STATIC_MEMORY = 0x0E    # Base of static memory
H_FLAGS2 = 0x10           # Flags 2 (word)
H_SERIAL = 0x12           # Serial code: 6 ASCII characters
H_ABBREVIATIONS = 0x18    # Location of abbreviations table
H_FILE_LENGTH = 0x1A      # Length of file / 4 (v4-5) or / 8 (v6+) (§11.1.6)
H_CHECKSUM = 0x1C         # Checksum of file
H_INTERPRETER_NUMBER = 0x1E
H_INTERPRETER_VERSION = 0x1F
H_SCREEN_HEIGHT_LINES = 0x20   # 255 = infinite
H_SCREEN_WIDTH_CHARS = 0x21
H_SCREEN_WIDTH_UNITS = 0x22    # word
H_SCREEN_HEIGHT_UNITS = 0x24   # word
# §11.1: v5 has width at $26 and height at $27; VERSION 6 SWAPS THEM.
H_FONT_WIDTH_UNITS = 0x26      # v5: width of a '0'
H_FONT_HEIGHT_UNITS = 0x27     # v5
H_FONT_HEIGHT_UNITS_V6 = 0x26  # v6: height
H_FONT_WIDTH_UNITS_V6 = 0x27   # v6: width of a '0'
H_ROUTINES_OFFSET = 0x28       # v6-7: R_O, packed routine addresses (§1.2.3)
H_STRINGS_OFFSET = 0x2A        # v6-7: S_O, packed string addresses (§1.2.3)
H_DEFAULT_BACKGROUND = 0x2C
H_DEFAULT_FOREGROUND = 0x2D
H_TERMINATING_CHARS = 0x2E     # address of terminating characters table
H_STANDARD_REVISION = 0x32     # two bytes: major, minor
H_ALPHABET_TABLE = 0x34        # 0 = default alphabets
H_EXTENSION_TABLE = 0x36       # header extension table

# Flags 1 bits (from version 4) - set by the INTERPRETER
F1_COLOURS = 1 << 0
F1_PICTURES = 1 << 1
F1_BOLD = 1 << 2
F1_ITALIC = 1 << 3
F1_FIXED = 1 << 4
F1_SOUND = 1 << 5
F1_TIMED_INPUT = 1 << 7

# Flags 2 bits - set by the GAME; the interpreter clears requests it can't meet
F2_TRANSCRIPT = 1 << 0
F2_FIXED_PITCH = 1 << 1
F2_PICTURES = 1 << 3
F2_UNDO = 1 << 4
F2_MOUSE = 1 << 5
F2_REDRAW = 1 << 2        # v6: the interpreter asks the game to redraw (§11)
F2_COLOURS = 1 << 6
F2_SOUND = 1 << 7
F2_MENUS = 1 << 8

# Header extension table word indexes (§11.1.7)
HX_MOUSE_X = 1
HX_MOUSE_Y = 2
HX_UNICODE_TABLE = 3
HX_FLAGS3 = 4

# The version-dependent rules (file-length divisor §11.1.6, packed
# addresses §1.2.3, ...) live in zforge/common/versions.py.


def word(data: bytes | bytearray, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


@dataclass(frozen=True)
class Header:
    """A read-only snapshot of the fields a loader needs."""
    version: int
    release: int
    high_memory: int
    initial_pc: int
    dictionary: int
    objects: int
    globals: int
    static_memory: int
    abbreviations: int
    file_length: int
    checksum: int
    serial: str
    alphabet_table: int
    extension_table: int
    terminating_chars: int
    routines_offset: int = 0         # R_O: only read where §1.2.3 uses it
    strings_offset: int = 0          # S_O

    @classmethod
    def parse(cls, data: bytes | bytearray) -> "Header":
        if len(data) < HEADER_SIZE:
            raise StoryFileError("Not a valid story file: shorter than the 64-byte header")
        version = data[H_VERSION]
        profile = profile_for(version)         # raises for unsupported versions
        h = cls(
            version=version,
            release=word(data, H_RELEASE),
            high_memory=word(data, H_HIGH_MEMORY),
            initial_pc=word(data, H_INITIAL_PC),
            dictionary=word(data, H_DICTIONARY),
            objects=word(data, H_OBJECTS),
            globals=word(data, H_GLOBALS),
            static_memory=word(data, H_STATIC_MEMORY),
            abbreviations=word(data, H_ABBREVIATIONS),
            file_length=word(data, H_FILE_LENGTH) * profile.file_length_divisor,
            checksum=word(data, H_CHECKSUM),
            serial=bytes(data[H_SERIAL:H_SERIAL + 6]).decode("latin-1"),
            alphabet_table=word(data, H_ALPHABET_TABLE),
            extension_table=word(data, H_EXTENSION_TABLE),
            terminating_chars=word(data, H_TERMINATING_CHARS),
            routines_offset=word(data, H_ROUTINES_OFFSET) if profile.uses_packing_offsets else 0,
            strings_offset=word(data, H_STRINGS_OFFSET) if profile.uses_packing_offsets else 0,
        )
        h.validate(len(data))
        return h

    @property
    def profile(self) -> VersionProfile:
        """The version rules for this story file (common/versions.py)."""
        return profile_for(self.version)

    @property
    def main_routine(self) -> int:
        """§5.4: in v6 the word at $06 is the PACKED address of the "main"
        routine the game starts by calling; in the others it is a byte
        address to start executing at (§5.5, `initial_pc`)."""
        return self.profile.unpack_routine(self.initial_pc, self.routines_offset)

    def font_size_bytes(self) -> tuple[int, int]:
        """(width byte, height byte) addresses: v6 swaps them (§11.1)."""
        if self.profile.font_bytes_swapped:
            return H_FONT_WIDTH_UNITS_V6, H_FONT_HEIGHT_UNITS_V6
        return H_FONT_WIDTH_UNITS, H_FONT_HEIGHT_UNITS

    def validate(self, actual_size: int) -> None:
        if self.static_memory < HEADER_SIZE or self.static_memory > actual_size:
            raise StoryFileError("Not a valid story file: bad static memory base")
        start = self.main_routine if self.profile.starts_with_main_routine else self.initial_pc
        if not HEADER_SIZE <= start < actual_size:
            raise StoryFileError("Not a valid story file: initial PC outside the file")
        if self.file_length and self.file_length > actual_size:
            raise StoryFileError(
                f"Not a valid story file: header says {self.file_length} bytes, "
                f"file has {actual_size} (truncated?)")


def compute_checksum(data: bytes | bytearray, file_length: int) -> int:
    """§15 verify: sum of all bytes from 0x40 to the file length, mod 0x10000."""
    return sum(data[HEADER_SIZE:file_length]) & 0xFFFF
