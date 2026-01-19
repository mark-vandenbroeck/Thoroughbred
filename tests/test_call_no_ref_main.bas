10 REM No-ref test
20 DIM A(5)
30 LET A(0)=10
40 PRINT "MAIN BEFORE:", A(0)
50 CALL "test_call_no_ref_sub", A(0)
60 PRINT "MAIN AFTER:", A(0)
70 END
