10 PRINT "--- RUN DIRECTIVE TEST ---"
20 LET A$ = "PERSISTENT"
30 PRINT "Starting main program. A$ =", A$
40 PRINT "Executing: RUN 'tests/test_run_target.BAS'"
50 RUN "tests/test_run_target.BAS"
60 PRINT "FAILURE: Returned to main program after RUN"
