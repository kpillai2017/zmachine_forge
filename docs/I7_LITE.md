# I7-lite: the Inform 7 subset zforge compiles

I7-lite is a documented subset of Inform 7's natural-language syntax
(Inform 7 builds 6L38-10.1). A game written in it is also a valid Inform 7
game; the reverse is not true. What is in and out comes from real use:
see `docs/I7_SURVEY.md` (a survey of a 2,013-line Inform 7 game).

How it is compiled: `docs/I7_TO_ZIL.md`.

**Steps** (column *Step*): **7a** is enough for `hello.ni` and Cloak of
Darkness; **7b** adds the survey's features (doors, devices, `try`, ...);
**7c** adds adaptive text. Anything not listed is refused with a problem
message that names the construct and points here.

**Built so far:** 7a, 7b and 7c (see `examples/cloak.ni`,
`tests/samples/doors_and_lamps.ni` and `tests/samples/adaptive.ni`).
Adaptive text agrees with the object named most recently, exactly as in
Inform 7 - so "[We] [are] by a stream that [flow]" prints "flow" (it
agrees with "you"); write "[regarding the stream]" or plain "flows". Details that differ from Inform 7:
doors are closed and openable by default, containers open; a door is
listed in room descriptions (not yet checked against real Inform 7).

## Source layout

* A source file is a sequence of **sentences**, ending in `.` (or a quoted
  text ending in `.` `!` or `?`). Paragraphs are separated by blank lines.
* `[Square brackets]` outside quoted text are comments.
* Headings (`Volume`, `Book`, `Part`, `Chapter`, `Section` + title) are
  allowed anywhere and only organise the source.
* A **rule** or **phrase definition** is a *preamble* ending in `:`
  followed by phrases, either on one line separated by `;` or on indented
  lines (tabs or 4 spaces; `if` / `otherwise` / `repeat` nest by
  indentation). A one-line rule may also follow another sentence on the
  same line: `The count is a number that varies. Every turn: increase the
  count by 1.`
* Words are case-insensitive except inside quoted text.
* A quoted text may go on over several lines: a line break inside it is a
  space, and a blank line inside it a paragraph break (ADR-047).

## 1. The story (7a)

| Sentence | Step |
|---|---|
| `"Cloak of Darkness" by Roger Firth` (first line: title and author) | 7a |
| `The story headline is "A basic IF demonstration".` | 7a |
| `The story genre is "...".` `The release number is 2.` | 7a |
| `Use scoring.` `Use no scoring.` `The maximum score is 2.` | 7a |
| harmless options: `Use no deprecated features.`, `Use BRIEF room descriptions.` (accepted, with a note) | 7b |

## 2. Rooms, things and the map

