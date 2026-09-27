# How the compiler works

A compiler is a translator. You write something a person can read, and it
produces something a machine can run. zforge's compiler reads a game
written in ZIL or Inform 7 and writes a **story file**: the bytes that a
Z-machine interpreter runs.

It does that in stages, each small enough to understand on its own. Every
stage hands a slightly different picture of the program to the next one,
and you can ask zforge to show you each picture. That's the best way to
learn how it works: build a tiny program, then look at what each stage
made of it.

This guide follows one small ZIL program through every stage, then shows
how Inform 7 is added in front. Every excerpt below was copied from a
real run, so you can make the same files and read along.

```
 Inform 7 (.ni) ─► English into ZIL ─┐
                                     ▼
          ZIL (.zil) ─► lexer ─► reader ─► form parser ─► checks ─► code generator
                                                                         │
                                                             assembly (.zas)
                                                                         ▼
                                                  assembler + linker ─► story file (.z5-.z8)
```

## The example

Work in the `zmachine_forge` folder, as in the README's "Getting set
up": `python -m zforge` only works from there. Keep your example files
there too, or give the path to them.

Put this in a file called `count.zil`:

```
<VERSION 5>

<ROUTINE GO ("AUX" N)
    <SET N 1>
    <REPEAT ()
        <TELL "Counting: " N .N CR>
        <SET N <+ .N 1>>
        <COND (<G? .N 3> <RETURN>)>>
    <QUIT>>
```

It counts to three. `GO` is where every ZIL game starts; `N` is a local
variable ("AUX" means "a variable of my own, not an argument"); `.N` means
"the value of N"; `REPEAT` loops until something `RETURN`s out of it; and
`COND` is ZIL's *if*.

Build it, asking for the in-between files, and run it:

```bash
python -m zforge compile count.zil --emit-tokens --emit-ast --emit-asm
python -m zforge run count.z5 --ui plain
```

```
Counting: 1
Counting: 2
Counting: 3
```

You now have `count.tokens`, `count.ast` and `count.zas` beside the story
file. We'll look at each in turn.

## Stage 1: the lexer cuts the text into tokens

*File: `zforge/compiler/lexer.py`*

The first job is to stop thinking about single characters. The lexer
reads the text from left to right and cuts it into **tokens**: the
smallest pieces that mean something, such as a bracket, a name or a
number. Here is the start of `count.tokens`:

```
1:1     LANGLE  '<'
1:2     ATOM    'VERSION'
1:10    NUMBER  '5'
1:11    RANGLE  '>'
3:1     LANGLE  '<'
3:2     ATOM    'ROUTINE'
3:10    ATOM    'GO'
3:13    LPAREN  '('
3:14    STRING  'AUX'
3:20    ATOM    'N'
3:21    RPAREN  ')'
```

Each token remembers its line and column (`3:10` is line 3, column 10).
Nothing later needs to look at the raw text again, but every error
message can still point at the exact spot. Spaces, line breaks and
comments are gone at this point: they only separated the tokens.

## Stage 2: the reader matches the brackets

*File: `zforge/compiler/reader.py`*

ZIL, like Lisp, is built out of brackets. `<...>` is a **form** (roughly,
"do this") and `(...)` is a list. The reader's only job is to match every
opening bracket with its closing one, turning the flat row of tokens into
nested groups. `<SET N 1>` becomes one form holding three things:

```
Form(items=[Atom(name='SET'), Atom(name='N'), Number(value=1)])
```

(There's no `--emit` option for this stage; the line above was printed
with `zforge.compiler.driver.read_source`, with the locations left out.)

The reader knows nothing about what `SET` means. That's deliberate: it
can check brackets for any ZIL program, including ones the rest of the
compiler has never heard of. Take away the `>` after `<SET N 1` and this
is the stage that notices:

```
zforge: bracket.zil:3:1: error: '<' is never closed
    <ROUTINE GO ("AUX" N)
    ^
bracket.zil:4:5: error: <SET> takes 2 argument(s), got 4
    <SET N 1
    ^
```

The second message comes from a later stage. With the `>` missing, the
next two forms ended up inside the `SET`. The compiler carries on after
the first error so that one run reports as much as it can, but it's
usually the first message that tells you what's really wrong.

