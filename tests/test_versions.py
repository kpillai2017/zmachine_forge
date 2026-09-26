"""VersionProfile and the per-version opcode tables (proforma v2, Tier 5).

The profile values are checked against the SPEC TEXT where the cached
sections are available, so nobody can type a Z-machine fact from memory.
"""
import json
import re

import pytest

from tests.conftest import ROOT
from zforge.common.errors import StoryFileError, UnsupportedVersion
from zforge.common.opcodes import OPCODES, V6_OPCODES, names_for, table_for
from zforge.common.versions import PROFILES, VersionProfile, profile_for

SECTIONS = ROOT / "spec" / "sections"


# ------------------------------------------------------------ the profile
def test_v5_profile_follows_the_standard():
    p = profile_for(5)
    assert p.unpack_routine(0x0123) == 4 * 0x0123            # §1.2.3: 4P
    assert p.unpack_string(0x0123) == 4 * 0x0123
    assert p.file_length_divisor == 4                        # §11.1.6
    assert p.max_story_size == 256 * 1024                    # §1.1.4
    assert p.starts_with_main_routine is False               # §5.5
    assert p.code_alignment == 4


@pytest.mark.parametrize("version", sorted(PROFILES))
def test_pack_is_the_inverse_of_unpack(version):
    p = profile_for(version)
    for address in (0x400, 0x1000, 0x3FFF8):
        assert p.unpack_routine(p.pack_routine(address)) == address
        assert p.unpack_string(p.pack_string(address)) == address


def test_misaligned_address_cannot_be_packed():
    with pytest.raises(ValueError, match="cannot be packed"):
        profile_for(5).pack_routine(0x401)


def test_offsets_only_matter_where_the_standard_uses_them():
    """§1.2.3: only versions 6 and 7 add 8*R_O / 8*S_O."""
    v67 = VersionProfile(version=7, packed_scale=4, uses_packing_offsets=True,
                         file_length_divisor=8, max_story_size=512 * 1024,
                         starts_with_main_routine=False, opcode_table=5)
    assert v67.unpack_routine(0x100, routines_offset=0x10) == 4 * 0x100 + 8 * 0x10
    assert v67.pack_string(4 * 0x100 + 8 * 0x20, strings_offset=0x20) == 0x100
    assert profile_for(5).unpack_routine(0x100, routines_offset=0x10) == 4 * 0x100


def test_unsupported_versions_are_refused_clearly():
    with pytest.raises(UnsupportedVersion, match="Unsupported story version 3"):
        profile_for(3)
    with pytest.raises(StoryFileError, match="version byte is 0"):
        profile_for(0)


# --------------------------------------------- the profile vs the spec text
def _section(name: str) -> str:
    path = SECTIONS / f"{name}.txt"
    if not path.exists():
        pytest.skip("spec/sections not built (python -m zbuilder spec)")
    return re.sub(r"\s+", " ", path.read_text())


def test_divisor_and_size_come_from_the_spec_text():
    sect11 = _section("sect11")
    assert "4 for Versions 4 to 5 or 8 for Versions 6 and later" in sect11   # §11.1.6
    sect01 = _section("sect01")
    assert "V1-3 V4-5 V6-8 128 256 512" in sect01                             # §1.1.4
    assert "4P Versions 4 and 5" in sect01                                    # §1.2.3
    assert "8P Version 8" in sect01
    assert "Versions 7 and 8 are identical to Version 5" in sect01            # §1


# ------------------------------------------------ opcode tables per version
def _spec_json() -> dict:
    return json.loads((ROOT / "spec" / "opcodes.json").read_text())


def test_opcode_counts_per_version_match_the_spec():
    counts = _spec_json()["counts"]
    assert counts == {"5": 98, "6": 116, "7": 98, "8": 98}
    for v in (5, 6, 7, 8):
        assert len(table_for(v)) == counts[str(v)], v


@pytest.mark.parametrize("version", [5, 6, 7, 8])
def test_each_version_table_matches_the_spec_json(version):
    spec = {(e["kind"], e["number"]): e for e in _spec_json()["all_versions"]
            if version in e["versions"]}
    ours = table_for(version)
    assert spec.keys() == ours.keys()
    for key, op in ours.items():
        e = spec[key]
        assert (e["name"], e["store"], e["branch"], e["text"]) == \
            (op.name, op.store, op.branch, op.text), key


def test_v7_and_v8_use_the_v5_table():
    """§1: versions 7 and 8 differ from 5 only in §1.1.4 and §1.2.3."""
    assert table_for(7) == table_for(5) == table_for(8)
    assert ("EXT", 18) not in table_for(8)          # window_style is v6-only


