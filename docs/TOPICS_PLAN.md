# Plan: topics in I7-lite

A **topic** is whatever the player types in a place where the game expects
free words rather than a thing: ASK THE BEAST ABOUT *THE ROSE GARDEN*,
LOOK UP *ELEPHANT* IN THE NOTES, THINK ABOUT *MY FATHER*. The words don't
have to name anything in the game, or even be words the game knows.

This plan says what Inform does, what I7-lite supports, how it works inside
zforge, and in what order it is built.

**Status:** steps A and B are done (ADR-045; `docs/I7_LITE.md`, section 5).
Steps C and D are next. Step E is parked (see the end).

## Why it matters

* **Many real games use topics.** Conversation (ASK/TELL), books and notes
  (LOOK UP, CONSULT) and hint commands all depend on them.
* **Bronze needs them.** The port fakes LOOK UP: each subject in Lucrezia's
  notes and the Records Room's papers is a hidden "topical" object. So LOOK
  UP only works where those objects are, and their names clash with real
  things (X TAMBOURINE in the Study asks "the image or the note about the
  cobbler?"). Bronze's hint system (HINT, THINK ABOUT, REMEMBER, about 630
  lines of the original) was left out largely because it needs topics.

## What Inform 7 does

**The `[text]` token.** In an Understand line, `[text]` matches one or more
words at that point:

    Understand "hint about [text]" as hinting topically about.
    Hinting topically about is an action applying to one topic.

The words matched are "the topic understood". If other words follow the
token in the grammar line (the "in" of LOOK UP [text] IN [something]), the
topic stops before them.

**Four built-in actions use topics**, with these default replies (checked
against Cold Iron, built with the official Inform 7):

| Action | Commands | Default reply |
|---|---|---|
| consulting it about | CONSULT X ABOUT T, LOOK UP T IN X, READ ABOUT T IN X | "You discover nothing of interest in [the noun]." |
| asking it about | ASK X ABOUT T | "There is no reply." |
| telling it about | TELL X ABOUT T | yourself: "You talk to yourself a while."; someone else: "This provokes no reaction." (from memory; to be checked against a real game) |
| answering it that | ANSWER T TO X, SAY T TO X | "There is no reply." |

**Matching a topic** in a rule uses a quoted pattern, with a slash between
alternative words and "or" between alternative phrases:

    Instead of asking the Beast about "roses/rose" or "rose garden", say "...".
    Instead of consulting the notes about "djinn/genie" or "elephant", say "...".

A slash separates the words that may stand in *one* place: "roses/rose
garden" would mean "roses garden" or "rose garden". Whole phrases are joined
with "or". `--` among the words means the place may be left out ("the/--
djinn").
    if the topic understood matches "father" or "my father", ...

"Matches" means the whole topic; "includes" means somewhere inside it.

**Tables of topics.** Many games list topics in a table and look them up:

    Instead of hinting topically about a topic listed in the Table of Topic Hints:
        say "[reply entry]".

**Saying the topic:** `say "[the topic understood]"` prints the words the
player typed.

## What I7-lite would support

1. The `[text]` token in Understand lines, anywhere a `[something]` can go.
2. Actions "applying to one topic" and "applying to one thing and one
   topic", and the four built-in actions with Inform's default replies.
3. Topic patterns in rule preambles, `matches` and `includes` in conditions,
   and `[the topic understood]` in text.
4. **Topic tables**, limited to what topic look-ups need: a table with a
   topic column and text columns, `a topic listed in the Table of X`, and
   `[reply entry]` (the matching row's entry). Not general tables. This is
   the one real choice in the plan (see "Questions" below).

## How it would work inside zforge

**In the command parser** (`zforge/lib/parser.zil`, inside `<IFFLAG (I7
...)>`, so ZIL games don't change and their golden builds stay identical):

* A grammar slot can be marked as a topic. Instead of looking for a thing,
  the parser takes the words from that point up to the next word the line
  expects (the "in" of LOOK UP ... IN ...), or to the end. It records where
  the topic starts in the command and how many words it has.
* Today the parser refuses any command with a word it doesn't know, before
  it tries any grammar line. That check must move after the grammar line is
  chosen, and skip the topic's words: LOOK UP ZANZIBAR IN THE NOTES has to
  work even though "zanzibar" is nowhere in the game.
* Matching a pattern compares the topic's words with dictionary words.
  Words the game doesn't know can't match a pattern, but they can still be
  printed, because `[the topic understood]` copies the letters the player
  typed.

**In the compiler** (`zforge/compiler/i7/`):

* Understand lines with `[text]` become grammar rows with a topic slot.
* Each quoted topic pattern is compiled into a small routine that checks the
  recorded words against the pattern's alternatives. Every word in a pattern
  goes into the dictionary.
* A topic table becomes a list of (pattern routine, reply) pairs, searched in
  order. The first row that matches gives the reply entry.

**A Z-machine detail.** Dictionary words keep only their first 9 letters
(Standard §3.7), so "remembrance" and "rememberin" look alike. It's the same
for every word in a Z-machine game, and Inform has the same limit.

## Order of work, with a check at each step

| Step | What | How it's checked |
|---|---|---|
| A | The `[text]` token, the topic understood and printing it; unknown words allowed in a topic | New tests; the ZIL golden builds stay identical |
| B | Topic patterns in rules, `matches` and `includes`; the four built-in actions and their replies | Tests; the same commands give the same replies on I7-lite and on Cold Iron |
| C | Topic tables | Tests; small example games |
| D | Bronze: replace the fake "topical" objects with real topics, so LOOK UP works anywhere and X TAMBOURINE no longer asks which | Bronze's walkthrough still wins; LOOK UP replies compared with the real game |
| E (later) | Bronze's hint system: the Table of Topic Hints, THINK ABOUT and HINT | Compared with the real game. Its REMEMBER [thing] also needs `[any seen thing]` grammar and "Definition:" adjectives, which are separate features |

Steps A and B are most of the work. C is small once B exists. D shrinks the
Bronze port and fixes its known look-up problems. E is a feature of its own
after that.

## Decisions

1. **Topic tables (step C): yes**, limited to topic look-ups (a topic column
   and text columns, `a topic listed in`, `[reply entry]`), not Inform's
   general tables.
2. **Step E (Bronze's hint system): parked.** It is large, and apart from
   topics it needs features mostly Bronze would use ("[any seen thing]",
   links between puzzles). "Definition:" adjectives are the exception - Cold
   Iron needs them too - and would be the next sensible feature on their
   own; after that, the hint system is a smaller step.
