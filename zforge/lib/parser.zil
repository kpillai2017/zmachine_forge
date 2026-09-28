"zforge/lib/parser.zil - a small SYNTAX-driven parser, written in ZIL-lite.

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

<OBJECT PLAYER (DESC "yourself")
    (SYNONYM ME MYSELF SELF YOURSELF)>   ;"'x me' (found when the player is in scope)"

;"0 = Infocom-style messages (\"I don't know the word ...\"); the I7-lite
  runtime sets 1 for Inform 7's wording (\"You can't see any such thing.\")"
<GLOBAL P-I7-STYLE 0>

;"A game compiled from Inform 7 sets <COMPILATION-FLAG I7 T> before
  including this file: its parser errors then go to the runtime's
  I7-PARSER-ERROR, which runs Inform 7's 'printing a parser error' activity.
  ZIL games compile exactly as before."
<COMPILATION-FLAG-DEFAULT I7 <>>

;"Inform 7 lets the first object be several: TAKE ALL, DROP ALL BUT THE
  LAMP, TAKE THE LAMP AND THE KEYS, DROP LAMP, KEYS AND FOOD - where the
  grammar line says [things] (a SYNTAX with (MANY): S-OPTS1 has SO-MANY). The parser lists them
  in P-MULTI; the I7 runtime runs the action once for each."
<IFFLAG (I7
<CONSTANT P-ERR-MULTI 4>        ;"several objects, but the verb takes one"
<CONSTANT P-ERR-NOTHING 5>      ;"ALL, but there is nothing it could mean"
<GLOBAL P-MULTIPLE 0>           ;"true: run the action for each object in P-MULTI"
<GLOBAL P-MULTI <ITABLE 17 0>>  ;"the objects: word 0 = count (at most 16)"
<GLOBAL P-AMBIG <ITABLE 48 0>>  ;"a list's unclear items: [n, o1..on] for each"
<GLOBAL P-AMBIG-LEN 0>          ;"words of P-AMBIG in use"
<GLOBAL P-SOFAR-ROW 0>          ;"[parser command so far]: the row, the slot and"
<GLOBAL P-SOFAR-SLOT 0>         ;"object 1 when 'can't use multiple objects' was"
<GLOBAL P-SOFAR-OBJ 0>          ;"raised"
<GLOBAL P-USED-ALL 0>           ;"the phrase said ALL / EVERYTHING"
<GLOBAL P-ALL-SEEN 0>           ;"how many things ALL could have meant, before any was left out"
) (ELSE)>

"------------------------------------------------------------ reading"

<ROUTINE PARSER ()
    <COND (<READ-COMMAND>
           <IFFLAG (I7 <COND (<AGAIN-OR-KEEP> <PARSE-COMMAND>)>)
                   (ELSE <PARSE-COMMAND>)>)>>

<IFFLAG (I7
;"Inform's AGAIN (or G): the last command typed at the prompt, typed again -
  even one that failed. Its text and its words are kept here; an answer to
  'Which do you mean' is not kept, so AGAIN repeats the whole command."
<GLOBAL AGAIN-READBUF <ITABLE 80 (BYTE)>>
<GLOBAL AGAIN-PARSEBUF <ITABLE 50 (BYTE)>>
<GLOBAL P-CAN-AGAIN 0>          ;"true once a command has been kept"

<ROUTINE AGAIN-OR-KEEP ()
    ;"AGAIN or G alone: put back the kept command (false if there is none);
      any other command is kept, for the next AGAIN"
    <COND (<AND <EQUAL? ,P-LEN 1> <EQUAL? <WORD-AT 1> ,W?AGAIN ,W?G>>
           <COND (<ZERO? ,P-CAN-AGAIN>
                  <TELL "You can hardly repeat that." CR>
                  <RFALSE>)>
           <COPY-BYTES ,AGAIN-READBUF ,READBUF 80>
           <COPY-BYTES ,AGAIN-PARSEBUF ,PARSEBUF 50>
           <SETG P-LEN <GETB ,PARSEBUF 1>>)
          (ELSE
           <COPY-BYTES ,READBUF ,AGAIN-READBUF 80>
           <COPY-BYTES ,PARSEBUF ,AGAIN-PARSEBUF 50>
           <SETG P-CAN-AGAIN 1>)>
    <RTRUE>>

<ROUTINE COPY-BYTES (FROM TO N)
    ;"the first N bytes of table FROM into table TO. The word buffer's
      positions count from the start of the text buffer (§13.6.3), so the
      two copies stay in step."
    <DO (I 0 <- .N 1>)
        <PUTB .TO .I <GETB .FROM .I>>>>
) (ELSE)>

