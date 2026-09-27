# A guided tour: what happens when you type "take lamp"

This is the quickest way into the code. We follow one command, from the
line of English that creates a lamp to the moment the Z-machine moves it
into your hands, and at each step you'll see the real text zforge
produces and the file where it happens. Nothing below is made up for the
tour. Every excerpt was copied from a real run, so you can make the same
files yourself and read along.

## The story

Put these four lines in a file called `lamp.ni`:

```
"The Lamp" by You

The Hall is a room. "A bare hall."
The brass lamp is in the Hall.
```

Then build it twice. The first build is an ordinary one, and we ask for
the in-between files as well. The second adds Inform's testing commands,
which we'll use at the end.

```bash
python -m zforge compile lamp.ni --emit-zil --emit-asm -o plain.z8
python -m zforge compile lamp.ni --testing -o lamp.z8
```

You now have `plain.zil` (the translation into ZIL), `plain.zas` (the
assembly) and `plain.z8` (the story file itself).

## 1. English becomes a world

The compiler first cuts the source into sentences and works out which
are statements about the world ("The brass lamp is in the Hall.") and
which are rules. That happens in `zforge/compiler/i7/source.py`.

`model.py` then builds a picture of the world from those statements.
There's a room called the Hall, and a thing called the brass lamp inside
it. Nobody said what kind of thing the lamp is, so it gets Inform's
defaults. It's an ordinary *thing*, portable, not scenery, and its name
gives the words a player can call it by: "brass" and "lamp".

## 2. The world becomes ZIL

`lower.py` writes the model out in ZIL, the language Infocom wrote its
games in (see `docs/I7_TO_ZIL.md`). The lamp becomes this, in
`plain.zil`:

```
<OBJECT BRASS-LAMP   ;"thing (line 4)"
    (IN HALL)
    (DESC "brass lamp")
    (SYNONYM BRASS LAMP)
    (ARTICLE 1)>
```

The comment says which line of your source it came from. Every
generated routine says the same, so you can always get back to the
sentence behind it.

Three other pieces of `plain.zil` matter for our command. The first is a
grammar line saying that "take" followed by one or more things means the
taking action:

```
<SYNTAX TAKE OBJECT (MANY) = V-TAKING>
```

The second is the taking action itself, which just runs its rulebook:

```
<ROUTINE V-TAKING ()   ;"the taking action"
    <RUN-ACTION ,TAKING-RULES>>
```

The third is the rulebook: six lists of rules, one for each of Inform's
stages (before, instead, check, carry out, after, report). It's one long
line in the file; here it's split up to make it easier to read:

```
<GLOBAL TAKING-RULES <TABLE <LTABLE > <LTABLE >
    <LTABLE ,TAKE-YOURSELF ,TAKE-PEOPLE ,TAKE-ALREADY-TAKEN ,TAKE-SCENERY ,TAKE-FIXED>
    <LTABLE ,TAKE-STANDARD> <LTABLE > <LTABLE ,TAKE-REPORT>>>
```

The before and instead lists are empty because our story has no rules
of its own. If you wrote "Instead of taking the lamp: ...", your rule
would appear in the second list.

The rules named here aren't generated; they're part of the library, in
`zforge/lib/i7/standard.zil`. The one that actually does the taking is a
single line:

```
<ROUTINE TAKE-STANDARD () <MOVE ,PRSO ,PLAYER> <FSET ,PRSO ,HANDLEDBIT> <RFALSE>>
```

It moves the noun (`PRSO`, "the direct object") to the player, and
notes that it has been handled. Returning false means "I haven't made
a decision; carry on with the next rule".

## 3. ZIL becomes assembly

The ZIL compiler (`zforge/compiler/`) turns each routine into Z-machine
instructions. Here's the same rule in `plain.zas`:

```
.routine TAKE-STANDARD
    insert_obj PRSO PLAYER
    set_attr PRSO HANDLEDBIT
    rfalse
.end
```

`MOVE` became `insert_obj` and `FSET` became `set_attr`. These are real
Z-machine opcodes, and each one is described in section 15 of the
standard. You can look any of them up offline with
`python -m zforge spec insert_obj`.

The assembler (`zforge/asm/`) then turns this text into bytes, works out
every address and writes the story file.

## 4. The interpreter reads your command

Now play the game and type `take lamp`. The parser is written in ZIL
too (`zforge/lib/parser.zil`), so it runs inside the Z-machine like the
rest of the game. It starts in `READ-COMMAND`:

```
<ROUTINE READ-COMMAND ()
    ;"read a line into READBUF and tokenise it into PARSEBUF; false if empty"
    <PUTB ,READBUF 0 78>          ;"§15 read: byte 0 = room for 78 characters"
    <PUTB ,READBUF 1 0>           ;"          byte 1 = none typed yet (v5)"
    <PUTB ,PARSEBUF 0 12>         ;"§13.6.3: room for 12 words"
    <READ ,READBUF ,PARSEBUF>
    ...
```

