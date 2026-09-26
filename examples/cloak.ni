"Cloak of Darkness" by Roger Firth

[The classic interactive fiction demonstration (Roger Firth, 1999), written
 for I7-lite. The same story as examples/cloak.zil, told in Inform 7.]

The story headline is "A basic IF demonstration".
Use scoring. The maximum score is 2.

When play begins:
	say "Hurrying through the rainswept November night, you're glad to see the bright lights of the Opera House. It's surprising that there aren't more people about but, hey, what do you expect in a cheap demo game...?"

Part 1 - The Foyer

The Foyer of the Opera House is a room. "You are standing in a spacious hall, splendidly decorated in red and gold, with glittering chandeliers overhead. The entrance from the street is to the north, and there are doorways south and west."

Instead of going north in the Foyer, say "You've only just arrived, and besides, the weather outside seems to be getting worse."

Part 2 - The Cloakroom

The Cloakroom is west of the Foyer. "The walls of this small room were clearly once lined with hooks, though now only one remains. The exit is a door to the east."

The small brass hook is a scenery supporter in the Cloakroom. Understand "peg" as the hook.
The description of the hook is "It's just a small brass hook, [if the cloak is on the hook]with a cloak hanging on it[otherwise]screwed to the wall[end if]."

Part 3 - The Bar

The Bar is south of the Foyer. "The bar, much rougher than you'd have guessed after the opulence of the foyer to the north, is completely empty. There seems to be some sort of message scrawled in the sawdust on the floor."
The Bar is dark.

The scrawled message is scenery in the Bar. Understand "floor" and "sawdust" as the message.

The disturbance count is a number that varies. The disturbance count is 0.

Before going in the Bar when in darkness:
	if the noun is not north:
		increase the disturbance count by 2;
		say "Blundering around in the dark isn't a good idea!" instead.

Before doing something other than going or looking in the Bar when in darkness:
	increase the disturbance count by 1;
	say "In the dark? You could easily disturb something!" instead.

Instead of examining the scrawled message:
	if the disturbance count is less than 2:
		increase the score by 1;
		say "The message, neatly marked in the sawdust, reads...";
		end the story finally saying "You have won";
	otherwise:
		say "The message has been carelessly trampled, making it difficult to read. You can just distinguish the words...";
		end the story saying "You have lost".

Part 4 - The cloak

The player wears a velvet cloak. Understand "dark", "black" and "satin" as the cloak.
The description of the cloak is "A handsome cloak, of velvet trimmed with satin, and slightly spattered with raindrops. Its blackness is so deep that it almost seems to suck light from the room."
The velvet cloak can be scored.

[The Bar is dark while the cloak is with the player.]
Carry out putting the cloak on the hook: now the Bar is lit.
Carry out dropping the cloak: now the Bar is lit.
Carry out taking the cloak: now the Bar is dark.

Carry out putting the cloak on the hook when the cloak is not scored:
	now the cloak is scored;
	increase the score by 1.

Instead of dropping the cloak when the player is not in the Cloakroom, say "This isn't the best place to leave a smart cloak lying around."
Instead of putting the cloak on something when the player is not in the Cloakroom, say "This isn't the best place to leave a smart cloak lying around."
