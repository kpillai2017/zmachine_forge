"lib/parser.zil - a small SYNTAX-driven parser, written in ZIL-lite.

 Include it with <INSERT-FILE \"lib/parser\">. The compiler turns every
 <SYNTAX ...> line into a row of SYNTAX-TABLE (see zforge/compiler/grammar.py);
 this code walks that table at run time, exactly the division of labour
 Infocom used: the compiler builds tables, the game's own code parses.

 What the library gives the game:
   globals  HERE (current room), LIT (0 = dark), PRSA (action number, compare
            with <VERB? TAKE>), PRSO / PRSI (direct / indirect object)
   object   PLAYER - its children are the inventory
   PARSER   read a command; true when PRSA/PRSO/PRSI are set
   PERFORM  run it: SYNTAX preaction, room ACTION, PRSI ACTION, PRSO ACTION,
            then the verb routine - the first that returns true wins

 Noun phrases: [the|a|an] [adjectives...] noun, where the noun is in the
 object's SYNONYM property and each adjective in ADJECTIVE (or SYNONYM).
 Scope: what the player holds, and - when LIT - the room's contents; one
 level down in each (e.g. a cloak on a hook).

 Pronouns: IT / THEM / HIM / HER mean the last direct object (P-IT).
 Ambiguity: when several objects in scope fit, the SYNTAX line's search
 options are tried first - HELD / CARRIED / HAVE prefer what the player
 holds, ON-GROUND / IN-ROOM prefer what they don't, INSIDE-PRSI prefers
 things inside the indirect object; if one candidate is left it is chosen
 and announced '(the rusty key)'. Otherwise the player is asked 'Which do
 you mean, the brass key or the iron key?'; the reply narrows the choice,
 and a reply that is not about those objects is parsed as a new command.
 Missing objects: 'take' or 'put key' fit a SYNTAX line except for the
 last object, so the parser asks 'What do you want to take?' / 'What do
 you want to put the brass key in?' and the reply ('cloak', 'in the box')
 completes the command - Infocom's parsers behaved the same way."

<PROPDEF ACTION 0>
<PROPDEF SYNONYM 0>
<PROPDEF ADJECTIVE 0>

<GLOBAL HERE 0>
<GLOBAL LIT 1>
<GLOBAL PRSA 0>
<GLOBAL PRSO 0>
<GLOBAL PRSI 0>
<GLOBAL P-SYNTAX 0>        ;"the matched SYNTAX-TABLE row"
<GLOBAL P-LEN 0>           ;"number of words typed"
<GLOBAL P-WORD 0>          ;"index of the next word to consume"
<GLOBAL P-IT 0>            ;"what IT / THEM / HIM / HER refer to"
<GLOBAL P-ERROR 0>         ;"why the last noun phrase failed: one of the P-ERR-..."
<GLOBAL P-ERROR-WORD 0>    ;"... and the index of the word to quote"
<CONSTANT P-ERR-NOT-FOUND 1>   ;"'You can't see any X here.'"
<CONSTANT P-ERR-NO-IT 2>       ;"'I'm not sure what \"it\" refers to.'"
<CONSTANT P-ERR-IT-GONE 3>     ;"'You can't see the X here.'"
<GLOBAL P-MISSING 0>       ;"MATCH-SYNTAX ran out of words where object 1 or 2 belongs"
<GLOBAL P-NOUN1 0>         ;"dictionary word naming object 1 (for 'put the KEY in?')"
<GLOBAL P-DEFAULT1 0>      ;"object 1 / 2 came from (FIND flag): announce it"
<GLOBAL P-DEFAULT2 0>
<GLOBAL P-DEFAULTED 0>     ;"set by NOUN-PHRASE when it used (FIND flag)"
<CONSTANT P-MAX-MATCHES 8>
<GLOBAL P-MATCHES1 <ITABLE 9 0>>   ;"candidates for PRSO: word 0 = count"
<GLOBAL P-MATCHES2 <ITABLE 9 0>>   ;"candidates for PRSI"
<GLOBAL READBUF <ITABLE 80 (BYTE)>>
<GLOBAL PARSEBUF <ITABLE 50 (BYTE)>>     ;"2 + 4 bytes x 12 words (§13.6.3)"

<OBJECT PLAYER (DESC "yourself")>

"------------------------------------------------------------ reading"

<ROUTINE PARSER ()
    <COND (<READ-COMMAND> <PARSE-COMMAND>)>>

