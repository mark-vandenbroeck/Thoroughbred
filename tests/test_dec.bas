0010 PRINT "Testing DEC function..."
0020 LET A = DEC("A")
0030 PRINT "DEC(""A"") = ", A, " (Expected: 65)"
0040 IF A <> 65 THEN PRINT "Fail: DEC(""A"")"
0050 LET B = DEC("AB")
0060 PRINT "DEC(""AB"") = ", B, " (Expected: 16706)"
0070 IF B <> 16706 THEN PRINT "Fail: DEC(""AB"")"
0080 LET C = DEC(BIN(193, 1))
0090 PRINT "DEC(BIN(193, 1)) = ", C, " (Expected: -63)"
0100 IF C <> -63 THEN PRINT "Fail: DEC(BIN(193, 1))"
0110 PRINT "Testing large value..."
0120 LET D$ = BIN(12345678, 4)
0130 LET D = DEC(D$)
0140 PRINT "DEC(BIN(12345678, 4)) = ", D, " (Expected: 12345678)"
0150 IF D <> 12345678 THEN PRINT "Fail: Large Value"
0160 PRINT "Testing ERR= parameter..."
0170 SETERR 300
0180 LET E = DEC(123)
0190 PRINT "Fail: DEC(123) should have caused error"
0200 STOP
0300 PRINT "Success: Error caught by SETERR (expected for non-string)"
0310 SETERR 0
0320 PRINT "Testing local ERR=..."
0330 LET F = DEC(123, ERR=400)
0340 PRINT "Fail: DEC(123, ERR=400) should have jumped"
0350 STOP
0400 PRINT "Success: Jumped to 400 via ERR= (expected for non-string)"
0410 PRINT "All tests finished."
0420 END