## Stage 3: the form parser works out what each form means

*Files: `zforge/compiler/forms.py`, `ast.py`, `grammar.py`*

Now the compiler asks what each form *means*. `<SET N 1>` is an
assignment; `<REPEAT ...>` is a loop; `<TELL ...>` prints. The answer is
a **syntax tree** (often called an AST, for "abstract syntax tree"): a
tree of Python objects, one kind for each thing the language can say.
`ast.py` defines the kinds. This is the start of `count.ast`, shortened:

```
RoutineDecl(name='GO',
            auxes=[('N', None)],
            body=[Call(name='SET', args=[Atom(name='N'), Num(value=1)]),
                  Repeat(body=[Tell(items=[('str', 'Counting: '),
                                           ('num', Local(name='N')),
                                           ('cr',)]),
                               Call(name='SET',
                                    args=[Atom(name='N'),
                                          Call(name='+', args=[Local(name='N'),
                                                               Num(value=1)])]),
                               Cond(...)])])
```

Compare it with the source. The tree has the same shape, but everything
has a job now: `.N` has become `Local(name='N')`, and the `TELL` has been
split into what it prints, in order. `grammar.py` does one extra step,
which it calls desugaring: it turns a game's `SYNTAX` lines (how the
player may type each command) into the tables the parser uses.

## Stage 4: the checks ask whether it makes sense

*File: `zforge/compiler/semantic.py`*

A program can have perfect brackets and still be nonsense. This stage
builds a **symbol table** (every routine, global, object and local
variable, and where each was defined) and checks every use against it.
Change `<G? .N 3>` to `<G? .M 3>` and you get:

```
zforge: typo.zil:8:20: error: unknown local variable .M
        <COND (<G? .M 3> <RETURN>)>>
                   ^
```

These checks run even after earlier errors, so a single compile tells you
about as many problems as possible. If there are any errors at all, the
compiler stops here: generating code from a broken program would only
produce more confusing messages.

## Stage 5: the code generator writes assembly

*File: `zforge/compiler/codegen.py`*

Now the tree is turned into **assembly language**: the Z-machine's own
instructions, one per line, still as text. This is `count.zas`, the
whole of it:

```
.routine GO .N
    store .N 1
_1:
    print "Counting: "
    print_num .N
    print "^"
    add .N 1 -> .N
    jg .N 3 ?~_4
    jump _2
    jump _3
_4:
_3:
    jump _1
_2:
    quit
.end
```

Read it next to the source and most lines explain themselves. `SET N 1`
became `store`, and `TELL` became three print instructions (`^` is a line
break). `<SET N <+ .N 1>>` became a single `add` whose result goes
straight back into `.N` (`-> .N`).

The loop and the `COND` are the interesting part, because the Z-machine
has no loops or ifs. It only has **jumps**. So the code generator invents
**labels** (`_1`, `_2`, ...) and jumps between them:

- `_1` is the top of the loop; `jump _1` at the bottom goes round again.
- `_2` is just after the loop, so `RETURN` becomes `jump _2`.
- `jg .N 3 ?~_4` means "is N greater than 3? If *not* (`~`), jump to
  `_4`", skipping the clause. That is how an *if* is built from a jump.

`jump _3` straight after `jump _2` can never run. A simple code generator
writes the same pattern for every clause and doesn't tidy up afterwards;
a real optimising compiler would remove it. zforge values code you can
follow over code that is as small as possible.

## Stage 6: the assembler and linker make the bytes

*Files: `zforge/asm/assembler.py`, `zforge/asm/linker.py`*

The assembler turns each line of assembly into bytes. The linker builds
everything else a story file needs: the header, the object table, the
dictionary, the global variables. It then puts them all at their
addresses. The assembler works in four passes:

1. **collect** every routine, global, string and table;
2. **size** each instruction. A jump is first assumed to be short, and
   made longer only if its target turns out to be too far away (this is
   called "relaxation");
3. **lay out** memory, giving everything an address;
4. **emit** the bytes, now that every label has an address.

The disassembler turns the bytes back into text, so you can see the
result: `python -m zforge disasm count.z5`:

