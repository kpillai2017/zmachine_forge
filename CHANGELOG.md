# Changelog

What changed from one version to the next, in plain words. The reasons
behind each change are in [docs/DECISIONS.md](docs/DECISIONS.md), by number
(ADR-021 and so on).

## Unreleased

- **A game can have many more actions.** Each action's rulebook used one of the
  Z-machine's 240 global variables, so a big game ran out ("too many globals").
  They are now table constants, which cost none. ZIL-lite's CONSTANT accepts a
  table.
- **The Island of Despair is about half as long again.** New chapters from the
  novel: the seasons (sow with the rains, and hedge your field against the
  hares), milk and cheese, a tallow lamp and the glittering vault, the rescue of
  Friday's father and the Spaniard, the great boat, and the five mutineers left
  behind. The walkthrough wins with 206 of 206 in 439 moves.

### Writing games (the Inform 7 compiler)

- **A grammar line with two fixed words and no object works**, such as
  `Understand "write in journal" as writing`. A line needing more fixed words
  than the grammar table can hold now gets a problem message; it used to
  stop the compiler with an internal error.
- **Possessive words can be typed**, such as EXAMINE COOK'S POT.
- **The word "of" in a name can be typed**, such as EXAMINE BAG OF SHOT.

### Writing games (ZIL)

- A backslash in an atom now quotes the next character without becoming part
  of the atom's name (`COOK\'S` gives the word "cook's").
- `<SYNTAX WRITE IN JOURNAL = V-WRITE>`: two words may follow the verb on a
  line with no OBJECT.

### Examples

- *The Island of Despair*, a long game after *Robinson Crusoe*, with its
  walkthrough.

## 0.2.0 - 2026-09-29

The first release. zforge grew from a version-5 toolchain into one for
versions 5 to 8, with a compiler for a part of Inform 7.

### Playing games (the interpreter)

- Plays Z-machine versions **5, 6, 7 and 8** (it was version 5 only).
  Version 6's eight windows are drawn as text, one character to a unit.
- Opens **Blorb files** (`.zblorb`), the form most games are downloaded in.
  A Blorb holding a Glulx game gets a clear message instead (ADR-061).
- The full-screen display follows the terminal as it is resized.
- Checked against czech (the Z-machine test suite: 406 checks passed,
  none failed, and the author's own expected output line for line) and real games:
  Crowther's *Adventure* and Andrew Plotkin's *Cold Iron* (Inform 7),
  *Jigsaw* (Inform 6), and Emily Short's *Bronze*.

### Writing games (the compilers)

- **I7-lite**, a compiler for a part of Inform 7, is new. Games are written
  in Inform 7's sentences and built for z5, z6, z7 or z8. It covers rooms,
  things, doors and keys, kinds, properties, rules and their responses,
  activities, definitions, topics and topic tables, parts, times of day,
  other people and giving them orders, and Inform's standard actions and
  messages. What it covers is in [docs/I7_LITE.md](docs/I7_LITE.md).
- Its output is checked against the real Inform 7: our port of the
  opening of *Adventure* prints exactly what the real game prints, and our
  port of *Bronze* wins with the official walkthrough.
- Two example games: *Cloak of Darkness* and *The Glasshouse Bequest*.
- The ZIL-lite compiler builds for versions 5 to 8 too; the version-5
  output is byte for byte what 0.1.0 made.

### Tools

- `zforge --version`.
- `zbuilder compare <commit>` builds and plays every example with an
  earlier version and this one, and says what changed (ADR-056).
- The GitHub checks run on Python 3.11, 3.12 and 3.13, keep the downloads
  between runs, and no longer fail when a download site is down.
- Installable with `pip install git+https://github.com/kpillai2017/zmachine_forge`.

### Reading the code

- Comments explain each part of the code, and two guides walk a beginner
  through it: [how the compiler works](docs/HOW_THE_COMPILER_WORKS.md) and
  [how the interpreter works](docs/HOW_THE_INTERPRETER_WORKS.md).

### Known limits

- I7-lite is a part of Inform 7, not all of it: most real Inform 7 games
  will not compile unchanged. [docs/I7_SURVEY.md](docs/I7_SURVEY.md)
  measures how far real games are.
- The interpreter is written to be read, not to be fast: a large Inform 7
  game can take several seconds a turn.
- [docs/KNOWN_GAPS.md](docs/KNOWN_GAPS.md) lists the rest.

## 0.1.0 - 2026-09-26

The starting point: a Z-machine version 5 interpreter, assembler and
disassembler, the ZIL-lite compiler, and the zbuilder workflow that built
them (tiers 0 to 4).
