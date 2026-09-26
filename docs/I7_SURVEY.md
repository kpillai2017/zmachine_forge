# I7 survey: what a real Inform 7 game uses

**Source studied:** `stories/Advent_Crowther_source.txt`, the Inform 7 (build
6L38) port of Crowther's 1976 *Adventure* by Chris Conley, 2,013 lines. It is
pinned in `stories/urls.txt`, and its compiled game `Advent_Crowther.z8` is
already a zforge regression case (`play-real-z8-advent`).

**Why:** before designing I7-lite (Tier 7), check the planned subset against
what a real author actually writes, rather than what we imagine they write.

**Method:** every count below comes from a search over the whole file
(`grep -cE`), so each can be re-checked. Sentence-level examples were read
in context (lines 28-300, 413-500 and 527-680 in full).

## Headline finding

Advent **cannot be compiled by any subset compiler as written**, and that is
not a flaw in the plan. About a quarter of the source changes Inform 7's
built-in library (the *Standard Rules*) from the inside:

- it replaces library rules (`Crowther's room description heading rule is
  listed instead of the room description heading rule`, line 425);
- it uses library internals (`visibility ceiling`, `visibility level count`,
  the *printing the description of a dark room* activity, lines 427-500);
- it rewrites 33 library messages (`The standard report taking rule
  response (A) is "OK."`);
- it contains 11 Inform 6 inclusions (`(- style roman; -)`).

A real I7 game is written *against* the Standard Rules, a very large
library. I7-lite brings its own small runtime library, so games that reach
into the Standard Rules are out of reach by design. What I7-lite *can* do
is make the **surface language** an author writes every day match real
Inform 7, so that small new games (like Cloak of Darkness) and hand-ported
parts of real ones read like genuine I7.

## Counts (whole file)

| Construct | Uses | Planned? | Verdict |
|---|---:|---|---|
| Understand lines (all kinds) | 164 | partly | **extend** (see below) |
| ... `Understand ... when <condition>` | 39 | no | consider after Cloak |
| ... `Understand the command(s) ... as something new` | 34 | no | later |
| `if` (block and one-line) | 73 | yes | keep |
| `<Room> is <direction> from/of <Room>` | 64 | "of" only | **add "from"** |
| `now X is Y` | 57 | yes | keep |
| Before / After action rules | 38 | yes | keep |
| `The short description ...` (custom property) | 36 | yes (value props) | keep |
| Response edits `... rule response (A) is` | 33 | no | out (library-coupled) |
| `Instead of` | 31 | yes | keep; **add one-line form** |
| Relations and relation verbs | 30 | no | out |
| `try <action>` | 24 | **no** | **add (essential)** |
| Custom adaptive verbs `To flow is a verb.` | 19 | no | with adaptive text (decision) |
| Check / Carry out / Report | 17 | yes | keep |
| `To say <phrase>` definitions | 16 | yes (user phrases) | keep |
| `<Direction> is <Room>.` inside a room paragraph | 14 | no | **add** |
| Doors | 14 | "only if needed" | **add** |
| I6 inclusions `(- ... -)` | 11 | no | out |
| `move X to Y` | 11 | yes | keep |
| `To decide` | 10 | yes | keep |
| Regions | 9 | no | out |
| `Rule for <activity>` | 9 | no | out |
| `[if]` conditional text | 7 | yes | keep |
| `repeat` | 7 | yes | keep |
| Backdrops | 6 | no | out |
| Every turn | 5 | yes | keep |
| Tables | 5 | no | out |
| Definition: | 4 | no | out |
| `end the story` | 4 | yes | keep |
| Use options | 3 | partly | accept harmless ones (see below) |
| Containers / supporters | 2 | yes | keep (Cloak needs a supporter) |
| People / animals | 2 | yes | keep, minimal |
| Devices (`switching on/off`) | 1 | no | **add** (the lamp is central) |
| Scenes | 0 | no | out (confirmed) |
| `[one of] ... [at random]` text | 0 | yes | keep (common in other games) |

**Text substitutions:** 170 distinct, **722 uses**. The top ten are all
*adaptive text*: `[are]` x121, `[We]` x93, `[/b]` x53, `[regarding it]` x28,
`[here]` x27, `['re]` x27, `[we]` x18, `[us]` x14, `[There]` x13, `[now]` x11.
Almost every room description is written this way, e.g. (line 558):
`"[We] [are] standing at the end of a road[/b] before a small brick building."`

