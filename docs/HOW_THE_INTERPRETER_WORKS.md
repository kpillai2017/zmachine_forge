# How the interpreter works

In 1979 the people who went on to found Infocom had a problem. There were
dozens of kinds of home computer, all different, and they wanted to sell
their games on every one of them. Rather than rewrite each game for each
machine, they invented an imaginary computer, the **Z-machine**. They
wrote their games for that, and then wrote one small program for each real
computer that pretended to be a Z-machine. That program is an
**interpreter**, and it's the reason a game from 1980 still runs today.

zforge's interpreter is one of those programs, written in Python so that
you can read it. Its most surprising feature is how little it knows. It
knows nothing about rooms, lamps or understanding English: all of that is
in the game. The interpreter just runs instructions, one after another,
as fast as it can. This guide shows how.

It uses two story files from
[HOW_THE_COMPILER_WORKS.md](HOW_THE_COMPILER_WORKS.md): `count.z5`, a
tiny program that counts to three, and `glued.z8`, a one-room Inform 7
game. Every excerpt was copied from a real run.

Work in the `zmachine_forge` folder, as in the README's "Getting set
up": `python -m zforge` only works from there. Keep your example files
there too, or give the path to them. If you haven't made those two files yet,
the compiler guide shows how.

## 1. The story file is the machine's memory

*Files: `zforge/common/memory.py`, `zforge/common/header.py`*

A Z-machine has no disk and no files. It has one block of memory, and the
story file *is* that memory: to start a game, the interpreter reads the
whole file into memory, byte for byte. Everything the game needs is in
there, including its code, its text, its objects and its dictionary.

The memory has three parts:

- **Dynamic memory**, at the start, is the only part the game may change.
  It holds the game's variables and objects, so it *is* the state of the
  game. That's why saving a game only needs to save this part.
- **Static memory** can be read but not changed, such as the dictionary.
- **High memory** holds the code and most of the text.

The first 64 bytes are the **header**, which tells the interpreter where
everything else is. `python -m zforge info count.z5 --header` shows it:

```
Header (§11):
  Version         5
  Release         1
  Serial          000000
  High memory     0x0368
  Initial PC      0x0368
  Dictionary      0x0360
  Object table    0x0102
  Globals         0x0180
  Static memory   0x0360
  Abbreviations   0x0040
  File length     920 bytes
  Checksum        0x4133 (ok)
```

The most important line is **Initial PC**: the address of the first
instruction to run. (The § numbers are sections of the Z-Machine
Standard, the document that defines the machine. The interpreter's
comments cite it throughout.)

## 2. The heart of it: fetch, decode, execute

*File: `zforge/vm/machine.py`*

Every processor, real or imaginary, works the same way. It keeps a
**program counter** (the PC): the address of the next instruction. Then,
over and over, it:

1. **fetches** the bytes at the PC,
2. **decodes** them, working out which instruction they are and what it
   applies to,
3. moves the PC past them, and
4. **executes** the instruction.

In zforge that's the `step` method, and this is the heart of it, only
slightly shortened:

```python
def step(self) -> None:
    ins = decode(self.mem.read_byte, self.pc, ...)     # fetch and decode
    self.current = ins
    self.pc = ins.next_address                         # move past it
    handler = self.handlers.get(ins.op.name)           # which instruction?
    handler(self, *self.operand_values(ins))           # execute it
```

The `run` method just calls `step` until the game quits. Moving the PC
*before* executing matters: an instruction that jumps simply sets the PC
to somewhere else, and the next step carries on from there.

You can watch the loop. `--trace` writes one line per instruction:

```bash
python -m zforge run count.z5 --ui plain --trace count.trace
```

```
PC=0x00368 depth=0  VAR:25  call_vn        #00dc
PC=0x00371 depth=1  2OP:13  store          #01 #01
PC=0x00374 depth=1  0OP:2   print
PC=0x0037d depth=1  VAR:6   print_num      L00
PC=0x00380 depth=1  0OP:2   print
PC=0x00383 depth=1  2OP:20  add            L00 #01 -> L00
PC=0x00387 depth=1  2OP:3   jg             L00 #03 ?~0x00391
PC=0x00391 depth=1  1OP:12  jump           #ffe2
PC=0x00374 depth=1  0OP:2   print
...
PC=0x00387 depth=1  2OP:3   jg             L00 #03 ?~0x00391
PC=0x0038b depth=1  1OP:12  jump           #0008
PC=0x00394 depth=1  0OP:10  quit
```

Follow the PC down the left. The game calls its main routine
(`call_vn`), which prints a line, adds 1, and tests. Then `jump` sends
the PC back to 0x374, and round it goes. On the third time round the
test comes out the other way, so the PC reaches the `jump` at 0x38b
instead, which leads to `quit`. The whole program is 21 instructions.

## 3. Decoding: what the bytes mean

*Files: `zforge/vm/decoder.py`, `zforge/common/opcodes.py`*

An instruction is at least one byte long, and the first byte says how to
read the rest. It tells the decoder three things:

