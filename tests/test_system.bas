10 PRINT "Testing SYSTEM command..."
20 SYSTEM "echo 'Hello from Subprocess'"
30 PRINT "Testing multiline command (Unix only)"
40 SYSTEM "ls -1 | head -n 3"
50 PRINT "Completed."
60 END