<ROUTINE READ-COMMAND ()
    ;"read a line into READBUF and tokenise it into PARSEBUF; false if empty"
    <PUTB ,READBUF 0 78>          ;"§15 read: byte 0 = room for 78 characters"
    <PUTB ,READBUF 1 0>           ;"          byte 1 = none typed yet (v5)"
    <PUTB ,PARSEBUF 0 12>         ;"§13.6.3: room for 12 words"
    <READ ,READBUF ,PARSEBUF>
    <SETG P-LEN <GETB ,PARSEBUF 1>>
    <COND (<ZERO? ,P-LEN>
           <IFFLAG (I7 <I7-PARSER-ERROR ,PE-PARDON>)
                   (ELSE <TELL "I beg your pardon?" CR>)>
           <RFALSE>)>
    <RTRUE>>

<IFFLAG (I7
;"Topics (Inform's [text]): a grammar slot marked (TOPIC) takes any words -
  even ones the game doesn't know - up to the next word the line expects, or
  the end. Words P-TOPIC-FIRST to P-TOPIC-LAST are 'the topic understood'
  (0: there is none). The slot names no thing: the noun is the other slot's."
<GLOBAL P-TOPIC-FIRST 0>
<GLOBAL P-TOPIC-LAST 0>
<GLOBAL P-BAD-WORD 0>           ;"the command's first unknown word, or 0"
<GLOBAL P-SWAP 0>               ;"for swapping the nouns of a line with nouns reversed"

<ROUTINE TOPIC-SLOT? (ROW SLOT)
    <BAND <GET .ROW <COND (<EQUAL? .SLOT 1> ,S-OPTS1) (ELSE ,S-OPTS2)>> ,SO-TOPIC>>

<ROUTINE TOPIC-PHRASE (STOP "AUX" FIRST)
    ;"the words up to STOP (a preposition) or the end are the topic; false
      if there are none"
    <SETG P-DEFAULTED 0>
    <SET FIRST ,P-WORD>
    <REPEAT ()
        <COND (<G? ,P-WORD ,P-LEN> <RETURN>)
              (<AND .STOP <EQUAL? <WORD-AT ,P-WORD> .STOP>> <RETURN>)>
        <SETG P-WORD <+ ,P-WORD 1>>>
    <COND (<G? .FIRST <- ,P-WORD 1>> <RFALSE>)>
    <SETG P-TOPIC-FIRST .FIRST>
    <SETG P-TOPIC-LAST <- ,P-WORD 1>>
    <RTRUE>>

<ROUTINE FIRST-UNKNOWN-WORD ("AUX" FOUND)
    ;"the first word not in the dictionary (a comma is no word), or 0"
    <DO (I 1 ,P-LEN)
        <COND (<AND <ZERO? <WORD-AT .I>> <NOT <COMMA? .I>>> <SET FOUND .I> <RETURN>)>>
    .FOUND>

<ROUTINE UNKNOWN-OUTSIDE-TOPIC? ("AUX" FOUND)
    ;"is there a word the game doesn't know anywhere but in the topic?"
    <DO (I 1 ,P-LEN)
        <COND (<AND <ZERO? <WORD-AT .I>> <NOT <COMMA? .I>>
                    <OR <ZERO? ,P-TOPIC-FIRST> <L? .I ,P-TOPIC-FIRST> <G? .I ,P-TOPIC-LAST>>>
               <SET FOUND T>
               <RETURN>)>>
    .FOUND>

;"A topic pattern ('\"roses/rose/garden\"', '\"the/-- rose garden\"') is a
  table: word 0 is its length; then, for each word position, how many
  words may stand there and those dictionary words (0: 'nothing', for
  '--'). TOPIC-FITS? tries the positions from OFF on against topic words I
  to LAST; with WHOLE, every word must be used up."
<ROUTINE TOPIC-FITS? (TBL OFF I LAST WHOLE "AUX" N W)
    <COND (<G? .OFF <GET .TBL 0>>                   ;"every position has been fitted"
           <COND (<OR <ZERO? .WHOLE> <G? .I .LAST>> <RTRUE>)>
           <RFALSE>)>
    <SET N <GET .TBL .OFF>>
    <DO (K 1 .N)
        <SET W <GET .TBL <+ .OFF .K>>>
        <COND (<ZERO? .W>
               <COND (<TOPIC-FITS? .TBL <+ .OFF .N 1> .I .LAST .WHOLE> <RTRUE>)>)
              (<AND <NOT <G? .I .LAST>> <EQUAL? <WORD-AT .I> .W>
                    <TOPIC-FITS? .TBL <+ .OFF .N 1> <+ .I 1> .LAST .WHOLE>>
               <RTRUE>)>>
    <RFALSE>>

<ROUTINE TOPIC-MATCHES? (TBL)
    ;"the topic understood is the pattern, all of it"
    <AND ,P-TOPIC-FIRST <TOPIC-FITS? .TBL 1 ,P-TOPIC-FIRST ,P-TOPIC-LAST T>>>

<ROUTINE TOPIC-INCLUDES? (TBL)
    ;"the pattern appears somewhere in the topic understood"
    <COND (,P-TOPIC-FIRST
           <DO (I ,P-TOPIC-FIRST ,P-TOPIC-LAST)
               <COND (<TOPIC-FITS? .TBL 1 .I ,P-TOPIC-LAST 0> <RTRUE>)>>)>
    <RFALSE>>

<ROUTINE PRINT-TOPIC ("AUX" START END)
    ;"[the topic understood]: the letters as typed, from the start of its
      first word to the end of its last (§13.6.3: in each word's block,
      byte 2 is its length and byte 3 its position in READBUF)"
    <COND (<ZERO? ,P-TOPIC-FIRST> <RTRUE>)>
    <SET START <GETB ,PARSEBUF <+ <* 4 ,P-TOPIC-FIRST> 1>>>
    <SET END <+ <GETB ,PARSEBUF <+ <* 4 ,P-TOPIC-LAST> 1>> <GETB ,PARSEBUF <* 4 ,P-TOPIC-LAST>>>>
    <DO (J .START <- .END 1>)
        <PRINTC <GETB ,READBUF .J>>>>
)
(ELSE)>

