"The Island of Despair" by K. Pillai

[An I7-lite story for zforge, after Daniel Defoe's "The Life and Strange
 Surprizing Adventures of Robinson Crusoe" (1719), which is in the public
 domain. The events follow the novel: the wreck of 30 September 1659, the
 raft, the castle, the ague, the goats and the parrot, the canoe, the
 Spanish wreck, the footprint, Friday, and the English ship of 1686.

 Acts: 1 the Wreck; 2 the Castle; 3 the Island; 4 the Footprint and
 Friday; 5 the English Ship. Build it for z8: it is too big for z5.

 Walkthrough: examples/crusoe_walkthrough.txt (spoilers).]

The story headline is "An interactive fiction after Daniel Defoe".
The story genre is "Historical".
The release number is 1.
Use scoring. The maximum score is 206.

Volume 1 - The Machinery

Part 1 - Rooms, the sea and the tide

A room can be coastal.
A room can be sheltered.
A thing can be heavy.

To decide whether the player is burdened:
    if the player carries the carpenter's chest or the player carries the sea chest or the player carries the powder barrel, decide yes;
    if the player carries the case of bottles or the player carries the roll of sailcloth, decide yes;
    if the player carries the treasure chest, decide yes;
    decide no.
A thing can be scored.

The act is a number that varies. The act is 1.
The day is a number that varies. The day is 1.
The year is a number that varies. The year is 1659.

To say the date:
    if the act is 1:
        say "[if the day is 1]the last day of September[otherwise if the day is 2]the first of October[otherwise]the [day in words] day of your landing[end if], 1659";
    otherwise:
        say "the year [year]".

The sea is a scenery thing. Understand "ocean", "waves", "wave", "surf", "breakers", "salt water" and "tide" as the sea. The description of the sea is "[sea view]".

To say sea view:
    if the location is the Landing Beach or the location is the Sand Flats or the location is the Creek Mouth:
        if the act is 1:
            say "[if low tide is true]The tide is out. The sea has drawn back across a great breadth of wet sand, and the ship sits up on her sandbank a quarter of a mile off, near enough, you think, to wade and swim to[otherwise]The tide is in. Grey water heaves over the flats, and the ship stands up out of it on her sandbank like a thing marooned[end if].";
        otherwise:
            say "The sea you came out of, so many years ago. Where the ship lay there is nothing now but the sandbank, awash at high water.";
    otherwise:
        say "[one of]The sea runs to the edge of the world on every side, empty of sails.[or]Blue and green over the shallows, deep violet beyond, and nothing on it.[or]The same sea. It has been the same sea every day.[stopping]"

When play begins:
    move the sea to the location.

Every turn when the location is coastal:
    if the sea is not in the location, move the sea to the location.

Instead of drinking the sea, say "Salt as tears. It would only make your thirst worse."
Instead of swimming when the sea is in the location and the location is not the Breakers and the location is not the Sand Flats, say "You have had enough of the sea for one lifetime, at least for today."

Part 2 - The tide

Low tide is a truth state that varies. Low tide is false.
The tide clock is a number that varies. The tide clock is 12.

Every turn when the act is 1:
    decrement the tide clock;
    if the tide clock is 0:
        now the tide clock is 12;
        if low tide is true:
            now low tide is false;
            if the location is coastal or the location is Beside the Wreck, say "The tide has turned. The sea is coming back in, fast, across the flats.";
        otherwise:
            now low tide is true;
            if the location is coastal, say "The tide is on the ebb now. The water draws back and back across the sand, and the ship's hull rises black out of the sea.".

[Rising: flowing in, towards the shore. Ebbing: flowing out.]
To decide whether the tide is flowing:
    if low tide is true, decide no;
    decide yes.

Part 3 - Days and sleep

The sleeping place is an object that varies.

Instead of sleeping:
    if the location is sheltered:
        advance the day;
    otherwise if the act is 1:
        say "Lie down here, in the open, with who knows what creatures about in the dark? Not tonight. You would sooner find some better place.";
    otherwise:
        say "You would rather sleep behind your own walls."

To advance the day:
    increment the day;
    say "You sleep[if the location is the Treetop], wedged in the fork of the tree, a short stick in your hand for defence,[end if] until the sun is high.[paragraph break]";
    now the tide clock is 12;
    now low tide is true;
    now current running is true;
    now the current clock is 10;
    morning news;
    if the act is greater than 2:
        turn the seasons;
        field morning news.

[Each act has its own news for the morning: see the parts below.]
To morning news:
    if the act is 1:
        wreck morning news;
    otherwise:
        castle morning news.

Part 4 - Score, hints and the story's verbs

To award (n - a number) for (item - a thing):
    if the item is not scored:
        now the item is scored;
        increase the score by n.

Hinting is an action applying to nothing. Understand "hint", "hints" and "help" as hinting.
Carry out hinting:
    say "[italic type][hint text][roman type]".

About-ing is an action applying to nothing. Understand "about", "credits" and "info" as about-ing.
Carry out about-ing:
    say "[bold type]The Island of Despair[roman type] is an interactive fiction after Daniel Defoe's [italic type]Robinson Crusoe[roman type] (1719). You are Robinson Crusoe of York, mariner, cast away on an island near the mouth of the great river Orinoco. Your aim is to survive, to find what treasure the sea brings you, and in the end to leave the island, not alone.[paragraph break]Type HINT when you are stuck, SCORE to see how you are doing, SLEEP to pass the night once you have somewhere safe to lie, and WRITE IN JOURNAL to keep your record. Most things can be examined, and the island rewards looking closely."

Swimming is an action applying to nothing. Understand "swim" and "wade" as swimming.
Carry out swimming:
    say "There is no water here fit to swim in."

Climbing up is an action applying to nothing. Understand "climb up" as climbing up.
Carry out climbing up: try going up.

Chopping is an action applying to one thing. Understand "chop [something]", "chop down [something]", "fell [something]", "cut down [something]" and "hew [something]" as chopping.
Check chopping:
    if the player does not carry the axe:
        say "You would need an axe for that." instead.
Carry out chopping:
    say "Your axe bites into [the noun] and you think better of it: there is no call to spoil it."

Digging is an action applying to one thing. Understand "dig [something]", "dig in [something]" and "dig up [something]" as digging.
Check digging:
    if the player does not carry the spade and the player does not carry the crow:
        say "You scrape at it with your fingers. You would need a spade, or at least an iron crow, to do any real digging." instead.
Carry out digging:
    say "You dig a little hole, and find nothing in it but more of the island."

Loading is an action applying to one thing. Understand "load [something]", "prime [something]" and "charge [something]" as loading.
Check loading:
    if the noun is not the fowling-piece and the noun is not the pistol:
        if the raft is in the Ship's Deck and the location is aboard:
            try loading the noun onto the raft instead;
        if the canoe is in the Spanish Deck and the location is the Spanish Cabin:
            try loading the noun onto the canoe instead;
        if the canoe is in the location:
            try loading the noun onto the canoe instead;
        say "That isn't something you can load." instead.

Shooting is an action applying to one thing. Understand "shoot [something]", "shoot at [something]" and "fire at [something]" as shooting.
Discharging is an action applying to nothing. Understand "shoot" and "fire" as discharging.


Writing is an action applying to nothing. Understand "write", "write journal", "write diary", "keep journal", "write in journal" and "write in diary" as writing.
Writing in is an action applying to one thing. Understand "write in [something]" and "write on [something]" as writing in.
Carry out writing in: try writing.

Praying is an action applying to nothing. Understand "pray" and "kneel" as praying.
Carry out praying:
    if the sick is true:
        say "'Lord, be my help, for I am in great distress.' It is the first prayer you have made in many years. You do not know whether it was heard.";
    otherwise:
        say "You kneel and give thanks, in your fashion, for your life and for your deliverance. It is a better habit than the ones you had at sea."

Volume 2 - The Wreck

Part 1 - The breakers and the beach

The Breakers is a room. The printed name of the Breakers is "Among the Breakers". The description of the Breakers is "The sea has you. A wave as high as a hill picked you up and flung you forward, and now you are half-swimming and half-drowning in a welter of foam, the bottom snatched away and given back as each sea goes over you. The ship is gone somewhere behind you in the spray; ahead, to the west, the land shows dark between the waves: rocks, a beach, a line of trees."
The Breakers is coastal.

Instead of going west in the Breakers, say "[breaker escape]".
Instead of swimming in the Breakers, say "[breaker escape]".
Instead of going nowhere in the Breakers, say "The only way is to the land, west, with the sea behind you driving you on."
Instead of waiting in the Breakers, say "You hold your breath while another sea buries you, and come up gasping. You cannot stay here: swim for the shore, to the west."
Instead of sleeping in the Breakers, say "Sleep here and you will sleep for ever."

To say breaker escape:
    say "You fix your eyes on the land and strike out for it. A sea takes you and dashes you against a rock with a force that beats the breath out of your body; you cling to the rock until the wave goes back, then run with the next, and the next, until you are up on the grass beyond the reach of the water, and alive.[paragraph break]";
    move the player to the Landing Beach.

The Landing Beach is a room. "[if the act is 1]You are ashore, and saved: the only one of all the ship's company. [end if]A broad beach of coarse sand shelves down eastward into the sea. [if the act is 1]Out on a sandbank, a quarter of a mile off, the ship lies on her side with her masts gone, the sea running white about her. [end if]Behind the beach, northward, stands a great thick tree, the only shelter in sight. The shore curves away southward to the mouth of a creek[if the act is 1], and east of you [tide flats][end if]."
The Landing Beach is coastal.

To say tide flats:
    if low tide is true:
        say "the ebb has left the flats bare almost to the ship";
    otherwise:
        say "the tide covers the flats"

The drowned men's things are scenery in the Landing Beach. Understand "hats", "hat", "cap", "shoes", "shoe" and "things" as the drowned men's things. The description of the drowned men's things is "Three hats, one cap, and two shoes that are not fellows: all that the sea has sent ashore of your shipmates. You never saw them afterwards, nor any sign of them. You leave the things where they lie."
Instead of taking the drowned men's things, say "You cannot bring yourself to take them. They are all that is left of eleven men."

The ship-far is scenery in the Landing Beach. The printed name of the ship-far is "ship". Understand "ship", "wreck", "hull" and "sandbank" as the ship-far when the act is 1. The description of the ship-far is "She lies on the sandbank where the storm threw her, her back broken and her masts over the side, but her hull still whole above the water. Everything you own, and a great deal besides, is aboard her[if low tide is true]. The tide is out: you could get out to her now, across the flats[end if]."

Part 2 - The great tree

The Great Tree is north of the Landing Beach. "A thick, bushy tree, something like a fir but thorny, stands alone above the beach, its lower branches almost touching the grass. Beyond it the land rises into scrub and rock, and you have no wish to go wandering in it in the dark. The beach lies south."
The Great Tree is coastal.

The thorny tree is scenery in the Great Tree. Understand "tree", "fir", "branch", "branches" and "fork" as the thorny tree. The description of the thorny tree is "A fork high in its branches would take a man's weight. You have no weapon, no light and no idea what beasts this country breeds: up there you might sleep in safety."
Instead of climbing the thorny tree, try going up.

The Treetop is up from the Great Tree. The printed name of the Treetop is "In the Tree". The description of the Treetop is "You are wedged in a fork of the thorny tree, high above the grass. Through the leaves you can see the sea, the dark hump of the ship, and nothing else in all the world. The way down is below you."
The Treetop is sheltered.

The short stick is in the Great Tree. The description of the short stick is "A short, heavy stick, cut from the thorny tree for a club. It would not stop a lion, but it is better than nothing." Understand "club" as the short stick.

Instead of going up in the Great Tree when the player does not carry the short stick, say "You would climb it, but you would like something in your hand for defence first: there is a short stick lying under the tree."

Part 3 - The flats and the ship

The Sand Flats are east of the Landing Beach. "[if low tide is true]Wet sand, ribbed by the ebb, runs out towards the ship. Pools shine here and there, and crabs go sideways out of your way. The ship lies to the east, her black side towering over the last stretch of water[otherwise]You are up to your chest in the flood, and the sea is still rising. There is no reaching the ship at high water[end if]. The beach is back to the west."
The Sand Flats are coastal.

Instead of going east in the Landing Beach when low tide is false, say "The tide is in, and the flats are under a fathom of rolling water. You will have to wait for the ebb."
Instead of going east in the Sand Flats when low tide is false, say "The water is too deep and running too strongly. Wait for the tide to go out."
Instead of swimming in the Sand Flats, try going east.

Every turn when the location is the Sand Flats and low tide is false:
    say "The flood is up to your chin. You struggle back to the beach before it lifts you off your feet.";
    move the player to the Landing Beach.

Beside the Wreck is east of the Sand Flats. "You have swum the last stretch and are treading water under the ship's side, which rises sheer and black above you: she sits so high on the sandbank that there is nothing to lay hold of. [if the hanging rope is in Beside the Wreck]A rope hangs down from the fore-chains, so low that you might reach it.[otherwise]You swim twice round her, looking for a way up.[end if] The flats and the beach are back to the west."

The hanging rope is a thing. It is fixed in place. Understand "rope" and "fore-chains" and "chains" as the hanging rope. The description of the hanging rope is "A small piece of rope hanging down by the fore-chains, so low that you wonder you did not see it at first."

The black hull is scenery in Beside the Wreck. Understand "ship", "hull", "side" and "wreck" as the black hull. The description of the black hull is "Her side goes straight up out of the water, wet and smooth. [if the hanging rope is in Beside the Wreck]A rope hangs from the fore-chains.[otherwise]If there is a way up, it is not on this side. You could swim round her.[end if]".

Searching-round is an action applying to nothing. Understand "swim round", "swim around", "circle ship" and "circle" as searching-round.
Searching-round-thing is an action applying to one thing.
Understand "swim round [something]", "swim around [something]" and "circle [something]" as searching-round-thing.
Carry out searching-round-thing: try searching-round.
Carry out searching-round:
    if the location is Beside the Wreck and the hanging rope is not in Beside the Wreck:
        now the hanging rope is in Beside the Wreck;
        say "You swim slowly round her, twice, before you see it: a small piece of rope hanging down by the fore-chains, so low that you wonder you did not see it at first.";
    otherwise:
        say "You look about you, and see nothing you have not seen already."

Instead of examining the black hull when the hanging rope is not in Beside the Wreck, try searching-round.

Instead of going up in Beside the Wreck:
    if the hanging rope is in Beside the Wreck:
        say "You catch the rope, and with great difficulty haul yourself up it, hand over hand, into the forecastle of the ship.";
        move the player to the Ship's Deck;
    otherwise:
        say "There is nothing to lay hold of. You will have to find a way."
Instead of climbing the hanging rope, try going up.
Instead of climbing the black hull, try going up.

Instead of going west in Beside the Wreck when the player is burdened, say "You could never swim ashore with a load like that. Heavy things must go by raft."

Every turn when the location is Beside the Wreck and low tide is false:
    say "The flood is coming in hard, and the current runs round her stern like a mill-race. You let it carry you back across the flats, and you crawl up the beach half drowned.";
    move the player to the Landing Beach.

Part 4 - Aboard the ship

The Ship's Deck is a room. "The ship lies so far over that you must go on hands and feet about her deck. Her masts are gone by the board, and her back is broken: there is water in her hold, but she is so high upon the sand that her stern, where the stores are, lies above it. [if the raft is in the Ship's Deck]Your raft floats alongside, below the rail, made fast with a rope. [end if][if the spars are in the Ship's Deck]Spare yards and a spare topmast lie lashed along the deck. [end if]A hatch leads down into the hold, and the great cabin is aft, to the west. You climbed aboard by the rope at the fore-chains: the way down into the sea is over the side."

The dog is in the Ship's Deck. "[if the dog is in the Ship's Deck]The dog, half starved and wild with joy to see you, comes scrambling across the deck and fawns about your feet[otherwise]Your dog is here, never far from your heels[end if]." Understand "hound" as the dog. The description of the dog is "A brown ship's dog of no particular breed, and the only other living thing aboard. He will not leave your side." 
Instead of taking the dog, say "He will follow you anywhere, and would swim after you if you left him."

The cats are scenery in the Ship's Deck. Understand "cat", "cats" and "two cats" as the cats. The description of the cats is "Two cats, who watch you from the top of the companion ladder as though the wreck were your fault."
Instead of taking the cats, say "The cats will come ashore in their own time, in some chest or other, as cats do."

The spars are in the Ship's Deck. They are fixed in place. Understand "spare yards", "yards", "yard", "topmast", "spare topmast", "timbers" and "spar" as the spars. The description of the spars is "Three or four spare yards and a spare topmast: good seasoned timber, and long. Lashed together and floored with planks, they would make a raft." 


The hatch is scenery in the Ship's Deck. Understand "hatch" and "hatchway" as the hatch. The description of the hatch is "The main hatch stands open. A ladder goes down into the darkness of the hold."

The Hold is below the Ship's Deck. "Most of the hold is under water, black and sloshing; but the after part, where the carpenter kept his stores and the stewards their provisions, is high and dry. Barrels and bales have broken loose and lie tumbled everywhere. The way up is by the ladder."

The Great Cabin is west of the Ship's Deck. "The captain's cabin, under the poop, has come through the storm better than any part of the ship. The stern windows are cracked, and sea-light moves on the bulkheads. The captain's table is still bolted to the deck, and against the side stands a locker with a drawer. A scuttle in the deck leads down to the gunroom. The door to the main deck is east."

The Gunroom is below the Great Cabin. "A low, dark space under the great cabin, smelling of tar and gunpowder. The arms rack is on the bulkhead, and the powder is kept here, in its barrels. The scuttle leads up to the cabin."


Part 5 - What the ship holds

[The essential things are heavy or light: heavy ones must come ashore by raft.]
A thing can be essential.
A thing can be cargo.

The captain's table is a supporter in the Great Cabin. It is scenery. Understand "table" as the captain's table. The description of the captain's table is "A heavy table, bolted down, stained with a thousand dinners and a few charts."

The perspective glass is on the captain's table. It is essential. Understand "telescope", "spyglass", "glass" and "spy-glass" as the perspective glass. The description of the perspective glass is "The captain's perspective glass, in a case of brass and leather. With it you could see a sail, or a man, at many miles."

The Bibles are on the captain's table. They are essential. Understand "Bible", "bible", "books", "book" and "prayer-books" as the Bibles. The description of the Bibles is "Three very good Bibles, which came to you in your cargo from England, and some Portuguese books of prayer. You have not opened a Bible in years."

The writing things are on the captain's table. The printed name of the writing things is "pen and ink". The indefinite article of the writing things is "a". Understand "pen", "ink", "paper", "journal" and "quills" as the writing things. The description of the writing things is "Pens, ink and paper, and a blank book bound in calf: enough to keep a journal of your days, while the ink lasts."

The locker is a closed openable container in the Great Cabin. It is scenery. Understand "drawer" and "drawers" as the locker. The description of the locker is "A locker of dark wood, with a drawer in it[if the locker is open], standing open[end if]."

The money is in the locker. The indefinite article of the money is "some". Understand "money", "coins", "coin", "gold", "silver", "pieces of eight" and "bag of coins" as the money. The description of the money is "About thirty-six pounds' value in money: some European coin, some Brazil, some pieces of eight, some gold and some silver.[paragraph break]'O drug!' you say aloud. 'What art thou good for? Thou art not worth to me, no, not the taking off the ground. One of those knives is worth all this heap.'"

The case of knives is in the locker. Understand "razors", "scissors" and "case" as the case of knives. The description of the case of knives is "Two or three razors, a large pair of scissors, and ten or a dozen good knives and forks."

The knife is a thing. Understand "good knife" as the knife. The description of the knife is "A good sharp knife, one of the dozen from the captain's locker."

Instead of taking the case of knives:
    if the knife is off-stage:
        now the player carries the knife;
        say "You take one good knife from the case, and leave the razors and forks where they are.";
    otherwise:
        say "One knife is all you need."

