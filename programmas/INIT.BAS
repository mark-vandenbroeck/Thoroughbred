0010 PRINT 'CS', "Database Initialisatie - Ledenbeheer"
0020 PRINT "Bezig met aanmaken van bestanden op D2..."
0030 REM Bestanden aanmaken op disk 2
0040 REM Members: ID(6), Naam(30), Familienaam(30), Adres(40), GebDatum(10) -> ca 120 bytes
0050 DIRECT "MEMBERS.DAT", 6, 128, 2, ERR=1000
0060 PRINT "MEMBERS.DAT aangemaakt."
0070 REM Courses: ID(6), Naam(30), Prijs(10), MaxLeden(4) -> ca 50 bytes
0080 DIRECT "COURSES.DAT", 6, 64, 2, ERR=1100
0090 PRINT "COURSES.DAT aangemaakt."
0100 REM Enroll: MemberID(6)+CourseID(6) = 12 bytes key
0110 DIRECT "ENROLL.DAT", 12, 16, 2, ERR=1200
0120 PRINT "ENROLL.DAT aangemaakt."
0130 PRINT "Initialisatie voltooid."
0140 END
1000 PRINT "Fout bij aanmaken MEMBERS.DAT (Bestand bestaat mogelijk al)"
1010 GOTO 0070
1100 PRINT "Fout bij aanmaken COURSES.DAT"
1110 GOTO 0100
1200 PRINT "Fout bij aanmaken ENROLL.DAT"
1210 GOTO 0130
