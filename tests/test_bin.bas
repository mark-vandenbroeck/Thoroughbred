0010 PRINT "Testing BIN function..."
0020 LET A$ = HTA(BIN(65, 3))
0030 PRINT "BIN(65, 3) = ", A$, " (Expected: 000041)"
0040 IF A$ <> "000041" THEN PRINT "Fail: BIN(65,3)"
0050 LET B$ = HTA(BIN(-65, 3))
0060 PRINT "BIN(-65, 3) = ", B$, " (Expected: FFFFBF)"
0070 IF B$ <> "FFFFBF" THEN PRINT "Fail: BIN(-65,3)"
0080 LET C$ = HTA(BIN(0, 2))
0090 PRINT "BIN(0, 2) = ", C$, " (Expected: 0000)"
0100 IF C$ <> "0000" THEN PRINT "Fail: BIN(0,2)"
0110 PRINT "Testing ERR= parameter..."
0120 SETERR 200
0130 LET D$ = BIN(3.14, 2)
0140 PRINT "Fail: BIN(3.14, 2) should have caused error"
0150 STOP
0200 PRINT "Success: Error caught by SETERR (expected for 3.14)"
0210 SETERR 0
0220 PRINT "Testing local ERR=..."
0230 LET E$ = BIN(3.14, 2, ERR=300)
0240 PRINT "Fail: BIN(3.14, 2, ERR=300) should have jumped"
0250 STOP
0300 PRINT "Success: Jumped to 300 via ERR= (expected for 3.14)"
0310 PRINT "All tests finished."
0320 END
