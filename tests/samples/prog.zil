"prog.zil - PROG / BIND semantics (eval case prog-bind, ADR-017)"

<VERSION 5>
<GLOBAL G 0>
<ROUTINE GO ("AUX" V)
  <SET V <PROG ((X 10)) <COND (<G? .X 5> <RETURN <* .X 2>>)> 99>>
  <TELL "prog-return " N .V CR>
  <SET V <PROG ((N 0)) <SET N <+ .N 1>> <COND (<L? .N 4> <AGAIN>)> .N>>
  <TELL "prog-again " N .V CR>
  <SET V <BIND ((B 7)) <+ .B 1>>>
  <TELL "bind-value " N .V CR>
  <TELL "bind-return " N <BIND-RET> CR>
  <TELL "sum " N <SUM 4> CR>
  <QUIT>>
<ROUTINE BIND-RET ()
  <PROG ()
     <BIND ((Z 5)) <RETURN <+ .Z 100>>>
     <TELL "not reached" CR>>>
<ROUTINE SUM (K "AUX" T)
  <DO (I 1 .K) <PROG ((SQ <* .I .I>)) <SET T <+ .T .SQ>>>>
  .T>
