import sys
import os
import threading
import queue
import time
from interpreter import ThoroughbredBasicInterpreter

try:
    import tkinter as tk
    from tkinter import font
    HAS_TK = True
except ImportError:
    HAS_TK = False

class ConsoleIOHandler:
    def write(self, text):
        print(text, end="", flush=True)

    def input(self, prompt=""):
        return input(prompt)

    def move_cursor(self, col, row):
        # ANSI escape codes for cursor positioning
        # \033[<row>;<col>H
        # Note: ANSI is 1-based usually
        print(f"\033[{row+1};{col+1}H", end="", flush=True)

    def clear_screen(self):
        print("\033[2J\033[H", end="", flush=True)

    def set_reverse(self, on):
        code = "7" if on else "27"
        print(f"\033[{code}m", end="", flush=True)

    def set_underline(self, on):
        code = "4" if on else "24"
        print(f"\033[{code}m", end="", flush=True)

    def move_relative(self, dx, dy):
        if dy < 0: print(f"\033[{-dy}A", end="", flush=True) # Up
        if dy > 0: print(f"\033[{dy}B", end="", flush=True)  # Down
        if dx < 0: print(f"\033[{-dx}D", end="", flush=True) # Left
        if dx > 0: print(f"\033[{dx}C", end="", flush=True)  # Right

    def clear_eos(self):
        print("\033[J", end="", flush=True)

    def clear_eol(self):
        print("\033[K", end="", flush=True)

    def delete_line(self):
        print("\033[M", end="", flush=True)

    def shutdown(self):
        sys.exit(0)

class GuiIOHandler:
    def __init__(self, gui):
        self.gui = gui
        self.input_queue = queue.Queue()

    def write(self, text):
        self.gui.write(text)

    def input(self, prompt=""):
        self.write(prompt)
        self.gui.enable_input()
        return self.input_queue.get()

    def move_cursor(self, col, row):
        self.gui.move_cursor(col, row)

    def clear_screen(self):
        self.gui.clear_screen()
        
    def set_reverse(self, on):
        self.gui.set_reverse(on)
        
    def set_underline(self, on):
        self.gui.set_underline(on)
        
    def move_relative(self, dx, dy):
        self.gui.move_relative(dx, dy)
        
    def clear_eos(self):
        self.gui.clear_eos()
        
    def clear_eol(self):
        self.gui.clear_eol()
        
    def delete_line(self):
        self.gui.delete_line()

    def shutdown(self):
        self.gui.shutdown()

class TerminalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Thoroughbred Basic Terminal")
        # Let the text widget determine the size
        self.root.resizable(False, False)
        
        # 80x24 character grid, fixed width font
        self.font = font.Font(family="Courier", size=14)
        # Calculate char width/height roughly or just rely on Text widget sizing
        
        self.text_widget = tk.Text(root, bg="black", fg="#00FF00", 
                                   insertbackground="green", 
                                   font=self.font,
                                   width=80, height=24,
                                   wrap=tk.NONE,
                                   padx=5, pady=5)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        self.text_widget.bind("<Key>", self.on_key)
        self.text_widget.bind("<Return>", self.on_return)
        self.text_widget.bind("<BackSpace>", self.on_backspace)
        
        # Disable mouse positioning to enforce terminal feel, but allow focus
        self.text_widget.bind("<Button-1>", lambda e: self.text_widget.focus_set() or "break")
        
        # Tags for formatting
        self.text_widget.tag_configure('reverse', background="#00FF00", foreground="black") # Inverted
        self.text_widget.tag_configure('underline', underline=1)
        
        self.reverse_mode = False
        self.underline_mode = False
        
        self.input_enabled = False
        self.current_input = []
        self.io_handler = None # Set later

    def set_io_handler(self, handler):
        self.io_handler = handler

    def clear_screen(self):
        self.root.after_idle(self._clear_screen_impl)

    def _clear_screen_impl(self):
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.mark_set(tk.INSERT, '1.0')

    def set_reverse(self, on):
        self.root.after_idle(lambda: setattr(self, 'reverse_mode', on))

    def set_underline(self, on):
        self.root.after_idle(lambda: setattr(self, 'underline_mode', on))

    def move_relative(self, dx, dy):
        self.root.after_idle(self._move_relative_impl, dx, dy)

    def _move_relative_impl(self, dx, dy):
        # simple relative move based on current insert
        current = self.text_widget.index(tk.INSERT)
        row, col = map(int, current.split('.'))
        
        # Approximate relative move
        new_row = max(1, row + dy)
        new_col = max(0, col + dx)
        
        self.text_widget.mark_set(tk.INSERT, f"{new_row}.{new_col}")

    def clear_eos(self):
        self.root.after_idle(lambda: self.text_widget.delete(tk.INSERT, tk.END))

    def clear_eol(self):
        self.root.after_idle(lambda: self.text_widget.delete(tk.INSERT, "insert lineend"))

    def delete_line(self):
        self.root.after_idle(lambda: self.text_widget.delete("insert linestart", "insert lineend + 1c"))

    def write(self, text):
        self.root.after_idle(self._write_impl, text)

    def _write_impl(self, text):
        for char in text:
            if char == '\n':
                # Handle newline: move to start of next line
                current_index = self.text_widget.index(tk.INSERT)
                curr_row, _ = map(int, current_index.split('.'))
                next_row = curr_row + 1
                
                # Ensure next line exists
                current_lines = int(self.text_widget.index('end-1c').split('.')[0])
                if next_row > current_lines:
                    self.text_widget.insert(tk.END, "\n")
                
                self.text_widget.mark_set(tk.INSERT, f"{next_row}.0")
            else:
                # Overwrite character
                # Determine tags
                tags = []
                if getattr(self, 'reverse_mode', False): tags.append('reverse')
                if getattr(self, 'underline_mode', False): tags.append('underline')
                
                # Check if we are at end of line (newline char or end of buffer)
                if self.text_widget.get(tk.INSERT) == '\n':
                     # We are at EOL (before the newline char), so insert
                     self.text_widget.insert(tk.INSERT, char, tuple(tags))
                elif self.text_widget.compare(tk.INSERT, "==", "end-1c"):
                     # At very end of buffer
                     self.text_widget.insert(tk.INSERT, char, tuple(tags))
                else:
                     # Overwrite existing char
                     self.text_widget.delete(tk.INSERT)
                     self.text_widget.insert(tk.INSERT, char, tuple(tags))
        self.text_widget.see(tk.END)

    def move_cursor(self, col, row):
        self.root.after_idle(self._move_cursor_impl, col, row)

    def _move_cursor_impl(self, col, row):
        tk_row = row + 1 # Tkinter lines are 1-based
        tk_col = col     # Tkinter cols are 0-based
        
        # Ensure rows exist
        current_lines = int(self.text_widget.index('end-1c').split('.')[0])
        while current_lines < tk_row:
             self.text_widget.insert(tk.END, "\n")
             current_lines += 1
        
        # Ensure column exists (pad with spaces if necessary)
        # Get line content length
        line_content = self.text_widget.get(f"{tk_row}.0", f"{tk_row}.end")
        if len(line_content) < tk_col:
            padding = " " * (tk_col - len(line_content))
            # Insert padding at end of line (before newline char if it exists)
            self.text_widget.insert(f"{tk_row}.end", padding)
            
        pos = f"{tk_row}.{tk_col}"
        self.text_widget.mark_set(tk.INSERT, pos)

    def enable_input(self):
        # Ensure cursor is at end for input?
        # Standard basic input is always at bottom or current cursor?
        # Usually INPUT prints a prompt via write(), so we are at the right spot.
        # But let's ensure we have focus.
        self.root.after_idle(self._enable_input_impl)

    def _enable_input_impl(self):
        self.input_enabled = True
        self.current_input = []
        self.text_widget.focus_set()
        # Move insertion point to end just in case?
        # No, move_cursor might have placed us somewhere specific for input (e.g. INPUT @(x,y))
        # But standard input is serial.
        pass

    def on_key(self, event):
        if not self.input_enabled:
            return "break"
        if event.char and event.keysym not in ("Return", "BackSpace"):
            self.current_input.append(event.char)
            # Allow default behavior to show char

    def on_backspace(self, event):
        if not self.input_enabled: return "break"
        if self.current_input:
            self.current_input.pop()
            # Allow default

    def on_return(self, event):
        if not self.input_enabled: return "break"
        
        # Send input
        text = "".join(self.current_input)
        self.text_widget.insert(tk.INSERT, "\n")
        self.text_widget.see(tk.END)
        self.input_enabled = False
        self.io_handler.input_queue.put(text)
        return "break"

    def shutdown(self):
        # Schedule window destruction
        self.root.after(100, self.root.destroy)
        # We also need to kill the thread/process eventually, 
        # but destroying root breaks mainloop in main thread, 
        # allowing the program to exit naturally or via daemon thread death.

