10 DIRECT "testfind", 10, 64, 0
20 OPEN (1) "testfind"
30 WRITE (1, KEY="10") "Ten"
40 WRITE (1, KEY="30") "Thirty"
50 WRITE (1, KEY="50") "Fifty"

100 REM Case 1: READ Missing Key advances pointer
110 READ (1, KEY="10")
120 LET K$ = KEY(1)
130 IF K$ <> "30" THEN PRINT "FAIL 1: Expected 30, got "; K$ : STOP
140 PRINT "At 10, Next is 30. Now READ 40 (Missing)..."
150 READ (1, KEY="40", ERR=160)
160 LET K$ = KEY(1)
170 PRINT "After READ 40, Next is "; K$
180 IF K$ <> "50" THEN PRINT "FAIL 2: Expected 50 (READ should advance), got "; K$ : STOP

200 REM Case 2: FIND Missing Key does NOT advance pointer
210 READ (1, KEY="10")
220 PRINT "Reset to 10. Next is 30. Now FIND 40 (Missing)..."
230 FIND (1, KEY="40", ERR=240)
240 LET K$ = KEY(1)
250 PRINT "After FIND 40, Next is "; K$
260 IF K$ <> "30" THEN PRINT "FAIL 3: Expected 30 (FIND should NOT advance from 10), got "; K$ : STOP

300 REM Case 3: FIND Success does move pointer (to the found record)
310 FIND (1, KEY="50")
320 REM Pointer should be at 50. Next is EOF (Error).
330 READ (1, ERR=340)
340 PRINT "At 50. Next read failed as expected."

400 REM Case 4: FIND RECORD reads entire record as one string
410 FIND RECORD (1, KEY="10") R$
420 PRINT "FIND RECORD 10: "; R$
430 IF R$ <> "Ten" THEN PRINT "FAIL 4: Expected Ten, got "; R$ : STOP

500 PRINT "SUCCESS"
510 CLOSE (1)
520 ERASE "testfind"
530 END
