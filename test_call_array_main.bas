10 REM Array passing test
20 DIM A(5)
30 LET A(0)=10
35 LET A(1)=20
40 PRINT "MAIN BEFORE:", A(0), A(1)
50 CALL "test_call_array_sub", A[ALL]
60 PRINT "MAIN AFTER:", A(0), A(1)
70 END
