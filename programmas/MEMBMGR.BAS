0010 REM Member Manager
0020 PRINT 'CS', @(25,2), 'BR', " LEDEN BEHEER ", 'ER'
0030 PRINT @(10,5), "1. Lid Toevoegen"
0040 PRINT @(10,7), "2. Lid Zoeken / Wijzigen"
0050 PRINT @(10,9), "0. Terug naar Menu"
0060 INPUT @(10,12), "Keuze: ", K
0070 IF K = 0 THEN EXIT
0080 IF K = 1 THEN GOTO 0100
0090 IF K = 2 THEN GOTO 0500
0095 GOTO 0020
0100 REM Lid Toevoegen
0110 PRINT 'CS', @(25,2), "LID TOEVOEGEN"
0120 INPUT @(10,5), "Lid ID (6 tekens): ", ID$
0130 IF LEN(ID$) <> 6 THEN GOTO 0120
0140 INPUT @(10,7), "Voornaam: ", VN$
0150 INPUT @(10,8), "Familienaam: ", FN$
0160 INPUT @(10,9), "Adres: ", AD$
0170 INPUT @(10,10), "Geboortedatum: ", GD$
0180 REM Data inpakken
0190 LET REC$ = VN$ + FILL(30-LEN(VN$)) + FN$ + FILL(30-LEN(FN$)) + AD$ + FILL(40-LEN(AD$)) + GD$ + FILL(10-LEN(GD$))
0200 OPEN (1) "MEMBERS.DAT"
0210 WRITE (1, KEY=ID$) REC$
0220 CLOSE (1)
0230 PRINT @(10,15), "Lid opgeslagen!"
0240 INPUT @(10,17), "Druk op Enter...", D$
0250 GOTO 0020
0500 REM Lid Zoeken
0510 PRINT 'CS', @(25,2), "LID ZOEKEN"
0520 INPUT @(10,5), "Lid ID: ", ID$
0530 OPEN (1) "MEMBERS.DAT", ERR=0600
0540 READ (1, KEY=ID$, ERR=0600) REC$
0550 CLOSE (1)
0560 LET VN$ = REC$(1,30)
0570 LET FN$ = REC$(31,30)
0580 PRINT @(10,7), "Voornaam: ", VN$
0590 PRINT @(10,8), "Familienaam: ", FN$
0595 INPUT @(10,15), "Druk op Enter...", D$
0598 GOTO 0020
0600 PRINT @(10,15), "Lid niet gevonden!"
0610 CLOSE (1)
0620 INPUT @(10,17), "Druk op Enter...", D$
0630 GOTO 0020