The arms rack is scenery in the Gunroom. Understand "rack" as the arms rack. The description of the arms rack is "A rack for the ship's small arms. Most of them went over the side with the boat and the men."

The fowling-piece is in the Gunroom. It is essential. Understand "gun", "fowling piece", "musket", "piece" and "firelock" as the fowling-piece. The description of the fowling-piece is "One of two very good fowling-pieces that were in the great cabin, the other having gone over the side. A long, light gun with a good lock[if the fowling-piece is loaded]. It is loaded and primed[end if]."
The pistol is in the Gunroom. It is cargo. Understand "pistols" as the pistol. The description of the pistol is "One of a brace of pistols. It throws a ball well enough at close range[if the pistol is loaded], and it is loaded[end if]."
A thing can be loaded.

The powder barrel is in the Gunroom. It is heavy, cargo and essential. Understand "powder", "gunpowder", "barrel", "barrels" and "kegs" as the powder barrel. The description of the powder barrel is "A barrel of good gunpowder[if the powder barrel is caked]. The water has caked the powder into a crust three or four inches thick on the outside, but inside it is dry and sound[end if]. It is far too heavy to swim ashore with."
A thing can be caked.

The bag of shot is in the Gunroom. It is essential. Understand "shot", "ball", "balls" and "lead" as the bag of shot. The description of the bag of shot is "A bag of small shot, with a great roll of sheet lead: enough to feed a gun for years."

The rusty cutlass is in the Gunroom. It is cargo. Understand "sword", "swords" and "cutlass" as the rusty cutlass. The description of the rusty cutlass is "One of two old rusty swords. The edge is poor, but it would cut corn, or a cord."

The carpenter's chest is a closed openable container in the Hold. It is heavy, cargo and essential. Understand "chest", "carpenter chest" and "tool chest" as the carpenter's chest. The description of the carpenter's chest is "The carpenter's chest, iron-bound and very heavy. It is worth more to you, as things stand, than a ship loaded with gold."

The axe is in the carpenter's chest. Understand "hatchet" and "axes" as the axe. The description of the axe is "A good broad axe. With this, and time, a man might build a house."
The saw is in the carpenter's chest. Understand "handsaw" as the saw. The description of the saw is "The carpenter's handsaw."
The adze is in the carpenter's chest. Understand "adz" as the adze. The description of the adze is "A carpenter's adze, for dressing timber and hollowing it."
The crow is in the carpenter's chest. Understand "crowbar", "iron crow" and "bar" as the crow. The description of the crow is "An iron crow, a great bar for levering and prising."
The bag of nails is in the carpenter's chest. Understand "nails", "spikes" and "bolts" as the bag of nails. The description of the bag of nails is "Two or three bags full of nails and spikes, and a great screw-jack."

The sea chest is a closed openable container in the Hold. It is heavy, cargo and essential. Understand "seaman chest", "seamans chest" and "provisions" as the sea chest. The description of the sea chest is "A seaman's chest, one of several, broken open and filled by you with what the rats have left of the provisions."
The provisions are in the sea chest. The printed name of the provisions is "bread and cheese". The indefinite article of the provisions is "some". Understand "bread", "cheese", "cheeses", "biscuit", "rice" and "food" as the provisions. The description of the provisions is "Bread and rice, three Dutch cheeses, five pieces of dried goat's flesh: provisions for many weeks, if you are careful."
The roll of tobacco is in the sea chest. It is essential. Understand "tobacco", "roll" and "leaves" as the roll of tobacco. The description of the roll of tobacco is "A roll of Brazil tobacco, some of it green and not yet cured."

The case of bottles is in the Hold. It is heavy, cargo and essential. Understand "bottles", "rum", "spirits", "cordial waters" and "case" as the case of bottles. The description of the case of bottles is "A case of bottles of fine cordial waters, and some five or six gallons of rack, which is rum by another name."

The roll of sailcloth is in the Hold. It is heavy, cargo and essential. Understand "sailcloth", "sails", "sail", "canvas" and "cloth" as the roll of sailcloth. The description of the roll of sailcloth is "All the spare sails of the ship, rolled and bound: enough canvas to make a tent, and a sail besides."

The coil of rope is in the Hold. Understand "rope", "cable", "cables", "hawser" and "twine" as the coil of rope when the hanging rope is not in the location. The description of the coil of rope is "A great coil of rope, and some small cordage besides."

The bag of chicken-feed is in the Hold. It is cargo. Understand "bag", "corn", "husks", "chicken feed", "chicken-feed", "feed" and "sack" as the bag of chicken-feed. The description of the bag of chicken-feed is "A little bag which had been filled with corn for the ship's fowls. The rats have been at it: there is nothing in it now but husks and dust."

A room can be aboard. The Ship's Deck, the Hold, the Great Cabin and the Gunroom are aboard.

Instead of taking a heavy thing when the location is aboard:
    say "It is far too heavy to carry up ladders and over the side in your arms. But with a rope you could sling it over onto a raft, if you had one alongside: LOAD it onto the raft, from anywhere aboard, once there is a raft."

Check taking a heavy thing when the player is burdened:
    say "You can manage only one heavy load at a time. Set down what you have first." instead.

After taking a heavy thing:
    say "You heave [the noun] up onto your shoulder, staggering."

Part 6 - The raft

The raft is a supporter. It is fixed in place. Understand "planks" as the raft. The description of the raft is "Spars lashed together at both ends, floored with short planks laid crosswise: a raft that will bear a reasonable weight, in a calm sea. [raft cargo]".

The raft load is a number that varies. The raft load is 0.

To say raft cargo:
    if the raft load is 0:
        say "It is empty.";
    otherwise:
        say "It carries [raft load in words] load[if the raft load is not 1]s[end if] of goods, of the five it will bear."


Building a raft is an action applying to nothing. Understand "build raft", "make raft", "build a raft", "make a raft" and "lash spars" as building a raft.
Check building a raft:
    if the raft is not off-stage:
        say "You have a raft already." instead;
    if the location is not the Ship's Deck:
        say "The timber for a raft is aboard the ship." instead;
    if the player does not carry the saw:
        say "The spars are too long as they are. You need to saw the topmast into lengths for the ends and the planks, and for that you need the carpenter's saw." instead;
    if the coil of rope is not in the location and the player does not carry the coil of rope:
        say "You need rope to lash the spars together. There is a great coil of it in the hold." instead.
Carry out building a raft:
    now the spars are off-stage;
    now the coil of rope is off-stage;
    now the raft is in the Ship's Deck;
    say "You throw overboard as many of the spars as you can manage for their weight, tying every one with a rope that they may not drive away. Then you go down over the side, draw them to you, and tie four of them together at both ends as well as you can. With the carpenter's saw you cut the spare topmast into three lengths, and lay short pieces of plank across them. It is a raft, and it will bear you.";
    award 3 for the raft.

Loading it onto is an action applying to two things. Understand "load [something] onto [something]", "load [something] on [something]", "lower [something] onto [something]", "lower [something] to [something]" and "sling [something] onto [something]" as loading it onto.
Instead of putting something on the raft, try loading the noun onto the raft.

Check loading something onto something:
    if the second noun is the canoe:
        if the canoe is not in the Spanish Deck and the canoe is not in the location, say "Your canoe is not here." instead;
        if the noun is not the treasure chest, say "You can carry [the noun] yourself." instead;
        now the noun is on the canoe;
        say "With the rope, and a great deal of heaving, you get [the noun] up out of the cabin and down into the canoe. She settles, but she swims." instead;
    if the second noun is not the raft:
        try putting the noun on the second noun instead;
    if the raft is not in the Ship's Deck and the raft is not in the location:
        say "There is no raft here." instead;
    if the raft load is 5:
        say "The raft is laden to the water already. Any more and she will swamp." instead;
    if the noun is the raft:
        say "That would be something to see." instead;
    if the noun is not cargo:
        say "You can carry [the noun] yourself. The raft is for the heavy goods." instead.
Carry out loading something onto something:
    now the noun is on the raft;
    increment the raft load;
    say "[if the noun is heavy]With a rope and a good deal of heaving you get [the noun] up and over the side and down onto the raft[otherwise]You set [the noun] on the raft[end if]."

First carry out taking something when the noun is on the raft:
    decrement the raft load.

Instead of going east in the Ship's Deck:
    say "You go over the side at the fore-chains and let yourself down the rope into the sea.";
    move the player to Beside the Wreck.
Instead of exiting in the Ship's Deck, try going east.

Part 7 - Launching the raft

Launching is an action applying to one thing. Understand "launch [something]", "paddle [something]", "sail [something]", "row [something]", "steer [something]" and "board [something]" as launching.
Pushing off is an action applying to nothing. Understand "push off", "cast off", "shove off", "set sail" and "launch" as pushing off.
Carry out pushing off:
    if the raft is in the location:
        try launching the raft;
    otherwise if the location is aboard and the raft is in the Ship's Deck:
        try launching the raft;
    otherwise if the canoe is in the location:
        try launching the canoe;
    otherwise:
        say "You have nothing here to launch."

Check launching:
    if the noun is the raft and the raft is not in the location:
        if the location is aboard and the raft is in the Ship's Deck:
            if the location is not the Ship's Deck:
                say "(first going up on deck)[line break]";
                move the player to the Ship's Deck, without printing a room description;
        otherwise:
            say "Your raft is not here." instead.

The trips is a number that varies. The trips is 0.
Wreck gone is a truth state that varies. Wreck gone is false.

Carry out launching the raft:
    if the location is the Ship's Deck:
        if low tide is true:
            say "The tide is on the ebb, and running out hard past the ship's stern. Push off now, and it will carry you straight out to sea. Push off anyway? ";
            if the player consents:
                end the story saying "The ebb takes the raft and you out past the sandbank into the open sea. You are never seen again.";
            otherwise:
                say "You wait on deck for the flood.";
            stop the action;
        say "You go down onto the raft, cast off, and push away from the ship. The flood tide takes you, slowly at first, then faster, towards the shore. A little way along you see an opening in the land, and a strong current setting into it: a creek. You steer for it with a broken oar[if the raft load is at least 3], and once the raft grounds at one end on a shoal and all your cargo slides towards the water; you hold the chests up with your back for half an hour before the rising tide sets her afloat again[end if], and at last you bring her in against the bank and moor her there, with an oar driven into the ground at each end.";
        move the raft to the Creek Mouth;
        if the dog is in the Ship's Deck:
            move the dog to the Creek Mouth;
            say "[paragraph break]The dog, rather than be left, jumps into the sea and swims after you, and is ashore before you are.";
        increment the trips;
        land the cargo;
        move the player to the Creek Mouth;
        if the trips is 2:
            say "The wind has been rising all afternoon, and the sky to seaward has gone the colour of lead. You do not like the look of it. If there is anything else you must have from the ship, you had better think hard about what.";
    otherwise:
        if wreck gone is true:
            say "There is no ship to go out to any more." instead;
        if low tide is false:
            say "The flood is running up the creek, and only presses the raft harder against the bank. You must wait for the ebb to carry you out." instead;
        say "You push off into the ebb, and it carries the raft down the creek and out across the flats, straight to the ship. You make her fast under the fore-chains and climb aboard by the rope.";
        move the raft to the Ship's Deck;
        move the player to the Ship's Deck.

To land the cargo:
    say "[paragraph break]You heave your goods up onto the bank, one after another, until the raft rides empty.";
    now the raft load is 0;
    if the carpenter's chest is on the raft, award 5 for the carpenter's chest;
    if the powder barrel is on the raft, award 3 for the powder barrel;
    if the sea chest is on the raft, award 2 for the sea chest;
    if the roll of sailcloth is on the raft, award 2 for the roll of sailcloth;
    if the case of bottles is on the raft, award 1 for the case of bottles;
    land the carpenter's chest;
    land the sea chest;
    land the powder barrel;
    land the case of bottles;
    land the roll of sailcloth;
    land the bag of chicken-feed;
    land the pistol;
    land the rusty cutlass.

To land (item - a thing):
    if the item is on the raft, move the item to the Creek Mouth.

The Creek Mouth is south of the Landing Beach. "A little creek runs into the land here between low banks of reeds and mud, with a strong tide setting in and out of it. [if the raft is in the Creek Mouth]Your raft is moored against the bank. [end if]The beach is north, and the bank of the creek runs inland to the west."
The Creek Mouth is coastal.

The reeds are scenery in the Creek Mouth. Understand "bank", "mud" and "creek" as the reeds. The description of the reeds is "Reeds, mud and the brown water of the creek, rising and falling with the tide."

To decide whether the dog can follow:
    if the location is aboard or the location is Beside the Wreck or the location is the Sand Flats or the location is the Treetop, decide no;
    if the location is Cove Waters or the location is the Spanish Deck or the location is the Spanish Cabin, decide no;
    if the location is Inside the Stockade or the location is the Cave, decide no;
    decide yes.

To decide whether a companion can follow:
    if the location is aboard or the location is Cove Waters or the location is the Spanish Deck or the location is the Spanish Cabin, decide no;
    decide yes.

Every turn when the dog is on-stage and the dog is not in the location and the dog is not in the Ship's Deck and the dog can follow:
    move the dog to the location.

Part 8 - The storm

To wreck morning news:
    if the day is 2:
        say "When you wake the weather is clear and the storm abated, so that the sea no longer rages as before. You see, to your great surprise, that the ship has been lifted off the sand in the night by the swelling of the tide, and driven up almost as far as the rock where you were dashed. She stands upright still, a quarter of a mile off. You wish yourself on board, to save at least some necessary things for your use.";
    otherwise if the trips is at least 2 and wreck gone is false:
        break up the ship;
    otherwise if the day is at least 5 and wreck gone is false:
        break up the ship;
    otherwise:
        say "The ship still lies on her sandbank, and the weather holds."

To break up the ship:
    now wreck gone is true;
    now the act is 2;
    now low tide is false;
    say "All night it blows very hard, a storm to set the teeth on edge. In the morning, when you look out, behold, no more ship is to be seen. She has gone to pieces on the bank in the night.[paragraph break]You are a little surprised, but recover yourself with the satisfying thought that you have lost no time, nor abated no diligence, to get everything out of her that could be useful to you.";
    if the Ship's Deck encloses the money or the Great Cabin encloses the money:
        now the money is off-stage;
    wash ashore the carpenter's chest;
    wash ashore the sea chest;
    wash ashore the powder barrel;
    wash ashore the case of bottles;
    wash ashore the roll of sailcloth;
    wash ashore the fowling-piece;
    wash ashore the bag of shot;
    wash ashore the Bibles;
    wash ashore the perspective glass;
    wash ashore the roll of tobacco;
    if the Ship's Deck encloses the raft or the raft is in the Ship's Deck:
        now the raft is off-stage;
    now the spars are off-stage;
    now the hanging rope is off-stage.

To wash ashore (item - a thing):
    if the Ship's Deck encloses the item or the Hold encloses the item or the Great Cabin encloses the item or the Gunroom encloses the item:
        move the item to the Landing Beach;
        if the item is the powder barrel, now the powder barrel is caked;
        if the washed up is false:
            now the washed up is true;
            say "[paragraph break]Down on the beach you can see things the sea has cast up from the wreck.".

The washed up is a truth state that varies. The washed up is false.

Part 9 - Placeholders for later acts

The treasure chest is a thing. It is heavy.
The spade is a thing.

To say hint text:
    if the act is 1:
        if the day is 1:
            say "Get out of the sea (go west). Night is coming: find somewhere safe to sleep, off the ground.";
        otherwise if the raft is off-stage:
            say "The ship holds everything you need. At low tide you can wade and swim out to her across the flats (east of the beach). Look closely at her side for a way up. Aboard, you will need a raft for the heavy goods: the carpenter's chest has the tools.";
        otherwise:
            say "Load the raft with what matters most: tools, powder, the gun, food, canvas, and the rum. Push off on the flood tide, which carries you into the creek; the ebb takes you back out to the ship. Do not push off from the ship on the ebb.";
    otherwise if the act is 2:
        if the tent pitched is false:
            say "Your goods are on the creek bank. Find a safe place to live: west of the creek there is a plain against a steep hill. Carry the sailcloth there (heavy things one at a time) and PITCH TENT, with the axe in hand.";
        otherwise if the stockade built is false:
            say "BUILD STOCKADE before the tent. You need the axe.";
        otherwise if the ladder is off-stage:
            say "A stockade with no gate needs a ladder: MAKE LADDER.";
        otherwise if the cave dug is false:
            say "Carry your goods inside, especially the powder and the rum and the sea chest. Then DIG CAVE behind the tent with the iron crow. A post to count the days (CARVE POST) and a journal (WRITE) would not be amiss.";
        otherwise if the quake done is false:
            say "Something is coming. Keep out of the cave when the ground grumbles.";
        otherwise if the rains done is false:
            say "Rain is coming. Is your powder under cover? Sleep, and see.";
        otherwise if the sick is true:
            say "The Brazilians cure almost everything with tobacco: it is in the sea chest. Steep some in the rum (PUT TOBACCO IN BOTTLES), look for comfort in a Bible (READ BIBLE), and drink the dose.";
        otherwise:
            say "Sleep, and let the year turn.";
    otherwise if the act is 3:
        if the canoe is off-stage:
            say "Explore up the creek and north along the brook. Everything you make matters: a spade of ironwood (in the thicket) digs clay; a pot, fired, carries water; grapes dried are food. A boat must be built where the water can reach it: remember the great cedar.";
        otherwise if the canoe trips is 0:
            say "Take your canoe out (LAUNCH CANOE at the southern cove, with a paddle) and come back, and sleep. Something may happen at sea.";
        otherwise if the treasure chest is not scored:
            say "The Spanish wreck lies east, past the rocky point. Watch the current from the point: it slackens with the turn. Take food (raisins or bread) and a fired pot of water. LOAD the chest into the canoe from the Spanish cabin.";
        otherwise:
            say "Carry the chest home. Sleep. Then go down to the southern cove again. While the years go by, there is much to do: dig and fence the ground east of the savannas and sow barley in the rainy season (grind only what you need: keep seed); MILK GOATS when your flock has grown, and MAKE CHEESE; MAKE LAMP (tallow, oakum from the carpenter's chest, clay) and LIGHT it, and see what lies deep in the cavern.";
    otherwise if the act is 4:
        if the Friday rescued is false:
            say "Watch for them from the hilltop above your castle: LOOK THROUGH GLASS, with your gun loaded. If one runs, be at the creek before him. Do not go near their shore.";
        otherwise if Friday is not named:
            say "NAME HIM FRIDAY.";
        otherwise if Friday is not clothed or Friday is not taught or the second landing is false:
            say "Friday wants burying of the dead (BURY BODIES), clothes (the Spanish shirts), and teaching (TEACH FRIDAY). Then sleep.";
        otherwise if the landing active is true:
            say "LOAD GUN and LOAD PISTOL, and GIVE PISTOL TO FRIDAY. Go through the thicket to the edge of the wood (west of the thicket) and SHOOT SAVAGES from behind the bush. Do not walk out onto their shore.";
        otherwise if the Spaniard is not scored or the old man is not scored:
            say "Down on the shore: FREE SPANIARD and FREE OLD MAN, with your knife.";
        otherwise if the Spaniard is not revived or the old man is not revived:
            say "They are faint with hunger: give them the barley loaf, raisins, cheese, or the flask of rum from your sea chest.";
        otherwise if the barrow-marker is not scored:
            say "MAKE BARROW with your axe, and carry them home.";
        otherwise if the hut is off-stage:
            say "BUILD HUT for them on the plain: your axe, and straw from a harvest.";
        otherwise if the plan known is false:
            say "TALK TO SPANIARD.";
        otherwise if the boat mast is false or the boat sail is false or the boat rudder is false:
            say "Build a great boat with Friday up the creek: CHOP the creek cedar (axe), HOLLOW LOG (adze), MAKE MAST (axe), MAKE SAIL (the old sails in your cave), MAKE RUDDER (saw), and DIG DOCK (spade).";
        otherwise if the baskets of grain are off-stage:
            say "Corn enough for all: a harvest from your barley field, carried in a basket.";
        otherwise:
            say "SEND SPANIARD, from the plain.";
    otherwise:
        if the mutiny phase is 0:
            say "Friday saw a sail. Go up the hill and LOOK THROUGH GLASS.";
        otherwise if the mutiny phase is 1:
            say "Wait, out of sight, for the heat of the day. They will sleep.";
        otherwise if the mutiny phase is 2:
            say "The prisoners are under the great tree, north of the landing beach. Talk to them, and FREE CAPTAIN.";
        otherwise if the mutiny phase is 3:
            say "With your gun loaded, take the captain to the sleeping seamen along the brook, and SHOOT MUTINEERS.";
        otherwise if the mutiny phase is 4:
            say "Make sure the seamen cannot get back to the ship: BREAK LONGBOAT with the axe.";
        otherwise if the mutiny phase is 5:
            say "Wait. The ship will send another boat.";
        otherwise if the mutiny phase is 6:
            say "Lead them astray in the woods: go inland with Friday and HALLOO.";
        otherwise if the mutiny phase is 7:
            say "At the creek mouth, RETAKE SHIP.";
        otherwise:
            say "Bring Friday and the Spanish chest (and Poll, and your umbrella and cap) to the creek mouth, and BOARD SHIP.";

