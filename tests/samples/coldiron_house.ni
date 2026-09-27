"Cold Iron's front room (I7-lite port)" by Andrew Plotkin

[The front room of Cold Iron (stories/coldiron.ni, lines 440-470), cut down
to what the "take all" check needs. Only the replies to commands are
compared with the real game, not the opening (eval: i7-coldiron-table).

The table is "a supporter" and nothing more - Inform 7 makes it fixed in
place by itself, which is the point of the check.

One change: the author's rule is "Report taking the book when the book WAS
on the table", and I7-lite has no past tense. A flag set just before the
taking does the same job.]

House is a room.

The table is a supporter in House.
Understand "maple", "maplewood", "furnishing", "handsome" as the table.

The book is a thing. The book is on the table.
Understand "battered", "old", "tales", "stories" as the book.
The book can be discovered or undiscovered. The book is undiscovered.
The book can be lifted or unlifted. The book is unlifted.

The non-axe is scenery in House. The printed name is "axe".
Understand "axe", "ax" as the non-axe.
The front-door is scenery in House. The printed name is "front door".
Understand "front", "door", "exit" as the front-door.

Before taking the book when the book is on the table:
	now the book is lifted.

Report taking the book when the book is lifted:
	now the book is unlifted;
	if the book is undiscovered:
		now the book is discovered;
		say "You pick it up off the table. It's an old book of tales you borrowed from Reverd Pearson up at the chapel. He made you promise to take care of it, not that you'd ever let a book get ruined -- the chapel only has six books, six story books that is, the Reverd has his big Book up on his lectern, but that isn't this one. This is just stories. You like stories, and the Reverd likes you to practice your reading.";
	otherwise:
		say "You pick it up off the table.";
	stop the action.
