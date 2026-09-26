"cloak_syntax.zil - 'Cloak of Darkness' again, written the way Infocom
 wrote games: SYNTAX lines, a parser library, verb routines (V-...) and
 ACTION routines on objects and rooms that can take over a command.

 Compare with cloak.zil, which hand-codes its parser: here the grammar is
 DATA (see the SYNTAX-TABLE in the generated .zas) and lib/parser.zil
 does the matching. Also shows PROG/BIND and VERB? / PRSO?."

<VERSION 5>
<INSERT-FILE "lib/parser">

<DIRECTIONS NORTH EAST SOUTH WEST>
<CONSTANT MAX-SCORE 2>

<GLOBAL SCORE 0>
<GLOBAL MOVES 0>
<GLOBAL DISTURBED 0>
<GLOBAL HUNG-BEFORE <>>

"------------------------------------------------------------- grammar"

<SYNTAX LOOK = V-LOOK>
<SYNTAX LOOK AT OBJECT = V-EXAMINE>
<VERB-SYNONYM LOOK L>
<SYNTAX EXAMINE OBJECT = V-EXAMINE>
<VERB-SYNONYM EXAMINE X READ>
<SYNTAX INVENTORY = V-INVENTORY>
<VERB-SYNONYM INVENTORY I>
<SYNTAX NORTH = V-NORTH>   <VERB-SYNONYM NORTH N>
<SYNTAX SOUTH = V-SOUTH>   <VERB-SYNONYM SOUTH S>
<SYNTAX EAST = V-EAST>     <VERB-SYNONYM EAST E>
<SYNTAX WEST = V-WEST>     <VERB-SYNONYM WEST W>
<SYNTAX TAKE OBJECT (ON-GROUND IN-ROOM) = V-TAKE>
<SYNTAX PICK UP OBJECT = V-TAKE>
<VERB-SYNONYM TAKE GET>
<SYNTAX DROP OBJECT (HELD CARRIED) = V-DROP>
<SYNTAX WEAR OBJECT (FIND CLOTHBIT) = V-WEAR>
<SYNTAX HANG OBJECT = V-HANG PRE-HANG>
<SYNTAX HANG OBJECT ON OBJECT = V-HANG PRE-HANG>
<VERB-SYNONYM HANG PUT>
<PREP-SYNONYM ON ONTO>
<SYNTAX WAIT = V-WAIT>     <VERB-SYNONYM WAIT Z>
<SYNTAX UNDO = V-UNDO>
<SYNTAX SAVE = V-SAVE>
<SYNTAX RESTORE = V-RESTORE>
<SYNTAX QUIT = V-QUIT>     <VERB-SYNONYM QUIT Q>
<SYNTAX HELP = V-HELP>

"--------------------------------------------------------------- world"

<OBJECT ROOMS (DESC "rooms")>

