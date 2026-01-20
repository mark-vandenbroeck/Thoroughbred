# Thoroughbred Basic Reference Manual

Deze handleiding bevat een alfabetisch overzicht van alle geïmplementeerde commando's (directives) en functies in deze interpreter.

---

## A

### ABS
**Syntax:** `ABS(num)`  
Geeft de absolute waarde van een getal.
- `ABS(-5)` -> `5`

### ASC
**Syntax:** `ASC(string)`  
Geeft de ASCII-waarde van het eerste karakter van de string.
- `ASC("A")` -> `65`

### ATN
**Syntax:** `ATN(num)`  
Geeft de arctangens van een getal (in radialen).

---

## C

### CALL
**Syntax:** `CALL "program", [ERR=line], [args...]`  
Roept een extern sub-programma aan met optionele argumenten. Variabelen worden "by value" doorgegeven tenzij expliciet teruggeschreven door het aangeroepen programma via `ENTER` en `EXIT`.

### CHR$
**Syntax:** `CHR$(code)`  
Geeft het karakter dat overeenkomt met de opgegeven ASCII-code.
- `CHR$(65)` -> `"A"`

### CLOSE
**Syntax:** `CLOSE (channel)`  
Sluit een geopend bestandskanaal.
- `CLOSE (1)`

### COS
**Syntax:** `COS(num)`  
Geeft de cosinus van een hoek (in radialen).

### CVS
**Syntax:** `CVS(string, mode)`  
Converteert of manipuleert een string op basis van de modus:
- `1`: Strip leading spaces
- `2`: Strip trailing spaces
- `16`: Naar hoofdletters (UpperCase)
- `32`: Naar kleine letters (LowerCase)
Modi kunnen opgeteld worden (bijv. `3` = strip leading & trailing).

---

## D

### DIM
**Syntax:** `DIM var[size](len), ...`  
Definieert arrays of reserveert geheugen voor string-arrays.
- `DIM A(10)`: Numerieke array met 11 elementen (0-10).
- `DIM S$(5)`: String array.

### DIRECT
**Syntax:** `DIRECT "filename", key_len, rec_len`  
Maakt een nieuw DIRECT bestand aan met vaste record- en sleutellengte.

---

## E

### END
**Syntax:** `END`  
Beëindigt de uitvoering van het programma en sluit alle open bestanden.

### ENTER
**Syntax:** `ENTER var1, var2...`  
Gebruikt in een aangeroepen sub-programma (`CALL`) om argumenten te ontvangen variabele namen te binden.

### ERASE
**Syntax:** `ERASE "filename"`  
Verwijdert een bestand van de schijf.

### EXECUTE
**Syntax:** `EXECUTE string_expr [, OPT="LOCAL"]`  
Voert dynamisch Basic-code uit.
- Zonder regelnummer: Directe uitvoering (console mode).
- Met regelnummer: Voegt regel toe of wijzigt regel in het programma.
- `OPT="LOCAL"`: Voert uit in de lokale context (standaard is globaal/main programma).

### EXIT
**Syntax:** `EXIT`  
Verlaat een sub-programma en keert terug naar de `CALL`. Schrijft gewijzigde variabelen terug naar de aanroeper indien van toepassing.

### EXP
**Syntax:** `EXP(num)`  
Geeft `e` tot de macht `num`.

### EXTRACT / EXTRACTRECORD
**Syntax:** `EXTRACT (chn, KEY=k, IND=i) ...`  
Leest een record en lockt deze voor updates (in deze interpreter functioneel gelijk aan `READ`).

---

## F

### FOR
**Syntax:** `FOR var = start TO end [STEP step]`  
Start een lus.
- `FOR I = 1 TO 10 STEP 2`

### FPT
**Syntax:** `FPT(num)`  
Geeft het fractionele deel van een getal (achter de komma).
- `FPT(3.14)` -> `0.14`

---

## G

### GOSUB
**Syntax:** `GOSUB line`  
Springt naar een subroutine op het opgegeven regelnummer. Keer terug met `RETURN`.

### GOTO
**Syntax:** `GOTO line`  
Springt onvoorwaardelijk naar het opgegeven regelnummer.

---

## I

