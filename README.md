# zmachine_forge

In the 1980s, Infocom sold text adventures such as Zork. You typed what you
wanted to do ("open the mailbox", "go north") and the game told you what
happened. To sell the same game for dozens of different home computers,
Infocom ran every game on an imaginary computer called the **Z-machine**,
and wrote a small program for each real computer that pretended to be one.
People still write games for the Z-machine today, mostly in a language
called **Inform 7**, which reads almost like English.

This project rebuilds that whole chain in Python, written to be read and
learned from rather than to be fast:

- **a player** (an *interpreter*) that runs Z-machine games. It handles
  versions 5, 6, 7 and 8 of the machine, which covers almost every modern
  game;
- **a translator for Inform 7** that turns a game written in English-like
  sentences into a Z-machine game file;
- **a compiler for ZIL**, the language Infocom themselves used, which the
  Inform 7 translator also uses as its stepping stone;
- **an assembler and disassembler**, so you can see the machine
  instructions a game is made of;
- **zbuilder**, the AI-assisted workflow that planned, built and checked
  all of the above.

Everything follows the official description of the machine, the
[Z-Machine Standards Document 1.1](https://inform-fiction.org/zmachine/standards/z1point1/index.html).
The code quotes it by section number, so you can read the two side by side.

The compiler, the interpreter, and these documents were written with the
help of an AI, a large language model: see [How it was built](#how-it-was-built).

## Getting set up

You need Python 3.13. Nothing else is required to play or compile games;
the two extra tools in `requirements.txt` are only for running the tests.

```bash
cd zmachine_forge
pip install -r requirements.txt     # pytest and ruff, for the tests
```

Run the commands in this README from the `zmachine_forge` folder; that's
all `python -m zforge` needs. To use it from another folder too, first run
`export PYTHONPATH=/path/to/zmachine_forge`.

If you use [direnv](https://direnv.net/), you can make your own `.envrc`
in the folder (it isn't part of the project, so each person keeps their
own). This one sets the path, and loads your `.env` settings for zbuilder
if you have any:

```bash
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
dotenv_if_exists .env
```

## Playing a game

The quickest start is the included example, *Cloak of Darkness*, the small
game people traditionally write to try out a new adventure system:

```bash
./start.sh
```

For something longer, try *The Glasshouse Bequest*: a treasure hunt in a
locked house and its overgrown garden, with puzzles, traps and a few red
herrings. It was written for this project in the part of Inform 7 that
zforge understands, so its source, `examples/glasshouse.ni`, is also a
good example to learn from:

```bash
python -m zforge compile examples/glasshouse.ni -o glasshouse.z8
python -m zforge run glasshouse.z8
```

If you get stuck, `examples/glasshouse_walkthrough.txt` has the full
solution. It gives everything away, so only look if you mean to.

To play any other Z-machine game, point zforge at its file:

```bash
python -m zforge run game.z8
```

In a terminal you get a full-screen display with a status line at the
top. Add `--ui plain` for simple scrolling text, `--script moves.txt` to
type the commands from a file, and `--transcript log.txt` to keep a copy
of everything the game says.

`python -m zbuilder stories` downloads the free games we test against,
including Crowther's original *Adventure* (in its Inform 7 version) and
Andrew Plotkin's *Cold Iron*, into `stories/`.

## Writing your own game

Put this in a file called `lamp.ni`:

```
"The Lamp" by You

The Hall is a room. "A bare hall."
The brass lamp is in the Hall.
```

then build it and play it:

```bash
python -m zforge compile lamp.ni -o lamp.z8
python -m zforge run lamp.z8
```

You can walk around, take and drop things, open doors, switch on lamps,
write your own rules ("Instead of taking the lamp: say "It's too hot.""),
and a good deal more. zforge understands a large part of Inform 7, but not
all of it. [docs/I7_LITE.md](docs/I7_LITE.md) lists what you can write,
and when you use something it doesn't know, it tells you so in plain words,
naming the line.

Games written in ZIL (`.zil` files) are built the same way:
`python -m zforge compile examples/cloak.zil -o cloak.z5`.

### Which version of the Z-machine?

Versions 5 and 8 are the usual choices. Version 8 allows bigger games, and
the Inform 7 translator uses it unless you say otherwise. Version 6 was
Infocom's graphical machine, with several windows on the screen at once.
zforge runs it on an ordinary text terminal: the windows work, but there
are no pictures. Version 7 was hardly ever used, but it's supported for
completeness.

Pick one with `--target z5` (or `z6`, `z7`, `z8`), or set it once for a
folder with a `zforge.toml` file containing `target = "z8"`.
`python -m zforge info --versions` shows exactly what changes from one
version to the next.

## Looking inside

This is what the project is for. Some starting points:

- **Start from the beginning.** If compilers and interpreters are new to
  you, read [docs/HOW_THE_COMPILER_WORKS.md](docs/HOW_THE_COMPILER_WORKS.md)
  and then [docs/HOW_THE_INTERPRETER_WORKS.md](docs/HOW_THE_INTERPRETER_WORKS.md).
  They build a tiny program and look at what every stage makes of it, and
  explain the ideas as they go.
- **Follow one command through the whole system.**
  [docs/TOUR.md](docs/TOUR.md) takes "take lamp" from the line of English
  that creates the lamp to the Z-machine instruction that moves it into
  your hands.
- **Watch a game think.** Build with `--testing`, and while you play,
  type `rules` to see each rule as it applies, `actions` to see each action
  and how it ended, and `tree` to see where everything is. These are
  Inform's own testing commands, and ordinary builds leave them out.
- **See the in-between steps.** `--emit-zil` and `--emit-asm` save the ZIL
  and the assembly that your game was turned into.
  `python -m zforge disasm game.z8` works backwards from a game file, and
  `python -m zforge info game.z8` shows its header, objects and dictionary.
- **Trace the machine.** `python -m zforge run game.z8 --trace trace.txt`
  writes down every single instruction it carries out.
- **Look up the standard.** `python -m zforge spec insert_obj` (or a
  section number, or a phrase) finds the relevant part of the standard
  without going online, once `python -m zbuilder spec` has fetched it.

[docs/DESIGN.md](docs/DESIGN.md) suggests an order for reading the code.

## What it can't do (yet)

zforge doesn't show pictures or play sounds, and it can't run games made
for versions 1 to 4 of the machine. Its Inform 7 is a subset: most
everyday game-writing works, but features such as tables and scenes don't,
and a game that rewrites Inform's built-in library from the inside can't be
translated. [docs/KNOWN_GAPS.md](docs/KNOWN_GAPS.md) has the full list.

## How we know it works

Where we could, we checked zforge against the real thing rather than
against our own reading of the rules.

- Two well-known test programs, *czech* and *praxix*, exercise every part
  of the machine, and both pass.
- For Inform 7, we rewrote the opening of the real *Adventure* in the
  subset zforge understands. We then played the same commands on our
  version and on the game Inform 7 itself built, and they print the same
  thing, word for word. *Cold Iron* is used the same way to check how
  "take all" behaves.

To run every check yourself:

```bash
ruff check .                   # tidy code
pytest -q                      # the unit tests
python -m eval.run_eval        # the acceptance cases, including the real-game comparisons
python -m zbuilder golden --check   # earlier builds still come out byte for byte the same
python -m zbuilder compare HEAD     # the Inform 7 examples, built and played with the last commit and now
```

The real-game comparisons are skipped if you haven't downloaded the games.

## How it was built

**With the help of an AI.** Most of the code in this project, and most of
its documentation, was written by an AI coding assistant built on a large
language model (LLM). A person directed the work throughout. They wrote
the brief (what to build, and the order to build it in), chose between the
options the assistant laid out, decided what to leave out, and approved
each step before it was committed. The assistant read the Z-Machine
Standard, designed and wrote the code, the tests and the documents, ran the
checks, and fixed what they found.

**Why that matters to you.** An LLM writes fluent, confident text whether
or not it is right. During this project it misquoted section numbers of
the Standard, misremembered how Inform 7 behaves, and once wrote a guide
whose example could never work. So nothing here is taken on trust. Every
feature has to pass the checks in [How we know it works](#how-we-know-it-works):
tests written from the Standard, comparisons with real games and with the
official Inform 7's own output, and builds that must come out byte for
byte the same. Mistakes may still remain, so if something here disagrees
with the Standard, the Standard is right.

**zbuilder** is the workflow built for the job. It splits the work into
tiers, each with its own acceptance tests, and has roles for AI agents: a
spec analyst, an architect, an implementer, a verifier and a reviewer.
`python -m zbuilder status` shows the plan and where each task stands, and
`python -m zbuilder review` checks the code for readability. It works
offline too: without an AI provider set up, it checks each task with real
tools and writes a brief for anything that still fails (see `.env.example`
to connect a provider). Much of this project was built that way, with the
assistant doing the work and zbuilder's checks deciding when each tier was
done.

## Further reading

- [docs/HOW_THE_COMPILER_WORKS.md](docs/HOW_THE_COMPILER_WORKS.md): the
  compiler, stage by stage, for beginners.
- [docs/HOW_THE_INTERPRETER_WORKS.md](docs/HOW_THE_INTERPRETER_WORKS.md):
  the interpreter, part by part, for beginners.
- [docs/TOUR.md](docs/TOUR.md): one command, all the way through.
- [docs/DESIGN.md](docs/DESIGN.md): how the pieces fit, and a reading order.
- [docs/I7_LITE.md](docs/I7_LITE.md): the Inform 7 you can write.
- [docs/I7_TO_ZIL.md](docs/I7_TO_ZIL.md): how Inform 7 is turned into ZIL.
- [docs/ZIL_SUBSET.md](docs/ZIL_SUBSET.md): the ZIL you can write.
- [docs/DECISIONS.md](docs/DECISIONS.md): every choice we made where the
  standard, or Inform, left room for more than one answer.
- [docs/KNOWN_GAPS.md](docs/KNOWN_GAPS.md): what's missing.

The games in `stories/` are downloaded rather than included here, so check
each one's licence before passing it on. The standard's text belongs to
its authors; zforge only keeps a local copy for looking things up.