## Recommended changes to the planned I7-lite subset

**Add (cheap, and a real author uses them constantly):**

1. **`X is <direction> from Y`** as well as `of` (64 uses). Same meaning.
2. **`<Direction> is <Room>.`** inside a room's paragraph (14 uses), e.g.
   `Upstream is End of Road.`: a connection from the room being described.
3. **`try <action>`** (24 uses), e.g. `Instead of thinking about something,
   try thinking.` Missing from the plan entirely; without it, rules cannot
   redirect one action to another, which is how most games say
   "this verb means that one here".
4. **One-line rules**: `Instead of X, say "...".` and `Instead of X, try Y.`
   (the rule body after a comma, no colon or indentation).
5. **`... instead`** at the end of a phrase (`say nokeys instead`): do it,
   then stop the action.
6. **`is usually`** kind defaults: `A room is usually dark.`,
   `The printed name of a forest is usually "Forest".`
7. **Doors** (two-sided, open/closed, lockable): 14 uses, and the grate is
   the first real puzzle in Adventure.
8. **Devices**: the `device` kind with *switching on* / *switching off*
   (the lamp, the other half of the darkness puzzle).
9. **Synonyms**: `Understand "x/y" as <thing>` and `... as <direction>`
   (both appear throughout), and `Understand the command "x" as "y"`.
10. **Small properties**: `The indefinite article is "some"`,
    `privately-named`, `plural-named`.
11. **Harmless Use options** (`Use no deprecated features.`,
    `Use BRIEF room descriptions.`): accept them with a note rather than a
    problem message; `Use scoring` / `Use no scoring` switch the score.

**Consider after Cloak of Darkness works:**

- `Understand "..." as <direction/thing> when the location is <room>`
  (39 uses): only the *location* form, which covers most of them.

**Keep out (confirmed by this survey):** relations and relation verbs,
tables, activities (`Rule for ...`), response edits, Inform 6 inclusions,
rulebook surgery (`is listed instead of`), `Definition:`, backdrops,
regions, scenes, `as something new`. Each either needs the full Standard
Rules or is rare. Each still gets a clear "not supported in I7-lite"
problem message pointing to this document.

## Decision needed: adaptive text

Modern Inform 7 writes text so the story can switch person and tense:
`[We] [are]` prints "You are" in a second-person, present-tense story.
Advent uses it in almost every sentence (722 substitutions).

Options:

- **(a) Leave it out** (the original plan). I7-lite games write
  `"You are standing..."` directly. Simplest; but I7-lite text then looks
  like 2010-era Inform 7, and ported text must be hand-edited.
- **(b) Fixed-viewpoint subset (recommended).** Always second person,
  present tense: `[We]` -> "You", `[are]` -> "are", `[regarding X]` makes
  the next verb agree with X (singular "flows" / plural "flow"), and
  `To flow is a verb.` declares a custom verb. No story-viewpoint
  switching. About ten fixed substitutions plus one small verb-agreement
  routine in the runtime library. Adds a few days, but makes I7-lite text
  look like modern Inform 7.

## Tier 7 bonus: a test against the real Inform 7

`Advent_Crowther.z8` was built by the real Inform 7 from this source. So:

1. Port the opening area (End of Road, Hill, Building, Valley, Forests,
   Slit, Outside Grate: lines 527-800) into I7-lite as
   `examples/advent_opening.ni`, keeping the player-visible text.
2. Play the same walkthrough on our build and on the real
   `Advent_Crowther.z8`.
3. Compare what the player sees: room names, descriptions, "OK." /
   "Taken." messages, the dark-room warning.

This is an *independent oracle*: differences are either I7-lite bugs or
known, documented simplifications (e.g. keyword travel via relations).
The opening area needs roughly: rooms and descriptions, both map forms,
things with initial appearances, a device (lamp), darkness, a locked door
(grate) and keys, synonyms, and a few Instead / After rules, i.e. the
"Add" list above.

## What this survey does not claim

- One game is one data point. Advent is a map-and-treasure game with
  almost no containers, people or conversation, so those rows are low here
  but high in other games. Cloak of Darkness (supporter, wearable cloak,
  a counter) covers some of that; a second survey of a different kind of
  game would cover more.
- The counts are pattern counts, not a parse. They are good to within a
  few, and each is re-checkable with the `grep -cE` patterns.
