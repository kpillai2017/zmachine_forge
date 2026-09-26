"zforge/lib/i7/activities.zil - Inform 7 activities.

 An action is WHAT happens ('taking the lamp'); an activity is HOW the
 story does one of its routine jobs: printing a name, the banner, a room's
 paragraphs. Each activity has three rulebooks, as in Inform 7:

   before ...     every rule runs (unless one decides)
   for ...        the first rule that applies DECIDES, and then the
                  library's own way is skipped; 'continue the activity'
                  in a rule means 'no decision, carry on'
   after ...      every rule runs

 The compiler writes one global per library activity: a TABLE of the
 three rulebooks (LTABLEs of rule routines, most specific first), e.g.
   <GLOBAL PRINTING-NAME-ACTIVITY <TABLE <LTABLE> <LTABLE ,RULE-12> <LTABLE>>>

 Two ways to use one - both are Inform 7's:
   <CARRY-OUT ,A .OBJ ,DEFAULT>   the library's hooks: before, for (or
                                  DEFAULT, the library's own way), after
   BEGIN / HANDLING? / END        the three steps separately, for an
                                  author's rule that does its own default
                                  ('begin the X activity; if handling the
                                  X activity: ...; end the X activity')

 ACT-OBJ is Inform 7's 'the item described': the object the activity is
 about ('printing the name of the lamp'). Activities nest (printing a
 room's paragraphs prints names), so BEGIN saves the old one on a small
 stack and END puts it back."

<GLOBAL ACT-OBJ 0>                   ;"the item described"
<CONSTANT ACT-DEPTH-MAX 16>
<GLOBAL ACT-STACK <ITABLE 16>>
<GLOBAL ACT-DEPTH 0>

<ROUTINE BEGIN-ACTIVITY (ACT OBJ)
    ;"'begin the X activity': remember the item described, run the befores"
    <COND (<L? ,ACT-DEPTH ,ACT-DEPTH-MAX>
           <PUT ,ACT-STACK ,ACT-DEPTH ,ACT-OBJ>
           <SETG ACT-DEPTH <+ ,ACT-DEPTH 1>>)>
    <SETG ACT-OBJ .OBJ>
    <FOLLOW-RULES <GET .ACT 0>>>

<ROUTINE HANDLING? (ACT)
    ;"'if handling the X activity': run the for rules; true if NONE decided,
      so the caller's own way should run"
    <COND (<FOLLOW-RULES <GET .ACT 1>> <RFALSE>)>
    <RTRUE>>

<ROUTINE END-ACTIVITY (ACT)
    ;"'end the X activity': run the afters, put the item described back"
    <FOLLOW-RULES <GET .ACT 2>>
    <COND (<G? ,ACT-DEPTH 0>
           <SETG ACT-DEPTH <- ,ACT-DEPTH 1>>
           <SETG ACT-OBJ <GET ,ACT-STACK ,ACT-DEPTH>>)>>

<ROUTINE CARRY-OUT (ACT OBJ DEFAULT)
    ;"carry out the X activity: DEFAULT is the library's own way (a routine
      of no arguments, which finds the object in ACT-OBJ), or 0 for none"
    <BEGIN-ACTIVITY .ACT .OBJ>
    <COND (<AND <HANDLING? .ACT> .DEFAULT> <APPLY .DEFAULT>)>
    <END-ACTIVITY .ACT>>

;"------------------------------------------------------ printing the name
  Every name the library prints comes here. Inform 7's own way (the
  standard name printing rule) prints the object's printed name. A rule
  for printing the name of X that says '[the X]' again would ask for X's
  name forever: while X's name is being printed, asking for it again
  gives the plain printed name (a zforge choice, ADR-031)."
<GLOBAL NAMING 0>                    ;"the object whose name is being printed"

<ROUTINE PRINT-NAME (O "AUX" OUTER)
    <COND (<EQUAL? .O ,NAMING> <TELL D .O> <RTRUE>)>
    <SET OUTER ,NAMING>
    <SETG NAMING .O>
    <CARRY-OUT ,PRINTING-NAME-ACTIVITY .O ,PRINT-NAME-STANDARD>
    <SETG NAMING .OUTER>>

<ROUTINE PRINT-NAME-STANDARD ()      ;"the standard name printing rule"
    <TELL D ,ACT-OBJ>>

;"---------------------------------------------- the rest of the library's
  own ways: each is the text that stood in the library before activities"
<ROUTINE BANNER-STANDARD ()          ;"the standard banner text"
    <PARA-ABSORB>
    <CRLF>
    <HLIGHT 2> <TELL ,STORY-TITLE> <HLIGHT 0> <CRLF>
    <TELL ,STORY-HEADLINE " by " ,STORY-AUTHOR CR>
    <TELL "Release " N ,RELEASE-NUMBER " / Serial number ">
    <DO (I 18 23) <PRINTC <GETB 0 .I>>>     ;"§11: header bytes $12-$17"
    <TELL " / zforge I7-lite" CR CR>>