<ROUTINE READ-COMMAND ()
    ;"read a line into READBUF and tokenise it into PARSEBUF; false if empty"
    <PUTB ,READBUF 0 78>          ;"§15 read: byte 0 = room for 78 characters"
    <PUTB ,READBUF 1 0>           ;"          byte 1 = none typed yet (v5)"
    <PUTB ,PARSEBUF 0 12>         ;"§13.6.3: room for 12 words"
    <READ ,READBUF ,PARSEBUF>
    <SETG P-LEN <GETB ,PARSEBUF 1>>
    <COND (<ZERO? ,P-LEN> <TELL "I beg your pardon?" CR> <RFALSE>)>
    <RTRUE>>

<ROUTINE PARSE-COMMAND ("AUX" ROW FOUND ORPHAN)
    ;"match the words in PARSEBUF against SYNTAX-TABLE"
    <SETG PRSA 0>
    <SETG PRSO 0>
    <SETG PRSI 0>
    <SETG P-SYNTAX 0>
    <SETG P-ERROR 0>
    <DO (I 1 ,P-LEN)
        <COND (<ZERO? <WORD-AT .I>>
               <TELL "I don't know the word \"">
               <PRINT-WORD .I>
               <TELL "\"." CR>
               <RFALSE>)>>
    <SET ROW <+ ,SYNTAX-TABLE 2>>              ;"word 0 is the row count"
    <DO (I 1 <GET ,SYNTAX-TABLE 0>)
        <COND (<EQUAL? <GET .ROW ,S-VERB> <WORD-AT 1>>
               <SET FOUND T>
               <COND (<MATCH-SYNTAX .ROW> <SETG P-SYNTAX .ROW> <RETURN>)
                     (<AND ,P-MISSING <ZERO? .ORPHAN>> <SET ORPHAN .ROW>)>)>
        <SET ROW <+ .ROW <* 2 ,S-SIZE>>>>
    <COND (,P-SYNTAX <RETURN <FINISH-COMMAND>>)
          (.ORPHAN <RETURN <ORPHAN-COMMAND .ORPHAN>>)>
    <PARSE-ERROR .FOUND>
    <RFALSE>>

<ROUTINE PARSE-ERROR (VERB-KNOWN)
    <COND (<NOT .VERB-KNOWN> <TELL "That's not a verb I recognise." CR>)
          (<EQUAL? ,P-ERROR ,P-ERR-NO-IT>
           <TELL "I'm not sure what \"">
           <PRINT-WORD ,P-ERROR-WORD>
           <TELL "\" refers to." CR>)
          (<EQUAL? ,P-ERROR ,P-ERR-IT-GONE> <TELL "You can't see the " D ,P-IT " here." CR>)
          (<EQUAL? ,P-ERROR ,P-ERR-NOT-FOUND>
           <TELL "You can't see any ">
           <PRINT-WORD ,P-ERROR-WORD>
           <TELL " here." CR>)
          (ELSE <TELL "I didn't understand that sentence." CR>)>>

<ROUTINE WORD-AT (I)
    ;"§13.6.3: word I (from 1) is a 4-byte block; its first WORD is the
      dictionary address, or 0 for a word not in the dictionary"
    <GET ,PARSEBUF <- <* 2 .I> 1>>>

<ROUTINE PRINT-WORD (I "AUX" LEN START)
    ;"echo word I as typed: byte 2 of its block = length, byte 3 = position"
    <SET LEN <GETB ,PARSEBUF <* 4 .I>>>
    <SET START <GETB ,PARSEBUF <+ <* 4 .I> 1>>>
    <DO (J .START <- <+ .START .LEN> 1>)
        <PRINTC <GETB ,READBUF .J>>>>

<ROUTINE VERB-WORD? (W "AUX" ROW)
    ;"does any SYNTAX line start with W?"
    <SET ROW <+ ,SYNTAX-TABLE 2>>
    <DO (I 1 <GET ,SYNTAX-TABLE 0>)
        <COND (<EQUAL? <GET .ROW ,S-VERB> .W> <RTRUE>)>
        <SET ROW <+ .ROW <* 2 ,S-SIZE>>>>
    <RFALSE>>

"------------------------------------------------------------ matching"