Volume 3 - The Castle

Part 1 - The way inland

Up the Creek is west of the Creek Mouth. "The creek narrows between higher banks, overhung with bushes, and turns north into the island. Westward the ground rises in a long green slope towards a hill whose face is steep as a house-side. The creek mouth is back to the east[if the act is at least 3], and a path you have worn follows the creek north, inland[end if]."

Instead of going north in Up the Creek when the act is less than 3, say "The creek winds away inland into thick country. You would rather make yourself safe before you go exploring: a place to sleep, a wall about you, your goods under cover."

The Hillside Plain is west of Up the Creek. "[if the stockade built is true]Before the hill stands your castle: a half-circle of strong stakes, driven close and doubled, higher than a man, with no gate in it anywhere[if the ladder is in the Hillside Plain]; your ladder leans against the stakes[end if]. Inside it, you know, is your tent, and behind the tent the rock[otherwise]A little plain, a hundred yards broad, lies on the side of the rising hill, and the hill's face towards it is steep as a house-side, so that nothing can come down on you from the top. In the face of the rock is a hollow place, worn a little way in, like the entrance or door of a cave. It is a good place: shade in the heat of the day, the sea in view, fresh water not far off[end if]. Above you, a track goes up to the top of the hill; the slope runs down to the creek, eastward."
The Hillside Plain is coastal.

The hollow in the rock is scenery in the Hillside Plain. Understand "hollow", "rock", "face", "hill", "door", "cave" and "entrance" as the hollow in the rock. The description of the hollow in the rock is "A hollow place in the rock, like the door of a cave, though there is no real cave behind it. The rock is soft enough, you think, that with tools a man might dig into it."

The Hilltop is up from the Hillside Plain. "From the top of the hill you can see the sea on every side: you are on an island, and no other land in sight but some rocks a great way off, and two small islands, less than this, about three leagues to the west[if the act is at least 3]. To the west and south, when the air is very clear, a long low shadow lies on the edge of the sea: the main land, you suppose, of America[end if]. There is no sign of man anywhere. The track goes down to the plain."
The Hilltop is coastal.

Part 2 - The tent, the stockade, the ladder

The stockade built is a truth state that varies.
The tent pitched is a truth state that varies.
The cave dug is a truth state that varies.

Inside the Stockade is a room. "Within the half-circle of stakes, against the face of the rock, stands your tent: the ship's sails, doubled, over a ridge-pole, with a tarpaulin spread above them against the rain. [if the cave dug is true]Behind the tent, the hollow in the rock has become a real cave, dug deep into the hill, where your stores are kept. [otherwise]Behind the tent is the hollow in the rock. [end if][if the calendar post is in Inside the Stockade]Your calendar post stands by the fence. [end if]The ladder is the only way out, over the stakes to the east."
Inside the Stockade is sheltered.

The tent is scenery in Inside the Stockade. Understand "sails", "tarpaulin" and "hammock" as the tent. The description of the tent is "A good tent of the ship's sails, with your hammock slung inside it and the powder and the tools about you, so that you may have them at hand in the night."

The inner hollow is scenery in Inside the Stockade. Understand "hollow", "rock", "face" and "hill" as the inner hollow. The description of the inner hollow is "[if the cave dug is true]The cave runs back into the hill, west of the tent.[otherwise]The hollow in the rock, a few feet deep. With a crow to break the rock, you could make a cave of it: DIG CAVE.[end if]".

Instead of going west in the Hillside Plain:
    if the stockade built is false:
        say "There is nothing there yet but the hollow in the rock." instead;
    if the ladder is not in the Hillside Plain:
        say "There is no gate in your stockade, by your own design. The only way in is over the top, by a ladder, and you have not yet made one." instead;
    say "You go up the ladder, over the stakes, and draw the ladder in after you.";
    move the player to Inside the Stockade.
Instead of climbing the ladder when the location is the Hillside Plain, try going west.
Instead of entering the stockade-outside, try going west.

The stockade-outside is scenery. The printed name of the stockade-outside is "stockade". Understand "stockade", "stakes", "fence", "castle" and "wall" as the stockade-outside. The description of the stockade-outside is "Two rows of strong stakes, driven into the ground till they stand firm like piles, the tops sharpened, and the whole higher than your head. It cost you many days of labour, and nothing on two legs or four will come over it without a ladder."

Instead of going east in Inside the Stockade:
    say "You set the ladder against the stakes, go up and over, and draw it down after you.";
    move the player to the Hillside Plain.
Instead of exiting in Inside the Stockade, try going east.

The ladder is a thing. It is scenery. The description of the ladder is "A rough ladder of two poles and rungs lashed across them. When it is drawn in after you, nothing can follow."

Pitching the tent is an action applying to nothing. Understand "pitch tent", "make tent", "build tent", "erect tent", "put up tent" and "pitch the tent" as pitching the tent.
Check pitching the tent:
    if the tent pitched is true, say "Your tent is pitched already." instead;
    if the location is not the Hillside Plain, say "You have your eye on a better place than this: the plain on the hillside, west of the creek, with the hollow in the rock." instead;
    if the roll of sailcloth is not in the location and the player does not carry the roll of sailcloth, say "You need the sailcloth from the ship, here, to make a tent." instead;
    if the player does not carry the axe, say "You need the axe to cut poles for it." instead.
Carry out pitching the tent:
    now the tent pitched is true;
    now the roll of sailcloth is off-stage;
    say "You cut poles in the thicket, and before the hollow in the rock you pitch a tent of the ship's sails, doubled, with a tarpaulin over the top against the rains that you fear will come. Under it you sling your hammock. It is the first night's lodging you have had that you could call a house.";
    award 3 for the tent.

Building the stockade is an action applying to nothing. Understand "build stockade", "make stockade", "build fence", "make fence", "build palisade", "build wall" and "drive stakes" as building the stockade.
Check building the stockade:
    if the stockade built is true, say "The stockade is built." instead;
    if the location is not the Hillside Plain, say "The place for a fortification is the hillside plain, before the hollow in the rock." instead;
    if the tent pitched is false, say "First you want a roof over your head: pitch a tent here." instead;
    if the player does not carry the axe, say "You would need the axe to cut the stakes." instead.
Carry out building the stockade:
    now the stockade built is true;
    move the stockade-outside to the Hillside Plain;
    say "Before the tent you draw a half-circle, ten yards from the rock, and in it you drive two rows of strong stakes, cut in the woods and sharpened at the top, standing like piles, five and a half feet out of the ground. Then you lay pieces of cable from the ship between the rows, and more stakes inside to lean against them. It takes you many days: the cutting, the carrying and the driving. When it is done there is no gate in it anywhere.";
    increase the day by 3;
    award 4 for the stockade-outside.

Making the ladder is an action applying to nothing. Understand "make ladder", "build ladder" and "carve ladder" as making the ladder.
Check making the ladder:
    if the ladder is not off-stage, say "You have a ladder already." instead;
    if the stockade built is false, say "What would you want with a ladder, with no wall to climb?" instead;
    if the player does not carry the axe and the player does not carry the saw, say "You need a saw or an axe." instead.
Carry out making the ladder:
    move the ladder to the Hillside Plain;
    say "You cut two long poles and lash short rungs across them with cordage from the ship. It is a poor sort of ladder, but it will take you over the stakes; and once you are inside, you draw it in after you, and you are as safe as in a castle.";
    award 2 for the ladder.

Part 3 - The cave

The Cave is west of Inside the Stockade. "A cave dug with your own hands into the soft rock of the hill, with a rough arch of timber at its mouth. It is dry and cool, and here you keep your powder and your stores, safe from the rain and from the lightning you so much fear. The way out, east, is into the stockade."

Instead of going west in Inside the Stockade when the cave dug is false, say "There is only the shallow hollow in the rock behind the tent. You could DIG CAVE, with the right tools."

Digging the cave is an action applying to nothing. Understand "dig cave", "dig hollow", "dig rock" and "enlarge hollow" as digging the cave.
Instead of digging the inner hollow, try digging the cave.
Instead of digging the hollow in the rock, try digging the cave.
Check digging the cave:
    if the cave dug is true, say "Your cave is as big as you need, for now." instead;
    if the location is the Hillside Plain and the stockade built is false, say "First make yourself safe here: a tent, and a fortification before it. Then dig." instead;
    if the location is not Inside the Stockade, say "The place to dig is the hollow in the rock behind your tent, inside the stockade." instead;
    if the player does not carry the crow and the player does not carry the spade, say "The rock is soft, but not that soft. You need the iron crow from the carpenter's chest." instead.
Carry out digging the cave:
    now the cave dug is true;
    now the quake clock is 0;
    say "With the iron crow you break into the soft rock behind your tent, and carry the earth and stones out through the tent and lay them against the stakes, so that the ground inside rises a foot and a half. Day after day you work at it, until the hollow is a real cave, running a good way back into the hill: a cellar for your house.";
    increase the day by 2;
    award 4 for the cave-marker.

The cave-marker is a thing.

Part 4 - The calendar post and the journal

The calendar post is a thing. It is fixed in place. Understand "post", "calendar", "cross", "notches" and "notch" as the calendar post. The description of the calendar post is "A great square post, carved with your knife in capital letters: I CAME ON SHORE HERE ON THE 30TH OF SEPT. 1659. Down its sides you cut a notch every day, every seventh notch as long again, and every first of the month as long again as that. There are [if the act is 1]a few[otherwise if the act is 2]dozens of[otherwise]thousands of[end if] notches on it now."

Carving the post is an action applying to nothing. Understand "carve post", "make post", "make calendar", "carve calendar", "make cross" and "cut post" as carving the post.
Check carving the post:
    if the calendar post is not off-stage, say "You have your calendar post already. You cut a notch in it for today." instead;
    if the player does not carry the knife and the player does not carry the axe, say "You need a knife to carve it with, and an axe to cut the post." instead.
Carry out carving the post:
    move the calendar post to the location;
    say "You fear you will lose your reckoning of time for want of books and pen and ink, and even forget the Sabbath days from the working days. So you cut a great square post, set it up in the ground, and carve upon it with your knife, in capital letters: I CAME ON SHORE HERE ON THE 30TH OF SEPT. 1659. You will cut a notch in it every day.";
    award 2 for the calendar post.

Notching is an action applying to nothing. Understand "notch post", "cut notch" and "mark post" as notching.
Carry out notching:
    if the calendar post is in the location:
        say "You cut the day's notch into the post: day [day] on the island, by your reckoning.";
    otherwise:
        say "Your calendar post is not here."

The journal written is a truth state that varies.

Carry out writing:
    if the player does not carry the writing things:
        say "You have nothing to write with." instead;
    if the journal written is false:
        now the journal written is true;
        say "You open the calf-bound book, dip your pen, and begin:[paragraph break][italic type]September 30, 1659. I, poor miserable Robinson Crusoe, being shipwrecked, during a dreadful storm, in the offing, came on shore on this dismal unfortunate island, which I called the Island of Despair; all the rest of the ship's company being drowned, and myself almost dead.[roman type][paragraph break]You go on to set down the good and the evil of your case, like debtor and creditor: you are cast upon a horrible desolate island, but you are alive; you are divided from mankind, but not starved; you have no clothes, but you are in a hot climate where you could hardly wear them. Written out, it is a little easier to bear.";
        award 2 for the writing things;
    otherwise:
        say "You write up the journal: [journal line]"

To say journal line:
    if the act is 1:
        say "the ship, the raft, and what you have got out of her.";
    otherwise if the act is 2:
        say "[if the sick is true]'The ague again, violently. I am very sick, and frighted with the thoughts of my condition.' Your hand shakes so that you can barely read it.[otherwise]the stockade, the cave, the day's labour, and the weather.[end if]";
    otherwise if the act is 3:
        say "the day's work, the goats, the corn, and your walks about the island.";
    otherwise if the act is 4:
        say "'I saw the print of a man's naked foot on the shore.' You find you have written nothing else all day.";
    otherwise:
        say "Friday, and the day's doings. Your ink is almost gone, and you water it thinner every year."

Part 5 - The earthquake, the rains, and the ague

The quake clock is a number that varies. The quake clock is 0.
The quake done is a truth state that varies.
The rains done is a truth state that varies.
The sick is a truth state that varies.
The ague count is a number that varies.
The cured is a truth state that varies.
The bible read is a truth state that varies.
The dose made is a truth state that varies.
The feed shaken is a truth state that varies.
The barley stage is a number that varies.
A thing can be spoiled.

Every turn when the cave dug is true and the quake done is false:
    increment the quake clock;
    if the quake clock is 7:
        say "[paragraph break]A strange low rumbling comes out of the ground, like thunder under your feet, and a little earth trickles from [if the location is the Cave]the roof of the cave[otherwise]the rock[end if].";
    if the quake clock is 8:
        now the quake done is true;
        if the location is the Cave:
            end the story saying "The whole roof of the cave comes down upon you, and the hill with it.";
        otherwise:
            say "[paragraph break]The earth shakes under you. Three times it heaves, with such violence that the stakes of the stockade lean and the sea itself foams and boils. A great piece of the rock falls from the hillside with a noise such as you never heard in your life; the cave's mouth [if the location is Inside the Stockade]behind your tent [end if]is choked with earth. You stand like one dead or stupefied. Then the wind rises and the clouds gather: rain is coming.";
            award 2 for the quake-marker.

The quake-marker is a thing.

To castle morning news:
    if the act is 4 and the Spaniard sailed is true:
        begin the fifth act;
        stop;
    if the act is 4 and the second landing is false and Friday is taught and Friday is clothed:
        start the second landing;
        stop;
    if the quake done is true and the rains done is false:
        now the rains done is true;
        say "All night and all the next day the rain falls as if the sky had split. When at last it slackens you go about your things to see what is saved.[paragraph break]";
        if the powder barrel is in the Cave or the powder barrel is in Inside the Stockade:
            say "The powder, under cover, is dry.";
            award 3 for the powder-marker;
        otherwise:
            now the powder barrel is spoiled;
            say "The powder barrel, which you left out in the weather, is soaked through. The powder in it is spoilt: black paste.";
        if the feed shaken is true:
            now the barley stage is 1;
        say "[paragraph break]You clear the fallen earth from the cave's mouth; the cave is sound behind it. But you feel strangely cold, and your head aches.";
        stop;
    if the rains done is true and the sick is false and the cured is false:
        now the sick is true;
        now the ague count is 0;
        say "In the night you are taken with a violent ague: shaking and cold, and then a fierce heat, and a headache that will not let you lie. You are very ill, and have no one to help you. In your fever you dream of a man descending in a flame of fire, who says: 'Seeing all these things have not brought thee to repentance, now thou shalt die.'[paragraph break]You remember that the Brazilians take no physic but their tobacco for almost all distempers, and that there is a roll of it in one of the chests.";
        stop;
    if the cured is true and the act is 2:
        begin the third act;
        stop;
    if the act is 3 and the canoe trips is at least 1 and the Spanish wreck seen is false:
        now the Spanish wreck seen is true;
        now the year is 1664;
        say "In the night there is a storm, and in the thick of it you hear, or think you hear, a gun fired at sea: then another, and another, at about half a minute's distance. In the morning, from the rocky point, you see it: a ship, cast away in the night upon the rocks beyond the point to the south-east, her masts gone, and no boat and no man anywhere. If there is anyone left alive on board, or anything, you must go out to her in your canoe.";
        stop;
    if the barley stage is 1:
        now the barley stage is 2;
        say "By the rock where you shook out the old chicken-feed, some stalks are shooting up out of the ground: green, and then with ears on them. It is barley, perfect English barley, and a little rice. You are astonished. It seems to you a miracle, until you remember the bag.";
        move the green barley to the feed spot;
        stop;
    say "[one of]The sun comes up over the sea, as it always does.[or]Another day. You cut its notch in your mind, if not in your post.[or]A fine morning, hot already by the time you are up.[or]The dew is heavy on everything. The island is very quiet.[at random]"

The feed spot is a room that varies. The feed spot is the Hillside Plain.

Every turn when the sick is true:
    increment the ague count;
    if the ague count is 15:
        say "[paragraph break]The fever comes back upon you, and you must sit down until the shaking passes.";
    if the ague count is 35:
        say "[paragraph break]You are weaker. You must find something for this ague, and soon: tobacco, in the sea chest, and the rum, and perhaps the Book.";
    if the ague count is 55:
        say "[paragraph break]You can scarcely stand. If you are not cured very soon you will not live.";
    if the ague count is 65:
        end the story saying "The ague takes you at last, alone on your island, with no one to close your eyes.".

Instead of eating the roll of tobacco:
    if the sick is true:
        say "You chew a leaf of the tobacco. It is green and strong; it stupefies your brain, and you feel a little easier, but only a little.";
    otherwise:
        say "You chew a leaf. It is foul, and does you no good at all."

Eating is an action applying to one thing. Understand "eat [something]", "chew [something]" and "taste [something]" as eating.
Carry out eating:
    say "That's plainly inedible."
Instead of eating the provisions:
    say "You eat a little bread and a piece of cheese, and put the rest back. It must last."
Understand "steep [something] in [something]" as inserting it into.

Instead of inserting the roll of tobacco into the case of bottles:
    if the dose made is true:
        say "Your dose is made already." instead;
    now the dose made is true;
    say "You take some of the tobacco, and steep it an hour or two in a bottle of rum, meaning to take it as a dose when you lie down. The smell of it alone makes your eyes water."

Instead of examining the Bibles when the sick is true and the bible read is false:
    now the bible read is true;
    say "You take down one of the Bibles, and open it at random. The first words that come into your eyes are these: [italic type]Call on me in the day of trouble, and I will deliver thee, and thou shalt glorify me.[roman type][paragraph break]The words are very apt to your case, and make some impression upon your thoughts. You lay the book down and, for the first time in your life, pray.";
    award 3 for the Bibles.
Instead of examining the Bibles when the sick is false:
    say "Three very good Bibles, and some prayer books. [if the bible read is true]You read in one of them every morning now, and every night. [end if]It is strange how the words, that meant nothing to you at sea, seem written for your case."