class BasicCLI:
    def __init__(self, io_handler):
        self.interpreter = ThoroughbredBasicInterpreter(io_handler=io_handler)
        self.io_handler = io_handler
        self.source_lines = {} # line_number -> raw_text

    def print(self, text):
        self.io_handler.write(text + "\n")

    def input(self, prompt):
        return self.io_handler.input(prompt)

    def list_program(self, start=None, end=None):
        if not self.source_lines:
            self.print("Program is empty.")
            return
        
        sorted_keys = sorted(self.source_lines.keys())
        for line_num in sorted_keys:
            if start is not None and line_num < start:
                continue
            if end is not None and line_num > end:
                continue
            self.print(f"{line_num} {self.source_lines[line_num]}")

    def save_program(self, filename):
        try:
            with open(filename, 'w') as f:
                for line_num in sorted(self.source_lines.keys()):
                    f.write(f"{line_num} {self.source_lines[line_num]}\n")
            self.print(f"Saved to {filename}")
        except Exception as e:
            self.print(f"Error saving: {e}")

    def load_program(self, filename):
        resolved_path = self.interpreter.file_manager.find_program(filename)
        if not resolved_path:
            self.print(f"File not found: {filename}")
            return
        try:
            self.source_lines = {}
            with open(resolved_path, 'r') as f:
                for line in f:
                    parts = line.strip().split(' ', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        self.source_lines[int(parts[0])] = parts[1]
            self.print(f"Loaded {resolved_path}")
        except Exception as e:
            self.print(f"Error loading: {e}")

    def do_run(self, args=""):
        if args:
            filename = args
            if (filename.startswith('"') and filename.endswith('"')) or \
               (filename.startswith("'") and filename.endswith("'")):
                filename = filename[1:-1]
            self.load_program(filename)
        
        if not self.source_lines:
            if not args:
                self.print("Nothing to run.")
            return

        full_code = "\n".join([f"{num} {text}" for num, text in sorted(self.source_lines.items())])
        try:
            self.interpreter.load_program(full_code)
            self.interpreter.execute()
            
            # Sync back source lines if changed (by EXECUTE)
            if hasattr(self.interpreter, 'program_source'):
                self.source_lines = {}
                for ln, txt in self.interpreter.program_source.items():
                    self.source_lines[ln] = txt

        except Exception as e:
            self.print(f"Execution Error: {e}")

    def run_repl(self, autorun=False):
        self.print("Thoroughbred Basic Interpreter CLI")
        self.print("Type 'HELP' for commands.")
        
        if autorun:
            self.do_run()

        while True:
            try:
                user_input = self.input("> ").strip()
            except EOFError:
                break
            except Exception as e:
                self.print(f"CLI Error: {e}")
                continue
            
            try:
                if not user_input:
                    continue
                
                cmd_upper = user_input.upper()
                
                if cmd_upper == 'EXIT' or cmd_upper == 'BYE':
                    self.io_handler.shutdown()
                    sys.exit(0) # In case shutdown doesn't kill immediately
                elif cmd_upper.startswith('LIST'):
                    # ... (keep existing LIST logic)
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
                                self.print(f"Invalid LIST range: {args_str}")
                        else:
                            try:
                                line_num = int(args_str)
                                self.list_program(start=line_num, end=line_num)
                            except ValueError:
                                self.print(f"Invalid LIST line: {args_str}")
                elif cmd_upper == 'NEW':
                    self.source_lines = {}
                    self.print("Program cleared.")
                elif cmd_upper.startswith('RUN'):
                    args = user_input[3:].strip()
                    self.do_run(args)
                elif cmd_upper.startswith('SAVE '):
                    filename = user_input[5:].strip()
                    self.save_program(filename)
                elif cmd_upper.startswith('LOAD '):
                    filename = user_input[5:].strip()
                    self.load_program(filename)
                elif cmd_upper == 'HELP':
                    self.print("Commands: LIST, RUN [file], NEW, SAVE <file>, LOAD <file>, EXIT")
                    self.print("Enter code like: 10 PRINT \"HELLO\"")
                elif user_input[0].isdigit():
                    parts = user_input.split(' ', 1)
                    line_num = int(parts[0])
                    if len(parts) > 1:
                        self.source_lines[line_num] = parts[1]
                    else:
                        self.source_lines.pop(line_num, None)
                else:
                    try:
                        self.interpreter.execute_direct(user_input)
                    except Exception as e:
                        self.print(f"Error: {e}")
            except Exception as e:
                self.print(f"CLI Error: {e}")

def check_tk_availability():
    """Checks if Tkinter can be initialized without crashing (via subprocess)."""
    import subprocess
    try:
        # Run a tiny script that attempts to init Tk
        # Timeout quickly to avoid hanging if it opens a window (it shouldn't if we don't mainloop)
        cmd = [sys.executable, "-c", "import tkinter as tk; root = tk.Tk(); root.destroy()"]
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False

def main():
    use_gui = HAS_TK
    if use_gui:
        # Verify it doesn't crash the process
        if not check_tk_availability():
            print("Tkinter found but unstable (crashed during check). Disabling GUI.")
            use_gui = False

    if use_gui:
        try:
            root = tk.Tk()
            gui = TerminalGUI(root)
            io_handler = GuiIOHandler(gui)
            gui.set_io_handler(io_handler)
            
            cli = BasicCLI(io_handler)
            
            if len(sys.argv) > 1:
                cli.load_program(sys.argv[1])
                
            t = threading.Thread(target=cli.run_repl, args=(len(sys.argv) > 1,), daemon=True)
            t.start()
            
            root.mainloop()
            return
        except Exception as e:
            print(f"Failed to initialize GUI: {e}")
            print("Falling back to console mode...")

    # Fallback to console
    print("Running in Console mode (Tkinter not available or failed).")
    io_handler = ConsoleIOHandler()
    cli = BasicCLI(io_handler)
    
    if len(sys.argv) > 1:
        cli.load_program(sys.argv[1])
        
    cli.run_repl(autorun=(len(sys.argv) > 1))

if __name__ == "__main__":
    main()
