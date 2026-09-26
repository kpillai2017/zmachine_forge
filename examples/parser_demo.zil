"parser_demo.zil - a one-room test bed for lib/parser.zil.

 Three keys and two books make the parser ASK: 'Which do you mean, the
 brass key, the iron key or the rusty key?'. Reply with an adjective
 ('rusty'), a fuller name ('iron key'), or type a new command instead.
 IT / THEM refer to the last thing you handled. Leave the object off
 ('take', 'put key') and the parser asks for it."

<VERSION 5>
<INSERT-FILE "lib/parser">

<SYNTAX LOOK = V-LOOK>               <VERB-SYNONYM LOOK L>
<SYNTAX EXAMINE OBJECT = V-EXAMINE>  <VERB-SYNONYM EXAMINE X READ>
<SYNTAX INVENTORY = V-INVENTORY>     <VERB-SYNONYM INVENTORY I>
"search options (ADR-019) steer 'Which do you mean?': TAKE prefers what
 you are not holding, DROP and PUT what you are, TAKE ... FROM prefers what
 is inside the thing named"
<SYNTAX TAKE OBJECT (ON-GROUND IN-ROOM) = V-TAKE>   <VERB-SYNONYM TAKE GET>
<SYNTAX TAKE OBJECT (INSIDE-PRSI) FROM OBJECT = V-TAKE>
<PREP-SYNONYM FROM OUT>
<SYNTAX DROP OBJECT (HELD CARRIED) = V-DROP>
<SYNTAX PUT OBJECT (HELD CARRIED) IN OBJECT = V-PUT-IN>
<PREP-SYNONYM IN INTO>
<SYNTAX QUIT = V-QUIT>               <VERB-SYNONYM QUIT Q>

<OBJECT ROOMS (DESC "rooms")>

<ROOM STUDY
    (IN ROOMS)
    (DESC "The Locksmith's Study")
    (LDESC "Shelves of locks line every wall of this cramped study.")>

<OBJECT BRASS-KEY (IN STUDY) (DESC "brass key") (SYNONYM KEY)
    (ADJECTIVE BRASS SHINY) (FLAGS TAKEBIT)
    (TEXT "A shiny brass key, stamped with the number 7.")>

<OBJECT IRON-KEY (IN STUDY) (DESC "iron key") (ARTICLE "an") (SYNONYM KEY)
    (ADJECTIVE IRON HEAVY) (FLAGS TAKEBIT)
    (TEXT "A heavy iron key, cold to the touch.")>

<OBJECT BOX (IN STUDY) (DESC "wooden box") (SYNONYM BOX)
    (ADJECTIVE WOODEN) (FLAGS CONTBIT)
    (TEXT "A plain wooden box with no lid.")>

<OBJECT RUSTY-KEY (IN BOX) (DESC "rusty key") (SYNONYM KEY)
    (ADJECTIVE RUSTY OLD) (FLAGS TAKEBIT)
    (TEXT "An old key, orange with rust.")>

<OBJECT RED-BOOK (IN STUDY) (DESC "red book") (SYNONYM BOOK TOME)
    (ADJECTIVE RED) (FLAGS TAKEBIT)
    (TEXT "'A Treatise on Tumblers', in red leather.")>

<OBJECT BLUE-BOOK (IN STUDY) (DESC "blue book") (SYNONYM BOOK TOME)
    (ADJECTIVE BLUE) (FLAGS TAKEBIT)
    (TEXT "'Keys of the Ancient World', bound in blue cloth.")>

<ROUTINE GO ()
    <SETG HERE ,STUDY>
    <TELL "PARSER DEMO - try TAKE KEY, then answer the question." CR CR>
    <V-LOOK>
    <REPEAT ()
        <TELL CR "> ">
        <COND (<PARSER> <PERFORM>)>>>

<ROUTINE V-LOOK ()
    <TELL D ,HERE CR>
    <PRINT <GETP ,HERE ,P?LDESC>>
    <CRLF>
    <MAP-CONTENTS (O ,HERE)
        <TELL "There is ">
        <A-OBJ .O>
        <TELL " here." CR>
        <COND (<FSET? .O ,CONTBIT> <LIST-CONTENTS .O>)>>>

<ROUTINE LIST-CONTENTS (CONT)
    <MAP-CONTENTS (O .CONT)
        <TELL "  The " D .CONT " holds ">
        <A-OBJ .O>
        <TELL "." CR>>>

<ROUTINE A-OBJ (O "AUX" ART)
    ;"'a brass key' / 'an iron key': an object may give its own ARTICLE"
    <SET ART <GETP .O ,P?ARTICLE>>
    <COND (.ART <PRINT .ART>) (ELSE <TELL "a">)>
    <TELL " " D .O>>

<ROUTINE V-EXAMINE ()
    <PRINT <GETP ,PRSO ,P?TEXT>>
    <CRLF>
    <COND (<FSET? ,PRSO ,CONTBIT>
           <COND (<FIRST? ,PRSO> <LIST-CONTENTS ,PRSO>)
                 (ELSE <TELL "It is empty." CR>)>)>>

<ROUTINE V-INVENTORY ()
    <COND (<NOT <FIRST? ,PLAYER>> <TELL "You are empty-handed." CR> <RTRUE>)>
    <TELL "You are carrying:" CR>
    <MAP-CONTENTS (O ,PLAYER) <TELL "  "> <A-OBJ .O> <CRLF>>>

<ROUTINE V-TAKE ()
    <COND (<IN? ,PRSO ,PLAYER> <TELL "You already have the " D ,PRSO "." CR>)
          (<NOT <FSET? ,PRSO ,TAKEBIT>> <TELL "The " D ,PRSO " is too awkward to carry." CR>)
          (<AND ,PRSI <NOT <IN? ,PRSO ,PRSI>>>
           <TELL "The " D ,PRSO " isn't in the " D ,PRSI "." CR>)
          (ELSE <MOVE ,PRSO ,PLAYER> <TELL "You take the " D ,PRSO "." CR>)>>

<ROUTINE V-DROP ()
    <COND (<NOT <IN? ,PRSO ,PLAYER>> <TELL "You aren't holding the " D ,PRSO "." CR>)
          (ELSE <MOVE ,PRSO ,HERE> <TELL "You drop the " D ,PRSO "." CR>)>>

<ROUTINE V-PUT-IN ()
    <COND (<NOT <FSET? ,PRSI ,CONTBIT>> <TELL "You can't put things in that." CR>)
          (<EQUAL? ,PRSO ,PRSI> <TELL "Not even a locksmith can do that." CR>)
          (<NOT <IN? ,PRSO ,PLAYER>> <TELL "You aren't holding the " D ,PRSO "." CR>)
          (ELSE <MOVE ,PRSO ,PRSI> <TELL "You put the " D ,PRSO " in the " D ,PRSI "." CR>)>>

<ROUTINE V-QUIT () <TELL "Goodbye." CR> <QUIT>>