Instead of drinking the case of bottles:
    if the sick is true and the dose made is true:
        if the bible read is false:
            say "You lift the bottle, then set it down again. Your hands shake so. You feel you ought first to look for some comfort that is not in a bottle: in one of the Bibles, perhaps." instead;
        now the sick is false;
        now the cured is true;
        say "You drink the rum with the tobacco steeped in it, which is so strong and rank you can hardly get it down. It flies up into your head, and you fall into a sound sleep, and do not wake till, as you judge by the sun, three o'clock the next afternoon; nay, you think afterwards that you slept all the next day and night, and lost a day in your reckoning.[paragraph break]When you wake you find yourself exceedingly refreshed, and your spirits lively and cheerful. The fit is gone, and does not come again. You go on your knees, and give God thanks for your recovery.";
        increase the day by 2;
        award 5 for the cure-marker;
    otherwise if the sick is true:
        say "The rum alone only makes your head swim. The Brazilians, you remember, take tobacco for almost every distemper.";
    otherwise:
        say "A dram of rum warms you. You are careful with it: there is not much, and no more to be had."

The cure-marker is a thing.
The powder-marker is a thing.

Shaking is an action applying to one thing. Understand "shake [something]", "empty [something]", "shake out [something]" and "scatter [something]" as shaking.
Carry out shaking:
    say "Nothing comes out of [the noun]."
Instead of shaking the earthen pot, try emptying the earthen pot.
Instead of shaking the bag of chicken-feed:
    if the feed shaken is true:
        say "The bag is empty." instead;
    now the feed shaken is true;
    now the feed spot is the location;
    say "You want the bag for something else, so you shake the husks of corn out of it, on one side of your fortification, under the rock, and think no more of it.";
    if the rains done is true:
        now the feed shaken is false;
        say "[paragraph break](A pity: the rains are over, and the seed has fallen on dry ground. The birds have it before evening.)"

The green barley is a thing. It is fixed in place. The indefinite article of the green barley is "some". Understand "barley", "rice", "stalks", "ears", "corn" and "shoots" as the green barley. The description of the green barley is "Ten or twelve ears of barley, of the same kind as the English, and some twenty or thirty stalks of rice: the chicken-feed you shook out, sprung up in the rains[if the act is at least 3]. It is ripe now: you could reap it[end if]."

Volume 4 - The Island

Part 1 - The second year

To begin the third act:
    now the act is 3;
    now the year is 1660;
    now the provisions are off-stage;
    if the barley stage is at least 1:
        now the barley stage is 3;
        move the green barley to the feed spot;
    say "[bold type]The Thirtieth of September, 1660[roman type][paragraph break]The rains end. You are well again, and stronger than before; and counting the notches on your post, you find that you have been ashore a full year. You keep the day as a solemn fast, and give thanks for the many wonderful mercies which your solitary condition has been attended with.[paragraph break]The last of the ship's bread went long ago. From now on you must live by the island. And you resolve, now that you are safe behind your walls, to go abroad and see what it holds: up the creek, northward, into the country.[if the barley stage is 3][paragraph break]And by the rock where you shook out the old chicken-feed, something is growing: green stalks with ears on them. It is barley, perfect English barley, and a little rice, ripe in the sun. You are astonished; it seems to you a miracle, until you remember the bag.[end if]";
    award 2 for the fast-marker.

The fast-marker is a thing.

Part 2 - The country inland

A room can be inland.

Along the Brook is north of Up the Creek. "The creek has dwindled to a brook of fresh water, clear and cold and good to drink, running between low banks through pleasant meadows, smooth and green. On the east bank, where the brook cuts into the ground, the earth is yellow-grey; to the west, willows grow thick along the water. The meadows open out northward, and the creek goes back down to the south."
Along the Brook is inland.

The stream is scenery in Along the Brook. Understand "water", "fresh water", "brook" and "meadows" as the stream. The description of the stream is "Clear fresh water. After the ship's stale casks it tastes like wine."
Instead of drinking the stream, say "You drink deep. It is the best water in the world."

The Clay Bank is east of Along the Brook. "The brook has cut deep into the bank here, and laid bare a bed of fine grey clay, smooth and sticky, that takes the print of your thumb. Such clay, you think, might be made into pots, if a man knew how. The brook is back to the west."
Along the Brook is west of the Clay Bank.

The clay bed is scenery in the Clay Bank. Understand "clay", "bed", "bank" and "earth" as the clay bed. The description of the clay bed is "Fine grey clay. You could dig it with a spade."

The Willow Bank is west of Along the Brook. "Willows crowd the edge of the brook here: the kind that are called osiers, with long thin wands that bend without breaking, such as the basket-makers in your father's town used. The brook is back to the east."

The osiers are scenery in the Willow Bank. Understand "willows", "willow", "wands", "twigs" and "osier" as the osiers. The description of the osiers is "Long, supple green wands. As a boy you used to stand at the basket-maker's door and watch him work, and even help him a little."

The Savannas are north of Along the Brook. "Open savannas, or meadows, roll away here, plain and smooth and covered with grass. On the rising parts of them grow tobacco, green and with a great strong stalk, and aloes, and wild sugar canes, imperfect for want of cultivation. [if the goat pen is in the Savannas]Your goat pen stands on the level ground, the kids cropping inside it. [end if]A wood of tall trees rises to the north; a valley opens to the west; the brook is south."
The Savannas are inland.

The wild tobacco is scenery in the Savannas. Understand "tobacco", "aloes", "canes", "sugar canes" and "sugar" as the wild tobacco. The description of the wild tobacco is "Tobacco, green, with a great and strong stalk. You gather some to cure and keep, now that you know its virtue."

The Parrot Wood is north of the Savannas. "Tall trees, their trunks grey and smooth, and a great noise of birds above: parrots, green and scarlet, in hundreds, quarrelling and screaming in the tops. [if Poll is in the Parrot Wood]In the low fork of one tree, almost within reach, a young parrot sits hunched and alone, not yet able to fly well.[end if] The savannas lie south."

The parrots are scenery in the Parrot Wood. Understand "birds", "bird", "tops" and "trees" as the parrots. The description of the parrots is "Hundreds of them, too high and too quick for you. But there is always a young one or two in the lower branches."

The Pleasant Valley is west of the Savannas. "A long delicious vale, where the country becomes more woody. Here are melons upon the ground in great abundance, and grapes upon the trees: the vines have spread indeed over the trees, and the clusters are ripe and rich. There are limes and lemons, and cocoa trees. The verdure is so fresh, and so like a planted garden, that you feel a secret kind of pleasure to think that this is all your own. [if the bower built is true]Your bower stands at the end of the vale: your country house. [end if]Northward the land rises to a grove of great trees; the goat hills are south; a long ridge climbs west; the savannas are east."
The Pleasant Valley is inland.

The grapes are scenery in the Pleasant Valley. Understand "vines", "vine", "clusters", "bunch", "bunches", "limes", "lemons", "melons" and "fruit" as the grapes. The description of the grapes is "Great clusters of grapes, very ripe. You know that to eat too many of them at a time brings on the flux; but dried in the sun, as they dry them in Spain, they would keep: raisins."

The Cedar Grove is north of the Pleasant Valley. "A grove of great cedar trees, so tall that you must lean back to see their tops. One of them, standing a little apart, is a king among them: five feet ten inches through at the foot, and straight as a mast, without a branch for twenty feet. From here, the sea is a glint far off to the east, down a long rough slope. The valley is south."
The Cedar Grove is inland.

The great cedar is scenery in the Cedar Grove. Understand "cedar", "tree", "king", "trunk" and "cedars" as the great cedar. The description of the great cedar is "[if the periagua stage is 0]The finest tree you ever saw. Hollowed, it would make a periagua, a great canoe, big enough to carry twenty-six men: big enough to carry you and all your goods to the main land.[otherwise if the periagua stage is 1]The great cedar lies where it fell, a mountain of timber.[otherwise]The periagua lies here, finished: a noble boat, the finest you ever saw, a hundred yards from the water and uphill all the way.[end if]".

The Western Hill is west of the Pleasant Valley. "The ridge climbs to a bare hill at the west end of the island. From here you look west over the sea, and on a clear day, far off on the horizon, you can make out a long low line of land: the main land, the country of the savages, perhaps even the Spaniards' country. Nearer, below you, is the western shore, where the sea breaks on a long pale beach. The valley is east, and a path goes down to the shore."
The Western Hill is coastal.

The main land is scenery in the Western Hill. Understand "mainland", "horizon", "line" and "land" as the main land. The description of the main land is "A line of land, very high and very far off: fifteen or twenty leagues, you guess. The savages' country. You will think often of that line, over the years, and of going to it."

The Western Shore is below the Western Hill. "A long pale beach at the west end of the island, strewn with shells and weed. The sea comes in here in slow, even ranks. Turtles come up on this shore to lay their eggs, and there are fowls of many kinds that you know, and many that you don't. The hill is above you; the shore runs away south."
The Western Shore is coastal.

The turtle is in the Western Shore. "A great turtle is labouring up the sand, far from the water." The description of the turtle is "A sea turtle, as big as a barrel, with a shell like beaten metal. Turn it on its back and it could not go anywhere." Understand "tortoise", "shell" and "turtles" as the turtle.

The Cannibal Shore is south of the Western Shore. "[if the act is less than 4]A lonely shore at the south-west of the island, with a round of flat sand above the tide-line, and the sea very blue beyond[otherwise]The south-west shore. And here your blood runs cold: the sand is spread with skulls, hands, feet and other bones of human bodies, and in the middle is the place where they made their fire, a circle dug in the earth like a cockpit, where they sat down to their inhuman feastings upon the bodies of their fellow creatures[end if]. The beach runs north, and east, along the south coast of the island, towards a cove."
The Cannibal Shore is coastal.

Part 3 - The south and the thicket

The Goat Hills are south of the Pleasant Valley. "Broken hilly ground, with rocks and short grass, rising steeply to the east. [if the goats are in the Goat Hills][goat view][otherwise]The goats have gone off over the hill.[end if] The valley is north; the hills climb up to some heights above you; a thicket lies south."

The goats are scenery in the Goat Hills. Understand "goat", "herd", "she-goat", "flock" and "kids" as the goats. The description of the goats is "[goat view]".

The approach from above is a truth state that varies.

To say goat view:
    if the approach from above is true:
        say "A little way below you, on the slope, a herd of goats is grazing, and they have not seen you: their eyes are set to watch the valleys, not the heights. There is a she-goat among them, with a young kid by her side.";
    otherwise:
        say "A herd of goats is grazing on the slope; but the moment you come in sight, they are off, bounding away up the rocks, as shy and swift as anything in the world. If you could come upon them from above, now."

Before going down in the Heights:
    now the approach from above is true.
Before going south in the Pleasant Valley:
    now the approach from above is false.
Before going north in the Thicket:
    now the approach from above is false.

The Heights are above the Goat Hills. "High rocky heights above the goat hills, where only goats and you would climb. From here you can see the herd grazing below, and the path down to them. [if the act is at least 3]To the north you can see the green of the valley, and to the east, far off, the blue of the sea by your castle.[end if]".

The Thicket is south of the Goat Hills. "A close thicket of low trees and bushes, hot and dim, full of the humming of insects. Among the trees grows one with a wood so hard and heavy that the Brazilians call it the iron tree. [if the act is at least 4]Under a rock at the thicket's edge is the black mouth of a cave. [end if]The goat hills are north, and a path goes south, towards the sea."

The iron tree is scenery in the Thicket. Understand "ironwood", "iron-wood", "tree" and "wood" as the iron tree. The description of the iron tree is "The iron tree: its wood is so hard it almost turns your axe. A man might make a spade of it, or a mortar to beat corn in."

The Southern Cove is south of the Thicket. "A little cove on the south side of the island, with a sandy beach that shelves gently into still water, sheltered by rocks on either hand. It is the best place on the island to keep a boat. [if the act is at least 4][footprint note]. [end if][if the canoe is in the Southern Cove]Your canoe is drawn up on the sand. [otherwise if the cove cedar is in the Southern Cove]A straight young cedar grows at the head of the beach, not ten yards from the water. [end if]The thicket is north; the shore runs west to the south-west beach, and east to a rocky point."
The Southern Cove is coastal. The Cannibal Shore is west of the Southern Cove.

The cove cedar is scenery in the Southern Cove. Understand "cedar", "young cedar", "tree" and "trunk" as the cove cedar. The description of the cove cedar is "A young cedar, straight and sound, not half the size of the giants inland, and not ten yards from the water's edge. It would make a canoe for one man, or two."

The Rocky Point is east of the Southern Cove. "A long point of rocks runs out into the sea at the south-east of the island, the waves breaking white along it. Off the end of the point the water runs strangely: [current view]. Northward, over the rocks, is the way back to the creek."
The Rocky Point is coastal.
The Creek Mouth is north of the Rocky Point.

The current is scenery in the Rocky Point. Understand "water", "eddy", "stream" and "race" as the current. The description of the current is "[if current running is true]A current like the sluice of a mill, setting hard away to the east and north, out to sea: nothing that floated would come back from it[otherwise]The current has slackened with the turn of the tide, and an eddy runs back towards the shore under the rocks. Now a boat might get round the point[end if]. You have watched it long enough to know its ways: it runs hard with the ebb, and slackens when the tide turns, and then runs hard again, over and over."

Current running is a truth state that varies. Current running is true.
The current clock is a number that varies. The current clock is 10.
The current watched is a truth state that varies.

To say current view:
    if current running is true:
        say "there is a current like the sluice of a mill, setting hard away to the east and north, out to sea, and nothing that floated would come back from it";
    otherwise:
        say "the current has slackened with the turn of the tide, and there is even an eddy running back towards the shore, under the rocks. Now, you think, a boat might get round the point"

Every turn when the location is the Rocky Point and the current watched is false:
    now the current watched is true;
    say "You sit a long while on the rocks and watch the current, and you see how it goes: it runs hard with the ebb, and slackens when the tide turns, and then runs hard again. A boat that went round the point would have to go on the slack, and come back on the slack.";
    award 2 for the current.

Every turn when the act is at least 3:
    decrement the current clock;
    if the current clock is 0:
        now the current clock is 10;
        if current running is true:
            now current running is false;
            if the location is the Rocky Point or the location is Cove Waters, say "Off the point, the current slackens, and the water lies quiet.";
        otherwise:
            now current running is true;
            if the location is the Rocky Point or the location is Cove Waters, say "The current off the point is running hard again.".

Part 4 - Things to make

Section 1 - Fire, the spade and the mortar

The tinderbox is in the sea chest. It is essential. Understand "tinder", "tinder-box", "flint" and "steel" as the tinderbox. The description of the tinderbox is "The cook's tinderbox: flint, steel and tinder, in a tin box."

The fire is a thing. It is fixed in place. Understand "fire", "flames", "embers", "hearth" and "coals" as the fire. The description of the fire is "A good fire of dry wood, well banked, burning in a hearth of stones."

Making fire is an action applying to nothing. Understand "make fire", "light fire", "build fire", "kindle fire" and "start fire" as making fire.
Check making fire:
    if the fire is in the location, say "Your fire is burning already." instead;
    if the location is not Inside the Stockade, say "You would rather keep your fire at home, in the stockade, where it can be watched." instead;
    if the player does not carry the tinderbox, say "You have nothing to strike fire with." instead.
Carry out making fire:
    move the fire to the location;
    say "You gather dry sticks and strike a spark into the tinder, and nurse it into a fire on a hearth of stones before your tent.";
    award 1 for the fire.

Making the spade is an action applying to nothing. Understand "make spade", "carve spade" and "cut spade" as making the spade.
Check making the spade:
    if the spade is not off-stage, say "You have a spade already." instead;
    if the location is not the Thicket, say "You want a wood that is hard enough, and none of the trees about here will do." instead;
    if the player does not carry the axe, say "You need the axe." instead.
Carry out making the spade:
    now the player carries the spade;
    say "You cut a piece of the iron tree, with great labour, for it is so hard it almost spoils your axe, and by little and little you work it into the form of a spade: the handle exactly shaped like ours in England, only the board part having no iron shod upon it at the bottom. It takes you many days.";
    increase the day by 2;
    award 2 for the spade.
The description of the spade is "A spade of ironwood, heavy, with no iron on its edge. It will serve."

The mortar is a thing. The description of the mortar is "A great block of ironwood, hollowed out by fire and the adze into a mortar, with a pestle of the same wood, to beat corn in."
Making the mortar is an action applying to nothing. Understand "make mortar", "carve mortar" and "make pestle" as making the mortar.
Check making the mortar:
    if the mortar is not off-stage, say "You have one already." instead;
    if the location is not the Thicket, say "You need a block of the iron tree, which grows in the thicket." instead;
    if the player does not carry the axe or the player does not carry the adze, say "You would need both the axe and the adze." instead.
Carry out making the mortar:
    now the player carries the mortar;
    say "You cut a great block of the iron tree, and with the adze, and by burning, you hollow it into a mortar, and make a pestle of the same wood. It is a heavy, clumsy thing, but it will beat corn into meal.";
    award 1 for the mortar.

Section 2 - Clay and pots

The lump of clay is a thing. Understand "clay" as the lump of clay. The description of the lump of clay is "A great sticky lump of the grey clay from the brook."
Instead of digging the clay bed:
    if the player does not carry the spade:
        say "You scrape out a handful with your fingers. You'd want a spade to dig any quantity." instead;
    if the lump of clay is not off-stage:
        say "You have clay enough already." instead;
    now the player carries the lump of clay;
    say "You dig out a good lump of the clay with your spade."
Instead of taking the clay bed, try digging the clay bed.

The earthen pot is a container. Understand "pot", "jar", "pots" and "vessel" as the earthen pot. A thing can be fired. The description of the earthen pot is "[if the earthen pot is fired]An earthen pot, burnt hard in the fire, red as a tile, and even glazed a little in one place where the sand in the clay ran with the heat. It will hold water, and bear the fire[otherwise]A pot shaped of clay and dried in the sun: ugly, heavy, and so soft that it would melt in the rain[end if][if the pot water is true]. It is full of fresh water[end if]."
The pot water is a truth state that varies.

Making the pot is an action applying to nothing. Understand "make pot", "shape pot", "mould pot", "form pot" and "make jar" as making the pot.
Check making the pot:
    if the earthen pot is not off-stage, say "You have made your pot." instead;
    if the player does not carry the lump of clay, say "You have no clay." instead.
Carry out making the pot:
    now the lump of clay is off-stage;
    now the player carries the earthen pot;
    say "You work the clay, and mould it, and it is a great while before you can make anything like a pot: many fall in, and many crack in the sun. But at last you have one, dried hard in the sun, that will stand. It will not bear water yet, you think, nor fire, until it is burnt.";
    award 1 for the lump of clay.

Firing is an action applying to one thing. Understand "fire [something]", "bake [something]", "burn [something]" and "harden [something]" as firing.
Instead of putting the earthen pot on the fire, try firing the earthen pot.
Instead of inserting the earthen pot into the fire, try firing the earthen pot.
Check firing:
    if the noun is not the earthen pot, say "You would rather not put that in the fire." instead;
    if the earthen pot is fired, say "It is fired already." instead;
    if the fire is not in the location, say "You need a good fire." instead.
Carry out firing:
    now the earthen pot is fired;
    say "You set the pot in the fire and heap the wood about it, and keep the fire going for five or six hours, until the pot is red hot through. One place begins to melt and run, the sand in the clay turning to glass. Then you let it cool slowly all night. In the morning you have a good, hard earthen pot, and you are as glad as ever you were of anything in your life.";
    award 3 for the earthen pot.

Filling is an action applying to one thing. Understand "fill [something]" as filling.
Check filling:
    if the noun is not the earthen pot, say "That can't hold water." instead;
    if the earthen pot is not fired, say "The raw clay would melt away to nothing." instead;
    if the location is not Along the Brook, say "There is no fresh water here. The brook, north of the creek, is the place." instead.
Carry out filling:
    now the pot water is true;
    say "You fill the pot at the brook with good fresh water."

Section 3 - Baskets, grapes, bread

The osier wands are a thing. Understand "wands", "osier" and "bundle" as the osier wands. The description of the osier wands is "A bundle of green osier wands, cut and ready."
Instead of taking the osiers:
    if the player does not carry the knife and the player does not carry the rusty cutlass and the player does not carry the axe:
        say "You need a blade to cut them." instead;
    if the osier wands are not off-stage:
        say "You have plenty." instead;
    now the player carries the osier wands;
    say "You cut a good bundle of the osier wands."
