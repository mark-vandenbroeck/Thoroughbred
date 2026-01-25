10 PRINT "Testing TEXT files..."
20 TEXT "TESTTEXT"
30 PRINT "File created."
40 OPEN (1, OPT="TEXT") "TESTTEXT"
50 PRINT "Writing Line 1..."
60 WRITE (1, IND=0) "Line 1"
70 PRINT "Writing Line 2..."
80 WRITE (1, IND=10) "Line 2"
90 CLOSE (1)
100 PRINT "Closed. Re-opening..."
110 OPEN (1, OPT="TEXT") "TESTTEXT"
120 READ (1, IND=0) A$
130 PRINT "Read 1: '"; A$; "'"
140 READ (1, IND=10) B$
150 PRINT "Read 2: '"; B$; "'"
160 CLOSE (1)
170 RUN "read_raw"
180 END
