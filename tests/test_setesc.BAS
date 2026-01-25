10 PRINT "--- SETESC TEST ---"
20 SETESC 100
30 PRINT "Looping... Press Ctrl+C (as proxy for ESC in console) or ESC (in GUI)"
40 LET I = I + 1
50 IF I < 1000000 THEN GOTO 40
60 PRINT "Loop finished without ESC."
70 END
100 PRINT "ESC Trapped! ERR =", ERR
110 PRINT "I value was: ", I
120 PRINT "Returning..."
130 RETURN