- the instruction's **form**, which is its overall shape. There are four:
  long, short, variable and extended.
- how many **operands** (inputs) it has, and whether each is a small
  number, a large number or a variable.
- the **opcode**: which instruction it is.

Some instructions then have a **store byte**, naming the variable to put
their answer in (`-> L00` above). Others have **branch bytes**, saying
where to jump if a test comes out a certain way (`?~0x00391`). The trace
names each instruction by its family and number, the way the Standard
does. `2OP:20` means "instruction number 20 of the ones with two
operands": `add`. The compiler guide decodes a few of these by hand, byte
by byte.

What each number means comes from **one opcode table**,
`zforge/common/opcodes.py`. The compiler, the assembler, the disassembler
and the interpreter all share it, so they can never disagree. A test
checks the table against section 14 of the Standard.

## 4. Executing: one small function per instruction

*Files: `zforge/vm/ops/*.py`*

Each instruction is a small Python function. The files group them by
family: arithmetic, calls and returns, objects, printing, input, and so
on. This is `add`, in full:

```python
def op_add(vm, a, b):
    """§15 add (2OP:20): a + b, signed 16-bit, wrapping."""
    vm.store_result(from_signed(to_signed(a) + to_signed(b)))
```

"Signed 16-bit, wrapping" is the one thing to know about Z-machine
numbers. Every number is 16 bits, so it runs from −32768 to 32767, and
going past the end wraps round: 32767 + 1 is −32768. The interpreter
keeps numbers as 0 to 65535 in memory (−1 is stored as 0xffff), and
`to_signed` and `from_signed` convert between the two.

Some instructions can't be carried out, and then the game stops with an
error rather than guessing: dividing by zero is one example. You get a
message, plus the last few instructions that ran, to help find where it
went wrong.

## 5. Variables, the stack and calling routines

*File: `zforge/vm/frames.py`*

An instruction can read or write three kinds of variable, told apart by
number:

| Number | Variable |
|---|---|
| 0 | the top of the **stack** (a pile of numbers: the last one pushed is the first one taken) |
| 1 to 15 | the current routine's **local** variables |
| 16 to 255 | the game's **global** variables, kept in dynamic memory |

A **routine** is the Z-machine's version of a function. Calling one
creates a new **frame**: a small record holding the routine's local
variables (up to 15), its own part of the stack, where to go back to
afterwards, and where to put its answer. Returning throws the frame away
and carries on after the call. The `depth` in the trace is the number of
frames: 0 while the start-up code runs, 1 inside the main routine.

A routine is called by its **packed address**, the real address divided
by 4 (in version 5) or 8 (version 8). That's why the trace says
`call_vn #00dc` when the routine is at 0x370: 0xdc × 4 = 0x370.

## 6. Text: five bits to a letter

*File: `zforge/common/text.py`*

Memory was precious in 1979, so the Z-machine packs text tightly. Each
character is a 5-bit code, and three of them fit in each 2-byte word,
with the word's top bit marking the end of the text. The 26 lower-case
letters have codes 6 to 31, in order. So "cat" fits in just two bytes,
`a0 d9`:

```
a0 d9  =  1 01000 00110 11001
          │   8     6    25
          │   c     a    t
          └── the end of the text
```

For anything else a code *shifts* to another alphabet for one character:
code 4 means "the next letter is upper case", and code 5 leads to digits
and punctuation. "Cat" therefore needs a 4 before the 8, and becomes
four bytes, `11 06 e4 a5`. The last word is padded with 5s, since three
codes must fill it. Common words can be stored once and reused, as
**abbreviations**, and characters outside the alphabets are spelled out
as ZSCII, the Z-machine's own version of ASCII.

The same file packs text when compiling and unpacks it when playing, so
the two always agree. A `print` instruction simply carries its text with
it, which is why `print 'Counting: '` above is 9 bytes long.

## 7. Objects: the world as a tree

*File: `zforge/vm/objects.py`*

Everything in a game's world (rooms, things, even the player) is an
**object** in a table in dynamic memory. Each object has:

- 48 **attributes**: on/off flags such as "this is lit" or "this is
  worn";
- three links, to its **parent**, its next **sibling** and its first
  **child**. They make every object part of one tree: the lamp's parent
  is the Hall, and taking the lamp makes the player its parent instead;
- a list of **properties**: numbered values such as its description or
  where each exit leads.

`python -m zforge info glued.z8 --objects` shows the table. Look for the
end of the list:

```
  [16] "Hall"  attrs=[1, 20]  props=[18, 16, 14]
    [17] "brass lamp"  attrs=[]  props=[16, 14]
```

The indentation is the tree: the lamp is inside the Hall. The Hall's
attributes 1 and 20 are the compiler's numbers for LITBIT and ROOMBIT:
"lit" and "is a room". Instructions such as `insert_obj` (move an object
into another), `test_attr` and `get_prop` are all a game needs to build a
whole world from this.

## 8. Reading what the player types

*File: `zforge/vm/lexer.py`*

