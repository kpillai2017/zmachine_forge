"""Small features Cold Iron needs: a property of one thing, 'is not
<adjective>', the attacking and entering actions, Understand ... as a mistake
(ADR-052); the author's activities, descriptions as grammar tokens, Does the
player mean (ADR-053)."""
from zforge.compiler.i7.driver import compile_i7
from zforge.vm.headless import play

STORY = '''"Small" by Test

The Hall is a room. A table is a supporter in the Hall. A book is on the table.
The lamp is in the Hall. The lamp has a number called the charge. The charge is 3.
The lamp can be polished. The lamp is not polished.
Rubbing is an action applying to one thing. Understand "rub [something]" as rubbing.
Carry out rubbing:
\tincrease the charge of the lamp by 1;
\tnow the lamp is polished;
\tsay "Charge [charge of the lamp][if the lamp is polished], polished[end if]."
Understand "help" as a mistake ("(No help: only [the lamp].)").
Understand "polish [something]" as a mistake ("You can't polish [the noun].").
Every turn: say "(a turn)".
'''


def replies(commands: list[str], story: str = STORY) -> list[str]:
    """What the story says to each command, each reply on one line."""
    out = play(compile_i7(story, "small.ni", 8).story, commands).transcript
    chunks = [chunk.partition("\n")[2] for chunk in out.split("\n>")[1:]][:len(commands)]
    return [" ".join(chunk.split()) for chunk in chunks]


def test_a_property_of_one_thing_and_not_an_adjective():
    assert replies(["rub lamp"]) == ["Charge 4, polished. (a turn)"]


def test_attacking_as_the_real_library_says_it():
    r = replies(["attack book", "break book", "hit table", "smash table", "punch table",
                 "destroy book", "thump table"])
    assert set(r) == {"Violence isn't the answer to this one. (a turn)"}


def test_entering_names_the_verb():
    r = replies(["enter book", "get in book", "get onto table", "sit on table",
                 "sit inside table", "stand on table"])
    assert r[:3] == ["That's not something you can enter. (a turn)"] * 3
    assert r[3:5] == ["That's not something you can sit down on. (a turn)"] * 2
    assert r[5] == "That's not something you can stand on. (a turn)"


def test_a_mistake_says_its_text_and_takes_no_turn():
    assert replies(["help", "polish book"]) == ["(No help: only the lamp.)",
                                                "You can't polish the book."]


# --- ADR-053: the author's activities; descriptions as grammar tokens; Does the player mean

ACTIVITY = '''"T" by T

The Hall is a room. The Garden is north of the Hall. A bead is in the Hall.
Forest-running is an activity.
For forest-running: say "You run through the trees."
For forest-running when in the Garden: say "You run among the roses."
First for forest-running when the player carries the bead:
\tsay "The bead pulls you onward.";
\tcontinue the activity.
Before forest-running when in the Garden: say "(Petals fall.)"
Running is an action applying to nothing. Understand "run" as running.
Carry out running: carry out the forest-running activity.
'''


def test_an_authors_activity_runs_its_rules_as_inform_does():
    r = replies(["take bead", "run", "n", "run", "drop bead", "run"], ACTIVITY)
    assert r[1] == "The bead pulls you onward. You run through the trees."
    assert r[3] == "(Petals fall.) The bead pulls you onward. You run among the roses."
    assert r[5] == "(Petals fall.) You run among the roses."


TOKENS = '''"T" by T

The Hall is a room. A table is a supporter in the Hall. It is fixed in place.
A book is in the Hall. A box is an open container in the Hall.
Definition: a thing is goable if it is fixed in place.
Understand "go [goable thing]" as a mistake ("(Try GO TO [the noun].)").
Tapping is an action applying to one thing. Understand "tap [open container]" as tapping.
Carry out tapping: say "You tap [the noun]."
'''


def test_a_description_token_takes_only_what_fits():
    assert replies(["go table", "tap box", "tap book"], TOKENS) == [
        "(Try GO TO the table.)", "You tap the box.",
        "You can't see any such thing."]                 # not 'What do you want to tap?'


LIKELY = '''"T" by T

The Hall is a room. A red ball and a blue ball are in the Hall. A green ball is in the Hall.
A tale is a kind of thing. A tale can be known.
The old tale is a tale in the Hall. The new tale is a tale in the Hall. It is known.
Bob is a man in the Hall. Bill is a man in the Hall.
Understand "guy" as Bob. Understand "guy" as Bill.
Does the player mean taking the blue ball: it is very likely.
Does the player mean taking the green ball: it is very unlikely.
Does the player mean doing something to the red ball: it is unlikely.
Does the player mean doing something to a not known tale: it is likely.
Does the player mean answering Bob that: it is likely.
'''


def test_does_the_player_mean_picks_the_likeliest():
    r = replies(["take ball", "x ball", "blue", "x tale", "answer hi to guy", "x guy"], LIKELY)
    assert r[0] == "(the blue ball) Taken."
    assert r[1] == "Which do you mean, the blue ball or the green ball?"   # red: unlikely
    assert r[3].startswith("(the old tale)")
    assert r[4].startswith("(Bob)")                     # the person is the noun
    assert r[5] == "Which do you mean, Bob or Bill?"    # no 'the' for a proper name


KINDS = '''"T" by T

The Hall is a room. A tale is a kind of thing.
The red tale is a tale in the Hall. The blue tale is a tale in the Hall.
Instead of examining a tale: say "A tale."
Every turn: if the noun is a tale, say "(tale)".
'''


