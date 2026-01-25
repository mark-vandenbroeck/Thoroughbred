10 PRINT "--- SDX FUNCTION TEST ---"
20 PRINT "1. Basic Tests (Expected: R300)"
30 PRINT "READ: ", SDX("READ"), " read: ", SDX("read"), " RED: ", SDX("RED")
40 PRINT ""
50 PRINT "2. Spelling Variants (Expected: B416)"
60 PRINT "boulevard: ", SDX("boulevard"), " bulavard: ", SDX("bulavard"), " blvrd: ", SDX("blvrd")
70 PRINT ""
80 PRINT "3. Name Variants (Expected: S530)"
90 PRINT "Smith: ", SDX("Smith"), " Smyth: ", SDX("Smyth")
100 PRINT ""
110 PRINT "4. Error Handling (Expected: Jump to 200)"
120 LET A$ = SDX("", ERR=200)
130 PRINT "FAILURE: SDX did not jump on empty string"
140 END
200 PRINT "SUCCESS: Correctly jumped on empty string"
210 END