Here the interpreter does a little more than run instructions, but only
a little. When the game wants a command it runs the `aread` instruction,
which:

1. reads a line from the keyboard into a buffer in memory;
2. splits it into words, at spaces and at the game's **separators**
   (here `.` `,` and `"`);
3. looks each word up in the game's **dictionary**, and writes the
   results into a second buffer: for each word, where it was typed and
   where it is in the dictionary.

That's all. *Understanding* "take lamp" is the game's job: the parser
(`zforge/lib/parser.zil`) is ordinary Z-machine code in the story file.
Try `--trace` on `glued.z8` with a one-line script that says `take lamp`.
It takes **1,089 instructions** just to print the banner, describe the
Hall and reach the first prompt, and **841 more** to deal with "take
lamp", nearly all of them the game's own parser and rules.

The dictionary is in the header's list. In version 5 and later a
dictionary word keeps only its first 9 letters, which is why
`info glued.z8 --dictionary` includes the word `everythin`: typing
"everything" still matches it.

## 9. The screen

*Files: `zforge/vm/streams.py`, `zforge/vm/screen/`*

Text goes out through **output streams**: stream 1 is the screen, 2 a
transcript file, 3 a table in memory, and 4 a record of the commands
typed. (zforge accepts stream 4 but doesn't use it; `--transcript FILE`
records a game instead.) Most of the time only the screen is on.

What the screen looks like depends on the version:

- **Versions 5, 7 and 8** have two **windows**: a small upper one, used
  for the status line, and the main lower one, where text scrolls. When a
  screenful has gone by without the player pressing a key, the
  interpreter shows `[MORE]` and waits (`screen/base.py`).
- **Version 6** has eight windows, which the game can move, resize and
  scroll however it likes. It was designed for graphics. zforge draws it
  in characters (`screen/v6.py`).

Either can be drawn in two ways. `--ui curses` uses the whole terminal
window (`screen/curses_screen.py`); `--ui plain` just prints, which suits
scripts and tests (`screen/plain.py`). The game can't tell which is in
use.

## 10. Saving, restoring and undo

*File: `zforge/vm/quetzal.py`*

A game's state is its dynamic memory, its stack of frames and its PC, so
that is what a saved game holds. zforge writes saves in **Quetzal**, the
standard format that other interpreters read too. To keep the file
small, the memory is stored as the *difference* from the original story
file, and runs of unchanged bytes are squeezed down to a count. **Undo**
is the same thing kept in memory instead of in a file: the game asks for
a snapshot at the start of each turn, and zforge keeps the last 10.

## Versions

Versions 5, 6, 7 and 8 are more alike than different. What changes is
mostly in the sums: how packed addresses are unpacked, how big a story
may be, and how the file length is stored. Version 6 also starts
differently, by calling a routine rather than jumping to an address, and
has the eight-window screen. Every such rule is in one file,
`zforge/common/versions.py`, and `python -m zforge info --versions`
prints them as a table. Everywhere else, the code asks the version's
profile rather than testing the version number itself.

## When something goes wrong

If a game does something the Z-machine forbids, such as dividing by zero
or running an instruction that doesn't exist, zforge stops and says what
went wrong, and at which address. It also lists the last instructions that
ran. For a closer look, run the game again with `--trace FILE` and read
the lines just before the end. `--verbose` also shows warnings: things a
game did that were odd but harmless.

## Try it yourself

1. Trace `count.z5` and match every line to the disassembly in
   [HOW_THE_COMPILER_WORKS.md](HOW_THE_COMPILER_WORKS.md). Which
   instruction runs most often?
2. Encode your own name by hand, five bits at a time, then check your
   answer with `print` in a small ZIL program and `disasm`.
3. Take the Instead rule out of `glued.ni`, rebuild it, then play it
   with `--trace` and type `take lamp`. Find the `insert_obj` that moves
   the lamp into object 1, the player. (With the rule left in, there
   isn't one: the lamp stays glued down.)
4. Build an Inform 7 game with `--testing` and type `tree` before and
   after taking something. It shows the object tree from section 7.
5. Read `op_add` and its neighbours in `zforge/vm/ops/arith.py`, then
   work out what `-32768 - 1` gives, and check it in a small program.

## Which file does what

| Part | File |
|---|---|
| Memory and the header | `common/memory.py`, `common/header.py` |
| What differs between versions | `common/versions.py` |
| The main loop | `vm/machine.py` |
| Decoding instructions | `vm/decoder.py`, `common/opcodes.py` |
| The instructions themselves | `vm/ops/*.py` (listed in `vm/ops/__init__.py`) |
| Routines and the stack | `vm/frames.py` |
| Text | `common/text.py` |
| Objects | `vm/objects.py` |
| Reading input | `vm/lexer.py` |
| Output and the screen | `vm/streams.py`, `vm/screen/` |
| Saving, restoring, undo | `vm/quetzal.py` |

[DESIGN.md](DESIGN.md) suggests an order for reading these files, and
[TOUR.md](TOUR.md) follows one command, "take lamp", through the
compiler, the interpreter and the game's own rules.
