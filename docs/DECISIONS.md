# Decision records

Where the Z-Machine Standard 1.1 is silent, ambiguous, or leaves a choice
to the implementer, the decision is recorded here and cited from the code.
New records are appended by `zbuilder.tools.decisions.record_decision`.

## ADR-001: Version 5 only
*spec: §1, §11.1* **Context.** Versions differ in header layout, object table
size, packed-address scale and opcode set. **Decision.** Only v5 is accepted
(v3/v6/v8 are rejected with a clear message). One version keeps every table
and routine readable without `if version >= 4` branches.

## ADR-002: Illegal opcodes are fatal, except unknown EXT >= 29
*spec: §14, §14.2.1* **Context.** `save`/`restore` as 0OP and `show_status`
are illegal in v5. **Decision.** Executing an illegal opcode stops with an
error naming the opcode and PC. Unknown extended opcodes from EXT:29 up are
reserved for future use and are skipped with a warning (§14.2.1).

## ADR-003: Object 0 is harmless
*spec: §12.3.3, §15 get_parent* **Context.** Object 0 means "nothing"; using
it is an error, but real games do it. **Decision.** As Frotz does: warn and
carry on with a neutral result (parent/child/sibling 0, attribute false,
moves ignored). `strictz.z5` exercises exactly this.

## ADR-004: Random numbers
*spec: §2.4, §15 random* **Decision.** `random n>0` returns 1..n from Python's
`random.Random`; `random -n` seeds it with n (predictable); `random 0`
re-seeds from the OS. `zforge run --seed N` makes whole runs repeatable.

## ADR-005: Timed input is not offered
*spec: §11.1 Flags 1 bit 7, §15 read* **Decision.** Flags 1 bit 7 is left
clear, so games do not rely on it; `time`/`routine` operands of `aread` and
`read_char` are ignored.

## ADR-006: Interpreter header values
*spec: §11.1.3* **Decision.** Interpreter number 6 (IBM PC), version 'Z',
Standard revision 1.1; screen size in characters with 1x1 font units;
colours/bold/italic/fixed-space advertised when the screen supports them.

