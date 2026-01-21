10 DIRECT "testiol", 30, 64, 0, 0
20 OPEN (1) "testiol"
30 IOLIST A$, B, C
35 Let A$="Hello"
36 Let B=42
37 Let C=3.14
40 WRITE (1, KEY="0", IOL=30)
50 READ (1, KEY="0", IOL=30)
60 PRINT "Read back: ", A$, B, C
70 IF A$ <> "Hello" THEN PRINT "FAIL A$" : END
80 IF B <> 42 THEN PRINT "FAIL B" : END
90 REM Test Mixed
100 IOLIST D$
110 WRITE (1, KEY="1", IOL=100) "World", "Extra"
120 READ (1, KEY="1") X$, Y$
130 PRINT "Mixed Read: ", X$, Y$
140 IF X$ <> "World" THEN PRINT "FAIL X$" : END
150 CLOSE (1)
160 ERASE "testiol"
170 END
