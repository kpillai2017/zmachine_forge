"The Glasshouse Bequest" by K. Pillai

[An I7-lite story for zforge. Your great-aunt Ottoline Marsh, botanist,
 explorer and practical joker, has left you Marsh Hall and a riddle.
 Garden: Front Garden, Glasshouse, Palm Walk, Sunken Garden.
 House (eight rooms): Hall, Library, Dining Room, Kitchen; Landing, Study,
 Bedroom, Attic.]

The story headline is "An inheritance in eight rooms".
Use scoring. The maximum score is 8.

When play begins:
	say "The solicitor's letter is soft from being read too often. [italic type]'...and to my great-niece or -nephew, whichever of you has the patience, I leave Marsh Hall and everything in it. The treasure lies where the house keeps its heart. Do mind the Duchess. -- O.M.'[roman type][paragraph break]The taxi's tail-lights have long since dwindled down the lane. Now there is only the house, the garden breathing around it in the warm dusk, and you."

A room can be outdoor.
A thing can be scored.
A room can be scored.

Every turn when the location is outdoor and a random chance of 1 in 3 succeeds:
	say "[one of]Somewhere in the leaves, a bird with a voice like a rusty hinge asks a question and gets no answer.[or]A warm breath of wind moves through the garden, and every leaf in it seems to turn and look at you.[or]A moth the size of your palm blunders past, dusty and enormous.[or]Far off, a clock that isn't a clock -- a frog, perhaps -- ticks twice and stops.[at random]"

Part 1 - The Garden

The Front Garden is a room. "Marsh Hall rises in front of you to the north: two storeys of honey-coloured stone, shuttered and silent, its windows reflecting nothing but the last of the light. The front door is set deep in a porch smothered with jasmine, with a worn doormat before it and a terracotta flowerpot standing guard beside it. A gravel path runs west towards the glint of a glasshouse and east beneath a colonnade of palms. The garden gate, and the long lane back to the world, lie south."
The Front Garden is outdoor.

Instead of going south in the Front Garden, say "You have come a very long way to stand in this garden. Turning back now would be a poor sort of beginning."

The doormat is scenery in the Front Garden. Understand "mat" as the doormat. The description of the doormat is "A coir mat, worn bald in the middle. Once it said WELCOME; now it says only ELCO, which is less reassuring."
The terracotta flowerpot is scenery in the Front Garden. Understand "pot" as the flowerpot. The description of the flowerpot is "A fat terracotta pot beside the door, home to a geranium that has given up. It is exactly where every burglar in England would look first for a spare key."
The jasmine is scenery in the Front Garden. Understand "porch" as the jasmine. The description of the jasmine is "The scent is so thick it is almost a colour."

The rusty spare key is a thing. The description of the rusty spare key is "An old iron key, orange with rust. A cardboard tag is tied to its bow."

The front door is a door. It is north of the Front Garden and south of the Hall. The front door is locked. The front door is scenery. The description of the front door is "Oak, iron-studded, with a keyhole big enough to post a letter through[if the front door is locked]. It is firmly locked[end if]."

The Glasshouse is west of the Front Garden. "The air in here is hot, wet and green, like breathing through a flannel. Panes of old glass, fogged and beaded, arch overhead. Orchids cling to rafters; ferns uncurl like question marks. And in the middle of it all, in a great copper tub, stands the Duchess. The only way out is east."
The Glasshouse is outdoor.

The Duchess is scenery in the Glasshouse. Understand "plant", "pitcher plant", "giant" and "nepenthes" as the Duchess. The description of the Duchess is "A pitcher plant grown to the size of a wardrobe. Her leaves end in long green-and-crimson pitchers, lidded like ewers, and the largest of them hangs open at chest height[if the small brass key is in the pitcher]. At the bottom of its throat, in an inch of glistening fluid, something brass catches the light[end if]. A card pinned to the tub reads: NEPENTHES 'THE DUCHESS'. DOES NOT CARE FOR FINGERS."
The pitcher is an open container in the Glasshouse. It is scenery. Understand "throat" and "fluid" as the pitcher. The description of the pitcher is "A crimson-veined throat, deep as your forearm is long, slick with something that smells of honey and old pennies[if the small brass key is in the pitcher]. A small brass key lies at the bottom[end if]."
The small brass key is in the pitcher. The small brass key unlocks the front door. Understand "front key" as the small brass key. The description of the small brass key is "A small brass key, still a little sticky. The Duchess has been guarding it for you."

