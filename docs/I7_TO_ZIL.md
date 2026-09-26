# How zforge compiles I7-lite

    game.ni ──source──▶ sentences ──sentences──▶ typed sentences ──model──▶ world model
            ──lower──▶ game.zil (ZIL-lite text) ──existing ZIL compiler──▶ .zas ──▶ .z5/.z7/.z8

The I7 half **ends in ZIL-lite text**, handed unchanged to the compiler
zforge already has (`docs/ZIL_SUBSET.md`). `zforge compile game.ni
--emit-zil` writes that text beside the story, so every construct can be
studied as the ZIL it becomes. ZIL is what Infocom wrote its games in, so
the chain is also a history lesson: Inform 7 sentences become Infocom-style
code.

## Modules (`zforge/compiler/i7/`)

| Module | Job |
|---|---|
| `source.py` | read the file; strip `[comments]`; split into sentences and rule bodies (indentation, `;`), keeping line:column for every piece |
| `sentences.py` | classify each sentence into a typed record (`Assertion`, `KindDecl`, `PropertyDecl`, `VariableDecl`, `Understand`, `ActionDecl`, `Rule`, `PhraseDef`, `Use`, `Bibliographic`) |
| `nouns.py` | noun phrases: articles, names, `It`, `called` |
| `model.py` | the world model: kinds, objects, properties, map, variables, actions, rules. Two passes: first every name, then every assertion, so forward references work |
| `phrases.py` | rule bodies: `say`, `now`, `if`, `try`, ... into a small phrase tree |
| `conditions.py` | conditions: `X is in Y`, `the player carries X`, `and`/`or`, comparisons |
| `text.py` | quoted text: substitutions, `'` to `"`, `[if]`/`[one of]` |
| `lower.py` | model + phrase trees into ZIL-lite text |
| `problems.py` | Inform-7-style problem messages ("Problem. You wrote 'X' (line 12), but ...") |
| `driver.py` | `compile_i7(source, filename, target)` |

## The runtime library (`zforge/lib/i7/`, written in ZIL-lite)

The generated game starts with `<INSERT-FILE "lib/i7/runtime">`. The
library reuses `zforge/lib/parser.zil` (the parser Tier 3 built: noun
phrases, pronouns, "Which do you mean ...?", "What do you want to take?")
and adds what is Inform 7's own:

| File | What |
|---|---|
| `runtime.zil` | turn sequence: When play begins, the banner, read → action → Every turn → time passes → status line; `end the story` |
| `actions.zil` | `RUN-ACTION`: the rulebooks Before → Instead → Check → Carry out → After → Report; `TRY` |
| `standard.zil` | the standard actions as library rules ("Taken.", "You can't go that way.", ...) |
| `world.zil` | darkness and light, scope, looking (room heading, description, "You can also see ...") |
| `say.zil` | printing names with articles, numbers in words, `[one of]` state, adaptive text (7c) |

Messages follow Inform 7's standard wording (e.g. "You can't see any such
thing.", "That's not a verb I recognise."). `parser.zil` asks a hook for
its messages; ZIL games keep their own wording.

## Lowering, by example

**Things and rooms** become ZIL objects. Names become ZIL atoms by
upper-casing and joining words with `-`; clashes get a number.

    The brass hook is a supporter in the Cloakroom. It is scenery.
    Understand "peg" as the brass hook.

    <OBJECT BRASS-HOOK (IN CLOAKROOM) (DESC "brass hook")
        (SYNONYM BRASS HOOK PEG)                  ; every name word, any order
        (FLAGS SUPPORTERBIT SCENERYBIT)>

**Map connections** become exit properties, both ways unless the reverse
is already set (Inform 7's rule):

    The Bar is south of the Foyer.   ->   FOYER (SOUTH TO BAR),  BAR (NORTH TO FOYER)

**Text** with no substitutions becomes a string; text with substitutions
becomes a routine. A *text property* is always a routine, so the library
can print any of them the same way:

    The description of the cloak is "A handsome cloak of [colour] velvet."

    <ROUTINE CLOAK-DESCRIPTION () <TELL "A handsome cloak of "> <SAY-COLOUR> <TELL " velvet.">>

**Rules** become routines that first test their own preamble and return
false ("no decision") when it does not apply:

    Instead of going north in the Foyer:
        say "You've only just arrived."

    <ROUTINE RULE-12 ()       ; Instead of going north in the Foyer (cloak.ni:14)
        <COND (<NOT <AND <EQUAL? ,PRSO ,P?NORTH> <EQUAL? ,HERE ,FOYER>>> <RFALSE>)>
        <TELL "You've only just arrived." CR>
        <RTRUE>>              ; Instead rules stop the action when they finish

**Rulebooks** are tables of rule routines, one per action and stage
(`INSTEAD-GOING`, `CHECK-TAKING`, ...), plus one per stage for rules about
several actions (`doing something ...`). `RUN-ACTION` runs a stage's rules
in order until one returns true.

**Rule order** follows Inform 7: more specific rules first; ties in source
order, library rules before the author's (the Standard Rules come first
in a real Inform 7 source). Specificity, highest first: a named noun or
second noun > a kind (`something`, `a container`) > nothing; then an
`in <room>` clause; then a `when` condition. A rule for one action comes
before a `doing something` rule.

**Actions** become ZIL SYNTAX lines naming a routine `V-<ACTION>`, so the
action number is `V?<ACTION>`:

    Understand "hang [something] on [something]" as putting it on.

    <SYNTAX HANG OBJECT ON OBJECT = V-PUTTING-IT-ON>

`V-PUTTING-IT-ON` just calls `<RUN-ACTION ,PUTTING-IT-ON-RULES>`. `try`
saves the current action, sets `PRSA`/`PRSO`/`PRSI`, runs the same routine,
and restores the saved action.

**Adaptive text** (7c): `[We]` becomes `<TELL "You">` and sets the "prior
named" object to the player; `[are]` becomes `<SAY-VERB ,VERB-BE>`, which
prints "are" or "is" by the prior named object's number.
`To flow is a verb.` makes a verb table with its forms ("flow" / "flows"),
built by English spelling rules at compile time (flow → flows, carry →
carries, go → goes, have → has).

## Target versions

The generated ZIL declares `<VERSION 5>`, so, like every ZIL-lite source,
it builds for z5, z7 or z8 (`--target`, ADR-023); z6 follows in Tier 8.
Default for `.ni` files: z8 (big games fit; `.zil` files keep z5).

## Limits worth knowing

* Z-machine v4+ has 48 attributes; I7-lite uses one per either/or property
  in use, and the compiler reports "too many either/or properties" rather
  than failing later.
* Dictionary words keep 9 characters in v4+ (§13): `invisibility` and
  `invisible` are the same word to the parser. The compiler warns when
  two different Understand words collide this way.
* 240 global variables and 15 locals per routine (ZIL-lite limits) apply
  to generated code; the compiler keeps well inside them.
