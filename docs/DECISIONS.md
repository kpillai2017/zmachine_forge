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

## ADR-033: Version 6 on a plain stream

**Context.** `zforge run --ui plain` (also what `run` uses when stdout is
not a terminal) crashed on v6 at the first prompt: PlainV6Screen combined
the v6 model with the plain screen, but the v6 model's input hooks
(`_input_line`, `_input_key`) were never written for the plain screen, and
v6's set_window hid the plain screen's status-line display, so the status
line's padding streamed out as text. The evals play v6 through the virtual
screen, so none noticed; found by trying the README's own commands.

**Decision.** A stream has no cursor, so the plain screen treats a v6
window by what its attributes say it is for (§8.8.3.2). A window that
scrolls holds running text and streams (window 0, by default). A window
that does not is painted - the status line, the demo's panel: its text is
kept out of the stream and its rows are shown as "| ..." lines when the
game switches away from it, whenever they changed, exactly as v5's status
line is. The typed command is echoed into the window's grid but not onto
the stream, which has already shown it.

**Consequences.** A story that uses no v6 feature now prints byte-for-byte
the same in plain mode on z5, z6, z7 and z8 (tests/test_plain_v6.py). The
v6 demo also had a bug of its own, visible only once more than one command
could be typed: it never reset byte 1 of its text buffer, which §15 read
counts as letters already typed, so every command after the first was
glued to the one before. It now resets it, as Infocom's games did.


## ADR-034: Parser errors, rule placement, phrases with parameters

Context. Real Inform 7 sources customise parser errors. Advent's hint
system is the example: after three parser errors in a row near the locked
grate it asks "Are you trying to get into the cave?". That needs the
*printing a parser error* activity, `the latest parser error`, a `first`
rule, a phrase with text parameters and a preamble that goes on over
several lines.

Decisions.
- **One parser, two ways, chosen at compile time.** `lib/parser.zil` is
  shared by ZIL games and I7 games, and the ZIL games are frozen golden
  builds. So ZIL-lite gains ZILF's `COMPILATION-FLAG` / `IFFLAG`, resolved as
  the source is read: the I7 runtime sets `I7` before it includes the
  parser, and each error site says `<IFFLAG (I7 <I7-PARSER-ERROR ...>) (ELSE
  ...the old code...)>`. ZIL games see exactly the tokens they saw before
  (the golden check proves it: byte-identical).
- **The names are Inform 7's, the letters are not used.** The error names
  (`the can't see any such thing error`, ...) were read out of the compiled
  Advent_Crowther.z8, which contains them. Which response letter goes with
  which error could not be settled (Advent replaces most of them with a
  random choice of three messages; probing the real game under six random
  seeds showed an unknown verb is N, not M as one might guess). So I7-lite
  does not let the parser error internal rule's responses be edited; a
  `Rule for printing a parser error when the latest parser error is ...`
  does the same job and needs no letters.