<ROUTINE PARSE-COMMAND ("AUX" ROW FOUND ORPHAN)
    ;"match the words in PARSEBUF against SYNTAX-TABLE"
    <SETG PRSA 0>
    <SETG PRSO 0>
    <SETG PRSI 0>
    <SETG P-SYNTAX 0>
    <SETG P-ERROR 0>
    ;"P-MULTIPLE here too: a reply to 'Which do you mean' can be a new
      command, and it is parsed from FINISH-COMMAND"
    <IFFLAG (I7 <SETG P-MULTIPLE 0> <SETG P-AMBIG-LEN 0> <SETG P-SOFAR-ROW 0>
                <SETG P-TOPIC-FIRST 0> <SETG P-TOPIC-LAST 0>)
            (ELSE)>
    ;"A word the game doesn't know: in an Inform 7 game it may be part of a
      topic, so that is only an error once no grammar line takes it as one
      (below) - unless it is the verb."
    <IFFLAG (I7
    <SETG P-BAD-WORD <FIRST-UNKNOWN-WORD>>
    <COND (<EQUAL? ,P-BAD-WORD 1> <I7-PARSER-ERROR ,PE-NOT-A-VERB> <RFALSE>)>)
    (ELSE
    <DO (I 1 ,P-LEN)
        <COND (<ZERO? <WORD-AT .I>>
               <COND (<AND ,P-I7-STYLE <EQUAL? .I 1>> <TELL "That's not a verb I recognise." CR>)
                     (,P-I7-STYLE <TELL "You can't see any such thing." CR>)
                     (ELSE <TELL "I don't know the word \""> <PRINT-WORD .I> <TELL "\"." CR>)>
               <RFALSE>)>>)>
    <SET ROW <+ ,SYNTAX-TABLE 2>>              ;"word 0 is the row count"
    <DO (I 1 <GET ,SYNTAX-TABLE 0>)
        <COND (<EQUAL? <GET .ROW ,S-VERB> <WORD-AT 1>>
               <SET FOUND T>
               ;"a missing topic is not asked for ('What do you want to ...?')"
               <IFFLAG (I7
               <COND (<MATCH-SYNTAX .ROW> <SETG P-SYNTAX .ROW> <RETURN>)
                     (<AND ,P-MISSING <ZERO? .ORPHAN> <NOT <TOPIC-SLOT? .ROW ,P-MISSING>>>
                      <SET ORPHAN .ROW>)>)
               (ELSE
               <COND (<MATCH-SYNTAX .ROW> <SETG P-SYNTAX .ROW> <RETURN>)
                     (<AND ,P-MISSING <ZERO? .ORPHAN>> <SET ORPHAN .ROW>)>)>)>
        <SET ROW <+ .ROW <* 2 ,S-SIZE>>>>
    <IFFLAG (I7 <COND (<AND ,P-BAD-WORD <OR <ZERO? ,P-SYNTAX> <UNKNOWN-OUTSIDE-TOPIC?>>>
                       <I7-PARSER-ERROR ,PE-CANT-SEE>
                       <RFALSE>)>)
            (ELSE)>
    <COND (,P-SYNTAX <RETURN <FINISH-COMMAND>>)
          (.ORPHAN <RETURN <ORPHAN-COMMAND .ORPHAN>>)>
    <PARSE-ERROR .FOUND>
    <RFALSE>>

;"Report why the command could not be understood. Inform 7 games pass the
  error to the printing a parser error activity; ZIL games print it here."
