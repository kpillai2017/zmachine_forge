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
    <COND (<RUN-STAGE .RULES ,BEFORE-STAGE> <RFALSE>)>
    <COND (<RUN-STAGE .RULES ,INSTEAD-STAGE> <RFALSE>)>
    <COND (<RUN-STAGE .RULES ,CHECK-STAGE> <RFALSE>)>
    <RUN-STAGE .RULES ,CARRY-OUT-STAGE>
    <COND (<RUN-STAGE .RULES ,AFTER-STAGE> <RTRUE>)>
    <COND (<NOT ,SILENTLY> <RUN-STAGE .RULES ,REPORT-STAGE>)>
    <RTRUE>>

<ROUTINE RUN-STAGE (RULES STAGE)
    <COND (<FOLLOW-RULES <GET .RULES .STAGE>> <RTRUE>)>
    <FOLLOW-RULES <GET ,GENERAL-RULES .STAGE>>>

<ROUTINE FOLLOW-RULES (TBL "AUX" N)
    ;"run the rules in an LTABLE in order; true as soon as one decides"
    <SET N <GET .TBL 0>>
    <DO (I 1 .N)
        <COND (<APPLY <GET .TBL .I>> <RTRUE>)>>   ;"RTRUE leaves the routine, not just the loop"
    <RFALSE>>

<ROUTINE TRY (ACTION FN O I "OPT" QUIET "AUX" OLD-A OLD-O OLD-I OLD-QUIET)
    ;"try <action>: run another action now, then carry on with this one"
    <SET OLD-A ,PRSA> <SET OLD-O ,PRSO> <SET OLD-I ,PRSI> <SET OLD-QUIET ,SILENTLY>
    <SETG PRSA .ACTION> <SETG PRSO .O> <SETG PRSI .I> <SETG SILENTLY .QUIET>
    <APPLY .FN>
    <SETG PRSA .OLD-A> <SETG PRSO .OLD-O> <SETG PRSI .OLD-I> <SETG SILENTLY .OLD-QUIET>>
