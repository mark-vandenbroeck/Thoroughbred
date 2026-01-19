10 REM Test Cursor Addressing
20 PRINT @(35, 0) "HOOFD TITEL"
30 PRINT @(0, 2) "Links Boven (0,2)"
40 PRINT @(60, 2) "Rechts Boven (60,2)"
50 FOR I = 5 TO 15
60   PRINT @(10, I) "Regel "; I
70   PRINT @(40, I) "Waarde "; I * 10
80 NEXT I
90 PRINT @(0, 22) "Onderaan scherm..."
100 PRINT @(30, 23) "KLAAR"
110 END
