import re

class Token:
    def __init__(self, type, value, line=None):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    def __init__(self):
        # Token specification
        self.token_specification = [
            ('NUMBER',   r'\d+(\.\d*)?'),  # Integer or decimal number
            ('STRING',   r'"[^"]*"'),      # String literal
            ('MNEMONIC', r"'[A-Z0-9]+'"),  # Thoroughbred Mnemonics (e.g. 'CS')
            ('ID_STR',   r'[A-Z][A-Z0-9]*\$'), # String variable
            ('ID_NUM',   r'[A-Z][A-Z0-9]*'),    # Numeric variable
            ('ASSIGN',   r'='),            # Assignment operator
            ('OP',       r'[+\-*/]'),       # Arithmetic operators
            ('RELOP',    r'[<>]=?|='),      # Relational operators
            ('AT',       r'@'),            # Cursor addressing
            ('LPAREN',   r'\('),           # (
            ('RPAREN',   r'\)'),           # )
            ('LBRACKET', r'\['),           # [
            ('RBRACKET', r'\]'),           # ]
            ('COMMA',    r','),            # ,
            ('SEMICOLON', r';'),           # ;
            ('NEWLINE',  r'\n'),           # Line endings
            ('SKIP',     r'[ \t]+'),       # Skip over spaces and tabs
            ('MISMATCH', r'.'),            # Any other character
        ]
        
        self.keywords = {
            'PRINT', 'LET', 'IF', 'THEN', 'ELSE', 'GOTO', 'GOSUB', 'RETURN', 'INPUT', 
            'FOR', 'TO', 'NEXT', 'STEP', 'END', 'REMARK', 'REM',
            'OPEN', 'CLOSE', 'READ', 'WRITE', 'DIRECT', 'INDEXED', 'SERIAL', 'SORT',
            'IND', 'KEY', 'ERASE', 'SELECT', 'EXTRACT', 'EXTRACTRECORD', 'ERR', 'DOM',
            'DIM', 'CALL', 'ENTER', 'EXIT', 'ALL', 'POS',
            'LEN', 'STR$', 'VAL', 'ASC', 'CHR$', 'UCS', 'LCS', 'CVS',
            'ABS', 'INT', 'SQR', 'SIN', 'COS', 'TAN', 'ATN', 'LOG', 'EXP', 'RND', 'SGN', 
            'MOD', 'ROUND', 'FPT', 'IPT'
        }

    def tokenize(self, text):
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specification)
        for mo in re.finditer(tok_regex, text.upper()):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'NUMBER':
                value = float(value) if '.' in value else int(value)
            elif kind == 'ID_NUM' or kind == 'ID_STR':
                if value in self.keywords:
                    kind = value
            elif kind == 'SKIP':
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'{value!r} unexpected on line')
            yield Token(kind, value)
