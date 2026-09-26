# ZIL-lite: the language the compiler accepts

ZIL (Zork Implementation Language) is the Lisp-like language Infocom wrote
its games in. zforge compiles a documented SUBSET of it straight to a v5
story file. No MDL macros (DEFMAC) and no compile-time evaluation.

Two ways to write a game's parser:
* by hand in ZIL, as `examples/cloak.zil` does, or
* Infocom-style: `SYNTAX` lines (compiled to a table) plus the small parser
  library `zforge/lib/parser.zil`, as `examples/cloak_syntax.zil` does.

## Syntax (lexer.py, reader.py)

    <FORM args...>   a call / declaration       <>      false (0)
    (LIST ...)       argument and property lists
    "string"         | is a newline; \" a quote; real newlines become spaces
    123  -5          decimal numbers            !\c     character code of c
    .X               value of LOCAL X           ,X      value of GLOBAL X (also
                                                         constants, objects,
                                                         routines, flags, P?prop)
    W?WORD           a dictionary word          ;       comments out the next form

## Top level (forms.py)

| Form | Meaning |
|---|---|
| `<VERSION 5>` | required target (EZIP/XZIP accepted) |
| `<CONSTANT NAME value>` | number, string or ,NAME |
| `<GLOBAL NAME init>` | init may be a number, string, ,NAME, W?WORD or a table |
| `<DIRECTIONS NORTH ...>` | declare direction properties first |
| `<PROPDEF NAME default>` | property default (§12.2) |
| `<OBJECT NAME clauses...>` `<ROOM ...>` | see below |
| `<ROUTINE NAME (args "OPT" (x d) "AUX" (y d) z) body...>` | at most 15 locals |
| `<INSERT-FILE "name">` | textual include of name.zil |
| `<COMPILATION-FLAG NAME T>` / `<COMPILATION-FLAG NAME <>>` | set a compile-time flag (ZILF) |
| `<COMPILATION-FLAG-DEFAULT NAME T>` | set it only if not set already |
| `<IFFLAG (NAME forms...) (ELSE forms...)>` | anywhere: replaced, as the source is read, by the forms of the first clause whose flag is true; an unknown flag is an error (ADR-034) |
| `<SYNTAX verb ... = ACTION [PREACTION]>` | a grammar line (see *Grammar* below) |
| `<VERB-SYNONYM TAKE GET>` `<PREP-SYNONYM ON ONTO>` | extra words for a verb / preposition |

Object clauses: `(IN obj)` / `(LOC obj)`, `(DESC "short name")`,
`(FLAGS F1 F2)`, `(SYNONYM w...)`, `(ADJECTIVE w...)`, `(PROP TO room)`
(1-byte exit), `(PROP values...)` (word values: numbers, strings, objects,
routines, W?words). Execution starts at `<ROUTINE GO ...>`.

## Expressions (codegen.py)

| Group | Forms |
|---|---|
| arithmetic | `+ - * / MOD BAND BOR BCOM RANDOM` (n-ary + - * /; `<- x>` negates) |
| predicates | `EQUAL? =? ==? N=? N==? G? L? G=? L=? ZERO? 0? 1? T? FSET? IN? NOT AND OR VERIFY FIRST? NEXT?` |
| variables | `SET SETG INC DEC` |
| objects | `MOVE REMOVE FSET FCLEAR LOC FIRST? NEXT? GETP PUTP GETPT PTSIZE NEXTP` |
| tables | `GET PUT GETB PUTB`, `<TABLE ...>` `<LTABLE ...>` `<ITABLE n [init]>` (+ `(BYTE)`) |
| output | `TELL` (strings, `CR`, `N x`, `D obj`, `C char`, `B addr`, or a packed string), `PRINT PRINTI PRINTN PRINTD PRINTC PRINTB CRLF` |
| input | `READ text parse`, `LEX text parse`, `INPUT 1` |
| screen | `SPLIT SCREEN CURSET HLIGHT CLEAR COLOR BUFOUT` (in v6, `CURSET` and `COLOR` take a window as a third argument) |
| screen, v6 only | `WINGET WINPUT WINATTR WINSIZE WINPOS MARGIN SCROLL FONT MOUSE-LIMIT MOUSE-INFO MENU DISPLAY DCLEAR PICINF PICSET PRINTF BUFFER-SCREEN XPUSH POP` - §8.8's windows, margins, user stacks and pictures. See examples/v6_windows.zil, and ADR-030 for what a character terminal can and cannot do. |
| control | `COND` (with `ELSE`/`T`), `REPEAT ()`, `DO (I from to [step])`, `MAP-CONTENTS (I container)`, `PROG (bindings)`, `BIND (bindings)`, `RETURN AGAIN RTRUE RFALSE RFATAL QUIT RESTART SAVE RESTORE APPLY` |
| grammar | `<VERB? TAKE DROP>` = `<EQUAL? ,PRSA ,V?TAKE ,V?DROP>`; `<PRSO? LAMP>` / `<PRSI? HOOK>` = `<EQUAL? ,PRSO ,LAMP>` |
| escape hatch | `<ZOP opcode args...>` - any §15 opcode by name, e.g. `<ZOP SAVE_UNDO>` |

A routine's value is its last form. See docs/DECISIONS.md ADR-009..013 for
the numbering, exit, RETURN and operand-order rules.