- **Inform 7's wording, where the real game shows it**: `I'm not sure what
  'it' refers to.` (single quotes, not the double quotes I7-lite printed).
  The 'it' gone message follows Inform 6's library (`You can't see 'it' (the
  lamp) at the moment.`); the real Advent answers that one at random.
- **A parser error is a message, not a paragraph.** After the error's
  message no paragraph break is owed: an after rule's text follows on the
  next line. The real game shows it: its hint question comes exactly one
  blank line after the message, and that blank line is the hint's own
  `[line break]`.
- **First/last** is a group sorted before specificity, in every rulebook
  (actions, activities, every turn, when play begins) - the same groups the
  "is listed first/last" sentences already used.
- **Parameters are locals.** A phrase with parameters is a routine with one
  local per parameter; its uses are found by matching the definition's
  words, with a slot per parameter. A text parameter always holds a routine
  (a quoted text becomes one; a text variable gets a small one that prints
  it), so the phrase prints it with APPLY and never has to guess. The same
  bindings give `let` (AUX locals, declared after the body is compiled),
  `repeat with ... running from ... to` (a DO loop) and `while` (a REPEAT).
- **A text given to a phrase cannot use the giver's own names.** It is a
  routine of its own, which cannot see the giver's locals. Inform 7 would
  substitute such a text there and then (printing it into memory); until
  I7-lite does that, a problem message says so.

Consequences. The Advent differential grew by the hint system - three
errors, the question, "no" ("OK."), a reset by a good command, three more,
"yes" and the hint - and still matches the real game on z5 and z8. Finding
the docs table claiming `let`, `repeat`, `while` and parameter phrases
that did not exist led to building them; the table now says what is there.

## ADR-035: Several objects at once (TAKE ALL), as Inform 7 does it

**Context.** Inform 7 lets the player act on several things at once: `take
all`, `drop all except the lamp`, `take lamp, keys and food`. Its details are
easy to guess wrong, so every rule below was checked by playing the same
commands on the real Inform 7 Advent (the i7-advent-differential case now has
13 such commands).

**Decision.**
- The library's grammar lines say what Inform 7's say: `take [things]`,
  `drop [things preferably held]`, `put [things preferably held] in/on
  [something]`. `[things]` lowers to ZIL's `OBJECT (MANY)` (a new `SO-MANY`
  search bit, Infocom's name); `preferably held` adds `HELD`.
- The parser (I7 branch of lib/parser.zil, ADR-034's IFFLAG: ZIL games stay
  byte-identical and still do not know "all") reads ALL / EVERYTHING,
  EXCEPT / BUT and lists joined by AND or commas into a list of at most 16.
  A comma has no dictionary word: it is recognised by its text.
- What ALL means: take - what lies in the room, not scenery, fixed in place,
  people or the player; held-things verbs - what is carried, not worn.
- ALL is ONE object with the "(the keys)" note only when ONE thing could
  have been meant, counting things it then leaves out (for take, held
  things). Evidence: with only the keys held, real Advent's DROP ALL prints
  "(the keys)"; with only the bottle not yet held, its TAKE ALL prints
  "bottle of water: OK.". This is also how Inform's parser is known to work
  (candidates first, the "all includes" exclusions after).
- The turn loop runs the action once per object, each on its line after its
  printed name and ": ", without paragraph breaks between them, as one turn:
  one undo snapshot, every turn rules once. The second noun is left out
  (`put all in box`). A command's list is forgotten before the next one.
- New parser errors: *can't use multiple objects* ("You can't use multiple
  objects with that verb.") when a `[something]` verb is given several;
  *nothing to do* ("There are none at all available!" - Inform 7's parser
  nothing error response B, the one Advent edits) when ALL means nothing.
- Found on the way: Inform 7's *can't drop what's already dropped rule*
  ("[The noun] [are] already here.") was missing from the library; and "The
  desk is fixed in place." was read as a place called "place" (the
  containment pattern now steps aside for adjectives only).

**Consequences.** Real sources' `take all` works. Not done: "Which do you
mean" inside a list (an ambiguous name takes its first match), several
objects in the second slot, "(first taking off)" for worn things, and
Inform 7's "deciding whether all includes" activity.

## ADR-036: The second object, unclear names in a list, worn things

**Context.** ADR-035 left three gaps: "Which do you mean" inside a list,
several objects in the second slot, and "(first taking off)" for worn things.

**Evidence.** From the real Advent (i7-advent-differential, now 82
commands): every one-object slot refuses ALL, `and` and commas with the
*can't use multiple objects* error - `unlock grate with all` is "You can
only unlock the grate with one thing at a time." (Advent's edit prints
`[parser command so far]`: the verb, then for a second-slot problem the
first object with "the" and the preposition). From the real Advent's story
file (Inform 7 6L38's compiled Standard Rules): the rules *can't drop /
put / insert / give clothes being worn* exist, and the message is
"(first taking [the noun] off)", compiled right after the dropping,
putting on and inserting messages it belongs with. The rules for what ALL
includes named there exclude people, scenery and fixed in place things -
none excludes worn things; the parser leaves them out (as it leaves out
held things for TAKE ALL, also with no named rule) - recalled from
Inform 6's parser, not observed: Advent has nothing to wear. Neither
pinned game has two things of one name in reach, so "Which do you mean"
inside a list is not checked against a real game.

**Decision.**
1. The second object is always one thing: ALL / a list there is the
   *can't use multiple objects* error.
2. Errors are ranked as Inform 6's parser ranks them (can't see < can't use
   multiple objects < not sure what "it" means < "it" gone < nothing to
   do); only a strictly higher error replaces the one kept, so among equals
   the first row's error is reported (the "unlock ... with" row before
   "unlock", as in Inform 7's sorted grammar). Inform 7 games only: ZIL
   games keep "the last row's error" (their bytes are unchanged).
3. An unclear name in a list is kept as a placeholder while the command is
   read; once the command fits, each placeholder gets the question a single
   object gets (CHOOSE), in order. (Asking at once would overwrite the rest
   of the command: the answer is read into the same buffer.) After
   `except`, an unclear name takes out every thing it fits.
4. The three clothes-being-worn rules (giving is not an I7-lite action):
   "(first taking [the noun] off)", silently try taking off, stop if still
   worn. Not editable, like the carrying requirements rule's "(first taking
   the X)".
5. An internal rule's response is printed with no automatic line break
   (Inform 7 prints it from Inform 6 code, not with `say`): the real
   Advent's edited "Please respond yes or no. " is followed by the prompt on
   the same line. The yes or no question internal rule is new (Advent edits
   it).

**Found on the way** (bugs of ADR-035, each with a test now): the list code
used object 2's candidate table as scratch and left it filled, so an
ambiguous LAST item of a one-object command got a bogus extra question;
`drop all and lamp` collapsed to one object when ALL had one candidate,
dropping the lamp silently; a new command typed as the answer to a list's
question kept the old list (the reset was in the turn loop, and the answer
is parsed from inside the parser).

**Consequences.** Several objects now work in every position I7-lite's
grammar allows, as Inform 7 does it. Not done: Inform 7's "deciding whether
all includes" activity; editing the "(first taking ... off)" message.

## ADR-037: A second real game - supporters, "all" and the table (Cold Iron)

**Context.** Three things in ADR-035/036 rested on memory rather than on a
real game: whether "all" leaves out worn things, how "Which do you mean"
behaves inside a list, and whether Inform 7 makes a supporter fixed in
place. We looked for a second game built by Inform 7 to Z-code, with its
source published, and pinned Andrew Plotkin's *Cold Iron* (release 6,
Inform 7 build 6G60, 2010; `stories/urls.txt`). We also played Stephen
Granade's *Fragile Shells* (build 5Z71, 2009) without pinning it: it
comes as a Blorb file, and only one of its answers is used below.

**What the real games showed.**
1. *Cold Iron* says "The table is a supporter in House." and nothing
   more: no "fixed in place", and no rule about taking it. Yet
   `take table` answers "That's fixed in place." So **a supporter is
   fixed in place unless the author says otherwise.** I7-lite let you pick
   one up. Now the supporter kind carries FIXEDBIT, like doors, and
   "portable" still overrides it.
2. `take all` in *Cold Iron*'s front room takes the book lying **on** the
   table, and prints it as a list ("book: ..."): the fixed table counts as
   a thing you could have meant. I7-lite's "all" only looked at the floor.
   Now it also looks at what's on each supporter in the room (one level,
   the same as the parser's scope), right after that supporter.
3. *Fragile Shells* starts you wearing a spacesuit, holding nothing.
   `drop all` answers "There are none at all available!", and the source
   has no rule that would make it so. So "all" leaves worn things out, as
   I7-lite already did.
4. Neither game has two things that honestly share a name early on.
   *Fragile Shells* seems to (two "walls"), but its author's "Does the
   player mean" rule makes the choice, so it tells us nothing about
   Inform's own. **"Which do you mean" in a list stays unchecked.**
5. The 2009 and 2010 builds answer "all" after a word like "on", "at" or
   "off" with "You can't see any such thing" (`put book on all`,
   `take off all`), and `put book on table and book` with "I only
   understood you as far as ...". The 2014 build of *Adventure* answers
   the same kind of command with "one thing at a time". Inform's parser
   changed between these builds, so the older games can't settle which
   error wins when grammar lines disagree. We follow the 2014 build and
   leave that question open.

**Decision.** Fix 1 and 2. Keep the rest, and list the unchecked points in
KNOWN_GAPS. Open containers stay out of "all": no game has shown what
Inform does with them.

**How it's checked.** `tests/samples/coldiron_house.ni` rebuilds the front
room in I7-lite, with the author's own rule for picking up the book. The
eval case `i7-coldiron-table` plays the same commands on it and on the
real `coldiron.z8`, and compares the replies (not the game's long
opening, which the port doesn't reproduce; `"replies_only": true`). The
port found one gap of its own: "The book is not lifted." isn't understood
after "The book can be lifted.", so the port names both states.

## ADR-038: Inform's testing commands, for studying a game

**Context.** The project is for studying how a game works, and Inform 7
already has the right tools for it: `rules`, `actions` and `tree`, which
it leaves out of a released game.

**Decision.**
1. `zforge compile --testing` (Inform 7 sources only) adds the three
   commands. Ordinary builds are exactly what they were: the extra code is
   in `lib/i7/testing.zil`, included only for such builds. A test checks
   that a testing build plays the same as an ordinary one while the
   commands aren't used.
2. `rules` shows `[Rule "..." applies.]` for each rule once its opening
   line matches, as Inform does. For your own rules, the check sits right
   after the rule's conditions, and the rule is shown in the words you
   wrote ("Instead of taking the lamp"), or by its name if it has one.
   The library's rules are called through a small wrapper that prints
   their Inform names. A library rule's conditions are just its action's,
   so it applies whenever it is reached.
3. `actions` prints `[taking the lamp]` when an action starts, and
   `[taking the lamp - succeeded]` or `- failed` when it ends. The name
   comes in two parts around the first thing, as Inform writes it
   ("putting" + the book + "on" + the table). The testing commands don't
   list themselves.
4. `tree` prints each room with everything in it, indented once per level,
   marks worn things, and ends with the things that are nowhere
   (off-stage). The compiler gives it a list of every room and thing.

**Not done.** Inform's `showme`, `scope`, `test` and `rules all`; tracing
the library's own activity rules. The wording of the on/off messages
follows Inform's as we remember it, and hasn't been checked against a
real game (release builds leave the commands out).

## ADR-039: Five sentence-reading fixes found by rewriting Bronze

**Context.** Rewriting Emily Short's *Bronze* in I7-lite (a local study
copy, not in the repository) was the largest I7-lite source so far, and
it found five places where the compiler misread a sentence, silently or
with an unhelpful message.

**Decision.**
1. *An object moved by a short name.* `The inkpot is in the Black
   Gallery.`, written after "the history of the inkpot" existed, took the
   inkpot to be that history (a short name, as Inform allows) and quietly
   moved it, so no inkpot was ever made. Short names stay as they are,
   because many stories rely on them; instead, putting something in a
   second, different place is now a problem, as it is in Inform 7, and
   the message explains the short-name trap when the sentence didn't use
   the full name.
2. *A keyword inside a quoted text.* `The description of the small key
   is "...intended to unlock more than one thing".` was read as a lock
   and key sentence. The sentence patterns now look at a copy in which
   quoted texts are blanked out, so no keyword inside a quote can match.
3. *Map sentences.* `It is south of the Lower Bulb.` after a room made a
   room called "It"; now `It` and `They` mean the last room (or door),
   and anything else is a problem. A list of exits separated by commas
   (`south of A, southwest of B and southeast of C`) made one room named
   after the whole list; commas now separate exits, like "and". (A
   plural door, `They are above X and below Y.`, was suspected too, but
   it already worked; a test now says so.)
4. *Too many either/or properties.* More than the Z-machine's 48
   attributes gave 162 ZIL errors reported as "a bug in zforge". The ZIL
   compiler now reports it once, with the total and the attributes that
   didn't fit; for an Inform 7 source it becomes a problem at the first
   either/or property that didn't fit, with the list and a suggestion.
5. *A full stop after a bare text.* A room description ending in
   `[end if]".` was printed with its quote marks and full stop. A text
   ending in `]` can't end a sentence by itself, so authors add the
   full stop after the quote; it is now dropped, as Inform does.