<ROUTINE MATCH-SYNTAX (ROW "AUX" N O)
    ;"does the command fit this row? sets PRSO / PRSI (first candidates).
      On failure P-MISSING says whether the words simply ran out where
      object 1 or 2 belongs - then the player can be asked for it"
    <SETG P-WORD 2>
    <SETG PRSO 0>
    <SETG PRSI 0>
    <SETG P-MISSING 0>
    <SETG P-DEFAULT1 0>
    <SETG P-DEFAULT2 0>
    <PUT ,P-MATCHES1 0 0>
    <PUT ,P-MATCHES2 0 0>
    <SET N <GET .ROW ,S-NOBJ>>
    <COND (<NOT <MATCH-PREP <GET .ROW ,S-PREP1>>> <MISSING-IF-ENDED 1 .N> <RFALSE>)>
    <COND (<G? .N 0>
           <SET O <NOUN-PHRASE <GET .ROW ,S-PREP2> <GET .ROW ,S-FIND1> ,P-MATCHES1>>
           <COND (<ZERO? .O> <MISSING-IF-ENDED 1 .N> <RFALSE>)>
           <SETG PRSO .O>
           <SETG P-DEFAULT1 ,P-DEFAULTED>
           <SETG P-NOUN1 <WORD-AT <- ,P-WORD 1>>>)>
    <COND (<NOT <MATCH-PREP <GET .ROW ,S-PREP2>>> <MISSING-IF-ENDED 2 .N> <RFALSE>)>
    <COND (<G? .N 1>
           <SET O <NOUN-PHRASE 0 <GET .ROW ,S-FIND2> ,P-MATCHES2>>
           <COND (<ZERO? .O> <MISSING-IF-ENDED 2 .N> <RFALSE>)>
           <SETG PRSI .O>
           <SETG P-DEFAULT2 ,P-DEFAULTED>)>
    <G? ,P-WORD ,P-LEN>>                 ;"no words left over"

<ROUTINE MISSING-IF-ENDED (SLOT N)
    ;"the row needs object SLOT and the player typed nothing more"
    <COND (<AND <G? ,P-WORD ,P-LEN> <NOT <G? .SLOT .N>> <ZERO? ,P-ERROR>>
           <SETG P-MISSING .SLOT>)>>

<ROUTINE MATCH-PREP (PREP)
    <COND (<ZERO? .PREP> <RTRUE>)
          (<G? ,P-WORD ,P-LEN> <RFALSE>)
          (<EQUAL? <WORD-AT ,P-WORD> .PREP> <SETG P-WORD <+ ,P-WORD 1>> <RTRUE>)
          (ELSE <RFALSE>)>>

<ROUTINE NOUN-PHRASE (STOP FIND TBL "AUX" FIRST LAST)
    ;"consume words up to STOP (a preposition) or the end; every object in
      scope that fits goes into TBL, and the first one is returned"
    <SETG P-DEFAULTED 0>
    <SET FIRST ,P-WORD>
    <REPEAT ()
        <COND (<G? ,P-WORD ,P-LEN> <RETURN>)
              (<AND .STOP <EQUAL? <WORD-AT ,P-WORD> .STOP>> <RETURN>)>
        <SETG P-WORD <+ ,P-WORD 1>>>
    <SET LAST <- ,P-WORD 1>>
    <SET FIRST <SKIP-ARTICLES .FIRST .LAST>>
    <COND (<G? .FIRST .LAST>                ;"nothing typed: (FIND flag) default"
           <COND (<L? .FIND 0> <RFALSE>)>
           <SETG P-DEFAULTED T>
           <FIND-FLAGGED .FIND>)
          (ELSE <RESOLVE .FIRST .LAST .TBL>)>>

<ROUTINE SKIP-ARTICLES (FIRST LAST)
    <REPEAT ()
        <COND (<G? .FIRST .LAST> <RETURN>)
              (<ARTICLE? <WORD-AT .FIRST>> <SET FIRST <+ .FIRST 1>>)
              (ELSE <RETURN>)>>
    .FIRST>

<ROUTINE RESOLVE (FIRST LAST TBL)
    ;"words FIRST..LAST name an object: a pronoun, or whatever in scope fits"
    <PUT .TBL 0 0>
    <COND (<AND <EQUAL? .FIRST .LAST> <PRONOUN? <WORD-AT .FIRST>>>
           <PRONOUN-OBJECT .FIRST>)
          (ELSE
           <SEARCH-SCOPE .FIRST .LAST .TBL>
           <COND (<G? <GET .TBL 0> 0> <GET .TBL 1>)
                 (ELSE
                  <SETG P-ERROR ,P-ERR-NOT-FOUND>
                  <SETG P-ERROR-WORD .LAST>
                  <RFALSE>)>)>>

