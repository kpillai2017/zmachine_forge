"""'Definition:' adjectives (ADR-050), and texts compared by their words."""
from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play


def replies(source: str, commands: list[str]) -> list[str]:
    """The reply to each command, in order."""
    out = play(compile_i7(source, "definitions.ni", 8).story, commands).transcript
    chunks = [chunk.partition("\n")[2] for chunk in out.split("\n>")[1:]][:len(commands)]
    return [" ".join(chunk.split()) for chunk in chunks]     # the words: layout aside

STORY = '''"Definitions" by Test

The Hall is a room. A table is a supporter in the Hall. It is fixed in place.
A rose is in the Hall. A lamp is in the Hall. The lamp is lit.
The Attic is a room. The Attic is above the Hall.
A thing has a text called scent. The scent of a thing is usually "nothing".
The scent of the rose is "sweet".
Definition: a thing is goable if it is scenery or it is fixed in place.
Definition: a thing is scented if the scent of it is not "nothing".
Definition: the lamp is glowing rather than dim if it is lit.
Definition: a room is high if it is the Attic.
Definition: a thing is mentionable:
\tif it is the player, no;
\tif it is fixed in place, no;
\tyes.
Testing is an action applying to one thing. Understand "test [something]" as testing.
Carry out testing:
\tif the noun is goable, say "goable. ";
\tif the noun is scented, say "scented. ";
\tif the noun is glowing, say "glowing. ";
\tif the noun is dim, say "dim. ";
\tif the noun is mentionable, say "mentionable. ";
\tif the location is high, say "high. ";
\tsay "(done)".
Sniffing is an action applying to one thing. Understand "sniff [something]" as sniffing.
Instead of sniffing something scented: say "[The noun] smells [scent of the noun]."
Instead of sniffing something: say "[The noun] smells of nothing."
Perfuming is an action applying to one thing. Understand "perfume [something]" as perfuming.
Carry out perfuming: now the scent of the noun is "musky"; say "Done."
Rubbing is an action applying to one thing. Understand "rub [something]" as rubbing.
Carry out rubbing: now the scent of the noun is "nothing"; say "Done."
'''


def test_each_form_of_definition():
    r = replies(STORY, ["test table", "test rose", "test lamp", "up", "test me"])
    assert r[0] == "goable. (done)"                         # fixed in place: not mentionable
    assert r[1] == "scented. mentionable. (done)"
    assert r[2] == "glowing. mentionable. (done)"           # 'rather than': not dim
    assert r[4].endswith("high. (done)")                    # a room's definition


def test_an_adjective_in_a_rule_preamble():
    r = replies(STORY, ["sniff rose", "sniff lamp"])
    assert r == ["The rose smells sweet.", "The lamp smells of nothing."]


def test_texts_compare_by_their_words_after_now():
    r = replies(STORY, ["perfume lamp", "test lamp", "sniff lamp", "rub rose", "test rose",
                        "sniff rose"])
    assert r[1] == "scented. glowing. mentionable. (done)"
    assert r[2] == "The lamp smells musky."                  # printing a text set by 'now'
    assert r[4] == "mentionable. (done)"                     # "nothing" again: not scented
    assert r[5] == "The rose smells of nothing."


def test_a_text_variable_set_by_now():
    story = STORY + '''The reply is a text that varies. The reply is "Yes.".
Asking is an action applying to nothing. Understand "ask" as asking.
Carry out asking: say "[reply]"; now the reply is "No."; if the reply is "No.", say " (no)".
'''
    assert replies(story, ["ask", "ask"]) == ["Yes. (no)", "No. (no)"]