Each fix has a test in `tests/test_i7_sentence_fixes.py`, and every I7
example (and Bronze) builds byte-for-byte as before.

**Not done.** Falling back to properties when the attributes run out,
which would let such a story compile as it is.


## ADR-040: Numbers for actions no command asks for

**Context.** ZIL gives an action its number (`V?LOOKING-TOWARD`) from the SYNTAX
lines that use it. An I7 action with no Understand line - one that only `try`
starts, like Bronze's "looking toward" - had no SYNTAX line and so no number, and
the build stopped with an internal error.

**Decision.** After writing every SYNTAX line, the I7 lowering gives each action
that none of them mentions a number of its own, from 1000 up, clear of the numbers
ZIL gives the typed actions (1, 2, 3, ...). The runtime only ever compares action
numbers, never uses them as indexes, so any unused number serves. ZIL games are
untouched. Also: `silently try ...` (Inform's order) is accepted as well as
`try silently ...`.

## ADR-041: Understand phrases match only as a whole

**Context.** `Understand "puzzle piece" as the jagged piece` was silently
dropped: a thing's words were single words only. Splitting a phrase into its
words was tried and was wrong - Glasshouse's "brass winding key" made "brass
key" ambiguous, and its "pitcher plant" made plain "pitcher" ambiguous.

**Decision.** As in Inform, a phrase names the thing only as a whole. The
compiler gives a thing a `PHRASES` property: each phrase's words, then 0 (at
most 32 words, the Z-machine's limit for a property, §12.4.2 - more is a
problem). In Inform 7 games `MATCHES?` walks the typed words, each step taking
a whole phrase of the thing or one word that describes it; the words must all
be used and the last step be a noun or a phrase. A slash is between words
("wooden shape/bit"). A phrase word that can't be typed is a problem.

