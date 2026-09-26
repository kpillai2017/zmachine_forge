# Contributing

The goal of this project is **readability for study**. A change is welcome
when a student can follow it with the Z-Machine Standard open beside it.

1. **Cite the spec.** Every opcode handler's docstring names its §15 entry;
   other code cites the section it implements (`# §4.7`). If the spec is
   silent or ambiguous, add a record to `docs/DECISIONS.md`.
2. **Plain Python.** Standard library only in `zforge/`. Short functions
   (the Reviewer flags anything over 60 lines), spec vocabulary for names,
   no metaprogramming or dispatch-by-reflection.
3. **Write the test first.** Unit tests live in `tests/`; behaviour the user
   sees belongs in `eval/cases.json`.
4. **Run the gates** before sending a change:

       ruff check .
       pytest -q
       python -m eval.run_eval
       python -m zbuilder --provider brief review
