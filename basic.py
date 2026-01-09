import sys
import os
from interpreter import ThoroughbredBasicInterpreter, Token

class BasicCLI:
    def __init__(self):
        self.interpreter = ThoroughbredBasicInterpreter()
        self.source_lines = {} # line_number -> raw_text

    def list_program(self, start=None, end=None):
        if not self.source_lines:
            print("Program is empty.")
            return
        
        sorted_keys = sorted(self.source_lines.keys())
        for line_num in sorted_keys:
            if start is not None and line_num < start:
                continue
            if end is not None and line_num > end:
                continue
            print(f"{line_num} {self.source_lines[line_num]}")

    def save_program(self, filename):
        try:
            with open(filename, 'w') as f:
                for line_num in sorted(self.source_lines.keys()):
                    f.write(f"{line_num} {self.source_lines[line_num]}\n")
            print(f"Saved to {filename}")
        except Exception as e:
            print(f"Error saving: {e}")

    def load_program(self, filename):
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return
        try:
            self.source_lines = {}
            with open(filename, 'r') as f:
                for line in f:
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        self.source_lines[int(parts[0])] = parts[1]
            print(f"Loaded {filename}")
        except Exception as e:
            print(f"Error loading: {e}")

    def run_repl(self):
        print("Thoroughbred Basic Interpreter CLI")
        print("Type 'HELP' for commands.")
        
        while True:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue
                
                cmd_upper = user_input.upper()
                
                if cmd_upper == 'EXIT' or cmd_upper == 'BYE':
                    break
                elif cmd_upper.startswith('LIST'):
                    # Handle LIST, LIST 20, LIST 20, , LIST , 20, LIST 20, 30
                    args_str = user_input[4:].strip()
                    if not args_str:
                        self.list_program()
                    else:
                        if ',' in args_str:
                            parts = args_str.split(',')
                            start_str = parts[0].strip()
                            end_str = parts[1].strip() if len(parts) > 1 else ""
                            
                            try:
                                start = int(start_str) if start_str else None
                                end = int(end_str) if end_str else None
                                self.list_program(start=start, end=end)
                            except ValueError:
                                print(f"Invalid LIST range: {args_str}")
                        else:
                            # Single line: LIST 20
                            try:
                                line_num = int(args_str)
                                self.list_program(start=line_num, end=line_num)
                            except ValueError:
                                print(f"Invalid LIST line: {args_str}")
                elif cmd_upper == 'NEW':
                    self.source_lines = {}
                    print("Program cleared.")
                elif cmd_upper.startswith('RUN'):
                    args = user_input[3:].strip()
                    if args:
                        # If filename starts with quotes, strip them
                        filename = args
                        if (filename.startswith('"') and filename.endswith('"')) or \
                           (filename.startswith("'") and filename.endswith("'")):
                            filename = filename[1:-1]
                        self.load_program(filename)
                    
                    if not self.source_lines:
                        # Only print "Nothing to run" if it wasn't just attempting to load
                        if not args:
                            print("Nothing to run.")
                        continue

                    # Reconstruct program for interpreter
                    full_code = "\n".join([f"{num} {text}" for num, text in sorted(self.source_lines.items())])
                    self.interpreter.load_program(full_code)
                    try:
                        self.interpreter.execute()
                    except Exception as e:
                        print(f"Execution Error: {e}")
                elif cmd_upper.startswith('SAVE '):
                    filename = user_input[5:].strip()
                    self.save_program(filename)
                elif cmd_upper.startswith('LOAD '):
                    filename = user_input[5:].strip()
                    self.load_program(filename)
                elif cmd_upper == 'HELP':
                    print("Commands: LIST, RUN [file], NEW, SAVE <file>, LOAD <file>, EXIT")
                    print("Enter code like: 10 PRINT \"HELLO\"")
                elif user_input[0].isdigit():
                    # Line entry: "10 PRINT ..."
                    parts = user_input.split(' ', 1)
                    line_num = int(parts[0])
                    if len(parts) > 1:
                        self.source_lines[line_num] = parts[1]
                    else:
                        # Delete line
                        self.source_lines.pop(line_num, None)
                else:
                    # Direct mode (not fully implemented in interpreter yet, but we can try)
                    # For now, just print an error or try to run as a single-line program
                    print(f"Direct mode not yet supported. Use line numbers.")

            except KeyboardInterrupt:
                print("\nType EXIT to quit.")
            except Exception as e:
                print(f"CLI Error: {e}")

if __name__ == "__main__":
    cli = BasicCLI()
    if len(sys.argv) > 1:
        cli.load_program(sys.argv[1])
        cli.run_repl()
    else:
        cli.run_repl()