<ROUTINE PARSE-ERROR (VERB-KNOWN)
    <IFFLAG (I7
    <I7-PARSER-ERROR <COND (<NOT .VERB-KNOWN> ,PE-NOT-A-VERB)
                           (<EQUAL? ,P-ERROR ,P-ERR-MULTI> ,PE-CANT-USE-MULTIPLE)
                           (<EQUAL? ,P-ERROR ,P-ERR-NOTHING> ,PE-NOTHING-TO-DO)
                           (<EQUAL? ,P-ERROR ,P-ERR-NO-IT> ,PE-NOT-SURE)
                           (<EQUAL? ,P-ERROR ,P-ERR-IT-GONE> ,PE-CANT-SEE-IT)
                           (<EQUAL? ,P-ERROR ,P-ERR-NOT-FOUND> ,PE-CANT-SEE)
                           (ELSE ,PE-DIDNT-UNDERSTAND)>>)
    (ELSE
    <COND (<NOT .VERB-KNOWN> <TELL "That's not a verb I recognise." CR>)
          (<EQUAL? ,P-ERROR ,P-ERR-NO-IT>
           <TELL "I'm not sure what \"">
           <PRINT-WORD ,P-ERROR-WORD>
           <TELL "\" refers to." CR>)
          (<EQUAL? ,P-ERROR ,P-ERR-IT-GONE> <TELL "You can't see the " D ,P-IT " here." CR>)
          (<AND <EQUAL? ,P-ERROR ,P-ERR-NOT-FOUND> ,P-I7-STYLE>
           <TELL "You can't see any such thing." CR>)
          (<EQUAL? ,P-ERROR ,P-ERR-NOT-FOUND>
           <TELL "You can't see any ">
           <PRINT-WORD ,P-ERROR-WORD>
           <TELL " here." CR>)
          (ELSE <TELL "I didn't understand that sentence." CR>)>)>>

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
           <IFFLAG (I7 <SET O <COND (<TOPIC-SLOT? .ROW 1> <TOPIC-PHRASE <GET .ROW ,S-PREP2>>)
                                    (ELSE <OBJECTS-PHRASE <GET .ROW ,S-PREP2> <GET .ROW ,S-FIND1>
                                                          <GET .ROW ,S-OPTS1> .ROW>)>>)
                   (ELSE
           <SET O <NOUN-PHRASE <GET .ROW ,S-PREP2> <GET .ROW ,S-FIND1> ,P-MATCHES1>>)>
           <COND (<ZERO? .O> <MISSING-IF-ENDED 1 .N> <RFALSE>)>
           <SETG PRSO .O>
           <IFFLAG (I7 <COND (<TOPIC-SLOT? .ROW 1> <SETG PRSO 0>)>) (ELSE)>
           <SETG P-DEFAULT1 ,P-DEFAULTED>
           <SETG P-NOUN1 <WORD-AT <- ,P-WORD 1>>>)>
    <COND (<NOT <MATCH-PREP <GET .ROW ,S-PREP2>>> <MISSING-IF-ENDED 2 .N> <RFALSE>)>
    <COND (<G? .N 1>
           <IFFLAG (I7                  ;"as in Inform 7: object 2 is always one thing"
                    <COND (<TOPIC-SLOT? .ROW 2> <SET O <TOPIC-PHRASE 0>>)
                          (<MULTI-WORDS? ,P-WORD ,P-LEN> <MULTI-REFUSED .ROW 2> <RFALSE>)
                          (ELSE <SET O <NOUN-PHRASE 0 <GET .ROW ,S-FIND2> ,P-MATCHES2>>)>)
                   (ELSE
           <SET O <NOUN-PHRASE 0 <GET .ROW ,S-FIND2> ,P-MATCHES2>>)>
           <COND (<ZERO? .O> <MISSING-IF-ENDED 2 .N> <RFALSE>)>
           <SETG PRSI .O>
           <IFFLAG (I7 <COND (<TOPIC-SLOT? .ROW 2> <SETG PRSI 0>)>) (ELSE)>
           <SETG P-DEFAULT2 ,P-DEFAULTED>)>
    <G? ,P-WORD ,P-LEN>>                 ;"no words left over"

<ROUTINE MISSING-IF-ENDED (SLOT N)
    ;"the row needs object SLOT and the player typed nothing more"
    <COND (<AND <G? ,P-WORD ,P-LEN> <NOT <G? .SLOT .N>> <ZERO? ,P-ERROR>>
           <SETG P-MISSING .SLOT>)>>

;"Does the next word match the preposition PREP (IN, ON ...)? If so, step
  past it. No preposition wanted (0) always matches."
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

