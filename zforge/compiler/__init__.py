"""The ZIL-lite compiler: ZIL source -> .zas assembly -> .z5 story file.

Pipeline (one module per stage - read them in this order):

    lexer.py        characters -> Tokens          "<TELL "Hi" CR>" -> < TELL "Hi" CR >
    reader.py       Tokens -> S-expressions       Form(Atom TELL, String Hi, Atom CR)
    forms.py        S-expressions -> typed AST    Tell([Str("Hi"), Newline()])
    semantic.py     symbol tables + checks        "FOO is a global; use ,FOO"
    codegen.py      AST -> .zas text              print "Hi" / new_line
    (zforge.asm)    .zas -> .z5

diagnostics.py formats errors as file:line:col with a caret.
The supported language is described in docs/ZIL_SUBSET.md.
"""
