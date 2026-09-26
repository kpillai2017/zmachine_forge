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
  indentation).
* Words are case-insensitive except inside quoted text.

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
| `The hook is a supporter in the Cloakroom.` | with a kind | 7a |
| `The cloak is on the hook.` / `in the box` | placement on a supporter / in a container | 7a |
| `The player wears a velvet cloak.` / `carries` | the player's possessions | 7a |
| `It is scenery.` / `It is fixed in place.` | `It` = the last thing named | 7a |
| `The hook is scenery.` `The box is open/closed/openable/locked/lockable.` | either/or properties | 7a |
| `The lamp is a device.` / `switched on` | a device (switching on/off) | 7b |
| `The grate is a door. It is north of X and south of Y.` | a two-sided door | 7b |
| `The grate is locked. The keys unlock the grate.` | lock and key | 7b |
| `The indefinite article of the water is "some".` | article | 7b |
| `The keys are plural-named.` / `privately-named` / `proper-named` | naming | 7b |

**Names.** A thing is called by its whole name (`velvet cloak`); every word
of the name also works alone in commands, in any order (`velvet`,
`cloak`). Articles `a an the some` are not part of names.

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

## 4. Understanding the player

| Sentence | Meaning | Step |
|---|---|---|
| `Understand "dark/black/satin" as the cloak.` | extra words for a thing | 7a |
| `Understand "hang [something] on [something]" as putting it on.` | a new grammar line for an action | 7a |
| `Understand "xyzzy" as casting xyzzy.` | grammar for a new action | 7a |
| `Understand "plugh" as north.` | a word for a direction | 7b |
| `Understand the command "grab" as "take".` | verb synonym | 7b |
| `... when the location is the Bar` (on an Understand line) | only there | after Cloak (decision in I7_SURVEY) |

Tokens: `[something]`, `[someone]`, `[things]` (treated as `[something]`),
`[text]` is not supported.

## 5. Actions

The standard actions (7a unless marked): looking, examining, taking,
dropping, going, taking inventory, putting it on, inserting it into,
wearing, taking off, waiting, requesting the score, saving the game,
restoring the game, quitting the game; 7b: opening, closing, locking it
with, unlocking it with, switching on, switching off. `read X` means
examining X; `undo` is handled before actions, as in Inform 7.

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
other than going`, `examining or taking the cloak`; optional
`in <room>` / `in the presence of X` (7b) and `when <condition>`.

One-line forms (7b): `Instead of eating the lamp, say "No.".`,
`Instead of thinking, try looking.`

Outcomes follow Inform 7: `Instead` and `After` rules stop the action when
they finish; `Before`, `Check`, `Carry out`, `Report` continue unless they
say `stop the action` (or end a phrase with `instead`, 7b).
`continue the action` overrides the default.

## 7. Phrases (inside rules)

| Phrase | Step |
|---|---|
| `say "text"` | 7a |
| `now X is Y` / `now X is in Y` / `now the player carries X` | 7a |
| `move X to Y` / `remove X from play` | 7a |
| `increase X by N` / `decrease X by N` / `increment X` | 7a |
| `let X be <value>` | 7a |
| `if <cond>: ...` / `otherwise if` / `otherwise` (indented or one line) | 7a |
| `repeat with I running from 1 to 10: ...` / `while <cond>: ...` | 7a |
| `end the story` / `end the story finally` / `end the story saying "..."` | 7a |
| `stop the action` / `continue the action` / `rule succeeds` / `rule fails` | 7a |
| `try <action>` / `silently try <action>` | 7b |
| `<phrase> instead` (do it, then stop) | 7b |
| `To <phrase> (N - a number): ...` user phrases; `To decide whether ...`; `To say <name>: ...` | 7a |

Conditions: `X is Y`, `X is not Y`, `X is in Y`, `X is on Y`, `the player
carries X`, `the player is in Y`, `X is <property>`, `the noun is X`,
`N is greater than / less than / at least / at most M` (and `>` `<`
`>=` `<=`), `A and B`, `A or B`, `a random chance of 1 in 3 succeeds`.
The location, the noun, the second noun, the player, the score, the turn
count are built in.

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
| **adaptive text** (7c): `[We] [we] [us] [our] [Our] [ourselves] [are] ['re] [have] [here] [now] [There] [there] [regarding X]`, and custom verbs `To flow is a verb.` then `[flow]` | 7c |

**Adaptive text in I7-lite** is always second person, present tense
(`[We] [are]` prints "You are"). `[regarding X]` makes the next verb agree
with X: `[regarding the stream][flow]` -> "flows", `[regarding the keys]
[are]` -> "are". There is no story-viewpoint switching.

## Not supported (a problem message says so)

Relations and relation verbs, tables, activities (`Rule for ...`),
response edits (`... response (A) is`), Inform 6 inclusions `(- -)`,
extensions (`Include`), rulebook changes (`is listed instead of`,
`does nothing`), `Definition:`, backdrops, regions, scenes, kinds of
value, `[text]` tokens, `Understand ... as something new`, units,
lists, and any viewpoint other than second person present.