The trowel is in the Glasshouse. The description of the trowel is "A gardener's trowel, its handle polished by years of Aunt Ottoline's grip. It looks as though it has buried a great many things, none of them treasure."

The sting count is a number that varies. The sting count is 0.

Instead of taking the small brass key when the small brass key is in the pitcher:
	increase the sting count by 1;
	if the sting count is 1:
		say "You reach into the pitcher. The fluid is warm, and then it is very much more than warm. The lid of the pitcher drops shut on your wrist with a wet little clap and you tear your hand free, fingers stinging as though you had plunged them into nettles. Your hand has come out empty. The Duchess, it seems, does not care for fingers.";
	otherwise:
		say "Your fingers remember the last time, even if you don't. The Duchess's lid trembles hopefully. You think better of it."

Instead of inserting the bamboo cane into the pitcher:
	if the small brass key is in the pitcher:
		now the player carries the small brass key;
		say "You lower the cane into the pitcher, the Duchess's lid twitching as you do. Probing about, you find the key's ring with the cane's crooked end and, slowly, slowly, draw it up out of the fluid and into your hand. The Duchess sulks.";
		if the small brass key is not scored:
			now the small brass key is scored;
			increase the score by 1;
	otherwise:
		say "You stir the pitcher's fluid with the cane. Nothing else is in there, and the Duchess seems to find the attention impertinent."

Instead of inserting something into the pitcher, say "You'd rather not feed the Duchess anything you might want back."

The Palm Walk is east of the Front Garden. "Palms march along this path in two stately ranks, their trunks shaggy, their crowns rattling softly overhead. Banana plants lean in between them with leaves like torn green flags. The path returns west to the front of the house; to the north, steps go down into a sunken garden."
The Palm Walk is outdoor.

The banana plants are scenery in the Palm Walk. Understand "banana", "bananas", "palms" and "palm" as the banana plants. The description of the banana plants is "The banana plants are propped up with canes, as though they had been out late and needed help getting home."
The bamboo cane is in the Palm Walk. The initial appearance of the bamboo cane is "One of the banana plants has shrugged off its prop: a long bamboo cane, hooked at one end, lies on the path." Understand "stick" and "prop" as the bamboo cane. The description of the bamboo cane is "A bamboo cane as long as you are tall, with a crook at the far end where it once hooked around a banana stem."

The coconut is in the Palm Walk. The description of the coconut is "A coconut. Someone has painted a face on it, with an expression of patient disappointment. You feel it has been waiting for you, and that you have let it down already."

The Sunken Garden is north of the Palm Walk. "Stone steps lead down into a square of lawn enclosed by clipped yew. Great flowerbeds of orange marigolds and blue salvia run this way and that across it, in no pattern you can make out from down here. In the centre stands a sundial on a mossy pedestal. Steps go back up to the south."
The Sunken Garden is outdoor.

The flowerbeds are scenery in the Sunken Garden. Understand "beds", "marigolds", "salvia" and "flowers" as the flowerbeds. The description of the flowerbeds is "Bold stripes and angles of blue salvia cut through the marigolds. It's gaudy, deliberate and, from where you stand, completely meaningless. Some gardens, Aunt Ottoline used to say, are meant to be seen the way birds see them."
The sundial is scenery in the Sunken Garden. Understand "pedestal" and "dial" as the sundial. The description of the sundial is "A bronze sundial, green with age. Around its rim is engraved: I COUNT NONE BUT THE SUNNY HOURS. The gnomon's shadow points nowhere useful: the sun has already gone."