## ADR-007: `--transcript` starts stream 2 immediately
*spec: §7.1.1, §7.3* **Decision.** Like Frotz's `-t`, `zforge run --transcript
FILE` sets Flags 2 bit 0 at start so the whole session is recorded.

## ADR-008: The assembler's start stub, and no abbreviations
*spec: §5.5, §3.3* **Context.** In v5 the initial PC is an instruction, not a
routine. **Decision.** The linker places `call_vn main; quit` at the initial
PC, so `main` can be an ordinary routine with locals. The abbreviations table
exists (every entry points at "") but the encoder never uses abbreviations -
it keeps generated text easy to read in a hex dump.

## ADR-009: ZIL FLAGS and property numbering
*spec: §12.3.1, §12.4* **Decision.** FLAGS become attributes 0..47 in first-seen
order. Property numbers 1..63 are given in first-seen order: DIRECTIONS
first, then PROPDEFs, then as met in objects. DESC is the short name, not a
property; SYNONYM and ADJECTIVE are word-list properties.

## ADR-010: ZIL exits
*spec: §12.4* **Decision.** `(NORTH TO ROOM)` is a 1-byte property holding the
room number; `(NORTH "message")` is a 2-byte property holding a packed
string. Game code tells them apart with `<PTSIZE ...>` (see examples/cloak.zil).

## ADR-011: RETURN inside loops
**Decision.** `<RETURN [v]>` inside REPEAT/DO/MAP-CONTENTS leaves the innermost
loop, and v becomes the loop's value; outside a loop it returns from the
routine (as in ZILF). Use `<RTRUE>`/`<RFALSE>` to leave a routine from a loop.

## ADR-012: AND/OR as values are 1 or 0
**Decision.** In a condition AND/OR compile to short-circuit branches. Used as a
VALUE they produce 1 or 0, not "the last value" as in MDL.

## ADR-013: Operand temporaries
*spec: §6.3, §4.2* **Context.** Operands are read left to right and each `sp`
operand POPS, so two computed operands would come off the stack reversed.
**Decision.** All but the last computed operand are stored in hidden locals
(.$T1, .$T2 ...). A routine that needs more than 15 locals in total is a
compile error with a clear message.

## ADR-014: Plain mode shows the upper window as a line
*spec: §8.6* **Decision.** With `--ui plain` (pipes, scripts) the upper window
is printed as `| ...` whenever the game switches back to the lower window
after changing it. Lower-window text is streamed as is.

## ADR-015: The read buffer's byte 1 belongs to the game
*spec: §15 read* **Context.** In v5, byte 1 of the text buffer is the number of
characters already present. **Decision.** We honour it (new text is appended)
and the game resets it before each READ, as Inform and ZILF libraries do.

## ADR-016: SYNTAX is compiled to data, the parser is ZIL code
*spec: §13 (dictionary, tokenise), §12.4 (word-list properties)* **Context.**
Infocom's compiler never parsed English; SYNTAX lines became tables that
the game's own parser walked. **Decision.** `grammar.py` desugars SYNTAX /
VERB-SYNONYM / PREP-SYNONYM into ordinary constants (`V?ACTION`, `S-*`
field offsets) and one `SYNTAX-TABLE` global (count, then 9-word rows:
verb, #objects, prep1, prep2, find1, find2, action, routine, preaction).
Later stages need no grammar knowledge, and the table is readable in the
`.zas`. Synonyms are expanded into extra rows (simple and small for demo
sized games). `zforge/lib/parser.zil` is the run-time matcher.

## ADR-017: PROG/BIND bindings are hidden locals; no shadowing
**Context.** MDL gives every PROG/BIND a fresh environment; a Z-machine
routine has one fixed set of at most 15 locals. **Decision.** Each binding
becomes an AUX local that is (re)initialised on entry to the block
(value or 0). Sibling blocks may reuse a name; binding a name that is
already in use - a routine argument or a name bound by an enclosing block -
is a compile error rather than a silent clobber. PROG is a RETURN/AGAIN
target (AGAIN restarts the body without re-initialising); BIND is not.

## ADR-018: Pronouns and "Which do you mean?"
**Context.** A parser that silently takes the first matching object is
surprising; Infocom's asked. **Decision.** Each object slot collects every
match in scope (up to 8) in `P-MATCHES1` / `P-MATCHES2`. When a SYNTAX row
fits and a slot has several candidates, `WHICH?` lists them and reads a
reply: candidates that every reply word describes (adjective, synonym or
article) are kept; one left = chosen, several = ask again, none = the reply
is parsed as a new command (the old command is dropped), empty = cancel.
`IT/THEM/HIM/HER` resolve to `P-IT`, set to PRSO after every successful
parse, and must still be in scope.

## ADR-019: SYNTAX search options are preferences
**Context.** Asking "Which do you mean?" for DROP KEY when only one key is
held is annoying; Infocom's grammar already says what fits (`(HELD CARRIED
HAVE)`, `(ON-GROUND IN-ROOM)`). **Decision.** The compiler stores each
object's options as bits in the SYNTAX row (`S-OPTS1/2`: SO-HELD, SO-ROOM,
SO-INSIDE). Before asking, the library narrows the candidates by each bit
in turn, skipping any filter that would leave none, and announces a single
survivor "(the rusty key)". Object 2 is settled first so that
`INSIDE-PRSI` - a zforge extension meaning "inside the indirect object",
for TAKE KEY FROM BOX - can use it. Options stay preferences, not rules:
the verb routine still reports "You aren't holding the key."
**Consequences.** Rows grew from 9 to 11 words; `TAKE MANY EVERYWHERE
SEARCH ADJACENT` are still ignored.

## ADR-020: Asking for a missing object
**Context.** "take" alone should be answerable with "cloak", as in
Infocom games ("orphaning"). **Decision.** MATCH-SYNTAX records
`P-MISSING` (1 or 2) when a row fails only because the words ran out where
an object belongs; if no row matches fully, the first such row is used:
the library asks "What do you want to put the brass key in?" (verb and
preposition printed from the dictionary with PRINTB, since the reply
overwrites PARSEBUF), accepts a noun phrase optionally led by that
preposition, and asks for object 2 next if both were missing. A reply that
starts with a verb, or holds an unknown word, is parsed as a new command.


## ADR-021: Versions 5-8 through one VersionProfile (supersedes ADR-001)
*spec: §1.1.4, §1.2.3, §5.4, §5.5, §11.1.6* **Context.** Proforma v2 adds
targets z6, z7 and z8 (and an I7-lite front end). ADR-001 kept v5-only code
readable by avoiding `if version` branches everywhere. **Decision.** Every
version-dependent rule lives in `zforge/common/versions.py` as data on a
`VersionProfile` (packing scale and offsets, file-length divisor, size limit,
start-up rule, opcode table). Other code asks the profile and never compares
version numbers (a test enforces this; only `versions.py` and `opcodes.py`
may). The refactor landed first with only `PROFILES[5]` registered, and it
is proven behaviour-preserving by `tests/golden/v1_hashes.json` (byte-identical
story files). v6/v7/v8 are accepted only once their tiers register a profile.
The default target stays z5 for `.zil` sources.

## ADR-022: Versions 7 and 8 use the version-5 opcode table
*spec: §1, §14* **Context.** Reading §14's V column literally ("the last line
whose V <= the target") gives v7 and v8 all 18 v6-only EXT opcodes and the
v6 forms of seven others (e.g. `pull` storing a result). But §1 ends:
"Versions 7 and 8 are identical to Version 5 except as stated at 1.1.4 and
1.2.3" (size limit and packed addresses only). **Decision.** The extractor
maps v7/v8 to the v5 table (`TABLE_VERSION` in `opcode_table.py`), and
`opcodes.table_for(7|8)` returns the v5 table. The counts are 98 / 116 / 98 / 98
for v5 / v6 / v7 / v8. **Note for Tier 8.** In v6, EXT:29 is `buffer_screen`
(Standard 1.1), so ADR-002's "unknown EXT >= 29 is skipped" rule must become
per-version.

## ADR-023: Versions 7 and 8; choosing R_O/S_O; the target setting
*spec: §1, §1.1.4, §1.2.3, §6.4.3, §11.1.6* **Context.** Tier 6 adds v7 and
v8, which §1 calls "identical to Version 5 except as stated at 1.1.4 and
1.2.3". **Decisions.**
1. *Profiles.* v7: 4P + 8·R_O / 4P + 8·S_O, divisor 8, 512K. v8: 8P,
   divisor 8, 512K. Both use the v5 opcode table and screen model.
2. *R_O and S_O (v7).* The assembler starts the routine area and the string
   area on multiples of 8 and sets each offset ONE 8-byte step before its
   area, so the first routine or string packs to P = 2. Pointing the offset
   exactly at the area makes the first routine P = 0, and §6.4.3 says a
   call to packed address 0 does nothing (found in testing: `hello.z7`
   silently printed nothing). Each area can reach 256K past its offset;
   packing refuses anything further, rather than silently wrapping.
3. *Size limit.* It is checked right after layout, before any packing, so an
   oversized story gets "v5 allows at most 256K (§1.1.4) - try --target z7
   or z8", not an "out of reach" message.
4. *Target setting.* `--target` > `zforge.toml` > `ZFORGE_TARGET` > the
   source (`<VERSION>` for .zil, z5 for .zas). The banner names the origin.
   A ZIL-lite source written for version N builds for any version with the
   same opcode set (`compatible_targets`: 5, 7, 8). `<VERSION 7>` and
   `<VERSION 8>` are accepted; EZIP stays 5 for v1 compatibility.
5. *Exit code 2* for an unsupported story version or target (the input is
   not something zforge handles); 1 stays for everything else. This changes
   one v1 test (a v3 story used to exit 1). `reject-non-v5` still passes
   unchanged; `reject-below-v5` adds the exit code and the new wording.
6. *czech.z8.* czech 0.8 ships only `czech.z5` plus `czech.inf` and the
   expected outputs `czech.out3/4/5/8`, so `czech.z8` is compiled locally
   with Inform 6 (`inform -v8`; 6.44 used). The case checks "Failed: 0" AND
   matches `czech.out8` line for line, except the 10-line "Header (No tests)"
   report, which the czech README says differs between interpreters. That
   makes the 19 print tests (which czech cannot judge itself) checked too.
   Without czech.z8 the case SKIPS with the instruction.

## ADR-024: Real v8 games as regression anchors
*spec: §1.2.3, §8, Quetzal* **Context.** czech tests opcodes one by one;
real games test them working together. **Decision.** Pin two freely
available IF Archive games that are both over 256 KB (so they need 8P
packing) and come from different compilers: `Advent_Crowther.z8`
(Crowther's 1976 Adventure, Inform 7 port by Chris Conley; its I7 source is
also on the archive, a reference for the I7-lite work) and `Jigsaw.z8`
(Graham Nelson, Inform 6). They were chosen from four candidates (plus Lost
Pig, Acheton), all of which played correctly. Each case checks key facts IN
ORDER (`must_contain_in_order`), so a restore that prints "Ok." but does not
bring the state back fails: this was verified by patching restore to keep
the current memory. **Found on the way.** `PlainScreen.read_line` echoed
input without moving the screen model's cursor, so games that re-prompt on
the same line ("Please respond yes or no. >") wrapped earlier every turn.
Fixed with `_next_lower_row()`; covered by a unit test.

## ADR-025: The I7-lite compiler lowers Inform 7 to ZIL-lite
*spec: docs/I7_LITE.md, docs/I7_TO_ZIL.md* **Context.** Inform 7's own
compiler goes through Inform 6 and targets z5/z8/Glulx only, and its
Standard Rules are a very large library (docs/I7_SURVEY.md). **Decision.**
Compile a documented subset, *I7-lite*, to ZIL-lite text and let the
existing ZIL compiler finish the job, so there is one code generator and the
output can be read (`--emit-zil`). Its runtime is written in ZIL-lite
(`zforge/lib/i7/`) and reuses `lib/parser.zil`. Choices made on the way:
Inform 7 stories default to **z8** (larger stories; `--target` overrides);
the player is IN the current room, as in Inform 7; directions are objects
(DIR-NORTH ...) because Inform 7 treats "north" as the noun of going;
every text property is a routine (so plain and substituted text print the
same way); rulebooks are six LTABLEs per action, ordered by specificity
(noun tests, then room, then *when*), library rules first on ties;
out-of-world actions skip Before/Instead/After and "doing something" rules;
a flag is declared by an object that is never anywhere (LIBRARY-FLAGS,
STORY-FLAGS), because ZIL creates a flag only when an object uses it.

## ADR-026: Parser: each match once, and Inform 7 wording (golden re-recorded)
*spec: -* **Context.** With the player inside the room (ADR-025), the
parser reached a held thing twice (as held, and one level down from the
room): "Which do you mean, the velvet cloak or the velvet cloak?". I7
stories also need Inform 7's parser messages. **Decision.** `ADD-MATCH`
ignores an object already matched; a new global `P-I7-STYLE` (0 by
default, set by the I7 runtime) switches the unknown-word and not-found
messages to "That's not a verb I recognise." / "You can't see any such
thing.". **Consequence.** The two v1 outputs that include the parser
(`cloak_syntax.zil`, `parser_demo.zil`) grew by 128 bytes each, so their
golden hashes were re-recorded; every other golden output is unchanged and
the v1 behaviour suite still passes 28/28 (their messages are unchanged).

## ADR-027: The player object answers to "me" (golden re-recorded)

**Decision.** `PLAYER` in `zforge/lib/parser.zil` gets `(SYNONYM ME MYSELF
SELF YOURSELF)`, so `x me` works in I7-lite games (where the player is in
the room, hence in scope). The two v1 examples that include the parser
change size by a few bytes (cloak_syntax 7688 -> 7720, parser_demo 5408 ->
5444) and are re-recorded; their behaviour is unchanged (v1 suite 28/28),
because in those games the player is not in scope.

**Also (Tier 7c).** Placing a room in something, or a thing in itself, is
now a problem message. Both usually mean a short name matched an existing
object ("The stream is scenery in the Stream Bank." - "stream" is the
Stream Bank), which Inform 7 also reports.


## ADR-028: Inform 7's named library rules, rule swapping and response edits

**Context.** The Advent comparison (I7_SURVEY) showed that real Inform 7
authors reshape the library: Advent replaces the room description rules,
edits 33 responses and forgets built-in grammar. The survey had put this
out of scope; the user chose to add it so that an I7-lite port of Advent's
opening could match the real game exactly.

**Decision.**
- The library is Inform 7's named rules in Inform 7's order: 72 rules, each
  one ZIL routine, with 50 responses written as Inform 7 text (catalogue in
  `compiler/i7/standard.py`, listed in I7_LITE.md section 9).
- Authors can name rules, unlist rules, list them instead of / before /
  after / first / last / in a rulebook, and edit responses. Rulebooks are
  ordered as in Inform 7 (specificity, then library before author, then
  source order); a replacement takes the replaced rule's place.
- Runtime behaviours copied from Inform 7 because the comparison depends on
  them: the game starts with `try looking`; arrivals run the carry out
  looking rules; the check new arrival rule marks rooms visited; writing an
  object's paragraph makes it the thing last named; a blank line separates
  one rule's finished sentence from a later rule's output.
- Also: forgetting grammar (`as something new`, `Understand nothing as`),
  going's action variables, `going nowhere`, `encloses`, `the player
  consents`, kind-owned properties (`Every room has ...`: every room gets
  the property, because `put_prop` needs it, §15), text properties with
  substitutions, lists of subjects, spaces kept inside texts.

**Still out.** Activities (so the banner cannot move), action variables,
kinds of action, author rulebooks, `does nothing`. The Advent port says the
same things with ordinary rules.

**Evidence.** Eval `i7-advent-differential`: the port of Advent's opening
(`examples/advent_opening.ni`), on z5 and z8, prints what the real Inform 7
game prints for all 31 responses of a 30-command walkthrough, line for line
and blank line for blank line. One normalisation: the banner and its blank
lines are set aside (Advent moves it with an activity). Mutations of one
word or one blank line are caught.

## ADR-029: Advent's preliminary cave: Inform 7 behaviours learned from the real game

**Context.** The Advent port (ADR-028) was extended past the grate to the
Top of Small Pit: the dark Debris Room, XYZZY, the cage, the rod and the
bird. Where Inform 7's documented behaviour and the real game's output
disagreed, the real game (Inform 7 6L38 output, run on our VM) decided.

**Decision.** I7-lite follows what the real game prints:
- `[It]`, `[it]`, `[There]`, `[there]` are printed as written, and the next
  verb agrees as a singular (`[We] [are] crawling ... [There] [are] a dim
  light` -> "There is"; `as [we] [approach] [it] [become] disturbed` ->
  "as you approach it becomes").
- Each new turn starts with nothing named (the crack's `[are]` after a
  look that ended on the plural steps prints "is").
- A thing first made by a sentence with "are" is plural-named, and "Some
  X" gives it the article "some" (Inform 7's inference; the port no longer
  needs "The keys are plural-named.").
- `move the player to X` describes X; `, without printing a room
  description` does not (Inform 7; no earlier example used it).
- A name met first in a list (`..., and Cobble Crawl are lighted`) is an
  assumed thing until a sentence gives it a kind; a map sentence makes it
  a room. A kind the author gave still gets a problem.
- Inventory notes are the list writer internal rule's responses (D, K, L),
  so `The list writer internal rule response (D) is "lit".` works.
- Also: adjectives before a kind (`an open unopenable door`), a kind then a
  place after a comma, `called` with adjectives, a door's other side (`The
  Hall is west from the steps.`), `Outside is nowhere.`, `if X,` blocks,
  modal verbs, `[']`, `held`, `does not carry`. A placement's description
  now splits at the last " in " (`a fixed in place thing in the Top`).

**Left out of the port, with a comment.** Advent's custom relations
(XYZZY is ported as an ordinary action with the same output), Understand
lines with `when`, `Inside from A ... are east from B`, the parser-error
activity and attacking. The walkthrough takes the food on its first visit:
Advent's food is "ambiguously plural", and later descriptions of the
Building would say "There are food here."

**Evidence.** Eval `i7-advent-differential`: 49 commands, z5 and z8, every
line and blank line the same as the real game. It stops before the Hall of
Mists, where the dwarves wake and move at random (Advent 1520). Golden
outputs unchanged; each behaviour above has a unit test in `tests/test_i7.py`.

## ADR-030: Version 6: one unit is one character

**Context.** Version 6 is Infocom's graphical Z-machine. Its screen is an
array of PIXELS with eight windows lying on top of each other like
transparencies (§8.8), and it can draw pictures from a separate file.
zforge is a character terminal program. Tier 8 had to decide what v6
means here.

**Decision. One unit is one character.** The font is 1 unit wide and 1
high (§11.1, header $26/$27), so every v6 coordinate - window positions
and sizes, cursor positions, margins, scrolling - is a character cell.
The Standard allows this: units are whatever the interpreter's font makes
them, and §8.8.3.2.5 simply reports the font size. Nothing in §8.8 is
skipped because of it: all eight windows, all four attributes, all
eighteen properties, margins, line counts and scrolling are implemented,
and `examples/v6_windows.zil` draws a bordered panel with text flowing
beside it to show them working.

**What is honestly absent**, with the Standard's own escape hatches:
- **Pictures** (§8.8.5). There is no picture file, so `picture_data`
  reports none available and does not branch, Flags 1's picture bit and
  Flags 2's picture bit are cleared, and `draw_picture` warns.
- **The mouse.** `read_mouse` writes the pointer at rest with no buttons;
  Flags 2's mouse bit is cleared.
- **Menus.** `make_menu` does not branch; Flags 2's menu bit is cleared.
- **Sampled sound.** The two bleeps work. A sampled sound with a callback
  raises, rather than leaving the game waiting for a sound that will
  never finish.
- **Newline interrupts** (§8.8.3.2.2) are counted but the routine is not
  called; see KNOWN_GAPS.

**Other decisions inside Tier 8:**
- **A v5 source may be built for z6** (`--target z6`). Version 6 adds
  eighteen opcodes and removes none, so everything a v5 source can say
  still means the same - except `pull`, which stores its result in v6,
  and the assembler says so if a source uses it. A **v6 source builds
  only for z6**, since it may use the v6-only opcodes.
- **The start-up stub is a routine in v6.** §5.4 CALLs the main routine
  at the packed address in $06, so the stub that calls the game's `GO`
  must itself have a packed address: it is laid out as the first routine
  of the routine area rather than before it.
- **Window 0 has wrapping on.** §8.8.3.3 lists window 0's attributes as
  scrolling, transcript and buffering; the note under §8.8.3.1.2.2 says
  wrapping "would normally be on for a window holding running text", and
  that window 0 has it on. The two passages disagree; zforge follows the
  note, as interpreters do.
- **Reaching the bottom of a window that does not scroll** is "undefined
  behaviour" (the §8.8 remark). zforge keeps the cursor on the last line,
  so later text overwrites it; nothing is ever painted outside a window.
- **Interpreter number 6 (IBM PC).** §11.1.3 says the choice matters in
  v6 because story files behave differently on different machines, and
  the §8.8 remark recommends interpreting DOS-intended files. zforge
  already reported 6, so v6 games get the machine they most expect.

**Evidence.** Evals `v6-story-file`, `v6-window-model`, `v6-opcodes`,
`v6-windows-demo` and `v6-reads-like-v5`; `tests/test_v6.py` (27 tests),
including the Standard's own worked wrapping example (§8.8.3.1.2.2) for
all four combinations of wrapping and buffering, cursor position
included. Every cross-version eval now covers z6, and the Inform 7 Advent
port prints the same 49-command walkthrough on z5, z6, z7 and z8.

## ADR-031: Inform 7 activities

**Context.** Activities are the second most common construct Advent uses
that I7-lite lacked (docs/I7_SURVEY.md), and the way real authors change how
the library prints things. Inform 7 gives each activity three rulebooks
(before, for, after) and runs them around a piece of library behaviour.

**Decision.**
- *One mechanism*: each activity is a table of three rulebooks plus the
  library's own way (lib/i7/activities.zil). `CARRY-OUT` runs the before
  rules, the for rules (the first that applies decides), the library's way
  if none did, then the after rules. `BEGIN-`, `HANDLING?` and
  `END-ACTIVITY` are the same three steps, so an author's rule can run an
  activity as Advent's heading and body rules do. Activity rules reuse the
  action machinery: the same preamble parser, the same noun tests
  (`object_guard`), the same specificity order.
- *Five activities*, the ones whose Inform 7 behaviour could be checked:
  printing the name, the banner text, the name and description of a dark
  room, writing a paragraph about. The library's own ways are the texts
  Inform 7 prints; the dark room's are the heading and body rules'
  responses (A), as in the Standard Rules, where they sit inside
  "if handling".
- *Every name goes through the activity* (`PRINT-NAME`), including the
  status line, which saves its paragraph state so a name rule cannot push a
  line break into it. A name rule that names its own thing gets the plain
  name: Inform 7 would recurse; we choose not to crash.
- *"Mentioned" means "said something"*: writing a paragraph about a thing
  gives it its own paragraph only if the activity printed text, as in
  Inform 7 (not merely if a rule applied). `PARA-FLUSH` counts says, since
  every non-empty say starts with it.
- *Refused, by name*: the other Standard Rules activities get a problem
  naming them, rather than "I don't understand".

**Checked against the real game.** The Advent port now prints its
introduction from `After printing the banner text` and runs Crowther's
dark-room activities through begin/handling/end. The differential grew
from 49 to 54 commands (lamp off, look, inventory, lamp on, look), and our
build still prints exactly what Inform 7 prints. Two Inform 7 behaviours
learned from it:
- A sentence-ending mark followed by a closing bracket or quote still ends
  the sentence: "(Type ABOUT ... implementation.)" is followed by a
  paragraph break (`ends_sentence`).
- A said text ending in a substitution, like Crowther's "...into a pit.[/b]",
  gets no line break of its own.

**Consequences.** No existing output changed: the golden builds, 184 tests
and all evals passed before any author activity rule existed. The survey's
"`Rule for <activity>`: out" becomes "partly in". `do nothing` became a
phrase on the way.

## ADR-032: The terminal is not a fixed size (Tier 9)

**Context.** Tier 8 drew v6's eight windows with curses, but the renderer
kept the grid it started with, drew typed text into the v5 lower window
whatever the story's version, and relied on curses.wrapper - which restores
the terminal after an exception, not after a signal.

**Decision.**
- *Resizing.* Each screen model has `resize(width, height)`. v5/v7/v8 keep
  the status line's rows and the lower window's NEWEST lines (up to the
  cursor), as a terminal does. In v6, windows that reached the old right or
  bottom edge follow the new one, a scrolling window whose cursor line
  would fall off scrolls up just enough to keep it, and everything is
  clipped. Then the machine rewrites the §11 screen-size header, and on v6
  sets Flags 2 bit 2 - the §11 remarks: the bit "may be set by modern
  interpreters after, for example, resizing the 'screen'". It is v6 only in
  §11's table, so it is a VersionProfile field (`redraw_request_bit`).
- *Typing is an overlay.* The line editor no longer writes into the grid;
  render() draws the typed text at `screen_cursor()` - the CURRENT window's
  cursor (§8.8.3.5 in v6). Found while building this tier: in a v6 game the
  old editor typed over the status line (row 0) and then blanked it
  (tests/test_curses_screen.py fails on the old code).
- *The cursor* follows §15 set_cursor -1/-2 through curs_set.
- *Signals.* SIGHUP and SIGTERM raise QuitGame("interrupted"), so zforge
  shuts down through its normal path and curses.wrapper restores the
  terminal. Measured without the handlers: SIGHUP (a closed terminal
  window) killed Python with the terminal left in curses mode; SIGTERM was
  cleaned up by ncurses itself, but around zforge's own shutdown (which is
  where a --transcript file is closed).

**Testing without a terminal.** tests/test_curses_screen.py drives the
real CursesScreen classes through real games with a stand-in window.
tests/test_curses_tty.py runs the real CLI in a pseudo-terminal (pty.fork):
it plays, resizes (TIOCSWINSZ + SIGWINCH), is killed, and must exit
normally having sent xterm's rmcup. Neither needs a screen, so both run in
CI - more than the one smoke test "skipped with no TTY" the plan asked for.

**Consequences.** No change for scripted play: the golden builds, the v1
suite and every transcript are unchanged.

