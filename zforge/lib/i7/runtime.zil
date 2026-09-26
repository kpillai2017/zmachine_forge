"zforge/lib/i7/runtime.zil - the I7-lite runtime library: the turn sequence.

 A game compiled from Inform 7 source starts with <INSERT-FILE \"lib/i7/runtime\">.
 The compiler then supplies, for this library to use:
   constants  STORY-TITLE STORY-AUTHOR STORY-HEADLINE RELEASE-NUMBER
              SCORING (1 = Use scoring) MAX-SCORE FIRST-ROOM
   tables     WHEN-PLAY-BEGINS-RULES  EVERY-TURN-RULES  (LTABLEs of rules)
              DOORS (an LTABLE of the story's doors)
              GENERAL-RULES (the six stages for 'doing something' rules)
   one routine V-<ACTION> and one rulebook table per action (actions.zil)

 The turn sequence is Inform 7's: When play begins; the banner; a look;
 then, every turn: read a command, run the action, then (for actions in
 the world) the Every turn rules and the turn count. Out-of-world actions
 (saving, quitting, the score) take no time."

<INSERT-FILE "lib/parser">
<INSERT-FILE "lib/i7/say">
<INSERT-FILE "lib/i7/world">
<INSERT-FILE "lib/i7/actions">
<INSERT-FILE "lib/i7/activities">
<INSERT-FILE "lib/i7/standard">

;"In ZIL a flag exists once some object uses it. This object - which is
  never anywhere - uses every flag the library tests, so a small game
  that has, say, no doors still compiles."
<OBJECT LIBRARY-FLAGS
    (DESC "library flags")
    (FLAGS LITBIT SCENERYBIT FIXEDBIT SUPPORTERBIT CONTAINERBIT OPENBIT
           OPENABLEBIT LOCKEDBIT LOCKABLEBIT WEARABLEBIT WORNBIT PROPERBIT
           PLURALBIT PERSONBIT DEVICEBIT ONBIT EDIBLEBIT DOORBIT VISITEDBIT
           HANDLEDBIT ROOMBIT MENTIONEDBIT)>

<GLOBAL TURN-COUNT 1>          ;"Inform 7's turn count starts at 1"
<GLOBAL SCORE 0>
<GLOBAL STORY-ENDED 0>         ;"0 = playing, 1 = ended, 2 = ended finally"
<GLOBAL END-SAYING 0>          ;"end the story saying \"...\": the text, or 0"
<GLOBAL OUT-OF-WORLD 0>        ;"set by out-of-world actions: no time passes"

<ROUTINE GO ()
    <MOVE-PLAYER-TO ,FIRST-ROOM>
    <FSET ,PLAYER ,PROPERBIT>
    <SETG P-I7-STYLE 1>                 ;"the parser speaks like Inform 7"
    <SPLIT 1>
    <SCREEN 0>
    <FOLLOW-RULES ,WHEN-PLAY-BEGINS-RULES>
    <COND (,STORY-ENDED <END-OF-STORY> <RTRUE>)>
    <BANNER>
    <SETG LIT <LIGHT-HERE?>>
    <TRY ,V?LOOKING ,V-LOOKING 0 0>    ;"Inform 7's first look is the looking action"
    <TURN-LOOP>>

<ROUTINE BANNER ()      ;"the printing the banner text activity (activities.zil)"
    <CARRY-OUT ,PRINTING-BANNER-ACTIVITY 0 ,BANNER-STANDARD>>

<ROUTINE TURN-LOOP ()
    <REPEAT ()
        <SETG LIT <LIGHT-HERE?>>
        <STATUS-LINE>
        <PARA-ABSORB>                      ;"the prompt has its own blank line"
        <SETG PRIOR-NAMED 0>               ;"a new turn: nothing has been named yet"
        <TELL CR ">">
        <SETG OUT-OF-WORLD 0>
        <COND (<NOT <PARSER>>)
              (<VERB? UNDO> <UNDO-TURN>)          ;"UNDO must not take a snapshot"
              (<EQUAL? <ZOP SAVE_UNDO> 2>         ;"we are back here after an UNDO"
               <TELL "[Previous turn undone.]" CR>)
              (ELSE
               <APPLY <GET ,P-SYNTAX ,S-ROUTINE>>
               <COND (<AND <NOT ,OUT-OF-WORLD> <NOT ,STORY-ENDED>>
                      <FOLLOW-RULES ,EVERY-TURN-RULES>
                      <SETG TURN-COUNT <+ ,TURN-COUNT 1>>)>)>
        <COND (,STORY-ENDED <END-OF-STORY> <RTRUE>)>>>

<ROUTINE UNDO-TURN ()
    <COND (<EQUAL? <ZOP RESTORE_UNDO> 0>
           <TELL "You can't \"undo\" what hasn't been done!" CR>)>>

<ROUTINE SAY-DARKNESS () <TELL "Darkness">>

<ROUTINE STATUS-LINE ("AUX" WIDTH OWED SAID)
    <SET WIDTH <GETB 0 33>>                   ;"§11: header byte $21 = screen width"
    <SCREEN 1>
    <HLIGHT 1>
    <CURSET 1 1>
    <DO (I 1 .WIDTH) <PRINTC 32>>
    <CURSET 1 2>
    ;"Inform 7's 'player's surroundings': names come from the activities.
      A rule's say must not leave a line break in the status line, so the
      paragraph state is set aside while it runs."
    <SET OWED ,PARA-BREAK> <SET SAID ,SAY-P> <SETG PARA-BREAK 0>
    <COND (,LIT <PRINT-NAME ,HERE>)
          (ELSE <CARRY-OUT ,PRINTING-DARK-NAME-ACTIVITY 0 ,SAY-DARKNESS>)>
    <SETG PARA-BREAK .OWED> <SETG SAY-P .SAID>
    <CURSET 1 <- .WIDTH 12>>
    <COND (,SCORING <TELL N ,SCORE "/" N ,TURN-COUNT>) (ELSE <TELL N ,TURN-COUNT>)>
    <HLIGHT 0>
    <SCREEN 0>>

<ROUTINE END-OF-STORY ()
    <PARA-ABSORB>
    <CRLF> <CRLF>
    <TELL "    *** ">
    <COND (,END-SAYING <PRINT ,END-SAYING>)
          (<EQUAL? ,STORY-ENDED 2> <TELL "The End">)
          (ELSE <TELL "The End">)>
    <TELL " ***" CR CR>
    <COND (,SCORING
           <TELL CR "In that game you scored " N ,SCORE " out of a possible "
                 N ,MAX-SCORE ", in " N ,TURN-COUNT " turn">
           <COND (<NOT <EQUAL? ,TURN-COUNT 1>> <TELL "s">)>
           <TELL "." CR>)>
    <FINAL-QUESTION>>

<ROUTINE FINAL-QUESTION ()
    <REPEAT ()
        <TELL CR "Would you like to RESTART, RESTORE a saved game, QUIT or UNDO the last command?" CR "> ">
        <COND (<READ-COMMAND>
               <COND (<EQUAL? <WORD-AT 1> ,W?RESTART> <RESTART>)
                     (<EQUAL? <WORD-AT 1> ,W?RESTORE>
                      <COND (<NOT <RESTORE>> <TELL "Restore failed." CR>)>)
                     (<EQUAL? <WORD-AT 1> ,W?QUIT ,W?Q> <QUIT>)
                     (<EQUAL? <WORD-AT 1> ,W?UNDO>
                      <COND (<EQUAL? <ZOP RESTORE_UNDO> 0>
                             <TELL "You can't \"undo\" what hasn't been done!" CR>)>)>)>>>
