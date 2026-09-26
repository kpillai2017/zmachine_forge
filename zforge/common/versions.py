"""VersionProfile: EVERY rule that differs between story-file versions,
in one readable place (proforma v2, Tier 5).

Everything else in zforge asks a profile instead of testing a version
number. (readability-audit checks that `version ==` appears nowhere else,
apart from the opcode tables in common/opcodes.py.)

The rules, as the Standard states them:

  rule                     v5          v6            v7            v8
  packed routine P  §1.2.3 4P          4P + 8*R_O    4P + 8*R_O    8P
  packed string  P  §1.2.3 4P          4P + 8*S_O    4P + 8*S_O    8P
  file length /     §11.1.6  4          8             8             8
  max story size    §1.1.4 256K        512K          512K          512K
  execution starts  §5.4-5 PC at $06   CALL main $06 PC at $06     PC at $06
  opcode set        §1/§14 v5          v6            v5            v5
  font size bytes   §11.1  $26 w, $27 h $26 h, $27 w  $26 w, $27 h  $26 w, $27 h
  screen model      §8     two windows  eight (§8.8)  two windows   two windows
  redraw request    §11    -           Flags 2 bit 2  -             -

(R_O and S_O are the routine and string offsets in header words $28/$2a.)
§1 ends: "Versions 7 and 8 are identical to Version 5 except as stated at
1.1.4 and 1.2.3" - which is why v7/v8 differ from v5 only in the first four
rows.

Registered: 5 (Tier 5), 7 and 8 (Tier 6), 6 (Tier 8, with its window model
and its 18 extra opcodes - see vm/screen/v6.py and ADR-030).
"""
from __future__ import annotations

from dataclasses import dataclass

from zforge.common.errors import LayoutError, StoryFileError, UnsupportedVersion


@dataclass(frozen=True)
class VersionProfile:
    version: int
    packed_scale: int              # §1.2.3: the multiplier of P (4 or 8)
    uses_packing_offsets: bool     # §1.2.3: v6/v7 add 8*R_O or 8*S_O
    file_length_divisor: int       # §11.1.6: header $1a holds length / this
    max_story_size: int            # §1.1.4: in bytes
    starts_with_main_routine: bool  # §5.4 (v6) versus §5.5 (the others)
    opcode_table: int              # §1/§14: whose opcode table this version uses
    font_bytes_swapped: bool = False   # §11.1: v6 puts height at $26, width at $27
    windows: int = 2                   # §8.7 two windows; §8.8 v6 has eight
    # §11 Flags 2 bit 2, "Int sets to request screen redraw", is marked v6
    # only; the §11 remarks suggest setting it "after, for example, resizing".
    redraw_request_bit: bool = False

    # ------------------------------------------------ packed addresses §1.2.3
    def unpack_routine(self, packed: int, routines_offset: int = 0) -> int:
        """Byte address of the routine at packed address `packed`."""
        return self.packed_scale * packed + self._offset(routines_offset)

    def unpack_string(self, packed: int, strings_offset: int = 0) -> int:
        """Byte address of the string at packed address `packed`."""
        return self.packed_scale * packed + self._offset(strings_offset)

    def pack_routine(self, address: int, routines_offset: int = 0) -> int:
        """The inverse of unpack_routine, used by the assembler."""
        return self._pack(address, routines_offset)

    def pack_string(self, address: int, strings_offset: int = 0) -> int:
        """The inverse of unpack_string, used by the assembler."""
        return self._pack(address, strings_offset)

    @property
    def code_alignment(self) -> int:
        """Routines and strings must start where a packed address can point:
        a multiple of the packing scale (§1.2.3)."""
        return self.packed_scale

    @property
    def area_alignment(self) -> int:
        """Where the routine area and the string area begin. With offsets
        (v6/v7) each area starts at 8 * R_O or 8 * S_O, so on a multiple of 8."""
        return 8 if self.uses_packing_offsets else self.code_alignment

    def _offset(self, header_offset: int) -> int:
        return 8 * header_offset if self.uses_packing_offsets else 0

    def _pack(self, address: int, header_offset: int) -> int:
        relative = address - self._offset(header_offset)
        if relative < 0 or relative % self.packed_scale:
            raise LayoutError(f"address 0x{address:x} cannot be packed in version "
                              f"{self.version} (scale {self.packed_scale})")
        packed = relative // self.packed_scale
        if packed > 0xFFFF:              # a packed address is one 16-bit word
            raise LayoutError(f"address 0x{address:x} is out of reach of a packed address "
                              f"in version {self.version} (it can reach "
                              f"{self.packed_scale * 0x10000 // 1024}K past its offset)")
        return packed

    def larger_versions(self) -> list[int]:
        """Registered versions with the same opcode set that allow bigger
        stories - what to suggest when a story is too large."""
        return [v for v, p in sorted(PROFILES.items())
                if p.opcode_table == self.opcode_table and p.max_story_size > self.max_story_size]


PROFILES: dict[int, VersionProfile] = {
    5: VersionProfile(version=5, packed_scale=4, uses_packing_offsets=False,
                      file_length_divisor=4, max_story_size=256 * 1024,
                      starts_with_main_routine=False, opcode_table=5),
    # §1: "Versions 7 and 8 are identical to Version 5 except as stated at
    # 1.1.4 and 1.2.3" - only the size limit and the packed addresses.
    # §5.4 the game starts by CALLing the "main" routine whose packed address
    # is in $06; §1.2.3 packing uses the offsets; §8.8 the window model.
    6: VersionProfile(version=6, packed_scale=4, uses_packing_offsets=True,
                      file_length_divisor=8, max_story_size=512 * 1024,
                      starts_with_main_routine=True, opcode_table=6,
                      font_bytes_swapped=True, windows=8, redraw_request_bit=True),
    7: VersionProfile(version=7, packed_scale=4, uses_packing_offsets=True,
                      file_length_divisor=8, max_story_size=512 * 1024,
                      starts_with_main_routine=False, opcode_table=5),
    8: VersionProfile(version=8, packed_scale=8, uses_packing_offsets=False,
                      file_length_divisor=8, max_story_size=512 * 1024,
                      starts_with_main_routine=False, opcode_table=5),
}

# The version zforge builds when nothing else is asked for (ADR-021).
DEFAULT_VERSION = 5


def supported_versions() -> list[int]:
    return sorted(PROFILES)


def _supported_phrase() -> str:
    versions = supported_versions()
    if len(versions) == 1:
        return f"zforge implements version {versions[0]} only"
    return ("zforge runs versions " + ", ".join(map(str, versions[:-1]))
            + f" and {versions[-1]}")


def profile_for(version: int) -> VersionProfile:
    """The profile of a story-file version, or a clear error (§11.1.1: the
    version number is the byte at $00)."""
    if version in PROFILES:
        return PROFILES[version]
    if 1 <= version <= 8:
        raise UnsupportedVersion(f"Unsupported story version {version}: {_supported_phrase()}")
    raise StoryFileError(f"Not a valid story file: version byte is {version}")