;"--------------------------------------------- several objects (I7 only)"
<IFFLAG (I7
<ROUTINE OBJECTS-PHRASE (STOP FIND OPTS ROW "AUX" FIRST LAST I W EXCEPT START O)
    ;"object 1: one object as NOUN-PHRASE finds it, or - if the words say
      ALL, AND or a comma - a list in P-MULTI (the first is returned)"
    <SETG P-MULTIPLE 0>
    <SETG P-USED-ALL 0>
    <SETG P-ALL-SEEN 0>
    <SET FIRST ,P-WORD>
    <SET LAST <- ,P-WORD 1>>
    <REPEAT ()                                  ;"where does the phrase end?"
        <COND (<G? <+ .LAST 1> ,P-LEN> <RETURN>)
              (<AND .STOP <EQUAL? <WORD-AT <+ .LAST 1>> .STOP>> <RETURN>)>
        <SET LAST <+ .LAST 1>>>
    <COND (<NOT <MULTI-WORDS? .FIRST .LAST>> <RETURN <NOUN-PHRASE .STOP .FIND ,P-MATCHES1>>)>
    <SETG P-WORD <+ .LAST 1>>
    <COND (<NOT <BAND .OPTS ,SO-MANY>> <MULTI-REFUSED .ROW 1> <RFALSE>)>
    <PUT ,P-MULTI 0 0>
    <PUT ,P-MATCHES1 0 0>
    <SET START .FIRST>
    <SET I .FIRST>
    <REPEAT ()                                  ;"items, split at AND / , / EXCEPT"
        <SET W <COND (<G? .I .LAST> 0) (ELSE <WORD-AT .I>)>>
        <COND (<OR <G? .I .LAST> <LIST-BREAK? .I>>
               <COND (<NOT <G? .START <- .I 1>>>
                      <COND (<NOT <MULTI-ITEM .START <- .I 1> .EXCEPT .OPTS>> <RFALSE>)>)>
               <COND (<AND <NOT <G? .I .LAST>> <EQUAL? .W ,W?EXCEPT ,W?BUT>> <SET EXCEPT T>)>
               <SET START <+ .I 1>>)>
        <COND (<G? .I .LAST> <RETURN>)>
        <SET I <+ .I 1>>>
    <PUT ,P-MATCHES2 0 0>                       ;"the items' scratch: not object 2's"
    <COND (<ZERO? <GET ,P-MULTI 0>> <RAISE-ERROR ,P-ERR-NOTHING 0> <RFALSE>)>
    <SET O <GET ,P-MULTI 1>>
    ;"As in Inform 7: ALL is one object - '(the keys)' - only when ONE thing
      could have been meant. Things it could mean but leaves out (held ones,
      for TAKE ALL) still count: one left over is then 'bottle: Taken.'"
    <COND (<AND ,P-USED-ALL <EQUAL? ,P-ALL-SEEN 1> <EQUAL? <GET ,P-MULTI 0> 1>>
           <SETG P-DEFAULTED T>)                    ;"(not TAKE ALL AND LAMP)"
          (ELSE <SETG P-MULTIPLE T> <SETG P-DEFAULTED 0>)>
    .O>

;"Do words FIRST..LAST name several things (ALL, EVERYTHING, AND, a comma)?"
<ROUTINE MULTI-WORDS? (FIRST LAST)
    <DO (I .FIRST .LAST)
        <COND (<OR <EQUAL? <WORD-AT .I> ,W?ALL ,W?EVERYTHING ,W?AND> <COMMA? .I>>
               <RTRUE>)>>
    <RFALSE>>

;"Does word I separate items in a list: AND, EXCEPT, BUT or a comma?"
<ROUTINE LIST-BREAK? (I) <OR <EQUAL? <WORD-AT .I> ,W?AND ,W?EXCEPT ,W?BUT> <COMMA? .I>>>

<ROUTINE COMMA? (I "AUX" E)
    ;"the lexer makes ',' a word of its own (a separator, §13.6.1); it is not
      in the dictionary, so look at the letter the player typed"
    <SET E <+ ,PARSEBUF <* 4 .I> -2>>           ;"§13.6.3: the word's 4-byte entry"
    <AND <ZERO? <GET .E 0>> <EQUAL? <GETB .E 2> 1>
         <EQUAL? <GETB ,READBUF <GETB .E 3>> 44>>>

<ROUTINE MULTI-ITEM (FIRST LAST EXCEPT OPTS "AUX" O)
    ;"one item of the list: ALL, or a noun (added, or with EXCEPT taken out)"
    <SET FIRST <SKIP-ARTICLES .FIRST .LAST>>
    <COND (<AND <EQUAL? .FIRST .LAST> <EQUAL? <WORD-AT .FIRST> ,W?ALL ,W?EVERYTHING>>
           <SETG P-USED-ALL T>
           <ADD-ALL .OPTS>
           <RTRUE>)>
    <SET O <RESOLVE .FIRST .LAST ,P-MATCHES2>>  ;"P-MATCHES2 as scratch: PRSI comes later"
    <COND (<ZERO? .O> <RFALSE>)
          (<AND .EXCEPT <G? <GET ,P-MATCHES2 0> 1>>  ;"ALL BUT COIN: every coin"
           <DO (I 1 <GET ,P-MATCHES2 0>) <MULTI-REMOVE <GET ,P-MATCHES2 .I>>>)
          (.EXCEPT <MULTI-REMOVE .O>)
          (<G? <GET ,P-MATCHES2 0> 1> <MULTI-ADD <UNCLEAR-ITEM ,P-MATCHES2>>)
          (ELSE <MULTI-ADD .O>)>
    <RTRUE>>

<ROUTINE UNCLEAR-ITEM (TBL "AUX" N START)
    ;"TAKE LAMP AND COIN with two coins: keep the candidates, and put a mark
      (minus where they are kept) in the list; the question comes once the
      whole command fits (FINISH-COMMAND): asking now would overwrite it"
    <SET N <GET .TBL 0>>
    <COND (<G? <+ ,P-AMBIG-LEN .N 1> 47> <RETURN <GET .TBL 1>>)>   ;"no room: the first"
    <SET START <+ ,P-AMBIG-LEN 1>>
    <PUT ,P-AMBIG .START .N>
    <DO (I 1 .N) <PUT ,P-AMBIG <+ .START .I> <GET .TBL .I>>>
    <SETG P-AMBIG-LEN <+ ,P-AMBIG-LEN .N 1>>
    <- 0 .START>>

<ROUTINE SETTLE-LIST ("AUX" X N O (RESULT 1))
    ;"ask about each unclear item, as for one object: 1 done, 0 the reply was
      a new command, -1 it was empty"
    <DO (I 1 <GET ,P-MULTI 0>)
        <SET X <GET ,P-MULTI .I>>
        <COND (<L? .X 0>
               <SET X <- 0 .X>>
               <SET N <GET ,P-AMBIG .X>>
               <PUT ,P-MATCHES1 0 .N>
               <DO (J 1 .N) <PUT ,P-MATCHES1 .J <GET ,P-AMBIG <+ .X .J>>>>
               <SET O <CHOOSE ,P-MATCHES1 <GET ,P-SYNTAX ,S-OPTS1>>>
               <PUT ,P-MATCHES1 0 0>
               <COND (<L? .O 1> <SET RESULT .O> <RETURN>)>
               <PUT ,P-MULTI .I .O>)>>
    <COND (<EQUAL? .RESULT 1> <SETG PRSO <GET ,P-MULTI 1>>)>
    .RESULT>

<ROUTINE MULTI-REFUSED (ROW SLOT)
    ;"several objects where the row takes one: remember how far the command
      got, for [parser command so far] - 'unlock the grate with'"
    <COND (<RAISE-ERROR ,P-ERR-MULTI 0>
           <SETG P-SOFAR-ROW .ROW>
           <SETG P-SOFAR-SLOT .SLOT>
           ;"-1: the first object was a list - Inform prints 'those things'
             (the real Advent: 'drop those things in what?')"
           <SETG P-SOFAR-OBJ <COND (<AND <EQUAL? .SLOT 2> ,P-MULTIPLE> -1)
                                   (ELSE ,PRSO)>>)>>

<ROUTINE ERROR-RANK (E)
    ;"Inform's parser reports the highest-ranked error of all the grammar
      lines it tried; these are in its order (CANTSEE < MULTI < VAGUE <
      ITGONE < NOTHING)"
    <COND (<EQUAL? .E ,P-ERR-NOT-FOUND> 1)
          (<EQUAL? .E ,P-ERR-MULTI> 2)
          (<EQUAL? .E ,P-ERR-NO-IT> 3)
          (<EQUAL? .E ,P-ERR-IT-GONE> 4)
          (<EQUAL? .E ,P-ERR-NOTHING> 5)
          (ELSE 0)>>

<ROUTINE RAISE-ERROR (E W)
    ;"as Inform's parser does, only a higher-ranked error replaces the one set
      by an earlier row: of equal ones the first stays - 'unlock the grate with'
      (row UNLOCK OBJECT WITH OBJECT) and not 'unlock' (row UNLOCK OBJECT)"
    <COND (<NOT <G? <ERROR-RANK .E> <ERROR-RANK ,P-ERROR>>> <RFALSE>)>
    <SETG P-ERROR .E>
    <SETG P-ERROR-WORD .W>
    <RTRUE>>

<ROUTINE ADD-ALL (OPTS "AUX" O)
    ;"Inform 7's ALL: with a held-things verb (DROP), what the player carries
      but does not wear; otherwise what lies in the room - not scenery, not
      fixed in place, not people, not what is held already"
    <COND (<BAND .OPTS ,SO-HELD>
           <SET O <FIRST? ,PLAYER>>
           <REPEAT ()
               <COND (<ZERO? .O> <RETURN>)>
               <SETG P-ALL-SEEN <+ ,P-ALL-SEEN 1>>      ;"worn things could be meant too"
               <COND (<NOT <FSET? .O ,WORNBIT>> <MULTI-ADD .O>)>
               <SET O <NEXT? .O>>>)
          (<NOT ,LIT>)                           ;"in the dark: nothing"
          (ELSE
           <SETG P-ALL-SEEN <+ ,P-ALL-SEEN <COUNT-HELD>>>  ;"held: meant, then left out"
           <SET O <FIRST? ,HERE>>
           <REPEAT ()
               <COND (<ZERO? .O> <RETURN>)>
               <COND (<NOT <EQUAL? .O ,PLAYER>> <SETG P-ALL-SEEN <+ ,P-ALL-SEEN 1>>)>
               <COND (<NOT <EQUAL? .O ,PLAYER>> <ADD-IF-TAKEABLE .O>)>
               <COND (<FSET? .O ,SUPPORTERBIT>          ;"and what is on a supporter"
                      <MAP-CONTENTS (C .O)               ;"(Cold Iron's book on its table)"
                          <SETG P-ALL-SEEN <+ ,P-ALL-SEEN 1>>
                          <ADD-IF-TAKEABLE .C>>)>
               <SET O <NEXT? .O>>>)>>

;"For ALL: add O to the list unless it is scenery, fixed or a person."
<ROUTINE ADD-IF-TAKEABLE (O)
    <COND (<NOT <OR <FSET? .O ,SCENERYBIT> <FSET? .O ,FIXEDBIT> <FSET? .O ,PERSONBIT>>>
           <MULTI-ADD .O>)>>

;"How many things the player is carrying."
<ROUTINE COUNT-HELD ("AUX" (N 0) O)
    <SET O <FIRST? ,PLAYER>>
    <REPEAT ()
        <COND (<ZERO? .O> <RETURN>)>
        <SET N <+ .N 1>>
        <SET O <NEXT? .O>>>
    .N>

;"Add O to the list of objects in P-MULTI (once only; at most 16)."
<ROUTINE MULTI-ADD (O "AUX" N)
    <SET N <GET ,P-MULTI 0>>
    <DO (I 1 .N) <COND (<EQUAL? <GET ,P-MULTI .I> .O> <RTRUE>)>>
    <COND (<L? .N 16> <PUT ,P-MULTI <+ .N 1> .O> <PUT ,P-MULTI 0 <+ .N 1>>)>>

;"Take O out of the P-MULTI list (for ALL EXCEPT ...)."
<ROUTINE MULTI-REMOVE (O "AUX" N KEPT)
    <SET N <GET ,P-MULTI 0>>
    <DO (I 1 .N)
        <COND (<NOT <EQUAL? <GET ,P-MULTI .I> .O>>
               <SET KEPT <+ .KEPT 1>>
               <PUT ,P-MULTI .KEPT <GET ,P-MULTI .I>>)>>
    <PUT ,P-MULTI 0 .KEPT>>
) (ELSE)>

