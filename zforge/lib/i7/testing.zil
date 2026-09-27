"zforge/lib/i7/testing.zil - Inform 7's testing commands, in ZIL-lite.

 Only a game compiled with 'zforge compile --testing' includes this file
 (Inform 7 leaves these commands out of a released game too). They are
 for studying how a game works while you play it:

   RULES       shows each rule as it applies:  [Rule \"can't take yourself rule\" applies.]
   ACTIONS     shows each action as it starts and how it ends:
                 [taking the book]  ...  [taking the book - succeeded]
   TREE        shows where every room and thing is, one level of
               indent for each 'in', 'on', 'carried by' or 'worn by'.

 The compiler adds the calls: RULE-APPLIES at the top of every rule, once
 the rule's own conditions have matched (the library's rules through a
 small wrapper), and ACTION-STARTS / ACTION-ENDS around every action."

<GLOBAL RULES-TRACING 0>
<GLOBAL ACTIONS-LISTING 0>

;"---------------------------------------------- switching them on and off"

<ROUTINE RULES-ON ()
    <SETG RULES-TRACING 1>
    <TELL "Rules tracing now switched on. Type \"rules off\" to switch it off again." CR>
    <RTRUE>>

<ROUTINE RULES-OFF ()
    <SETG RULES-TRACING 0>
    <TELL "Rules tracing now switched off." CR>
    <RTRUE>>

<ROUTINE ACTIONS-ON ()
    <SETG ACTIONS-LISTING 1>
    <TELL "Actions listing on." CR>
    <RTRUE>>

<ROUTINE ACTIONS-OFF ()
    <SETG ACTIONS-LISTING 0>
    <TELL "Actions listing off." CR>
    <RTRUE>>

;"---------------------------------------------- RULES"

<ROUTINE RULE-APPLIES (NAME)
    <COND (,RULES-TRACING <TELL "[Rule \""> <PRINT .NAME> <TELL "\" applies.]" CR>)>>

;"---------------------------------------------- ACTIONS
  An action's name comes in two parts around its first thing, as Inform 7
  writes them: 'putting' + the book + 'on' + the table."

<ROUTINE ACTION-STARTS (VERB REST N)
    <COND (,ACTIONS-LISTING <TELL "["> <SAY-ACTION .VERB .REST .N> <TELL "]" CR>)>>

<ROUTINE ACTION-ENDS (VERB REST N DONE)
    <COND (,ACTIONS-LISTING
           <TELL "["> <SAY-ACTION .VERB .REST .N>
           <COND (.DONE <TELL " - succeeded]" CR>) (ELSE <TELL " - failed]" CR>)>)>>

<ROUTINE SAY-ACTION (VERB REST N)
    <PRINT .VERB>
    <COND (<AND <G? .N 0> ,PRSO> <TELL " "> <TRACE-NAME ,PRSO>)>
    <COND (.REST <TELL " "> <PRINT .REST>)>
    <COND (<AND <G? .N 1> ,PRSI> <TELL " "> <TRACE-NAME ,PRSI>)>>

<ROUTINE TRACE-NAME (O)
    ;"'the book', 'north', 'yourself' - without changing what [are] agrees with"
    <COND (<NOT <FSET? .O ,PROPERBIT>> <TELL "the ">)>
    <PRINT-NAME .O>>

;"---------------------------------------------- TREE
  The compiler lists every room and thing in ALL-OBJECTS. Rooms have no
  place of their own, so they are the roots; anything else with no place
  is off-stage (not yet in play, or taken out of it)."

<ROUTINE SHOW-TREE ("AUX" N O HEADED)
    <SET N <GET ,ALL-OBJECTS 0>>
    <DO (I 1 .N)
        <SET O <GET ,ALL-OBJECTS .I>>
        <COND (<AND <FSET? .O ,ROOMBIT> <NOT <LOC .O>>> <TREE-BRANCH .O 0>)>>
    <DO (I 1 .N)
        <SET O <GET ,ALL-OBJECTS .I>>
        <COND (<AND <NOT <FSET? .O ,ROOMBIT>> <NOT <LOC .O>>>
               <COND (<NOT .HEADED> <TELL "Nowhere (off-stage):" CR> <SET HEADED 1>)>
               <TREE-BRANCH .O 1>)>>
    <RTRUE>>

<ROUTINE TREE-BRANCH (O DEPTH "AUX" C)
    <DO (I 1 .DEPTH) <TELL "  ">>
    <PRINT-NAME .O>
    <COND (<FSET? .O ,WORNBIT> <TELL " (worn)">)>
    <CRLF>
    <SET C <FIRST? .O>>
    <REPEAT ()
        <COND (<NOT .C> <RETURN>)>
        <TREE-BRANCH .C <+ .DEPTH 1>>
        <SET C <NEXT? .C>>>>
