# Thoroughbred Basic Interpreter (Python)

Dit project is een Python-gebaseerde interpreter voor een subset van de **Thoroughbred Basic** programmeertaal. Het stelt je in staat om klassieke Business Basic programma's te laden, te editen en uit te voeren binnen een moderne Python-omgeving.

## 🚀 Mogelijkheden
*   **Variabelen**: Ondersteuning voor numerieke variabelen (`A`, `B1`) en string-variabelen (`A$`, `NAAM$`).
*   **Controle Logica**: `GOTO`, `GOSUB`, `RETURN`, `IF...THEN` en gestructureerde `FOR...NEXT` lussen.
*   **Input/Output**: Interactieve `INPUT` en flexibele `PRINT` commando's.
*   **Line-based**: Volledige ondersteuning voor regelnummers (verplicht voor programmaflow).

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
*   `RUN`: Voert het huidige programma uit.
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

---
> [!NOTE]
> Deze interpreter ondersteunt nu de belangrijkste Thoroughbred Basic File I/O functies via emulatie in JSON-bestanden.
