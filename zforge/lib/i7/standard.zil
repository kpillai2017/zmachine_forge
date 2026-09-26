"zforge/lib/i7/standard.zil - the standard actions' own rules.

 One routine per Inform 7 library rule, named after it (the compiler's
 catalogue, zforge/compiler/i7/standard.py, pairs each routine with its
 Inform 7 name - 'the can't take what's already taken rule' - and puts it
 in its action's rulebook, where an author can remove or replace it).

 A rule never prints its message itself: it calls a response routine
 such as TAKE-ALREADY-TAKEN-A, which the compiler writes from the rule's
 response text - Inform 7's default, or the author's own ('The standard
 report taking rule response (A) is \"OK.\"').

 A rule returns true when it decides (a check rule stops the action);
 false means 'no decision, go on'.

 Directions: Inform 7 treats 'north' as an object (the noun of 'going
 north'). The compiler makes one DIR-... object per direction, holding
 the ZIL direction property it stands for in DIR-PROP."

<PROPDEF DIR-PROP 0>

;"------------------------------------------------------------- looking"
;"The four carry out looking rules; going into a room runs them too."
<ROUTINE DESCRIBE-ROOM () <FOLLOW-RULES <GET ,LOOKING-RULES ,CARRY-OUT-STAGE>>>

<ROUTINE LOOK-HEADING ()               ;"the room description heading rule"
    <PARA-FLUSH>
    <HLIGHT 2>
    <COND (,LIT <TELL D ,HERE>) (ELSE <LOOK-HEADING-A>)>
    <HLIGHT 0> <CRLF>
    <RFALSE>>

<ROUTINE LOOK-BODY ()                  ;"the room description body text rule"
    <COND (<NOT ,LIT> <LOOK-BODY-A>)
          (<GETP ,HERE ,P?DESCRIPTION> <PARA-FLUSH> <SAY-TEXT ,HERE ,P?DESCRIPTION> <CRLF>)>
    <RFALSE>>

<ROUTINE LOOK-OBJECTS ()     ;"the room description paragraphs about objects rule"
    <COND (<NOT ,LIT> <RFALSE>)>
    ;"things that describe themselves, until they are first picked up.
      Like Inform 7, the thing is 'regarded' first: '[There] [are] ...'
      in its paragraph agrees with it."
    <MAP-CONTENTS (O ,HERE)
        <COND (<SHOWS-INITIAL? .O>
               <SETG PRIOR-NAMED .O>
               <PARA-ABSORB> <CRLF> <SAY-TEXT .O ,P?INITIAL-APPEARANCE> <CRLF>)>>
    <COND (<NOT <ZERO? <COUNT-LISTED ,HERE ,LISTED-HERE?>>>
           <PARA-ABSORB>
           <CRLF> <TELL "You can see "> <SAY-LIST ,HERE ,LISTED-HERE?> <TELL " here." CR>)>
    ;"what is on scenery supporters (Inform 7 mentions these too)"
    <MAP-CONTENTS (O ,HERE)
        <COND (<AND <FSET? .O ,SCENERYBIT> <FSET? .O ,SUPPORTERBIT>
                    <NOT <ZERO? <COUNT-LISTED .O ,VISIBLE-THING?>>>>
               <PARA-ABSORB> <CRLF> <TELL "On "> <SAY-THE .O> <TELL " ">
               <COND (<EQUAL? <COUNT-LISTED .O ,VISIBLE-THING?> 1> <TELL "is ">)
                     (ELSE <TELL "are ">)>
               <SAY-LIST .O ,VISIBLE-THING?> <TELL "." CR>)>>
    <RFALSE>>

<ROUTINE LOOK-NEW-ARRIVAL ()           ;"the check new arrival rule"
    <COND (,LIT <FSET ,HERE ,VISITEDBIT>)>
    <RFALSE>>

;"----------------------------------------------------------- examining"
<GLOBAL EXAMINE-SAID 0>                ;"has an examining rule said something?"
<ROUTINE EXAMINE-STANDARD ()           ;"the standard examining rule"
    <SETG EXAMINE-SAID 0>
    <COND (<GETP ,PRSO ,P?DESCRIPTION>
           <PARA-FLUSH> <SAY-TEXT ,PRSO ,P?DESCRIPTION> <CRLF> <SETG EXAMINE-SAID 1>)>
    <RFALSE>>
<ROUTINE EXAMINE-UNDESCRIBED ()        ;"the examine undescribed things rule"
    <COND (<NOT ,EXAMINE-SAID> <EXAMINE-UNDESCRIBED-A>)>
    <RFALSE>>

;"-------------------------------------------------------------- taking"
<ROUTINE TAKE-YOURSELF ()
    <COND (<EQUAL? ,PRSO ,PLAYER> <TAKE-YOURSELF-A> <RTRUE>)> <RFALSE>>
<ROUTINE TAKE-PEOPLE ()
    <COND (<FSET? ,PRSO ,PERSONBIT> <TAKE-PEOPLE-A> <RTRUE>)> <RFALSE>>
<ROUTINE TAKE-ALREADY-TAKEN ()
    <COND (<IN? ,PRSO ,PLAYER> <TAKE-ALREADY-TAKEN-A> <RTRUE>)> <RFALSE>>
<ROUTINE TAKE-SCENERY ()
    <COND (<FSET? ,PRSO ,SCENERYBIT> <TAKE-SCENERY-A> <RTRUE>)> <RFALSE>>
<ROUTINE TAKE-FIXED ()
    <COND (<FSET? ,PRSO ,FIXEDBIT> <TAKE-FIXED-A> <RTRUE>)> <RFALSE>>
<ROUTINE TAKE-STANDARD () <MOVE ,PRSO ,PLAYER> <FSET ,PRSO ,HANDLEDBIT> <RFALSE>>
<ROUTINE TAKE-REPORT () <TAKE-REPORT-A> <RFALSE>>

;"------------------------------------------------------------ dropping"
<ROUTINE DROP-NOT-HELD ()
    <COND (<NOT <IN? ,PRSO ,PLAYER>> <DROP-NOT-HELD-A> <RTRUE>)> <RFALSE>>
<ROUTINE DROP-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,HERE> <RFALSE>>
<ROUTINE DROP-REPORT () <DROP-REPORT-A> <RFALSE>>

;"--------------------------------------------------------------- going"
;"Inform 7's action variables for going, set before any rule runs, so
  that Before rules can already see them: the room gone from, the room
  gone to (0 = 'going nowhere') and the door gone through (0 = none)."
<GLOBAL GOING-FROM 0>
<GLOBAL GOING-TO 0>
<GLOBAL GOING-DOOR 0>
<ROUTINE GOING-VARIABLES ("AUX" DIR PT)
    <SETG GOING-FROM ,HERE> <SETG GOING-TO 0> <SETG GOING-DOOR 0>
    <SET DIR <GETP ,PRSO ,P?DIR-PROP>>        ;"0 if the noun is not a direction"
    <COND (.DIR <SET PT <GETPT ,HERE .DIR>>)>
    <COND (<AND .PT <EQUAL? <PTSIZE .PT> 1>> <SETG GOING-TO <GETB .PT 0>>)>
    ;"an exit may lead to a door: then through it, to the other side"
    <COND (<AND ,GOING-TO <FSET? ,GOING-TO ,DOORBIT>>
           <SETG GOING-DOOR ,GOING-TO>
           <SETG GOING-TO <OTHER-SIDE ,GOING-DOOR>>)>>
<ROUTINE GO-CLOSED-DOOR ()
    <COND (<AND ,GOING-DOOR <NOT <FSET? ,GOING-DOOR ,OPENBIT>>> <GO-CLOSED-DOOR-A> <RTRUE>)>
    <RFALSE>>
<ROUTINE GO-THAT-WAY ()
    <COND (<ZERO? ,GOING-TO> <GO-THAT-WAY-A> <RTRUE>)> <RFALSE>>
<ROUTINE GO-MOVE () <MOVE-PLAYER-TO ,GOING-TO> <RFALSE>>
<ROUTINE GO-DESCRIBE () <DESCRIBE-ROOM> <RFALSE>>

;"---------------------------------------------------- taking inventory"
<ROUTINE INVENTORY-EMPTY ()
    <COND (<ZERO? <COUNT-LISTED ,PLAYER ,ANY-THING?>> <INVENTORY-EMPTY-A> <RTRUE>)>
    <RFALSE>>
<ROUTINE INVENTORY-STANDARD ()
    <INVENTORY-STANDARD-A>
    <MAP-CONTENTS (O ,PLAYER)
        <TELL "  "> <SAY-A .O>
        <COND (<FSET? .O ,WORNBIT> <TELL " (being worn)">)>
        <CRLF>>
    <RFALSE>>
<ROUTINE ANY-THING? (O) <RTRUE>>

;"------------------------------------------ putting it on / inserting"
<ROUTINE IMPLICITLY-TAKE ()            ;"the carrying requirements rule"
    ;"Inform 7 picks a thing up first: '(first taking the cloak)'"
    <COND (<IN? ,PRSO ,PLAYER> <RFALSE>)>
    <TELL "(first taking "> <SAY-THE ,PRSO> <TELL ")" CR>
    <TRY ,V?TAKING ,V-TAKING ,PRSO 0 1>
    <NOT <IN? ,PRSO ,PLAYER>>>
<ROUTINE PUT-ON-ITSELF ()
    <COND (<EQUAL? ,PRSO ,PRSI> <PUT-ON-ITSELF-A> <RTRUE>)> <RFALSE>>
<ROUTINE PUT-NOT-SUPPORTER ()
    <COND (<NOT <FSET? ,PRSI ,SUPPORTERBIT>> <PUT-NOT-SUPPORTER-A> <RTRUE>)> <RFALSE>>
<ROUTINE PUT-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,PRSI> <RFALSE>>
<ROUTINE PUT-REPORT () <PUT-REPORT-A> <RFALSE>>
<ROUTINE INSERT-ITSELF ()
    <COND (<EQUAL? ,PRSO ,PRSI> <INSERT-ITSELF-A> <RTRUE>)> <RFALSE>>
<ROUTINE INSERT-NOT-CONTAINER ()
    <COND (<NOT <FSET? ,PRSI ,CONTAINERBIT>> <INSERT-NOT-CONTAINER-A> <RTRUE>)> <RFALSE>>
<ROUTINE INSERT-CLOSED ()
    <COND (<AND <FSET? ,PRSI ,OPENABLEBIT> <NOT <FSET? ,PRSI ,OPENBIT>>>
           <INSERT-CLOSED-A> <RTRUE>)>
    <RFALSE>>
<ROUTINE INSERT-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,PRSI> <RFALSE>>
<ROUTINE INSERT-REPORT () <INSERT-REPORT-A> <RFALSE>>

;"------------------------------------------------- wearing / taking off"
<ROUTINE WEAR-NOT-CLOTHING ()
    <COND (<NOT <FSET? ,PRSO ,WEARABLEBIT>> <WEAR-NOT-CLOTHING-A> <RTRUE>)> <RFALSE>>
<ROUTINE WEAR-ALREADY ()
    <COND (<FSET? ,PRSO ,WORNBIT> <WEAR-ALREADY-A> <RTRUE>)> <RFALSE>>
<ROUTINE WEAR-STANDARD () <FSET ,PRSO ,WORNBIT> <RFALSE>>
<ROUTINE WEAR-REPORT () <WEAR-REPORT-A> <RFALSE>>
<ROUTINE TAKE-OFF-NOT-WORN ()
    <COND (<NOT <FSET? ,PRSO ,WORNBIT>> <TAKE-OFF-NOT-WORN-A> <RTRUE>)> <RFALSE>>
<ROUTINE TAKE-OFF-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <RFALSE>>
<ROUTINE TAKE-OFF-REPORT () <TAKE-OFF-REPORT-A> <RFALSE>>

;"--------------------------------------------------- opening / closing"
<ROUTINE OPEN-UNOPENABLE ()
    <COND (<NOT <FSET? ,PRSO ,OPENABLEBIT>> <OPEN-UNOPENABLE-A> <RTRUE>)> <RFALSE>>
<ROUTINE OPEN-LOCKED ()
    <COND (<FSET? ,PRSO ,LOCKEDBIT> <OPEN-LOCKED-A> <RTRUE>)> <RFALSE>>
<ROUTINE OPEN-ALREADY ()
    <COND (<FSET? ,PRSO ,OPENBIT> <OPEN-ALREADY-A> <RTRUE>)> <RFALSE>>
<ROUTINE OPEN-STANDARD () <FSET ,PRSO ,OPENBIT> <RFALSE>>
<ROUTINE OPEN-REPORT () <OPEN-REPORT-A> <RFALSE>>
<ROUTINE CLOSE-UNOPENABLE ()
    <COND (<NOT <FSET? ,PRSO ,OPENABLEBIT>> <CLOSE-UNOPENABLE-A> <RTRUE>)> <RFALSE>>
<ROUTINE CLOSE-ALREADY ()
    <COND (<NOT <FSET? ,PRSO ,OPENBIT>> <CLOSE-ALREADY-A> <RTRUE>)> <RFALSE>>
<ROUTINE CLOSE-STANDARD () <FCLEAR ,PRSO ,OPENBIT> <RFALSE>>
<ROUTINE CLOSE-REPORT () <CLOSE-REPORT-A> <RFALSE>>

;"------------------------------------------------- locking / unlocking"
<ROUTINE LOCK-NO-LOCK ()
    <COND (<NOT <FSET? ,PRSO ,LOCKABLEBIT>> <LOCK-NO-LOCK-A> <RTRUE>)> <RFALSE>>
<ROUTINE LOCK-ALREADY ()
    <COND (<FSET? ,PRSO ,LOCKEDBIT> <LOCK-ALREADY-A> <RTRUE>)> <RFALSE>>
<ROUTINE LOCK-OPEN ()
    <COND (<FSET? ,PRSO ,OPENBIT> <LOCK-OPEN-A> <RTRUE>)> <RFALSE>>
<ROUTINE LOCK-WRONG-KEY ()
    <COND (<NOT <EQUAL? <GETP ,PRSO ,P?WITH-KEY> ,PRSI>> <LOCK-WRONG-KEY-A> <RTRUE>)>
    <RFALSE>>
<ROUTINE LOCK-STANDARD () <FSET ,PRSO ,LOCKEDBIT> <RFALSE>>
<ROUTINE LOCK-REPORT () <LOCK-REPORT-A> <RFALSE>>
<ROUTINE UNLOCK-NO-LOCK ()
    <COND (<NOT <FSET? ,PRSO ,LOCKABLEBIT>> <UNLOCK-NO-LOCK-A> <RTRUE>)> <RFALSE>>
<ROUTINE UNLOCK-ALREADY ()
    <COND (<NOT <FSET? ,PRSO ,LOCKEDBIT>> <UNLOCK-ALREADY-A> <RTRUE>)> <RFALSE>>
<ROUTINE UNLOCK-WRONG-KEY ()
    <COND (<NOT <EQUAL? <GETP ,PRSO ,P?WITH-KEY> ,PRSI>> <UNLOCK-WRONG-KEY-A> <RTRUE>)>
    <RFALSE>>
<ROUTINE UNLOCK-STANDARD () <FCLEAR ,PRSO ,LOCKEDBIT> <RFALSE>>
<ROUTINE UNLOCK-REPORT () <UNLOCK-REPORT-A> <RFALSE>>

;"------------------------------------------------------- switching"
<ROUTINE SWITCH-ON-UNSWITCHABLE ()
    <COND (<NOT <FSET? ,PRSO ,DEVICEBIT>> <SWITCH-ON-UNSWITCHABLE-A> <RTRUE>)> <RFALSE>>
<ROUTINE SWITCH-ON-ALREADY ()
    <COND (<FSET? ,PRSO ,ONBIT> <SWITCH-ON-ALREADY-A> <RTRUE>)> <RFALSE>>
<ROUTINE SWITCH-ON-STANDARD () <FSET ,PRSO ,ONBIT> <RFALSE>>
<ROUTINE SWITCH-ON-REPORT () <SWITCH-ON-REPORT-A> <RFALSE>>
<ROUTINE SWITCH-OFF-UNSWITCHABLE ()
    <COND (<NOT <FSET? ,PRSO ,DEVICEBIT>> <SWITCH-OFF-UNSWITCHABLE-A> <RTRUE>)> <RFALSE>>
<ROUTINE SWITCH-OFF-ALREADY ()
    <COND (<NOT <FSET? ,PRSO ,ONBIT>> <SWITCH-OFF-ALREADY-A> <RTRUE>)> <RFALSE>>
<ROUTINE SWITCH-OFF-STANDARD () <FCLEAR ,PRSO ,ONBIT> <RFALSE>>
<ROUTINE SWITCH-OFF-REPORT () <SWITCH-OFF-REPORT-A> <RFALSE>>

;"--------------------------------------------------------------- misc"
<ROUTINE WAIT-REPORT () <WAIT-REPORT-A> <RFALSE>>

<ROUTINE SCORE-ANNOUNCE ()             ;"the announce the score rule"
    <PARA-FLUSH>
    <COND (<NOT ,SCORING> <TELL "There is no score in this story." CR> <RFALSE>)>
    <TELL "You have so far scored " N ,SCORE " out of a possible " N ,MAX-SCORE
          ", in " N ,TURN-COUNT " turn">
    <COND (<NOT <EQUAL? ,TURN-COUNT 1>> <TELL "s">)>
    <TELL "." CR>
    <RFALSE>>

<ROUTINE SAVE-GAME ("AUX" R)           ;"the save the game rule"
    <SET R <SAVE>>
    <COND (<EQUAL? .R 2> <TELL "Ok." CR>)          ;"we are back after a RESTORE"
          (.R <TELL "Ok." CR>)
          (ELSE <TELL "Save failed." CR>)>
    <RFALSE>>

<ROUTINE RESTORE-GAME ()               ;"the restore the game rule"
    <COND (<NOT <RESTORE>> <TELL "Restore failed." CR>)>
    <RFALSE>>

<ROUTINE QUIT-GAME ()                  ;"the quit the game rule"
    <TELL "Are you sure you want to quit? ">
    <COND (<YES?> <QUIT>)>
    <RFALSE>>

<ROUTINE YES? ()                       ;"'if the player consents'"
    <REPEAT ()
        <COND (<READ-COMMAND>
               <COND (<EQUAL? <WORD-AT 1> ,W?YES ,W?Y> <RTRUE>)
                     (<EQUAL? <WORD-AT 1> ,W?NO ,W?N> <RFALSE>)>)>
        <TELL "Please answer yes or no.> ">>>