def test_v6_changes_and_additions():
    v6 = table_for(6)
    assert v6[("VAR", 9)].store is True             # §15 pull: v6 form stores
    assert table_for(5)[("VAR", 9)].store is False
    assert v6[("EXT", 5)].name == "draw_picture"
    assert v6[("EXT", 29)].name == "buffer_screen"  # Standard 1.1
    assert names_for(6)["get_wind_prop"].store
    new = [op for op in V6_OPCODES if (op.kind, op.number) not in table_for(5)]
    changed = [op.name for op in V6_OPCODES if (op.kind, op.number) in table_for(5)]
    assert len(new) == 116 - 98 == 18               # EXT:5-8 and EXT:16-29
    assert sorted(changed) == ["erase_line", "output_stream", "pull", "set_colour",
                               "set_cursor", "set_font", "set_true_colour"]


def test_v5_table_is_unchanged():
    assert table_for(5) == {(op.kind, op.number): op for op in OPCODES}


# --------------------------------------------- version logic lives in ONE place
def test_no_version_comparisons_outside_the_profile():
    pattern = re.compile(r"version\s*(==|!=|<=|>=|<|>)\s*\d|\.version\s*(==|!=|<|>)")
    allowed = {"common/versions.py", "common/opcodes.py"}
    offenders = []
    for path in (ROOT / "zforge").rglob("*.py"):
        rel = path.relative_to(ROOT / "zforge").as_posix()
        if rel in allowed:
            continue
        for n, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#", 1)[0]
            if pattern.search(code):
                offenders.append(f"zforge/{rel}:{n}: {line.strip()}")
    assert not offenders, "version logic belongs in VersionProfile:\n" + "\n".join(offenders)


# ------------------------------------------------ Tier 6: v7/v8 layouts
def _big_story_source(n: int = 200, chars: int = 1000) -> str:
    """n routines, each holding ~chars of INLINE text (routine area) and
    printing a distinct ~chars STRING (string area): ~270K in total."""
    lines = [".main MAIN", ".routine MAIN", f"    call_vn R{n - 1}", "    quit", ".end"]
    for k in range(n):
        body = f"routine {k} " + "abcdefghij " * (chars // 11)
        text = f"string {k} " + "klmnopqrst " * (chars // 11)
        lines += [f".routine R{k}", f'    print "{body}"', f'    print_paddr "{text}"',
                  "    rtrue", ".end"]
    return "\n".join(lines) + "\n"


def test_size_limit_v5_refuses_a_big_story_with_a_hint():
    from zforge.asm.assembler import assemble
    from zforge.common.errors import LayoutError
    with pytest.raises(LayoutError, match=r"v5 allows at most 256K \(§1.1.4\) - try --target z7"):
        assemble(_big_story_source(), "big.zas", 5)


@pytest.mark.parametrize("version", [7, 8])
def test_size_limit_v7_v8_build_and_reach_the_far_end(version):
    """§1.1.4: 512K. The last routine and its string lie beyond 256K, so
    they are reachable only through 8P (v8) or the offsets (v7)."""
    from zforge.asm.assembler import assemble
    from zforge.vm.machine import ZMachine
    from zforge.vm.screen.virtual import VirtualScreen
    story = assemble(_big_story_source(), "big.zas", version)
    assert len(story) > 256 * 1024
    screen = VirtualScreen()
    ZMachine(story, screen).run()
    text = "".join(screen.transcript)
    assert "routine 199 abcdefghij" in text and "string 199 klmnopqrst" in text


def test_a_packed_address_must_fit_in_16_bits():
    from zforge.common.errors import LayoutError
    with pytest.raises(LayoutError, match="out of reach"):
        profile_for(5).pack_routine(4 * 0x10000)


def test_v7_offsets_never_pack_anything_to_zero():
    """§6.4.3: calling packed address 0 does nothing, so R_O/S_O are chosen
    one 8-byte step before each area and the first item packs to P = 2."""
    from zforge.asm.assembler import assemble
    from zforge.common.header import Header
    story = assemble((ROOT / "tests/samples/hello.zas").read_text(), "hello.zas", 7)
    h = Header.parse(story)
    assert h.routines_offset and h.strings_offset
    main_packed = int.from_bytes(story[h.initial_pc + 2:h.initial_pc + 4], "big")
    assert main_packed == 2
    assert h.profile.unpack_routine(main_packed, h.routines_offset) % 4 == 0


def test_v8_aligns_routines_and_strings_to_8():
    from zforge.asm.assembler import assemble
    from zforge.common.header import Header
    story = assemble((ROOT / "tests/samples/hello.zas").read_text(), "hello.zas", 8)
    h = Header.parse(story)
    main_packed = int.from_bytes(story[h.initial_pc + 2:h.initial_pc + 4], "big")
    assert h.profile.unpack_routine(main_packed) % 8 == 0
    assert len(story) % 8 == 0 and h.file_length == len(story)      # §11.1.6


def test_zil_sources_build_for_compatible_targets_only():
    from zforge.compiler.driver import compatible_targets
    # §1: 7 and 8 are "identical to 5"; v6 adds opcodes but removes none
    assert compatible_targets(5) == [5, 6, 7, 8]
    assert compatible_targets(6) == [6]               # a v6 source may use the v6-only opcodes
