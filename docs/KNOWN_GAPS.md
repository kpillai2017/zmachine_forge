# What zforge doesn't do (yet)

This is the honest list: the things zforge leaves out on purpose, the
places where it takes a shortcut, and the behaviour we believe is right but
haven't been able to check against the real thing. The numbers in brackets
point to the full reasoning in [DECISIONS.md](DECISIONS.md).

## Playing games

- **Only versions 5 to 8.** Games for versions 1 to 4 (most of Infocom's
  original catalogue) are refused with a clear message. (ADR-021, 023, 030)
- **No pictures, sound or mouse.** zforge runs in a text terminal. Version 6
  games get all their windows, since one character stands in for one pixel,
  but when a game asks whether pictures are available, the answer is no.
  The same goes for the mouse and for menus. Sound is at most a beep, and
  font 3 (Infocom's block graphics) isn't drawn. (ADR-030)
- **No timed input.** Some games do something if you wait too long at the
  prompt; zforge simply waits for you. (ADR-005)
- **Two small v6 corners.** A v6 game can ask to be interrupted after a
  given number of lines. zforge counts the lines but never makes the call,
  since no game it builds uses one, and neither does the workaround the
  standard describes for Zork Zero. What `buffer_mode` does in v6 isn't
  defined by the standard; zforge does what the Frotz interpreter does.
- **Reading commands from a file** is done with `zforge run --script FILE`,
  not with the machine's own "input stream 1".
- **Resizing the window** works in the full-screen display only. When you
  resize, a version 6 game is asked to redraw. The other versions aren't,
  because the standard only has a way to ask version 6: their text re-flows
  from the next line and the status line from the next turn. A v6 window
  that doesn't reach the screen's right or bottom edge keeps its size until
  the game rearranges things. (ADR-032)
- **In plain mode** the top window is shown as lines starting with `| `.
  (ADR-014)

## Writing Inform 7

zforge understands a subset of Inform 7, listed in [I7_LITE.md](I7_LITE.md).
Anything outside it gets a problem message naming the line, never a crash.
The biggest things missing:

- **tables, scenes, relations and lists**;
- **most activities**. Six are supported. The ones for darkness and light,
  for supplying a missing noun and for choosing what to mention in a room
  are refused, because we couldn't check how Inform does them by default.
  In a supported activity rule, the `while` clause and `(called ...)` names
  don't work. A "writing a paragraph about" rule counts as having said
  something as soon as it runs a `say`, even one that printed nothing.
  (ADR-031)
- **changes to Inform's own library from the inside.** Crowther's
  *Adventure* does this, so its full source can't be translated.
  ([I7_SURVEY.md](I7_SURVEY.md))
- **Inform 6 code** mixed into the Inform 7 source.

Smaller things:

- **Phrases** you define (`To praise (item - a thing): ...`) can take texts,
  numbers, truth states and things. There's no "To decide which ...", no
  "repeat with X running through ...", and a text passed to a phrase can't
  mention the phrase's own names. `let` names last to the end of the rule,
  not the end of their block, and a rule has to start on a new line.
  (ADR-034)
- **"The book is not lifted."** isn't understood after "The book can be
  lifted."; give both states a name instead: "The book can be lifted or
  unlifted. The book is unlifted."
- **The turn count** starts at 1, so "score" after four turns says five. We
  haven't found a real Inform 7 game with scoring to check this against.
- **Undo** straight after a command like "score" undoes nothing, where
  Inform would undo the last real turn.

## Things we believe are right but haven't checked

We check zforge against games built by Inform 7 itself wherever we can
(Crowther's *Adventure*, built in 2014, and *Cold Iron*, built in 2010).
These behaviours never came up in either game, so they follow our best
reading of Inform rather than a real game:

- **"Which do you mean ...?" inside a list**, as in "take lamp and coin"
  when there are two coins. It asks the same question as for a single
  thing. (ADR-036)
- **"all" and open containers.** "take all" includes what's on a table in
  the room, as *Cold Iron* showed, but not what's inside an open box. We
  don't know what Inform does there. (ADR-037)
- **The order of "take all"** when there are things both on the floor and
  on a table. (ADR-037)
- **Two error messages** that come from Inform 6's library: the one for
  "it" when "it" is out of sight, and "I didn't understand that sentence".
- **Which error wins** when several grammar lines fail in different ways
  ("put lamp in all"). The two older games showed that Inform's answer
  changed between versions: in the 2009 and 2010 builds, "all" after a word
  like "on" or "in" just gets "You can't see any such thing". zforge
  follows the 2014 build that *Adventure* was made with. (ADR-037)

## The parser in ZIL games

ZIL games use a simpler parser than Inform 7 games. It knows no "all" and no
lists of things ("take lamp and keys"), and it doesn't pick things up for
you before using them. It looks only one level inside containers, and "it",
"them", "him" and "her" all mean the same last thing. When a word matches
several things, it offers at most eight of them. It asks for a missing
thing only at the end of a command, so "put in box" isn't completed. When
it asks a question it prints the verb from the dictionary, which keeps only
the first nine letters of a long word. (ADR-016, 018-020, 035)

In Inform 7 games: the parser makes six of Inform's parser errors (the
others can be named but never happen), their messages are changed with a
"Rule for printing a parser error" rather than by editing responses, and a
few odd commands ("inventory foo") get "I didn't understand that sentence."
where Inform says more. The "(first taking the cloak off)" message can't be
edited, and Inform's "deciding whether all includes" activity isn't
supported. (ADR-034, 035)

## Writing ZIL

ZIL-lite has no macros and no compile-time evaluation. `AND` and `OR` give
1 or 0 rather than the last value, and a `PROG` or `BIND` can't reuse a
name that's already in use. (ADR-012, 017; [ZIL_SUBSET.md](ZIL_SUBSET.md))
The compiler doesn't optimise beyond joining neighbouring pieces of text
and choosing the shortest forms of calls and branches.

## Studying a game

The testing commands (`zforge compile --testing`) are `rules`, `actions`
and `tree`. Inform's others, such as `showme`, `scope`, `test` and
`rules all`, aren't there. `rules` shows the rules of actions and every rule
you write, but not the library's own rules for activities (how names are
printed, for example). When "take all" goes through a list, the action
line follows the "book:" label on the same line. (ADR-038)

## Testing

- **czech.z8** has to be built on your machine, since czech ships only its
  version 5 file. Install Inform 6 (`brew install inform6`), then run
  `inform -v8 stories/czech.inf stories/czech.z8`. Without it, that one
  check is skipped.
- **Comparison with dfrotz**, a well-known interpreter, runs only if you
  have it installed.

- **The player does not get a kind's "usually" values.** The player is an
  object of the runtime library, not of the story, so `The scent of a thing
  is usually "nothing".` gives every thing a scent but the player: the
  player's scent is no text, and printing it prints nothing. (ADR-050)
- **A text ending in punctuation and a space** (`say "goable. "`) ends the
  line, as if it ended with the punctuation. Real Inform, I believe, only
  ends the line when the last character is `.`, `!` or `?`; not yet checked
  against a real game.
