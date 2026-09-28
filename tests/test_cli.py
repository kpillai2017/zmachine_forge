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
    # exit 2 = "not something zforge handles" (ADR-023; was 1 in zforge v1)
    assert main(["run", str(bad), "--ui", "plain"]) == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err and "version 3" in err
    assert "zforge runs versions 5, 6, 7 and 8" in err


def test_scripted_play_of_the_example_game(tmp_path, capsys):
    out = tmp_path / "cloak.z5"
    main(["compile", str(ROOT / "examples/cloak.zil"), "-o", str(out)])
    script = tmp_path / "moves.txt"
    script.write_text("w\nhang cloak\ne\ns\nread message\n")
    assert main(["run", str(out), "--ui", "plain", "--script", str(script)]) == 0
    assert "You have won" in capsys.readouterr().out


def test_output_piped_into_head_does_not_crash(tmp_path):
    """`zforge run game.z5 | head -3`: the reader closes the pipe early.
    That is not our error, so no traceback and no 'Exception ignored'."""
    import subprocess
    import sys
    story = tmp_path / "cloak.z5"
    assert main(["compile", str(ROOT / "examples/cloak.zil"), "-o", str(story)]) == 0
    script = tmp_path / "moves.txt"
    script.write_text("look\n" * 200)                  # plenty of output
    proc = subprocess.Popen([sys.executable, "-m", "zforge", "run", str(story), "--ui",
                             "plain", "--script", str(script)], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.stdout.readline()
    proc.stdout.close()                                 # like `head` exiting
    err = proc.stderr.read().decode()
    proc.wait(timeout=30)
    assert "Traceback" not in err and "Exception ignored" not in err, err
    assert proc.returncode == 0


def test_compile_makes_the_output_folder(tmp_path, capsys):
    # A fresh copy has no build/ folder; `-o build/game.z8` used to fail with
    # a traceback. All three build commands now make the folder.
    for cmd, src, out in [("compile", "examples/cloak.ni", "a/b/cloak.z8"),
                          ("compile", "examples/cloak.zil", "c/cloak.z5"),
                          ("asm", "tests/samples/hello.zas", "d/e/hello.z5")]:
        assert main([cmd, str(ROOT / src), "-o", str(tmp_path / out)]) == 0
        assert (tmp_path / out).exists()


def test_a_file_that_cannot_be_written_is_a_plain_error(tmp_path, capsys):
    story = tmp_path / "hello.z5"
    main(["asm", str(ROOT / "tests/samples/hello.zas"), "-o", str(story)])
    capsys.readouterr()
    blocker = tmp_path / "not_a_folder"
    blocker.write_text("a file, where a folder is needed")
    status = main(["run", str(story), "--ui", "plain",
                   "--transcript", str(blocker / "log.txt")])
    err = capsys.readouterr().err
    assert status == 1 and "Traceback" not in err
    assert err.startswith("zforge: ") and "log.txt" in err
