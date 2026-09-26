# Known gaps (deliberate, for this version)

- **Versions**: 5, 6, 7 and 8 are supported (ADR-021, ADR-023, ADR-030);
  versions 1-4 are refused (exit 2).
- **Version 6 has no pictures, mouse or menus** (ADR-030): one unit is one
  character, so windows, margins and scrolling all work, but `picture_data`
  reports none available, `read_mouse` reports the pointer at rest and
  `make_menu` does not branch. The header bits are cleared to say so.
- **Newline interrupts** (§8.8.3.2.2): the line count is counted down, but
  the interrupt routine is not called. No story zforge builds uses one, and
  calling a routine in the middle of printing needs the VM to re-enter
  itself. §8.8.3.2.2.1's Zork Zero workaround is not implemented either.
- **`buffer_mode` in v6** is "undefined" in the Standard; zforge sets the
  current window's buffering attribute, as Frotz does.
- **czech.z8** has to be compiled locally (czech 0.8 ships only the v5
  binary): `brew install inform6`, then `inform -v8 stories/czech.inf
  stories/czech.z8`. Without it, `czech-conformance-z8` skips.
- **Timed input** (`aread`/`read_char` time + routine) is ignored (ADR-005).
- **Sound** effects beyond a terminal beep; **font 3** character graphics;
  `set_true_colour` is accepted but has no visible effect.
- **Input stream 1** (reading commands from a file via the opcode) - use
  `zforge run --script FILE` instead.
- **Plain mode** shows the upper window as `| ...` lines (ADR-014).
- **ZIL-lite** has no MDL macros and no `%` compile-time evaluation; AND/OR
  values are 1/0 (ADR-012); PROG/BIND cannot shadow a variable (ADR-017).
- **Grammar / parser library** (ADR-016, 018-020): no ALL / MANY (multiple
  objects) and no implicit TAKE; search options are preferences only (the
  verb routine still has to check); one level of containment in scope; one
  IT for all pronouns; at most 8 candidates are offered; the parser only
  asks for a missing object at the END of a command ("put in box" is not
  completed); questions print the verb from the dictionary, so a verb longer
  than 9 letters is shown truncated (§3.7: v5 dictionary words hold 9
  Z-characters).
- The **compiler** does no optimisation beyond merging adjacent TELL text and
  choosing the shortest call/branch forms.
- **Differential testing** against dfrotz runs only if dfrotz is installed.
- **I7-lite** is a subset (docs/I7_LITE.md): stories written for the full
  Inform 7 (Standard Rules internals, tables, relations, most activities,
  Inform 6 inclusions) do not compile - Advent's source
  cannot (docs/I7_SURVEY.md). Unsupported constructs are Problems, not crashes.
- **I7 turn count**: the runtime starts it at 1 and counts each turn in the
  world, so "score" after 4 turns says "in 5 turns". Not yet checked against
  a real Inform 7 game with scoring (Advent uses no scoring).
- **I7 undo** after an out-of-world command (e.g. "score") undoes nothing:
  the snapshot is taken every turn; Inform 7 undoes the last turn in the world.
- **I7 phrases**: no phrases with parameters, no "To decide which ...", no
  'let' / repeat / while yet; adaptive text and the survey additions (doors,
  devices, 'try', 'is usually' ...) are Tier 7b/7c.
- **I7 activities** (ADR-031): five are supported. The announcements of
  darkness and light, parser errors, supplying a missing noun and choosing
  notable locale objects are refused: their Inform 7 defaults could not be
  checked against a real game (Advent overrides them all), and the last two
  need parser changes. A *writing a paragraph* rule counts as having "said
  something" when any say ran, even one whose text came out empty
  (`say "[if false]x[end if]"`); the `while`
  clause (`... while taking inventory`) and `(called ...)` names in activity
  rules are not supported.
- **Resizing** (ADR-032): only the curses screen follows the terminal; the
  plain screen keeps `--width`. A v6 window that does not touch the
  screen's right or bottom edge keeps its size (and is clipped if the screen
  shrinks past it), until the game rearranges its windows in answer to the
  redraw request. v5/v7/v8 games are told the new size but not asked to
  redraw: the redraw bit is v6 only (§11), so their text reflows from the
  next line on and the status line from the next turn.