```
00368: f9 3f 00 dc              call_vn        routine@0x00370
0036c: ba                       quit

00370: routine  locals=1
00371: 0d 01 01                 store          L00 1
00374: b2 11 14 6a 79 3a 6c 97  print          'Counting: '
0037d: e6 bf 01                 print_num      L00
00380: b2 94 e5                 print          '\n'
00383: 54 01 01 01              add            L00 1 -> L00
00387: 43 01 03 48              jg             L00 3 ?~0x00391
0038b: 8c 00 08                 jump           0x00394
0038e: 8c 00 02                 jump           0x00391
00391: 8c ff e2                 jump           0x00374
00394: ba                       quit
```

On the left is each instruction's address, then its bytes. (The
disassembler numbers local variables from 0, so `L00` is our `N`.) It's
worth decoding a couple by hand, with section 4 of the Z-Machine Standard
open beside you:

- **`54 01 01 01` is `add`.** The first byte says a lot. Its top bit is
  0, so this is the "long" form. The next two bits say the first operand
  is a variable and the second a small number. The low five bits, `10100`,
  are 20: the opcode for `add`. Then come the operands, variable 1 (our
  `N`) and the number 1, and the variable to store the answer in (1
  again).
- **`43 01 03 48` is `jg`**, "jump if greater". The last byte, `48`, is
  the branch. Its top bit is 0, meaning "branch when the test is
  *false*": that's the `~`. The next bit is 1, meaning the offset fits in
  this one byte: 8. The target is the address after the instruction, plus
  the offset, minus 2: 0x38b + 8 − 2 = 0x391, as shown.
- **`f9 3f 00 dc` calls our routine.** This is the tiny start-up stub the
  linker adds: call `GO`, then `quit`. But `GO` lives at 0x370, and the
  instruction says 0xdc. That's because routine addresses are stored
  **packed**: in version 5 the real address is the packed one times 4,
  and 0xdc × 4 = 0x370. Packing lets a 2-byte number reach further into
  a large story file.

## Choosing the version

A story file can be built for version 5, 6, 7 or 8 of the Z-machine.
Choose with `--target` (or a `zforge.toml` file, or the `ZFORGE_TARGET`
setting):

```bash
python -m zforge compile count.zil --target z8
```

The earlier stages don't care: the tokens, the tree and the assembly are
the same for every version. Only this last stage changes. Build
`count.zil` both ways and just **5 bytes** differ: the version number in
the header, the file length and checksum, and the packed address. In
version 8 the start-up stub says `00 6e`, because a version-8 address is
the packed one times 8, and 0x6e × 8 is 0x370 again. Everything that
differs between versions lives in one file, `zforge/common/versions.py`.
`python -m zforge info --versions` prints it as a table.

## The other half: English into ZIL

*Files: `zforge/compiler/i7/`*

An Inform 7 game goes through one more translation first: zforge turns
the English into ZIL, then compiles that ZIL exactly as above. Take this
story, `glued.ni`:

```
"Glued" by You

The Hall is a room. "A bare hall."
The brass lamp is in the Hall.
Instead of taking the lamp: say "It's glued down."
```

```bash
python -m zforge compile glued.ni --emit-zil
```

The English goes through four steps of its own:

1. **`source.py`** cuts the text into sentences and rules. This is
   harder than it sounds: a full stop inside a quotation doesn't always
   end the sentence.
2. **`model.py`** builds a model of the world from the sentences: there
   is a room called the Hall, and a thing called the brass lamp inside
   it. It reads everything twice, so a sentence may mention something
   that is only described later.
3. **`phrases.py`** reads the rules: which action each one is about, when
   it applies, and what it does.
4. **`lower.py`** writes the model and the rules out as ZIL.

In `glued.zil` the lamp has become an ordinary ZIL object. The words the
player may use for it come from its name:

```
<OBJECT BRASS-LAMP   ;"thing (line 4)"
    (IN HALL)
    (DESC "brass lamp")
    (SYNONYM BRASS LAMP)
    (ARTICLE 1)>
```

The rule has become a routine. Its first line checks that the rule
applies (that the thing being taken, `PRSO`, is the lamp). Returning
false means "this rule doesn't apply":