<ROUTINE ARTICLE? (W) <EQUAL? .W ,W?THE ,W?A ,W?AN>>

<ROUTINE PRONOUN? (W) <EQUAL? .W ,W?IT ,W?THEM ,W?HIM ,W?HER>>

<ROUTINE PRONOUN-OBJECT (I)
    <COND (<ZERO? ,P-IT>
           <SETG P-ERROR ,P-ERR-NO-IT>
           <SETG P-ERROR-WORD .I>
           <RFALSE>)
          (<NOT <IN-SCOPE? ,P-IT>> <SETG P-ERROR ,P-ERR-IT-GONE> <RFALSE>)
          (ELSE ,P-IT)>>

"-------------------------------------------------------------- scope"

<ROUTINE SEARCH-SCOPE (FIRST LAST TBL)
    <SEARCH-IN ,PLAYER .FIRST .LAST .TBL>
    <COND (,LIT <SEARCH-IN ,HERE .FIRST .LAST .TBL>)>>

<ROUTINE SEARCH-IN (CONTAINER FIRST LAST TBL)
    <MAP-CONTENTS (O .CONTAINER)
        <COND (<MATCHES? .O .FIRST .LAST> <ADD-MATCH .TBL .O>)>
        <MAP-CONTENTS (C .O)
            <COND (<MATCHES? .C .FIRST .LAST> <ADD-MATCH .TBL .C>)>>>>

<ROUTINE ADD-MATCH (TBL O "AUX" N)
    <SET N <GET .TBL 0>>
    <COND (<L? .N ,P-MAX-MATCHES>
           <SET N <+ .N 1>>
           <PUT .TBL .N .O>
           <PUT .TBL 0 .N>)>>

<ROUTINE HELD? (O "AUX" L)
    ;"carried by the player, or inside something they carry"
    <SET L <LOC .O>>
    <OR <EQUAL? .L ,PLAYER> <AND .L <IN? .L ,PLAYER>>>>

<ROUTINE IN-SCOPE? (O "AUX" L)
    ;"the same places SEARCH-SCOPE looks"
    <SET L <LOC .O>>
    <COND (<HELD? .O> <RTRUE>)
          (<ZERO? ,LIT> <RFALSE>)
          (<EQUAL? .L ,HERE> <RTRUE>)
          (ELSE <AND .L <IN? .L ,HERE>>)>>

<ROUTINE MATCHES? (O FIRST LAST)
    ;"the last word is a noun of O; every earlier word describes O"
    <COND (<NOT <IN-PROP? .O ,P?SYNONYM <WORD-AT .LAST>>> <RFALSE>)>
    <DO (I .FIRST <- .LAST 1>)
        <COND (<NOT <DESCRIBES? .O <WORD-AT .I>>> <RFALSE>)>>
    <RTRUE>>

<ROUTINE DESCRIBES? (O W)
    <OR <IN-PROP? .O ,P?ADJECTIVE .W> <IN-PROP? .O ,P?SYNONYM .W> <ARTICLE? .W>>>

<ROUTINE IN-PROP? (O PROP W "AUX" PT N)
    ;"is dictionary word W in O's word-list property PROP? (§12.4)"
    <SET PT <GETPT .O .PROP>>
    <COND (<ZERO? .PT> <RFALSE>)>
    <SET N </ <PTSIZE .PT> 2>>
    <DO (I 0 <- .N 1>)
        <COND (<EQUAL? <GET .PT .I> .W> <RTRUE>)>>
    <RFALSE>>

<ROUTINE FIND-FLAGGED (FLAG "AUX" FOUND)
    <MAP-CONTENTS (O ,PLAYER)
        <COND (<FSET? .O .FLAG> <SET FOUND .O> <RETURN>)>>
    <COND (<AND <ZERO? .FOUND> ,LIT>
           <MAP-CONTENTS (O ,HERE)
               <COND (<FSET? .O .FLAG> <SET FOUND .O> <RETURN>)>>)>
    .FOUND>

"------------------------------------------------ finishing a command"

