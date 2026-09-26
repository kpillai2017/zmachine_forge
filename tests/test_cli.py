"""The zforge command line: exit codes and friendly errors."""
from tests.conftest import ROOT
from zforge.cli import main


def test_compile_run_disasm_info(tmp_path, capsys):
    out = tmp_path / "hello.z5"
    assert main(["compile", str(ROOT / "examples/hello.zil"), "-o", str(out), "--emit-asm"]) == 0
    assert out.exists() and out.with_suffix(".zas").exists()
    assert main(["run", str(out), "--ui", "plain"]) == 0
    assert "Hello, world!" in capsys.readouterr().out
    assert main(["disasm", str(out)]) == 0
    assert main(["info", str(out), "--header"]) == 0


def test_errors_are_one_line_and_nonzero(tmp_path, capsys):
    assert main(["run", str(tmp_path / "missing.z5")]) == 1
    bad = tmp_path / "v3.z5"
    bad.write_bytes(b"\x03" + bytes(100))
    assert main(["run", str(bad), "--ui", "plain"]) == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "version 3" in err


def test_scripted_play_of_the_example_game(tmp_path, capsys):
    out = tmp_path / "cloak.z5"
    main(["compile", str(ROOT / "examples/cloak.zil"), "-o", str(out)])
    script = tmp_path / "moves.txt"
    script.write_text("w\nhang cloak\ne\ns\nread message\n")
    assert main(["run", str(out), "--ui", "plain", "--script", str(script)]) == 0
    assert "You have won" in capsys.readouterr().out