The new `MATCHES?` and its helper `PHRASE-AT` are inside `<IFFLAG (I7 ...)>` in
`lib/parser.zil`, with the ZIL version left as it was, so ZIL games build
byte-identical (the golden builds are unchanged). `<PROPDEF PHRASES 0>` is in
the Inform 7 runtime. ZIL-lite now also adds a `W?word` used only in a
property list to the dictionary, as it already did for one in code.

## ADR-042: AGAIN (G) in Inform 7 games

**Context.** Inform's AGAIN, or G, repeats the last command; the official
*Bronze* walkthrough uses it, and I7-lite did not have it.

**Decision.** In Inform 7 games the parser keeps a copy of each command typed
at the prompt - its text buffer and its word buffer, whose word positions
count from the start of the text buffer (§13.6.3), so the copies stay in step.
A command that is just `again` or `g` puts the copy back and is parsed as if
typed. As the real *Bronze* does: a command that failed is repeated too, AGAIN
never repeats itself, and with nothing to repeat it says "You can hardly
repeat that." and takes no turn. An answer to "Which do you mean" is not kept,
so AGAIN repeats the whole command (and asks again). The code is inside
`<IFFLAG (I7 ...)>` in `lib/parser.zil`, so ZIL games are unchanged.

## ADR-043: Lists of things, and one-line rules after another sentence