| Sentence | Meaning | Step |
|---|---|---|
| `The Foyer is a room.` | a room | 7a |
| `The Foyer is a room. "You are standing..."` | a quoted sentence straight after a room is its description | 7a |
| `The Bar is south of the Foyer.` | map connection, two-way (and creates the Bar as a room if new) | 7a |
| `The Bar is south from the Foyer.` | same meaning ("from" = "of") | 7b |
| `South of the Foyer is the Bar.` | same, subject last | 7a |
| `North is the Cloakroom.` (inside a room's paragraph) | from the room being described | 7b |
| `The Bar is dark.` / `lit` | darkness | 7a |
| `A brass hook is in the Cloakroom.` | a thing, placed | 7a |
| `The hook is a supporter in the Cloakroom.` | with a kind. A supporter is fixed in place unless you say it is portable, as in Inform 7 (checked against *Cold Iron*, ADR-037) | 7a |
| `The cloak is on the hook.` / `in the box` | placement on a supporter / in a container | 7a |
| `The player wears a velvet cloak.` / `carries` | the player's possessions; a list makes several (`The player carries a lamp and some coins.`) | 7a |
| `A red ball and a blue ball are in the Hall.` | a list (with "are"): one thing for each name, as in Inform (a name containing "and" needs `called`). A name with "some" (`some beads`) is plural-named | |
| `It is scenery.` / `It is fixed in place.` | `It` = the last thing named | 7a |
| `The hook is scenery.` `The box is open/closed/openable/locked/lockable.` | either/or properties | 7a |
| `The lamp is a device.` / `switched on` | a device (switching on/off) | 7b |
| `The grate is a door. It is north of X and south of Y.` | a two-sided door | 7b |
| `The grate is locked. The keys unlock the grate.` | lock and key | 7b |
| `The indefinite article of the water is "some".` | article | 7b |
| `The keys are plural-named.` / `privately-named` / `proper-named` | naming | 7b |
| `Some keys are in the Building.` | a thing first made by an "are" sentence is plural-named; "Some ..." gives it the article "some" (Inform 7's inference) | Advent |
| `The steps are an open unopenable door.` / `a scenery, privately-named thing` | adjectives before the kind, separated by commas, "and" or spaces | Advent |
| `The steps are an open unopenable door, below the Top.` | the kind, then (after a comma) where it is | Advent |
| `The Hall is west from the steps.` (the steps being a door) | the door's other side: the Hall, going east | Advent |
| `In the Bird Chamber is a scenery thing called walls.` | a thing named with "called", with its kind and adjectives | Advent |
| `Outside is nowhere.` (inside a room's paragraph) | no exit that way, cancelling the automatic reverse connection | Advent |
| `A, B, and C are lighted.` | a list (with "are"); a part not yet defined is made now, and becomes a room when a later sentence needs one | Advent |
| `The Pit is south of the Crypt, southwest of the Fen and southeast of the Moor.` | several exits in one sentence, separated by commas or "and" | ADR-039 |
| `The Library is north of the Hall. It is west of the Garden.` | `It` (or `They`) after a room means that room | ADR-039 |

**Names.** A thing is called by its whole name (`velvet cloak`); every word
of the name also works alone in commands, in any order (`velvet`,
`cloak`). Articles `a an the some` are not part of names.

A short form of a name works in the source too (`the cloak` for the
velvet cloak), and that can catch you out: if the history of the inkpot
already exists, `The inkpot is in the Black Gallery.` means *that*
history, not a new inkpot. A thing can be in only one place, so when a
sentence would move something an earlier sentence put elsewhere, you get
a problem message saying so. If you meant a new thing, give it a name
that isn't part of the other one's.

## 3. Properties and values

| Sentence | Meaning | Step |
|---|---|---|
| `The description of the cloak is "A handsome cloak...".` | what EXAMINE says | 7a |
| `The printed name of X is "...".` `The initial appearance of X is "...".` | | 7a |
| `A thing can be shiny.` `A thing can be shiny or dull.` | new either/or property | 7a |
| `A thing has a number called weight.` `The weight of X is 3.` | value property | 7a |
| `The trample count is a number that varies.` `... The trample count is 0.` | global variable (number, truth state, text, object) | 7a |
| `A treasure is a kind of thing.` | new kind | 7a |
| `A room is usually dark.` / `The printed name of a forest is usually "Forest".` | kind defaults | 7b |
| `Every room has a number called the visit count.` | every room gets it (starting at 0) | Advent |
| `Forest1 has a number called the counter. The counter is 1.` | a property of one thing; "The counter is 1." next gives its value (ADR-052) | Cold Iron |
| `The oak can be worded. The oak is not worded.` | "not" before an adjective: the thing is not so | Cold Iron |
| `Every room has a text called the short description.` `The short description is "[We]['re] here again."` | a text property; the short form means the last thing named | Advent |
| `The Lab, the Hall and the Yard are lighted.` | several subjects at once | Advent |

**Either/or properties are limited.** Each one becomes a Z-machine
attribute, and there are only 48 (§12.3.1), shared with the library,
which uses about 20. A story that needs more gets a problem message
listing the ones that didn't fit. One number property can often replace
several of them: `A room has a number called the wing.` instead of
`A room can be central.`, `A room can be ancient.` and so on.

**Definitions** (ADR-050) make an adjective that is worked out when it is
used, rather than stored:

    Definition: a thing is goable if it is scenery or it is fixed in place.
    Definition: the lamp is glowing rather than dim if it is lit.
    Definition: a room is high if it is the Attic.
    Definition: a thing is mentionable:
        if it is the player, no;
        yes.

The definition is for a kind (a thing, a room, a kind the author made) or
for one object, and the thing is called "it" ("they" for plural things,
or a name given with `(called ...)`). The same adjective can be defined for
several objects (Bronze defines "solved" for each puzzle). "Rather than"
names the opposite. A defined adjective works where an either/or property
does: `if the lamp is glowing`, and in a rule's preamble,
`Instead of sniffing something scented` or `... a scented thing`.

**Texts compare by their words**: `if the scent of the noun is "nothing"`
is true when the scent has those words, whether it was set in the source
or by `now`. A text with substitutions (`"[if ...]..."`) can only be
compared with `""` (no text).

## 4. Understanding the player

| Sentence | Meaning | Step |
|---|---|---|
| `Understand "dark/black/satin" as the cloak.` | extra words for a thing | 7a |
| `Understand "puzzle piece" or "wooden shape/bit" as the piece.` | a phrase: names the thing only as a whole ("puzzle" alone does not); a slash is between words | 7b |
| `Understand "hang [something] on [something]" as putting it on.` | a new grammar line for an action | 7a |
| `Understand "give [someone] [something]" as giving it to (with nouns reversed).` | the first thing typed is the second noun (ADR-049); on a topic action it changes nothing, as the thing is the noun anyway | 7c |
| `Understand "xyzzy" as casting xyzzy.` | grammar for a new action | 7a |
| `Understand "plugh" as north.` | a word for a direction | 7b |
| `Understand "wreath", "circlet" as the branches when the branches are woven.` | words that name the thing only while the condition holds (single words, not phrases; ADR-051) | Cold Iron |
| `Understand "help" as a mistake ("(Type ABOUT for credits.)").` | a command that only says the text; no turn passes (ADR-052) | Cold Iron |
| `Understand the command "grab" as "take".` | verb synonym | 7b |
| `Understand the commands "open", "close" as something new.` | forget their earlier grammar | Advent |
| `Understand nothing as dropping.` | forget an action's earlier grammar | Advent |
| `... when the location is the Bar` (on an Understand line) | only there | after Cloak (decision in I7_SURVEY) |

Tokens: `[something]`, `[someone]`, `[things]` and `[things preferably
held]` (several objects, below), and `[text]` (a topic, section 5).

A token can also be a **description** (ADR-053): adjectives - either/or
properties or the author's definitions, each maybe after `not` - and a
kind, the library's or the author's: `[open container]`,
`[undirectional goable thing]`. The slot takes only the things that fit.
If none does, the parser tries the verb's other lines, as in Inform; if
no line fits, it says "You can't see any such thing." (Inform's usual
reply for a thing a command cannot use; not checked against a real game).
A description token has no implied object, and can't take several things.

**Does the player mean** (ADR-053), as in Inform 7, settles which thing a
word means when it fits several:

    Does the player mean taking the blue ball: it is very likely.
    Does the player mean doing something to a not known tale: it is likely.
    Does the player mean answering Bob that: it is likely.

Each candidate is tried as the noun of the command being parsed (on a
topic line the person is the noun, as for the action itself) and scored:
`very unlikely`, `unlikely`, `possible` (when no rule applies), `likely`,
`very likely`. Only the best-scored are kept; if one is left, the parser
says which, `(the blue ball)`, and otherwise asks "Which do you mean ...?"
among those. A proper-named thing is named without "the" there, as in
Inform: `(Bob)`, "Which do you mean, Bob or Bill?".

**Several objects at once** (ADR-035), as in Inform 7: the library's take,
drop, put ... on / in and insert lines use `[things]` / `[things preferably
held]`, so the player can type `take all`, `drop all except the lamp`,
`take all but food`, `take lamp and keys`, `drop lamp, keys and food`.
Each object's result is on its own line after its name (`keys: Taken.`),
all in one turn. What ALL means: for take, what lies in the room or on a
supporter in it (a book on a table: *Cold Iron*, ADR-037) - not scenery,
not fixed in place, not people, not what is held; for drop and put,
what is carried but not worn. `put all in the box` leaves out the box. ALL
is one object, with `(the keys)`, only when ONE thing could have been meant;
otherwise even a single thing left over is `bottle of water: Taken.`
(both checked against the real Advent). A verb whose line says
`[something]` refuses several objects (the *can't use multiple objects*
error) - and so does every second object: `unlock grate with all` or
`put lamp in box and table` (as in the real Advent, where
`[parser command so far]` is then "unlock the grate with"); ALL with nothing
to mean is the *nothing to do* error. When several rows of a verb fail,
the most serious error is reported (as Inform ranks them: *can't see* is
below *can't use multiple objects*, which is below *nothing to do*).

An unclear name in a list (`take lamp and coin`, with two coins) is asked
about once the whole command is read - "Which do you mean, the gold coin or
the silver coin?" - one question per unclear name, as for a single object;
an empty answer cancels the command, and an answer that is a new command
is carried out instead. After `except` / `but`, an unclear name takes out
every thing it fits (`take all but coin`). (Advent has no two things of one
name: this is not checked against a real game.)

A worn thing is taken off first when it is dropped, put on or put in
something - "(first taking the cloak off)", the words of Inform 7's
*can't drop / put / insert clothes being worn* rules - but ALL never means
a worn thing.

## 5. Actions

The standard actions (7a unless marked): looking, examining, taking,
dropping, going, taking inventory, putting it on, inserting it into,
wearing, taking off, waiting, requesting the score, saving the game,
restoring the game, quitting the game; 7b: opening, closing, locking it
with, unlocking it with, switching on, switching off; ADR-052: attacking
(`attack`, `break`, `smash`, `hit`, `punch`, `destroy`, `thump`) and
entering (`enter`, `get in/into/on/onto`, `sit on/in/inside`, `stand on`),
with the words and replies of the real library (checked against *Cold
Iron*). There are no enterable things, so entering is always refused. `read X` means
examining X; `undo` is handled before actions, as in Inform 7. `again`
(or `g`) repeats the last command typed, even one that failed, and says
"You can hardly repeat that." when there is none (checked against the real
*Bronze*; ADR-042).

**Topics** (ADR-045). Four standard actions take a *topic* - whatever words
the player types, even ones the game doesn't know - as well as a thing:
consulting it about (`consult X about T`, `look up T in X`, `read about T
in X`), asking it about (`ask X about T`), telling it about (`tell X about
T`) and answering it that (`answer T to X`, `say T to X`). Their default
replies are Inform 7's, checked against *Cold Iron*. An author's own action
can apply to one topic, or to one thing and one topic, with `[text]` in its
Understand lines:

    Pondering is an action applying to one topic.
    Understand "ponder [text]" as pondering.
    Carry out pondering: say "You ponder [the topic understood]."

A rule names a topic in quotation marks. A slash separates the words that
may stand in one place, `--` means that place may be left out, and `or`
joins whole phrases:

    Instead of consulting the notes about "roses/rose/garden" or "rose garden", ...
    Instead of asking the Beast about "the/-- djinn", ...
    Instead of asking the Beast about when the topic understood includes "father", ...

In a rule the topic must match all the words typed; `if the topic
understood matches "..."` does the same, and `includes "..."` finds the
words anywhere in it (`does not include` too). `[the topic understood]`
prints the words as typed. A command that stops where the topic should be
(CONSULT THE NOTES) is not understood, as in Inform 7.

**Topic tables** (ADR-046) list many topics at once, the way Inform authors
usually do. A table is a "Table of ..." line, a line of column names, and
one row per line, with the entries separated by tabs; a blank line ends it.
It needs one column called `topic`; the other columns hold texts (`--` for
none). A rule or condition looks a topic up, and `[reply entry]` (any
column's name, then "entry") prints that column of the row found:

    Instead of consulting the notes about a topic listed in the Table of Notes:
        say "[reply entry][paragraph break]".

    Table of Notes
    topic	reply
    "rose/roses/garden" or "rose garden"	"The roses are of Lucrezia's own breeding."
    "the/-- djinn"	"A djinn, bound in brass."

`if the topic understood is a topic listed in the Table of Notes` does the
same in a condition. A rule may also leave the topic out altogether
(`Instead of consulting the notes: ...`): any topic will do. I7-lite has only these topic tables: not Inform's
tables of numbers or things, and not `choose a row`, `repeat through` and
the rest.

New actions (7a):

    Casting xyzzy is an action applying to nothing.
    Polishing is an action applying to one thing.
    Carry out polishing: say "It gleams."

## 6. Rules

    When play begins: ...
    Every turn: ...                  Every turn when <condition>: ...
    Before / Instead of / Check / Carry out / After / Report <action pattern>: ...

Action patterns: `taking the lamp`, `taking something`, `putting the cloak
on the hook`, `going north`, `going`, `doing something`, `doing something
other than going`, `doing something to the lamp` (any action on it,
ADR-053), `examining or taking the cloak`; optional
`in <room>` / `in the presence of X` (7b) and `when <condition>`. A
condition can also be `in <room>` (`when in Forest3`: the player is there).

Where a rule or condition names a kind - `a container`, or the author's
`a tale` (`if the noun is a tale`) - it means any thing of that kind or of
a kind of it, and a description can put adjectives before it, with `not`
(`an important not known tale`). The author's kinds are tested by their
members, which the compiler knows (ADR-053).

One-line forms (7b): `Instead of eating the lamp, say "No.".`,
`Instead of thinking, try looking.`

Outcomes follow Inform 7: `Instead` and `After` rules stop the action when
they finish; `Before`, `Check`, `Carry out`, `Report` continue unless they
say `stop the action` (or end a phrase with `instead`, 7b).
`continue the action` overrides the default.

Named rules and rule swapping (ADR-028). The library's rules are Inform
7's named rules (section 9), and the author can name rules too:

    Carry out looking (this is the lamp glow rule): ...
    This is the Crowther's room description heading rule: ...

    The can't take scenery rule is not listed in the check taking rulebook.
    The fixed rule is not listed in any rulebook.
    The X rule is listed instead of the room description heading rule
        in the carry out looking rulebook.
    The X rule is listed before / after the Y rule in the check going rulebook.
    The X rule is listed first / last / in the report taking rulebook.
    The standard report taking rule response (A) is "OK."

Rules are ordered as in Inform 7: more specific first, then the library
before the author, then source order; a rule listed instead of another
takes its place. A response edit may use substitutions.

`First` and `last` put a rule at the front or the back of its rulebook,
whatever its specificity (ADR-034): `First every turn: ...`,
`Last carry out taking: ...`, `The first after printing a parser error
rule: ...`.

A long preamble may go on in the next lines, each starting with a space
(a body line starts with a tab):

    To pose the question (proposition - a text)
     with affirmative response (hint text - a text):
        ...
    After printing a parser error when the locked grate is in the location,
     pose the question "Are you trying to get into the cave? "
     with affirmative response "The grate is very solid ...".

A rule begins a line: `The count is a number that varies. When play
begins: ...` on one line is not read as a rule.

Other rule forms: `going nowhere` (a direction with no exit), `[the door
gone through]`, `[the room gone to]`, `[the room gone from]`.

Spacing follows Inform 7: when a rule's text ends a sentence and a later
rule prints, a blank line separates them (so an every turn rule's text
stands in its own paragraph).

## 7. Phrases (inside rules)

| Phrase | Step |
|---|---|
| `say "text"` | 7a |
| `now X is Y` / `now X is in Y` / `now the player carries X` | 7a |
| `move X to Y` / `remove X from play` | 7a |
| `increase X by N` / `decrease X by N` | 7a |
| `increment X` / `decrement X` (by one) | Advent |
| `let X be <value>` (a number, a thing or a text; `let` again gives it a new value) | Advent |
| `if <cond>: ...` / `otherwise if` / `otherwise` (indented or one line) | 7a |
| `repeat with I running from 1 to 10: ...` / `while <cond>: ...` | Advent |
| `end the story` / `end the story finally` / `end the story saying "..."` | 7a |
| `stop the action` / `continue the action` / `rule succeeds` / `rule fails` | 7a |
| `try <action>` / `silently try <action>` (or `try silently <action>`) | 7b |
| `<phrase> instead` (do it, then stop) | 7b |
| `To <phrase>: ...` / `To say <name>: ...` user phrases | 7a |
| `To decide whether ...: ...` with `decide yes` / `decide no` | Advent |
| phrases with parameters: `To praise (item - a thing) times (n - a number): ...`, `To say fancy (item - a thing): ...`, `To decide whether (item - a thing) is gleaming: ...` | Advent |
| `say line break` / `say paragraph break` | Advent |

Conditions: `X is Y`, `X is not Y`, `X is in Y`, `X is on Y`, `the player
carries X`, `the player is in Y`, `X is <property>`, `the noun is X`,
`N is greater than / less than / at least / at most M` (and `>` `<`
`>=` `<=`), `A and B`, `A or B`, `a random chance of 1 in 3 succeeds`,
`X encloses Y`, `the player consents` (a yes/no question), `in darkness`,
`X is ""` (a text property with no text), `the latest parser error is the
<name> error` (section 10), and a description as the subject: `the locked
grate is in the location` means the grate, if it is locked (`the grate is
locked and the grate is in the location`).

Parameters (ADR-034) are texts, numbers, truth states or objects (any kind
of thing, or `object`). Inside the phrase they are names like any other:
`say "[proposition]"`, `if the item is lit`, `increase the count by n`. A
text argument may have substitutions; it is worked out when the phrase
prints it. One limit: a text given to a phrase cannot use the names of the
rule or phrase that gives it (`echo "[message]!"` inside a phrase whose
parameter is `message`) - I7-lite says so; say the text there instead.
The location, the noun, the second noun, the player, the score, the turn
count are built in.


Also (from Advent's cave):

| Phrase | Meaning |
|---|---|
| `if <condition>,` with the phrases indented below it | the same as `if <condition>:` |
| `move the player to X` | moves the player and describes X, as Inform 7 does |
| `move the player to X, without printing a room description` | moves the player only |
| `if X is held` / `is not held` | carried or worn by the player |
| `if the player does not carry X` / `does not wear X` | negated possession |

## 8. Text substitutions (inside quoted text)

| Substitution | Step |
|---|---|
| `[the noun]` `[a noun]` `[The noun]` `[A noun]` `[noun]` `[second noun]` | 7a |
| `[the X]` `[a X]` `[X]` for any thing, `[printed name of X]` | 7a |
| `[number]`-valued: `[score]`, `[the trample count]`, `[N in words]` | 7a |
| `[line break]` `[paragraph break]` `[bold type]` `[italic type]` `[roman type]` | 7a |
| `[if <cond>]...[otherwise if <cond>]...[otherwise]...[end if]` | 7a |
| `[one of]...[or]...[at random / cycling / stopping / purely at random]` | 7a |
| `[name of a To say phrase]` | 7a |
| `'` is printed as `"` unless inside a word (`don't`), as in Inform 7 | 7a |
| a `[paragraph break]` that ends a say leaves a blank line owed: printed before whatever is printed next, but not before the prompt (ADR-047) | 7c |
| blank lines as Inform 7 prints them (ADR-048): the output of two rules is set apart by a blank line; after going (not looking) the room's name is set off by one; a description that already ended its line (a say inside it did) gets no extra line break | 7c |
| **adaptive text** (7c): `[We] [we] [us] [our] [Our] [ourselves] [are] ['re] [have] [here] [now] [There] [there] [regarding X]`, and custom verbs `To flow is a verb.` then `[flow]` | 7c |
| `[It]` `[it]` `[There]` `[there]`: printed as written; the next verb then agrees as a singular (`[There] [are] a light` -> "There is a light") | Advent |
| modal verbs: `[can catch]` `[cannot carry]` `[can't go]` `[might try]` (printed as written) | Advent |
| `[']`: an apostrophe | Advent |

**Adaptive text in I7-lite** is always second person, present tense
(`[We] [are]` prints "You are"). `[regarding X]` makes the next verb agree
with X: `[regarding the stream][flow]` -> "flows", `[regarding the keys]
[are]` -> "are"; `[regarding them][are]` -> "are" with no thing named.
`[bracket]` and `[close bracket]` print `[` and `]`. `[parser command so far]` prints the command's verb, spelled out as Inform 7 does (`x` -> examine, `l` -> look, `i` -> inventory, `z` -> wait): Advent's "You can only examine one thing at a time." There is no
story-viewpoint switching. As in Inform 7
(checked against the real Advent), a paragraph about a thing agrees with
that thing, and each new turn starts with nothing named.

## 9. The library's rules and responses (ADR-028)

Every rule an author can unlist, replace or edit, by action and stage, in
the order they run. Response letters and default texts follow Inform 7.

**looking**

| Stage | Rule | Responses |
|---|---|---|
| carry out | room description heading rule | (A) "Darkness" |
| carry out | room description body text rule | (A) "It is pitch dark, and you can't see a thing." |
| carry out | room description paragraphs about objects rule | - |
| carry out | check new arrival rule | - |

**examining**

| Stage | Rule | Responses |
|---|---|---|
| carry out | standard examining rule | - |
| carry out | examine undescribed things rule | (A) "You see nothing special about [the noun]." |

**taking**

| Stage | Rule | Responses |
|---|---|---|
| check | can't take yourself rule | (A) "You are always self-possessed." |
| check | can't take other people rule | (A) "I don't suppose [the noun] would care for that." |
| check | can't take what's already taken rule | (A) "You already have that." |
| check | can't take scenery rule | (A) "That's hardly portable." |
| check | can't take what's fixed in place rule | (A) "That's fixed in place." |
| carry out | standard taking rule | - |
| report | standard report taking rule | (A) "Taken." |

**dropping**

| Stage | Rule | Responses |
|---|---|---|
| check | can't drop what's already dropped rule | (A) "[The noun] [are] already here." |
| check | can't drop what's not held rule | (A) "You haven't got that." |
| check | can't drop clothes being worn rule | - : "(first taking [the noun] off)", then silently tries taking it off (not editable in I7-lite) |
| carry out | standard dropping rule | - |
| report | standard report dropping rule | (A) "Dropped." |

**going**

| Stage | Rule | Responses |
|---|---|---|
| check | can't go through closed doors rule | (A) "You can't, since [the door gone through] [are] closed." |
| check | can't go that way rule | (A) "You can't go that way." |
| carry out | move player and vehicle rule | - |
| report | describe room gone into rule | - |

**taking inventory**

| Stage | Rule | Responses |
|---|---|---|
| carry out | print empty inventory rule | (A) "You are carrying nothing." |
| carry out | print standard inventory rule | (A) "You are carrying:[line break]" |

**putting it on**

| Stage | Rule | Responses |
|---|---|---|
| check | can't put something on itself rule | (A) "You can't put something on top of itself." |
| check | can't put onto what's not a supporter rule | (A) "Putting things on [the second noun] would achieve nothing." |
| check | carrying requirements rule | - |
| check | can't put clothes being worn rule | - : "(first taking [the noun] off)", then silently tries taking it off (not editable in I7-lite) |
| carry out | standard putting rule | - |
| report | standard report putting rule | (A) "You put [the noun] on [the second noun]." |

**inserting it into**

| Stage | Rule | Responses |
|---|---|---|
| check | can't insert something into itself rule | (A) "You can't put something inside itself." |
| check | can't insert into what's not a container rule | (A) "[The second noun] can't contain things." |
| check | can't insert into closed containers rule | (A) "[The second noun] [are] closed." |
| check | carrying requirements rule | - |
| check | can't insert clothes being worn rule | - : "(first taking [the noun] off)", then silently tries taking it off (not editable in I7-lite) |
| carry out | standard inserting rule | - |
| report | standard report inserting rule | (A) "You put [the noun] into [the second noun]." |

**wearing**

| Stage | Rule | Responses |
|---|---|---|
| check | can't wear what's not clothing rule | (A) "You can't wear that!" |
| check | can't wear what's already worn rule | (A) "You're already wearing that!" |
| check | carrying requirements rule | - |
| carry out | standard wearing rule | - |
| report | standard report wearing rule | (A) "You put on [the noun]." |

**taking off**

| Stage | Rule | Responses |
|---|---|---|
| check | can't take off what's not worn rule | (A) "You're not wearing that." |
| carry out | standard taking off rule | - |
| report | standard report taking off rule | (A) "You take off [the noun]." |

**opening**

| Stage | Rule | Responses |
|---|---|---|
| check | can't open unless openable rule | (A) "That's not something you can open." |
| check | can't open what's locked rule | (A) "It seems to be locked." |
| check | can't open what's already open rule | (A) "That's already open." |
| carry out | standard opening rule | - |
| report | standard report opening rule | (A) "You open [the noun]." |

**closing**

| Stage | Rule | Responses |
|---|---|---|
| check | can't close unless openable rule | (A) "That's not something you can close." |
| check | can't close what's already closed rule | (A) "That's already closed." |
| carry out | standard closing rule | - |
| report | standard report closing rule | (A) "You close [the noun]." |

**locking it with**

| Stage | Rule | Responses |
|---|---|---|
| check | can't lock without a lock rule | (A) "That doesn't seem to be something you can lock." |
| check | can't lock what's already locked rule | (A) "It's locked at the moment." |
| check | can't lock what's open rule | (A) "First you would have to close [the noun]." |
| check | can't lock without the correct key rule | (A) "That doesn't seem to fit the lock." |
| carry out | standard locking rule | - |
| report | standard report locking rule | (A) "You lock [the noun]." |

**unlocking it with**

| Stage | Rule | Responses |
|---|---|---|
| check | can't unlock without a lock rule | (A) "That doesn't seem to be something you can unlock." |
| check | can't unlock what's already unlocked rule | (A) "It's unlocked at the moment." |
| check | can't unlock without the correct key rule | (A) "That doesn't seem to fit the lock." |
| carry out | standard unlocking rule | - |
| report | standard report unlocking rule | (A) "You unlock [the noun]." |

**switching on**

| Stage | Rule | Responses |
|---|---|---|
| check | can't switch on unless switchable rule | (A) "That isn't something you can switch." |
| check | can't switch on what's already on rule | (A) "That's already on." |
| carry out | standard switching on rule | - |
| report | standard report switching on rule | (A) "You switch [the noun] on." |

**switching off**

| Stage | Rule | Responses |
|---|---|---|
| check | can't switch off unless switchable rule | (A) "That isn't something you can switch." |
| check | can't switch off what's already off rule | (A) "That's already off." |
| carry out | standard switching off rule | - |
| report | standard report switching off rule | (A) "You switch [the noun] off." |

**consulting it about** (the noun is the thing; the topic is the words typed)

| Stage | Rule | Responses |
|---|---|---|
| report | block consulting rule | (A) "You discover nothing of interest in [the noun]." |

**asking it about**

| Stage | Rule | Responses |
|---|---|---|
| check | block asking rule | (A) "There is no reply." |

**telling it about**

| Stage | Rule | Responses |
|---|---|---|
| check | telling yourself rule | (A) "You talk to yourself a while." |
| check | block telling rule | (A) "This provokes no reaction." |

**answering it that**

| Stage | Rule | Responses |
|---|---|---|
| check | block answering rule | (A) "There is no reply." |

**attacking**

| Stage | Rule | Responses |
|---|---|---|
| check | block attacking rule | (A) "Violence isn't the answer to this one." |

**entering** (I7-lite has no enterable things: entering is always refused.
Inform's one response adapts to the verb; here it is three.)

| Stage | Rule | Responses |
|---|---|---|
| check | can't enter what's not enterable rule | (A) "That's not something you can enter." (B) "That's not something you can sit down on." (C) "That's not something you can stand on." |

**waiting**

| Stage | Rule | Responses |
|---|---|---|
| report | standard report waiting rule | (A) "Time passes." |

**requesting the score**

| Stage | Rule | Responses |
|---|---|---|
| carry out | announce the score rule | - |

**saving the game**

| Stage | Rule | Responses |
|---|---|---|
| carry out | save the game rule | - |

**restoring the game**

| Stage | Rule | Responses |
|---|---|---|
| carry out | restore the game rule | - |

**quitting the game**

| Stage | Rule | Responses |
|---|---|---|
| carry out | quit the game rule | - |

**internal rules** (in no rulebook; their responses can be edited)

| Stage | Rule | Responses |
|---|---|---|
| - | list writer internal rule | (D) "providing light", (K) "providing light and being worn", (L) "being worn": the inventory's notes in brackets |
| - | yes or no question internal rule | (A) "Please answer yes or no." - printed before the prompt, with no line break of its own (as Inform 6 code prints it) |

## 10. Activities (ADR-031)

An *action* is what happens; an *activity* is how the library does
something along the way - printing a name, writing a room's paragraphs.
Each activity has three rulebooks: `Before <activity>`, `Rule for
<activity>` and `After <activity>`. The before and after rules all run;
the first *for* rule that applies decides, and the library's own way is
skipped, unless the rule ends with `continue the activity`.

| Activity | Written as | The library's own way |
|---|---|---|
| printing a parser error | `Rule for printing a parser error when the latest parser error is the not a verb I recognise error: ...` | Inform 7's message for that error |
| printing the name | `Rule for printing the name of the lamp: ...` | the printed name |
| printing the banner text | `After printing the banner text: ...` | title, headline, release line |
| printing the name of a dark room | `Rule for printing the name of a dark room: ...` | "Darkness" (heading response (A)) |
| printing the description of a dark room | `Rule for printing the description of a dark room: ...` | "It is pitch dark, and you can't see a thing." (body text response (A)) |
| writing a paragraph about | `Rule for writing a paragraph about the rock: ...` | nothing: the thing is listed as usual |

- `of`/`about` takes a thing (`the lamp`), a kind (`a container`) or
  `something`; a `when` condition may follow. As with actions, rules about a
  particular thing run before rules about a kind, and those before rules
  about anything.
- Inside the rules, `the item described` is the thing being named or
  described.
- Every name the library prints goes through *printing the name*: room
  descriptions, lists, inventory, messages, the status line. A name rule
  that says its own thing's name (`say "[the box] (empty)"`) gets the plain
  name there, not an endless loop.
- A *writing a paragraph* rule that says something gives the thing its own
  paragraph and leaves it out of "You can see ..."; one that says nothing
  (`do nothing`) leaves the thing as it was, as in Inform 7.
- An author's rule can run an activity itself, as Advent's heading and body
  rules do: `begin the X activity`, `if handling the X activity:`,
  `end the X activity`, or all three at once with
  `carry out the X activity [with <thing>]`.

**The author's own activities** (ADR-053), as in Inform 7:

    Forest-running is an activity.
    For forest-running: say "You run through the trees."
    For forest-running when in Forest3: ...
    First for forest-running when the player carries the bead: ...; continue the activity.
    Before forest-running when in the Garden: ...
    Carry out running: carry out the forest-running activity.

`For X:` is short for `Rule for X:`. They work as the library's own
activities do: all the before rules; then the first for rule that applies
(`First` rules first, then the more specific: a `when` rule before one
without); then all the after rules. An activity is on nothing: `... is an
activity on things` is not supported.

*Printing a parser error* (ADR-034) runs when a command cannot be
understood. `the latest parser error` says why, by Inform 7's own names
(checked against the compiled Advent): I7-lite's parser makes

| The ... error | Inform 7's message |
|---|---|
| I beg your pardon | I beg your pardon? |
| not a verb I recognise | That's not a verb I recognise. |
| can't see any such thing | You can't see any such thing. |
| not sure what it refers to | I'm not sure what 'it' refers to. |
| can't see it at the moment | You can't see 'it' (the lamp) at the moment. |
| didn't understand | I didn't understand that sentence. |
| can't use multiple objects | You can't use multiple objects with that verb. |
| nothing to do | There are none at all available! |

(`nothing to do` is the *parser nothing error internal rule*'s response B
in Inform 7: the one Advent edits for an empty TAKE ALL.) Inform 7's other
error names (`said too little`, `can only do that to something animate`,
...) can be used in conditions, but I7-lite's parser never makes them. A parser
error is a message, not a paragraph: what an after rule prints follows it
on the next line, as in Inform 7. Its responses (`The parser error internal
rule response (N) is ...`) cannot be edited: write a rule for the activity.

Other Inform 7 activities (the announcements of darkness and light,
supplying a missing noun, choosing notable locale objects, listing
contents, and so on) are recognised by name and refused with a problem
message that says so.

## Not supported (a problem message says so)

Relations and relation verbs, tables other than topic tables, activities other than the six in
section 10 and the author's own (on nothing), editing the parser error internal rule's responses, texts
given to a phrase that use the giver's own names, `To decide which/what`, Inform 6 inclusions `(- -)`,
extensions (`Include`), `does nothing`, action variables, kinds of action
(`... is attempting entry`), rulebooks the author makes,
backdrops, regions, scenes, kinds of value, units,
lists, and any viewpoint other than second person present.

## Testing commands

Compile with `zforge compile --testing` to add three of Inform 7's testing
commands, for studying a game while you play it: `rules` (and `rules off`)
shows each rule as it applies, `actions` (and `actions off`) shows each
action as it starts and how it ends, and `tree` shows where every room and
thing is. An ordinary build doesn't have them, just as a released Inform 7
game doesn't. See [TOUR.md](TOUR.md) for an example, and ADR-038.
