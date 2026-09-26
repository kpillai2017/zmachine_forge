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
| `Every room has a number called the visit count.` | every room gets it (starting at 0) | Advent |
| `Every room has a text called the short description.` `The short description is "[We]['re] here again."` | a text property; the short form means the last thing named | Advent |
| `The Lab, the Hall and the Yard are lighted.` | several subjects at once | Advent |

## 4. Understanding the player

| Sentence | Meaning | Step |
|---|---|---|
| `Understand "dark/black/satin" as the cloak.` | extra words for a thing | 7a |
| `Understand "hang [something] on [something]" as putting it on.` | a new grammar line for an action | 7a |
| `Understand "xyzzy" as casting xyzzy.` | grammar for a new action | 7a |
| `Understand "plugh" as north.` | a word for a direction | 7b |
| `Understand the command "grab" as "take".` | verb synonym | 7b |
| `Understand the commands "open", "close" as something new.` | forget their earlier grammar | Advent |
| `Understand nothing as dropping.` | forget an action's earlier grammar | Advent |
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
| `increase X by N` / `decrease X by N` / `increment X` | 7a |
| `let X be <value>` | 7a |
| `if <cond>: ...` / `otherwise if` / `otherwise` (indented or one line) | 7a |
| `repeat with I running from 1 to 10: ...` / `while <cond>: ...` | 7a |
| `end the story` / `end the story finally` / `end the story saying "..."` | 7a |
| `stop the action` / `continue the action` / `rule succeeds` / `rule fails` | 7a |
| `try <action>` / `silently try <action>` | 7b |
| `<phrase> instead` (do it, then stop) | 7b |
| `To <phrase> (N - a number): ...` user phrases; `To decide whether ...`; `To say <name>: ...` | 7a |
| `say line break` / `say paragraph break` | Advent |

Conditions: `X is Y`, `X is not Y`, `X is in Y`, `X is on Y`, `the player
carries X`, `the player is in Y`, `X is <property>`, `the noun is X`,
`N is greater than / less than / at least / at most M` (and `>` `<`
`>=` `<=`), `A and B`, `A or B`, `a random chance of 1 in 3 succeeds`,
`X encloses Y`, `the player consents` (a yes/no question), `in darkness`,
`X is ""` (a text property with no text).
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
| check | can't drop what's not held rule | (A) "You haven't got that." |
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
| carry out | standard putting rule | - |
| report | standard report putting rule | (A) "You put [the noun] on [the second noun]." |

**inserting it into**

| Stage | Rule | Responses |
|---|---|---|
| check | can't insert something into itself rule | (A) "You can't put something inside itself." |
| check | can't insert into what's not a container rule | (A) "[The second noun] can't contain things." |
| check | can't insert into closed containers rule | (A) "[The second noun] [are] closed." |
| check | carrying requirements rule | - |
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

## Not supported (a problem message says so)

Relations and relation verbs, tables, activities (`Rule for ...`,
`After printing the banner text`), Inform 6 inclusions `(- -)`,
extensions (`Include`), `does nothing`, action variables, kinds of action
(`... is attempting entry`), rulebooks the author makes, `Definition:`,
backdrops, regions, scenes, kinds of value, `[text]` tokens, units,
lists, and any viewpoint other than second person present.
