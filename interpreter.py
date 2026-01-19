import json
import os
import re
import sys
import math
import random


from file_manager import FileManager
from lexer import Lexer, Token

class ThoroughbredBasicInterpreter:
    def __init__(self, io_handler=None):
        self.context_stack = []
        self.file_manager = FileManager()
        self.io_handler = io_handler # Can be None for stdout/stdin fallback
        self.lexer = Lexer()
        
        # Initial context for the main program
        self._push_context({}, [])

    def _push_context(self, program, line_numbers, variables=None, passed_args=None):
        self.context_stack.append({
            'program': program,
            'line_numbers': line_numbers,
            'current_line_idx': 0,
            'variables': variables if variables is not None else {},
            'gosub_stack': [],
            'for_loops': {},
            'passed_args': passed_args or [],
            'caller_refs': {} # local_name -> {'ctx_idx': idx, 'var_name': name, 'is_all': bool}
        })

    def _curr(self):
        return self.context_stack[-1]

    @property
    def variables(self): return self._curr()['variables']
    @property
    def program(self): return self._curr()['program']
    @program.setter
    def program(self, value): self._curr()['program'] = value
    @property
    def line_numbers(self): return self._curr()['line_numbers']
    @line_numbers.setter
    def line_numbers(self, value): self._curr()['line_numbers'] = value
    @property
    def current_line_idx(self): return self._curr()['current_line_idx']
    @current_line_idx.setter
    def current_line_idx(self, value): self._curr()['current_line_idx'] = value
    @property
    def stack(self): return self._curr()['gosub_stack']
    @property
    def for_loops(self): return self._curr()['for_loops']

    def load_program(self, source_code):
        self.program = {}
        for line in source_code.splitlines():
            if not line.strip():
                continue
            
            tokens = list(self.lexer.tokenize(line))
            if not tokens:
                continue
                
            if tokens[0].type == 'NUMBER':
                line_number = tokens[0].value
                self.program[line_number] = tokens[1:]
            else:
                # Direct mode not supported in this simple version
                print(f"Skipping line without line number: {line}")
        
        self.line_numbers = sorted(self.program.keys())

    def evaluate_expression(self, tokens):
        """
        A simplified expression evaluator that handles:
        - Parentheses for grouping: (A + B)
        - Array indexing: A(1), S$[1]
        - Substrings: S$(1, 5)
        - Basic arithmetic: +, -, *, /
        - Literals and Variables
        """
        if not tokens:
            return None

        # Helper to find matching bracket/parenthesis
        def find_matching(start_idx, open_type, close_type):
            count = 0
            for i in range(start_idx, len(tokens)):
                if tokens[i].type == open_type: count += 1
                elif tokens[i].type == close_type:
                    count -= 1
                    if count == 0: return i
            return -1

        # 1. Handle built-in functions: POS(...)
        if tokens[0].type == 'POS' and len(tokens) > 2 and tokens[1].type == 'LPAREN':
            close_idx = find_matching(1, 'LPAREN', 'RPAREN')
            if close_idx != -1:
                inner = tokens[2:close_idx]
                # POS syntax is unique: (search relop reference [, step [, occurrence]])
                # We need to split by relop first, then by commas for optional args.
                relop_idx = -1
                for i, t in enumerate(inner):
                    if t.type == 'RELOP' or (t.type == 'ASSIGN' and t.value == '='):
                        relop_idx = i
                        break
                
                if relop_idx != -1:
                    search_tokens = inner[:relop_idx]
                    relop = inner[relop_idx].value
                    
                    # The rest: reference [, step [, occurrence]]
                    rest = inner[relop_idx+1:]
                    parts = []
                    current = []
                    depth = 0
                    for t in rest:
                        if t.type in ('LPAREN', 'LBRACKET'): depth += 1
                        elif t.type in ('RPAREN', 'RBRACKET'): depth -= 1
                        if depth == 0 and t.type == 'COMMA':
                            parts.append(current)
                            current = []
                        else:
                            current.append(t)
                    if current: parts.append(current)
                    
                    search_str = str(self.evaluate_expression(search_tokens))
                    ref_str = str(self.evaluate_expression(parts[0]))
                    step = int(self.evaluate_expression(parts[1])) if len(parts) > 1 else 1
                    occ_target = int(self.evaluate_expression(parts[2])) if len(parts) > 2 else 1
                    
                    found_count = 0
                    search_len = len(search_str)
                    ref_len = len(ref_str)
                    
                    # Normalize relops
                    if relop == '><': relop = '<>'
                    if relop == '=>': relop = '>='
                    if relop == '=<': relop = '<='
                    
                    def compare(s1, s2, op):
                        res = False
                        if op == '=': res = (s1 == s2)
                        elif op == '<>': res = (s1 != s2)
                        elif op == '<': res = (s1 < s2)
                        elif op == '>': res = (s1 > s2)
                        elif op == '<=': res = (s1 <= s2)
                        elif op == '>=': res = (s1 >= s2)
                        return res

                    # Iteration range
                    if step > 0:
                        indices = range(0, ref_len - search_len + 1, step)
                    elif step < 0:
                        indices = range(ref_len - search_len, -1, step)
                    else:
                        indices = [] # Step 0? Invalid but handle safely
                    
                    for i in indices:
                        segment = ref_str[i:i+search_len]
                        if compare(search_str, segment, relop):
                            found_count += 1
                            if occ_target != 0 and found_count == occ_target:
                                return i + 1 # 1-based index
                    
                    if occ_target == 0:
                        return found_count
                    return 0
        
                    if occ_target == 0:
                        return found_count
                    return 0
        
        # 1b. Handle built-in functions
        builtins = {'LEN', 'STR$', 'VAL', 'ASC', 'CHR$', 'UCS', 'LCS', 'CVS',
                    'ABS', 'INT', 'SQR', 'SIN', 'COS', 'TAN', 'ATN', 'LOG', 'EXP', 'RND', 'SGN', 
                    'MOD', 'ROUND', 'FPT', 'IPT'}
        
        if tokens[0].type in builtins and len(tokens) > 2 and tokens[1].type == 'LPAREN':
            close_idx = find_matching(1, 'LPAREN', 'RPAREN')
            if close_idx != -1:
                inner = tokens[2:close_idx]
                # Split args by COMMA
                args = []
                current = []
                d = 0
                for t in inner:
                    if t.type in ('LPAREN', 'LBRACKET'): d+=1
                    elif t.type in ('RPAREN', 'RBRACKET'): d-=1
                    if d==0 and t.type == 'COMMA':
                        args.append(current)
                        current = []
                    else:
                        current.append(t)
                if current: args.append(current)
                
                func = tokens[0].type
                
                # Helper to evaluate single arg
                def eval_arg(idx):
                    if idx < len(args): return self.evaluate_expression(args[idx])
                    return None

                val1 = eval_arg(0)
                
                # String Functions
                if func == 'LEN': return len(str(val1))
                elif func == 'STR$': return str(val1)
                elif func == 'VAL':
                    try: return float(str(val1))
                    except: return 0.0
                elif func == 'ASC': return ord(str(val1)[0]) if str(val1) else 0
                elif func == 'CHR$': return chr(int(val1))
                elif func == 'UCS': return str(val1).upper()
                elif func == 'LCS': return str(val1).lower()
                elif func == 'CVS':
                    s = str(val1)
                    code = int(eval_arg(1) or 0)
                    if code & 1: s = s.lstrip()
                    if code & 2: s = s.rstrip()
                    if code & 16: s = s.upper()
                    if code & 32: s = s.lower()
                    return s

                # Numeric Functions
                try:
                    n1 = float(val1) if val1 is not None else 0.0
                except:
                    n1 = 0.0 # Strict basic might error, here we default

                if func == 'ABS': return abs(n1)
                elif func == 'INT': return math.floor(n1)
                elif func == 'IPT': return int(n1) # Integer part (truncation)
                elif func == 'FPT': return round(n1 - int(n1), 10) # Fractional part (cleaned)
                elif func == 'SGN': return (n1 > 0) - (n1 < 0)
                elif func == 'SQR': return math.sqrt(n1) if n1 >= 0 else 0
                elif func == 'SIN': return math.sin(n1)
                elif func == 'COS': return math.cos(n1)
                elif func == 'TAN': return math.tan(n1)
                elif func == 'ATN': return math.atan(n1)
                elif func == 'EXP': return math.exp(n1)
                elif func == 'LOG': return math.log(n1) if n1 > 0 else 0
                elif func == 'RND': return random.random() # RND(X) often uses X to seed or determine range, but simple RND() 0-1 is standard-ish fallback
                elif func == 'MOD':
                    n2 = float(eval_arg(1) or 0)
                    return int(n1 % n2)
                elif func == 'ROUND':
                    n2 = int(eval_arg(1) or 0)
                    return round(n1, n2)


        # 2. Handle single values / atoms (Base case)
        if len(tokens) == 1:
            token = tokens[0]
            if token.type == 'NUMBER' or token.type == 'STRING':
                val = token.value
                if isinstance(val, str) and val.startswith('"'):
                    val = val[1:-1]
                return val
            elif token.type in ('ID_NUM', 'ID_STR'):
                return self.variables.get(token.value, 0 if token.type == 'ID_NUM' else "")
            return 0

        # 2. Handle indexing/substrings: ID(idx) or ID[idx] or ID(start, len)
        if tokens[0].type in ('ID_NUM', 'ID_STR') and len(tokens) > 1:
            if tokens[1].type in ('LPAREN', 'LBRACKET'):
                open_type = tokens[1].type
                close_type = 'RPAREN' if open_type == 'LPAREN' else 'RBRACKET'
                match_idx = find_matching(1, open_type, close_type)
                if match_idx != -1:
                    var_name = tokens[0].value
                    # Extract arguments between brackets/parentheses
                    inner_tokens = tokens[2:match_idx]
                    args = []
                    current_arg = []
                    for t in inner_tokens:
                        if t.type == 'COMMA':
                            if current_arg: args.append(self.evaluate_expression(current_arg))
                            current_arg = []
                        else:
                            current_arg.append(t)
                    if current_arg: args.append(self.evaluate_expression(current_arg))

                    var_val = self.variables.get(var_name)
                    
                    # Case A: Numeric Array A(i, j, ...)
                    if tokens[0].type == 'ID_NUM' and open_type == 'LPAREN':
                        if isinstance(var_val, list):
                            # Simple flat list for now, or nested
                            # Assume 1D for now if it's a list
                            idx = int(args[0])
                            return var_val[idx] if 0 <= idx < len(var_val) else 0
                    
                    # Case B: String Array S$[i]
                    if tokens[0].type == 'ID_STR' and open_type == 'LBRACKET':
                        if isinstance(var_val, list):
                            idx = int(args[0])
                            return var_val[idx] if 0 <= idx < len(var_val) else ""

                    # Case C: Substring S$(start, len) or S$(start)
                    if tokens[0].type == 'ID_STR' and open_type == 'LPAREN':
                        s = str(var_val) if var_val is not None else ""
                        start = int(args[0]) - 1 # 1-based to 0-based
                        length = int(args[1]) if len(args) > 1 else len(s)
                        return s[start:start+length]

                    # If not handled, continue to arithmetic
                
        # 3. Handle grouping (rest of expression)
        # This part is still very basic and needs better precedence handler
        # but let's implement binary ops first.
        
        # Simplified precedence: just look for lowest precedence op (+, -)
        for op_type in ('+', '-'):
            depth = 0
            for i in range(len(tokens) - 1, 0, -1): # Start from end, stop at 1 (0 is always unary)
                t = tokens[i]
                if t.type in ('RPAREN', 'RBRACKET'): depth += 1
                elif t.type in ('LPAREN', 'LBRACKET'): depth -= 1
                elif depth == 0 and t.type == 'OP' and t.value == op_type:
                    # Check if binary: Preceded by a value-like token
                    prev = tokens[i-1]
                    if prev.type in ('NUMBER', 'STRING', 'ID_NUM', 'ID_STR', 'RPAREN', 'RBRACKET'):
                        left = self.evaluate_expression(tokens[:i])
                        right = self.evaluate_expression(tokens[i+1:])
                        if op_type == '+': return left + right
                        if op_type == '-': return left - right

        for op_type in ('*', '/'):
            depth = 0
            for i in range(len(tokens) - 1, 0, -1): # Stop at 1
                t = tokens[i]
                if t.type in ('RPAREN', 'RBRACKET'): depth += 1
                elif t.type in ('LPAREN', 'LBRACKET'): depth -= 1
                elif depth == 0 and t.type == 'OP' and t.value == op_type:
                    prev = tokens[i-1]
                    if prev.type in ('NUMBER', 'STRING', 'ID_NUM', 'ID_STR', 'RPAREN', 'RBRACKET'):
                        left = self.evaluate_expression(tokens[:i])
                        right = self.evaluate_expression(tokens[i+1:])
                        if op_type == '*': return left * right
                        if op_type == '/': return left / right

        # Unary minus
        if tokens[0].type == 'OP' and tokens[0].value == '-':
            return -self.evaluate_expression(tokens[1:])

        # Parentheses/Brackets at the beginning
        if tokens[0].type in ('LPAREN', 'LBRACKET'):
            close_type = 'RPAREN' if tokens[0].type == 'LPAREN' else 'RBRACKET'
            match_idx = find_matching(0, tokens[0].type, close_type)
            if match_idx == len(tokens) - 1:
                return self.evaluate_expression(tokens[1:match_idx])

        # Atom
        if len(tokens) == 1:
            token = tokens[0]
            if token.type == 'NUMBER' or token.type == 'STRING':
                val = token.value
                if isinstance(val, str) and val.startswith('"'):
                    val = val[1:-1]
                return val
            elif token.type in ('ID_NUM', 'ID_STR'):
                return self.variables.get(token.value, 0 if token.type == 'ID_NUM' else "")

        return 0

    def _handle_file_error(self, err_type, options):
        """Helper to route execution based on ERR= or DOM= options."""
        if err_type == 'DOM' and 'DOM' in options:
            try:
                target = int(float(options['DOM']))
                if target in self.line_numbers:
                    self.current_line_idx = self.line_numbers.index(target)
                    return True
            except: pass
        if 'ERR' in options:
            try:
                target = int(float(options['ERR']))
                if target in self.line_numbers:
                    self.current_line_idx = self.line_numbers.index(target)
                    return True
            except: pass
        return False

    def execute(self):
        self.current_line_idx = 0
        while self.current_line_idx < len(self.line_numbers):
            try:
                line_num = self.line_numbers[self.current_line_idx]
                tokens = self.program[line_num]
                
                if not tokens:
                    self.current_line_idx += 1
                    continue

                cmd = tokens[0].type
                
                if cmd == 'PRINT':
                    # Improved PRINT: comma/semicolon aware, but skips those inside () or []
                    # Check for @(col, row)
                    current_idx = 1
                    if current_idx < len(tokens) and tokens[current_idx].type == 'AT':
                        # Expect LPAREN, col, COMMA, row, RPAREN
                        try:
                            if tokens[current_idx+1].type == 'LPAREN':
                                # Parse (col, row)
                                paren_end = -1
                                depth = 0
                                for i in range(current_idx+1, len(tokens)):
                                    if tokens[i].type == 'LPAREN': depth += 1
                                    elif tokens[i].type == 'RPAREN': 
                                        depth -= 1
                                        if depth == 0: 
                                            paren_end = i
                                            break
                                
                                if paren_end != -1:
                                    # Extract inside parens
                                    inside = tokens[current_idx+2:paren_end]
                                    # Split by comma
                                    parts = []
                                    curr = []
                                    d = 0
                                    for t in inside:
                                        if t.type in ('LPAREN', 'LBRACKET'): d+=1
                                        elif t.type in ('RPAREN', 'RBRACKET'): d-=1
                                        if d==0 and t.type == 'COMMA':
                                            parts.append(curr)
                                            curr = []
                                        else:
                                            curr.append(t)
                                    if curr: parts.append(curr)
                                    
                                    if len(parts) >= 2:
                                        col = int(self.evaluate_expression(parts[0]))
                                        row = int(self.evaluate_expression(parts[1]))
                                        if self.io_handler:
                                            self.io_handler.move_cursor(col, row)
                                    
                                    current_idx = paren_end + 1
                        except Exception:
                            pass # Fallback to normal print if parsing fails

                    output = []
                    current_expr = []
                    depth = 0
                    final_separator = None 

                    for t in tokens[current_idx:]:
                        if t.type == 'MNEMONIC':
                            # Flush current expression if any
                            if current_expr:
                                val = str(self.evaluate_expression(current_expr))
                                output.append(val)
                                current_expr = []
                            
                            # Handle Mnemonic
                            mnemonic = t.value[1:-1] # Strip quotes
                            if self.io_handler:
                                # Flush current output first
                                if output:
                                    text_out = " ".join(output)
                                    self.io_handler.write(text_out)
                                    output = []

                    for t in tokens[current_idx:]:
                        if t.type == 'MNEMONIC':
                            # Flush current expression if any
                            if current_expr:
                                val = str(self.evaluate_expression(current_expr))
                                output.append(val)
                                current_expr = []
                            
                            # Handle Mnemonic
                            mnemonic = t.value[1:-1] # Strip quotes
                            if self.io_handler:
                                # Flush current output first
                                if output:
                                    text_out = " ".join(output)
                                    self.io_handler.write(text_out)
                                    output = []

                                if mnemonic == 'CS': self.io_handler.clear_screen()
                                elif mnemonic == 'BR': self.io_handler.set_reverse(True)
                                elif mnemonic == 'ER': self.io_handler.set_reverse(False)
                                elif mnemonic == 'BU': self.io_handler.set_underline(True)
                                elif mnemonic == 'EU': self.io_handler.set_underline(False)
                                elif mnemonic == 'VT': self.io_handler.move_relative(0, -1)
                                elif mnemonic == 'LF': self.io_handler.move_relative(0, 1)
                                elif mnemonic == 'BS': self.io_handler.move_relative(-1, 0)
                                elif mnemonic == 'CH': self.io_handler.move_cursor(0, 0) # Home
                                elif mnemonic == 'CE': self.io_handler.clear_eos()
                                elif mnemonic == 'CL': self.io_handler.clear_eol()
                                elif mnemonic == 'LD': self.io_handler.delete_line()
                            # Ignore unknown mnemonics or add more later
                            
                            final_separator = None 
                            
                        else:
                            # Update depth for parens/brackets
                            if t.type in ('LPAREN', 'LBRACKET'): 
                                depth += 1
                            elif t.type in ('RPAREN', 'RBRACKET'): 
                                depth -= 1
                            
                            if depth == 0 and t.type in ('COMMA', 'SEMICOLON'):
                                if current_expr:
                                    val = str(self.evaluate_expression(current_expr))
                                    output.append(val)
                                    current_expr = []
                                    
                                # Handle spacing behavior
                                final_separator = t.type
                            else:
                                current_expr.append(t)
                                final_separator = None
                            
                    if current_expr:
                        output.append(str(self.evaluate_expression(current_expr)))
                    
                    # Construct string
                    text_out = " ".join(output)
                    if self.io_handler:
                        self.io_handler.write(text_out)
                        if final_separator != 'SEMICOLON':
                             self.io_handler.write("\n")
                    else:
                        # Fallback
                        print(text_out, end="" if final_separator == 'SEMICOLON' else "\n")
                        
                    self.current_line_idx += 1
                
                elif cmd == 'LET':
                    # Determine if it's a simple assignment or indexed/substring
                    # LET A = val
                    # LET A(idx) = val
                    # LET S$[idx] = val
                    # LET S$(start, len) = val
                    
                    var_name = tokens[1].value
                    idx_end = 1
                    params = []
                    open_type = None

                    if len(tokens) > 2 and tokens[2].type in ('LPAREN', 'LBRACKET'):
                        open_type = tokens[2].type
                        close_type = 'RPAREN' if open_type == 'LPAREN' else 'RBRACKET'
                        # Find matching bracket
                        depth = 0
                        for i in range(2, len(tokens)):
                            if tokens[i].type == open_type: depth += 1
                            elif tokens[i].type == close_type:
                                depth -= 1
                                if depth == 0:
                                    idx_end = i
                                    # Parse params
                                    inner = tokens[3:i]
                                    curr = []
                                    for t in inner:
                                        if t.type == 'COMMA':
                                            if curr: params.append(self.evaluate_expression(curr))
                                            curr = []
                                        else: curr.append(t)
                                    if curr: params.append(self.evaluate_expression(curr))
                                    break

                    # Find '='
                    assign_idx = -1
                    for i in range(idx_end + 1, len(tokens)):
                        if tokens[i].type == 'ASSIGN':
                            assign_idx = i
                            break
                    
                    val = self.evaluate_expression(tokens[assign_idx+1:])

                    if open_type is None:
                        # Simple LET A = val
                        self.variables[var_name] = val
                    else:
                        var_val = self.variables.get(var_name)
                        if open_type == 'LPAREN':
                            if tokens[1].type == 'ID_NUM':
                                # Numeric Array Assignment A(i) = val
                                if isinstance(var_val, list):
                                    idx = int(params[0])
                                    if 0 <= idx < len(var_val): var_val[idx] = val
                            else:
                                # Substring Assignment S$(start, len) = val
                                s = list(str(var_val)) if var_val is not None else []
                                start = int(params[0]) - 1
                                if len(params) > 1:
                                    length = int(params[1])
                                    val_str = str(val)[:length].ljust(length)
                                    s[start:start+length] = list(val_str)
                                else:
                                    val_str = str(val)
                                    s[start:start+len(val_str)] = list(val_str)
                                self.variables[var_name] = "".join(s)
                        
                        elif open_type == 'LBRACKET':
                            # String Array Assignment S$[i] = val
                            if isinstance(var_val, list):
                                idx = int(params[0])
                                if 0 <= idx < len(var_val): var_val[idx] = val

                    self.current_line_idx += 1
                
                elif cmd == 'DIM':
                    # DIM A(10), S$(20), S$[10](20)
                    idx = 1
                    while idx < len(tokens):
                        if tokens[idx].type == 'COMMA': idx += 1; continue
                        var_name = tokens[idx].value
                        var_type = tokens[idx].type
                        idx += 1
                        
                        dims = []
                        if idx < len(tokens) and tokens[idx].type in ('LPAREN', 'LBRACKET'):
                            open_t = tokens[idx].type
                            close_t = 'RPAREN' if open_t == 'LPAREN' else 'RBRACKET'
                            
                            # Find matching
                            count = 0
                            match_idx = -1
                            for i in range(idx, len(tokens)):
                                if tokens[i].type == open_t: count += 1
                                elif tokens[i].type == close_t:
                                    count -= 1
                                    if count == 0: match_idx = i; break
                            
                            inner = tokens[idx+1:match_idx]
                            # Correct parsing of dims (comma-aware)
                            curr = []
                            d_depth = 0
                            for t in inner:
                                if t.type in ('LPAREN', 'LBRACKET'): d_depth += 1
                                elif t.type in ('RPAREN', 'RBRACKET'): d_depth -= 1
                                if d_depth == 0 and t.type == 'COMMA':
                                    if curr: dims.append(int(self.evaluate_expression(curr)))
                                    curr = []
                                else: curr.append(t)
                            if curr: dims.append(int(self.evaluate_expression(curr)))
                            
                            idx = match_idx + 1
                        
                        # Check for secondary DIM (length for strings)
                        str_len = None
                        if var_type == 'ID_STR' and idx < len(tokens) and tokens[idx].type == 'LPAREN':
                            match_idx = -1
                            count = 0
                            for i in range(idx, len(tokens)):
                                if tokens[i].type == 'LPAREN': count += 1
                                elif tokens[i].type == 'RPAREN':
                                    count -= 1
                                    if count == 0: match_idx = i; break
                            
                            inner = tokens[idx+1:match_idx]
                            str_len = int(self.evaluate_expression(inner))
                            idx = match_idx + 1

                        # Initialize
                        if var_type == 'ID_NUM':
                            # Numeric Array: A(10) -> list of 11 zeros
                            size = dims[0] + 1 if dims else 1
                            self.variables[var_name] = [0] * size
                        else:
                            # String: S$(20) or S$[10](20)
                            if dims:
                                # String Array
                                size = dims[0] + 1
                                length = str_len if str_len else 24
                                self.variables[var_name] = [" " * length] * size
                            else:
                                # Scalar String
                                length = str_len if str_len else 24
                                self.variables[var_name] = " " * length
                    
                    self.current_line_idx += 1
                    
                elif cmd == 'GOTO':
                    try:
                        target = int(float(tokens[1].value))
                        if target in self.line_numbers:
                            self.current_line_idx = self.line_numbers.index(target)
                        else:
                            raise RuntimeError(f"Undefined line number {target}")
                    except ValueError:
                        raise RuntimeError(f"Invalid line number {tokens[1].value}")

                elif cmd == 'GOSUB':
                    try:
                        target = int(float(tokens[1].value))
                        self.stack.append(self.current_line_idx + 1)
                        if target in self.line_numbers:
                            self.current_line_idx = self.line_numbers.index(target)
                        else:
                            raise RuntimeError(f"Undefined line number {target}")
                    except ValueError:
                        raise RuntimeError(f"Invalid line number {tokens[1].value}")

                elif cmd == 'RETURN':
                    if not self.stack:
                        raise RuntimeError("RETURN without GOSUB")
                    self.current_line_idx = self.stack.pop()

                elif cmd == 'IF':
                    # IF [expr] THEN [target]
                    then_idx = -1
                    for i, t in enumerate(tokens):
                        if t.type == 'THEN':
                            then_idx = i
                            break
                    
                    condition_tokens = tokens[1:then_idx]
                    target_tokens = tokens[then_idx+1:]
                    
                    cond_val = False
                    if len(condition_tokens) == 3 and condition_tokens[1].type == 'ASSIGN':
                        left = self.evaluate_expression([condition_tokens[0]])
                        right = self.evaluate_expression([condition_tokens[2]])
                        cond_val = (left == right)
                    else:
                        cond_val = bool(self.evaluate_expression(condition_tokens))

                    if cond_val:
                        if target_tokens[0].type == 'NUMBER':
                            try:
                                target = int(float(target_tokens[0].value))
                                self.current_line_idx = self.line_numbers.index(target)
                            except:
                                self.current_line_idx += 1
                        else:
                            self.current_line_idx += 1
                    else:
                        self.current_line_idx += 1
                
                elif cmd == 'INPUT':
                    prompt = ""
                    var_token = None
                    if tokens[1].type == 'STRING':
                        prompt = tokens[1].value[1:-1]
                        var_token = tokens[3] if len(tokens) > 3 else tokens[1]
                    else:
                        var_token = tokens[1]
                    
                    if self.io_handler:
                        user_input = self.io_handler.input(prompt)
                    else:
                        user_input = input(prompt)

                    if var_token.type == 'ID_NUM':
                        try:
                            self.variables[var_token.value] = float(user_input) if '.' in user_input else int(user_input)
                        except ValueError:
                            self.variables[var_token.value] = 0
                    else:
                        self.variables[var_token.value] = user_input
                    self.current_line_idx += 1

                elif cmd == 'FOR':
                    var_name = tokens[1].value
                    assign_idx = 2
                    to_idx = -1
                    for i, t in enumerate(tokens):
                        if t.type == 'TO':
                            to_idx = i
                            break
                    start_val = self.evaluate_expression(tokens[assign_idx+1:to_idx])
                    step_idx = -1
                    for i, t in enumerate(tokens):
                        if t.type == 'STEP':
                            step_idx = i
                            break
                    if step_idx != -1:
                        end_val = self.evaluate_expression(tokens[to_idx+1:step_idx])
                        step_val = self.evaluate_expression(tokens[step_idx+1:])
                    else:
                        end_val = self.evaluate_expression(tokens[to_idx+1:])
                        step_val = 1
                    self.variables[var_name] = start_val
                    self.for_loops[var_name] = {'end': end_val, 'step': step_val, 'start_line_idx': self.current_line_idx + 1}
                    self.current_line_idx += 1

                elif cmd == 'NEXT':
                    var_name = tokens[1].value
                    if var_name not in self.for_loops: raise RuntimeError(f"NEXT without FOR: {var_name}")
                    loop_info = self.for_loops[var_name]
                    self.variables[var_name] += loop_info['step']
                    if (loop_info['step'] > 0 and self.variables[var_name] <= loop_info['end']) or \
                       (loop_info['step'] < 0 and self.variables[var_name] >= loop_info['end']):
                        self.current_line_idx = loop_info['start_line_idx']
                    else:
                        del self.for_loops[var_name]
                        self.current_line_idx += 1

                elif cmd in ('OPEN', 'CLOSE', 'WRITE', 'READ', 'EXTRACT', 'EXTRACTRECORD', 'ERASE', 'DIRECT', 'INDEXED', 'SERIAL', 'SORT', 'SELECT'):
                    # Shared parsing for file commands
                    options = {}
                    idx = 0
                    
                    if cmd in ('DIRECT', 'INDEXED', 'SERIAL', 'SORT'):
                        # Creation commands: DIRECT "filename", arg1, arg2 [, ERR=line]
                        filename = tokens[1].value[1:-1]
                        idx = 2
                        args = []
                        while idx < len(tokens):
                            t = tokens[idx]
                            if t.type == 'COMMA': idx += 1; continue
                            if t.type == 'ERR':
                                idx += 2; options['ERR'] = tokens[idx].value
                            else:
                                args.append(self.evaluate_expression([t]))
                            idx += 1
                        
                        try:
                            rec_len = args[1] if len(args) > 1 and cmd != 'SERIAL' else (args[0] if args else None)
                            key_len = args[0] if len(args) > 0 and cmd != 'SERIAL' else None
                            self.file_manager.create(filename, cmd, rec_len=rec_len, key_len=key_len)
                            self.current_line_idx += 1
                        except Exception as e:
                            if not self._handle_file_error('ERR', options): raise e

                    elif cmd == 'OPEN':
                        idx = 1
                        chn = 0
                        if tokens[idx].type == 'LPAREN':
                            chn = tokens[idx+1].value
                            idx += 3
                        filename = tokens[idx].value[1:-1]
                        idx += 1
                        file_type = None
                        rec_len = None
                        
                        # Parse options (DIRECT, ERR= etc)
                        while idx < len(tokens):
                            t = tokens[idx]
                            if t.type == 'COMMA': idx += 1; continue
                            if t.type in ('DIRECT', 'INDEXED', 'SERIAL', 'SORT'): file_type = t.type
                            elif t.type == 'ERR':
                                idx += 2; options['ERR'] = tokens[idx].value
                            elif t.type in ('IND', 'KEY'): # Still support for backwards compatibility or specific Thoroughbred syntax
                                idx += 2; rec_len = tokens[idx].value
                            idx += 1
                        
                        try:
                            self.file_manager.open(chn, filename, file_type, rec_len)
                            self.current_line_idx += 1
                        except FileNotFoundError as e:
                            if not self._handle_file_error('ERR', options):
                                print(f"Runtime Error at line {line_num}: {e}")
                                break # Stop execution if no ERR= handling
                        except Exception as e:
                            if not self._handle_file_error('ERR', options): raise e
                    
                    elif cmd == 'CLOSE':
                        self.file_manager.close(tokens[2].value)
                        self.current_line_idx += 1

                    elif cmd in ('WRITE', 'READ', 'EXTRACT', 'EXTRACTRECORD'):
                        chn = tokens[2].value
                        idx = 3
                        key, ind = None, None
                        
                        while idx < len(tokens) and tokens[idx].type != 'RPAREN':
                            t = tokens[idx]
                            if t.type in ('IND', 'KEY', 'ERR', 'DOM'):
                                opt_type = t.type
                                idx += 2
                                val = self.evaluate_expression([tokens[idx]])
                                if opt_type == 'IND': ind = val
                                elif opt_type == 'KEY': key = val
                                else: options[opt_type] = val
                            idx += 1
                        
                        if idx < len(tokens) and tokens[idx].type == 'RPAREN': idx += 1
                        if idx < len(tokens) and tokens[idx].type == 'COMMA': idx += 1

                        jumped = False
                        try:
                            if cmd == 'WRITE':
                                values = []
                                current_expr = []
                                while idx < len(tokens):
                                    if tokens[idx].type == 'COMMA':
                                        if current_expr: values.append(self.evaluate_expression(current_expr)); current_expr = []
                                    else: current_expr.append(tokens[idx])
                                    idx += 1
                                if current_expr: values.append(self.evaluate_expression(current_expr))
                                
                                if key is not None or ind is not None:
                                    existing = self.file_manager.read(chn, key=key, ind=ind)
                                    if existing is not None and 'DOM' in options:
                                        if self._handle_file_error('DOM', options): jumped = True
                                
                                if not jumped:
                                    self.file_manager.write(chn, key=key, ind=ind, values=values)
                            
                            elif cmd in ('READ', 'EXTRACT', 'EXTRACTRECORD'):
                                if cmd in ('EXTRACT', 'EXTRACTRECORD'):
                                    data = self.file_manager.extract(chn, key=key, ind=ind)
                                else:
                                    data = self.file_manager.read(chn, key=key, ind=ind)
                                
                                if data is None:
                                    if self._handle_file_error('DOM', options): jumped = True
                                    else: raise RuntimeError(f"Record not found on channel {chn}")
                                
                                if not jumped:
                                    if cmd == 'EXTRACTRECORD':
                                        var_tok = tokens[idx]
                                        self.variables[var_tok.value] = "|".join(map(str, data))
                                    else:
                                        var_idx = 0
                                        while idx < len(tokens):
                                            t = tokens[idx]
                                            if t.type in ('ID_NUM', 'ID_STR'):
                                                if var_idx < len(data): self.variables[t.value] = data[var_idx]
                                                var_idx += 1
                                            idx += 1
                            
                            if not jumped:
                                self.current_line_idx += 1
                        except Exception as e:
                            if not self._handle_file_error('ERR', options): raise e

                    elif cmd == 'ERASE':
                        filename = tokens[1].value[1:-1]
                        idx = 2
                        while idx < len(tokens):
                            if tokens[idx].type == 'ERR':
                                idx += 2; options['ERR'] = tokens[idx].value
                            idx += 1
                        try:
                            self.file_manager.erase(filename)
                            self.current_line_idx += 1
                        except:
                            if not self._handle_file_error('ERR', options): raise

                    elif cmd == 'SELECT':
                        # SELECT (chn) "pattern" [, ERR=line]
                        idx = 1
                        chn = 0
                        if idx < len(tokens) and tokens[idx].type == 'LPAREN':
                            chn = tokens[idx+1].value
                            idx += 3
                        
                        pattern = tokens[idx].value[1:-1] if idx < len(tokens) and tokens[idx].type == 'STRING' else "*"
                        idx += 1
                        
                        while idx < len(tokens):
                            if tokens[idx].type == 'ERR':
                                idx += 2; options['ERR'] = tokens[idx].value
                            idx += 1
                        
                        try:
                            # Implementation of SELECT: list files in basic_storage
                            files = [f.replace('.json', '') for f in os.listdir(self.file_manager.storage_dir) if f.endswith('.json')]
                            if pattern != "*":
                                import fnmatch
                                files = fnmatch.filter(files, pattern)
                            
                            # Create a virtual "SERIAL" file with the file list
                            path = self.file_manager._get_path(f"_SELECT_{chn}")
                            file_content = {
                                "_metadata": {"type": "SERIAL", "rec_len": 128, "key_len": None},
                                "records": {str(i): [f] for i, f in enumerate(sorted(files))}
                            }
                            # We don't actually save this to disk, or maybe we do temporarily?
                            # Thoroughbred SELECT creates a list that can be READ.
                            # Let's just mock it in FileManager as an open channel.
                            self.file_manager.channels[chn] = {
                                'type': 'SERIAL',
                                'filename': f"_SELECT_{chn}",
                                'data': file_content["records"],
                                'metadata': file_content["_metadata"],
                                'pos': 0
                            }
                            self.current_line_idx += 1
                        except Exception as e:
                            if not self._handle_file_error('ERR', options): raise e

                elif cmd == 'CALL':
                    # CALL prog$, [ERR=line], args...
                    idx = 1
                    prog_tokens = []
                    while idx < len(tokens) and tokens[idx].type != 'COMMA':
                        prog_tokens.append(tokens[idx])
                        idx += 1
                    
                    prog_name = self.evaluate_expression(prog_tokens)
                    if idx < len(tokens) and tokens[idx].type == 'COMMA': idx += 1
                    
                    options = {}
                    args = [] # list of {value, var_name, is_all}
                    
                    while idx < len(tokens):
                        if tokens[idx].type == 'COMMA': idx += 1; continue
                        if tokens[idx].type == 'ERR':
                            idx += 2; options['ERR'] = tokens[idx].value
                            idx += 1
                        else:
                            # Parse arg
                            arg_tokens = []
                            expr_tokens = []
                            is_all = False
                            while idx < len(tokens) and tokens[idx].type != 'COMMA':
                                if tokens[idx].type == 'ALL': 
                                    is_all = True
                                else: 
                                    expr_tokens.append(tokens[idx])
                                arg_tokens.append(tokens[idx]) # Keep for variable check
                                idx += 1
                            
                            # If is_all, the expression is just the ID before the [ALL]
                            if is_all:
                                # A[ALL] -> expr is just [A]
                                id_tokens = [t for t in expr_tokens if t.type in ('ID_NUM', 'ID_STR', 'LBRACKET', 'RBRACKET')]
                                # Filter out brackets to get the base variable
                                eval_tokens = [t for t in id_tokens if t.type not in ('LBRACKET', 'RBRACKET')]
                                val = self.evaluate_expression(eval_tokens)
                            else:
                                val = self.evaluate_expression(expr_tokens)
                            
                            # Identify if it was a variable reference
                            var_name = None
                            if expr_tokens and expr_tokens[0].type in ('ID_NUM', 'ID_STR'):
                                if len(expr_tokens) == 1:
                                    var_name = expr_tokens[0].value
                                elif is_all:
                                    var_name = expr_tokens[0].value

                            args.append({'value': val, 'var_name': var_name, 'is_all': is_all})
                    
                    # Search for program
                    # Search for program
                    filename = prog_name + ".bas"
                    if not os.path.exists(filename):
                        # Try tests directory
                        test_filename = os.path.join("tests", filename)
                        if os.path.exists(test_filename):
                            filename = test_filename
                        elif not self._handle_file_error('ERR', options):
                            raise RuntimeError(f"ERR=12: Program not found: {filename}")
                        else:
                             continue
                    
                    # Load and execute
                    with open(filename, 'r') as f:
                        source = f.read()
                    
                    # Create temporary interpreter to parse
                    temp_int = ThoroughbredBasicInterpreter()
                    temp_int.load_program(source)
                    
                    if len(self.context_stack) >= 127:
                        raise RuntimeError("ERR=127: Maximum CALL nesting exceeded")
                    
                    self._push_context(temp_int.program, temp_int.line_numbers, passed_args=args)
                    continue

                elif cmd == 'ENTER':
                    curr = self._curr()
                    passed = curr['passed_args']
                    idx = 1
                    arg_idx = 0
                    
                    if len(tokens) == 1:
                        if len(self.context_stack) > 1:
                            caller_vars = self.context_stack[-2]['variables']
                            curr['variables'].update(caller_vars)
                            for k in caller_vars:
                                curr['caller_refs'][k] = {'var_name': k, 'is_all': True}
                    else:
                        while idx < len(tokens):
                            if tokens[idx].type == 'COMMA': idx += 1; continue
                            
                            var_name = tokens[idx].value
                            is_all = False
                            idx += 1
                            if idx < len(tokens) and tokens[idx].type == 'LBRACKET':
                                # Skip [ ALL ] or [ idx ]
                                depth = 0
                                for i in range(idx, len(tokens)):
                                    if tokens[i].type == 'LBRACKET': depth += 1
                                    elif tokens[i].type == 'RBRACKET':
                                        depth -= 1
                                        if depth == 0:
                                            # Check if ALL was inside
                                            for t in tokens[idx:i]:
                                                if t.type == 'ALL': is_all = True
                                            idx = i + 1
                                            break
                            
                            if arg_idx < len(passed):
                                arg = passed[arg_idx]
                                curr['variables'][var_name] = arg['value']
                                if arg['var_name']:
                                    curr['caller_refs'][var_name] = {'var_name': arg['var_name'], 'is_all': arg['is_all'] or is_all}
                                arg_idx += 1
                        
                    self.current_line_idx += 1
                
                elif cmd == 'EXIT':
                    if len(self.context_stack) <= 1:
                        break # Top-level EXIT acts like END
                    
                    curr = self.context_stack.pop()
                    caller_refs = curr['caller_refs']
                    caller_ctx = self._curr()
                    
                    # Write back values
                    for local_name, ref in caller_refs.items():
                        if ref['var_name']:
                            val = curr['variables'].get(local_name)
                            caller_ctx['variables'][ref['var_name']] = val
                    
                    self.current_line_idx += 1
                    continue

                elif cmd == 'END':
                    if len(self.context_stack) > 1:
                        # END in sub-program acts like EXIT but maybe without write-back?
                        # Thoroughbred usually suggests EXIT for return. 
                        # Let's follow EXIT logic but maybe END just pops.
                        self.context_stack.pop()
                        self.current_line_idx += 1
                        continue
                        
                    for chn in list(self.file_manager.channels.keys()): self.file_manager.close(chn)
                    break
                    
                else:
                    self.current_line_idx += 1

            except Exception as e:
                # Global error handling (can be expanded)
                print(f"Runtime Error at line {self.line_numbers[self.current_line_idx]}: {e}")
                break

if __name__ == "__main__":
    code = """
    10 LET A = 1
    20 FOR I = 1 TO 5
    30 PRINT "LUS STAP:", I
    40 NEXT I
    50 PRINT "LUS KLAAR"
    60 END
    """
    interpreter = ThoroughbredBasicInterpreter()
    interpreter.load_program(code)
    interpreter.execute()

if __name__ == "__main__":
    code = """
    10 LET A = 100
    20 LET B$ = "HALLO WERELD"
    30 PRINT A
    40 PRINT B$
    50 END
    """
    interpreter = ThoroughbredBasicInterpreter()
    interpreter.load_program(code)
    interpreter.execute()
