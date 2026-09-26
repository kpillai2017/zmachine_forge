# Known gaps (deliberate, for this version)

- **Versions**: 5, 7 and 8 are supported (ADR-021, ADR-023); version 6 comes
  with proforma v2 Tier 8, and versions 1-4 are refused (exit 2).
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