Cutting is an action applying to one thing. Understand "cut [something]" as cutting.
Cutting it with is an action applying to two things. Understand "cut [something] with [something]" as cutting it with.
Carry out cutting something with something: try cutting the noun.
Carry out cutting:
    say "Cutting [the noun] would serve no purpose."
Instead of cutting the osiers, try taking the osiers.

The basket is a container. The description of the basket is "A basket woven of osier wands: not very handsome, but strong, and it will carry a load."
Weaving is an action applying to nothing. Understand "make basket", "weave basket" and "weave osiers" as weaving.
Check weaving:
    if the basket is not off-stage, say "You have a basket." instead;
    if the player does not carry the osier wands, say "You need osier wands for that." instead.
Carry out weaving:
    now the osier wands are off-stage;
    now the player carries the basket;
    say "You sit in the shade and weave, remembering the basket-maker's hands, and after a day's work you have a basket: a poor one, but strong.";
    award 2 for the basket.

The bunch of grapes is a thing. Understand "grapes" and "bunch" as the bunch of grapes. The description of the bunch of grapes is "A great heavy bunch of ripe grapes."
The raisins are a thing. Understand "raisins" and "dried grapes" as the raisins. The description of the raisins is "Good raisins of the sun, as sweet as any in Spain: food that will keep, for a journey."
Instead of taking the grapes:
    if the bunch of grapes is not off-stage or the raisins are not off-stage:
        say "You have grapes enough for now." instead;
    now the player carries the bunch of grapes;
    say "You cut a great bunch of the grapes."
Drying is an action applying to one thing. Understand "dry [something]" and "hang [something]" as drying.
Check drying:
    if the noun is not the bunch of grapes, say "That doesn't need drying." instead;
    if the location is not the Pleasant Valley, say "You want them to hang in the sun where they grew, in the valley, where you can come back for them." instead.
Carry out drying:
    now the bunch of grapes is off-stage;
    now the player carries the raisins;
    say "You hang the grapes upon the out-branches of the trees, to cure and dry in the sun, and when you come back, after some days, they are raisins: as good as any you ever ate.";
    increase the day by 2;
    award 2 for the raisins.
Instead of eating the bunch of grapes, say "You eat a few, sparingly: too many bring on the flux."
Instead of eating the grapes, say "You eat a few, sparingly: too many bring on the flux."
Does the player mean drying the bunch of grapes: it is very likely.
Does the player mean eating the bunch of grapes: it is very likely.

Instead of eating the raisins, say "They must keep: they are your food for a journey."

The ears of barley are a thing. Understand "barley", "ears", "corn" and "grain" as the ears of barley. The description of the ears of barley is "The ripe ears of your barley, and some rice."
Reaping is an action applying to one thing. Understand "reap [something]", "harvest [something]" and "gather [something]" as reaping.
Check reaping:
    if the noun is not the green barley, say "There is nothing there to reap." instead;
    if the act is less than 3, say "It is not ripe yet." instead;
    if the player does not carry the rusty cutlass and the player does not carry the knife, say "You need a blade: the old cutlass would do for a sickle." instead.
Carry out reaping:
    now the green barley is off-stage;
    now the player carries the ears of barley;
    say "With the old cutlass for a sickle you reap your little harvest, ear by ear. You mean to save it all for seed, and so, in time, you will have bread: but some, a little, you may grind now.";
    award 2 for the green barley.
Instead of taking the green barley, try reaping the green barley.

The meal is a thing. Understand "flour" and "meal" as the meal. The description of the meal is "A little barley meal, coarse, but good."
Grinding is an action applying to one thing. Understand "grind [something]", "pound [something]", "beat [something]" and "crush [something]" as grinding.
Check grinding:
    if the noun is not the ears of barley, say "That isn't something to grind." instead;
    if the player does not carry the mortar, say "You need a mortar to beat the corn in." instead;
    if the meal is not off-stage or the barley loaf is not off-stage, say "You have ground enough for now: the rest of the ears you are keeping back for seed." instead.
Carry out grinding:
    now the player carries the meal;
    say "You beat the corn in your mortar with the pestle, a long, patient labour, until you have a little heap of coarse barley meal. The best of the ears you keep back, for seed."

The barley loaf is a thing. Understand "bread", "loaf" and "cake" as the barley loaf. The description of the barley loaf is "A barley loaf, baked by your own hand in the island: the first bread you have eaten in two years. It tastes like home."
Baking is an action applying to nothing. Understand "bake bread", "make bread", "bake loaf" and "make loaf" as baking.
Check baking:
    if the barley loaf is not off-stage, say "You have your loaf." instead;
    if the player does not carry the meal, say "You have no meal to make bread of." instead;
    if the fire is not in the location, say "You need a fire." instead;
    if the player does not carry the earthen pot or the earthen pot is not fired, say "You need an oven of some kind: a fired earthen pot, turned over the dough on the hot hearth, would serve." instead.
Carry out baking:
    now the meal is off-stage;
    now the player carries the barley loaf;
    say "You mix the meal with water, knead it, and lay it on the hot hearth, and turn your earthen pot over it, and heap the embers round. In an hour you lift the pot, and there is a barley loaf, brown and smoking. You could weep.";
    award 4 for the barley loaf.
Instead of eating the barley loaf, say "It must keep, for a journey. You break off only a crumb, to taste."

Section 4 - Goats

The goat carcass is a thing. Understand "carcass", "dead goat", "meat" and "flesh" as the goat carcass. The description of the goat carcass is "A fat she-goat, shot through the head."
The goatskin is a thing. Understand "skin", "hide" and "goat skin" as the goatskin. The description of the goatskin is "A goat's skin, dried in the sun and stretched on sticks, with the hair on."
The kid is a thing. Understand "young kid", "young goat" and "baby goat" as the kid. The description of the kid is "A young kid, which will not leave you: it has lost its mother."
The kid penned is a truth state that varies.

Every turn when the kid is on-stage and the kid penned is false and the kid is not in the location:
    move the kid to the location;
    say "[one of]The kid trots after you, bleating.[or]The kid follows at your heels.[or]The kid is still with you.[at random]".

Carry out shooting:
    if the player does not carry the fowling-piece and the player does not carry the pistol, say "You have no gun." instead;
    if the fowling-piece is not loaded and the pistol is not loaded, say "Your gun is not loaded." instead;
    say "The shot goes wide. You have wasted the charge.";
    now the fowling-piece is not loaded.

Carry out discharging:
    if the player does not carry the fowling-piece and the player does not carry the pistol, say "You have no gun." instead;
    if the fowling-piece is not loaded and the pistol is not loaded, say "Your gun is not loaded." instead;
    now the fowling-piece is not loaded;
    now the pistol is not loaded;
    say "You fire into the air. The whole island rises at the noise: a cloud of birds of many sorts, screaming and crying, the first gun that has been fired there since the creation of the world, you believe."
Instead of firing the fowling-piece, try discharging.
Instead of firing the pistol, try discharging.

Instead of shooting the player, say "Not today."

Carry out loading:
    if the noun is loaded, say "It is loaded already." instead;
    if the powder barrel is spoiled and the powder horns are not held:
        say "Your powder is spoilt: the rain has made paste of it. You need good dry powder." instead;
    if the powder barrel is not in the location and the player does not carry the powder horns and the powder barrel is not held:
        say "Your powder is not here. It is in the barrel[if the powder barrel is in the Cave], in your cave[end if]; you must fetch a charge from it." instead;
    if the player does not carry the bag of shot, say "You have no shot." instead;
    now the noun is loaded;
    say "You load [the noun] with powder and small shot, and prime it."

Instead of shooting the goats:
    if the player does not carry the fowling-piece, say "You have no gun." instead;
    if the fowling-piece is not loaded, say "Your gun is not loaded." instead;
    now the fowling-piece is not loaded;
    if the approach from above is false:
        now the goats are off-stage;
        say "They are off before you can take aim, and your shot goes whistling over the rocks. You will never come near them from below." instead;
    if the goat carcass is not off-stage or the goatskin is not off-stage:
        say "You shoot another goat, which makes good eating for a week, and dry its skin." instead;
    now the goat carcass is in the location;
    now the kid is in the location;
    say "The goats do not see you. You take aim, and fire, and the she-goat falls. The rest go bounding away; but her young kid stands by her, and when you come and take up the old one on your shoulders, the kid follows you, bleating.";
    award 3 for the goat carcass.

Skinning is an action applying to one thing. Understand "skin [something]", "flay [something]" and "butcher [something]" as skinning.
Check skinning:
    if the noun is not the goat carcass, say "You can't skin that." instead;
    if the player does not carry the knife, say "You need your knife." instead.
Carry out skinning:
    now the goat carcass is off-stage;
    now the player carries the goatskin;
    now the player carries the tallow;
    say "You skin the goat with your knife, and cut up the meat, which you will salt and dry and eat for many days. The skin you stretch on sticks in the sun to dry.".

Building the pen is an action applying to nothing. Understand "build pen", "make pen", "build enclosure", "make enclosure" and "fence savanna" as building the pen.
The goat pen is a thing. It is scenery. Understand "pen", "enclosure" and "hedge" as the goat pen. The description of the goat pen is "A piece of the level savanna, fenced with a close hedge of stakes, with a gate of hurdles. [if the kid penned is true]Your goats are inside: the kid, grown now, and more besides, for you have taken others in pit-traps. You have milk, and butter, and cheese, and meat, whenever you please[otherwise]It is empty[end if]."
Check building the pen:
    if the goat pen is not off-stage, say "The pen is built." instead;
    if the location is not the Savannas, say "You want level, open ground, with grass: the savannas." instead;
    if the player does not carry the axe, say "You need the axe to cut the stakes." instead.
Carry out building the pen:
    move the goat pen to the Savannas;
    say "You enclose a piece of the savanna with a hedge of stakes, and a gate of hurdles, so close that no goat can get out. It takes you three months, as it seems; but it is done.";
    increase the day by 3;
    award 2 for the goat pen.
Instead of inserting the kid into the goat pen, try penning.
Instead of putting the kid on the goat pen, try penning.
Penning is an action applying to nothing. Understand "pen kid", "pen goat" and "release kid" as penning.
Check penning:
    if the kid is not in the location, say "You have no goat to pen." instead;
    if the goat pen is not in the location, say "There is no pen here." instead.
Carry out penning:
    now the kid penned is true;
    now the kid penned day is the day;
    now the kid is off-stage;
    say "You shut the kid in the pen. In time you will have a flock of them, and milk and cheese, and never want for meat again.";
    award 3 for the kid.

The goat pit is a thing. It is fixed in place. Understand "pit" and "trap" as the goat pit. The description of the goat pit is "A pit dug where the goats pass, covered over with sticks and grass."
Digging the pit is an action applying to nothing. Understand "dig pit", "dig trap" and "make trap" as digging the pit.
Check digging the pit:
    if the goat pit is not off-stage, say "You have dug a pit." instead;
    if the location is not the Goat Hills, say "Dig it where the goats pass: in the goat hills." instead;
    if the player does not carry the spade, say "You need a spade." instead.
Carry out digging the pit:
    move the goat pit to the Goat Hills;
    say "You dig a pit where the goats come to feed, and cover it with hurdles and grass. In the morning, you think, there may be something in it."
Every turn when the goat pit is in the Goat Hills and the kid is off-stage and the kid penned is false and the location is the Goat Hills and the day is greater than the pit day:
    now the kid is in the Goat Hills;
    say "In the pit is a young kid, bleating, unhurt. You lift it out, and it follows you, as tame as a dog.".
The pit day is a number that varies.
After digging the pit: now the pit day is the day.

Section 5 - The umbrella and the cap

The umbrella is a thing. The description of the umbrella is "An umbrella of goat's skins, the hair outwards, so that it casts off the rain like a penthouse and keeps off the sun. You spoilt two or three before you made one to your mind; this one opens and shuts."
The goatskin cap is a wearable thing. Understand "cap" and "hat" as the goatskin cap. The description of the goatskin cap is "A great high shapeless cap of goat's skin, with a flap hanging down behind to keep the sun off your neck. If anyone in England saw you in it, they would laugh, or run."

Making the umbrella is an action applying to nothing. Understand "make umbrella" and "sew umbrella" as making the umbrella.
Check making the umbrella:
    if the umbrella is not off-stage, say "You have one." instead;
    if the player does not carry the goatskin, say "You need a goat's skin." instead;
    if the player does not carry the knife, say "You need your knife." instead.
Carry out making the umbrella:
    now the player carries the umbrella;
    say "You take great pains, and are a great while about it, and spoil two or three; but at last you have an umbrella that will open and shut, of goat's skin with the hair outwards. There is skin to spare for a cap.";
    award 2 for the umbrella.
Making the cap is an action applying to nothing. Understand "make cap", "sew cap" and "make hat" as making the cap.
Check making the cap:
    if the goatskin cap is not off-stage, say "You have one." instead;
    if the player does not carry the goatskin, say "You need a goat's skin." instead.
Carry out making the cap:
    now the goatskin is off-stage;
    now the player wears the goatskin cap;
    say "Of the last of the skin you make a great high cap, with a flap behind. You put it on.";
    award 1 for the goatskin cap.

Section 6 - Poll

Poll is a thing in the Parrot Wood. Poll is proper-named. Poll is scenery. The printed name of Poll is "Poll". Understand "parrot", "young parrot" and "bird" as Poll. The description of Poll is "A young green parrot[if Poll is in the Parrot Wood], hunched in a low fork, just out of reach[otherwise], your own, who sits on your shoulder and looks at you sideways[end if][if the poll lessons is at least 3]. Poll can talk[end if]."
The poll lessons is a number that varies.

Instead of taking Poll when Poll is in the Parrot Wood:
    if the player carries the short stick:
        now the player carries Poll;
        now Poll is not scenery;
        say "You knock the young parrot down out of the fork with your stick, gently, and catch it before it falls, and it lies in your hands, stunned and furious. You carry it home. It will be some years before you can make it speak; but make it speak you will.";
        award 2 for Poll;
    otherwise:
        say "Just out of reach. A stick might do it."
Instead of attacking Poll when Poll is in the Parrot Wood, try taking Poll.

Teaching is an action applying to one thing. Understand "teach [something]" and "train [something]" as teaching.
Check teaching:
    if the noun is not Poll, say "That can't learn anything from you." instead;
    if the player does not carry Poll, say "You'd need Poll with you." instead.
Carry out teaching:
    increment the poll lessons;
    if the poll lessons is 1:
        say "You say to Poll, slowly and clearly, 'Poor Robin Crusoe.' Poll looks at you.";
    otherwise if the poll lessons is 2:
        say "'Poor Robin Crusoe! Where are you?' Poll bobs its head and mutters something in parrot.";
    otherwise if the poll lessons is 3:
        say "'Poor Robin Crusoe! Where are you? Where have you been?' And Poll, clear as a bell, answers: [italic type]Poor Robin Crusoe! Where are you? Where have you been? How came you here?[roman type][paragraph break]It is the first voice you have heard, other than your own, since you came ashore. You sit down on the ground and laugh until you cry.";
        award 3 for the pen-lesson-marker;
    otherwise:
        say "'Poor Robin Crusoe!' says Poll, before you can open your mouth."
The pen-lesson-marker is a thing.

Section 7 - The turtle

Instead of turning the turtle:
    if the turtle is not scored:
        say "You catch the turtle by the edge of the shell and heave it over on its back, and there it lies, waving its flippers helplessly. You cut it up: in it are threescore eggs, and its flesh is to you the most savoury and pleasant that ever you tasted in your life.";
        award 2 for the turtle;
        now the turtle is off-stage;
    otherwise:
        say "It is gone.".
Instead of pushing the turtle, try turning the turtle.
Instead of taking the turtle, try turning the turtle.

Section 8 - The periagua (a lesson)

The periagua stage is a number that varies.
Instead of chopping the great cedar:
    if the periagua stage is 0:
        now the periagua stage is 1;
        say "You fall to work upon the great cedar. You are twenty days hacking and hewing at it at the bottom, fourteen more getting the branches off, and a month in shaping it. At last it falls, with a noise like the end of the world.";
        increase the day by 4;
    otherwise:
        say "It is down already."
Instead of chopping the great cedar when the player does not carry the axe, say "You would need an axe for that."
Hollowing is an action applying to one thing. Understand "hollow [something]", "hollow out [something]", "shape [something]" and "carve out [something]" as hollowing.
Check hollowing:
    if the noun is the great cedar:
        if the periagua stage is 0, say "It must come down first." instead;
        if the periagua stage is 2, say "It is finished." instead;
        if the player does not carry the adze, say "You need the adze." instead;
    otherwise if the noun is the cove cedar:
        if the cove cedar is in the Southern Cove, say "It must come down first." instead;
    otherwise:
        say "That can't be hollowed." instead.
Carry out hollowing:
    if the noun is the great cedar:
        now the periagua stage is 2;
        say "It costs you near three months more to clear the inside, and work it out so as to make an exact boat of it: by mallet and chisel, by dint of hard labour, till you have brought it to be a very handsome periagua, and big enough to carry six-and-twenty men.[paragraph break]When you have done, you are extremely delighted with it. The boat is really much bigger than ever you saw a canoe or periagua, that was made of one tree, in your life. Many a weary stroke it has cost, you may be sure; and there remains nothing but to get it into the water.";
        increase the day by 4.

Launching the periagua is an action applying to nothing. Understand "launch periagua", "push periagua", "drag periagua" and "move periagua" as launching the periagua.
Instead of launching the great cedar, try launching the periagua.
Instead of pushing the great cedar, try launching the periagua.
Carry out launching the periagua:
    if the location is not the Cedar Grove or the periagua stage is less than 2:
        say "There is no periagua here." instead;
    say "It lies about a hundred yards from the water, and no more; but the ground is higher towards the creek than where it lies. You dig away the rise to make a declivity: that costs a prodigious deal of pains. Then you try to push it, and it will not stir; you might as well push the hill. You measure the distance, and resolve to cut a dock or canal, to bring the water up to it; but when you calculate how deep it must be dug, and how broad, you find that by the number of hands you have, being none but your own, it must have been ten or twelve years before you could have gone through with it.[paragraph break]Now you see, though too late, the folly of beginning a work before you count the cost, and before you judge rightly of your own strength to go through with it. You leave it where it lies. The next boat, you resolve, will be built where the water can reach it.";
    award 1 for the great cedar.

Section 9 - The bower

The bower built is a truth state that varies.
Instead of building the bower when the location is the Hillside Plain, try hut-building.
Building the bower is an action applying to nothing. Understand "build bower", "make bower", "build house" and "build hut" as building the bower.
Check building the bower:
    if the bower built is true, say "Your bower is built." instead;
    if the location is not the Pleasant Valley, say "The place for a country house is the pleasant valley, among the grapes." instead;
    if the player does not carry the axe, say "You need the axe." instead.
Carry out building the bower:
    now the bower built is true;
    now the Pleasant Valley is sheltered;
    say "At the end of the valley you make a little kind of bower, surrounded at a distance with a strong fence, being a double hedge as high as you can reach, well staked and filled between with brushwood. Here you lie very secure, sometimes two or three nights together: your country house, while the stockade by the sea is your castle.";
    award 2 for the bower-marker.
The bower-marker is a thing.

Part 5 - The canoe

The canoe is a supporter. It is fixed in place. Understand "boat" and "dugout" as the canoe. The description of the canoe is "A canoe of one cedar trunk, hollowed with the adze: small, rough, and near enough the water to be launched. [canoe cargo]".
To say canoe cargo:
    if the treasure chest is on the canoe:
        say "The Spanish chest is lashed amidships.";
    otherwise:
        say "It is empty."

