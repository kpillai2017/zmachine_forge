"cloak.zil - 'Cloak of Darkness' (the classic IF demo, by Roger Firth's
 design) written in ZIL-lite for zforge. Shows off: rooms and objects,
 FLAGS/properties, exits (TO room = 1 byte, message = packed string),
 a tiny verb-noun parser on top of READ + the dictionary, a reverse-video
 status line in the upper window, UNDO, and winning/losing endings."

<VERSION 5>

<DIRECTIONS NORTH EAST SOUTH WEST>
<CONSTANT MAX-SCORE 2>

<GLOBAL HERE 0>
<GLOBAL SCORE 0>
<GLOBAL MOVES 0>
<GLOBAL DISTURBED 0>
<GLOBAL HUNG-BEFORE <>>
<GLOBAL VERB 0>
<GLOBAL NOUN 0>
<GLOBAL READBUF <ITABLE 80 (BYTE)>>
<GLOBAL PARSEBUF <ITABLE 32 (BYTE)>>

<OBJECT ROOMS (DESC "rooms")>
<OBJECT PLAYER (DESC "yourself")>

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
    (NORTH TO FOYER)>

<OBJECT CLOAK
    (IN PLAYER)
    (DESC "velvet cloak")
    (SYNONYM CLOAK)
    (ADJECTIVE VELVET)
    (TEXT "A handsome cloak, of velvet trimmed with satin, and slightly
spattered with raindrops. Its blackness is so deep that it almost seems to
suck light from the room.")
    (FLAGS TAKEBIT WORNBIT)>

<OBJECT HOOK
    (IN CLOAKROOM)
    (DESC "small brass hook")
    (SYNONYM HOOK PEG)
    (TEXT "It's just a small brass hook, screwed to the wall.")>

<OBJECT MESSAGE
    (IN BAR)
    (DESC "scrawled message")
    (SYNONYM MESSAGE SAWDUST FLOOR)>

"--------------------------------------------------------------- main loop"

<ROUTINE GO ()
    <SETG HERE ,FOYER>
    <PUTB ,READBUF 0 78>
    <PUTB ,PARSEBUF 0 6>
    <CLEAR -1>
    <SPLIT 1>
    <TELL CR "Hurrying through the rainswept November night, you're glad to
see the bright lights of the Opera House. It's surprising that there aren't
more people about but, hey, what do you expect in a cheap demo game...?" CR CR>
    <HLIGHT 2>
    <TELL "Cloak of Darkness">
    <HLIGHT 0>
    <TELL CR "A basic IF demonstration, compiled from ZIL by zforge." CR CR>
    <DESCRIBE-ROOM>
    <MAIN-LOOP>>

<ROUTINE MAIN-LOOP ()
    <REPEAT ()
        <STATUS-LINE>
        <TELL CR "> ">
        <PUTB ,READBUF 1 0>       ;"v5: byte 1 = characters already in the buffer"
        <READ ,READBUF ,PARSEBUF>
        <COND (<PARSE>
               <COND (<EQUAL? ,VERB ,W?UNDO>
                      <ZOP RESTORE_UNDO>
                      <TELL "You can't undo any further." CR>)
                     (<EQUAL? <ZOP SAVE_UNDO> 2>
                      <TELL "[Previous turn undone.]" CR CR>
                      <DESCRIBE-ROOM>)
                     (ELSE
                      <PERFORM>
                      <SETG MOVES <+ ,MOVES 1>>)>)>>>

<ROUTINE STATUS-LINE ("AUX" WIDTH)
    <SET WIDTH <GETB 0 33>>
    <SCREEN 1>
    <HLIGHT 1>
    <CURSET 1 1>
    <DO (I 1 .WIDTH) <PRINTC 32>>
    <CURSET 1 2>
    <COND (<LIT?> <TELL D ,HERE>) (ELSE <TELL "Darkness">)>
    <CURSET 1 <- .WIDTH 20>>
    <TELL "Score: " N ,SCORE "  Moves: " N ,MOVES>
    <HLIGHT 0>
    <SCREEN 0>>

"------------------------------------------------------------------ parser"

<ROUTINE PARSE ("AUX" N (I 2) O)
    <SETG VERB 0>
    <SETG NOUN 0>
    <SET N <GETB ,PARSEBUF 1>>
    <COND (<ZERO? .N> <TELL "I beg your pardon?" CR> <RFALSE>)>
    <SETG VERB <GET ,PARSEBUF 1>>
    <COND (<ZERO? ,VERB>
           <TELL "I don't know the word \"">
           <PRINT-WORD 1>
           <TELL "\"." CR>
           <RFALSE>)>
    <REPEAT ()
        <COND (<G? .I .N> <RETURN>)>
        <SET O <FIND-OBJECT <GET ,PARSEBUF <- <* 2 .I> 1>>>>
        <COND (.O <SETG NOUN .O> <RETURN>)>
        <SET I <+ .I 1>>>
    <RTRUE>>

<ROUTINE PRINT-WORD (N "AUX" LEN START)
    <SET LEN <GETB ,PARSEBUF <- <* 4 .N> 0>>>
    <SET START <GETB ,PARSEBUF <+ <* 4 .N> 1>>>
    <DO (I .START <- <+ .START .LEN> 1>)
        <PRINTC <GETB ,READBUF .I>>>>

<ROUTINE MATCHES? (O W "AUX" PT LEN)
    <SET PT <GETPT .O ,P?SYNONYM>>
    <COND (<ZERO? .PT> <RFALSE>)>
    <SET LEN </ <PTSIZE .PT> 2>>
    <DO (I 0 <- .LEN 1>)
        <COND (<EQUAL? <GET .PT .I> .W> <RTRUE>)>>
    <RFALSE>>

<ROUTINE FIND-IN (CONTAINER W "AUX" O)
    <SET O <FIRST? .CONTAINER>>
    <REPEAT ()
        <COND (<ZERO? .O> <RFALSE>)
              (<MATCHES? .O .W> <RETURN .O>)>
        <SET O <NEXT? .O>>>>

<ROUTINE FIND-OBJECT (W "AUX" O)
    <COND (<SET O <FIND-IN ,PLAYER .W>> .O)
          (<NOT <LIT?>> <>)
          (<SET O <FIND-IN ,HERE .W>> .O)
          (<AND <EQUAL? ,HERE ,CLOAKROOM> <SET O <FIND-IN ,HOOK .W>>> .O)
          (ELSE <>)>>

"--------------------------------------------------------------- the world"

<ROUTINE LIT? ()
    <COND (<FSET? ,HERE ,LIGHTBIT> <RTRUE>)
          (<EQUAL? ,HERE ,BAR> <NOT <IN? ,CLOAK ,PLAYER>>)
          (ELSE <RFALSE>)>>

<ROUTINE DESCRIBE-ROOM ()
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

<ROUTINE GO-DIR (DIR "AUX" PT)
    <COND (<AND <EQUAL? ,HERE ,BAR> <NOT <LIT?>> <NOT <EQUAL? .DIR ,P?NORTH>>>
           <SETG DISTURBED <+ ,DISTURBED 2>>
           <TELL "Blundering around in the dark isn't a good idea!" CR>
           <RTRUE>)>
    <SET PT <GETPT ,HERE .DIR>>
    <COND (<ZERO? .PT> <TELL "You can't go that way." CR>)
          (<EQUAL? <PTSIZE .PT> 1>
           <SETG HERE <GETB .PT 0>>
           <DESCRIBE-ROOM>)
          (ELSE <PRINT <GET .PT 0>> <CRLF>)>>

"------------------------------------------------------------------- verbs"

<ROUTINE PERFORM ()
    <COND (<EQUAL? ,VERB ,W?LOOK ,W?L> <DESCRIBE-ROOM>)
          (<EQUAL? ,VERB ,W?INVENTORY ,W?I> <V-INVENTORY>)
          (<EQUAL? ,VERB ,W?NORTH ,W?N> <GO-DIR ,P?NORTH>)
          (<EQUAL? ,VERB ,W?SOUTH ,W?S> <GO-DIR ,P?SOUTH>)
          (<EQUAL? ,VERB ,W?EAST ,W?E> <GO-DIR ,P?EAST>)
          (<EQUAL? ,VERB ,W?WEST ,W?W> <GO-DIR ,P?WEST>)
          (<EQUAL? ,VERB ,W?QUIT ,W?Q> <V-QUIT>)
          (<EQUAL? ,VERB ,W?SAVE> <V-SAVE>)
          (<EQUAL? ,VERB ,W?RESTORE> <V-RESTORE>)
          (<AND <EQUAL? ,HERE ,BAR> <NOT <LIT?>>>
           <SETG DISTURBED <+ ,DISTURBED 1>>
           <TELL "In the dark? You could easily disturb something!" CR>)
          (<EQUAL? ,VERB ,W?TAKE ,W?GET> <V-TAKE>)
          (<EQUAL? ,VERB ,W?DROP> <V-DROP>)
          (<EQUAL? ,VERB ,W?WEAR> <V-WEAR>)
          (<EQUAL? ,VERB ,W?HANG ,W?PUT> <V-HANG>)
          (<EQUAL? ,VERB ,W?EXAMINE ,W?X ,W?READ> <V-EXAMINE>)
          (<EQUAL? ,VERB ,W?HELP> <TELL "Try LOOK, INVENTORY, N/S/E/W, TAKE, DROP,
WEAR, HANG CLOAK, EXAMINE or READ something, UNDO, SAVE, RESTORE and QUIT." CR>)
          (ELSE <TELL "I don't know how to do that." CR>)>>

<ROUTINE V-INVENTORY ()
    <COND (<NOT <FIRST? ,PLAYER>> <TELL "You are empty-handed." CR> <RTRUE>)>
    <TELL "You are carrying:" CR>
    <MAP-CONTENTS (O ,PLAYER)
        <TELL "  a " D .O>
        <COND (<FSET? .O ,WORNBIT> <TELL " (being worn)">)>
        <CRLF>>>

<ROUTINE V-TAKE ()
    <COND (<ZERO? ,NOUN> <TELL "What do you want to take?" CR>)
          (<IN? ,NOUN ,PLAYER> <TELL "You already have that." CR>)
          (<NOT <FSET? ,NOUN ,TAKEBIT>> <TELL "That's hardly portable." CR>)
          (ELSE <MOVE ,NOUN ,PLAYER> <TELL "Taken." CR>)>>

<ROUTINE V-DROP ()
    <COND (<OR <ZERO? ,NOUN> <NOT <IN? ,NOUN ,PLAYER>>>
           <TELL "You aren't carrying that." CR>)
          (<NOT <EQUAL? ,HERE ,CLOAKROOM>>
           <TELL "This isn't the best place to leave a smart cloak lying around." CR>)
          (ELSE
           <FCLEAR ,NOUN ,WORNBIT>
           <MOVE ,NOUN ,HERE>
           <TELL "Dropped." CR>)>>

<ROUTINE V-WEAR ()
    <COND (<NOT <EQUAL? ,NOUN ,CLOAK>> <TELL "You can't wear that." CR>)
          (<NOT <IN? ,CLOAK ,PLAYER>> <TELL "You'll need to take it first." CR>)
          (<FSET? ,CLOAK ,WORNBIT> <TELL "You're already wearing it." CR>)
          (ELSE <FSET ,CLOAK ,WORNBIT> <TELL "You put on the velvet cloak." CR>)>>

<ROUTINE V-HANG ()
    <COND (<NOT <EQUAL? ,NOUN ,CLOAK>> <TELL "You can't hang that up." CR>)
          (<NOT <EQUAL? ,HERE ,CLOAKROOM>> <TELL "There's nothing to hang it on here." CR>)
          (<NOT <IN? ,CLOAK ,PLAYER>> <TELL "You aren't carrying the cloak." CR>)
          (ELSE
           <FCLEAR ,CLOAK ,WORNBIT>
           <MOVE ,CLOAK ,HOOK>
           <TELL "You hang the velvet cloak on the small brass hook." CR>
           <COND (<NOT ,HUNG-BEFORE>
                  <SETG HUNG-BEFORE T>
                  <SETG SCORE <+ ,SCORE 1>>)>)>>

<ROUTINE V-EXAMINE ("AUX" TEXT)
    <COND (<ZERO? ,NOUN> <TELL "What do you want to examine?" CR>)
          (<EQUAL? ,NOUN ,MESSAGE> <READ-MESSAGE>)
          (ELSE
           <SET TEXT <GETP ,NOUN ,P?TEXT>>
           <COND (.TEXT <PRINT .TEXT>) (ELSE <TELL "You see nothing special.">)>
           <COND (<AND <EQUAL? ,NOUN ,HOOK> <IN? ,CLOAK ,HOOK>>
                  <TELL " A velvet cloak is hanging on it.">)>
           <CRLF>)>>

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

<ROUTINE V-SAVE ("AUX" RESULT)
    ;"§15 save: 0 = failed, 1 = saved, 2 = we are back here after a RESTORE"
    <SET RESULT <SAVE>>
    <COND (<EQUAL? .RESULT 1> <TELL "Saved." CR>)
          (<EQUAL? .RESULT 2> <TELL "Restored." CR CR> <DESCRIBE-ROOM>)
          (ELSE <TELL "Save failed." CR>)>>

<ROUTINE V-RESTORE ()
    ;"on success execution continues inside V-SAVE, so we only see failure"
    <RESTORE>
    <TELL "Restore failed." CR>>

<ROUTINE V-QUIT ("AUX" KEY)
    <TELL "Are you sure you want to quit? (Y/N) ">
    <SET KEY <INPUT 1>>
    <CRLF>
    <COND (<EQUAL? .KEY !\y !\Y> <TELL "Goodbye." CR> <QUIT>)
          (ELSE <TELL "OK." CR>)>>
