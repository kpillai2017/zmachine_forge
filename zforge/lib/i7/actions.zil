"zforge/lib/i7/actions.zil - Inform 7's action processing, in ZIL-lite.

 Every action has a rulebook table from the compiler: six LTABLEs of rule
 routines, one per stage, in the order Inform 7 runs them.
 A rule returns true when it has made a decision ('stop the action', or
 an Instead / After rule finishing); false means 'no decision, go on'.

   stage       if a rule decides ...
   Before      the action stops (nothing happened)
   Instead     the action stops: the rule did something else
   Check       the action stops: it was not allowed
   Carry out   (the rest of carry out is skipped; the action goes on)
   After       the action stops: the After rule replaced the report
   Report      (the rest of report is skipped)

 GENERAL-RULES holds 'doing something' rules; they run after the
 action's own rules in each stage (a rule about one action is more
 specific than a rule about every action)."

<CONSTANT BEFORE-STAGE 0>
<CONSTANT INSTEAD-STAGE 1>
<CONSTANT CHECK-STAGE 2>
<CONSTANT CARRY-OUT-STAGE 3>
<CONSTANT AFTER-STAGE 4>
<CONSTANT REPORT-STAGE 5>

<GLOBAL SILENTLY 0>            ;"'silently try': skip the Report stage"

<ROUTINE RUN-ACTION (RULES)
    ;"Out-of-world actions (saving, the score, ...) happen outside the
      story: like Inform 7, they skip Before, Instead and After rules"
    <COND (<AND <NOT ,OUT-OF-WORLD> <RUN-STAGE .RULES ,BEFORE-STAGE>> <RFALSE>)>
    <COND (<AND <NOT ,OUT-OF-WORLD> <RUN-STAGE .RULES ,INSTEAD-STAGE>> <RFALSE>)>
    <COND (<RUN-STAGE .RULES ,CHECK-STAGE> <RFALSE>)>
    <RUN-STAGE .RULES ,CARRY-OUT-STAGE>
    <COND (<AND <NOT ,OUT-OF-WORLD> <RUN-STAGE .RULES ,AFTER-STAGE>> <RTRUE>)>
    <COND (<NOT ,SILENTLY> <RUN-STAGE .RULES ,REPORT-STAGE>)>
    <RTRUE>>

;"Run one stage: the action's own rules first, then the 'doing something'
  rules (GENERAL-RULES). True if a rule decided."
<ROUTINE RUN-STAGE (RULES STAGE)
    <COND (<FOLLOW-RULES <GET .RULES .STAGE>> <RTRUE>)
          (,OUT-OF-WORLD <RFALSE>)>        ;"no 'doing something' rules either"
    <FOLLOW-RULES <GET ,GENERAL-RULES .STAGE>>>

<ROUTINE FOLLOW-RULES (TBL "AUX" N)
    ;"run the rules in an LTABLE in order; true as soon as one decides"
    <SET N <GET .TBL 0>>
    <DO (I 1 .N)
        <COND (<APPLY <GET .TBL .I>> <PARA-DIVIDE> <RTRUE>)>  ;"RTRUE leaves the routine"
        <PARA-DIVIDE>>
    <RFALSE>>

<IFFLAG (ORDERS
;"Inform's requested actions require persuasion rule: 'oak, jump' asks the oak
  to try jumping. The persuasion rules decide; if none says it succeeds, the
  person refuses - with Inform's words only if the rules printed nothing. A
  person persuaded cannot act in I7-lite (there are no actions by other
  characters), so they are unable to (ADR-055)."
<ROUTINE ASK-TO-TRY ("AUX" (N ,SAID-COUNT))
    <SETG PERSUADED 0>
    <FOLLOW-RULES ,PERSUASION-RULES>
    <COND (<EQUAL? ,PERSUADED 1>
           <SAY-CAP-THE ,P-ACTOR>
           <COND (<FSET? ,P-ACTOR ,PLURALBIT> <TELL " are">) (ELSE <TELL " is">)>
           <TELL " unable to do that." CR>)
          (<EQUAL? ,SAID-COUNT .N>
           <SAY-CAP-THE ,P-ACTOR>
           <COND (<FSET? ,P-ACTOR ,PLURALBIT> <TELL " have">) (ELSE <TELL " has">)>
           <TELL " better things to do." CR>)>>
) (ELSE)>

<ROUTINE TRY (ACTION FN O I "OPT" QUIET "AUX" OLD-A OLD-O OLD-I OLD-QUIET)
    ;"try <action>: run another action now, then carry on with this one"
    <SET OLD-A ,PRSA> <SET OLD-O ,PRSO> <SET OLD-I ,PRSI> <SET OLD-QUIET ,SILENTLY>
    <SETG PRSA .ACTION> <SETG PRSO .O> <SETG PRSI .I> <SETG SILENTLY .QUIET>
    <APPLY .FN>
    <SETG PRSA .OLD-A> <SETG PRSO .OLD-O> <SETG PRSI .OLD-I> <SETG SILENTLY .OLD-QUIET>>
