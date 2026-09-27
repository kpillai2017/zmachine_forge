"""Inform 7's testing commands - RULES, ACTIONS and TREE - in a game compiled
with --testing (lib/i7/testing.zil, ADR-038)."""
import subprocess
import sys
from pathlib import Path

import pytest

from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play

ROOT = Path(__file__).resolve().parents[1]
HOUSE = (ROOT / "tests/samples/coldiron_house.ni").read_text()


def run(source: str, commands: list[str], testing: bool = True) -> str:
    story = compile_i7(source, "t.ni", target=8, testing=testing).story
    t = play(story, commands).transcript
    return t[t.find(">"):]


def reply(transcript: str, command: str) -> str:
    part = transcript.split(">" + command + "\n", 1)[1]
    return part.split("\n>", 1)[0].strip()


def test_an_ordinary_build_does_not_know_them():
    t = run(HOUSE, ["rules", "actions", "tree"], testing=False)
    for word in ("rules", "actions", "tree"):
        assert reply(t, word) == "That's not a verb I recognise."


def test_tree_shows_where_everything_is():
    t = run(HOUSE, ["tree"])
    assert reply(t, "tree").splitlines() == [
        "House", "  yourself", "  table", "    book", "  axe", "  front door"]


def test_tree_shows_things_carried_and_off_stage():
    source = HOUSE + "\nThe ghost is a thing.\n"          # never placed: off-stage
    t = run(source, ["take book", "tree"])
    tree = reply(t, "tree").splitlines()
    assert tree[:2] == ["House", "  yourself"] and tree[2] == "    book"
    assert tree[-2:] == ["Nowhere (off-stage):", "  ghost"]


def test_actions_lists_each_action_and_how_it_ended():
    t = run(HOUSE, ["actions", "take table", "drop book", "actions off", "look"])
    assert reply(t, "actions") == "Actions listing on."
    assert reply(t, "take table") == ("[taking the table]\nThat's fixed in place.\n"
                                      "[taking the table - failed]")
    assert reply(t, "drop book").startswith("[dropping the book]")
    assert "[" not in reply(t, "look")                      # switched off again


def test_actions_names_both_things_of_a_two_thing_action():
    t = run(HOUSE, ["take book", "actions", "put book on table"])
    out = reply(t, "put book on table")
    assert out.startswith("[putting the book on the table]")
    assert out.endswith("[putting the book on the table - succeeded]")


def test_rules_names_library_rules_and_the_authors_rules():
    t = run(HOUSE, ["rules", "take book", "rules off"])
    lines = reply(t, "take book").splitlines()
    assert lines[0] == '[Rule "Before taking the book when the book is on the table" applies.]'
    assert '[Rule "can\'t take what\'s fixed in place rule" applies.]' in lines
    assert '[Rule "Report taking the book when the book is lifted" applies.]' in lines
    assert reply(t, "rules off") == "Rules tracing now switched off."


def test_a_rule_whose_conditions_fail_is_not_shown():
    t = run(HOUSE, ["take book", "drop book", "rules", "take book"])   # now on the floor
    traced = reply(t.split(">rules\n", 1)[1], "take book")
    assert '[Rule "standard taking rule" applies.]' in traced      # tracing is on...
    assert "Before taking the book" not in traced                  # ...but it is not on the table


def test_a_named_rule_is_shown_by_its_name():
    source = HOUSE + ("\nCheck taking the table (this is the table stays rule): "
                      "say \"It stays.\"; stop the action.\n")
    t = run(source, ["rules", "take table"])
    assert '[Rule "table stays rule" applies.]' in reply(t, "take table")


@pytest.mark.parametrize("name", ["examples/cloak.ni", "examples/advent_opening.ni"])
def test_unused_they_change_nothing(name):
    source = (ROOT / name).read_text()
    commands = ["look", "i", "n", "s", "e", "w", "take all", "x me", "wait", "score"]
    assert run(source, commands, testing=True) == run(source, commands, testing=False)


def test_only_for_inform_7_sources(tmp_path):
    out = subprocess.run([sys.executable, "-m", "zforge", "compile", "examples/cloak.zil",
                          "--testing", "-o", str(tmp_path / "c.z5")],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode != 0 and "for Inform 7 (.ni) sources only" in out.stderr
    assert "Traceback" not in out.stderr


def test_a_rule_is_shown_in_the_authors_own_words():
    source = HOUSE + '\nInstead of taking the table: say "It stays."\n'
    t = run(source, ["rules", "take table"])
    assert reply(t, "take table").startswith('[Rule "Instead of taking the table" applies.]')
