"""Choosing the target version (zforge/config.py, proforma v2 §1).

Order: --target > zforge.toml > ZFORGE_TARGET > the source's <VERSION>.
"""
import pytest

from tests.conftest import ROOT
from zforge.cli import main
from zforge.common.errors import UnsupportedTarget
from zforge.config import parse_target, resolve_target


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    monkeypatch.delenv("ZFORGE_TARGET", raising=False)
    monkeypatch.chdir(tmp_path)           # no zforge.toml unless a test writes one
    return tmp_path


def test_parse_target_accepts_z8_Z8_and_8():
    assert parse_target("z8") == parse_target("Z8") == parse_target("8") == 8


@pytest.mark.parametrize("bad", ["z3", "z6", "zz", ""])
def test_unsupported_targets_are_refused(bad):
    with pytest.raises(UnsupportedTarget, match="choose z5, z7, z8"):
        parse_target(bad)


def test_the_order_of_the_settings(clean_env, monkeypatch):
    assert resolve_target(None, 5).describe() == "target z5 (from the source)"
    monkeypatch.setenv("ZFORGE_TARGET", "z8")
    assert resolve_target(None, 5).describe() == "target z8 (from ZFORGE_TARGET)"
    (clean_env / "zforge.toml").write_text('target = "z7"\n')
    assert resolve_target(None, 5).describe() == "target z7 (from zforge.toml)"
    assert resolve_target("z5", 5).describe() == "target z5 (from --target)"


def test_zforge_toml_may_use_a_build_table(clean_env):
    (clean_env / "zforge.toml").write_text('[build]\ntarget = "z8"\n')
    assert resolve_target(None, 5).version == 8


def test_compile_names_the_target_and_its_origin(clean_env, capsys):
    out = clean_env / "cloak.z8"
    assert main(["compile", str(ROOT / "examples/cloak.zil"), "--target", "z8",
                 "-o", str(out)]) == 0
    assert out.read_bytes()[0] == 8
    assert "target z8 from --target" in capsys.readouterr().out


def test_compile_default_output_suffix_follows_the_target(clean_env, monkeypatch, capsys):
    src = clean_env / "hello.zil"
    src.write_text((ROOT / "examples/hello.zil").read_text())
    monkeypatch.setenv("ZFORGE_TARGET", "7")
    assert main(["compile", str(src)]) == 0
    assert (clean_env / "hello.z7").read_bytes()[0] == 7


def test_asm_target_and_bad_target_exit_code(clean_env, capsys):
    out = clean_env / "h.z8"
    assert main(["asm", str(ROOT / "tests/samples/hello.zas"), "--target", "z8",
                 "-o", str(out)]) == 0
    assert out.read_bytes()[0] == 8
    assert main(["asm", str(ROOT / "tests/samples/hello.zas"), "--target", "z3"]) == 2
    assert "Unsupported target z3" in capsys.readouterr().err