Looking under is an action applying to one thing. Understand "look under [something]", "lift [something]" and "search [something]" as looking under.
Instead of looking under something, say "You find nothing there but a little dust and a great deal of disappointment."
Instead of looking under the doormat, say "You lift a corner of the mat. A woodlouse regards you with the tired look of someone who gets asked this a lot. There is nothing else."
Instead of looking under the flowerpot:
	if the rusty spare key is not handled:
		now the rusty spare key is handled;
		now the player carries the rusty spare key;
		say "You tip the pot. Beneath it, pressed into the soil, is a rusty iron key, which you pocket with the small glow of a detective who has read the right books.";
	otherwise:
		say "Just soil, and the ghost of a key-shaped hollow."

A thing can be handled.
A thing can be revealed.

Moving is an action applying to one thing. Understand "move [something]", "push [something]", "pull [something]", "shift [something]" and "look behind [something]" as moving.
Instead of moving something, say "You shove [the noun] about a little, to no useful end."

Digging is an action applying to one thing. Understand "dig [something]" and "dig in [something]" as digging.
Instead of digging something:
	if the player does not carry the trowel:
		say "With your bare hands? You'd want at least a trowel.";
	otherwise if the noun is the sundial or the noun is the flowerbeds:
		say "You dig about at the foot of the sundial until your nails are black and the yew hedge seems to be watching you disapprovingly. There is nothing buried here. Aunt Ottoline was never a woman to bury things where people would think to dig.";
	otherwise:
		say "That's not a sensible thing to dig."

Drinking is an action applying to one thing. Understand "drink [something]", "sip [something]" and "taste [something]" as drinking.
Instead of drinking something, say "That's not something you can drink."

Turning is an action applying to one thing. Understand "turn [something]", "set [something]" and "adjust [something]" as turning.
Instead of turning something, say "Turning [the noun] achieves nothing."

Winding is an action applying to one thing. Understand "wind [something]" and "wind up [something]" as winding.
Instead of winding something, say "That isn't something that winds."

Instead of unlocking the front door with the rusty spare key, say "The rusty key slides into the lock with promising ease, and then refuses, absolutely, to turn. You notice for the first time the words on its cardboard tag, in Aunt Ottoline's looping hand: [italic type]Not so easy, dear.[roman type]".

Part 2 - The Ground Floor

A room is usually lit.

The Hall is a room. "A tall, cool hall, floored in black and white marble like a chessboard waiting for pieces. Framed pressed flowers climb the walls in ranks. A broad staircase curves up into shadow. Doorways lead west, into a library, and east, to a dining room; the front door is back to the south.[paragraph break]Against the stairs stands a grandfather clock, taller than a man, [if the grandfather clock is open]its long case standing open[otherwise if the grandfather clock is wound]ticking deep and slow[otherwise]its pendulum still[end if]."

The pressed flowers are scenery in the Hall. Understand "frames" and "pictures" as the pressed flowers. The description of the pressed flowers is "Hundreds of them, each labelled in the same looping hand: where found, when, and occasionally a short remark such as 'nearly died getting this one' or 'Borneo -- never again'."
The staircase is scenery in the Hall. Understand "stairs" as the staircase. The description of the staircase is "Mahogany banisters, worn smooth by a century of hands."

The grandfather clock is a closed container in the Hall. It is scenery. It is unopenable. Understand "clock", "case", "hands", "face", "dial" and "pendulum" as the grandfather clock.
The grandfather clock can be wound.
The clock hour is a number that varies. The clock hour is 4.
The description of the grandfather clock is "A long-case clock in dark walnut, its face painted with a ring of flowers in place of numbers -- though small Roman numerals peep between the petals. The hands stand at [clock hour in words] o'clock. [if the grandfather clock is wound]It ticks, deep and patient, like a heart[otherwise]It is silent: someone has let it run down. Below the face is a small winding hole[end if].[if the grandfather clock is open] The case stands open.[end if]".

Instead of opening the grandfather clock, say "The case has no handle and no keyhole. It must open by some mechanism of its own."

