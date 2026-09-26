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
