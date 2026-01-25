import json
import os
import re
import sys
import math
import random
from datetime import datetime


from file_manager import FileManager
from lexer import Lexer, Token

class ExecutionFinished(Exception): pass
class EscapeInterruption(Exception): pass
class BasicErrorJump(Exception):
    def __init__(self, target): self.target = target

class ThoroughbredBasicInterpreter:
    def __init__(self, io_handler=None):
        self.context_stack = []
        self.file_manager = FileManager()
        self.io_handler = io_handler # Can be None for stdout/stdin fallback
        self.lexer = Lexer()
        
        # Initial context for the main program
        self._push_context({}, [])

        # Trace State
        self.trace_enabled = False
        self.trace_channel = 0
        self.trace_mode = "FULL"
        self.trace_options = set()
        self.trace_delay = 0

        # Error Handling State (SETERR)
        self.seterr_line = 0
        self.seterr_active = False
        self.seterr_saved = 0
        self.retry_index = 0 # Index of the line to retry
        self.last_error_line = None 
        
        # Escape Handling State (SETESC)
        self.setesc_line = 0
        self.escape_trapped = False
        self.escape_return_idx = None

    def reset_state(self):
        """Resets the interpreter to a clean state for a new execution."""
        self.context_stack = []
        self._push_context({'CTL': 0}, [])
        
        # Reset trace state
        self.trace_enabled = False
        self.trace_channel = 0
        self.trace_mode = "FULL"
        self.trace_options = set()
        self.trace_delay = 0

        # Reset error handling state
        self.seterr_line = 0
        self.seterr_active = False
        self.seterr_saved = 0
        self.retry_index = 0
        self.last_error_line = None

        # Reset escape state
        self.setesc_line = 0
        self.escape_trapped = False
        self.escape_return_idx = None

        # Reset files
        for chn in list(self.file_manager.channels.keys()):
            try: self.file_manager.close(chn)
            except: pass

    def signal_escape(self):
        """Signals that the Escape key was pressed."""
        self.escape_trapped = True

    def _check_escape_trap(self):
        """Checks if an escape was trapped and handles branching."""
        if self.escape_trapped and self.setesc_line > 0:
            target = self.setesc_line
            self.escape_trapped = False
            # system variable ERR = 127
            self.variables['ERR'] = 127
            
            # Save return point: current line index
            # The manual says RETURN goes to the statement FOLLOWING the interrupted one.
            # If we trap between statements, we shouldn't have moved current_line_idx yet?
            # Actually, we check at the START of the loop.
            # So current_line_idx is the line that *is about* to be executed.
            # After trap-routine finishes, RETURN should go to the statement FOLLOWING the interrupted one.
            self.escape_return_idx = self.current_line_idx + 1
            self.retry_index = self.current_line_idx
            
            if target in self.line_numbers:
                self.current_line_idx = self.line_numbers.index(target)
                return True
        elif self.escape_trapped:
            # No SETESC handler: default is to stop (like ExecutionFinished or error)
            self.escape_trapped = False
            raise ExecutionFinished()
        return False


    def _push_context(self, program, line_numbers, variables=None, passed_args=None):
        self.context_stack.append({
            'program': program,
            'line_numbers': line_numbers,
            'current_line_idx': 0,
            'variables': variables if variables is not None else {},
            'program_source': {}, # Map line_number -> raw text for LIST
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

    @property
    def program_source(self): return self._curr().get('program_source', {})
    @program_source.setter
    def program_source(self, value): self._curr()['program_source'] = value

    def execute_direct(self, code):
        tokens = list(self.lexer.tokenize(code))
        if tokens:
            self._dispatch_statement(tokens)

    def load_program(self, source_code, reset=True):
        if reset:
            self.reset_state()
        self.program = {}
        self.program_source = {} # line_number -> raw source string
        
        for line in source_code.splitlines():
            if not line.strip():
                continue
            
            tokens = list(self.lexer.tokenize(line))
            if not tokens:
                continue
                
            if tokens[0].type == 'NUMBER':
                line_number = tokens[0].value
                self.program[line_number] = tokens[1:]
                
                # Store cleaned source line (without line number for easier re-assembly?)
                # Or store everything after the number.
                # Let's verify if original line had the number.
                # Simple extraction:
                match = re.match(r'^\s*\d+\s+(.*)', line)
                if match:
                    self.program_source[line_number] = match.group(1)
                else:
                    self.program_source[line_number] = ""
            else:
                # Direct mode not supported in this simple version
                print(f"Skipping line without line number: {line}")
        
        self.line_numbers = sorted(self.program.keys())

    def _get_iolist_items(self, line_number):
        """
        Retrieves the tokens defined in an IOLIST at line_number.
        Returns a list of items to be processed by READ/WRITE/PRINT/INPUT.
        """
        line_number = int(line_number)
        if line_number not in self.program:
            raise RuntimeError(f"IOLIST line {line_number} not found")
            
        tokens = self.program[line_number]
        if not tokens or tokens[0].type != 'IOLIST':
            raise RuntimeError(f"Line {line_number} is not an IOLIST")
            
        # Parse the IOLIST content
        # IOLIST A$, B, C, @(10,20), 'CS', "Literal"
        # We return a list of 'Action Items'
        items = []
        current_idx = 1 # Skip IOLIST keyword
        
        while current_idx < len(tokens):
            t = tokens[current_idx]
            
            if t.type == 'COMMA' or t.type == 'SEMICOLON':
                current_idx += 1
                continue
                
            if t.type in ('ID_NUM', 'ID_STR'):
                # Variable
                items.append({'type': 'VAR', 'token': t})
                current_idx += 1
            elif t.type == 'OP' and t.value == '*':
                # SKIP (*)
                items.append({'type': 'SKIP'})
                current_idx += 1
            elif t.type == 'MNEMONIC':
                items.append({'type': 'MNEMONIC', 'value': t.value[1:-1]})
                current_idx += 1
            elif t.type == 'STRING' or t.type == 'NUMBER':
                # Literal output
                 items.append({'type': 'LITERAL', 'value': t.value})
                 current_idx += 1
            elif t.type == 'AT':
                # Cursor @(col, row)
                try:
                    if current_idx+1 < len(tokens) and tokens[current_idx+1].type == 'LPAREN':
                        # Find matching RPAREN
                        depth = 0
                        paren_end = -1
                        for i in range(current_idx+1, len(tokens)):
                            tk = tokens[i]
                            if tk.type == 'LPAREN': depth +=1
                            elif tk.type == 'RPAREN': 
                                depth -= 1
                                if depth == 0: 
                                    paren_end = i
                                    break
                                    
                        if paren_end != -1:
                            items.append({'type': 'CURSOR', 'tokens': tokens[current_idx:paren_end+1]})
                            current_idx = paren_end + 1
                        else:
                             current_idx += 1
                    else:
                         current_idx += 1
                except:
                     current_idx += 1
            else:
                 current_idx += 1
                 
        return items

    def _find_matching(self, tokens, start_idx, open_type, close_type):
        count = 0
        for i in range(start_idx, len(tokens)):
            if tokens[i].type == open_type: count += 1
            elif tokens[i].type == close_type:
                count -= 1
                if count == 0: return i
        return -1

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

        # 1. Handle built-in functions: POS(...)
        if tokens[0].type == 'POS' and len(tokens) > 2 and tokens[1].type == 'LPAREN':
            close_idx = self._find_matching(tokens, 1, 'LPAREN', 'RPAREN')
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
                    'MOD', 'ROUND', 'FPT', 'IPT',
                    'AND', 'OR', 'NOT', 'XOR', 'DTN',
                                        'ATH', 'HTA', 'MAX', 'MIN', 'NUM', 'KEY', 'BIN', 'DEC', 'FILL', 'SDX'}

        # KEY function logic
        if tokens[0].type == 'KEY' and len(tokens) > 2 and tokens[1].type == 'LPAREN':
            close_idx = self._find_matching(tokens, 1, 'LPAREN', 'RPAREN')
            if close_idx != -1:
                inner = tokens[2:close_idx]
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

                if len(args) == 0: raise RuntimeError("KEY() requires channel")
                
                chn = int(self.evaluate_expression(args[0]))
                
                options = {}
                for arg_toks in args[1:]:
                    if len(arg_toks) >= 3 and arg_toks[1].type == 'ASSIGN':
                         kw = arg_toks[0].value
                         val_expr = arg_toks[2:]
                         val = self.evaluate_expression(val_expr)
                         options[kw] = val
                
                err_line = int(options.get('ERR')) if 'ERR' in options else None
                end_line = int(options.get('END')) if 'END' in options else None

                try:
                    return self.file_manager.get_next_key(chn)
                except EOFError:
                    if end_line: raise BasicErrorJump(end_line)
                    if err_line: raise BasicErrorJump(err_line)
                    raise RuntimeError("End of file (ERR=2)")
                except Exception as e:
                    msg = str(e)
                    code = 13 if "Channel" in msg or "Invalid" in msg else 0
                    if err_line: raise BasicErrorJump(err_line)
                    raise RuntimeError(f"{msg} (ERR={code})")
        
        if tokens[0].type in builtins and len(tokens) > 2 and tokens[1].type == 'LPAREN':
            close_idx = self._find_matching(tokens, 1, 'LPAREN', 'RPAREN')
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
                elif func == 'FILL':
                    count = int(val1)
                    char = str(eval_arg(1) or "\0")
                    if len(char) > 0:
                        # If char is a digit, it might be an ASCII code?
                        # Thoroughbred FILL(10, "A") fills with A.
                        # FILL(10, 0) fills with CHR(0).
                        # Let's try to handle both.
                        try:
                            # If it's a numeric value passed as a string/float
                            c_int = int(float(char))
                            return chr(c_int & 0xFF) * count
                        except:
                            return char[0] * count
                    return "\0" * count
                elif func == 'CVS':
                    s = str(val1)
                    code = int(eval_arg(1) or 0)
                    if code & 1: s = s.lstrip()
                    if code & 2: s = s.rstrip()
                    if code & 16: s = s.upper()
                    if code & 32: s = s.lower()
                    return s

                elif func == 'SDX':
                    try:
                        # Handle ERR/ERC options
                        err_line = None
                        for i in range(1, len(args)):
                            arg_toks = args[i]
                            if len(arg_toks) >= 3 and arg_toks[1].type == 'ASSIGN' and arg_toks[1].value == '=':
                                if arg_toks[0].type == 'ERR':
                                    err_line = int(self.evaluate_expression(arg_toks[2:]))

                        s = str(val1).upper()
                        if not s: raise ValueError("Empty string for SDX")

                        # Soundex mapping
                        mapping = {
                            'B': '1', 'F': '1', 'P': '1', 'V': '1',
                            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
                            'D': '3', 'T': '3',
                            'L': '4',
                            'M': '5', 'N': '5',
                            'R': '6'
                        }
                        
                        # 1. Find the first alphanumeric character
                        first_char = ""
                        for char in s:
                            if char.isalnum():
                                first_char = char
                                break
                        if not first_char: return "    "
                        
                        # 2. Build the codes
                        res = [first_char]
                        prev_code = mapping.get(first_char, "0")
                        
                        # Skip characters until we have 3 digits
                        for char in s[s.find(first_char)+1:]:
                            if len(res) >= 4: break
                            
                            code = mapping.get(char)
                            if code:
                                if code != prev_code:
                                    res.append(code)
                                    prev_code = code
                                else:
                                    # Same code as previous literal character?
                                    # Rule: If two letters with same code are adjacent, only first is retained.
                                    # If they are separated by A,E,I,O,U,Y, both are used.
                                    # If they are separated by H,W, only first is used.
                                    # This is complex. Standard Soundex usually ignores H/W separation effect.
                                    # Let's follow the standard rule where adjacency means "consecutive characters in source".
                                    pass 
                            elif char in "HW":
                                # H and W are ignored but prevent adjacency merge? 
                                # No, they are usually skipped entirely in modern Soundex.
                                # But some versions say they DON'T separate.
                                pass
                            else:
                                # Vowels/Others: reset prev_code so next same-code letter is included
                                prev_code = "0"
                        
                        # Padding
                        while len(res) < 4: res.append("0")
                        return "".join(res[:4])
                        
                    except Exception as e:
                        if 'err_line' in locals() and err_line: raise BasicErrorJump(err_line)
                        raise e

                # Bitwise String Functions
                elif func in ('AND', 'OR', 'XOR', 'NOT'):
                    s1 = str(val1)
                    if func == 'NOT':
                        # Bitwise NOT on each char (0-255 range usually)
                        return "".join(chr(~ord(c) & 0xFF) for c in s1)
                    else:
                        s2 = str(eval_arg(1) or "")
                        # Apply to min length? Or assume same length?
                        # Thoroughbred usually does bitwise ops on corresponding chars.
                        # If sizes differ, usually stops at shortest? Or pads?
                        # Let's assume min length to be safe.
                        length = min(len(s1), len(s2))
                        res = []
                        for i in range(length):
                            c1 = ord(s1[i])
                            c2 = ord(s2[i])
                            if func == 'AND': r = c1 & c2
                            elif func == 'OR':  r = c1 | c2
                            elif func == 'XOR': r = c1 ^ c2
                            res.append(chr(r))
                        return "".join(res)

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
                elif func == 'DTN':
                    try:
                        v = str(val1)
                        m = str(eval_arg(1)) if len(args) > 1 else "DD-MON-YYYY HH:MI:SS"
                        return self._calculate_dtn(v, m)
                    except: return 0.0
                elif func == 'ATH':
                    # ASCII to Hex (creates string where bytes are hex values)
                    s = str(val1)
                    if len(s) % 2 != 0: s = '0' + s
                    try: return bytes.fromhex(s).decode('latin1')
                    except: return "" # ERR=26 logic needed eventually
                elif func == 'HTA':
                    # Hex to ASCII (returns hex string of input bytes)
                    s = str(val1)
                    return s.encode('latin1').hex().upper()
                elif func == 'BIN':
                    # BIN(numeric-value, result-length [,ERR=line-ref|,ERC=error-code])
                    # numeric-value is an integer
                    # result-length is 1 to 32600
                    
                    try:
                        # Check if first arg is numeric and integer
                        if not isinstance(val1, (int, float)):
                            raise ValueError("ERR=26: Numeric value required")
                        
                        if isinstance(val1, float) and not val1.is_integer():
                            raise ValueError("ERR=26: Integer required")
                        
                        num = int(val1)
                        length = int(eval_arg(1))
                        
                        # Parse options (ERR, ERC)
                        err_line = None
                        erc_code = None
                        for i in range(2, len(args)):
                            arg_tokens = args[i]
                            if len(arg_tokens) >= 3 and arg_tokens[1].type == 'ASSIGN' and arg_tokens[1].value == '=':
                                kw = arg_tokens[0].type
                                val = self.evaluate_expression(arg_tokens[2:])
                                if kw == 'ERR': err_line = int(val)
                                elif kw == 'ERC': erc_code = int(val)
                        
                        try:
                            # Convert to binary
                            # Use unsigned for positive values to allow e.g. BIN(193, 1)
                            # Use signed for negative values for two's complement.
                            if num >= 0:
                                res_bytes = num.to_bytes(length, byteorder='big', signed=False)
                            else:
                                res_bytes = num.to_bytes(length, byteorder='big', signed=True)
                            return res_bytes.decode('latin1')
                        except OverflowError:
                            # If result-length is too small
                            if err_line is not None: raise BasicErrorJump(err_line)
                            raise RuntimeError(f"ERR=26: Value {num} does not fit in {length} bytes")
                        except Exception as e:
                            if err_line is not None: raise BasicErrorJump(err_line)
                            raise e

                    except Exception as e:
                        # Handle ERR=26 or others
                        # Refined error handling: search for ERR= in args if not already found
                        # (But we already parsed it above for the main logic)
                        
                        # Re-parse if needed if exception happened before loop
                        err_line = None
                        for i in range(1, len(args)): # Check all args for ERR=
                            arg_tokens = args[i]
                            if len(arg_tokens) >= 3 and arg_tokens[1].type == 'ASSIGN' and arg_tokens[1].value == '=':
                                if arg_tokens[0].type == 'ERR':
                                    try: err_line = int(self.evaluate_expression(arg_tokens[2:]))
                                    except: pass
                        
                        if err_line is not None:
                            raise BasicErrorJump(err_line)
                        
                        # Default error code for BIN is often 26 for non-integers
                        if "Integer" in str(e) or "Numeric" in str(e):
                            raise RuntimeError("ERR=26: Invalid parameter")
                        raise e
                elif func == 'DEC':
                    # DEC (string-value [,ERR=line-ref|,ERC=error-code])
                    try:
                        if not isinstance(val1, str):
                            raise ValueError("String required")
                        
                        data = val1.encode('latin1')
                        if not data:
                            return 0
                        
                        # int.from_bytes with signed=True handles the leftmost bit as sign bit in two's complement.
                        return int.from_bytes(data, byteorder='big', signed=True)
                    except Exception as e:
                        # Handle ERR=
                        err_line = None
                        for i in range(1, len(args)):
                            arg_tokens = args[i]
                            if len(arg_tokens) >= 3 and arg_tokens[1].type == 'ASSIGN' and arg_tokens[1].value == '=':
                                if arg_tokens[0].type == 'ERR':
                                    try: err_line = int(self.evaluate_expression(arg_tokens[2:]))
                                    except: pass
                        if err_line is not None:
                            raise BasicErrorJump(err_line)
                        raise e
                elif func in ('MAX', 'MIN'):
                    # MAX(v1, v2, ...) / MIN(v1, v2, ...)
                    values = []
                    # Evaluate all arguments
                    for i in range(len(args)):
                        v = eval_arg(i)
                        if v is not None:
                            values.append(v)
                    
                    if not values:
                        return 0
                        
                    # Check for mixed types (str vs numbers) -> convert all to float? Or str?
                    # Python max() fails on mixed types.
                    # Basic usually promotes/converts.
                    # If any is string, treat all as strings?
                    has_str = any(isinstance(x, str) for x in values)
                    if has_str:
                        values = [str(x) for x in values]
                    else:
                        # All numbers?
                        # Ensure all are numbers (int/float)
                        pass 
                        
                    return max(values) if func == 'MAX' else min(values)
                elif func == 'NUM':
                    # NUM(string-value [,ERR=line-ref|,ERC=error-code])
                    # NUM(string-value, NTP=numeric-type [,SIZ=precision] [,ERR=line-ref|,ERC=error-code])
                    
                    # Parse args similar to POS but more flexible for kwargs
                    # 1. First arg is string value
                    str_val = str(eval_arg(0))
                    
                    # 2. Parse remaining args
                    ntp = 0
                    siz = None
                    err_line = None
                    erc_code = 0
                    
                    # Check subsequent args for Assignments (NTP=, SIZ=, ERR=, ERC=)
                    # We need to peek at the tokens of remaining args passed in 'args' list
                    # args[1], args[2] etc are list of tokens.
                    # We need to detect "KEY = VAL" pattern in them.
                    
                    # Wait, eval_arg evaluates the expression. 
                    # If arg is "NTP=6", that is NOT a standard expression if NTP is a keyword.
                    # The Lexer tokenizes "NTP=6" as [NTP, ASSIGN, NUMBER].
                    # eval_arg calls evaluate_expression which normally evaluates this as an assignment? 
                    # No, evaluate_expression expects expressions. "NTP=6" in an expression:
                    # If NTP is variable, it compares NTP = 6 (return 0 or 1).
                    # But here we want named parameters.
                    
                    # We need to inspect the RAW tokens of the arguments, not just evaluate them blindly.
                    # 'args' variable contains lists of tokens for each argument.
                    
                    for i in range(1, len(args)):
                        arg_tokens = args[i]
                        # Check format: KEY (=) VAL
                        if len(arg_tokens) >= 3 and arg_tokens[1].type == 'ASSIGN' and arg_tokens[1].value == '=':
                            key = arg_tokens[0].type
                            val_tokens = arg_tokens[2:]
                            val = self.evaluate_expression(val_tokens)
                            
                            if key == 'NTP': ntp = int(val)
                            elif key == 'SIZ': siz = float(val) # SIZ is .01 to .15
                            elif key == 'ERR': err_line = int(val)
                            elif key == 'ERC': erc_code = int(val)
                            # print(f"DEBUG NUM: key={key} val={val} siz={siz}")
                        else:
                            # Positional? NUM only has one positional arg usually.
                            pass
                            
                    # Perform Conversion
                    try:
                        # NTP=0: Fixed point positive/negative (Standard)
                        # Valid: 0-9, leading +, leading -, max one decimal, E, spaces.
                        # Spaces must be stripped? "12 34" -> 1234
                        # "12-", "-", "12.31.88" -> error
                        
                        if ntp == 0:
                            clean_s = str_val.replace(" ", "")
                            if not re.match(r'^[+-]?\d*(\.\d*)?([eE][+-]?\d+)?$', clean_s):
                                raise ValueError("Invalid numeric format")
                            if clean_s in ('', '+', '-'): raise ValueError("Empty numeric string")
                            result = float(clean_s)
                            
                        elif ntp in (1, 2):
                             # 1: Fix pos, 2: Fix neg. Checks needed?
                             clean_s = str_val.replace(" ", "")
                             res = float(clean_s)
                             if ntp == 1 and res < 0: raise ValueError("Positive required")
                             if ntp == 2 and res > 0: raise ValueError("Negative required")
                             result = res
                             
                        # Placeholder for binary types
                        elif ntp >= 3:
                             # For now, just simplistic parsing or return 0
                             # In future: implement binary decoding logic
                             # Example: $02182E$, NTP=6 -> 12345 (Packed Decimal?)
                             # For now, just strip $ and parse hex? No, packed decimal is specific.
                             pass
                             # Try basic float fallback
                             result = float(str_val.replace("$", ""))
                             
                        else:
                            result = float(str_val)

                        # Apply SIZ (rounding)
                        if siz is not None:
                             # SIZ=.01 (0 digits), .02 (1 digit)... .15 (14 digits)
                             # Docs says "precision of 0 through 14".
                             # Mapping: .01 -> 0, .02 -> 1, ...
                             prec = int((siz * 100) - 1)
                             if prec >= 0:
                                 result = round(result, prec)

                        return result

                    except Exception as e:
                        # Error handling
                        if err_line is not None:
                             # Trigger Jump!
                             raise BasicErrorJump(err_line)
                        else:
                             # Raise exception so global SETERR or default handler acts
                             raise e

                             



        # 2. Handle single values / atoms (Base case)
        if len(tokens) == 1:
            token = tokens[0]
            if token.type == 'NUMBER' or token.type == 'STRING':
                val = token.value
                if isinstance(val, str) and val.startswith('"'):
                    val = val[1:-1]
                return val
            elif token.type in ('ID_NUM', 'ID_STR', 'ERR'):
                return self.variables.get(token.value, 0 if token.type != 'ID_STR' else "")
            elif token.type == 'MNEMONIC':
                return token.value[1:-1]
            return 0

        # 2. Handle indexing/substrings: ID(idx) or ID[idx] or ID(start, len)
        if tokens[0].type in ('ID_NUM', 'ID_STR') and len(tokens) > 1:
            if tokens[1].type in ('LPAREN', 'LBRACKET'):
                open_type = tokens[1].type
                close_type = 'RPAREN' if open_type == 'LPAREN' else 'RBRACKET'
                match_idx = self._find_matching(tokens[i:], 1, open_type, close_type)
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
                        try:
                            if op_type == '+': return left + right
                            if op_type == '-': return left - right
                        except TypeError as e:
                             raise RuntimeError(f"{e} (left={left} ({type(left)}), right={right} ({type(right)}))")

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
            match_idx = self._find_matching(tokens, 0, tokens[0].type, close_type)
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
                    self.retry_index = self.current_line_idx
                    self.seterr_saved = self.seterr_line
                    self.current_line_idx = self.line_numbers.index(target)
                    return True
            except: pass
        if 'ERR' in options:
            try:
                target = int(float(options['ERR']))
                if target in self.line_numbers:
                    self.retry_index = self.current_line_idx
                    self.seterr_saved = self.seterr_line
                    self.current_line_idx = self.line_numbers.index(target)
                    return True
            except: pass
        return False

    def _handle_runtime_error(self, e):
        """
        Handles runtime errors via SETERR mechanism.
        Returns True if error was handled (branched), False otherwise.
        """
        if self.seterr_active and self.seterr_line > 0:
            target = self.seterr_line
            
            # Save state for RETRY
            self.seterr_saved = self.seterr_line
            self.retry_index = self.current_line_idx
            
            # Disable SETERR (SETERR 0)
            self.seterr_line = 0
            
            # Find target index
            if target in self.line_numbers:
                self.current_line_idx = self.line_numbers.index(target)
                return True
            else:
                # Fallback if SETERR target doesn't exist?
                print(f"Error: SETERR target line {target} not found.")
                return False
        return False

    def execute(self):
        while self.context_stack:
            try:
                # 0. Check for Escape Trap
                if self._check_escape_trap():
                    continue

                # Get current line
                ctx = self._curr()
                if ctx['current_line_idx'] >= len(ctx['line_numbers']):
                    # End of program in this context
                    # Implicit END/EXIT behavior
                    if len(self.context_stack) > 1:
                        # Return from sub-program/CALL
                        self.context_stack.pop()
                        # Update caller's vars if needed (handled in EXIT usually, but implicit return?)
                        # Implicit return usually doesn't write back vars unless EXIT/ENTER logic used?
                        # Let's assume distinct contexts pop back.
                        self.current_line_idx += 1
                        continue
                    else:
                        break # End of main program

                current_line_num = ctx['line_numbers'][ctx['current_line_idx']]
                
                # Trace Logic
                if self.trace_enabled and self.trace_mode == "FULL":
                    is_in_call = len(self.context_stack) > 1
                    is_in_gosub = len(self.stack) > 0
                    
                    should_trace = True
                    if 'SKIPCALLS' in self.trace_options and is_in_call: should_trace = False
                    if 'SKIPGOSUBS' in self.trace_options and is_in_gosub: should_trace = False
                    
                    if should_trace:
                        # Reconstruct basic output
                        src = ctx.get('program_source', {}).get(current_line_num, "")
                        msg = f"-->{current_line_num:05d} {src}"
                        if self.trace_channel == 0:
                            print(msg)
                            if self.trace_delay > 0:
                                import time; time.sleep(self.trace_delay)
                        # TODO: Implement channel output if needed

                tokens = ctx['program'][current_line_num]
                
                if not tokens:
                    self.current_line_idx += 1
                    continue
                
                self._dispatch_statement(tokens)
                
            except ExecutionFinished:
                break
            except (EscapeInterruption, KeyboardInterrupt):
                # Triggered by IO device (Terminal)
                self.signal_escape()
                continue
            except BasicErrorJump as jump:
                # Handle ERR= jump
                if jump.target in self.line_numbers:
                    self.current_line_idx = self.line_numbers.index(jump.target)
                else:
                    print(f"Runtime Error: Jump target {jump.target} not found")
                    break
            except Exception as e:
                # 1. Try SETERR
                if self._handle_runtime_error(e):
                    continue
                
                # 2. Default Error Reporting
                line_str = "?"
                try:
                    if self.context_stack and self.line_numbers and self.current_line_idx < len(self.line_numbers):
                         line_str = str(self.line_numbers[self.current_line_idx])
                except: pass
                print(f"Runtime Error at line {line_str}: {e}")
                break
                break

    def _handle_assignment(self, tokens, var_offset):
        # Determine if it's a simple assignment or indexed/substring
        # LET A = val (offset 1)
        # A = val (offset 0)

        var_name = tokens[var_offset].value
        idx_end = var_offset
        params = []
        open_type = None

        if len(tokens) > var_offset + 1 and tokens[var_offset + 1].type in ('LPAREN', 'LBRACKET'):
            open_type = tokens[var_offset + 1].type
            close_type = 'RPAREN' if open_type == 'LPAREN' else 'RBRACKET'
            # Find matching bracket
            depth = 0
            for i in range(var_offset + 1, len(tokens)):
                if tokens[i].type == open_type: depth += 1
                elif tokens[i].type == close_type:
                    depth -= 1
                    if depth == 0:
                        idx_end = i
                        # Parse params
                        inner = tokens[var_offset + 2:i]
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
        
        if assign_idx == -1:
            # Not an assignment? Maybe syntax error or procedure call without CALL?
            # For now ignore or raise
             raise RuntimeError("Syntax error: missing '=' in assignment")

        val = self.evaluate_expression(tokens[assign_idx+1:])

        if open_type is None:
            # Simple LET A = val
            self.variables[var_name] = val
        else:
            var_val = self.variables.get(var_name)
            if open_type == 'LPAREN':
                if tokens[var_offset].type == 'ID_NUM':
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

    def _dispatch_statement(self, tokens):
        if self.trace_enabled and self.trace_mode == "PARTIAL":
            is_in_call = len(self.context_stack) > 1
            is_in_gosub = len(self.stack) > 0
            should_trace = True
            if 'SKIPCALLS' in self.trace_options and is_in_call: should_trace = False
            if 'SKIPGOSUBS' in self.trace_options and is_in_gosub: should_trace = False


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
            self._handle_assignment(tokens, 1)

        elif cmd == 'ON':
            # ON numeric-value GOTO/GOSUB line-ref0 [, line-ref1 ...]
            branch_idx = -1
            branch_type = None
            for i, t in enumerate(tokens):
                if t.type in ('GOTO', 'GOSUB'):
                    branch_idx = i
                    branch_type = t.type
                    break
            
            if branch_idx == -1:
                raise RuntimeError("Syntax error: ON without GOTO or GOSUB")

            expr_tokens = tokens[1:branch_idx]
            val = int(self.evaluate_expression(expr_tokens))
            
            targets = []
            idx = branch_idx + 1
            current_target = []
            
            while idx < len(tokens):
                t = tokens[idx]
                if t.type == 'COMMA':
                   if current_target:
                       targets.append(int(float(current_target[0].value))) 
                   current_target = []
                else:
                   current_target.append(t)
                idx += 1
            if current_target:
                targets.append(int(float(current_target[0].value)))

            target_idx = val
            if target_idx < 0: target_idx = 0
            if target_idx >= len(targets): target_idx = len(targets) - 1
            
            target_line = targets[target_idx]
            
            if target_line in self.line_numbers:
                if branch_type == 'GOSUB':
                    self.stack.append(self.current_line_idx + 1)
                
                self.current_line_idx = self.line_numbers.index(target_line)
            else:
                 raise RuntimeError(f"Undefined line number {target_line}")

        elif cmd in ('ID_NUM', 'ID_STR'):
            self._handle_assignment(tokens, 0)

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
            if self.escape_return_idx is not None:
                # Returning from a SETESC trap
                self.current_line_idx = self.escape_return_idx
                self.escape_return_idx = None
                return

            if not self.stack:
                raise RuntimeError("RETURN without GOSUB")
            self.current_line_idx = self.stack.pop()
            
        elif cmd == 'RETRY':
            # Restore SETERR state
            if self.seterr_saved > 0:
                self.seterr_line = self.seterr_saved
                self.seterr_active = True
                self.seterr_saved = 0
            
            # Jump to retry index
            if 0 <= self.retry_index < len(self.line_numbers):
                self.current_line_idx = self.retry_index
                return # Skip += 1
            
            self.current_line_idx += 1

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
            # Find comparison operator in condition tokens
            # Simple case: expr OP expr
            # We scan for RELOP or ASSIGN at top level (depth 0)
            op_idx = -1
            op_type = None
            depth = 0
            for i, t in enumerate(condition_tokens):
                if t.type in ('LPAREN', 'LBRACKET'): depth += 1
                elif t.type in ('RPAREN', 'RBRACKET'): depth -= 1
                elif depth == 0 and (t.type == 'RELOP' or t.type == 'ASSIGN'):
                    op_idx = i
                    op_type = t.value
                    break
            
            if op_idx != -1:
                left = self.evaluate_expression(condition_tokens[:op_idx])
                right = self.evaluate_expression(condition_tokens[op_idx+1:])
                if op_type == '=': cond_val = (left == right)
                elif op_type == '<': cond_val = (left < right)
                elif op_type == '>': cond_val = (left > right)
                elif op_type == '<=': cond_val = (left <= right)
                elif op_type == '>=': cond_val = (left >= right)
                elif op_type == '<>' or op_type == '!=': cond_val = (left != right)
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
                    # Execute as statement
                    self._dispatch_statement(target_tokens)
                    # _dispatch_statement incremented current_line_idx, but IF logic 
                    # also increments it later? Wait, _dispatch_statement increments 
                    # except for GOTO.
                    # Actually, we should NOT increment again if we dispatched.
                    return 
            else:
                self.current_line_idx += 1


        elif cmd == 'INPUT':
            # Robust INPUT parsing: support mnemonics, @(c,r), prompts, and MULTIPLE variables.
            # Syntax: INPUT [@(c,r),] [mnemonic,] ["Prompt",] [vars...]
            current_idx = 1
            
            # 1. Cursor addressing at strict start
            if current_idx < len(tokens) and tokens[current_idx].type == 'AT':
                try:
                    if tokens[current_idx+1].type == 'LPAREN':
                        match = self._find_matching(tokens, current_idx+1, 'LPAREN', 'RPAREN')
                        if match != -1:
                            inside = tokens[current_idx+2:match]
                            parts = []
                            curr = []
                            d = 0
                            for t in inside:
                                if t.type in ('LPAREN', 'LBRACKET'): d+=1
                                elif t.type in ('RPAREN', 'RBRACKET'): d-=1
                                if d==0 and t.type == 'COMMA':
                                    parts.append(curr); curr = []
                                else: curr.append(t)
                            if curr: parts.append(curr)
                            if len(parts) >= 2:
                                col = int(self.evaluate_expression(parts[0]))
                                row = int(self.evaluate_expression(parts[1]))
                                if self.io_handler: self.io_handler.move_cursor(col, row)
                            current_idx = match + 1
                except: pass

            # 2. Split remainder by COMMA
            remaining = tokens[current_idx:]
            args = []
            curr = []
            d = 0
            for t in remaining:
                if t.type in ('LPAREN', 'LBRACKET'): d += 1
                elif t.type in ('RPAREN', 'RBRACKET'): d -= 1
                if d == 0 and t.type == 'COMMA':
                    if curr: args.append(curr)
                    curr = []
                else:
                    curr.append(t)
            if curr: args.append(curr)

            prompt_parts = []
            target_vars = []

            for arg_toks in args:
                if not arg_toks: continue
                t0 = arg_toks[0]
                if t0.type == 'MNEMONIC' and len(arg_toks) == 1:
                    mnemonic = t0.value[1:-1]
                    if self.io_handler:
                        if prompt_parts:
                            self.io_handler.write(" ".join(prompt_parts))
                            prompt_parts = []
                        
                        if mnemonic == 'CS': self.io_handler.clear_screen()
                        elif mnemonic == 'BR': self.io_handler.set_reverse(True)
                        elif mnemonic == 'ER': self.io_handler.set_reverse(False)
                        elif mnemonic == 'BU': self.io_handler.set_underline(True)
                        elif mnemonic == 'EU': self.io_handler.set_underline(False)
                        elif mnemonic == 'VT': self.io_handler.move_relative(0, -1)
                        elif mnemonic == 'LF': self.io_handler.move_relative(0, 1)
                        elif mnemonic == 'BS': self.io_handler.move_relative(-1, 0)
                        elif mnemonic == 'CH': self.io_handler.move_cursor(0, 0)
                        elif mnemonic == 'CE': self.io_handler.clear_eos()
                        elif mnemonic == 'CL': self.io_handler.clear_eol()
                        elif mnemonic == 'LD': self.io_handler.delete_line()
                elif len(arg_toks) == 1 and arg_toks[0].type in ('ID_NUM', 'ID_STR'):
                    target_vars.append(arg_toks[0])
                else:
                    val = self.evaluate_expression(arg_toks)
                    prompt_parts.append(str(val))

            final_prompt = " ".join(prompt_parts)
            
            for i, var_token in enumerate(target_vars):
                p = final_prompt if i == 0 else ""
                if self.io_handler:
                    res = self.io_handler.input(p)
                    # Support both (text, ctl) and simple text
                    if isinstance(res, tuple):
                        user_input, ctl = res
                    else:
                        user_input, ctl = res, 0
                else:
                    user_input, ctl = input(p), 0
                
                self.variables['CTL'] = ctl
                
                # If only CTL key pressed (ctl != 0 and user_input empty), no data assigned?
                # Manual says: "If the only key pressed... is a CTL-generating key no data is returned"
                # This implies we skip assignment or assign empty/default?
                # "only the appropriate value in CTL."
                # If we don't assign, what happens to the variable? It keeps old value?
                # Usually INPUT overwrites. Let's assume it assigns existing buffer (empty).
                
                if var_token.type == 'ID_NUM':
                    try:
                        self.variables[var_token.value] = float(user_input) if '.' in user_input else int(user_input)
                    except:
                        self.variables[var_token.value] = 0
                else:
                    self.variables[var_token.value] = user_input
                final_prompt = "" 
            
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

        elif cmd in ('OPEN', 'CLOSE', 'WRITE', 'READ', 'EXTRACT', 'EXTRACTRECORD', 'ERASE', 'DIRECT', 'INDEXED', 'SERIAL', 'SORT', 'SELECT', 'REMOVE', 'FIND', 'FINDRECORD', 'READRECORD'):
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
                    # Determine args based on command type
                    key_len = None
                    rec_len = None
                    disk_num = None
                    
                    if cmd == 'SERIAL':
                        if len(args) > 0: rec_len = args[0]
                        if len(args) > 1: disk_num = args[1]
                        # args[2] sector ignored
                    else:
                        if len(args) > 0: key_len = args[0]
                        if len(args) > 1: rec_len = args[1]
                        if len(args) > 2: disk_num = args[2]
                        # args[3] sector ignored

                    self.file_manager.create(filename, cmd, rec_len=rec_len, key_len=key_len, disk_num=disk_num)
                    self.current_line_idx += 1
                except Exception as e:
                    if not self._handle_file_error('ERR', options): raise e

            elif cmd in ('OPEN', 'READ', 'WRITE', 'CLOSE', 'EXTRACT', 'EXTRACTRECORD', 'FIND', 'REMOVE', 'INPUT', 'FINDRECORD', 'READRECORD'):
                # 1. Parse RECORD variation
                idx = 1
                if cmd in ('READ', 'FIND', 'EXTRACT') and idx < len(tokens) and tokens[idx].type == 'RECORD':
                    cmd = cmd + 'RECORD'
                    idx += 1

                # 2. Parse Channel (if present)
                channel = 0
                if idx < len(tokens) and tokens[idx].type == 'LPAREN':
                    channel = int(tokens[idx+1].value)
                    idx += 3

                # 2. Parse Filename (for OPEN/ERASE-like context, though ERASE is separate)
                filename = None
                file_type = None
                rec_len = None
                
                if cmd == 'OPEN':
                     if idx < len(tokens) and tokens[idx].type == 'STRING':
                         filename = tokens[idx].value[1:-1]
                         idx += 1
                
                # 3. Parse Options and Arguments
                options = {}
                args = [] # list of {value, var_name, is_all, is_skip}
                
                # Helper: Extract comma-separated raw args first
                raw_args = []
                current_arg = []
                depth = 0
                
                while idx < len(tokens):
                    t = tokens[idx]
                    if t.type in ('LPAREN', 'LBRACKET'): depth += 1
                    elif t.type in ('RPAREN', 'RBRACKET'): 
                        depth -= 1
                        if depth < 0:
                            # Closing paren of Channel Spec (or mismatched)
                            # Flush current arg if any
                            if current_arg: raw_args.append(current_arg)
                            current_arg = []
                            depth = 0
                            idx += 1
                            continue

                    if depth == 0 and t.type == 'COMMA':
                        if current_arg: raw_args.append(current_arg)
                        current_arg = []
                    else:
                        current_arg.append(t)
                    idx += 1
                if current_arg: raw_args.append(current_arg)
                
                iol_line = None
                
                for r_arg in raw_args:
                    if not r_arg: continue
                    # Check for Assignment: KEY=, IND=, ERR=, IOL=, DOM=
                    if len(r_arg) >= 3 and r_arg[1].type == 'ASSIGN' and r_arg[1].value == '=':
                        kw = r_arg[0].value
                        val = self.evaluate_expression(r_arg[2:])
                        if kw == 'IOL': iol_line = val
                        else: options[kw] = val
                    # Check for options like DIRECT, SORT, etc (single tokens)
                    elif len(r_arg) == 1 and r_arg[0].type in ('DIRECT', 'INDEXED', 'SERIAL', 'SORT'):
                        file_type = r_arg[0].type
                    elif len(r_arg) == 1 and r_arg[0].type == 'OP' and r_arg[0].value == '*':
                        args.append({'is_skip': True}) # SKIP
                    else:
                        # Variable or Value
                        # Identify ALL
                        is_all = False
                        toks = r_arg
                        if toks[0].type == 'ALL':
                            is_all = True
                            toks = toks[1:]
                        
                        var_name = None
                        # Heuristic: if it looks like a variable, store name. 
                        # READ needs name. WRITE evaluates value (unless needed for something else).
                        if len(toks) == 1 and toks[0].type in ('ID_NUM', 'ID_STR'):
                            var_name = toks[0].value
                        
                        # Evaluate value for WRITE/OPEN/etc
                        # For READ with var_name, we don't eval yet? 
                        # Actually we do NOT eval for READ.
                        val = None
                        if cmd not in ('READ', 'EXTRACT', 'EXTRACTRECORD', 'FIND', 'INPUT', 'READRECORD', 'FINDRECORD') or var_name is None:
                             # Try to eval
                             try: val = self.evaluate_expression(toks)
                             except: pass 
                        
                        args.append({'value': val, 'var_name': var_name, 'is_all': is_all, 'tokens': toks})

                # 4. Integrate IOLIST
                if iol_line:
                    iol_items = self._get_iolist_items(iol_line)
                    for item in iol_items:
                        if item['type'] == 'VAR':
                             args.append({'var_name': item['token'].value, 'is_all': False, 'value': None})
                        elif item['type'] == 'SKIP':
                             args.append({'is_skip': True})
                        elif item['type'] == 'LITERAL':
                            # WRITE uses literals. READ ignores.
                            if cmd in ('WRITE', 'PRINT'):
                                 args.append({'value': item['value']})
                        elif item['type'] == 'MNEMONIC':
                            if cmd == 'PRINT': 
                                pass
                        elif item['type'] == 'CURSOR':
                             pass
                
                # 5. EXECUTE COMMAND
                try:
                    jumped = False
                    
                    if cmd == 'OPEN':
                        file_type = file_type or options.get('type') # Helper?
                        rec_len = rec_len or options.get('rec_len') # Logic?
                        # Fallback for old parsing: KEY=10 -> rec_len?
                        # New parser puts IND/KEY in options.
                        # basic.py logic: "elif t.type in ('IND', 'KEY'): idx+=2; rec_len=..."
                        # We need to respect that usage if we see IND/KEY but meant rec_len?
                        # Actually, in OPEN, KEY/IND usually define key length.
                        # Let's use whatever we found.
                        
                        self.file_manager.open(channel, filename, file_type, rec_len)
                        
                    elif cmd == 'CLOSE':
                        self.file_manager.close(channel)
                        
                    elif cmd == 'REMOVE':
                         self.file_manager.remove(channel, key=options.get('KEY'))
                    
                    elif cmd in ('WRITE', 'READ', 'EXTRACT', 'EXTRACTRECORD', 'FIND', 'READRECORD', 'FINDRECORD'):
                        key = options.get('KEY')
                        ind = options.get('IND')
                        
                        if cmd == 'WRITE':
                             values = []
                             for a in args:
                                 if a.get('is_skip'): continue
                                 if a.get('value') is not None: values.append(a['value'])
                                 # What if it was a variable we didn't eval?
                                 elif a.get('var_name'):
                                     values.append(self.variables.get(a['var_name'], ""))
                             
                             # Check DOM
                             if key is not None or ind is not None:
                                 existing = self.file_manager.read(channel, key=key, ind=ind)
                                 if existing is not None and 'DOM' in options:
                                      if self._handle_file_error('DOM', options): jumped = True
                             
                             if not jumped:
                                 self.file_manager.write(channel, key=key, ind=ind, values=values)
                        
                        elif cmd in ('READ', 'EXTRACT', 'EXTRACTRECORD', 'FIND', 'READRECORD', 'FINDRECORD'):
                             # READ / FIND / RECORD
                             update_ptr = True
                             if cmd in ('FIND', 'FINDRECORD'): update_ptr = False

                             if cmd in ('EXTRACT', 'EXTRACTRECORD'):
                                 # Locking logic? Not implemented.
                                 val = self.file_manager.extract(channel, key=key, ind=ind)
                             else:
                                 val = self.file_manager.read(channel, key=key, ind=ind, update_ptr_on_error=update_ptr)

                             # Special case: FIND on SORT file does not transfer data
                             if cmd in ('FIND', 'FINDRECORD'):
                                 try:
                                     if self.file_manager.channels[channel]['type'] == 'SORT':
                                         # Logic: behave as if no variables were passed? Or just don't assign?
                                         # The loop below iterates 'args'. We can empty 'val' or flag to skip assignment.
                                         # But we still need to check for errors (val is None).
                                         if val is not None: val = [] # Clear data so no assignment happens?
                                         # If val is [] (empty list/string), len(val) is 0. var_idx will stay 0.
                                         # Loop will run but "if var_idx < len(val)" will be false.
                                         pass
                                 except: pass
                             
                             if val is None:
                                  if 'DOM' in options:
                                      if self._handle_file_error('DOM', options): jumped = True
                                  if not jumped:
                                      # EOF
                                      if not self._handle_file_error('ERR', options): # ERR=2 usually
                                           raise RuntimeError("End of file or record not found")
                                      jumped = True # Handled via ERR
                             
                             if not jumped and val is not None:
                                 if cmd in ('EXTRACTRECORD', 'READRECORD', 'FINDRECORD'):
                                      # Special single var
                                      if args and args[0].get('var_name'):
                                          self.variables[args[0]['var_name']] = "|".join(map(str, val))
                                 else:
                                     # Distribute values
                                     var_idx = 0
                                     for a in args:
                                         if a.get('is_skip'):
                                             var_idx += 1
                                             continue
                                         if a.get('var_name'):
                                             if var_idx < len(val):
                                                 self.variables[a['var_name']] = val[var_idx]
                                             var_idx += 1

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
            resolved_path = self.file_manager.find_program(prog_name)
            if not resolved_path:
                if not self._handle_file_error('ERR', options):
                    raise RuntimeError(f"ERR=12: Program not found: {prog_name}")
                return

            # Load and execute
            with open(resolved_path, 'r') as f:
                source = f.read()

            # Create temporary interpreter to parse
            temp_int = ThoroughbredBasicInterpreter()
            temp_int.load_program(source)

            if len(self.context_stack) >= 127:
                raise RuntimeError("ERR=127: Maximum CALL nesting exceeded")

            self._push_context(temp_int.program, temp_int.line_numbers, passed_args=args)
            return

        elif cmd == 'EXECUTE':
            # Syntax: EXECUTE string-value [,OPT="LOCAL"]
            expr_tokens = []
            idx = 1
            # Parse string expression
            while idx < len(tokens) and tokens[idx].type != 'COMMA':
                expr_tokens.append(tokens[idx])
                idx += 1

            exec_str_val = str(self.evaluate_expression(expr_tokens))

            opt_local = False
            if idx < len(tokens) and tokens[idx].type == 'COMMA':
                idx += 1
                # Parse OPT="LOCAL"
                # Expect: ID_NUM(OPT) ASSIGN STRING("LOCAL")
                if idx + 2 < len(tokens) and \
                   tokens[idx].type == 'ID_NUM' and tokens[idx].value == 'OPT' and \
                   tokens[idx+1].type == 'ASSIGN' and \
                   tokens[idx+2].type == 'STRING' and tokens[idx+2].value == '"LOCAL"':
                    opt_local = True
                else:
                    # Loose parsing check or error?
                    pass

            # Analyze the string value
            # Does it start with a number?
            match = re.match(r'^\s*(\d+)\s*(.*)', exec_str_val)
            if match:
                # It is a program line: "10 PRINT 'HI'"
                line_num = int(match.group(1))
                line_content = match.group(2)

                # Tokenize the content
                new_tokens = list(self.lexer.tokenize(line_content))

                # Determine context
                # OPT="LOCAL" -> current context (self._curr()['program'])
                # Default -> main running program (self.context_stack[0]['program'])
                target_ctx = self._curr() if opt_local else self.context_stack[0]
                target_prog = target_ctx['program']

                if not line_content.strip():
                    # Deletion: "10" (empty content usually implies delete in simple editors, 
                    # but EXECUTE "10" usually needs content to update, unless empty string implies delete?
                    # Thoroughbred docs say: "inserts the program line". 
                    # If content is empty/rem-only, it replaces. 
                    # If we assume standard basic editing, empty line deletes.
                    # But here we just set it.
                    if line_num in target_prog:
                        del target_prog[line_num]
                        if 'program_source' in target_ctx and line_num in target_ctx['program_source']:
                             del target_ctx['program_source'][line_num]
                else:
                    target_prog[line_num] = new_tokens
                    if 'program_source' in target_ctx:
                         target_ctx['program_source'][line_num] = line_content

                # IMPORTANT: We must update line_numbers list for that context
                target_ctx['line_numbers'] = sorted(target_prog.keys())
                
                # Since we modified program, we just move to next line
                self.current_line_idx += 1
                
            else:
                # Immediate execution: "PRINT 'HI'"
                # "treated as if typed in Console Mode"
                
                exec_tokens = list(self.lexer.tokenize(exec_str_val))
                if exec_tokens:
                    # Recursive dispatch
                    self._dispatch_statement(exec_tokens)
                else:
                    # Empty string -> just move on
                    self.current_line_idx += 1

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


        elif cmd == 'SETERR':
            if len(tokens) > 1:
                t1 = tokens[1]
                val_up = str(t1.value).upper()
                
                if t1.type == 'OFF' or val_up == 'OFF':
                    self.seterr_active = False
                elif t1.type == 'ON' or val_up == 'ON':
                    self.seterr_active = True
                else:
                    # Evaluate target (supports expressions like SETERR 1000 or SETERR Dest)
                    try:
                        val = self.evaluate_expression(tokens[1:])
                        line_num = int(float(val))
                        if line_num == 0:
                            self.seterr_line = 0
                            self.seterr_active = False
                        else:
                            self.seterr_line = line_num
                            self.seterr_active = True
                    except Exception as e:
                        print(f"SETERR Error: {e}")
                        
            self.current_line_idx += 1

        elif cmd == 'SETTRACE':
            chn = 0
            if len(tokens) > 2 and tokens[1].type == 'LPAREN':
                chn = int(tokens[2].value)
            self.trace_enabled = True
            self.trace_channel = chn
            self.current_line_idx += 1

        elif cmd == 'ENDTRACE':
            self.trace_enabled = False
            self.current_line_idx += 1

        elif cmd == 'SETESC':
            try:
                val = self.evaluate_expression(tokens[1:])
                self.setesc_line = int(float(val))
            except:
                self.setesc_line = 0
            self.current_line_idx += 1

        elif cmd == 'SET' and len(tokens) > 1 and tokens[1].type == 'TRACEMODE':
             idx = 2
             arg_tokens = []
             while idx < len(tokens):
                 arg_tokens.append(tokens[idx])
                 idx += 1
             
             mode_str = str(self.evaluate_expression(arg_tokens))
             parts = mode_str.upper().split('|')
             t_mode = "FULL"
             t_opts = set()
             t_delay = 0
             
             for p in parts:
                 p = p.strip()
                 if p in ('F', 'FULL'): t_mode = "FULL"
                 elif p in ('P', 'PARTIAL'): t_mode = "PARTIAL"
                 elif p in ('SC', 'SKIPCALLS'): t_opts.add('SKIPCALLS')
                 elif p in ('SG', 'SKIPGOSUBS'): t_opts.add('SKIPGOSUBS')
                 elif p.startswith('D=') or p.startswith('DELAY='):
                     try: t_delay = float(p.split('=')[1])
                     except: pass
             
             self.trace_mode = t_mode
             self.trace_options = t_opts
             self.trace_delay = t_delay
             self.current_line_idx += 1

        elif cmd == 'RUN':
            # RUN [program-name] [,ERR=line-ref|,ERC=error-code]
            idx = 1
            prog_tokens = []
            while idx < len(tokens) and tokens[idx].type != 'COMMA':
                prog_tokens.append(tokens[idx])
                idx += 1
            
            prog_name = None
            if prog_tokens:
                prog_name = self.evaluate_expression(prog_tokens)
            
            options = {}
            if idx < len(tokens) and tokens[idx].type == 'COMMA':
                idx += 1
                while idx < len(tokens):
                    if tokens[idx].type == 'COMMA': idx += 1; continue
                    if idx + 2 < len(tokens) and tokens[idx+1].value == '=':
                        opt_name = tokens[idx].type
                        opt_val = self.evaluate_expression(tokens[idx+2:])
                        options[opt_name] = opt_val
                        # Skip until next comma or end
                        while idx < len(tokens) and tokens[idx].type != 'COMMA': idx += 1
                    else:
                        idx += 1

            if prog_name:
                # Search for program
                resolved_path = self.file_manager.find_program(prog_name)
                if not resolved_path:
                    if not self._handle_file_error('ERR', options):
                        raise RuntimeError(f"ERR=12: Program not found: {prog_name}")
                    return

                # Load program
                try:
                    with open(resolved_path, 'r') as f:
                        source = f.read()
                    
                    # RESET sequence
                    # 1. Clear context stack (except main) and return stack
                    while len(self.context_stack) > 1:
                        self.context_stack.pop()
                    
                    # 2. Reset the main context (preserve variables)
                    ctx = self._curr()
                    ctx['gosub_stack'] = []
                    ctx['for_loops'] = {}
                    
                    # 3. Reset error/precision state
                    self.seterr_line = 0
                    self.seterr_active = False
                    self.seterr_saved = 0
                    # PRECISION = 2 (standard fallback)
                    
                    self.setesc_line = 0
                    self.escape_trapped = False
                    self.escape_return_idx = None
                    
                    # 4. Parse and load the new program into current context
                    temp_int = ThoroughbredBasicInterpreter()
                    temp_int.load_program(source, reset=False) # Don't reset temp_int's internal context
                    
                    ctx['program'] = temp_int.program
                    ctx['line_numbers'] = temp_int.line_numbers
                    ctx['program_source'] = temp_int.program_source
                    ctx['current_line_idx'] = 0
                    
                    # Execution commences at first line
                    return # execute() will pick up the new ctx
                    
                except Exception as e:
                    if not self._handle_file_error('ERR', options):
                        # Attempting to load a non-basic file might cause errors
                        # TB returns ERR=17 if it's not a program file
                        if isinstance(e, RuntimeError) and "ERR=" not in str(e):
                            raise RuntimeError(f"ERR=17: Invalid program file: {e}")
                        raise e
                    return
            else:
                # RUN without program name:
                # Commences execution at current pointer.
                # If we are in dispatch, we just return and it continues?
                # This usually means starting from the beginning of the CURRENT loaded program.
                if self.line_numbers:
                    self.current_line_idx = 0
                    return # DO NOT increment here, so next iter is also 0

        elif cmd == 'STOP':

            self.trace_enabled = False
            # print("STOP") # Optional
            if len(self.context_stack) > 1: self.context_stack.pop(); self.current_line_idx += 1; return # STOP in sub? usually HALT.
            # STOP forces end of execution usually.
            raise ExecutionFinished()

        elif cmd == 'EXIT':
            if len(self.context_stack) <= 1:
                raise ExecutionFinished() # Top-level EXIT acts like END
            
            curr = self.context_stack.pop()
            caller_refs = curr['caller_refs']
            caller_ctx = self._curr()
            
            # Write back values
            for local_name, ref in caller_refs.items():
                if ref['var_name']:
                    val = curr['variables'].get(local_name)
                    caller_ctx['variables'][ref['var_name']] = val
            
            self.current_line_idx += 1
            return

        elif cmd == 'END':
            self.trace_enabled = False
            if len(self.context_stack) > 1:
                # END in sub-program acts like EXIT but maybe without write-back?
                # Thoroughbred usually suggests EXIT for return. 
                # Let's follow EXIT logic but maybe END just pops.
                self.context_stack.pop()
                self.current_line_idx += 1
                return
                
            for chn in list(self.file_manager.channels.keys()): self.file_manager.close(chn)
            self.setesc_line = 0
            raise ExecutionFinished()

        else:
            self.current_line_idx += 1

    def _calculate_dtn(self, val_str, mask_str):
        # Tokens map (Priority by length)
        tokens = [
             ('YYYY', r'(?P<Y4>[+\-]?\d{4})'), ('YYY', r'(?P<Y3>\d{3})'), ('YY', r'(?P<Y2>\d{2})'),
             ('MONTH', r'(?P<MONTH>[A-Z]+)'), ('Month', r'(?P<Month>[a-zA-Z]+)'), ('MON', r'(?P<MON>[A-Z]{3})'), ('Mon', r'(?P<Mon>[a-zA-Z]{3})'),
             ('MM', r'(?P<M>\d{2})'),
             ('DD', r'(?P<D>\d{2})'),
             ('HH', r'(?P<H>\d{2})'), ('MI', r'(?P<MI>\d{2})'), ('SS', r'(?P<S>\d{2})')
        ]
        
        pattern = re.escape(mask_str)
        for tok, rgx in tokens:
            pattern = pattern.replace(re.escape(tok), rgx)
            
        match = re.match(f'^{pattern}', val_str)
        if not match: return 0.0 # Or raise error
        
        parts = match.groupdict()
        
        y, m, d = 1, 1, 1
        Hr, Mn, Sc = 0, 0, 0
        
        if 'Y4' in parts and parts['Y4']: y = int(parts['Y4'])
        elif 'Y3' in parts and parts['Y3']: y = int(parts['Y3'])
        elif 'Y2' in parts and parts['Y2']:
            y2 = int(parts['Y2'])
            now_y = datetime.now().year
            pivot = now_y % 100
            cent = (now_y // 100) * 100
            if y2 > pivot + 49: y = (cent - 100) + y2
            elif y2 < pivot - 50: y = (cent + 100) + y2
            else: y = cent + y2

        if 'M' in parts and parts['M']: m = int(parts['M'])
        elif 'MON' in parts and parts['MON']:
            abbrs = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
            try: m = abbrs.index(parts['MON'].upper()) + 1
            except: pass
        elif 'MONTH' in parts and parts['MONTH']:
             full = ["JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE","JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"]
             try: m = full.index(parts['MONTH'].upper()) + 1
             except: pass
             
        if 'D' in parts and parts['D']: d = int(parts['D'])
        if 'H' in parts and parts['H']: Hr = int(parts['H'])
        if 'MI' in parts and parts['MI']: Mn = int(parts['MI'])
        if 'S' in parts and parts['S']: Sc = int(parts['S'])
        
        def jdn(Y, M, D):
            return (1461 * (Y + 4800 + (M - 14) // 12)) // 4 + (367 * (M - 2 - 12 * ((M - 14) // 12))) // 12 - (3 * ((Y + 4900 + (M - 14) // 12) // 100)) // 4 + D - 32075

        jd = jdn(y, m, d)
        tf = (Hr * 3600 + Mn * 60 + Sc) / 86400.0
        return float(jd) + tf


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
