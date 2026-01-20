# Thoroughbred Basic Interpreter (Python)

Dit project is een Python-gebaseerde interpreter voor een subset van de **Thoroughbred Basic** programmeertaal. Het stelt je in staat om klassieke Business Basic programma's te laden, te editen en uit te voeren binnen een moderne Python-omgeving.

## 🚀 Mogelijkheden
*   **Variabelen**: Ondersteuning voor numerieke variabelen (`A`, `B1`) en string-variabelen (`A$`, `NAAM$`).
*   **Controle Logica**: `GOTO`, `GOSUB`, `RETURN`, `IF...THEN` en gestructureerde `FOR...NEXT` lussen.
*   **Input/Output**: Interactieve `INPUT` en flexibele `PRINT` commando's.
*   **Line-based**: Volledige ondersteuning voor regelnummers (verplicht voor programmaflow).
*   **GUI Terminal**: Inclusief een 80x24 terminal venster met ondersteuning voor mnemonics (cursor positionering, kleuren, etc.).

## 📂 Project Structuur
Het project is modulair opgebouwd:
*   `basic.py`: De entry-point en CLI/GUI interface.
*   `interpreter.py`: De kernlogica van de interpreter.
*   `lexer.py`: Tokenizer en syntax definities.
*   `file_manager.py`: Afhandeling van Basic bestandsformaten en I/O.

## 🛠 Gebruikshandleiding

### 1. Programma's Schrijven en Editen
Basic-programma's worden geschreven als gewone tekst. Elk commando moet voorafgegaan worden door een regelnummer.

Je kunt programma's direct in de `interpreter.py` file aanpassen onder de sectie `if __name__ == "__main__":`, of je kunt een externe `.bas` file aanmaken.

**Voorbeeld (test.bas):**
```basic
10 PRINT "REKENMACHINE"
20 INPUT "GETAL 1: ", A
30 INPUT "GETAL 2: ", B
40 LET C = A + B
50 PRINT "DE SOM IS: ", C
60 END
```

### 2. Programma's Laden
Op dit moment laadt de interpreter code via de `load_program(source_code)` methode. Je kunt een string met code meegeven of een bestand inlezen:

```python
with open("test.bas", "r") as f:
    code = f.read()

interpreter = ThoroughbredBasicInterpreter()
interpreter.load_program(code)
```

### 2. De Interactive CLI (`basic.py`)
Je kunt nu ook een interactieve shell gebruiken om code te schrijven en te beheren:

```bash
python3 basic.py
```

**Beschikbare Commando's in de CLI:**
*   `LOAD <bestandsnaam>`: Laadt een Basic-programma van schijf.
*   `SAVE <bestandsnaam>`: Slaat het huidige programma op.
*   `LIST`: Toont de huidige programmacode met regelnummers.
*   `RUN [file]`: Voert het huidige programma uit, of laadt en runt direct een bestand (bijv. `RUN "test.bas"`).
*   `NEW`: Wissen van het huidige programma in het geheugen.
*   `<regelnummer> <commando>`: Toevoegen of overschrijven van een regel (bijv. `10 PRINT "HALLO"`).
*   `<regelnummer>`: Verwijderen van een specifieke regel.
*   `EXIT` of `BYE`: Afsluiten van de CLI.

### 3. Programma's Uitvoeren vanuit de Terminal
Je kunt een bestand ook direct laden en de CLI starten:

```bash
python3 basic.py mijn_programma.bas
```

## 📋 Ondersteunde Commando's
| Keyword | Gebruik |
| :--- | :--- |
| `LET` | Toewijzen van waarden: `LET X = 5` |
| `PRINT` | Uitvoer naar scherm: `PRINT "WAARDE:", X` |
| `INPUT` | Vraag invoer aan gebruiker: `INPUT "NAAM?", N$` |
| `GOTO` | Spring naar regel: `GOTO 10` |
| `IF` | Voorwaardelijke sprong: `IF A=B THEN 100` |
| `GOSUB` | Roep subroutine aan op regelnummer. |
| `RETURN` | Keer terug uit de laatste `GOSUB`. |
| `FOR/NEXT`| Herhaalblokken: `FOR I = 1 TO 10 STEP 2` |
| `DIRECT` | Maak direct bestand: `DIRECT "FILE", 10, 100` |
| `INDEXED`| Maak indexed bestand: `INDEXED "FILE", 10, 100` |
| `SERIAL` | Maak serial bestand: `SERIAL "FILE", 100` |
| `OPEN` | Open bestaand kanaal: `OPEN (1) "FILE", DIRECT` |
| `READ` | Lees van kanaal: `READ (1, KEY=K$) A, B$` of `READ (1, IND=5) A, B$` |
| `WRITE` | Schrijf naar kanaal: `WRITE (1, KEY=K$) X, Y$` of `WRITE (1, IND=5) X, Y$` |
| `CLOSE` | Sluit kanaal en sla data op: `CLOSE (1)` |
| `ERASE` | Verwijder een bestand van schijf: `ERASE "FILE"` |
| `END` | Stop programma en sluit alle kanalen. |
| `DIM` | Definieer arrays: `DIM A(10), S$(20), B$[5](10)` |
| `CALL/ENTER/EXIT` | Public programs: `CALL "SUB", A`, `ENTER X`, `EXIT` |
| `POS` | Zoek substring: `POS("S"=A$, 1, 1)` |
| `LEN` | Lengte van string: `LEN("ABC")` |
| `STR$/VAL` | Conversie: `STR$(100)`, `VAL("1.5")` |
| `ASC/CHR$` | ASCII: `ASC("A")`, `CHR$(65)` |
| `UCS/LCS` | Case: `UCS("a")` -> "A", `LCS("A")` -> "a" |
| `CVS` | Convert String: `CVS(S$, 3)` (Strip links/rechts) |
| `INT/IPT/FPT`| Integer/Fractional parts: `INT(4.9)` -> 4, `FPT(4.9)` -> 0.9 |
| `MOD` | Modulo: `MOD(10, 3)` -> 1 |
| `ROUND` | Afronden: `ROUND(3.14159, 2)` -> 3.14 |
| `SIN/COS/TAN`| Goniometrie: `SIN(0.5)`, `ATN(1)` |
| `LOG/EXP` | Logaritmen: `LOG(10)`, `EXP(1)` |
| `SQR` | Wortel: `SQR(16)` -> 4 |
| `EXECUTE` | Dynamic code: `EXECUTE "PRINT 'HI'"` |

## 📟 Commando's en Mnemonics in `PRINT`
De interpreter ondersteunt nu ook terminal mnemonics voor geavanceerde schermsturing.

**Voorbeeld:**
```basic
10 PRINT 'CS', 'BR', "Title", 'ER'
20 PRINT @(10, 5), "Cursor op kolom 10, rij 5"
```

| Mnemonic | Functie |
| :--- | :--- |
| `'CS'` | Clear Screen |
| `'BR'/'ER'` | Begin/End Reverse Video |
| `'BU'/'EU'` | Begin/End Underline |
| `'VT'/'LF'` | Omhoog/Omlaag |
| `'BS'/'CH'` | Backspace/Cursor Home |
| `'CE'` | Clear to End of Screen |
| `'CL'` | Clear to End of Line |
| `'LD'` | Line Delete |

---
> [!NOTE]
> Deze interpreter ondersteunt nu de belangrijkste Thoroughbred Basic File I/O functies via emulatie in JSON-bestanden.
