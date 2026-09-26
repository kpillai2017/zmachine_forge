"Adventure" by "William Crowther"

[The opening of Colossal Cave: William Crowther's Adventure, as ported to
 Inform 7 by Chris Conley (the IF Archive's Advent_Crowther_source.txt,
 pinned in stories/urls.txt), rewritten in I7-lite. The texts are Crowther's.

 The same commands, played here and on the real Inform 7 game
 (stories/Advent_Crowther.z8), must show the same text: the eval case
 i7-advent-differential. Where Conley's source uses Inform 7 that I7-lite
 lacks, this port says the same thing another way; each such place names
 the source line it replaces.]

Part 1 - Crowther's rules

A room is usually dark.
Every room has a number called the description print count.
Every room has a text called the short description.

[Advent 233-254: look again at the end of certain turns. Conley keeps
 'looked intentionally' as an action variable; here the truth state itself
 says it: a look while look later is false is one the player asked for.]
Look later is a truth state that varies.
When play begins: now look later is true.
Before going nowhere: now look later is true.
After going: now look later is true.
Every turn when look later is true: try looking.
Before looking when look later is false:
	say "Sorry, but I am not allowed to give more detail. I will repeat the long description of [our] location."
After looking: now look later is false.

[Advent 296-321: Crowther's hints. A few are given after failing to solve a
 puzzle - but only after 3 parser errors in a row. Every turn rules run only
 after a command was understood, so they reset the count.]
The count of sequential parser errors is a number that varies.

The first after printing a parser error rule:
	increment the count of sequential parser errors.

Every turn: now the count of sequential parser errors is 0.

To pose the question (proposition - a text)
 with affirmative response (hint text - a text):
	if the count of sequential parser errors is 3:
		now the count of sequential parser errors is 0;
		say "[line break][proposition][paragraph break]  ";
		if the player consents:
			say "[hint text][paragraph break]";
		otherwise:
			say "OK."