Instead of winding the grandfather clock:
	if the grandfather clock is wound:
		say "It is already wound, and ticking.";
	otherwise if the player does not carry the winding key:
		say "There is a winding hole below the face, but you have nothing to wind it with.";
	otherwise:
		now the grandfather clock is wound;
		say "You fit the winding key into the hole and turn it. Something deep in the case clicks, catches, and then the pendulum stirs and the clock begins to tick: slow, deep and patient, like a heart.";
		test the clock.

Instead of turning the grandfather clock:
	increase the clock hour by 1;
	if the clock hour is greater than 12:
		now the clock hour is 1;
	say "You push the minute hand round a full circle. The hour hand creeps on to [clock hour in words].";
	test the clock.

To test the clock:
	if the grandfather clock is wound and the clock hour is 9 and the grandfather clock is not open:
		now the grandfather clock is open;
		move the small silver key to the grandfather clock;
		increase the score by 1;
		say "[line break]The clock draws a long breath of cogs and begins to strike. One. Two. Three... you count them, not breathing, all the way to nine. On the ninth stroke the long case swings open with a sigh, as if it had been waiting years to be asked. Hanging inside on a hook is a small silver key."

The small silver key is a thing. Understand "tag" as the small silver key. The description of the small silver key is "A tiny silver key, finely made. A tag on a ribbon reads: [italic type]Where the house keeps its heart.[roman type]".

The Library is west of the Hall. "Shelves climb from floor to ceiling, crammed with books that smell of dust, leather and far-off places. A library ladder leans against the stacks, and a reading chair sits turned towards the shuttered window as though its owner had only just stepped out. The way out is east."
The Library is dark.

The shelves are scenery in the Library. Understand "books", "stacks" and "bookshelves" as the shelves. The description of the shelves is "Botany, mostly, and travel; a great many diaries; and a single row of adventure novels, as if kept for emergencies. Two volumes stick out a little from the rest: a battered copy of [italic type]Treasure Island[roman type] and a fat green book called [italic type]The Flora of the Spice Islands[roman type]."
The reading chair is scenery in the Library. Understand "chair" as the reading chair.
The library ladder is scenery in the Library. The description of the library ladder is "A ladder on a brass rail, for reaching the higher shelves -- and, to judge by the scuffs, for Aunt Ottoline to ride along them at speed." The description of the reading chair is "Deep, button-backed, and moulded to the shape of someone who is no longer there."
Treasure Island is in the Library. It is proper-named. Understand "novel", "stevenson" and "copy" as Treasure Island. The description of Treasure Island is "Stevenson's classic, read almost to pieces. Someone has underlined, heavily, the words [italic type]X marks the spot[roman type]. Beside them, in the margin, in looping pencil: [italic type]Not in this house, dear. Try the flowers.[roman type]".
The botany book is in the Library. The printed name of the botany book is "Flora of the Spice Islands". The botany book is proper-named. Understand "flora", "spice", "islands" and "green" as the botany book. The description of the botany book is "A heavy green volume with gold lettering: [italic type]The Flora of the Spice Islands, Vol. II[roman type]. It falls open by habit at a pressed specimen of Nepenthes, with a note in the margin: [italic type]Opens at dusk. Mine, rather later.[roman type]".

After examining the botany book when the botany book is not scored:
	now the botany book is scored;
	now the winding key is in the Library;
	increase the score by 1;
	say "As you turn the pages, something slips from between them and drops to the floor with a small metallic ring: a brass winding key."

The winding key is a thing. Understand "brass winding key" as the winding key. The description of the winding key is "A brass key with a square socket instead of teeth -- a clock key."

Rule for printing the description of a dark room when the location is the Library:
	say "It is pitch dark. You can smell old paper and older leather, and somewhere nearby something creaks on a brass rail, but you can see nothing at all. The doorway back to the hall is a faint grey shape to the east."

