from interpreter import ThoroughbredBasicInterpreter
import sys
class IO:
    def write(self, text): 
        sys.stderr.write(f"WRITE: {text}\n")
    def input(self, prompt=""): return ""
interp = ThoroughbredBasicInterpreter(IO())
interp.load_program('10 PRINT "HELLO"')
interp.execute()
