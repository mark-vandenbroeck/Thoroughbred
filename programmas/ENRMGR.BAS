0010 REM Enrollment Manager
0020 PRINT 'CS', @(25,2), 'BR', " INSCHRIJVINGEN ", 'ER'
0030 PRINT @(10,5), "1. Lid inschrijven voor kursus"
0040 PRINT @(10,7), "2. Inschrijvingen bekijken"
0050 PRINT @(10,9), "0. Terug naar Menu"
0060 INPUT @(10,12), "Keuze: ", K
0070 IF K = 0 THEN EXIT
0080 IF K = 1 THEN GOTO 0100
0090 IF K = 2 THEN GOTO 0500
0095 GOTO 0020
0100 REM Inschrijven
0110 PRINT 'CS', @(25,2), "INSCHRIJVEN"
0120 INPUT @(10,5), "Lid ID: ", MID$
0130 INPUT @(10,7), "Kursus ID: ", CID$
0140 REM Controleer of ID's bestaan (optioneel, voor nu direct opslaan)
0150 LET EKEY$ = MID$ + CID$
0160 OPEN (1) "ENROLL.DAT"
0170 WRITE (1, KEY=EKEY$) "OK"
0180 CLOSE (1)
0190 PRINT @(10,15), "Inschrijving voltooid!"
0200 INPUT @(10,17), "Druk op Enter...", D$
0210 GOTO 0020
0500 REM Bekijken
0510 PRINT 'CS', @(25,2), "INSCHRIJVINGEN LIJST"
0520 OPEN (1) "ENROLL.DAT", ERR=0600
0530 LET ROW = 5
0540 READRECORD (1, IND=0, ERR=0590) K$, R$
0545 IF LEN(K$) < 12 THEN GOTO 0590
0550 LET MID$ = K$(1,6)
0560 LET CID$ = K$(7,6)
0570 PRINT @(5, ROW), "Lid: ", MID$, " Kursus: ", CID$
0580 LET ROW = ROW + 1
0585 GOTO 0540
0590 CLOSE (1)
0595 INPUT "Druk op Enter...", D$
0598 GOTO 0020
0600 PRINT @(10,15), "Geen inschrijvingen gevonden!"
0610 CLOSE (1)
0620 INPUT @(10,17), "Druk op Enter...", D$
0630 GOTO 0020
