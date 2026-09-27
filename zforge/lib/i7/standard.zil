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
    ;"in the dark: the printing the name of a dark room activity, whose
      library way is this rule's response (A), 'Darkness'"
    <COND (,LIT <PRINT-NAME ,HERE>)
          (ELSE <CARRY-OUT ,PRINTING-DARK-NAME-ACTIVITY 0 ,LOOK-HEADING-A>)>
    <HLIGHT 0> <CRLF>
    <RFALSE>>

<ROUTINE LOOK-BODY ()                  ;"the room description body text rule"
    <COND (<NOT ,LIT> <CARRY-OUT ,PRINTING-DARK-DESC-ACTIVITY 0 ,LOOK-BODY-A>)
          (<GETP ,HERE ,P?DESCRIPTION> <PARA-FLUSH> <SAY-TEXT ,HERE ,P?DESCRIPTION> <CRLF>)>
    <RFALSE>>

<ROUTINE WRITE-PARAGRAPH? (O "AUX" MARK OWED SAID NAMED)
    ;"offer O to the writing a paragraph about activity; true if a rule
      printed something. A blank line is owed first, so it is printed only
      if the rule says anything; if it says nothing, the paragraph state is
      put back exactly as it was."
    <SET OWED ,PARA-BREAK> <SET SAID ,SAY-P> <SET MARK ,SAID-COUNT>
    <SET NAMED ,PRIOR-NAMED>
    <SETG PARA-BREAK 1>
    <SETG PRIOR-NAMED .O>
    <CARRY-OUT ,WRITING-PARAGRAPH-ACTIVITY .O 0>
    <COND (<EQUAL? .MARK ,SAID-COUNT>
           <SETG PARA-BREAK .OWED> <SETG SAY-P .SAID> <SETG PRIOR-NAMED .NAMED>
           <RFALSE>)>
    <RTRUE>>