`READ` becomes the Z-machine's `aread` instruction. That is where
Python takes over. `op_aread` in `zforge/vm/ops/input.py` waits for your
line, and `zforge/vm/lexer.py` splits it into words and looks each one
up in the story's dictionary. After it, the game has a short list: word
one is the dictionary entry for "take", word two is the entry for
"lamp".

You can watch this happen. Run the story with `--trace trace.txt` and
the interpreter writes down every instruction it carries out. The
`aread` looks like this (your addresses may differ):

```
PC=0x01383 depth=4  VAR:2   storeb         G14 #00 #0c
PC=0x01388 depth=4  VAR:4   aread          G13 G14 -> G00
```

The `storeb` is the `<PUTB ,PARSEBUF 0 12>` line above: room for twelve
words.

## 5. The parser works out what you meant

`PARSE-COMMAND` looks for a grammar line whose first word is "take" and
tries each one in turn (`MATCH-SYNTAX`). For `take OBJECT` it needs a
thing, so it looks at the words that are left and asks, for every thing
you can see, whether they describe it. The test is `MATCHES?`: the last
word must be one of the thing's nouns (its `SYNONYM` list), and every
earlier word must be a noun, an adjective or "the".

```
<ROUTINE MATCHES? (O FIRST LAST)
    ;"the last word is a noun of O; every earlier word describes O"
    <COND (<NOT <IN-PROP? .O ,P?SYNONYM <WORD-AT .LAST>>> <RFALSE>)>
    ...
```

"lamp" is in the brass lamp's `SYNONYM` list, and nothing else in the
Hall answers to it. So the noun is the lamp, the action is taking, and
the parser calls `V-TAKING`.

## 6. The rules run

`RUN-ACTION` (in `zforge/lib/i7/actions.zil`) goes through the six
lists in order, and `FOLLOW-RULES` runs each rule in a list until one of
them makes a decision. In the trace it looks like this:

```
PC=0x02687 depth=6  2OP:15  loadw          L00 L02 -> sp
PC=0x0268b depth=6  1OP:8   call_1s        sp -> sp
PC=0x02bd1 depth=7  2OP:14  insert_obj     G04 #01
PC=0x02bd4 depth=7  2OP:11  set_attr       G04 #13
PC=0x02bd7 depth=7  0OP:1   rfalse
PC=0x0268e depth=6  1OP:0   jz             sp ?0x02698
```

Read it top to bottom. `loadw` fetches the next rule from the list, and
`call_1s` calls it. The next three lines are `TAKE-STANDARD` from
step 3: the object in global 4 (the noun, our lamp) goes into object 1
(the player), it gets attribute 19 (`HANDLEDBIT`), and the rule returns
false. Back in the loop, `jz` sees the false and carries on to the next
rule.

The interpreter's side of `insert_obj` is in `zforge/vm/ops/objects.py`:

```python
def op_insert_obj(vm, obj, destination):
    """§15 insert_obj (2OP:14): obj becomes the first child of destination."""
    ...
    vm.objects.insert(obj, destination)
```

and `zforge/vm/objects.py` does the actual pointer shuffling in the
object tree (section 12 of the standard).

## 7. The same thing, from the inside

The testing build (`lamp.z8`) can tell you all of this while you play.
Type `actions` and `rules`, then `take lamp`:

```
>take lamp
[taking the brass lamp]
[Rule "can't take yourself rule" applies.]
[Rule "can't take other people rule" applies.]
[Rule "can't take what's already taken rule" applies.]
[Rule "can't take scenery rule" applies.]
[Rule "can't take what's fixed in place rule" applies.]
[Rule "standard taking rule" applies.]
[Rule "standard report taking rule" applies.]
Taken.
[taking the brass lamp - succeeded]
```

The five check rules are the third list of `TAKING-RULES`. None of them
objected, so carry out ran `TAKE-STANDARD`, and report printed "Taken.".
Type `tree` and you'll see the lamp has moved:

```
Hall
  yourself
    brass lamp
```

Now try `take me`. The very first check rule stops it, and the action
fails:

```
>take me
[taking yourself]
[Rule "can't take yourself rule" applies.]
You are always self-possessed.
[taking yourself - failed]
```

Or add a line like `Instead of taking the lamp: say "It's too hot."` to
the story and rebuild. Your rule turns up in the list by the words you
wrote it with, and you can see it stop the action before any check rule
runs.

## Where to go next

- `docs/DESIGN.md` suggests an order for reading the code.
- `docs/I7_LITE.md` lists the Inform 7 you can write, and
  `docs/I7_TO_ZIL.md` shows how each part is translated.
- `python -m zforge info --versions` shows how the four Z-machine
  versions differ, with the section of the standard behind each row.
- `docs/DECISIONS.md` records every choice we made where the standard,
  or Inform, left room for more than one answer.
