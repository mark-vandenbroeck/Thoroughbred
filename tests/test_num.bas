10 REM Test NUM function
20 PRINT "NUM('1234') = ", NUM("1234")
30 PRINT "NUM('12.34') = ", NUM("12.34")
40 LET C$ = ".24E+5"
50 PRINT "NUM('.24E+5') = ", NUM(C$)
60 PRINT "NUM('12 34') = ", NUM("12 34")
70 PRINT "Testing ERR= jump logic..."
80 LET X = NUM("12345,67", ERR=200)
90 PRINT "FAILED TO CATCH ERROR - Execution continued mistakenly"
100 GOTO 300
200 PRINT "Caught Error as Expected (Jumped to 200)"
210 REM Test NTP and SIZ
220 PRINT "NUM('123.456', SIZ=.02) -> 123.5 ? ", NUM("123.456", SIZ=.02)
230 PRINT "NUM('123.456', SIZ=.01) -> 123 ? ", NUM("123.456", SIZ=.01)
240 REM Test Mixed Args
250 LET S$ = "999"
260 PRINT "NUM(S$, NTP=0) = ", NUM(S$, NTP=0)
300 END