The fallen cedar is a thing. It is fixed in place. Understand "log", "cedar", "trunk" and "tree" as the fallen cedar. The description of the fallen cedar is "The young cedar lies at the head of the beach, lopped and ready to be shaped."
Instead of chopping the cove cedar:
    if the player does not carry the axe, say "You would need an axe." instead;
    now the cove cedar is off-stage;
    move the fallen cedar to the Southern Cove;
    say "You fell the young cedar where it stands, close to the water, and lop its branches. This time, you have learnt, you have counted the cost before you began: it lies not ten yards from the sea, and downhill."
Instead of hollowing the fallen cedar:
    if the player does not carry the adze, say "You need the adze." instead;
    now the fallen cedar is off-stage;
    move the canoe to the Southern Cove;
    say "With the adze, and with fire, you hollow the log and shape it, day after day, until it is a canoe: not large, but sound, and when you push it, it moves.";
    increase the day by 3;
    award 4 for the canoe.

The paddle is a thing. Understand "oar" as the paddle. The description of the paddle is "A paddle, carved from a piece of cedar."
Carving the paddle is an action applying to nothing. Understand "carve paddle", "make paddle", "make oar" and "carve oar" as carving the paddle.
Check carving the paddle:
    if the paddle is not off-stage, say "You have a paddle." instead;
    if the player does not carry the knife and the player does not carry the adze, say "You need a knife or the adze." instead.
Carry out carving the paddle:
    now the player carries the paddle;
    say "You carve a paddle from a piece of cedar, broad in the blade.";
    award 1 for the paddle.

Cove Waters is a room. The printed name of Cove Waters is "In the Canoe". "You are in your canoe, off the southern cove, riding the swell. The island lies green and quiet to the north. Eastward, beyond the rocky point, [if the Spanish wreck seen is true]you can see the wreck of the Spanish ship, jammed between two rocks[otherwise]the open sea stretches away, and the current you have watched[end if]."
Cove Waters is coastal.

The Spanish wreck seen is a truth state that varies.
The canoe trips is a number that varies.

Carry out launching the canoe:
    if the location is the Southern Cove:
        if the canoe is not in the Southern Cove, say "Your canoe is not here." instead;
        if the player does not carry the paddle, say "You would need a paddle." instead;
        move the canoe to Cove Waters;
        move the player to Cove Waters;
        increment the canoe trips;
    otherwise if the location is the Spanish Deck:
        paddle home;
    otherwise:
        say "Your canoe is not here."

Instead of going north in Cove Waters:
    say "You paddle back into the cove and run the canoe up on the sand.";
    move the canoe to the Southern Cove;
    move the player to the Southern Cove;
    if the treasure chest is on the canoe:
        move the treasure chest to the Southern Cove;
        say "[paragraph break]You heave the Spanish chest out onto the beach.";
        now the chest day is the day;
        now the footprint pending is true;
        award 5 for the treasure chest.
Instead of exiting in Cove Waters, try going north.

Instead of going east in Cove Waters:
    if the Spanish wreck seen is false:
        say "There is nothing out there but sea and the current. You have no errand past the point yet." instead;
    if the player does not carry the raisins and the player does not carry the barley loaf:
        say "It is a long way out to the wreck, and you might be all day about it. You will not put to sea without food for the voyage: raisins, or bread." instead;
    if the earthen pot is not held or the pot water is false:
        say "It is a long way out, under the sun. You will not venture it without water: a pot of fresh water." instead;
    if current running is true:
        say "The current is running hard off the point. Paddle out into it anyway? ";
        if the player consents:
            end the story saying "The current takes the canoe like a leaf, and carries you off to the north and east, past the end of the island, and out into the empty sea." instead;
        say "You hold the canoe in the lee of the rocks and wait." instead;
    say "You paddle out past the point on the slack water, keeping close under the rocks while the eddy helps you, and then strike out for the wreck. It is a long pull, and hot; you eat and drink as you go. At last you come up under her side and make the canoe fast.";
    move the canoe to the Spanish Deck;
    move the player to the Spanish Deck.

To paddle home:
    if the canoe is not in the Spanish Deck, say "Your canoe is not here." instead;
    if current running is true:
        say "The current is running hard off the point, between you and home. Push off into it anyway? ";
        if the player consents:
            end the story saying "The current takes you out of sight of the land, and you never see it again." instead;
        say "You wait aboard the wreck for the slack." instead;
    say "You push off and paddle back across the slack water, round the point, and into the lee of the island.";
    move the canoe to Cove Waters;
    move the player to Cove Waters.

Part 6 - The Spanish wreck

The Spanish Deck is a room. The printed name of the Spanish Deck is "The Spanish Wreck". "A ship of the Spanish build, jammed fast between two rocks, her stern and quarter beaten to pieces by the sea, her forecastle standing up out of the water. There is no one aboard: the men must have taken to the boat, and been lost. [if the canoe is in the Spanish Deck]Your canoe is made fast under her side. [end if]A hatch leads down into what is left of her cabin."
The Spanish Deck is coastal.

The Spanish Cabin is below the Spanish Deck. "The cabin is half full of water. Chests and bales are tumbled against the side where she lies over. Most are soaked and spoilt; one iron-bound chest, jammed high under the beams, looks sound."

The treasure chest is in the Spanish Cabin. It is heavy, cargo and essential. Understand "iron-bound chest", "spanish chest", "chest" and "money" as the treasure chest. The description of the treasure chest is "An iron-bound chest, very heavy. You prise up the lid: it is full of pieces of eight, eleven hundred of them, you judge; and six doubloons of gold wrapped in a paper, and some small bars or wedges of gold, weighing near a pound. A great treasure, and of no more use to you here than the dirt under your feet. And yet you take it."

The powder horns are in the Spanish Cabin. They are essential. Understand "horns", "horn", "powder" and "powder horn" as the powder horns. The description of the powder horns is "Two powder horns, full of fine glazed powder, such as our English gunners use: dry, sound, and worth more to you than the gold."

The Spanish shirts are in the Spanish Cabin. Understand "shirts", "linen", "handkerchiefs" and "shirt" as the Spanish shirts. The description of the Spanish shirts is "Some very good linen shirts, and a dozen and a half of white linen handkerchiefs and coloured neckcloths. You have not had linen next your skin in years."

Instead of taking the treasure chest when the location is the Spanish Cabin, say "It is far too heavy to carry up out of the cabin. With a rope you could get it up and into your canoe: LOAD it."
Instead of putting something on the canoe, try loading the noun onto the canoe.
Instead of inserting something into the canoe, try loading the noun onto the canoe.

Instead of going up in the Spanish Deck, say "There is nothing up there but broken rigging."

Part 7 - The footprint

The footprint seen is a truth state that varies.
The footprint pending is a truth state that varies.

To say footprint note:
    say "On the sand above the tide-line is the print of a man's naked foot: toes, heel and every part of a foot, very plain".

The chest day is a number that varies.

Every turn when the location is the Southern Cove and the footprint pending is true and the footprint seen is false and the day is greater than the chest day:
    now the footprint seen is true;
    now the act is 4;
    now the year is 1674;
    now the dog is off-stage;
    say "[bold type]The Fifteenth Year[roman type][paragraph break]Going down to your canoe one noon, you are exceedingly surprised with the print of a man's naked foot on the shore, very plain to be seen in the sand. You stand like one thunderstruck, or as if you had seen an apparition. You listen, you look round you, you can hear nothing, nor see anything. You go up the shore and down, but it is all one: you can see no other impression but that one.[paragraph break]Your old dog is dead these two years, of mere old age; you have only Poll, and the goats, and now this. You go home to your fortification, not feeling, as we say, the ground you go on, but terrified to the last degree, looking behind you at every two or three steps, mistaking every bush and tree, and fancying every stump at a distance to be a man.";
    award 3 for the footprint-marker.
The footprint-marker is a thing.

Volume 5 - The Footprint and Friday

Part 1 - The dark cave and the bones

The Cavern is inside from the Thicket. "A great cave, very dark, much bigger than your own. Deep in the dark at the back [if the old goat is in the Cavern]two broad shining eyes are staring at you, whether of devil or man you cannot tell[otherwise]the old goat lies still[end if]. The daylight is outside."
Instead of going inside in the Thicket when the act is less than 4, say "There is nothing here but the thicket."

The old goat is in the Cavern. It is scenery. Understand "eyes", "goat", "devil" and "thing" as the old goat. The description of the old goat is "[if the old goat is scored]A monstrous frightful old he-goat, just making his will, as we say, and gasping for life, dying indeed of mere old age[otherwise]Two broad shining eyes, in the dark, watching you. Your hair stands on end[end if]."
Instead of doing something other than examining to the old goat:
    if the old goat is not scored:
        say "You pluck up your courage, take up a firebrand, and rush in. Before you have gone three steps you are almost as much frightened as before: you hear a very loud sigh, like that of a man in some pain, followed by a broken noise, as of words half expressed, and a deep sigh again. Then you see it: a monstrous frightful old he-goat, lying on the ground, dying of old age. You laugh at yourself till your sides ache.[paragraph break]It is a fine dry cave, you think. A man could hide his powder here, and himself too, if the savages came.";
        award 2 for the old goat;
    otherwise:
        say "Let the old fellow die in peace."
Instead of entering the Cavern, try going inside.

Part 2 - The savages

The rescue clock is a number that varies.
The savages landed is a truth state that varies.
The Friday rescued is a truth state that varies.

Looking through is an action applying to one thing. Understand "look through [something]", "look in [something]", "use [something]" and "spy with [something]" as looking through.
Check looking through:
    if the noun is not the perspective glass, say "You see nothing special." instead;
    if the player does not carry the perspective glass, say "You don't have it." instead.
Carry out looking through:
    if the location is not the Hilltop and the location is not the Western Hill and the location is not the Heights:
        say "Trees and rocks block the view. From the top of a hill you could see a long way." instead;
    if the act is 4 and the Friday rescued is false:
        if the day is less than the footprint day plus 1:
            say "You sweep the sea and the shores with the glass, again and again. Nothing: no canoe, no smoke, no man. But the print was real." instead;
        now the savages landed is true;
        now the rescue clock is 10;
        say "You sweep the shores with the glass, and your heart stops: on the south-west shore, where the bones are, there are five canoes drawn up, and thirty savages dancing about a fire. As you watch, they drag two wretches from the boats. One is knocked down at once. The other, seeing himself a little at liberty, starts away from them, and runs with incredible swiftness along the sands, directly towards you: towards the creek by your castle. Three of them are after him.[paragraph break]If he reaches the creek he must swim it. You could be there before him.";
        award 2 for the perspective glass;
    otherwise if the act is 5 and the mutiny phase is 0:
        start the mutiny;
    otherwise if the Spanish wreck seen is true and the act is 3:
        say "Far off to the south-east, beyond the rocky point, the Spanish wreck sits between her rocks.";
    otherwise:
        say "The sea, empty to the edge of the world."

The footprint day is a number that varies.
Every turn when the footprint seen is true and the footprint day is 0:
    now the footprint day is the day.

The first savage is a man. The description of the first savage is "A tall savage, naked, with a club in his hand." Understand "savage", "savages", "pursuer" and "man" as the first savage.
The second savage is a man. The description of the second savage is "A savage, naked, fitting an arrow to his bow." Understand "savage", "savages", "pursuer", "bowman" and "man" as the second savage.
The captive is a man. The printed name of the captive is "young savage". The description of the captive is "A comely, handsome young fellow, with long black hair, of about twenty-six[if the Friday rescued is true], who owes you his life. He watches your every movement, and waits for you to give him a name[otherwise], running for his life[end if]." Understand "savage", "runner", "prisoner", "fellow", "young" and "him" as the captive.
The dead savages are a thing. It is fixed in place. Understand "bodies", "body", "dead" and "corpses" as the dead savages. The description of the dead savages is "The two savages lie where they fell, on the creek bank."

Every turn when the savages landed is true and the Friday rescued is false:
    if the location is Up the Creek:
        if the first savage is off-stage and the second savage is off-stage and the captive is off-stage:
            move the first savage to Up the Creek;
            move the second savage to Up the Creek;
            move the captive to Up the Creek;
            say "[paragraph break]Here he comes, running along the shore, and plunges into the creek, and swims across it in thirty strokes, and runs on up the bank, straight towards you. Of the three who follow, one stops at the creek, not being able to swim, and goes back; the other two swim over, and come on, the first with a club, the second with his bow in his hand. The runner sees you and stops, terrified, between you and them. Now is the time: if you are to have a servant, and perhaps a companion, you are called upon plainly by Providence to save this poor creature's life.";
    otherwise if the first savage is off-stage:
        decrement the rescue clock;
        if the rescue clock is 0:
            now the savages landed is false;
            say "[paragraph break]Too late: you are not at the creek. When you come there at last there is nothing but footprints in the mud. Later, from the hill, you watch the canoes put off, and the smoke of the fire drift away. They will come again. You will watch for them, and be quicker.".

Instead of going west in the Western Shore when the savages landed is true, say "You can hear them from here, the drums and the shrieking."
Instead of going south in the Western Shore when the savages landed is true:
    say "They are there on the south-west shore, thirty of them, about their fire. Walk out among them? ";
    if the player consents:
        end the story saying "They see you at once, and they are thirty.";
    otherwise:
        say "You draw back into the trees."
Instead of going west in the Southern Cove when the savages landed is true:
    say "The savages are on the shore just west of here, thirty of them. Walk out among them? ";
    if the player consents:
        end the story saying "They see you at once, and they are thirty.";
    otherwise:
        say "You draw back into the thicket."

Instead of attacking the first savage:
    if the first savage is not in the location, continue the action;
    now the first savage is off-stage;
    move the dead savages to the location;
    say "You rush between the runner and his pursuers, and with the stock of your piece you knock the foremost down. He does not rise again.";
    check the rescue.
Instead of attacking the second savage:
    if the first savage is in the location:
        say "The one with the club is nearer." instead;
    if the fowling-piece is loaded or the pistol is loaded:
        try shooting the second savage instead;
    say "He has his bow drawn, and he is too far off to reach with the stock of a gun. You need a loaded gun." instead.
Instead of shooting the second savage:
    if the fowling-piece is not loaded and the pistol is not loaded, say "Your gun is not loaded." instead;
    now the fowling-piece is not loaded;
    now the pistol is not loaded;
    now the second savage is off-stage;
    move the dead savages to the location;
    say "The second savage has fitted his arrow to the bow, and is taking aim at you, when you fire. He drops dead. The runner, though he saw both his enemies fallen, is so frighted with the fire and noise of your piece that he stands stock still.";
    check the rescue.
Instead of shooting the first savage:
    if the fowling-piece is not loaded and the pistol is not loaded, say "Your gun is not loaded." instead;
    now the fowling-piece is not loaded;
    now the pistol is not loaded;
    now the first savage is off-stage;
    move the dead savages to the location;
    say "You fire, and the savage with the club drops dead. The other stops, and fits an arrow to his bow.";
    check the rescue.
Instead of attacking the captive, say "You have not come to kill him."
Instead of shooting the captive, say "You have not come to kill him."

To check the rescue:
    if the first savage is off-stage and the second savage is off-stage:
        now the Friday rescued is true;
        now the savages landed is false;
        say "[paragraph break]You beckon to the runner to come to you. He comes nearer and nearer, kneeling down every ten or twelve steps, in token of acknowledgment for saving his life. At last he lays his head upon the ground, and, taking you by the foot, sets your foot upon his head: a token, as you understand it, of swearing to be your slave for ever.";
        say "[paragraph break]He will need a name.";
        award 5 for the captive.

Part 3 - Friday

Understand "approach [something]" as touching.

Friday is a man. Friday is proper-named. Understand "savage", "man", "young man", "servant" and "fellow" as Friday. The description of Friday is "A comely, handsome fellow, tall and well-shaped, of about twenty-six. He has a very good countenance, with all the sweetness and softness of an European in it, especially when he smiles. His hair is long and black, his forehead very high, and his eyes lively and sparkling[if Friday is clothed]. He wears a linen shirt from the Spanish wreck, and is very proud of it[otherwise]. He is stark naked[end if][if Friday is taught]. He can speak English now, after his fashion, and calls you Master[end if]."
A person can be named. A person can be clothed. A person can be taught.

Every turn when the Friday rescued is true and the captive is on-stage and the captive is not in the location and a companion can follow:
    move the captive to the location;
    say "The young savage follows you, close as a shadow.".

Every turn when the Friday rescued is true and Friday is not in the location and Friday is on-stage and a companion can follow:
    move Friday to the location;
    say "[one of]Friday follows close at your heels.[or]Friday comes after you, watching everything.[or]Friday is with you.[at random]".

Naming is an action applying to one thing. Understand "name [someone] friday", "call [someone] friday" and "christen [someone] friday" as naming.
Check naming:
    if the noun is Friday, say "He is Friday already." instead;
    if the noun is not the captive, say "They have a name already." instead.
Carry out naming:
    now the captive is off-stage;
    move Friday to the location;
    now Friday is named;
    say "You let him know his name shall be Friday, which is the day you saved his life; you call him so for the memory of the time. You teach him to say Master, and let him know that is to be your name.";
    award 2 for Friday.

Burying is an action applying to one thing. Understand "bury [something]" as burying.
Check burying:
    if the noun is not the dead savages, say "There is no need to bury that." instead.
Carry out burying:
    now the dead savages are off-stage;
    say "Friday makes signs to you that he would like to dig the two savages up again, and eat them. You appear very angry at it, and express your abhorrence of it, and make him understand you will kill him if he offers it. Then, very reluctantly, he helps you bury them in the sand, so deep that no one will find them.";
    award 2 for the dead savages.

Instead of giving something to the captive, say "First he wants a name: NAME HIM FRIDAY."
Instead of teaching the captive, say "First he wants a name: NAME HIM FRIDAY."

Instead of giving the Spanish shirts to Friday:
    now Friday is clothed;
    now the Spanish shirts are off-stage;
    say "You give him a linen shirt from the Spanish wreck, and a pair of drawers you cut from a sailcloth waistcoat, and a cap of hare's skin. He is mightily well pleased to see himself almost as well clothed as his master. It sits very awkwardly upon him at first, and he complains of it; but after a while he takes to it very well.";
    award 2 for the Spanish shirts.
Instead of giving the goatskin to Friday:
    now Friday is clothed;
    now the goatskin is off-stage;
    say "You make him a jerkin of goat's skin, as well as your skill will allow. He wears it with a kind of wonder.";
    award 2 for the Spanish shirts.

Instead of teaching Friday:
    if Friday is taught, say "He learns something new every day." instead;
    if Friday is not named, say "First give him a name: NAME HIM FRIDAY." instead;
    now Friday is taught;
    say "You set about teaching him to speak, and he is the aptest scholar that ever was; so merry, so constantly diligent, and so pleased when he can but understand you, that it is very pleasant to you to talk to him. You teach him Master, and yes, and no, and bread, and then a great many words; and in time he talks to you pretty well. You tell him about God, and England; he tells you about his people, and the white men with beards who live among them, over the sea.";
    award 3 for the pen-lesson-friday.
The pen-lesson-friday is a thing.

Instead of asking Friday about, say "[if Friday is taught]'Friday not know that, Master,' he says, cheerfully.[otherwise]He watches your face, and does not understand.[end if]".
Instead of telling Friday about, say "[if Friday is taught]Friday listens, his head on one side, and nods very seriously.[otherwise]He watches your face, and does not understand.[end if]".

Volume 6 - The English Ship

Part 1 - The ship

The mutiny phase is a number that varies. The mutiny phase is 0.
The mutiny clock is a number that varies.