Rule for printing a parser error when the latest parser error is the can't see any such thing error and the location is the Library and in darkness:
	say "[one of]You grope about in the dark and set a ladder rolling along its rail with a noise like a train. You stand very still until it stops.[or]Your hand closes on a book, which you drop, which knocks over another, which knocks over several more. The darkness fills with the sound of literature falling.[or]You barge into something upholstered and nearly go over.[cycling] It's far too dark in here: you'll need a light."

The Dining Room is east of the Hall. "A long table runs the length of the room under a dust sheet, like a sleeping animal. Twelve chairs stand at attention around it. A mahogany sideboard fills one wall, and a silver candelabrum presides over it. A doorway leads north to the kitchen; the hall is back to the west."

The long table is scenery in the Dining Room. Understand "dust sheet" and "sheet" as the long table. The description of the long table is "Under the sheet the table is laid for twelve, as though for a dinner that never happened. The napkins have been folded into the shapes of orchids."
The sideboard is a closed openable container in the Dining Room. It is scenery. Understand "drawer" and "mahogany" as the sideboard. The description of the sideboard is "Heavy, dark and heavily carved with twining leaves. It has one long drawer[if the sideboard is open], which stands open[end if][if the sideboard is open and the box of matches is in the sideboard]. Inside lies a box of matches[end if]."
The box of matches is a thing. Understand "match" and "matchbox" as the box of matches. The description of the box of matches is "A box of Swan Vestas, rattling pleasingly."
The silver candelabrum is scenery in the Dining Room. Understand "candelabra" and "candlestick" as the candelabrum. The description of the candelabrum is "Five silver branches, no candles. It holds nothing but a faint smell of old dinners."
The decanter is in the Dining Room. The initial appearance of the decanter is "On the sideboard stands a cut-glass decanter, half full of port." Understand "port" and "cut-glass" as the decanter. The description of the decanter is "A cut-glass decanter, half full of port the colour of old garnets. You lift the stopper: it smells rich and plummy and, underneath, faintly and oddly of bitter almonds."

Instead of drinking the decanter:
	say "You pour yourself a small glass -- surely the heir is entitled -- and drink it down. It is very good port. It is very good port for about four seconds, and then the room tilts gently to one side and the dust sheet rises up to meet you. The last thing you remember is thinking that bitter almonds, in the detective stories, never mean anything good.";
	end the story saying "You have been poisoned".

The Kitchen is north of the Dining Room. "A stone-flagged kitchen with a black range, cold for years, and a scrubbed pine table. Copper pans hang from a rack. Bunches of dried herbs dangle from the beams like the leavings of a very tidy witch. The only way out is south."

The range is scenery in the Kitchen. Understand "stove" as the range. The description of the range is "Black iron, cold as a tombstone."
The copper pans are scenery in the Kitchen. Understand "pan", "rack" and "herbs" as the copper pans. The description of the copper pans is "Polished, hung by size, never used. Aunt Ottoline cooked, if at all, on a spirit stove in a tent."
The pine table is scenery in the Kitchen. The description of the pine table is "Scrubbed pale with years of scrubbing."
The oil lamp is a device in the Kitchen. The initial appearance of the oil lamp is "An old brass oil lamp stands on the pine table, as if waiting for someone to need it." Understand "lantern" and "lamp" as the oil lamp. The oil lamp can be lit or unlit. The description of the oil lamp is "A brass oil lamp with a glass chimney[if the oil lamp is switched on], burning with a steady golden flame[otherwise]. Its wick is dry but full of oil[end if]."
The jar of honey is in the Kitchen. The initial appearance of the jar of honey is "Beside it sits a jar of honey, gone hard and golden." Understand "jar" as the jar of honey. The description of the jar of honey is "A jar of honey with a handwritten label: GLASSHOUSE BEES, 1987. It has set into something like amber."

Instead of switching on the oil lamp when the player does not carry the box of matches, say "The lamp has no switch: it wants lighting, and you have nothing to light it with."
Understand "light [something]" as switching on.
Carry out switching on the oil lamp:
	now the oil lamp is lit.