**Context.** `A red ball and a blue ball are in the Hall.` made one plural
thing called "red ball and a blue ball" (so TAKE BALL could not ask which),
and `The player carries a lamp and a key.` one called "lamp and a key".
Separately, a one-line rule after another sentence on the same line
(`The count is a number that varies. Every turn: increase the count by 1.`)
was read as an assertion and reported as not understood.

**Decision.** As in Inform 7, a subject list with "are" (placing, and the
adjective sentences that already did this), and the object of carries /
wears, names one thing per name (split at commas and "and"). A new thing
named with "some" gets "some" as its article, and in an "are" sentence is
plural-named. The source reader turns any complete one-line rule found
inside an assertion paragraph into a rule, with the same tests as a rule at
the start of a line.

**Consequences.** A name containing "and" in such a sentence must use
`called`, as in Inform. The five I7 examples build byte-identical.
Tests: tests/test_i7_sentence_fixes.py sections 9-10.

## ADR-044: 'if X, <phrase> instead' stops only when X holds

**Context.** In a rule, `if the box is not seen, say "Not seen." instead;`
was compiled with the stopping outside the `if`, so the rule always stopped
at that line and the lines after it never ran, with no warning.

**Decision.** The one-line `if X, <phrase>` form is recognised before a
trailing `instead`, so the `instead` belongs to the branch, as in Inform 7.