The longboat is a thing. It is fixed in place. Understand "boat", "longboat" and "long-boat" as the longboat. The description of the longboat is "An English ship's longboat, run up on the mud of the creek[if the mutiny phase is at least 5], with a great hole knocked in her bottom[end if]."
The mutineers are a man. The mutineers are plural-named. Understand "seamen", "sailors", "mutineers", "men" and "rogues" as the mutineers. The description of the mutineers is "[if the mutiny phase is 1]Eleven seamen, armed, rambling about the creek and the shore as if to see the country[otherwise if the mutiny phase is 2]The seamen lie asleep under the trees, in the heat of the day, their muskets beside them[otherwise]The mutineers[end if]."
The captain is a man. Understand "prisoners", "prisoner", "mate" and "passenger" as the captain. The description of the captain is "[if the mutiny phase is less than 3]Three men, bound hand and foot, sitting under the great tree: one, by his dress, a ship's captain; the others his mate and a passenger. They look like men who expect to be killed[otherwise]The captain of the English ship: a sober, sensible man, grateful and quick[end if]."

To start the mutiny:
    now the mutiny phase is 1;
    now the mutiny clock is 12;
    now the year is 1686;
    move the longboat to the Creek Mouth;
    move the mutineers to the Creek Mouth;
    move the captain to the Great Tree;
    say "A ship! You have not seen an English ship in seven-and-twenty years. She rides at anchor a league and a half off, to the south-east, and as you watch, her longboat puts in towards the shore, into your very creek, with eleven men in her. They run her up on the mud; three of them are unarmed, and bound, and the others push them about with the butts of their muskets. You know these men, or men like them: they are mutineers, and the three are their prisoners, and they mean to maroon them, or worse.[paragraph break]You must be careful. Friday is at your elbow, trembling.";
    award 2 for the longboat.

Every turn when the mutiny phase is 1:
    decrement the mutiny clock;
    if the mutiny clock is 6:
        move the mutineers to Along the Brook;
        if the location is the Creek Mouth or the location is Up the Creek, say "The seamen leave the boat and straggle off up the creek, into the country, laughing and shouting.";
    if the mutiny clock is 0:
        now the mutiny phase is 2;
        say "[paragraph break]It is the heat of the day. You can see, or guess, that the seamen have gone to lie down under the trees along the brook, and are asleep; the three prisoners sit alone under the great tree above the landing beach.".

Instead of going north in the Landing Beach when the mutiny phase is 1:
    say "The seamen are still awake and about, and the prisoners are under the great tree, in plain view. Go to them now? ";
    if the player consents:
        end the story saying "A musket-ball takes you in the chest before you have gone ten steps.";
    otherwise:
        say "You wait in the bushes." instead.
Instead of going north in Up the Creek when the mutiny phase is 1 and the mutineers are in Along the Brook:
    say "The seamen are just up the brook, awake. You would walk straight into them." instead.

Part 2 - The captain

Instead of talking to the captain, captain talk.
Instead of asking the captain about, captain talk.
Instead of telling the captain about, captain talk.

To captain talk:
    if the mutiny phase is 2:
        say "You come up behind them, and call aloud in Spanish, 'What are ye, gentlemen?' They start up at the noise, and at your strange figure: goatskin and cap and gun. 'Am I talking to God, or man? Is it a real man, or an angel?' the captain says. You tell him you are a man, an Englishman, and disposed to assist him. His men have mutinied, he says, and meant to leave him here to die. You make terms with him: that while he stays on the island he will be governed by you, and that if the ship is recovered he will carry you and your man to England, passage free. He agrees to everything. 'I will live and die with you,' he says.[paragraph break]Now cut them loose.";
    otherwise if the mutiny phase is 3:
        say "'Two of them are desperate villains,' says the captain, 'the ringleaders. The rest would return to their duty if those two were dead.' The seamen are asleep by the brook.";
    otherwise:
        say "The captain nods, and waits for your orders."

Talking to is an action applying to one thing. Understand "talk to [someone]", "speak to [someone]", "greet [someone]" and "hail [someone]" as talking to.
Carry out talking to: say "[The noun] [if the noun is Friday]smiles, and says 'Master!'[otherwise]does not answer.[end if]".

Freeing is an action applying to one thing. Understand "free [someone]", "untie [someone]", "unbind [someone]" and "release [someone]" as freeing.
Instead of cutting the captain, try freeing the captain.
The bonds are part of the captain. Understand "bond", "ropes", "rope", "cords" and "cord" as the bonds. The description of the bonds is "[if the mutiny phase is greater than 2]Cut, and lying in the grass[otherwise]Tarred cord, pulled cruelly tight about their wrists[end if]."
Instead of cutting the bonds, try freeing the captain.
Check freeing:
    if the noun is not the captain, say "[The noun] is not bound." instead;
    if the mutiny phase is greater than 2, say "They are free already." instead;
    if the player does not carry the knife and the player does not carry the rusty cutlass and the player does not carry the axe, say "You have nothing to cut their bonds with." instead.
Carry out freeing:
    now the mutiny phase is 3;
    say "You cut their bonds with your knife, and they stand up, rubbing their wrists. You give the captain your pistol, and the mate a fowling-piece of the ship's; they follow you, their faces set.";
    award 3 for the captain.

Every turn when the mutiny phase is at least 3 and the mutiny phase is less than 8 and the captain is not in the location and a companion can follow:
    move the captain to the location.

Instead of attacking the mutineers, try shooting the mutineers.
Instead of shooting the mutineers:
    if the mutiny phase is less than 3:
        say "One gun against eleven? Free the prisoners first." instead;
    if the mutiny phase is greater than 3:
        say "They have surrendered." instead;
    if the location is not Along the Brook, say "They are asleep along the brook." instead;
    if the fowling-piece is not loaded, say "Your gun is not loaded." instead;
    now the fowling-piece is not loaded;
    now the mutiny phase is 4;
    say "You come upon them sleeping. The captain and his mate fire; one of the ringleaders is killed on the spot, and the other badly wounded. You come up with your gun levelled, and the rest wake to find themselves surrounded and cry for quarter. The captain tells them he will spare their lives, if they will give him any assurance of their abhorrence of the villainy they have been guilty of, and they swear it, all of them. You bind the worst two, and keep them prisoners in your cave.";
    award 4 for the mutineers.

Instead of attacking the longboat, try breaking the longboat.
Breaking is an action applying to one thing. Understand "break [something]", "stave [something]", "stave in [something]", "hole [something]" and "sink [something]" as breaking.
Breaking it with is an action applying to two things. Understand "break [something] with [something]", "stave [something] with [something]", "stave in [something] with [something]" and "hole [something] with [something]" as breaking it with.
Carry out breaking something with something: try breaking the noun.
Carry out breaking: say "You would rather not break [the noun]."
Instead of breaking the longboat:
    if the mutiny phase is less than 4, say "Not while the seamen might hear." instead;
    if the mutiny phase is greater than 4, say "She is holed already." instead;
    if the player does not carry the axe and the player does not carry the crow, say "You need an axe or the iron crow." instead;
    now the mutiny phase is 5;
    now the mutiny clock is 4;
    say "You knock a great hole in her bottom with the axe, and take out her oars, mast, sail and rudder, so that if the ship sends men after her they may not carry her off.";
    award 2 for the longboat-marker.
The longboat-marker is a thing.

Every turn when the mutiny phase is 5:
    decrement the mutiny clock;
    if the mutiny clock is 0:
        now the mutiny phase is 6;
        say "[paragraph break]A gun booms from the ship, and her ensign goes up: a signal for the boat. No boat comes. After a while you see them hoist out another boat, and ten men put off in her, all armed. They come into the creek, find the longboat stove in, and set up a great hallooing; then they go off inland, in a body, to look for their fellows. The captain says, low, that three or four of these are honest men, and would come over if they could.".

Hallooing is an action applying to nothing. Understand "halloo", "hallo", "holla", "hollo", "shout", "call out" and "yell" as hallooing.
Carry out hallooing:
    if the mutiny phase is not 6:
        say "Your voice goes out over the island, and comes back to you from the hills. [if Poll is held]'Poor Robin Crusoe!' says Poll.[end if]" instead;
    if the location is not inland:
        say "Not here: they would see where the noise comes from. It must be done in the woods, where a voice seems to come from everywhere." instead;
    if Friday is not in the location:
        say "You need someone to answer them from another quarter: Friday." instead;
    now the mutiny phase is 7;
    say "You set Friday and the mate to halloo, and to answer the seamen whenever they halloo, from one hill to another, from one wood to another, leading them farther and farther into the island, over the brook and among the woods, until night falls and they are weary and lost and frighted. Then the captain calls to them in the dark by name, and tells them the island is held by the governor's men, fifty of them, and bids them lay down their arms. They do, every one.";
    award 4 for the halloo-marker.
The halloo-marker is a thing.

Part 3 - The ship retaken, and home

Retaking is an action applying to nothing. Understand "retake ship", "board ship", "row to ship", "take ship", "seize ship" and "attack ship" as retaking.
Check retaking:
    if the act is not 5 or the mutiny phase is less than 7, say "There is no ship for you to board." instead;
    if the location is not the Creek Mouth, say "The boats are at the creek mouth." instead.
Carry out retaking:
    if the mutiny phase is 7:
        now the mutiny phase is 8;
        say "At midnight the captain and twenty men of his, the honest ones and the frightened ones together, row out in the second boat, and the mended longboat, to the ship. You stay ashore, as governor, with Friday. From the beach you hear the fighting: a shot, a cry, a volley. Then silence. Then seven guns, the signal you agreed on: the ship is taken, and the rebel captain dead.[paragraph break]In the morning the captain comes ashore. He embraces you, and points to the ship, riding at anchor, trim and fine: 'My dear friend and deliverer,' says he, 'there's your ship, for she is all yours, and so are we, and all that belong to her.'[paragraph break]She sails for England with the tide. You have only to go aboard.";
        award 4 for the retake-marker;
    otherwise:
        leave the island.
The retake-marker is a thing.

To leave the island:
    if Friday is not in the location:
        say "You will not go without Friday." instead;
    if the player does not carry the treasure chest:
        say "Your treasure is not with you: the Spanish chest[if the treasure chest is in the Cave], still in your cave[end if]. Go aboard without it? ";
        if the player consents:
            end the story saying "You leave the island, the 19th of December 1686, after eight-and-twenty years, two months and nineteen days, with Friday and your cap and your parrot and your life, and nothing else. It is enough. It is more than enough." instead;
        say "You go back for it." instead;
    award 5 for the leave-marker;
    if Poll is held, award 2 for the poll-aboard-marker;
    if the umbrella is held, award 1 for the umbrella-aboard-marker;
    if the goatskin cap is worn, award 1 for the cap-aboard-marker;
    if the money is held, award 2 for the money;
    say "And so you leave the island, the nineteenth of December, 1686, after eight-and-twenty years, two months and nineteen days: as you find by the ship's account. You carry on board, for relics, the great goat's-skin cap you made, your umbrella, and one of your parrots; also the money, which has lain by you so long useless that it is grown rusty, or tarnished, and could hardly pass for silver till it had been a little rubbed and handled; and the Spanish gold besides.[paragraph break]Friday stands at the rail beside you, and watches the island go down into the sea, green and small, and then gone.[paragraph break]'Poor Robin Crusoe,' says Poll, from your shoulder. 'Where have you been?'";
    end the story finally saying "You have come home".
The leave-marker is a thing.
The poll-aboard-marker is a thing.
The umbrella-aboard-marker is a thing.
The cap-aboard-marker is a thing.

Volume 7 - Mornings, years and hints

To begin the fifth act:
    now the act is 5;
    say "[bold type]The Twenty-Seventh Year[roman type][paragraph break]The years go by, and they are the pleasantest of all your years on the island. Friday is a faithful, loving, sincere servant, and you love him. The Spaniard and Friday's old father have sailed for the mainland in your great boat, to fetch the Spaniard's countrymen, and you wait for their coming. Eight days go by. Then one morning, very early, Friday comes running in: 'Master, master, they are come, they are come!' But it is not they. A sail, he says, a sail, big, far off. Go up to the hill and look."


Volume 5b - The longer years

Part 1 - Seasons

[From the third year, the island has a dry season and a rainy one, turning every two days. Sowing only thrives if the seed goes in with the rains, as Crusoe learned: his first sowing, in the dry season, came to nothing.]

The wet season is a truth state that varies.
The season days is a number that varies. The season days is 2.

To turn the seasons:
    if the act is less than 3, stop;
    decrement the season days;
    if the season days is greater than 0, stop;
    now the season days is 2;
    if the wet season is true:
        now the wet season is false;
        say "[paragraph break]The rains are over. The dry season has come again: the sky is hard and blue, and the ground bakes.";
    otherwise:
        now the wet season is true;
        say "[paragraph break]The rains have come again: warm, heavy rain, day after day, and the ground drinks it in."

Part 2 - The barley field

The Barley Field is east of the Savannas. "A level piece of good black ground at the edge of the savannas, cleared of its brush, with the brook not far off. [if the field state is 0]It wants only digging to be a field.[otherwise if the field state is 1]The ground is dug, and ready for seed.[otherwise if the field state is 2]Your seed is in: green shoots are coming up in rows.[otherwise if the field state is 3]The barley stands ripe and golden, rustling in the wind.[otherwise]Stubble, where your harvest was.[end if] [if the field fenced is true]A thick hedge of stakes rings it round.[otherwise]Nothing keeps out the goats and the hares.[end if] The savannas are west.[if the wet season is true] The ground is soft with the rains.[otherwise] It is the dry season: the earth is baked hard.[end if]".
The Barley Field is inland.

The tilled ground is scenery in the Barley Field. Understand "ground", "earth", "soil", "field", "barley field" and "shoots" as the tilled ground. The description of the tilled ground is "[if the field state is 0]Good black earth, undug.[otherwise if the field state is 1]Dug ground, ready for seed.[otherwise if the field state is 2]Green shoots of barley, in rows.[otherwise if the field state is 3]Ripe barley, ready for the cutlass.[otherwise]Stubble.[end if]".

The field state is a number that varies.
The field fenced is a truth state that varies.
The field grow is a number that varies.

Instead of digging the tilled ground, try digging the ground.
Digging the ground is an action applying to nothing. Understand "dig ground", "dig field", "dig earth", "till field" and "plough field" as digging the ground.
Check digging the ground:
    if the location is not the Barley Field, say "This is no place for a field. East of the savannas there is good ground." instead;
    if the field state is not 0 and the field state is not 4, say "The ground is dug already." instead;
    if the player does not carry the spade, say "You need a spade." instead.
Carry out digging the ground:
    now the field state is 1;
    say "You dig the ground with your wooden spade, a long day's work in the sun, until it lies in dark clods ready for the seed.";
    award 1 for the tilled ground.

Sowing is an action applying to nothing. Understand "sow", "sow barley", "sow seed", "sow corn", "sow field", "sow ground", "plant barley", "plant seed" and "plant corn" as sowing.
Check sowing:
    if the location is not the Barley Field, say "You have no ground dug for seed here." instead;
    if the field state is 0 or the field state is 4, say "Dig the ground first." instead;
    if the field state is not 1, say "The seed is in already." instead;
    if the player does not carry the ears of barley, say "You have no seed corn." instead.
Carry out sowing:
    if the wet season is false:
        say "You sow your seed in the dry earth. But it is the dry season: no rain falls on it, and within a few days the seed has shrivelled in the ground and come to nothing. You have seed enough left to try again, at a better time; and you have learned something about the seasons of this island.";
    otherwise:
        now the field state is 2;
        now the field grow is 0;
        say "You sow your seed in the soft wet earth, and rake it in with a bough. With the rains upon it, it should thrive: if nothing eats it first.";
        award 2 for the ears of barley.

The fence-stakes-marker is a thing.
Hedging is an action applying to nothing. Understand "fence field", "hedge field", "make hedge", "build hedge" and "plant hedge" as hedging.
Check hedging:
    if the location is not the Barley Field, say "There is nothing here to hedge." instead;
    if the field fenced is true, say "It is hedged already." instead;
    if the player does not carry the axe, say "You need the axe, to cut stakes." instead.
Carry out hedging:
    now the field fenced is true;
    say "You cut stakes, and drive them close about the field, and weave the tops with osiers, until neither goat nor hare can get in.";
    award 2 for the fence-stakes-marker.

To field morning news:
    if the field state is 2:
        if the field fenced is false:
            now the field state is 1;
            say "[paragraph break]When you go to your barley field, the young shoots are gone: nibbled to the ground by the hares, and the goats have trodden the rest. You must sow again, and hedge it this time.";
        otherwise:
            increment the field grow;
            if the field grow is at least 2:
                now the field state is 3;
                say "[paragraph break]Your barley field, safe inside its hedge, stands ripe and golden: a real harvest, the first of many."

The baskets of grain are a thing. Understand "basket", "baskets", "grain", "harvest" and "corn" as the baskets of grain. The description of the baskets of grain is "Baskets of good barley and rice, enough seed and bread for a year."
The bundle of straw is a thing. Understand "straw" and "bundle" as the bundle of straw. The description of the bundle of straw is "A bundle of barley straw, good for thatch."
Harvesting is an action applying to nothing. Understand "harvest", "harvest field", "harvest barley", "reap field", "reap harvest" and "cut field" as harvesting.
Instead of reaping the tilled ground, try harvesting.
Check harvesting:
    if the location is not the Barley Field, say "There is nothing here to harvest." instead;
    if the field state is not 3, say "There is nothing ripe to harvest." instead;
    if the player does not carry the rusty cutlass and the player does not carry the knife, say "You need something to cut it with." instead;
    if the player does not carry the basket, say "You need something to carry the grain in." instead.
Carry out harvesting:
    now the field state is 4;
    now the player carries the baskets of grain;
    now the player carries the bundle of straw;
    say "You cut your barley with the old cutlass, for scythe, and carry the ears home in your basket, and beat out the grain, and fill basket after basket. It comes to near twenty bushels of barley, and as much rice. You will never again be afraid of wanting bread.";
    award 5 for the baskets of grain.

Part 3 - Milk and cheese

The kid penned day is a number that varies.
The pot milk is a truth state that varies.

Milking is an action applying to nothing. Understand "milk goat", "milk goats", "milk kid" and "milk flock" as milking.
Check milking:
    if the kid penned is false, say "You have no tame goats to milk." instead;
    if the goat pen is not in the location, say "Your goats are in their pen, on the savannas." instead;
    if the day is less than the kid penned day plus 2, say "Your little flock is too young yet to give milk. Give it a few days." instead;
    if the player does not carry the earthen pot, say "You have nothing to milk into." instead;
    if the pot water is true, say "Your pot is full of water. EMPTY POT first." instead;
    if the pot milk is true, say "Your pot is full of milk already." instead.
Carry out milking:
    now the pot milk is true;
    say "Your kids have grown into a little flock, and there are young ones among them. You milk the she-goats into your earthen pot: warm, sweet milk, the first you have tasted since England.";
    award 2 for the pot-milk-marker.
The pot-milk-marker is a thing.

Emptying is an action applying to one thing. Understand "empty [something]" and "pour out [something]" as emptying.
Check emptying:
    if the noun is not the earthen pot, say "That isn't something to empty." instead;
    if the pot water is false and the pot milk is false, say "It is empty." instead.
Carry out emptying:
    now the pot water is false;
    now the pot milk is false;
    say "You empty the pot on the ground."

The cheese is a thing. Understand "cheese" and "butter" as the cheese. The description of the cheese is "A round of goat's-milk cheese, made by your own hand."
Cheese-making is an action applying to nothing. Understand "make cheese", "make butter" and "churn milk" as cheese-making.
Check cheese-making:
    if the cheese is not off-stage, say "You have your cheese." instead;
    if the pot milk is false or the player does not carry the earthen pot, say "You need milk to make cheese of." instead.
Carry out cheese-making:
    now the pot milk is false;
    now the player carries the cheese;
    say "It takes you a long while and a great many tries; but at last you have butter, and a round of cheese, and are as proud as ever you were of anything.";
    award 2 for the cheese.

Part 4 - The lamp and the glittering vault

The tallow is a thing. Understand "fat" and "suet" as the tallow. The description of the tallow is "A lump of goat's tallow, from the she-goat you shot."
The hank of oakum is in the carpenter's chest. Understand "oakum", "hank", "tow" and "wick" as the hank of oakum. The description of the hank of oakum is "Loose old rope-fibre, for caulking seams: it would make a wick."