[Advent edits the parser error internal rule's response (N) - its message
 for a word it does not know - to "I don't know that word. ". I7-lite does
 not let a parser error's responses be edited; this rule says the same.]
Rule for printing a parser error when the latest parser error is the not a verb I recognise error:
	say "I don't know that word. ".

[Advent 330, 388 and 395, the same way: its edits of the parser error
 internal rule's response (H) - one thing at a time - and of the parser
 nothing error internal rule's response (B) - TAKE ALL with nothing there.]
To say dunno:
	say "I don't know how to apply that word here. ".

Rule for printing a parser error when the latest parser error is the can't use multiple objects error:
	say "[We] [can] only [parser command so far] one thing at a time. ".

Rule for printing a parser error when the latest parser error is the nothing to do error:
	say "[dunno]".

[Advent 261: there is nothing to examine closely.]
Instead of examining something: try looking.

[Advent 354, 363, 367.]
The standard report taking rule response (A) is "OK."
The can't take what's already taken rule response (A) is "[We] [are] already carrying [regarding the noun][them]! ".
The standard report dropping rule response (A) is "OK."
The can't go that way rule response (A) is "There is no way to go that direction."
The list writer internal rule response (D) is "lit".

[Advent 268-271: Crowther always displayed the initial appearance of everything in a room.]
After dropping something:
	now the noun is not handled;
	continue the action.

[Advent 425-487: the first time, and every fifth time after, a room shows
 its long description; otherwise its short one.]
The Crowther's heading rule is listed instead of the room description heading rule in the carry out looking rulebook.
The Crowther's body text rule is listed instead of the room description body text rule in the carry out looking rulebook.

This is the Crowther's heading rule:
	if in darkness:
		begin the printing the name of a dark room activity;
		end the printing the name of a dark room activity;
	otherwise:
		if the description print count of the location is 5:
			now the description print count of the location is 0;
		if look later is true and the description print count of the location is not 0 and the short description of the location is not "":
			say "[short description of the location][line break]".

This is the Crowther's body text rule:
	if in darkness:
		begin the printing the description of a dark room activity;
		if handling the printing the description of a dark room activity:
			say "It is now pitch black. If you proceed you will likely fall into a pit.[/b]";
		end the printing the description of a dark room activity;
	otherwise if look later is false:
		say "[description of the location][line break]";
	otherwise if the location is visited:
		increase the description print count of the location by 1;
		if the description print count of the location is 1 or the short description of the location is "":
			say "[description of the location][line break]";
	otherwise:
		increase the description print count of the location by 1;
		say "[description of the location][line break]".

Part 2 - Road, building, valley

To flow is a verb.

End of Road is a room. "[We] [are] standing at the end of a road before a small brick building. Around [us] [regarding it][are] a forest. A small stream [regarding it][flow] out of the building and down a gully."
The short description is "[We]['re] at End of Road again."

The Building is east from End of Road. "[We] [are] inside a building, a well house for a large spring."
The short description is "[We]['re] inside Building."
The Building is inside from End of Road.

Some keys are in the Building. "[There] [regarding keys][are] some keys on the ground [here]."

The lamp is a device in the Building. "[There] [are] a shiny brass lamp nearby."
Understand "headlamp" as the lamp.
After switching on the lamp:
	now the lamp is lit;
	say "[Our] [lamp] [are] [now] on."
After switching off the lamp:
	now the lamp is not lit;
	say "[Our] [lamp] [are] [now] off."

[Advent 640: the food is 'ambiguously plural', which I7-lite lacks; so its
 paragraph is plain text.]
The food is in the Building. "There is food here."
The indefinite article of the food is "some".

The bottle is in the Building. "[There] [are] a [bottle] [here]."
The printed name of the bottle is "bottle of water".
Understand "water" as the bottle.

The Valley is south from End of Road. "[We] [are] in a valley in the forest beside a stream tumbling along a rocky bed."
The short description is "[We]['re] in Valley."

To splash is a verb.
The Streambed is south of the Valley. "At [our] feet all the water of the stream [regarding it][splash] into a 2 inch slit in the rock. Downstream the streambed [are] bare rock."
The short description is "[We]['re] at Slit in Streambed."
The printed name of the Streambed is "Slit in Streambed".

Part 3 - The grate

To lead is a verb.
Stream's End is south from the Streambed. "[We] [are] in a 20 foot depression floored with bare dirt. Set into the dirt [regarding it][are] a strong steel grate mounted in concrete. A dry streambed [lead] into the depression."
The short description is "[We]['re] Outside Grate."
The printed name of Stream's End is "Outside Grate".

The Entryway is a room. "[We] [are] in a small chamber beneath a 3x3 steel grate to the surface. A low crawl over cobbles [regarding it][lead] inward to the west."
The short description is "[We]['re] Below the Grate."
The printed name of the Entryway is "Below the Grate".
The Entryway is privately-named.

The grate is a door. The grate is locked and lockable. The grate is down from Stream's End and outside from the Entryway.
"[The grate] [are] [if the grate is open]open[otherwise]locked[end if]."
The keys unlock the grate.

[Advent 777-779]
After printing a parser error when the locked grate is in the location,
 pose the question "Are you trying to get into the cave? "
 with affirmative response "The grate is very solid and has a hardened steel lock. [We] [cannot enter] without a key, and there [regarding them][are] no keys nearby. I would recommend looking elsewhere for the keys."

End of Road, the Building, the Valley, the Streambed, Stream's End, the Entryway, and Cobble Crawl are lighted.

[Advent 172-180 and 736-775: Crowther's grate is opened by unlocking it and
 shut by locking it. Conley's 'kinds of action' (attempting entry,
 cave-sealing, acting ungrateful) are written here as Before rules.]
Understand the commands "open", "close" as something new.
Unlocking keylessly is an action applying to one thing.
Understand "open [something]" and "unlock [something]" as unlocking keylessly.
Locking keylessly is an action applying to one thing.
Understand "close [something]" and "lock [something]" as locking keylessly.

Before unlocking keylessly the grate when the grate is locked and the location encloses the keys:
	now the grate is open;
	now the grate is unlocked;
	say "[The grate] [are] [now] unlocked." instead.
Before unlocking the grate with something when the grate is locked and the location encloses the keys:
	now the grate is open;
	now the grate is unlocked;
	say "[The grate] [are] [now] unlocked." instead.
Before locking keylessly the grate when the grate is unlocked and the location encloses the keys:
	now the grate is closed;
	now the grate is locked;
	say "[The grate] [are] [now] locked." instead.
Before locking the grate with something when the grate is unlocked and the location encloses the keys:
	now the grate is closed;
	now the grate is locked;
	say "[The grate] [are] [now] locked." instead.
Before unlocking keylessly the grate when the grate is unlocked and the location encloses the keys:
	say "The grate was already unlocked." instead.
Before unlocking the grate with something when the grate is unlocked and the location encloses the keys:
	say "The grate was already unlocked." instead.
Before locking keylessly the grate when the grate is locked and the location encloses the keys:
	say "The grate was already locked." instead.
Before locking the grate with something when the grate is locked and the location encloses the keys:
	say "The grate was already locked." instead.
Before going down in Stream's End when the grate is locked:
	now look later is true;
	say "[We] [can't go] in through a locked steel grate!" instead.

Part 3b - The preliminary cave

[Advent 808-905, as far as the Top of Small Pit: the dwarves wake once the
 player has been in the Hall of Mists (Advent 1520), and they move at random,
 so the port stops at the top of the steps.  Left out, as the walkthrough
 never needs them: the conditional Understand lines ('Understand "crawl" as
 west when the location is Entryway'), the depressive/debrisward/pitwise
 relations, 'Inside from A is east from B', attacking the bird, and the
 parser-error question (an activity).]

Cobble Crawl is west of the Entryway. "[We] [are] crawling over cobbles in a low passage. [There] [are] a dim light at the east end of the passage."
The short description is "[We]['re] in Cobble Crawl."
Outside is the Entryway.

A small wicker cage is in the Cobble Crawl. "There [are] a small wicker cage discarded nearby."

To become is a verb. To say is a verb.
The Debris Room is inside from Cobble Crawl. "[We] [are] in a debris room, filled with stuff washed in from the surface. A low wide passage with cobbles [regarding it][become] plugged with mud and debris [here], but an awkward canyon [lead] upward and west.[paragraph break]A note on the wall [say] [']Magic word XYZZY[']."
The short description is "[We]['re] in Debris Room."
East is Cobble Crawl. Outside is nowhere.

To lie (he lies, they lie, he lay, it is lain, he is lying) is a verb.
A black rod is in the Debris Room. "A three foot [black rod] with a rusty star on an end [lie] nearby."

[Advent 783-798: XYZZY is a keyword for going between two xyzzy-linked
 rooms, a relation.  Here it is an action that moves the player the same
 way, and leaves the room description to the every turn rule, as going does.]
Xyzzying is an action applying to nothing. Understand "xyzzy" as xyzzying.
Carry out xyzzying:
	if the location is the Debris Room:
		move the player to the Building, without printing a room description;
		now look later is true;
	otherwise if the location is the Building:
		move the player to the Debris Room, without printing a room description;
		now look later is true;
	otherwise:
		say "Nothing happens."

The Awkward Canyon is west of the Debris Room. "[We] [are] in an awkward sloping east/west canyon."
Down is the Debris Room.

To exit is a verb.
The Bird Chamber is west of the Awkward Canyon. "[We] [are] in a splendid chamber thirty feet high. The [walls] [are] frozen rivers of orange stone. An awkward canyon and a good passage [exit] from east and west sides of the chamber."
The short description is "[We]['re] in Bird Chamber."
In the Bird Chamber are a scenery, privately-named, plural-named thing called walls.

A little bird is a thing in the Bird Chamber. "A cheerful [little bird] [are] sitting [here] singing."

To approach is a verb. To catch is a verb.
Check taking the little bird when the little bird is not held:
	if the player carries the rod,
		say "The bird was unafraid when [we] entered, but as [we] [approach] [it] [become] disturbed and [we] [cannot catch] it." instead;
	if the player does not carry the cage,
		say "[We] [can catch] the bird, but [we] [cannot carry] it." instead;

To end is a verb.
The Top of Small is west of the Bird Chamber. "At [our] feet [regarding it][are] a small pit breathing traces of white mist. An east passage [end] [here] except for a small crack leading on."
The short description is "[We]['re] at Top of Small Pit."
The printed name is "Top of Small Pit".

Instead of going west in the Top of Small, say "The crack [are] far too small for [us] to follow."

Some rough stone steps are an open unopenable door, below the Top of Small. "Rough stone steps [regarding steps][lead] [if the location is the Top of Small]down into the pit[otherwise]up the dome[end if]."
The Hall of Mists is west from the steps.

Part 4 - The beginning

[Advent 1676-1689: Crowther's introduction follows the banner. (Conley's
 guard 'when we must print the intro' stops a second banner, from the
 VERSION command, repeating it; this port has no VERSION command.)]
After printing the banner text:
	say "[line break]Welcome to Adventure!! Would you like instructions?[paragraph break]  ";
	if the player consents:
		say line break;
		say "Somewhere nearby is Colossal Cave, where others have found fortunes in treasure and gold, though it is rumored that some who enter are never seen again. Magic is said to work in the cave. I will be your eyes and hands. Direct me with commands of 1 or 2 words.";
		say "(Errors, suggestions, complaints to Crowther)[line break](If stuck type HELP for some hints)";
		say paragraph break;
	otherwise:
		say line break;
	say "(Type ABOUT for details about this specific Inform 7 implementation.)".
