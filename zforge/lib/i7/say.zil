"zforge/lib/i7/say.zil - printing names, articles and lists.

 The compiler gives every thing an ARTICLE property, worked out when the
 game is compiled: 1 = 'a', 2 = 'an', 3 = 'some' (plural-named), 0 = none
 (proper-named, like 'Roger'), 4 = the author's own, in ARTICLE-TEXT. So
 the running game never needs to look at the letters of a name."

<PROPDEF ARTICLE 1>
<PROPDEF ARTICLE-TEXT 0>

;"Adaptive text (fixed viewpoint: 'you', present tense). Inform 7 remembers
  the object named most recently - the 'prior named object' - and makes
  verbs and pronouns agree with it: '[regarding the keys][They] [are]'
  prints 'They are'. Every routine here that prints a name sets it."
;"Paragraphs, as in Inform 7: a say that ends a sentence leaves a
  paragraph pending (SAY-P, Inform 7's say__p). Between two rules a
  pending paragraph becomes a pending break, printed only if something
  more is printed (so a turn never ends with an extra blank line)."
<GLOBAL SAY-P 0>
<GLOBAL PARA-BREAK 0>

<ROUTINE SENTENCE-BREAK ()      ;"the line break after 'say \"Taken.\"'"
    <CRLF> <SETG SAY-P 1>>

<ROUTINE PARA-END ()            ;"after a description: end its paragraph"
    ;"a line break - unless the text already ended with one (a say inside
      it, such as a say phrase's, ended a sentence), as in Inform 7"
    <COND (<ZERO? ,SAY-P> <SENTENCE-BREAK>)>>

<GLOBAL SAID-COUNT 0>    ;"one more for every say: 'did that activity print anything?'"

<ROUTINE PARA-FLUSH ()          ;"before printing: the blank line owed, if any"
    <SETG SAID-COUNT <+ ,SAID-COUNT 1>>
    <SETG SAY-P 0>
    <COND (,PARA-BREAK <CRLF> <SETG PARA-BREAK 0>)>>

<ROUTINE PARA-ABSORB ()         ;"before a print that starts with its own blank line"
    <SETG SAY-P 0> <SETG PARA-BREAK 0>>

<ROUTINE PARA-DIVIDE ()         ;"between two rules"
    <COND (,SAY-P <SETG PARA-BREAK 1> <SETG SAY-P 0>)>>

<GLOBAL PRIOR-NAMED 0>

<OBJECT SOME-THINGS                ;"never anywhere: '[regarding them]' names it,"
    (DESC "them")                  ;"so what follows agrees as a plural"
    (FLAGS PLURALBIT)>

<ROUTINE PRIOR-PLURAL? ()
    ;"do verbs take their plural form? (for 'you', and plural-named things)"
    <OR <EQUAL? ,PRIOR-NAMED ,PLAYER> <AND ,PRIOR-NAMED <FSET? ,PRIOR-NAMED ,PLURALBIT>>>>

<ROUTINE SAY-VERB (PLURAL SINGULAR)
    ;"'are'/'is', 'flow'/'flows': the compiler supplies both forms"
    <COND (<PRIOR-PLURAL?> <PRINT .PLURAL>) (ELSE <PRINT .SINGULAR>)>>

<ROUTINE SAY-WE (TEXT)
    ;"[We] [we] [us] [our] ...: the player - print the word, and they are now
      the prior named object"
    <SETG PRIOR-NAMED ,PLAYER>
    <PRINT .TEXT>>

<ROUTINE SAY-IT (S)
    ;"[it]: prints 'it'; what follows agrees with a singular"
    <TELL .S> <SETG PRIOR-NAMED 0>>

<ROUTINE SAY-PRONOUN (YOU THEY IT)
    ;"[They] [they] [them] [Those]: the pronoun for the prior named object"
    <COND (<EQUAL? ,PRIOR-NAMED ,PLAYER> <PRINT .YOU>)
          (<PRIOR-PLURAL?> <PRINT .THEY>)
          (ELSE <PRINT .IT>)>>

;"[noun]: the name alone."
<ROUTINE SAY-NAME (O)
    <SETG PRIOR-NAMED .O>
    <PRINT-NAME .O>>

;"[a noun]: the name with its indefinite article."
<ROUTINE SAY-A (O "AUX" A)
    <SETG PRIOR-NAMED .O>
    ;"[a noun]: 'a brass hook', 'an apple', 'some water', 'Roger'"
    <SET A <GETP .O ,P?ARTICLE>>
    <COND (<FSET? .O ,PROPERBIT>)
          (<EQUAL? .A 2> <TELL "an ">)
          (<EQUAL? .A 3> <TELL "some ">)
          (<EQUAL? .A 4> <PRINT <GETP .O ,P?ARTICLE-TEXT>> <TELL " ">)
          (<EQUAL? .A 1> <TELL "a ">)>
    <PRINT-NAME .O>>

;"[A noun]: the same, with a capital letter."
<ROUTINE SAY-CAP-A (O "AUX" A)
    <SETG PRIOR-NAMED .O>
    ;"[A noun]"
    <SET A <GETP .O ,P?ARTICLE>>
    <COND (<FSET? .O ,PROPERBIT>)
          (<EQUAL? .A 2> <TELL "An ">)
          (<EQUAL? .A 3> <TELL "Some ">)
          (<EQUAL? .A 4> <SAY-CAPITALISED <GETP .O ,P?ARTICLE-TEXT>> <TELL " ">)
          (<EQUAL? .A 1> <TELL "A ">)>
    <PRINT-NAME .O>>

<GLOBAL CAP-BUFFER <ITABLE 64 (BYTE)>>

<ROUTINE SAY-CAPITALISED (STR "AUX" N C)
    ;"print a string with its first letter in capitals: print it into a
      buffer (output stream 3, §7.1.2), then print the buffer"
    <ZOP OUTPUT_STREAM 3 ,CAP-BUFFER>
    <PRINT .STR>
    <ZOP OUTPUT_STREAM -3>
    <SET N <GET ,CAP-BUFFER 0>>
    <DO (I 0 <- .N 1>)
        <SET C <GETB ,CAP-BUFFER <+ .I 2>>>
        <COND (<AND <ZERO? .I> <G? .C 96> <L? .C 123>> <SET C <- .C 32>>)>
        <PRINTC .C>>>

;"[the noun]: the name with the definite article."
<ROUTINE SAY-THE (O)
    <SETG PRIOR-NAMED .O>
    ;"[the noun]"
    <COND (<NOT <FSET? .O ,PROPERBIT>> <TELL "the ">)>
    <PRINT-NAME .O>>

;"[The noun]: the same, with a capital letter."
<ROUTINE SAY-CAP-THE (O)
    <SETG PRIOR-NAMED .O>
    ;"[The noun]"
    <COND (<NOT <FSET? .O ,PROPERBIT>> <TELL "The ">)>
    <PRINT-NAME .O>>

<ROUTINE SAY-TEXT (O PROP "AUX" R)
    ;"print a text property (description, initial appearance, ...): the
      compiler makes every one a routine; true if there was one"
    <COND (<SET R <GETP .O .PROP>> <APPLY .R> <RTRUE>)>
    <RFALSE>>

;"[is-are]: is or are, to agree with O."
<ROUTINE SAY-IS-ARE (O)
    <COND (<FSET? .O ,PLURALBIT> <TELL " are">) (ELSE <TELL " is">)>>

;"---------------------------------------------------------------- lists"

<ROUTINE COUNT-LISTED (PARENT TEST "AUX" N)
    ;"how many children of PARENT pass TEST (a routine: true = list it)"
    <SET N 0>
    <MAP-CONTENTS (O .PARENT)
        <COND (<APPLY .TEST .O> <SET N <+ .N 1>>)>>
    .N>

<ROUTINE SAY-LIST (PARENT TEST "AUX" TOTAL DONE)
    ;"'a brass hook, a lamp and some water': the children passing TEST"
    <SET TOTAL <COUNT-LISTED .PARENT .TEST>>
    <SET DONE 0>
    <MAP-CONTENTS (O .PARENT)
        <COND (<APPLY .TEST .O>
               <SAY-A .O>
               <SET DONE <+ .DONE 1>>
               <COND (<EQUAL? .DONE <- .TOTAL 1>> <TELL " and ">)
                     (<L? .DONE .TOTAL> <TELL ", ">)>)>>
    .TOTAL>

;"------------------------------------------------------------- numbers"

<ROUTINE SAY-IN-WORDS (N "AUX" TENS)
    ;"[N in words], for 0 to 999"
    <COND (<L? .N 0> <TELL "minus "> <SET N <- 0 .N>>)>
    <COND (<G? .N 99>
           <SAY-UNITS </ .N 100>> <TELL " hundred">
           <SET N <MOD .N 100>>
           <COND (<ZERO? .N> <RTRUE>)>
           <TELL " and ">)>
    <COND (<L? .N 20> <SAY-UNITS .N> <RTRUE>)>
    <SET TENS </ .N 10>>
    <COND (<EQUAL? .TENS 2> <TELL "twenty">) (<EQUAL? .TENS 3> <TELL "thirty">)
          (<EQUAL? .TENS 4> <TELL "forty">)  (<EQUAL? .TENS 5> <TELL "fifty">)
          (<EQUAL? .TENS 6> <TELL "sixty">)  (<EQUAL? .TENS 7> <TELL "seventy">)
          (<EQUAL? .TENS 8> <TELL "eighty">) (ELSE <TELL "ninety">)>
    <COND (<NOT <ZERO? <MOD .N 10>>> <TELL "-"> <SAY-UNITS <MOD .N 10>>)>>

<GLOBAL UNIT-WORDS <TABLE "zero" "one" "two" "three" "four" "five" "six" "seven"
    "eight" "nine" "ten" "eleven" "twelve" "thirteen" "fourteen" "fifteen"
    "sixteen" "seventeen" "eighteen" "nineteen">>

;"A number in words: one, two, three ... (from the UNIT-WORDS table)."
<ROUTINE SAY-UNITS (N) <PRINT <GET ,UNIT-WORDS .N>>>