;"Step past THE, A and AN at the start of words FIRST..LAST."
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
                  <IFFLAG (I7 <RAISE-ERROR ,P-ERR-NOT-FOUND .LAST>)
                          (ELSE <SETG P-ERROR ,P-ERR-NOT-FOUND> <SETG P-ERROR-WORD .LAST>)>
                  <RFALSE>)>)>>

;"Is dictionary word W an article?"
<ROUTINE ARTICLE? (W) <EQUAL? .W ,W?THE ,W?A ,W?AN>>

;"Is dictionary word W a pronoun the parser understands?"
<ROUTINE PRONOUN? (W) <EQUAL? .W ,W?IT ,W?THEM ,W?HIM ,W?HER>>

;"The thing IT (word I) stands for: the last thing the player named."
<ROUTINE PRONOUN-OBJECT (I)
    <COND (<ZERO? ,P-IT>
           <IFFLAG (I7 <RAISE-ERROR ,P-ERR-NO-IT .I>)
                   (ELSE <SETG P-ERROR ,P-ERR-NO-IT> <SETG P-ERROR-WORD .I>)>
           <RFALSE>)
          (<NOT <IN-SCOPE? ,P-IT>>
           <IFFLAG (I7 <RAISE-ERROR ,P-ERR-IT-GONE .I>)     ;"Inform 7 names the word"
                   (ELSE <SETG P-ERROR ,P-ERR-IT-GONE>)>
           <RFALSE>)
          (ELSE ,P-IT)>>