<ROUTINE FINISH-COMMAND ("AUX" O)
    ;"a row fits: settle ambiguity (object 2 first, so INSIDE-PRSI can use
      it), announce defaults, then remember IT"
    <SETG PRSA <GET ,P-SYNTAX ,S-ACTION>>
    <COND (<G? <GET ,P-MATCHES2 0> 1>
           <SET O <CHOOSE ,P-MATCHES2 <GET ,P-SYNTAX ,S-OPTS2>>>
           <COND (<L? .O 0> <RFALSE>)
                 (<ZERO? .O> <RETURN <PARSE-COMMAND>>)>   ;"the reply was a new command"
           <SETG PRSI .O>)>
    <COND (<G? <GET ,P-MATCHES1 0> 1>
           <SET O <CHOOSE ,P-MATCHES1 <GET ,P-SYNTAX ,S-OPTS1>>>
           <COND (<L? .O 0> <RFALSE>)
                 (<ZERO? .O> <RETURN <PARSE-COMMAND>>)>
           <SETG PRSO .O>)>
    <COND (,P-DEFAULT1 <TELL "(the " D ,PRSO ")" CR>)>
    <COND (,P-DEFAULT2 <TELL "(the " D ,PRSI ")" CR>)>
    <COND (,PRSO <SETG P-IT ,PRSO>)>
    <RTRUE>>

<ROUTINE CHOOSE (TBL OPTS)
    ;"several candidates: let the SYNTAX search options narrow them; if one
      is left say which, otherwise ask"
    <COND (<BAND .OPTS ,SO-HELD> <KEEP-IF .TBL ,SO-HELD>)>
    <COND (<BAND .OPTS ,SO-ROOM> <KEEP-IF .TBL ,SO-ROOM>)>
    <COND (<AND <BAND .OPTS ,SO-INSIDE> ,PRSI> <KEEP-IF .TBL ,SO-INSIDE>)>
    <COND (<EQUAL? <GET .TBL 0> 1>
           <TELL "(the " D <GET .TBL 1> ")" CR>
           <GET .TBL 1>)
          (ELSE <WHICH? .TBL>)>>

<ROUTINE KEEP-IF (TBL TEST "AUX" N KEPT O)
    ;"narrow TBL to the candidates passing TEST - unless none would be left
      (a preference, not a rule: the verb routine has the final say)"
    <SET N <GET .TBL 0>>
    <DO (I 1 .N)
        <COND (<PASSES? <GET .TBL .I> .TEST> <SET KEPT <+ .KEPT 1>>)>>
    <COND (<ZERO? .KEPT> <RFALSE>)>
    <SET KEPT 0>
    <DO (I 1 .N)
        <SET O <GET .TBL .I>>
        <COND (<PASSES? .O .TEST> <SET KEPT <+ .KEPT 1>> <PUT .TBL .KEPT .O>)>>
    <PUT .TBL 0 .KEPT>
    <RTRUE>>

<ROUTINE PASSES? (O TEST)
    <COND (<EQUAL? .TEST ,SO-HELD> <HELD? .O>)
          (<EQUAL? .TEST ,SO-ROOM> <NOT <HELD? .O>>)
          (ELSE <IN? .O ,PRSI>)>>

"------------------------------------------------------ asking questions"

<ROUTINE WHICH? (TBL "AUX" N HITS RESULT)
    ;"ask until one candidate is left. Returns it; 0 when the reply is not
      about these objects (it is left in PARSEBUF as a new command);
      -1 when the reply was empty"
    <REPEAT ()
        <SET N <GET .TBL 0>>
        <TELL "Which do you mean, ">
        <DO (I 1 .N)
            <TELL "the " D <GET .TBL .I>>
            <COND (<L? .I <- .N 1>> <TELL ", ">)
                  (<EQUAL? .I <- .N 1>> <TELL " or ">)>>
        <TELL "?" CR "> ">
        <COND (<NOT <READ-COMMAND>> <SET RESULT -1> <RETURN>)>
        <SET HITS <NARROW .TBL>>
        <COND (<EQUAL? .HITS 1> <SET RESULT <GET .TBL 1>> <RETURN>)
              (<ZERO? .HITS> <RETURN>)>>
    .RESULT>

<ROUTINE NARROW (TBL "AUX" N KEPT O)
    ;"keep the candidates that EVERY word of the reply describes"
    <SET N <GET .TBL 0>>
    <DO (I 1 .N)
        <SET O <GET .TBL .I>>
        <COND (<REPLY-DESCRIBES? .O> <SET KEPT <+ .KEPT 1>> <PUT .TBL .KEPT .O>)>>
    <COND (.KEPT <PUT .TBL 0 .KEPT>)>
    .KEPT>

