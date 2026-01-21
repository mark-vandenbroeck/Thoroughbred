from lexer import Lexer

l = Lexer()
code = "print ATH('1')"
print(f"Code: {code}")
tokens = list(l.tokenize(code))
for t in tokens:
    print(t)

code2 = "PRINT ATH('1')"
print(f"Code2: {code2}")
tokens2 = list(l.tokenize(code2))
for t in tokens2:
    print(t)
