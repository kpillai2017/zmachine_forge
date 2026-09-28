"zforge/lib/i7/world.zil - light, darkness, doors and moving about.

 (Describing a room is the looking action's job: lib/i7/standard.zil.)

 A room is lit if it has LITBIT (the compiler sets it unless the source
 says the room is dark), or if a lit thing is in it or carried by the
 player (one level deep, like the parser's scope)."

<PROPDEF DESCRIPTION 0>
<PROPDEF INITIAL-APPEARANCE 0>

;"A door is in two rooms at once in Inform 7, but a ZIL object has one
  parent. So a door (listed in the compiler's DOORS table) is moved into
  whichever of its two rooms (SIDE-A, SIDE-B) the player arrives in."
<PROPDEF SIDE-A 0>
<PROPDEF SIDE-B 0>
<PROPDEF WITH-KEY 0>                   ;"what locks and unlocks it"

;"The room on the far side of DOOR from where the player is."
<ROUTINE OTHER-SIDE (DOOR)
    <COND (<EQUAL? <GETP .DOOR ,P?SIDE-A> ,HERE> <GETP .DOOR ,P?SIDE-B>)
          (ELSE <GETP .DOOR ,P?SIDE-A>)>>

;"After the player moves: bring each door of this room here, so it can be
  seen and opened from this side."
<ROUTINE PLACE-DOORS ("AUX" N D)
    <SET N <GET ,DOORS 0>>
    <DO (I 1 .N)
        <SET D <GET ,DOORS .I>>
        <COND (<EQUAL? ,HERE <GETP .D ,P?SIDE-A> <GETP .D ,P?SIDE-B>> <MOVE .D ,HERE>)>>>

;"Is there light where the player is? (See the top of this file.)"
<ROUTINE LIGHT-HERE? ()
    <COND (<FSET? ,HERE ,LITBIT> <RTRUE>)
          (<HAS-LIGHT? ,HERE> <RTRUE>)
          (<HAS-LIGHT? ,PLAYER> <RTRUE>)>
    <RFALSE>>

;"Does anything directly inside PARENT give light? One level only."
<ROUTINE HAS-LIGHT? (PARENT)
    <MAP-CONTENTS (O .PARENT)
        <COND (<FSET? .O ,LITBIT> <RTRUE>)>>
    <RFALSE>>

;"Is O described by its own initial appearance paragraph? Only until it
  is first picked up (HANDLEDBIT), as in Inform 7."
<ROUTINE SHOWS-INITIAL? (O)
    <AND <NOT <FSET? .O ,HANDLEDBIT>> <GETP .O ,P?INITIAL-APPEARANCE>
         <NOT <EQUAL? .O ,PLAYER>>>>

;"Would a room description mention O at all? Not scenery or the player."
<ROUTINE VISIBLE-THING? (O)
    <IFFLAG (PARTS <COND (<FSET? .O ,PARTBIT> <RFALSE>)>) (ELSE)>   ;"parts: not listed"
    <NOT <OR <FSET? .O ,SCENERYBIT> <EQUAL? .O ,PLAYER>>>>

;"Does O go in the room's you-can-also-see list? Not if it has already
  had a paragraph of its own."
<ROUTINE LISTED-HERE? (O)
    <AND <VISIBLE-THING? .O> <NOT <SHOWS-INITIAL? .O>> <NOT <FSET? .O ,MENTIONEDBIT>>>>

;"Move the player to ROOM and bring the world up to date: where HERE is,
  which doors are here, and whether it is lit."
<ROUTINE MOVE-PLAYER-TO (ROOM)
    <MOVE ,PLAYER .ROOM>
    <SETG HERE .ROOM>
    <PLACE-DOORS>
    <SETG LIT <LIGHT-HERE?>>>

<ROUTINE ENCLOSES? (OUTER O)
    ;"'the location encloses the keys': O is in OUTER, at any depth"
    <REPEAT ()
        <SET O <LOC .O>>
        <COND (<ZERO? .O> <RFALSE>)
              (<EQUAL? .O .OUTER> <RTRUE>)>>>
