0010 PRINT 'CS', @(0,0), "Enhanced INPUT Test"
0020 INPUT @(5,5), 'BR', "Enter Name: ", 'ER', N$
0030 PRINT @(5,7), "Hello ", N$
0040 INPUT @(5,9), 'BU', "Enter Age: ", 'EU', A
0050 PRINT @(5,11), "You are ", A, " years old."
0060 PRINT @(5,13), "Testing multiple prompt parts..."
0070 INPUT 'BR', "PROMPT1 ", "PROMPT2 ", X$
0080 PRINT "You entered: ", X$
0090 PRINT "Test completed."
0100 END