The lamp is a thing. Understand "candle" and "dish" as the lamp. The description of the lamp is "A little dish of clay, baked hard in the sun, with goat's tallow in it and a wick of oakum.[if the lamp is lit] It burns with a small, steady flame.[end if]".
Contriving is an action applying to nothing. Understand "make lamp", "make candle" and "make light" as contriving.
Check contriving:
    if the lamp is not off-stage, say "You have your lamp." instead;
    if the player does not carry the tallow, say "You would want some fat or tallow to burn." instead;
    if the player does not carry the hank of oakum, say "You would want something for a wick." instead;
    if the player does not carry the lump of clay, say "You would want a dish of clay to hold it." instead.
Carry out contriving:
    now the tallow is off-stage;
    now the hank of oakum is off-stage;
    now the lump of clay is off-stage;
    now the player carries the lamp;
    say "You shape a little dish of clay and bake it hard in the sun, and put your tallow in it, and a wick of oakum. It is not so clear as a candle, but it will give you a light in the dark.";
    award 2 for the lamp.
Lighting is an action applying to one thing. Understand "light [something]" and "kindle [something]" as lighting.
Check lighting:
    if the noun is not the lamp, say "That isn't something you can light." instead;
    if the lamp is lit, say "It is lit." instead;
    if the player does not carry the tinderbox and the fire is not in the location, say "You need a light for it: your tinderbox, or a fire." instead.
Carry out lighting:
    now the lamp is lit;
    say "You strike a spark into the tinder and light the wick. The lamp burns up small and steady."

The Glittering Vault is west of the Cavern. It is dark. "Beyond the place where the old goat lay, the cave narrows and runs on, and opens at last into a vault so high your lamp cannot find the top of it. The walls and roof throw back your little light a hundred thousand ways, as if they were set with diamonds, or precious stones, or gold. It is perfectly dry. It would be the safest magazine in the world for your powder. The way out is east."
The Glittering Vault is inland.
The glittering walls are scenery in the Glittering Vault. Understand "walls", "roof", "diamonds", "stones", "gold", "jewels", "glitter" and "lights" as the glittering walls. The description of the glittering walls is "They sparkle wonderfully in the lamplight. Whether it is diamonds, or gold, or only the damp on the rock, you cannot tell."
Instead of taking the glittering walls, say "You pick and scrape at the brightest place with your knife, and get a handful of grit, which glitters in your palm for a moment and then is only grit: the shine was nothing but the wet on the rock. You throw it down."
Instead of digging the glittering walls, try taking the glittering walls.
Instead of going west in the Cavern when the old goat is not scored, say "You dare not go deeper while those two eyes glare out of the dark."
The vault-marker is a thing.
Every turn when the location is the Glittering Vault and the player carries the lamp and the lamp is lit and the vault-marker is not scored:
    say "You stand a long while with your little lamp held up, lost in wonder. No one, in all the ages of the world, has seen this place before you.";
    award 3 for the vault-marker.

Part 5 - The mainland

Instead of going west in Cove Waters:
    say "The mainland lies somewhere over there, forty miles off, if it lies anywhere: past the currents, in a canoe, with no sail. Paddle for it anyway? ";
    if the player consents:
        end the story saying "You are never seen again";
    otherwise:
        say "You turn back to the cove."

Part 6 - Friday's father and the Spaniard

The second landing is a truth state that varies.
To start the second landing:
    now the second landing is true;
    now the landing active is true;
    move the war party to the Edge of the Wood;
    say "Very early, Friday comes running in to you, as if he flew, and calls out: 'O Master! O Master! O sorrow! O bad!' He holds up his fingers: 'One, two, three canoe! One, two, three!' They have landed on the south-west shore, below the edge of the wood, beyond the thicket; and poor Friday is dreadfully afraid they are come to look for him, and will cut him in pieces and eat him. Load your guns, and look to Friday.".
The landing active is a truth state that varies.
The Spaniard sailed is a truth state that varies.
The plan known is a truth state that varies.
A person can be revived.

The Edge of the Wood is west of the Thicket. "The trees end here, above the shore of the south-west, and a great bush grows at the very edge: from behind it you can see the whole round of sand below without being seen.[if the landing active is true] Down on the sand, one-and-twenty savages sit about a fire, with their three canoes drawn up beside them. A white man, a European, lies bound upon the sand; and in one of the canoes lies another prisoner, bound hand and foot. They are going to kill the white man now.[end if] The thicket is east; the shore is south-west."
The Cannibal Shore is southwest of the Edge of the Wood.
The Edge of the Wood is inland.
The great bush is scenery in the Edge of the Wood. Understand "bush", "tree" and "trees" as the great bush. The description of the great bush is "A thick bush, a good screen, and not above eighty yards from the savages' fire."

The war party is a man. The war party is plural-named. The war party is scenery. Understand "savages", "cannibals", "band", "party", "twenty-one savages" and "fire" as the war party. The description of the war party is "One-and-twenty of them, about the fire, and the white man bound among them."
The Spaniard is a man. Understand "white man", "european", "prisoner" and "spaniard" as the Spaniard. The description of the Spaniard is "[if the Spaniard is revived]A Spaniard, a gentleman by his manners, weak but mending[otherwise]A white man, a Spaniard by his dress, so weak and faint he can scarce stand or speak[end if]."
The old man is a man. Understand "old prisoner", "father", "friday's father", "old savage" and "canoe prisoner" as the old man. The description of the old man is "[if the old man is revived]Friday's father, a grave old man, mending every day[otherwise]An old savage, bound hand and foot, near dead with fear and the cords[end if]."

Instead of going southwest in the Edge of the Wood when the landing active is true, try going to the feast.
Instead of going south in the Western Shore when the landing active is true, try going to the feast.
Instead of going west in the Southern Cove when the landing active is true, try going to the feast.
Going to the feast is an action applying to nothing.
Carry out going to the feast:
    say "One-and-twenty of them, about the fire, and you would walk out among them. Go on? ";
    if the player consents:
        end the story saying "You are killed on the sand";
    otherwise:
        say "You draw back."

Instead of giving the pistol to Friday:
    if the pistol is not loaded, say "Load it first: he cannot load a pistol." instead;
    now Friday carries the pistol;
    say "You give Friday the loaded pistol, and show him how to point it. He takes it very gravely.";
    award 1 for the pistol.

Instead of attacking the war party, try shooting the war party.
Instead of shooting the war party:
    if the location is not the Edge of the Wood, say "You are too far off, and out in the open." instead;
    if the player does not carry the fowling-piece or the fowling-piece is not loaded, say "Your gun is not loaded, or not in your hand." instead;
    if Friday is not in the location, say "Not alone, against one-and-twenty." instead;
    if Friday does not carry the pistol, say "Friday must be armed too: give him the loaded pistol." instead;
    now the landing active is false;
    now the war party is off-stage;
    now the fowling-piece is not loaded;
    move the Spaniard to the Cannibal Shore;
    move the old man to the Cannibal Shore;
    say "'Now, Friday,' you say, 'do exactly as you see me do.' You take aim together, and fire. Friday fires his pistol a half-second after your gun. Three of them fall, and the rest leap up in the most dreadful fright, not knowing which way to run, nor where the death comes from. You break out of the bush with a great shout, and Friday after you; and they fly for the canoes, and paddle away across the sea, those that can. The shore is yours.";
    award 5 for the war party.

Instead of cutting the Spaniard, try freeing the Spaniard.
Instead of freeing the Spaniard:
    if the Spaniard is not in the location, say "He is not here." instead;
    if the landing active is true, say "Not while they are round him." instead;
    if the Spaniard is scored, say "He is free." instead;
    if the player does not carry the knife and the player does not carry the rusty cutlass, say "You have nothing to cut the cords with." instead;
    say "You cut the flags, or rushes, that bind his hands and feet. 'Christianus,' he says, very faint: he is a Spaniard. You give him your cutlass, and he takes it like a man that has been given his life.";
    award 3 for the Spaniard.
Instead of cutting the old man, try freeing the old man.
Instead of freeing the old man:
    if the old man is not in the location, say "He is not here." instead;
    if the landing active is true, say "Not while they are round him." instead;
    if the old man is scored, say "He is free." instead;
    if the player does not carry the knife and the player does not carry the rusty cutlass, say "You have nothing to cut the cords with." instead;
    say "You cut the cords of the prisoner in the canoe, and bid Friday speak to him and tell him he is safe. Friday looks at him, and then it would move anyone to tears to see him: he kisses him, embraces him, hugs him, cries, laughs, hallooes, jumps about, dances, sings, then cries again. It is a good while before he can tell you: it is his father.";
    award 4 for the old man.

Instead of giving something to the Spaniard:
    if the noun is not the flask and the noun is not the barley loaf and the noun is not the raisins and the noun is not the cheese, say "He shakes his head faintly." instead;
    if the Spaniard is revived, say "He has had enough, and thanks you." instead;
    now the Spaniard is revived;
    now the noun is off-stage;
    say "He takes it with trembling hands, and eats and drinks, and some colour comes back into his face.";
    award 1 for the Spaniard-food-marker.
Instead of giving something to the old man:
    if the noun is not the flask and the noun is not the barley loaf and the noun is not the raisins and the noun is not the cheese, say "He does not understand." instead;
    if the old man is revived, say "He has had enough." instead;
    now the old man is revived;
    now the noun is off-stage;
    say "Friday takes it from you and puts it to his father's lips himself, and chafes his arms and ankles, which are numbed with the binding, until the old man can sit up.";
    award 1 for the father-food-marker.
The Spaniard-food-marker is a thing.
The father-food-marker is a thing.
The flask is in the sea chest. Understand "flask" and "dram" as the flask. The description of the flask is "A flask of the ship's rum, kept by against some great need."

Barrow-making is an action applying to nothing. Understand "make barrow", "make hand-barrow", "build barrow", "make litter" and "carry them" as barrow-making.
Check barrow-making:
    if the Spaniard is not in the location or the old man is not in the location, say "There is no one here who needs carrying." instead;
    if the Spaniard is not scored or the old man is not scored, say "Cut them free first." instead;
    if the Spaniard is not revived or the old man is not revived, say "They are too faint to be moved yet: give them something to eat or drink." instead;
    if the player does not carry the axe, say "You need the axe to cut poles." instead.
Carry out barrow-making:
    say "You cut two poles and lash a hand-barrow between them, and you and Friday carry them home upon it, the Spaniard and the old man, resting often, all the long way round to your castle. They cannot climb your ladder; you set them down outside your wall.";
    move the Spaniard to the Hillside Plain;
    move the old man to the Hillside Plain;
    move Friday to the Hillside Plain;
    move the player to the Hillside Plain;
    award 3 for the barrow-marker.
The barrow-marker is a thing.

The hut is a thing. It is scenery. Understand "hut" and "shelter" as the hut. The description of the hut is "A snug hut of poles, thatched with barley straw, outside your wall."
Hut-building is an action applying to nothing. Understand "build hut", "make hut", "build shelter" and "thatch hut" as hut-building.
Check hut-building:
    if the location is not the Hillside Plain, say "Build it by your castle, where they are." instead;
    if the hut is not off-stage, say "The hut is built." instead;
    if the Spaniard is not in the location, say "There is no one to shelter yet." instead;
    if the player does not carry the bundle of straw, say "You need thatch: straw, from a harvest." instead;
    if the player does not carry the axe, say "You need the axe to cut poles." instead.
Carry out hut-building:
    now the hut is in the Hillside Plain;
    now the bundle of straw is off-stage;
    say "You and Friday build them a hut between your two walls, of poles, thatched with your barley straw, and lay a bed of rice straw in it and a blanket on it; and there they mend, day by day.";
    award 3 for the hut.

To Spaniard talk:
    if the hut is off-stage, say "'Gracias, señor,' he whispers. He is too weak to talk." instead;
    now the plan known is true;
    say "He is mending, and he talks with you by Friday's help, and his own little English. There are sixteen of them, he says, Spaniards and Portuguese, cast away on the mainland among Friday's people, living miserably. If you would take them in, they would all help you build a ship, and go away together, and be bound to you for ever. But there are so many mouths to feed, he says: first there must be corn enough for them all, and a boat big enough to fetch them. Then he and Friday's father could go and bring them.";
    award 1 for the plan-marker.
The plan-marker is a thing.
Instead of talking to the Spaniard, Spaniard talk.
Instead of asking the Spaniard about, Spaniard talk.
Instead of talking to the old man, say "He smiles and nods at you, and says something to Friday, who laughs."

The creek cedar is scenery in Up the Creek. Understand "cedar", "tree", "great tree" and "creek tree" as the creek cedar. The description of the creek cedar is "A great cedar, standing close by the creek, not above fifty yards from the water: big enough for a boat that would carry twenty men, and near enough the water to launch."
The great log is a thing. It is fixed in place. Understand "log", "trunk" and "great log" as the great log. The description of the great log is "The trunk of the great cedar, lying by the creek."
The big boat is a thing. It is fixed in place. Understand "boat", "big boat", "periagua" and "hull" as the big boat. The description of the big boat is "A great periagua, cut out of a single cedar, big enough to carry twenty men.[if the boat mast is true] She has a mast[otherwise] She has no mast yet[end if][if the boat sail is true], a sail[end if][if the boat rudder is true], and a rudder[end if].[if the boat dock is true] She lies in a little dock you dug for her.[end if]".
The boat mast is a truth state that varies.
The boat sail is a truth state that varies.
The boat rudder is a truth state that varies.
The boat dock is a truth state that varies.
The pieces of old sail are in the Cave. Understand "sail", "sails", "old sails", "canvas" and "pieces" as the pieces of old sail. The description of the pieces of old sail is "Pieces of the ship's old sails, which you have kept by all these years."

Instead of chopping the creek cedar:
    if the act is less than 4 or Friday is not in the location, say "It is too great a work for one man." instead;
    if the player does not carry the axe, say "You need the axe." instead;
    now the creek cedar is off-stage;
    now the great log is in Up the Creek;
    say "You and Friday fell the great cedar together, and it comes down by the creek with a noise like a gun. Friday works with a will: with his help, what would have taken you a month takes a week.".
Instead of hollowing the great log:
    if the great log is not in the location, say "There is nothing here to make a boat of." instead;
    if the player does not carry the adze, say "You need the adze." instead;
    now the great log is off-stage;
    now the big boat is in Up the Creek;
    say "Friday works as well as you with the adze, once you have shown him, and between you, in a month's hard labour, you shape the trunk into a very handsome periagua, big enough to carry twenty men.";
    award 3 for the big boat.
Mast-making is an action applying to nothing. Understand "make mast", "cut mast" and "step mast" as mast-making.
Check mast-making:
    if the big boat is not in the location, say "You have no boat here to put a mast in." instead;
    if the boat mast is true, say "She has her mast." instead;
    if the player does not carry the axe, say "You need the axe." instead.
Carry out mast-making:
    now the boat mast is true;
    say "You cut a straight young cedar for a mast, and step it in the boat.";
    award 1 for the mast-marker.
The mast-marker is a thing.
Sail-making is an action applying to nothing. Understand "make sail", "sew sail" and "rig sail" as sail-making.
Check sail-making:
    if the big boat is not in the location, say "You have no boat here to rig." instead;
    if the boat sail is true, say "She has her sail." instead;
    if the boat mast is false, say "She needs a mast first." instead;
    if the player does not carry the pieces of old sail, say "You need canvas: there are pieces of the old sails in your cave." instead.
Carry out sail-making:
    now the boat sail is true;
    now the pieces of old sail are off-stage;
    say "You cut and sew the pieces of old sail into a sail, a three-cornered ugly thing, a shoulder-of-mutton sail as they call it at home, and rig it to the mast.";
    award 1 for the sail-marker.
The sail-marker is a thing.
Rudder-making is an action applying to nothing. Understand "make rudder", "hang rudder" and "fit rudder" as rudder-making.
Check rudder-making:
    if the big boat is not in the location, say "You have no boat here." instead;
    if the boat rudder is true, say "She has her rudder." instead;
    if the player does not carry the saw, say "You need the saw." instead.
Carry out rudder-making:
    now the boat rudder is true;
    say "You saw and shape a rudder for her stern, and hang it. You are prouder of it than of the whole boat.";
    award 1 for the rudder-marker.
The rudder-marker is a thing.
Dock-digging is an action applying to nothing. Understand "dig dock" and "make dock" as dock-digging.
Check dock-digging:
    if the big boat is not in the location, say "You have no boat here." instead;
    if the boat dock is true, say "She has her dock." instead;
    if the player does not carry the spade, say "You need a spade." instead.
Carry out dock-digging:
    now the boat dock is true;
    say "You dig a little dock in the bank of the creek, and float her into it at high water, where she lies safe from the weather.";
    award 1 for the dock-marker.
The dock-marker is a thing.

Sending is an action applying to nothing. Understand "send spaniard", "send them", "send father" and "send them away" as sending.
Instead of telling the Spaniard about, try sending.
Check sending:
    if the Spaniard is off-stage, say "There is no one to send." instead;
    if the plan known is false, say "Talk with the Spaniard first." instead;
    if the big boat is off-stage or the boat mast is false or the boat sail is false or the boat rudder is false, say "There is no boat fit for the voyage yet: she wants her mast, her sail and her rudder." instead;
    if the baskets of grain is off-stage, say "There is not corn enough yet for so many mouths. Grow a harvest first." instead;
    if the Spaniard is not in the location, say "The Spaniard is at your castle." instead.
Carry out sending:
    now the Spaniard sailed is true;
    now the Spaniard is off-stage;
    now the old man is off-stage;
    now the big boat is off-stage;
    now the baskets of grain are off-stage;
    say "You give them each a musket, with powder and ball, and bread and raisins enough for many days, and your baskets of corn to keep them all; and make the Spaniard swear to bring back none who will not swear to be true to you. With a fair wind and the full moon, Friday's father and the Spaniard sail away in your great boat for the mainland. Friday watches till the sail is gone, and then goes about his work very quiet.";
    award 5 for the Spaniard sailed-marker.
The Spaniard sailed-marker is a thing.

Part 7 - The five left behind

The five mutineers are a man. The five mutineers are plural-named. Understand "five", "mutineers", "prisoners", "rogues" and "five mutineers" as the five mutineers. The description of the five mutineers is "The five worst of the mutineers, bound: the captain would hang them in England. They are to stay on the island instead."
Every turn when the mutiny phase is 8 and the five mutineers are off-stage:
    move the five mutineers to the Creek Mouth.
The island-lore-marker is a thing.
Instead of talking to the five mutineers:
    if the island-lore-marker is scored, say "They have heard all you can tell them." instead;
    say "Since they are to stay, you tell them the whole story of the place, and how you came to it: you show them your fortifications, the way you make your bread, plant your corn, cure your grapes; how to tame the goats and milk them, and make butter and cheese. You tell them of the sixteen Spaniards who are to come, and leave a letter for them, and make the rogues promise to treat them well. You leave them your firearms, your tools, and the island.";
    award 3 for the island-lore-marker.
Instead of asking the five mutineers about, try talking to the five mutineers.
Does the player mean talking to the five mutineers: it is very likely.

Volume 7b - Which savage

Does the player mean attacking the first savage: it is very likely.
Does the player mean shooting the second savage: it is very likely.
Does the player mean attacking the captive: it is very unlikely.
Does the player mean shooting the captive: it is very unlikely.
Does the player mean naming the captive: it is very likely.

Does the player mean taking the treasure chest: it is very likely.

Volume 9 - Last of all

[The general BUILD line comes last, so that the particular ones (BUILD RAFT and the rest) are tried first.]
Building is an action applying to one topic. Understand "build [text]", "make [text]", "construct [text]", "weave [text]" and "carve [text]" as building.
Carry out building:
    say "You turn the notion of making [the topic understood] over in your mind, but can see neither how nor why to set about it here."