After switching on the oil lamp:
	if the oil lamp is not scored:
		now the oil lamp is scored;
		increase the score by 1;
	say "You strike a match and touch it to the wick. The flame gutters, steadies, and swells into a warm golden light."
Carry out switching off the oil lamp:
	now the oil lamp is unlit.

Before going north in the Front Garden when the front door is open and the Hall is not scored:
	now the Hall is scored;
	increase the score by 1.

Part 3 - The Upper Floor

The Landing is above the Hall. "A gallery runs around the top of the stairs, hung with maps whose coastlines have been corrected in pencil. Doors open west, into a study, and east, into a bedroom. A narrow ladder climbs to a hatch in the ceiling. The stairs curve back down."

The maps are scenery in the Landing. Understand "map" and "coastlines" as the maps. The description of the maps is "Admiralty charts of seas you have never heard of, annotated in pencil: 'Wrong.' 'Also wrong.' 'Crocodiles.'".
The loft ladder is scenery in the Landing. Understand "ladder" and "hatch" as the loft ladder. The description of the loft ladder is "A narrow wooden ladder up to a hatch, which stands open on the dark of the roof."

The Study is west of the Landing. "Aunt Ottoline's study is a nest of papers, specimen jars and pinned butterflies. A roll-top desk, buried under correspondence, faces the window. Above a wide stone fireplace hangs her portrait, and the fireplace itself -- the hearth -- is swept clean, as though it were kept for something better than fires. The landing is east."

The roll-top desk is scenery in the Study. Understand "desk", "papers" and "correspondence" as the roll-top desk. The description of the roll-top desk is "Bills, seed catalogues and letters from learned societies, most of them beginning 'Dear Miss Marsh, we regret...'. Nothing of use."
The specimen jars are scenery in the Study. Understand "jars", "butterflies" and "specimens" as the specimen jars. The description of the specimen jars is "Things in spirits. You decide not to look too closely at the one that seems to be looking back."
The portrait is scenery in the Study. Understand "painting" and "picture" as the portrait. The description of the portrait is "Aunt Ottoline in a pith helmet, one foot on a rock, painted with the expression of a woman who knows exactly where you are about to look."
The wall safe is a container. It is open. It is fixed in place. The description of the wall safe is "A small steel safe set into the wall, its door hanging open. It is empty but for a card."
The white card is in the wall safe. The description of the white card is "In looping ink: [italic type]Too obvious, my dear. -- O.M.[roman type]".

Instead of moving the portrait:
	if the wall safe is in the Study:
		say "You've already found everything the portrait has to hide, which is to say: nothing.";
	otherwise:
		move the wall safe to the Study;
		say "You lift the portrait off its hook. Behind it, set into the wall, is a steel safe -- and your heart gives a lurch, because its door is already standing open. There is nothing inside but a white card.";
Instead of taking the portrait, try moving the portrait.

The hearth is scenery in the Study. Understand "fireplace", "grate" and "chimney" as the hearth. The description of the hearth is "A deep stone hearth, swept spotless. Low in its back wall, where a fire would usually hide it, is a small iron door, blackened and square[if the iron door is open], standing open[end if]."
The iron door is a closed openable locked lockable container in the Study. It is scenery. Understand "little door" as the iron door. The small silver key unlocks the iron door. The description of the iron door is "An iron door no bigger than a book, with a tiny, delicate keyhole quite out of keeping with the rest of it[if the iron door is open]. It stands open[end if]."
The Marsh Sapphire is a thing. Understand "sapphire", "jewel", "gem", "stone" and "treasure" as the Marsh Sapphire. The description of the Marsh Sapphire is "A sapphire the size of a pigeon's egg, blue as the salvia in the garden and deeper than any sea on the landing's maps."

After taking the Marsh Sapphire:
	increase the score by 2;
	say "You reach into the heart of the house and close your hand around something cool, heavy and faceted. When you draw it out into the light it blazes: a sapphire the size of a pigeon's egg, blue as the salvia in the garden. Tucked beneath it is a last card: [italic type]Well done. The house is yours; mind the Duchess, and water her on Thursdays. -- O.M.[roman type]";
	end the story finally saying "You have found the Marsh Sapphire".