`<VERSION 6>` (or `YZIP`) makes a source version 6, which can only be
built for z6. A source written for version 5 can be built for z5, z6, z7
or z8 (`--target`): v6 adds opcodes but takes none away. The one form
that changed is `pull`, which stores its result in v6; the assembler says
so if a source uses it.

The v6 names above are Infocom's YZIP ones where they are known. Each maps
to the §15 opcode of the same job: `WINGET` is `get_wind_prop`, `WINPUT`
is `put_wind_prop`, `WINATTR` is `window_style`, `WINSIZE` is
`window_size`, `WINPOS` is `move_window`, `MARGIN` is `set_margins`,
`SCROLL` is `scroll_window`, `MOUSE-LIMIT` is `mouse_window`, `MOUSE-INFO`
is `read_mouse`, `MENU` is `make_menu`, `DISPLAY` is `draw_picture`,
`DCLEAR` is `erase_picture`, `PICINF` is `picture_data`, `PICSET` is
`picture_table`, `PRINTF` is `print_form`, `XPUSH` is `push_stack` and
`POP` is `pop_stack`. `PICINF`, `XPUSH` and `MENU` branch.

## Blocks: PROG and BIND (ADR-017)

    <PROG ((X 1) (Y) Z) body...>      bindings: (NAME value), (NAME) or NAME
    <BIND ((WIDTH <GETB 0 33>)) body...>

Both evaluate their body and yield the last form's value; every binding
starts fresh (its value, or 0) each time the block is entered.
* **PROG** is a target: `<RETURN v>` leaves it with v, `<AGAIN>` restarts
  its body (bindings are not re-initialised).
* **BIND** only scopes names: RETURN/AGAIN pass through to the enclosing
  PROG, loop or routine.

A binding becomes a hidden local, so a name already in use (a routine
argument, or bound by an enclosing block) cannot be bound again - the
compiler says so instead of silently sharing one variable.

## Grammar: SYNTAX lines (ADR-016)

    <SYNTAX LOOK = V-LOOK>                          verb alone
    <SYNTAX LOOK AROUND = V-LOOK>                   verb + particle
    <SYNTAX TAKE OBJECT = V-TAKE>                   one object
    <SYNTAX PICK UP OBJECT = V-TAKE>                preposition before it
    <SYNTAX WEAR OBJECT (FIND CLOTHBIT) = V-WEAR>   default object if none typed
    <SYNTAX HANG OBJECT ON OBJECT = V-HANG PRE-HANG>  two objects + preaction
    <SYNTAX DROP OBJECT (HELD CARRIED) = V-DROP>    search options (ADR-019)
    <SYNTAX TAKE OBJECT (INSIDE-PRSI) FROM OBJECT = V-TAKE>
    <VERB-SYNONYM TAKE GET GRAB>
    <PREP-SYNONYM ON ONTO>

The compiler does not parse English - it turns these lines into DATA
(`zforge/compiler/grammar.py`): constants `V?LOOK V?TAKE ...` (action
numbers, first-seen order), field offsets `S-VERB ... S-PREACTION` and
`S-SIZE`, search-option bits `SO-HELD SO-ROOM SO-INSIDE`, and
`SYNTAX-TABLE` - a row count followed by one 11-word row per verb x
preposition synonym. Search options become per-object bits: `HELD CARRIED
HAVE` -> SO-HELD, `ON-GROUND IN-ROOM` -> SO-ROOM, `INSIDE-PRSI` -> SO-INSIDE
(a zforge extension, not Infocom ZIL), `MANY` -> SO-MANY (several objects:
read only by the Inform 7 branch of lib/parser, ADR-035 - a ZIL game's
parser ignores it); `TAKE EVERYWHERE SEARCH ADJACENT` are accepted and
ignored.

`<INSERT-FILE "lib/parser">` supplies the run-time half, in ZIL:
`HERE LIT PRSA PRSO PRSI`, the `PLAYER` object, `<PARSER>` (read + match:
articles `the a an`, adjectives, scope = held items and, when LIT, the
room, one level deep) and `<PERFORM>` (preaction, room ACTION, PRSI ACTION,
PRSO ACTION, then the verb routine - the first to return true handles it).

The library also handles (ADR-018; try `examples/parser_demo.zil`):
* **pronouns** - `IT THEM HIM HER` mean the last direct object; "I'm not
  sure what "it" refers to." before there is one, "You can't see the X
  here." once it is out of scope;
* **ambiguity** - when several objects in scope fit, it asks "Which do you
  mean, the brass key, the iron key or the rusty key?". Every word of the
  reply must describe a candidate (`rusty`, `iron key`); a reply that still
  fits several asks again with only those, an empty reply cancels, and a
  reply about none of them is parsed as a brand-new command;
* **context** (ADR-019) - before asking, the row's search options narrow
  the candidates: SO-HELD keeps what the player holds, SO-ROOM what they
  don't, SO-INSIDE what is inside PRSI (object 2 is settled first). They
  are preferences - ignored if they would leave nothing - and a single
  survivor is announced: "(the rusty key)";
* **missing objects** (ADR-020) - `take`, `put`, `put key`, `put key in`
  fit a row except for a trailing object, so the library asks "What do you
  want to take?" / "What do you want to put the brass key in?". The reply
  (`cloak`, `the box`, `in the box`, `it`) completes the command; a reply
  starting with a verb is run as a new command.