"-------------------------------------------------------------- scope"

<ROUTINE SEARCH-SCOPE (FIRST LAST TBL)
    <SEARCH-IN ,PLAYER .FIRST .LAST .TBL>
    <COND (,LIT <SEARCH-IN ,HERE .FIRST .LAST .TBL>)>>

;"Add to TBL each thing in CONTAINER - and one level inside those - that
  words FIRST..LAST describe."
<ROUTINE SEARCH-IN (CONTAINER FIRST LAST TBL)
    <MAP-CONTENTS (O .CONTAINER)
        <COND (<MATCHES? .O .FIRST .LAST> <ADD-MATCH .TBL .O>)>
        <MAP-CONTENTS (C .O)
            <COND (<MATCHES? .C .FIRST .LAST> <ADD-MATCH .TBL .C>)>>>>

<ROUTINE ADD-MATCH (TBL O "AUX" N)
    ;"once only: when the player is IN the room (as in Inform 7), a thing
      they hold is reached twice - as held, and inside the room's contents"
    <SET N <GET .TBL 0>>
    <DO (I 1 .N) <COND (<EQUAL? <GET .TBL .I> .O> <RTRUE>)>>
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

<IFFLAG (I7
;"Do words FIRST..LAST name O? They are O's own words and whole phrases
  (Inform's Understand \"puzzle piece\" as ...), in any mixture: each step
  takes a phrase of O found at that word, or one word that describes O. The
  words must all be used, and the last step be a phrase or a noun of O -
  so 'puzzle' alone does not name the piece, but 'puzzle piece' does."
<ROUTINE MATCHES? (O FIRST LAST "AUX" (I .FIRST) N NOUN)
    <REPEAT ()
        <COND (<G? .I .LAST> <RETURN>)>
        <SET N <PHRASE-AT .O .I .LAST>>
        <COND (<G? .N 0>
               <SET I <+ .I .N>>
               <SET NOUN T>)
              (<DESCRIBES? .O <WORD-AT .I>>
               <SET NOUN <IN-PROP? .O ,P?SYNONYM <WORD-AT .I>>>
               <SET I <+ .I 1>>)
              (ELSE <RFALSE>)>>
    <COND (.NOUN <RTRUE>) (ELSE <RFALSE>)>>

;"How many words, from word I (not past LAST), make one of O's phrases? The
  longest wins; 0 if none. PHRASES holds each phrase's words and then 0."
<ROUTINE PHRASE-AT (O I LAST "AUX" PT N (K 0) J OK (BEST 0))
    <SET PT <GETPT .O ,P?PHRASES>>
    <COND (<ZERO? .PT> <RETURN 0>)>
    <SET N </ <PTSIZE .PT> 2>>
    <REPEAT ()
        <COND (<NOT <L? .K .N>> <RETURN>)>
        <SET J .I>                              ;"try the phrase starting at K"
        <SET OK T>
        <REPEAT ()
            <COND (<ZERO? <GET .PT .K>> <RETURN>)>
            <COND (<OR <G? .J .LAST> <NOT <EQUAL? <WORD-AT .J> <GET .PT .K>>>>
                   <SET OK <>>)>
            <SET J <+ .J 1>>
            <SET K <+ .K 1>>>
        <COND (<AND .OK <G? <- .J .I> .BEST>> <SET BEST <- .J .I>>)>
        <SET K <+ .K 1>>>                       ;"past the phrase's 0"
    .BEST>
) (ELSE
<ROUTINE MATCHES? (O FIRST LAST)
    ;"the last word is a noun of O; every earlier word describes O"
    <COND (<NOT <IN-PROP? .O ,P?SYNONYM <WORD-AT .LAST>>> <RFALSE>)>
    <DO (I .FIRST <- .LAST 1>)
        <COND (<NOT <DESCRIBES? .O <WORD-AT .I>>> <RFALSE>)>>
    <RTRUE>>
)>

;"Could word W be part of a name for O: one of its adjectives or
  synonyms, or an article?"
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

;"No noun was typed: find a default from the SYNTAX line's FIND flag -
  something carried first, then (if there is light) something here."
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
    <IFFLAG (I7 <COND (,P-MULTIPLE
                       <SET O <SETTLE-LIST>>
                       <COND (<L? .O 0> <RFALSE>)
                             (<ZERO? .O> <RETURN <PARSE-COMMAND>>)>)>)
            (ELSE)>
    <COND (,P-DEFAULT1 <TELL "(the " D ,PRSO ")" CR>)>
    <COND (,P-DEFAULT2 <TELL "(the " D ,PRSI ")" CR>)>
    ;"as in Inform, the thing is the noun whichever slot it was typed in"
    <IFFLAG (I7 <COND (<TOPIC-SLOT? ,P-SYNTAX 1> <SETG PRSO ,PRSI> <SETG PRSI 0>)>) (ELSE)>
    ;"a line 'with nouns reversed': the thing typed first is the second noun"
    <IFFLAG (I7 <COND (<BAND <GET ,P-SYNTAX ,S-OPTS1> ,SO-REVERSED>
                       <SETG P-SWAP ,PRSO> <SETG PRSO ,PRSI> <SETG PRSI ,P-SWAP>)>) (ELSE)>
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

;"Does O pass one of the SYNTAX line's search options: HELD, IN-ROOM, or
  (otherwise) being inside the second object?"
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

;"The answer to Which do you mean: does every word of it describe O?"
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