<ROUTINE LOOK-OBJECTS ()     ;"the room description paragraphs about objects rule"
    <COND (<NOT ,LIT> <RFALSE>)>
    ;"Each thing here in turn, as Inform 7's locale paragraphs do: first it
      is offered to the writing a paragraph about activity; if no rule wrote
      anything, a thing that describes itself (until first picked up) shows
      its initial appearance. Either way it is then MENTIONED, and not
      listed in 'You can see ...'. Like Inform 7, the thing is 'regarded'
      first: '[There] [are] ...' in its paragraph agrees with it."
    <MAP-CONTENTS (O ,HERE) <FCLEAR .O ,MENTIONEDBIT>>
    <MAP-CONTENTS (O ,HERE)
        <COND (<VISIBLE-THING? .O>
               <COND (<WRITE-PARAGRAPH? .O> <FSET .O ,MENTIONEDBIT>)
                     (<SHOWS-INITIAL? .O>
                      <SETG PRIOR-NAMED .O>
                      <PARA-ABSORB> <CRLF> <SAY-TEXT .O ,P?INITIAL-APPEARANCE> <CRLF>
                      <FSET .O ,MENTIONEDBIT>)>)>>
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
;"Inform 7's can't take other people rule."
<ROUTINE TAKE-PEOPLE ()
    <COND (<FSET? ,PRSO ,PERSONBIT> <TAKE-PEOPLE-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't take what's already taken rule."
<ROUTINE TAKE-ALREADY-TAKEN ()
    <COND (<IN? ,PRSO ,PLAYER> <TAKE-ALREADY-TAKEN-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't take scenery rule."
<ROUTINE TAKE-SCENERY ()
    <COND (<FSET? ,PRSO ,SCENERYBIT> <TAKE-SCENERY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't take what's fixed in place rule."
<ROUTINE TAKE-FIXED ()
    <COND (<FSET? ,PRSO ,FIXEDBIT> <TAKE-FIXED-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard taking rule."
<ROUTINE TAKE-STANDARD () <MOVE ,PRSO ,PLAYER> <FSET ,PRSO ,HANDLEDBIT> <RFALSE>>
;"Inform 7's standard report taking rule."
<ROUTINE TAKE-REPORT () <TAKE-REPORT-A> <RFALSE>>

;"------------------------------------------------------------ dropping"
<ROUTINE DROP-ALREADY ()                ;"in the holder of the actor: the room, or a seat"
    <COND (<IN? ,PRSO <LOC ,PLAYER>> <DROP-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't drop what's not held rule."
<ROUTINE DROP-NOT-HELD ()
    <COND (<NOT <IN? ,PRSO ,PLAYER>> <DROP-NOT-HELD-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard dropping rule."
<ROUTINE DROP-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,HERE> <RFALSE>>
;"Inform 7's standard report dropping rule."
<ROUTINE DROP-REPORT () <DROP-REPORT-A> <RFALSE>>

;"--------------------------------------------------------------- going"
;"Inform 7's action variables for going, set before any rule runs, so
  that Before rules can already see them: the room gone from, the room
  gone to (0 = 'going nowhere') and the door gone through (0 = none)."
<GLOBAL GOING-FROM 0>
<GLOBAL GOING-TO 0>
<GLOBAL GOING-DOOR 0>
;"Work out where going the noun leads, before any rule runs: Inform 7's
  action variables room gone from, room gone to and door gone through."
<ROUTINE GOING-VARIABLES ("AUX" DIR PT)
    <SETG GOING-FROM ,HERE> <SETG GOING-TO 0> <SETG GOING-DOOR 0>
    <SET DIR <GETP ,PRSO ,P?DIR-PROP>>        ;"0 if the noun is not a direction"
    <COND (.DIR <SET PT <GETPT ,HERE .DIR>>)>
    <COND (<AND .PT <EQUAL? <PTSIZE .PT> 1>> <SETG GOING-TO <GETB .PT 0>>)>
    ;"an exit may lead to a door: then through it, to the other side"
    <COND (<AND ,GOING-TO <FSET? ,GOING-TO ,DOORBIT>>
           <SETG GOING-DOOR ,GOING-TO>
           <SETG GOING-TO <OTHER-SIDE ,GOING-DOOR>>)>>
;"Inform 7's can't go through closed doors rule."
<ROUTINE GO-CLOSED-DOOR ()
    <COND (<AND ,GOING-DOOR <NOT <FSET? ,GOING-DOOR ,OPENBIT>>> <GO-CLOSED-DOOR-A> <RTRUE>)>
    <RFALSE>>
;"Inform 7's can't go that way rule."
<ROUTINE GO-THAT-WAY ()
    <COND (<ZERO? ,GOING-TO> <GO-THAT-WAY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's move player and vehicle rule."
<ROUTINE GO-MOVE () <MOVE-PLAYER-TO ,GOING-TO> <RFALSE>>
;"Inform 7's describe room gone into rule."
<ROUTINE GO-DESCRIBE () <DESCRIBE-ROOM> <RFALSE>>

;"---------------------------------------------------- taking inventory"
<ROUTINE INVENTORY-EMPTY ()
    <COND (<ZERO? <COUNT-LISTED ,PLAYER ,ANY-THING?>> <INVENTORY-EMPTY-A> <RTRUE>)>
    <RFALSE>>
;"Inform 7's print standard inventory rule."
<ROUTINE INVENTORY-STANDARD ()
    <INVENTORY-STANDARD-A>
    <MAP-CONTENTS (O ,PLAYER)
        <TELL "  "> <SAY-A .O> <LIST-ANNOTATION .O> <CRLF>>
    <RFALSE>>

<ROUTINE LIST-ANNOTATION (O)
    ;"the list writer internal rule: '(providing light)', '(being worn)'"
    <COND (<AND <FSET? .O ,LITBIT> <FSET? .O ,WORNBIT>>
           <TELL " ("> <LIST-WRITER-K> <TELL ")">)
          (<FSET? .O ,LITBIT> <TELL " ("> <LIST-WRITER-D> <TELL ")">)
          (<FSET? .O ,WORNBIT> <TELL " ("> <LIST-WRITER-L> <TELL ")">)>>
;"A test every thing passes: the inventory counts everything carried."
<ROUTINE ANY-THING? (O) <RTRUE>>

;"------------------------------------------ putting it on / inserting"
<ROUTINE IMPLICITLY-TAKE ()            ;"the carrying requirements rule"
    ;"Inform 7 picks a thing up first: '(first taking the cloak)'"
    <COND (<IN? ,PRSO ,PLAYER> <RFALSE>)>
    <TELL "(first taking "> <SAY-THE ,PRSO> <TELL ")" CR>
    <TRY ,V?TAKING ,V-TAKING ,PRSO 0 1>
    <NOT <IN? ,PRSO ,PLAYER>>>
<ROUTINE TAKE-OFF-FIRST ()            ;"can't drop / put / insert clothes being worn"
    ;"Inform 7 takes a worn thing off first: '(first taking the cloak off)' -
      the words as the real Advent's story file has them - and stops the
      action if it is still worn"
    <COND (<NOT <AND <FSET? ,PRSO ,WORNBIT> <IN? ,PRSO ,PLAYER>>> <RFALSE>)>
    <TELL "(first taking "> <SAY-THE ,PRSO> <TELL " off)" CR>
    <TRY ,V?TAKING-OFF ,V-TAKING-OFF ,PRSO 0 1>
    <FSET? ,PRSO ,WORNBIT>>
;"Inform 7's can't put something on itself rule."
<ROUTINE PUT-ON-ITSELF ()
    <COND (<EQUAL? ,PRSO ,PRSI> <PUT-ON-ITSELF-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't put onto what's not a supporter rule."
<ROUTINE PUT-NOT-SUPPORTER ()
    <COND (<NOT <FSET? ,PRSI ,SUPPORTERBIT>> <PUT-NOT-SUPPORTER-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard putting rule."
<ROUTINE PUT-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,PRSI> <RFALSE>>
;"Inform 7's standard report putting rule."
<ROUTINE PUT-REPORT () <PUT-REPORT-A> <RFALSE>>
;"Inform 7's can't insert something into itself rule."
<ROUTINE INSERT-ITSELF ()
    <COND (<EQUAL? ,PRSO ,PRSI> <INSERT-ITSELF-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't insert into what's not a container rule."
<ROUTINE INSERT-NOT-CONTAINER ()
    <COND (<NOT <FSET? ,PRSI ,CONTAINERBIT>> <INSERT-NOT-CONTAINER-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't insert into closed containers rule."
<ROUTINE INSERT-CLOSED ()
    <COND (<AND <FSET? ,PRSI ,OPENABLEBIT> <NOT <FSET? ,PRSI ,OPENBIT>>>
           <INSERT-CLOSED-A> <RTRUE>)>
    <RFALSE>>
;"Inform 7's standard inserting rule."
<ROUTINE INSERT-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <MOVE ,PRSO ,PRSI> <RFALSE>>
;"Inform 7's standard report inserting rule."
<ROUTINE INSERT-REPORT () <INSERT-REPORT-A> <RFALSE>>

;"------------------------------------------------- wearing / taking off"
<ROUTINE WEAR-NOT-CLOTHING ()
    <COND (<NOT <FSET? ,PRSO ,WEARABLEBIT>> <WEAR-NOT-CLOTHING-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't wear what's already worn rule."
<ROUTINE WEAR-ALREADY ()
    <COND (<FSET? ,PRSO ,WORNBIT> <WEAR-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard wearing rule."
<ROUTINE WEAR-STANDARD () <FSET ,PRSO ,WORNBIT> <RFALSE>>
;"Inform 7's standard report wearing rule."
<ROUTINE WEAR-REPORT () <WEAR-REPORT-A> <RFALSE>>
;"Inform 7's can't take off what's not worn rule."
<ROUTINE TAKE-OFF-NOT-WORN ()
    <COND (<NOT <FSET? ,PRSO ,WORNBIT>> <TAKE-OFF-NOT-WORN-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard taking off rule."
<ROUTINE TAKE-OFF-STANDARD () <FCLEAR ,PRSO ,WORNBIT> <RFALSE>>
;"Inform 7's standard report taking off rule."
<ROUTINE TAKE-OFF-REPORT () <TAKE-OFF-REPORT-A> <RFALSE>>

;"--------------------------------------------------- opening / closing"
<ROUTINE OPEN-UNOPENABLE ()
    <COND (<NOT <FSET? ,PRSO ,OPENABLEBIT>> <OPEN-UNOPENABLE-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't open what's locked rule."
<ROUTINE OPEN-LOCKED ()
    <COND (<FSET? ,PRSO ,LOCKEDBIT> <OPEN-LOCKED-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't open what's already open rule."
<ROUTINE OPEN-ALREADY ()
    <COND (<FSET? ,PRSO ,OPENBIT> <OPEN-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard opening rule."
<ROUTINE OPEN-STANDARD () <FSET ,PRSO ,OPENBIT> <RFALSE>>
;"Inform 7's standard report opening rule."
<ROUTINE OPEN-REPORT () <OPEN-REPORT-A> <RFALSE>>
;"Inform 7's can't close unless openable rule."
<ROUTINE CLOSE-UNOPENABLE ()
    <COND (<NOT <FSET? ,PRSO ,OPENABLEBIT>> <CLOSE-UNOPENABLE-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't close what's already closed rule."
<ROUTINE CLOSE-ALREADY ()
    <COND (<NOT <FSET? ,PRSO ,OPENBIT>> <CLOSE-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard closing rule."
<ROUTINE CLOSE-STANDARD () <FCLEAR ,PRSO ,OPENBIT> <RFALSE>>
;"Inform 7's standard report closing rule."
<ROUTINE CLOSE-REPORT () <CLOSE-REPORT-A> <RFALSE>>

;"------------------------------------------------- locking / unlocking"
<ROUTINE LOCK-NO-LOCK ()
    <COND (<NOT <FSET? ,PRSO ,LOCKABLEBIT>> <LOCK-NO-LOCK-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't lock what's already locked rule."
<ROUTINE LOCK-ALREADY ()
    <COND (<FSET? ,PRSO ,LOCKEDBIT> <LOCK-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't lock what's open rule."
<ROUTINE LOCK-OPEN ()
    <COND (<FSET? ,PRSO ,OPENBIT> <LOCK-OPEN-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't lock without the correct key rule."
<ROUTINE LOCK-WRONG-KEY ()
    <COND (<NOT <EQUAL? <GETP ,PRSO ,P?WITH-KEY> ,PRSI>> <LOCK-WRONG-KEY-A> <RTRUE>)>
    <RFALSE>>
;"Inform 7's standard locking rule."
<ROUTINE LOCK-STANDARD () <FSET ,PRSO ,LOCKEDBIT> <RFALSE>>
;"Inform 7's standard report locking rule."
<ROUTINE LOCK-REPORT () <LOCK-REPORT-A> <RFALSE>>
;"Inform 7's can't unlock without a lock rule."
<ROUTINE UNLOCK-NO-LOCK ()
    <COND (<NOT <FSET? ,PRSO ,LOCKABLEBIT>> <UNLOCK-NO-LOCK-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't unlock what's already unlocked rule."
<ROUTINE UNLOCK-ALREADY ()
    <COND (<NOT <FSET? ,PRSO ,LOCKEDBIT>> <UNLOCK-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't unlock without the correct key rule."
<ROUTINE UNLOCK-WRONG-KEY ()
    <COND (<NOT <EQUAL? <GETP ,PRSO ,P?WITH-KEY> ,PRSI>> <UNLOCK-WRONG-KEY-A> <RTRUE>)>
    <RFALSE>>
;"Inform 7's standard unlocking rule."
<ROUTINE UNLOCK-STANDARD () <FCLEAR ,PRSO ,LOCKEDBIT> <RFALSE>>
;"Inform 7's standard report unlocking rule."
<ROUTINE UNLOCK-REPORT () <UNLOCK-REPORT-A> <RFALSE>>

;"------------------------------------------------------- switching"
<ROUTINE SWITCH-ON-UNSWITCHABLE ()
    <COND (<NOT <FSET? ,PRSO ,DEVICEBIT>> <SWITCH-ON-UNSWITCHABLE-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't switch on what's already on rule."
<ROUTINE SWITCH-ON-ALREADY ()
    <COND (<FSET? ,PRSO ,ONBIT> <SWITCH-ON-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard switching on rule."
<ROUTINE SWITCH-ON-STANDARD () <FSET ,PRSO ,ONBIT> <RFALSE>>
;"Inform 7's standard report switching on rule."
<ROUTINE SWITCH-ON-REPORT () <SWITCH-ON-REPORT-A> <RFALSE>>
;"Inform 7's can't switch off unless switchable rule."
<ROUTINE SWITCH-OFF-UNSWITCHABLE ()
    <COND (<NOT <FSET? ,PRSO ,DEVICEBIT>> <SWITCH-OFF-UNSWITCHABLE-A> <RTRUE>)> <RFALSE>>
;"Inform 7's can't switch off what's already off rule."
<ROUTINE SWITCH-OFF-ALREADY ()
    <COND (<NOT <FSET? ,PRSO ,ONBIT>> <SWITCH-OFF-ALREADY-A> <RTRUE>)> <RFALSE>>
;"Inform 7's standard switching off rule."
<ROUTINE SWITCH-OFF-STANDARD () <FCLEAR ,PRSO ,ONBIT> <RFALSE>>
;"Inform 7's standard report switching off rule."
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
        <YES-OR-NO-A> <TELL "> ">>>              ;"the yes or no question internal rule"