```
<ROUTINE RULE-1 ()   ;"instead taking the lamp (line 5)"
    <COND (<NOT <EQUAL? ,PRSO ,BRASS-LAMP>> <RFALSE>)>
    <PARA-FLUSH> <TELL "It's glued down."> <SENTENCE-BREAK>
    <RTRUE>>
```

And the routine is filed in the taking action's **rulebook**: a table of
six lists, one for each stage an action goes through (before, instead,
check, carry out, after, report). `RULE-1` sits in the second, the
Instead rules, ahead of Inform 7's own check rules:

```
<GLOBAL TAKING-RULES <TABLE <LTABLE > <LTABLE ,RULE-1>
    <LTABLE ,TAKE-YOURSELF ,TAKE-PEOPLE ,TAKE-ALREADY-TAKEN ,TAKE-SCENERY ,TAKE-FIXED>
    <LTABLE ,TAKE-STANDARD> <LTABLE > <LTABLE ,TAKE-REPORT>>>
```

The routines named there, `TAKE-PEOPLE` and the rest, are Inform 7's
standard rules. They are written in ZIL too, in `zforge/lib/i7/`, and
they're compiled into every Inform 7 game. So the compiler doesn't need
to know how taking works: it only has to file each rule in the right
place. [TOUR.md](TOUR.md) follows a command through all of this while
the game runs, and [I7_TO_ZIL.md](I7_TO_ZIL.md) lists how each kind of
sentence is translated.

## When something goes wrong

There are two kinds of error, and zforge tries hard to tell you which
one you've hit:

- **A mistake in your game.** You get a message with the file, line and
  column, and the line itself with a `^` under the problem, as in the
  examples above. Inform 7 sources get Inform-style messages that quote
  your sentence:

  ```
  bad.ni:4: Problem. You wrote 'The lamp is on the Hall.', but 'Hall' is
  not a supporter, so nothing can be put on it.
  ```
- **A mistake in zforge.** If the ZIL generated from an Inform 7 game
  doesn't compile, that's zforge's bug, not yours, and the message says
  so ("internal error: I7-lite generated ZIL that does not compile"). Use
  `--emit-zil` to see the code it generated.

To see the full Python error behind a message, put `--debug` straight
after `zforge`, before the command: `python -m zforge --debug compile
count.zil`.

## Try it yourself

1. Change the `3` in `count.zil` to `10`, rebuild, and look at
   `count.zas` again. Only one number changes. Why is that all?
2. Make the mistakes shown above on purpose, and a few of your own. Which
   stage reports each one?
3. Build `count.zil` with `--target z8` and run `disasm` on both files.
   Find the start-up stub in each and check the packed address by hand.
4. Read the `repeat` and `cond` methods in `zforge/compiler/codegen.py`,
   and match the labels they create to the ones in `count.zas`.
5. Add a second rule to `glued.ni`, such as
   `Instead of examining the lamp: say "It gleams."`, and find where it's
   filed in `glued.zil`.

## Which file does what

| Stage | File | Makes |
|---|---|---|
| Inform 7: sentences | `compiler/i7/source.py` | sentences and rule bodies |
| Inform 7: the world | `compiler/i7/model.py`, `phrases.py` | a model of rooms, things and rules |
| Inform 7: into ZIL | `compiler/i7/lower.py`, `standard.py` | ZIL source (`--emit-zil`) |
| Lexer | `compiler/lexer.py` | tokens (`--emit-tokens`) |
| Reader | `compiler/reader.py` | nested forms |
| Form parser | `compiler/forms.py`, `ast.py`, `grammar.py` | the syntax tree (`--emit-ast`) |
| Checks | `compiler/semantic.py` | the symbol table, or error messages |
| Code generator | `compiler/codegen.py` | assembly (`--emit-asm`) |
| Assembler and linker | `asm/assembler.py`, `asm/linker.py` | the story file |
| The whole chain | `compiler/driver.py`, `compiler/i7/driver.py` | runs the stages in order |

[DESIGN.md](DESIGN.md) suggests an order for reading the code, and
[HOW_THE_INTERPRETER_WORKS.md](HOW_THE_INTERPRETER_WORKS.md) picks up
where this guide stops: what happens when the story file runs.
