10 DIRECT "testkey", 10, 64, 0, 0
20 OPEN (1) "testkey"
30 WRITE (1, KEY="A") "Data A"
40 WRITE (1, KEY="C") "Data C"
50 WRITE (1, KEY="B") "Data B"
55 CLOSE (1)
56 OPEN (1) "testkey"
60 REM Sequential order should be A, B, C
70 LET K$ = KEY(1, ERR=800)
80 PRINT "First Key (implicit next from start): ", K$
90 READ (1, KEY="A")
100 PRINT "Next Key after A: ", KEY(1)
110 READ (1, KEY="B")
120 PRINT "Next Key after B: ", KEY(1)
130 READ (1, KEY="C")
140 LET K$ = KEY(1, ERR=200)
150 PRINT "Should not be here"
160 GOTO 999
200 PRINT "Caught EOF (ERR=2) as expected"
210 CLOSE (1)
220 ERASE "testkey"
230 END
800 PRINT "Unexpected Error on first key"
810 END
999 PRINT "Failed to catch EOF"
1000 END
