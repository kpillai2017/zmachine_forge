"zforge/lib/i7/standard.zil - the standard actions' own rules.

 The compiler puts these routines into each action's rulebook alongside
 the author's rules (zforge/compiler/i7/standard.py says which rule goes
 in which stage). The wording follows Inform 7's standard responses.

 Directions: Inform 7 treats 'north' as an object (the noun of 'going
 north'). The compiler makes one DIR-... object per direction, holding
 the ZIL direction property it stands for in DIR-PROP."

<PROPDEF DIR-PROP 0>

;"------------------------------------------------------------- looking"
<ROUTINE LOOKING-CARRY-OUT () <DESCRIBE-ROOM> <RFALSE>>

;"----------------------------------------------------------- examining"
<ROUTINE EXAMINING-CARRY-OUT ()
    <COND (<SAY-TEXT ,PRSO ,P?DESCRIPTION> <CRLF>)
          (ELSE <TELL "You see nothing special about "> <SAY-THE ,PRSO> <TELL "." CR>)>
    <RFALSE>>

;"-------------------------------------------------------------- taking"
<ROUTINE TAKING-CHECK ()
    <COND (<EQUAL? ,PRSO ,PLAYER> <TELL "You are always self-possessed." CR> <RTRUE>)
          (<IN? ,PRSO ,PLAYER> <TELL "You already have that." CR> <RTRUE>)
          (<FSET? ,PRSO ,PERSONBIT>
           <TELL "I don't suppose "> <SAY-THE ,PRSO> <TELL " would care for that." CR> <RTRUE>)
          (<FSET? ,PRSO ,SCENERYBIT> <TELL "That's hardly portable." CR> <RTRUE>)
          (<FSET? ,PRSO ,FIXEDBIT> <TELL "That's fixed in place." CR> <RTRUE>)>
    <RFALSE>>
<ROUTINE TAKING-CARRY-OUT () <MOVE ,PRSO ,PLAYER> <FSET ,PRSO ,HANDLEDBIT> <RFALSE>>
<ROUTINE TAKING-REPORT () <TELL "Taken." CR> <RFALSE>>

;"------------------------------------------------------------ dropping"
<ROUTINE DROPPING-CHECK ()
    <COND (<NOT <IN? ,PRSO ,PLAYER>> <TELL "You haven't got that." CR> <RTRUE>)>
    <RFALSE>>
<ROUTINE DROPPING-CARRY-OUT () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,HERE> <RFALSE>>
<ROUTINE DROPPING-REPORT () <TELL "Dropped." CR> <RFALSE>>

;"--------------------------------------------------------------- going"
<GLOBAL GOING-TO 0>
<ROUTINE GOING-CHECK ("AUX" PT)
    <SET PT <GETPT ,HERE <GETP ,PRSO ,P?DIR-PROP>>>
    <COND (<OR <ZERO? .PT> <NOT <EQUAL? <PTSIZE .PT> 1>>>
           <TELL "You can't go that way." CR> <RTRUE>)>
    <SETG GOING-TO <GETB .PT 0>>
    <RFALSE>>
<ROUTINE GOING-CARRY-OUT () <MOVE-PLAYER-TO ,GOING-TO> <RFALSE>>
<ROUTINE GOING-REPORT () <DESCRIBE-ROOM> <RFALSE>>

;"---------------------------------------------------- taking inventory"
<ROUTINE INVENTORY-CARRY-OUT ()
    <COND (<ZERO? <COUNT-LISTED ,PLAYER ,ANY-THING?>>
           <TELL "You are carrying nothing." CR> <RFALSE>)>
    <TELL "You are carrying:" CR>
    <MAP-CONTENTS (O ,PLAYER)
        <TELL "  "> <SAY-A .O>
        <COND (<FSET? .O ,WORNBIT> <TELL " (being worn)">)>
        <CRLF>>
    <RFALSE>>
<ROUTINE ANY-THING? (O) <RTRUE>>

;"------------------------------------------ putting it on / inserting"
<ROUTINE IMPLICITLY-TAKE ()
    ;"Inform 7 picks a thing up first: '(first taking the cloak)'"
    <COND (<IN? ,PRSO ,PLAYER> <RFALSE>)>
    <TELL "(first taking "> <SAY-THE ,PRSO> <TELL ")" CR>
    <TRY ,V?TAKING ,V-TAKING ,PRSO 0 1>
    <NOT <IN? ,PRSO ,PLAYER>>>
<ROUTINE PUTTING-CHECK ()
    <COND (<EQUAL? ,PRSO ,PRSI> <TELL "You can't put something on top of itself." CR> <RTRUE>)
          (<NOT <FSET? ,PRSI ,SUPPORTERBIT>>
           <TELL "Putting things on "> <SAY-THE ,PRSI> <TELL " would achieve nothing." CR> <RTRUE>)>
    <IMPLICITLY-TAKE>>
<ROUTINE PUTTING-CARRY-OUT () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,PRSI> <RFALSE>>
<ROUTINE PUTTING-REPORT ()
    <TELL "You put "> <SAY-THE ,PRSO> <TELL " on "> <SAY-THE ,PRSI> <TELL "." CR> <RFALSE>>
<ROUTINE INSERTING-CHECK ()
    <COND (<EQUAL? ,PRSO ,PRSI> <TELL "You can't put something inside itself." CR> <RTRUE>)
          (<NOT <FSET? ,PRSI ,CONTAINERBIT>>
           <SAY-CAP-THE ,PRSI> <TELL " can't contain things." CR> <RTRUE>)
          (<AND <FSET? ,PRSI ,OPENABLEBIT> <NOT <FSET? ,PRSI ,OPENBIT>>>
           <SAY-CAP-THE ,PRSI> <SAY-IS-ARE ,PRSI> <TELL " closed." CR> <RTRUE>)>
    <IMPLICITLY-TAKE>>
<ROUTINE INSERTING-CARRY-OUT () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,PRSI> <RFALSE>>
<ROUTINE INSERTING-REPORT ()
    <TELL "You put "> <SAY-THE ,PRSO> <TELL " into "> <SAY-THE ,PRSI> <TELL "." CR> <RFALSE>>

;"------------------------------------------------- wearing / taking off"
<ROUTINE WEARING-CHECK ()
    <COND (<NOT <FSET? ,PRSO ,WEARABLEBIT>> <TELL "You can't wear that!" CR> <RTRUE>)
          (<FSET? ,PRSO ,WORNBIT> <TELL "You're already wearing that!" CR> <RTRUE>)>
    <IMPLICITLY-TAKE>>
<ROUTINE WEARING-CARRY-OUT () <FSET ,PRSO ,WORNBIT> <RFALSE>>
<ROUTINE WEARING-REPORT () <TELL "You put on "> <SAY-THE ,PRSO> <TELL "." CR> <RFALSE>>
<ROUTINE TAKING-OFF-CHECK ()
    <COND (<NOT <FSET? ,PRSO ,WORNBIT>> <TELL "You're not wearing that." CR> <RTRUE>)>
    <RFALSE>>
<ROUTINE TAKING-OFF-CARRY-OUT () <FCLEAR ,PRSO ,WORNBIT> <RFALSE>>
<ROUTINE TAKING-OFF-REPORT () <TELL "You take off "> <SAY-THE ,PRSO> <TELL "." CR> <RFALSE>>

;"--------------------------------------------------------------- misc"
<ROUTINE WAITING-REPORT () <TELL "Time passes." CR> <RFALSE>>

<ROUTINE SCORE-CARRY-OUT ()
    <COND (<NOT ,SCORING> <TELL "There is no score in this story." CR> <RFALSE>)>
    <TELL "You have so far scored " N ,SCORE " out of a possible " N ,MAX-SCORE
          ", in " N ,TURN-COUNT " turn">
    <COND (<NOT <EQUAL? ,TURN-COUNT 1>> <TELL "s">)>
    <TELL "." CR>
    <RFALSE>>

<ROUTINE SAVING-CARRY-OUT ("AUX" R)
    <SET R <SAVE>>
    <COND (<EQUAL? .R 2> <TELL "Ok." CR>)          ;"we are back after a RESTORE"
          (.R <TELL "Ok." CR>)
          (ELSE <TELL "Save failed." CR>)>
    <RFALSE>>

<ROUTINE RESTORING-CARRY-OUT ()
    <COND (<NOT <RESTORE>> <TELL "Restore failed." CR>)>
    <RFALSE>>

<ROUTINE QUITTING-CARRY-OUT ()
    <TELL "Are you sure you want to quit? ">
    <COND (<YES?> <QUIT>)>
    <RFALSE>>

<ROUTINE YES? ()
    <REPEAT ()
        <COND (<READ-COMMAND>
               <COND (<EQUAL? <WORD-AT 1> ,W?YES ,W?Y> <RTRUE>)
                     (<EQUAL? <WORD-AT 1> ,W?NO ,W?N> <RFALSE>)>)>
        <TELL "Please answer yes or no.> ">>>
