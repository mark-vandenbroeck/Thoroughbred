10 PRINT "--- Inside test_run_target.BAS ---"
20 PRINT "A$ value: ", A$
30 IF A$ = "PERSISTENT" THEN PRINT "SUCCESS: Variable preserved" ELSE PRINT "FAILURE: Variable lost"
40 PRINT ""
50 PRINT "Testing stack reset (GOSUB stack should be empty)..."
60 SETERR 100
70 RETURN
80 PRINT "FAILURE: RETURN did not trigger error"
90 END
100 PRINT "SUCCESS: RETURN triggered error (expected after RUN reset)"
110 SETERR 0
120 PRINT ""
130 IF RESTARTED = 1 THEN GOTO 200
140 PRINT "Testing program restart (RUN without name)..."
150 LET RESTARTED = 1
160 RUN
200 PRINT "SUCCESS: Program restarted and 'RESTARTED' flag preserved"
210 PRINT ""
220 PRINT "Testing missing file with ERR=..."
230 RUN "NONEXISTENT.BAS", ERR=300
240 PRINT "FAILURE: Did not jump on missing file"
250 END
300 PRINT "SUCCESS: Correctly jumped to 300 on missing file"
310 PRINT "--- RUN TEST COMPLETE ---"
320 END
