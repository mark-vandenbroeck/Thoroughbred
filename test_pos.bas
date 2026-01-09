10 REM Test POS function
20 LET A$ = "XXSUBSTRXX"
30 PRINT "A$ = ", A$
40 PRINT "POS ('S' = A$):", POS ("S" = A$)
50 PRINT "POS ('S' = A$, 1, 2):", POS ("S" = A$, 1, 2)
60 PRINT "POS ('S' > A$):", POS ("S" > A$)
70 PRINT "POS ('Z' < A$):", POS ("Z" < A$)
80 PRINT "POS ('TR' = A$, -2):", POS ("TR" = A$, -2)
90 PRINT "POS ('TR' = A$, 3):", POS ("TR" = A$, 3)
100 PRINT "POS ('TR' = A$, -3):", POS ("TR" = A$, -3)
110 PRINT "POS ('X' = A$, 1, 0):", POS ("X" = A$, 1, 0)
120 END