**Consequences.** None of the examples used the form, so all build
byte-identical. Test: tests/test_i7_sentence_fixes.py section 11.
Found while adding the Rooted Room's inscription reply to Bronze.

## ADR-045: Topics (Inform's [text]), steps A and B of docs/TOPICS_PLAN.md

**Context.** Inform 7 lets a command carry free words - a *topic* - for
conversation (ASK, TELL, ANSWER), books and notes (LOOK UP, CONSULT) and an
author's own actions. I7-lite had none, so Bronze's port faked LOOK UP with
hidden objects whose names clashed with real things.

**Decision.**
* A grammar slot marked `(TOPIC)` (option bit `SO-TOPIC`) takes the words up
  to the next word its line expects, or the end, and records where they are
  (`P-TOPIC-FIRST` / `P-TOPIC-LAST`). It names no thing: the thing typed in
  the other slot is the noun either way (`look up T in X`, `consult X about T`).
* Unknown words: in an Inform 7 game they are only an error once no grammar
  line takes them as part of a topic (still at once for the verb); the
  errors are the ones given before. A missing topic is not asked for:
  "I didn't understand that sentence.", as Cold Iron says.
* A topic pattern becomes a table of word positions, each with the
  dictionary words allowed there (0 for `--`); `TOPIC-FITS?` tries it,
  whole (rules, `matches`) or anywhere (`includes`).
* The four standard actions, with the rules and replies of Inform 7. Their
  replies were compared with Cold Iron's, word for word; that the block
  asking, telling and answering rules are *check* rules and the block
  consulting rule a *report* rule is from memory of the Standard Rules.
