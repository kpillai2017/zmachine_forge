"Signed 16-bit arithmetic edge cases (§2, §15 div/mod)."
<VERSION 5>
<GLOBAL BIG 32767>

<ROUTINE SHOW (N) <PRINTN .N> <TELL CR>>

<ROUTINE GO ("AUX" (A -7) (B 2))
    <SHOW </ .A .B>>                 ;"-3  (division truncates toward zero)"
    <SHOW <MOD .A .B>>               ;"-1  (sign follows the dividend)"
    <SHOW <MOD 7 -2>>                ;"1"
    <SHOW <+ ,BIG 1>>                ;"-32768 (wraps)"
    <SHOW <* 300 300>>               ;"24464 (90000 mod 65536)"
    <SHOW <- 5>>                     ;"-5"
    <SHOW <+ 1 2 3 4>>               ;"10"
    <SHOW <- 10 <* 2 3> 1>>          ;"3 (operands evaluated left to right)"
    <SHOW <BAND 12 10>>              ;"8"
    <SHOW <BOR 12 10>>               ;"14"
    <SHOW <BCOM 0>>                  ;"-1"
    <COND (<AND <G? 3 2> <L? -1 0> <NOT <EQUAL? 1 2 3 4 5 6>>> <TELL "logic ok" CR>)>
    <COND (<EQUAL? 6 1 2 3 4 5 6> <TELL "equal? chain ok" CR>)>
    <QUIT>>
