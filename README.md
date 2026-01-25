# Thoroughbred Basic Interpreter (Python)

This project is a Python-based interpreter for a subset of the **Thoroughbred Basic** programming language. It allows you to load, edit, and execute classic Business Basic programs within a modern Python environment.

## 🚀 Features
*   **Variables**: Support for numeric variables (`A`, `B1`) and string variables (`A$`, `NAME$`).
*   **Control Logic**: `GOTO`, `GOSUB`, `RETURN`, `IF...THEN` and structured `FOR...NEXT` loops.
*   **Input/Output**: Interactive `INPUT` and flexible `PRINT` commands.
*   **Line-based**: Full support for line numbers (required for program flow).
*   **GUI Terminal**: Includes an 80x24 terminal window with support for mnemonics (cursor positioning, colors, etc.).

## 📂 Project Structure
The project is modular:
*   `basic.py`: The entry point and CLI/GUI interface.
*   `interpreter.py`: The core logic of the interpreter.
*   `lexer.py`: Tokenizer and syntax definitions.
*   `file_manager.py`: Handling of Basic file formats and I/O.

## 🛠 Usage Guide

### 1. Writing and Editing Programs
Basic programs are written as plain text. Each command must be preceded by a line number.

You can edit programs directly in the `interpreter.py` file under the section `if __name__ == "__main__":`, or you can create an external `.bas` file.

**Example (test.bas):**
```basic
10 PRINT "CALCULATOR"
20 INPUT "NUMBER 1: ", A
30 INPUT "NUMBER 2: ", B
40 LET C = A + B
50 PRINT "THE SUM IS: ", C
60 END
```

### 2. Loading Programs
Currently, the interpreter loads code via the `load_program(source_code)` method. You can pass a string with code or read a file:

```python
with open("test.bas", "r") as f:
    code = f.read()

interpreter = ThoroughbredBasicInterpreter()
interpreter.load_program(code)
```

### 3. The Interactive CLI (`basic.py`)
You can now also use an interactive shell to write and manage code:

```bash
python3 basic.py
```

**Available Commands in the CLI:**
*   `LOAD <filename>`: Loads a Basic program from disk.
*   `SAVE <filename>`: Saves the current program.
*   `LIST`: Shows the current program code with line numbers.
*   `RUN [file]`: Executes the current program, or loads and runs a file directly (e.g., `RUN "test.bas"`).
*   `NEW`: Clears the current program from memory.
*   `<line number> <command>`: Add or overwrite a line (e.g., `10 PRINT "HELLO"`).
*   `<line number>`: Delete a specific line.
*   `EXIT` or `BYE`: Exit the CLI.

### 4. Running Programs from the Terminal
You can also load a file directly and start the CLI:

```bash
python3 basic.py my_program.bas
```

## 📋 Supported Commands
| Keyword | Usage |
| :--- | :--- |
| `LET` | Assign values: `LET X = 5` |
| `PRINT` | Output to screen: `PRINT "VALUE:", X` |
| `INPUT` | Request input from user: `INPUT "NAME?", N$` |
| `GOTO` | Jump to line: `GOTO 10` |
| `IF` | Conditional jump: `IF A=B THEN 100` |
| `GOSUB` | Call subroutine at line number. |
| `RETURN` | Return from the last `GOSUB`. |
| `FOR/NEXT`| Loop blocks: `FOR I = 1 TO 10 STEP 2` |
| `DIRECT` | Create direct file: `DIRECT "FILE", 10, 100` |
| `INDEXED`| Create indexed file: `INDEXED "FILE", 10, 100` |
| `SERIAL` | Create serial file: `SERIAL "FILE", 100` |
| `TEXT` | Create text file: `TEXT "FILE"` |
| `OPEN` | Open existing channel: `OPEN (1) "FILE", DIRECT` |
| `READ` | Read from channel: `READ (1, KEY=K$) A, B$` or `READ (1, IND=5) A, B$` |
| `WRITE` | Write to channel: `WRITE (1, KEY=K$) X, Y$` or `WRITE (1, IND=5) X, Y$` |
| `CLOSE` | Close channel and save data: `CLOSE (1)` |
| `ERASE` | Delete a file from disk: `ERASE "FILE"` |
| `SYSTEM` | System command: `SYSTEM "ls"` |
| `END` | Stop program and close all channels. |
| `DIM` | Define arrays: `DIM A(10), S$(20), B$[5](10)` |
| `CALL/ENTER/EXIT` | Public programs: `CALL "SUB", A`, `ENTER X`, `EXIT` |
| `POS` | Find substring: `POS("S"=A$, 1, 1)` |
| `LEN` | Length of string: `LEN("ABC")` |
| `STR$/VAL` | Conversion: `STR$(100)`, `VAL("1.5")` |
| `ASC/CHR$` | ASCII: `ASC("A")`, `CHR$(65)` |
| `UCS/LCS` | Case: `UCS("a")` -> "A", `LCS("A")` -> "a" |
| `CVS` | Convert String: `CVS(S$, 3)` (Strip left/right) |
| `INT/IPT/FPT`| Integer/Fractional parts: `INT(4.9)` -> 4, `FPT(4.9)` -> 0.9 |
| `MOD` | Modulo: `MOD(10, 3)` -> 1 |
| `ROUND` | Rounding: `ROUND(3.14159, 2)` -> 3.14 |
| `SIN/COS/TAN`| Trigonometry: `SIN(0.5)`, `ATN(1)` |
| `ACS/ASN`| Trigonometry: `ACS(0.5)`, `ASN(0.5)` |
| `LOG/EXP` | Logarithms: `LOG(10)`, `EXP(1)` |
| `SQR` | Root: `SQR(16)` -> 4 |
| `ATH/HTA` | ASCII/Hex conversion: `ATH("41")` -> "A", `HTA("A")` -> "41" |
| `MIN/MAX` | Extremes: `MIN(1,2)`, `MAX(A,B)` |
| `NUM` | Valid numeric check: `NUM(S$)` |
| `SETERR/RETRY` | Error handling: `SETERR 100`, `RETRY` |
| `SETESC/OFF` | Escape key handling: `SETESC 500` |
| `SDX` | Soundex: `SDX("Smith")` |
| `FIND` | Read without moving pointer (or random read): `FIND (1, KEY=K$)` |
| `SELECT` | Filter records (partial support): `SELECT (1, KEY=K$)` |
| `EXTRACT` | Read and lock (emulated): `EXTRACT (1, KEY=K$)` |
| `REMOVE` | Delete record: `REMOVE (1, KEY=K$)` |
| `STOP` | Halt execution: `STOP` |
| `EXECUTE` | Dynamic code: `EXECUTE "PRINT 'HI'"` |
| `CTL` | System variable: `PRINT CTL` (Last control value) |

## 📟 Commands and Mnemonics in `PRINT`
The interpreter now also supports terminal mnemonics for advanced screen control.

**Example:**
```basic
10 PRINT 'CS', 'BR', "Title", 'ER'
20 PRINT @(10, 5), "Cursor at column 10, row 5"
```

| Mnemonic | Function |
| :--- | :--- |
| `'CS'` | Clear Screen |
| `'BR'/'ER'` | Begin/End Reverse Video |
| `'BU'/'EU'` | Begin/End Underline |
| `'VT'/'LF'` | Up/Down |
| `'BS'/'CH'` | Backspace/Cursor Home |
| `'CE'` | Clear to End of Screen |
| `'CL'` | Clear to End of Line |
| `'LD'` | Line Delete |

---
> [!NOTE]
> This interpreter now supports the most important Thoroughbred Basic File I/O functions via emulation in JSON files.