def test_a_kind_of_the_authors_with_several_members_can_be_tested():
    assert replies(["x blue tale"], KINDS) == ["A tale. (tale)"]


# --- ADR-054: parts; times of day

PARTS = '''"T" by T

The Hall is a room. A table is a supporter in the Hall. A leg is part of the table.
The player carries a knife. The shadow is part of the knife.
A book is on the table. A tale is in the Hall.
Telling is an action applying to nothing. Understand "tell" as telling.
Carry out telling: now the tale is part of the book; say "The tale joins the book."
Checking is an action applying to nothing. Understand "check" as checking.
Carry out checking:
\tif the tale is part of the book:
\t\tsay "Part.";
\totherwise:
\t\tsay "Not part."
'''


def test_a_part_goes_with_its_whole_and_cannot_be_taken():
    r = replies(["take shadow", "x shadow", "take leg", "take all", "check", "tell", "check",
                 "take tale", "drop knife", "look"], PARTS)
    assert r[0] == "That seems to be a part of the knife."
    assert r[1] == "You see nothing special about the shadow."
    assert r[2] == "That seems to be a part of the table."
    assert r[3] == "book: Taken. tale: Taken."                   # not the leg
    assert (r[4], r[5], r[6]) == ("Not part.", "The tale joins the book.", "Part.")
    assert r[7] == "That seems to be a part of the book."
    assert "You can see a knife and a table here." in r[9]       # its shadow goes with it


def test_a_story_without_parts_or_times_gets_none_of_their_code():
    zil = compile_i7(ACTIVITY, "t.ni", 8).zil
    assert "PARTBIT" not in zil and "COMPILATION-FLAG PARTS" not in zil
    assert "COMPILATION-FLAG TIMES" not in zil


TIMES = '''"T" by T

The Hall is a room. The watch is in the Hall.
The watch has a time. The time of the watch is 12:00 AM.
Winding is an action applying to one thing. Understand "wind [something]" as winding.
Carry out winding:
\tlet T be the time of the watch;
\tnow the time of the watch is five minutes after T;
\tsay "It reads [time of the watch]."
Rewinding is an action applying to one thing. Understand "rewind [something]" as rewinding.
Carry out rewinding:
\tnow the time of the watch is two hours before the time of the watch;
\tsay "It reads [time of the watch][if the time of the watch is 10:05 PM] (ten past)[end if]."
Timesetting it to is an action applying to one thing and one time.
Understand "set [something] to [time]" as timesetting it to.
Carry out timesetting: now the time of the watch is the time understood.
Report timesetting: say "The watch reads [time of the watch]."
'''


def test_times_of_day_count_print_and_wrap_round():
    assert replies(["wind watch", "rewind watch"], TIMES) == [
        "It reads 12:05 am.", "It reads 10:05 pm (ten past)."]


def test_a_time_token_reads_the_times_players_type():
    r = replies(["set watch to 9:37", "set watch to 9:37 pm", "set watch to 12:00 am",
                 "set watch to 9 pm", "set watch to 21:05", "set watch to 9:7",
                 "set watch to 13:00 pm"], TIMES)
    assert r[:5] == ["The watch reads 9:37 am.", "The watch reads 9:37 pm.",
                     "The watch reads 12:00 am.", "The watch reads 9:00 pm.",
                     "The watch reads 9:05 pm."]
    assert r[5] == r[6] == "You can't see any such thing."   # not times


# --- ADR-055: someone else's possessions; orders and persuasion

PEOPLE = '''"T" by T

The Clearing is a room. The guy is a man in the Clearing. The printed name is "man".
The guy wears a hat. The guy carries a coin. A key is in the Clearing.
The oak is a person in the Clearing.
Giving is an action applying to nothing. Understand "give" as giving.
Carry out giving: now the guy carries the key; say "He pockets the key."
Checking is an action applying to nothing. Understand "check" as checking.
Carry out checking:
\tif the guy wears the hat:
\t\tsay "Hatted.";
\tif the guy carries the key:
\t\tsay "Keyed."
Persuasion rule for asking the oak to try waiting: say "The oak creaks."; persuasion fails.
Persuasion rule for asking the oak to try taking something: persuasion succeeds.
Persuasion rule for asking the oak to try examining something:
\tinstead say "You can't talk to [the oak]."
'''


def test_what_someone_else_carries_or_wears_is_theirs():
    r = replies(["take hat", "take coin", "check", "give", "check", "take key"], PEOPLE)
    assert r[0] == r[1] == r[5] == "That seems to belong to the man."
    assert (r[2], r[3], r[4]) == ("Hatted.", "He pockets the key.", "Hatted. Keyed.")


def test_orders_go_to_the_persuasion_rules():
    r = replies(["oak, wait", "oak, take key", "oak, x hat", "guy, x hat", "hat, wait",
                 "xyzzy, wait", "oak,", "oak, regleotis"], PEOPLE)
    assert r[0] == "The oak creaks."                       # it printed: no refusal
    assert r[1] == "The oak is unable to do that."        # persuaded (no NPC actions)
    assert r[2] == "You can't talk to the oak."           # an instead rule
    assert r[3] == "The man has better things to do."     # no rule decided
    assert r[4] == "You can't talk to the hat."
    assert r[5] == "You seem to want to talk to someone, but I can't see whom."
    assert r[6] == r[7] == "There is no reply."           # answering them instead


def test_a_command_with_a_list_is_not_an_order():
    assert replies(["take key, coin"], PEOPLE) == [
        "key: Taken. coin: That seems to belong to the man."]
