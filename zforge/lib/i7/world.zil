"zforge/lib/i7/world.zil - light, darkness and describing a room.

 A room is lit if it has LITBIT (the compiler sets it unless the source
 says the room is dark), or if a lit thing is in it or carried by the
 player (one level deep, like the parser's scope)."

<PROPDEF DESCRIPTION 0>
<PROPDEF INITIAL-APPEARANCE 0>

<ROUTINE LIGHT-HERE? ()
    <COND (<FSET? ,HERE ,LITBIT> <RTRUE>)
          (<HAS-LIGHT? ,HERE> <RTRUE>)
          (<HAS-LIGHT? ,PLAYER> <RTRUE>)>
    <RFALSE>>

<ROUTINE HAS-LIGHT? (PARENT)
    <MAP-CONTENTS (O .PARENT)
        <COND (<FSET? .O ,LITBIT> <RTRUE>)>>
    <RFALSE>>

<ROUTINE DESCRIBE-ROOM ()
    ;"the looking action: heading, description, then what is here"
    <COND (<NOT ,LIT>
           <HLIGHT 2> <TELL "Darkness"> <HLIGHT 0> <CRLF>
           <TELL "It is pitch dark, and you can't see a thing." CR>
           <RTRUE>)>
    <HLIGHT 2> <TELL D ,HERE> <HLIGHT 0> <CRLF>
    <COND (<SAY-TEXT ,HERE ,P?DESCRIPTION> <CRLF>)>
    <FSET ,HERE ,VISITEDBIT>
    ;"things that describe themselves, until they are first picked up"
    <MAP-CONTENTS (O ,HERE)
        <COND (<SHOWS-INITIAL? .O>
               <CRLF> <SAY-TEXT .O ,P?INITIAL-APPEARANCE> <CRLF>)>>
    <COND (<NOT <ZERO? <COUNT-LISTED ,HERE ,LISTED-HERE?>>>
           <CRLF> <TELL "You can see "> <SAY-LIST ,HERE ,LISTED-HERE?> <TELL " here." CR>)>
    ;"what is on scenery supporters (Inform 7 mentions these too)"
    <MAP-CONTENTS (O ,HERE)
        <COND (<AND <FSET? .O ,SCENERYBIT> <FSET? .O ,SUPPORTERBIT>
                    <NOT <ZERO? <COUNT-LISTED .O ,VISIBLE-THING?>>>>
               <CRLF> <TELL "On "> <SAY-THE .O> <TELL " ">
               <COND (<EQUAL? <COUNT-LISTED .O ,VISIBLE-THING?> 1> <TELL "is ">)
                     (ELSE <TELL "are ">)>
               <SAY-LIST .O ,VISIBLE-THING?> <TELL "." CR>)>>>

<ROUTINE SHOWS-INITIAL? (O)
    <AND <NOT <FSET? .O ,HANDLEDBIT>> <GETP .O ,P?INITIAL-APPEARANCE>
         <NOT <EQUAL? .O ,PLAYER>>>>

<ROUTINE VISIBLE-THING? (O)
    <NOT <OR <FSET? .O ,SCENERYBIT> <EQUAL? .O ,PLAYER>>>>

<ROUTINE LISTED-HERE? (O)
    <AND <VISIBLE-THING? .O> <NOT <SHOWS-INITIAL? .O>>>>

<ROUTINE MOVE-PLAYER-TO (ROOM)
    <MOVE ,PLAYER .ROOM>
    <SETG HERE .ROOM>
    <SETG LIT <LIGHT-HERE?>>>