### IF
**Syntax:** `IF condition THEN line` / `IF condition THEN statement`  
Voert conditionele logica uit.
- `IF A < 10 THEN 100`
- `IF A = B THEN PRINT "GELIJK"`

### INDEXED
**Syntax:** `INDEXED "filename", key_len, rec_len`  
Maakt een INDEXED bestand aan.

### INPUT
**Syntax:** `INPUT "Prompt: ", var`  
Vraagt invoer van de gebruiker.

### INT
**Syntax:** `INT(num)`  
Geeft het grootste gehele getal kleiner dan of gelijk aan `num` (floor).
- `INT(3.9)` -> `3`

### IPT
**Syntax:** `IPT(num)`  
Geeft het gehele deel van een getal (truncation).
- `IPT(3.9)` -> `3`
- `IPT(-3.9)` -> `-3`

---

## L

### LCS
**Syntax:** `LCS(string)`  
Converteert een string naar kleine letters (LowerCase).

### LEN
**Syntax:** `LEN(string)`  
Geeft de lengte van een string.

### LET
**Syntax:** `LET var = expr`  
Wijst een waarde toe aan een variabele. Het woord `LET` is optioneel in veel basics, maar hier expliciet. Ondersteunt substrings: `LET A$(1,3) = "ABC"`.

### LOG
**Syntax:** `LOG(num)`  
Geeft de natuurlijke logaritme van een getal.

---

## M

### MOD
**Syntax:** `MOD(num, div)`  
Geeft de restwaarde van een deling (modulo).

---

## N

### NEXT
**Syntax:** `NEXT var`  
Sluit een `FOR` lus af en verhoogt de teller.

---

## O

### OPEN
**Syntax:** `OPEN (chn) "filename" [, DIRECT|INDEXED|SERIAL]`  
Opent een bestand op een specifiek kanaalnummer.

---

## P

### POS
**Syntax:** `POS(heystack, needle, start)`  
(Let op syntax kan variëren per Basic, hier geïmplementeerd als functie). Zoekt de positie van een substring.

### PRINT
**Syntax:** `PRINT expr, ...`  
Toont tekst of waarden op het scherm.
- Mnemonics: `PRINT 'CS'` (Clear Screen), `'@(col,row)'` (Cursor Positie).

---

## R

### READ
**Syntax:** `READ (chn, KEY=k, IND=i) var1, var2...`  
Leest data uit een geopend bestand.

### REM / REMARK
**Syntax:** `REM comment`  
Regel met commentaar, wordt genegeerd door de interpreter.

### RETURN
**Syntax:** `RETURN`  
Keert terug van een subroutine aangeroepen met `GOSUB`.

### RND
**Syntax:** `RND([seed])`  
Geeft een willekeurig getal tussen 0 en 1.

### ROUND
**Syntax:** `ROUND(num, decimals)`  
Rondt een getal af op het opgegeven aantal decimalen.

---

## S

### SELECT
**Syntax:** `SELECT (chn) ...`  
(Gedeeltelijke implementatie) Selecteert records uit een bestand.

### SERIAL
**Syntax:** `SERIAL "filename", rec_len`  
Maakt een SERIAL bestand aan (oplopend, geen sleutel).

### SGN
**Syntax:** `SGN(num)`  
Geeft het teken van een getal: 1 (positief), -1 (negatief), 0 (nul).

### SIN
**Syntax:** `SIN(num)`  
Geeft de sinus van een hoek (in radialen).

### SORT
**Syntax:** `SORT "filename", key_len, rec_len`  
Maakt een SORT bestand aan.

### SQR
**Syntax:** `SQR(num)`  
Geeft de vierkantswortel van een getal.

### STR$
**Syntax:** `STR$(num)`  
Converteert een getal naar een string.

---

## T

### TAN
**Syntax:** `TAN(num)`  
Geeft de tangens van een hoek (in radialen).

---

## U

### UCS
**Syntax:** `UCS(string)`  
Converteert een string naar hoofdletters (UpperCase).

---

## V

### VAL
**Syntax:** `VAL(string)`  
Converteert een string naar een getal.

---

## W

### WRITE
**Syntax:** `WRITE (chn, KEY=k, IND=i) var1, var2...`  
Schrijft data naar een geopend bestand.