* Everything is inside `<IFFLAG (I7 ...)>` (a global rather than a local,
  since a new local would change every game's PARSE-COMMAND): ZIL games and
  their golden builds are unchanged. Inform 7 games grow by the four actions.

**Consequences.** Found on the way: a quotation mark in a rule's preamble
ended the ZIL comment the compiler writes above the rule; comments now use
single quotes. Tests: tests/test_i7_topics.py.

## ADR-046: Topic tables (step C of docs/TOPICS_PLAN.md)

**Context.** Inform authors usually list topics in a table and look the
player's topic up in it; Bronze's notes, papers and contract book do.

**Decision.** Only topic tables: one `topic` column and columns of texts,
written in Inform's layout (tab-separated). The reader keeps a table's rows
with the sentence; the model checks them. Each table becomes TABLE-n-FIND,
which tries the rows' topics in order (the same topic patterns as rules)
and remembers the first that fits in CURRENT-TABLE and CURRENT-ROW; each
column name becomes ENTRY-<COLUMN>, which prints that row's entry.
`a topic listed in the Table of X` works in a rule's action and in `if the
topic understood is ...`.

**Consequences.** Anything else about tables (numbers, `choose a row`,
`repeat through`) is not supported and is reported as such. Printing a
blank entry (`--`) prints nothing, where Inform would stop with a run-time
problem. Tests: tests/test_i7_topics.py, step C.

## ADR-047: What porting Bronze to topic tables showed (step D)

**Context.** Step D replaced the Bronze port's stand-in look-ups with the
original's three topic tables, copied from `Bronze.txt` by I7-lite's own
reader. Four things in I7-lite had to change for them to work as written.

**Decision.**
* **Quoted text over several lines.** Inform lets a quoted text go on over
  line breaks and blank lines; the original's entries do. The reader now
  joins such lines first (a line break is a space, a blank line a
  `[paragraph break]`) and keeps each line's source line number, so
  problems still name the right line. An unclosed quote is left alone.
* **A paragraph break at the end of a say** is a line break and a blank
  line *owed* (PARA-BREAK), as in Inform 7: printed before the next text,
  absorbed by the prompt. Before, it was two line breaks, and a turn ending
  with one showed an extra blank line before the prompt.
* **Topic patterns are written inline**, as a table in the test itself.
  One global each ran out of the Z-machine's 240 globals: the three tables
  have over 100 topics.
* **A rule may name a topic action without its topic** (`consulting the
  great contract book`, as the original writes it): any topic.

**Consequences.** Bronze's look-ups answer from anywhere the notes are,
X TAMBOURINE in the Study no longer asks which you mean, and the port lost
its invented "nothing under that name" messages (the original gives the
standard reply). The original also cuts "the" out of look-up commands
("After reading a command"), which I7-lite cannot do; the port's topics
start with an optional "the/--" instead. Tests: tests/test_i7_topics.py.

## ADR-048: Blank lines, checked against the real Bronze

**Context.** Comparing the Bronze port with the real game (built by
Inform 7), response by response over the 589-command walkthrough, showed
that I7-lite's blank lines were often wrong where its words were right:
only 187 of the 347 responses with the same words matched exactly.

**Decision.** Three rules of Inform 7's spacing, each checked against the
real game:
* **Printing a description leaves "something was said"** (SAY-P), as any
  printing does in Inform: the room's description, a thing's paragraph,
  "You can see ... here." and an examined thing's description end with a
  sentence break, so the next rule's text is set apart by a blank line
  (before, "You read: ..." came straight after the sign's description).
* **Going spacing.** After going, the room's name is set off by a blank
  line (the describe room gone into rule sets GOING-LOOK); after LOOK it
  is not. The real game does this after 262 of 302 moves (the others were
  blocked or printed something first); Advent's rooms have no names, so
  the Advent case never saw it.
* **A description that already ended its line gets no extra line break**
  (PARA-END): when a say inside it, such as a say phrase's, ended a
  sentence and nothing followed on the line. The compiler clears SAY-P
  when text follows a say phrase in the same text, so SAY-P can be trusted.

The Advent case now compares the blank lines at the start and end of each
response too (eval/differential.py): before, it could not see a blank line
too many before the prompt, and it passed with the paragraph-break bug of
ADR-047 (it now fails on that version).

**Consequences.** 346 of the 347 responses match the real game exactly;
the one left is the real game printing two blank lines after one room
description (a quirk of the original's own rules). Every I7-lite story
gains blank lines where Inform prints them (Glasshouse: 29, no other
change). The Bronze port's Beast thoughts now come from an After going
rule that tries looking, as in the original. Tests:
tests/test_i7_paragraphs.py.
