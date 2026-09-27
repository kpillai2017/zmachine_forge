"""docs/TOUR.md must stay true: its story is built from the tour's own text,
and every transcript it shows must be what the game really prints."""
import re
from pathlib import Path

from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play

TOUR = (Path(__file__).resolve().parents[1] / "docs/TOUR.md").read_text()
BLOCKS = re.findall(r"```[a-z]*\n(.*?)```", TOUR, re.S)


def the_story() -> str:
    return next(b for b in BLOCKS if b.startswith('"The Lamp" by You'))


def transcript(commands: list[str], testing: bool) -> str:
    story = compile_i7(the_story(), "lamp.ni", target=8, testing=testing).story
    return play(story, commands).transcript


def shown_transcripts() -> list[str]:
    """The tour's blocks that show play: they start at a prompt."""
    return [b for b in BLOCKS if b.startswith(">")]


def test_the_tour_shows_play():
    assert len(shown_transcripts()) >= 2


def test_every_transcript_in_the_tour_is_what_the_game_prints():
    t = transcript(["actions", "rules", "take lamp", "take me"], testing=True)
    for block in shown_transcripts():
        assert block.strip() in t, f"TOUR.md shows something the game does not print:\n{block}"


def test_the_tree_in_the_tour():
    tree = next(b for b in BLOCKS if b.startswith("Hall\n"))
    t = transcript(["take lamp", "tree"], testing=True)
    assert tree.strip() in t


def test_the_zil_the_tour_quotes_is_what_the_compiler_writes():
    from zforge.compiler.i7.driver import generate_zil
    zil = generate_zil(the_story(), "lamp.ni")[1]
    for block in BLOCKS:
        if block.startswith(("<OBJECT BRASS-LAMP", "<SYNTAX TAKE", "<ROUTINE V-TAKING")):
            assert block.strip() in zil, f"TOUR.md quotes ZIL the compiler does not write:\n{block}"