<ROUTINE REPLY-DESCRIBES? (O)
    <DO (I 1 ,P-LEN)
        <COND (<NOT <DESCRIBES? .O <WORD-AT .I>>> <RFALSE>)>>
    <RTRUE>>

<ROUTINE ORPHAN-COMMAND (ROW "AUX" SLOT R)
    ;"the command fits ROW but stops short of an object: ask for it (and
      for object 2 as well if 'put' alone left both out)"
    <MATCH-SYNTAX .ROW>               ;"re-run: restores PRSO and P-MISSING for ROW"
    <SET SLOT ,P-MISSING>
    <REPEAT ()
        <ASK-FOR .ROW .SLOT>
        <SET R <COND (<READ-COMMAND> <ORPHAN-REPLY .ROW .SLOT>) (ELSE -1)>>
        <COND (<NOT <EQUAL? .R 1>> <RETURN>)
              (<AND <EQUAL? .SLOT 1> <EQUAL? <GET .ROW ,S-NOBJ> 2>> <SET SLOT 2>)
              (ELSE <RETURN>)>>
    <COND (<EQUAL? .R 1> <SETG P-SYNTAX .ROW> <FINISH-COMMAND>)
          (<ZERO? .R> <PARSE-COMMAND>)
          (ELSE <RFALSE>)>>

<ROUTINE ASK-FOR (ROW SLOT "AUX" PREP)
    ;"'What do you want to take?' / 'What do you want to put the key in?'
      PRINTB prints a dictionary word (§15 print_addr), so the question
      still reads right after the player's reply has replaced PARSEBUF"
    <TELL "What do you want to ">
    <PRINTB <GET .ROW ,S-VERB>>
    <COND (<EQUAL? .SLOT 1> <SET PREP <GET .ROW ,S-PREP1>>)
          (ELSE
           <TELL " the ">
           <COND (<G? <GET ,P-MATCHES1 0> 1> <PRINTB ,P-NOUN1>) (ELSE <TELL D ,PRSO>)>
           <SET PREP <GET .ROW ,S-PREP2>>)>
    <COND (.PREP <TELL " "> <PRINTB .PREP>)>
    <TELL "?" CR "> ">>

<ROUTINE ORPHAN-REPLY (ROW SLOT "AUX" TBL PREP FIRST O)
    ;"1 = the reply names object SLOT; 0 = it is a new command (left in
      PARSEBUF); -1 = it named nothing here (the error is printed)"
    <SET TBL <COND (<EQUAL? .SLOT 1> ,P-MATCHES1) (ELSE ,P-MATCHES2)>>
    <SET PREP <GET .ROW <COND (<EQUAL? .SLOT 1> ,S-PREP1) (ELSE ,S-PREP2)>>>
    <DO (I 1 ,P-LEN) <COND (<ZERO? <WORD-AT .I>> <RFALSE>)>>
    <COND (<VERB-WORD? <WORD-AT 1>> <RFALSE>)>
    <SET FIRST 1>
    <COND (<AND .PREP <EQUAL? <WORD-AT 1> .PREP>> <SET FIRST 2>)>   ;"'in the box'"
    <SET FIRST <SKIP-ARTICLES .FIRST ,P-LEN>>
    <COND (<G? .FIRST ,P-LEN> <RFALSE>)>
    <SETG P-ERROR 0>
    <SET O <RESOLVE .FIRST ,P-LEN .TBL>>
    <COND (<ZERO? .O> <PARSE-ERROR T> <RETURN -1>)>
    <COND (<EQUAL? .SLOT 1> <SETG PRSO .O> <SETG P-NOUN1 <WORD-AT ,P-LEN>>)
          (ELSE <SETG PRSI .O>)>
    <RTRUE>>

"------------------------------------------------------------ running"

<ROUTINE PERFORM ("AUX" R)
    <SET R <GET ,P-SYNTAX ,S-PREACTION>>
    <COND (<AND .R <APPLY .R>> <RTRUE>)>
    <COND (<AND <SET R <GETP ,HERE ,P?ACTION>> <APPLY .R>> <RTRUE>)>
    <COND (<AND ,PRSI <SET R <GETP ,PRSI ,P?ACTION>> <APPLY .R>> <RTRUE>)>
    <COND (<AND ,PRSO <SET R <GETP ,PRSO ,P?ACTION>> <APPLY .R>> <RTRUE>)>
    <APPLY <GET ,P-SYNTAX ,S-ROUTINE>>>
