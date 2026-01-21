from interpreter import ThoroughbredBasicInterpreter
from lexer import Lexer

interp = ThoroughbredBasicInterpreter()
l = Lexer()

code = "PRINT ATH('41')"
print(f"--- Executing: {code} ---")
tokens = list(l.tokenize(code))
print("Tokens:", tokens)
interp.execute_direct(code)

print("\n")

code2 = 'PRINT ATH("41")'
print(f"--- Executing: {code2} ---")
tokens2 = list(l.tokenize(code2))
print("Tokens:", tokens2)
interp.execute_direct(code2)