<ROOM FOYER
    (IN ROOMS)
    (DESC "Foyer of the Opera House")
    (LDESC "You are standing in a spacious hall, splendidly decorated in red
and gold, with glittering chandeliers overhead. The entrance from the street
is to the north, and there are doorways south and west.")
    (NORTH "You've only just arrived, and besides, the weather outside seems
to be getting worse.")
    (SOUTH TO BAR)
    (WEST TO CLOAKROOM)
    (FLAGS LIGHTBIT)>

<ROOM CLOAKROOM
    (IN ROOMS)
    (DESC "Cloakroom")
    (LDESC "The walls of this small room were clearly once lined with hooks,
though now only one remains. The exit is a door to the east.")
    (EAST TO FOYER)
    (FLAGS LIGHTBIT)>

<ROOM BAR
    (IN ROOMS)
    (DESC "Foyer Bar")
    (LDESC "The bar, much rougher than you'd have guessed after the opulence
of the foyer to the north, is completely empty. There seems to be some sort
of message scrawled in the sawdust on the floor.")
    (NORTH TO FOYER)
    (ACTION BAR-F)>

<OBJECT CLOAK
    (IN PLAYER)
    (DESC "velvet cloak")
    (SYNONYM CLOAK)
    (ADJECTIVE VELVET BLACK)
    (TEXT "A handsome cloak, of velvet trimmed with satin, and slightly
spattered with raindrops. Its blackness is so deep that it almost seems to
suck light from the room.")
    (FLAGS TAKEBIT WORNBIT CLOTHBIT)
    (ACTION CLOAK-F)>

<OBJECT HOOK
    (IN CLOAKROOM)
    (DESC "small brass hook")
    (SYNONYM HOOK PEG)
    (ADJECTIVE SMALL BRASS)
    (TEXT "It's just a small brass hook, screwed to the wall.")>

<OBJECT MESSAGE
    (IN BAR)
    (DESC "scrawled message")
    (SYNONYM MESSAGE SAWDUST FLOOR)
    (ACTION MESSAGE-F)>

"----------------------------------------------------------- main loop"

<ROUTINE GO ()
    <SETG HERE ,FOYER>
    <CLEAR -1>
    <SPLIT 1>
    <TELL CR "Hurrying through the rainswept November night, you're glad to
see the bright lights of the Opera House. It's surprising that there aren't
more people about but, hey, what do you expect in a cheap demo game...?" CR CR>
    <HLIGHT 2>
    <TELL "Cloak of Darkness">
    <HLIGHT 0>
    <TELL CR "A basic IF demonstration, compiled from ZIL (with SYNTAX) by zforge." CR CR>
    <V-LOOK>
    <MAIN-LOOP>>

<ROUTINE MAIN-LOOP ()
    <REPEAT ()
        <SETG LIT <LIT?>>
        <STATUS-LINE>
        <TELL CR "> ">
        <COND (<NOT <PARSER>>)
              (<VERB? UNDO> <V-UNDO>)          ;"UNDO must not take a snapshot"
              (<EQUAL? <ZOP SAVE_UNDO> 2>
               <TELL "[Previous turn undone.]" CR CR>
               <V-LOOK>)
              (ELSE
               <PERFORM>
               <SETG MOVES <+ ,MOVES 1>>)>>>

<ROUTINE STATUS-LINE ()
    <BIND ((WIDTH <GETB 0 33>))            ;"§11: header byte $21 = screen width"
        <SCREEN 1>
        <HLIGHT 1>
        <CURSET 1 1>
        <DO (I 1 .WIDTH) <PRINTC 32>>
        <CURSET 1 2>
        <COND (,LIT <TELL D ,HERE>) (ELSE <TELL "Darkness">)>
        <CURSET 1 <- .WIDTH 20>>
        <TELL "Score: " N ,SCORE "  Moves: " N ,MOVES>
        <HLIGHT 0>
        <SCREEN 0>>>

<ROUTINE LIT? ()
    <COND (<FSET? ,HERE ,LIGHTBIT> <RTRUE>)
          (<EQUAL? ,HERE ,BAR> <NOT <IN? ,CLOAK ,PLAYER>>)
          (ELSE <RFALSE>)>>

"------------------------------------------------------ ACTION routines"

<ROUTINE BAR-F ()
    ;"a room ACTION sees every command first; true = handled"
    <COND (<LIT?> <RFALSE>)
          (<VERB? NORTH LOOK INVENTORY UNDO SAVE RESTORE QUIT HELP> <RFALSE>)
          (<VERB? SOUTH EAST WEST>
           <SETG DISTURBED <+ ,DISTURBED 2>>
           <TELL "Blundering around in the dark isn't a good idea!" CR>)
          (ELSE
           <SETG DISTURBED <+ ,DISTURBED 1>>
           <TELL "In the dark? You could easily disturb something!" CR>)>>

<ROUTINE CLOAK-F ()
    <COND (<AND <VERB? DROP> <NOT <EQUAL? ,HERE ,CLOAKROOM>>>
           <TELL "This isn't the best place to leave a smart cloak lying around." CR>)
          (ELSE <RFALSE>)>>

<ROUTINE MESSAGE-F ()
    <COND (<VERB? EXAMINE> <READ-MESSAGE>)
          (<VERB? TAKE> <TELL "It's scrawled in the sawdust - hardly portable." CR>)
          (ELSE <RFALSE>)>>

<ROUTINE PRE-HANG ()
    ;"a SYNTAX preaction runs before any ACTION routine"
    <COND (<AND ,PRSI <NOT <PRSI? HOOK>>> <TELL "You can only hang things on the hook." CR>)
          (<NOT <EQUAL? ,HERE ,CLOAKROOM>> <TELL "There's nothing to hang it on here." CR>)
          (ELSE <RFALSE>)>>

"---------------------------------------------------------------- verbs"

<ROUTINE V-LOOK ()
    <COND (<NOT <LIT?>>
           <HLIGHT 2> <TELL "Darkness"> <HLIGHT 0>
           <TELL CR "It is pitch dark, and you can't see a thing." CR>
           <RTRUE>)>
    <HLIGHT 2> <TELL D ,HERE> <HLIGHT 0>
    <TELL CR>
    <PRINT <GETP ,HERE ,P?LDESC>>
    <CRLF>
    <MAP-CONTENTS (O ,HERE)
        <COND (<FSET? .O ,TAKEBIT> <TELL "You can see a " D .O " here." CR>)>>
    <COND (<AND <EQUAL? ,HERE ,CLOAKROOM> <IN? ,CLOAK ,HOOK>>
           <TELL "A velvet cloak hangs on the brass hook." CR>)>>

<ROUTINE V-NORTH () <GO-DIR ,P?NORTH>>
<ROUTINE V-SOUTH () <GO-DIR ,P?SOUTH>>
<ROUTINE V-EAST () <GO-DIR ,P?EAST>>
<ROUTINE V-WEST () <GO-DIR ,P?WEST>>

<ROUTINE GO-DIR (DIR "AUX" PT)
    <SET PT <GETPT ,HERE .DIR>>
    <COND (<ZERO? .PT> <TELL "You can't go that way." CR>)
          (<EQUAL? <PTSIZE .PT> 1>           ;"(DIR TO ROOM): 1 byte, ADR-010"
           <SETG HERE <GETB .PT 0>>
           <V-LOOK>)
          (ELSE <PRINT <GET .PT 0>> <CRLF>)>>

<ROUTINE V-INVENTORY ()
    <COND (<NOT <FIRST? ,PLAYER>> <TELL "You are empty-handed." CR> <RTRUE>)>
    <TELL "You are carrying:" CR>
    <MAP-CONTENTS (O ,PLAYER)
        <TELL "  a " D .O>
        <COND (<FSET? .O ,WORNBIT> <TELL " (being worn)">)>
        <CRLF>>>

<ROUTINE V-TAKE ()
    <COND (<IN? ,PRSO ,PLAYER> <TELL "You already have that." CR>)
          (<NOT <FSET? ,PRSO ,TAKEBIT>> <TELL "That's hardly portable." CR>)
          (ELSE <MOVE ,PRSO ,PLAYER> <TELL "Taken." CR>)>>

<ROUTINE V-DROP ()
    <COND (<NOT <IN? ,PRSO ,PLAYER>> <TELL "You aren't carrying that." CR>)
          (ELSE
           <FCLEAR ,PRSO ,WORNBIT>
           <MOVE ,PRSO ,HERE>
           <TELL "Dropped." CR>)>>

<ROUTINE V-WEAR ()
    <COND (<NOT <FSET? ,PRSO ,CLOTHBIT>> <TELL "You can't wear that." CR>)
          (<NOT <IN? ,PRSO ,PLAYER>> <TELL "You'll need to take it first." CR>)
          (<FSET? ,PRSO ,WORNBIT> <TELL "You're already wearing it." CR>)
          (ELSE <FSET ,PRSO ,WORNBIT> <TELL "You put on the " D ,PRSO "." CR>)>>

<ROUTINE V-HANG ()
    <COND (<NOT <PRSO? CLOAK>> <TELL "You can't hang that up." CR>)
          (<NOT <IN? ,CLOAK ,PLAYER>> <TELL "You aren't carrying the cloak." CR>)
          (ELSE
           <FCLEAR ,CLOAK ,WORNBIT>
           <MOVE ,CLOAK ,HOOK>
           <TELL "You hang the velvet cloak on the small brass hook." CR>
           <COND (<NOT ,HUNG-BEFORE>
                  <SETG HUNG-BEFORE T>
                  <SETG SCORE <+ ,SCORE 1>>)>)>>

<ROUTINE V-EXAMINE ()
    <PROG ((TEXT <GETP ,PRSO ,P?TEXT>))
        <COND (.TEXT <PRINT .TEXT>) (ELSE <TELL "You see nothing special.">)>
        <COND (<AND <PRSO? HOOK> <IN? ,CLOAK ,HOOK>>
               <TELL " A velvet cloak is hanging on it.">)>
        <CRLF>>>

<ROUTINE READ-MESSAGE ()
    <COND (<L? ,DISTURBED 2>
           <SETG SCORE <+ ,SCORE 1>>
           <TELL "The message, neatly marked in the sawdust, reads..." CR CR>
           <HLIGHT 2> <TELL "*** You have won ***"> <HLIGHT 0>)
          (ELSE
           <TELL "The message has been carelessly trampled, making it difficult
to read. You can just distinguish the words..." CR CR>
           <HLIGHT 2> <TELL "*** You have lost ***"> <HLIGHT 0>)>
    <TELL CR CR "You scored " N ,SCORE " out of " N ,MAX-SCORE " in " N <+ ,MOVES 1>
          " moves." CR>
    <QUIT>>

<ROUTINE V-WAIT () <TELL "Time passes." CR>>

<ROUTINE V-UNDO ()
    <ZOP RESTORE_UNDO>                  ;"on success we continue after SAVE_UNDO"
    <TELL "You can't undo any further." CR>>

<ROUTINE V-SAVE ("AUX" RESULT)
    <SET RESULT <SAVE>>                 ;"§15 save: 0 failed, 1 saved, 2 restored"
    <COND (<EQUAL? .RESULT 1> <TELL "Saved." CR>)
          (<EQUAL? .RESULT 2> <TELL "Restored." CR CR> <V-LOOK>)
          (ELSE <TELL "Save failed." CR>)>>

<ROUTINE V-RESTORE ()
    <RESTORE>
    <TELL "Restore failed." CR>>

<ROUTINE V-QUIT ("AUX" KEY)
    <TELL "Are you sure you want to quit? (Y/N) ">
    <SET KEY <INPUT 1>>
    <CRLF>
    <COND (<EQUAL? .KEY !\y !\Y> <TELL "Goodbye." CR> <QUIT>)
          (ELSE <TELL "OK." CR>)>>

<ROUTINE V-HELP ()
    <TELL "Try LOOK, INVENTORY, N/S/E/W, TAKE, DROP, WEAR, HANG CLOAK ON HOOK,
EXAMINE or READ something, WAIT, UNDO, SAVE, RESTORE and QUIT." CR>>