The Bedroom is east of the Landing. "A high, airy bedroom, all faded chintz. The four-poster bed has its curtains drawn back. On the dressing table, beside a looking glass, sits a lacquered jewellery box. The landing is west."

The four-poster bed is scenery in the Bedroom. Understand "bed" and "curtains" as the four-poster bed. The description of the four-poster bed is "Made up with military neatness. On the pillow, instead of a mint, a pressed violet."
The dressing table is scenery in the Bedroom. Understand "looking glass" and "mirror" as the dressing table. The description of the dressing table is "Your own reflection looks back from the glass, rather dustier and more determined than you expected."
The jewellery box is an open container in the Bedroom. It is scenery. Understand "lacquered" and "box" as the jewellery box. The description of the jewellery box is "Black lacquer, painted with golden cranes[if the emerald necklace is in the jewellery box]. Coiled inside it, glinting green, is an emerald necklace[end if]."
The emerald necklace is in the jewellery box. Understand "emeralds" and "necklace" as the emerald necklace. The description of the emerald necklace is "A necklace of emeralds, green as the Glasshouse. For a moment your pulse quickens. Then you hold it to the light, and the stones are a little too bright and a little too even, and there on the clasp is a tiny paper tag: [italic type]Paste. Keep looking. -- O.[roman type]".

The Attic is above the Landing. "A long, low attic under the slates, hot and dry and smelling of old wood. At the west end, under a skylight, a brass telescope stands on a tripod, aimed down at the garden. The floorboards toward the east end are dark and spongy with rot; someone has drawn a chalk skull on them, which seems theatrical even for Aunt Ottoline. The hatch leads down."
The Attic is lit.

The rotten boards are scenery in the Attic. Understand "floorboards", "floor", "skull" and "chalk" as the rotten boards. The description of the rotten boards is "Dark, soft, sagging. The chalk skull grins up at you. Beyond it, at the far east end, you can just make out an old sea chest."
The sea chest is scenery in the Attic. Understand "chest" as the sea chest. The description of the sea chest is "An old sea chest, banded with brass, stencilled O.M. -- tantalisingly out of reach beyond the rotten boards."

Instead of going east in the Attic:
	say "Surely a chalk skull is just Aunt Ottoline's sense of humour. You step out onto the boards towards the sea chest. The first one holds. The second one groans. The third one simply is not there any more, and neither is the floor, nor the landing below it, and the marble chessboard of the Hall comes up to meet you with great speed and no sense of humour at all.";
	end the story saying "You have fallen through the floor".
Instead of taking the sea chest, try going east.
Instead of opening the sea chest, try going east.

The brass telescope is scenery in the Attic. Understand "telescope", "eyepiece" and "tripod" as the brass telescope.
Understand "look through [something]", "look in [something]" and "use [something]" as examining.
The description of the brass telescope is "You put your eye to the eyepiece. The garden swims up at you, huge and green and gold in the dusk: the palms, the glasshouse roof, and then the Sunken Garden -- where the flowerbeds, so meaningless from the lawn, resolve from up here into two enormous letters picked out in blue salvia against the orange marigolds: [bold type]I X[roman type].[paragraph break]Nine."
After examining the brass telescope when the brass telescope is not scored:
	now the brass telescope is scored;
	increase the score by 1;
	continue the action.

After opening the sideboard:
	if the box of matches is not revealed:
		now the box of matches is revealed;
		move the box of matches to the sideboard;
		say "You pull open the long drawer. Inside, among the napkin rings, lies a box of matches.";
	otherwise:
		continue the action.

After opening the iron door:
	if the Marsh Sapphire is not revealed:
		now the Marsh Sapphire is revealed;
		move the Marsh Sapphire to the iron door;
		say "The little iron door swings open on a cavity in the chimney breast. Something inside catches the light and gives it back, deep and blue.";
	otherwise:
		continue the action.
