10 REM Test HEX functions
20 PRINT "ATH('41') = ", ATH("41")
30 PRINT "ATH('2A') = ", ATH("2A")
40 LET S$ = ATH("414243")
50 PRINT "S$ = ", S$
60 PRINT "HTA(S$) = ", HTA(S$)
70 PRINT "HTA('A') = ", HTA("A")
80 PRINT "ATH('1') -> '01' -> >"; ATH("1"); "<"
90 PRINT "HTA('1') = ", HTA("1")
100 REM Test Mnemonic arg
110 PRINT "ATH('1' mnemonic) -> >"; ATH('1'); "<"
120 END
