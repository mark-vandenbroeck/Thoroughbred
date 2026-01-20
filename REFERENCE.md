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
### ASC
**Syntax:** `ASC(string)`  
Geeft de ASCII-waarde van het eerste karakter van de string.
- `ASC("A")` -> `65`

### AND
**Syntax:** `AND(str1, str2)`  
Voert een bitwise AND uit op de ASCII-waarden van de karakters in beide strings.
- `AND(CHR$(255), CHR$(15))` -> `CHR$(15)`

### ATN
**Syntax:** `ATN(num)`  
Geeft de arctangens van een getal (in radialen).

---

## C

### CALL
**Syntax:** `CALL "program", [ERR=line], [args...]`  
Roept een extern sub-programma aan met optionele argumenten.
**Effect:**
- Start een nieuwe interpreter context, pusht variabelen en keert terug na `EXIT` of `END`.
**Side Effects:**
- Variabelen worden "by value" gekopieerd (tenzij `ENTER`/`EXIT` data terugschrijven).

### CHR$
**Syntax:** `CHR$(code)`  
Geeft het karakter dat overeenkomt met de opgegeven ASCII-code.
- `CHR$(65)` -> `"A"`

### CLOSE
**Syntax:** `CLOSE (channel)`  
Sluit een geopend bestandskanaal.
**Side Effects:**
- Schrijft alle in-memory wijzigingen aan het bestand (JSON) weg naar schijf.
- Maakt het kanaalnummer vrij voor hergebruik.

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
**Effect:**
- Initialiseert arrays met 0 of lege strings.

### DIRECT
**Syntax:** `DIRECT "filename", key_len, rec_len`  
Maakt een nieuw DIRECT bestand aan met vaste record- en sleutellengte.
**Effect:**
- Creëert een nieuw JSON bestand op schijf met metadata `type="DIRECT"`.
- Overschrijft bestaand bestand indien aanwezig.

---

## E

### END
**Syntax:** `END`  
Beëindigt de uitvoering van het programma en sluit alle open bestanden.
**Side Effects:**
- Forceert `CLOSE` op alle open kanalen.

### ENTER
**Syntax:** `ENTER var1, var2...`  
Gebruikt in een aangeroepen sub-programma (`CALL`) om argumenten te ontvangen variabele namen te binden.

### ERASE
**Syntax:** `ERASE "filename"`  
Verwijdert een bestand van de schijf.
**Side Effects:**
- Het bestand is permanent verwijderd.

### EXECUTE
**Syntax:** `EXECUTE string_expr [, OPT="LOCAL"]`  
Voert dynamisch Basic-code uit.
**Effect:**
- Parsed de string `string_expr` en voert deze uit.
- Zonder regelnummer: Directe uitvoering (console mode).
- Met regelnummer: Voegt regel toe of wijzigt regel in het huidige programma.
- `OPT="LOCAL"`: Voert uit in de lokale context (standaard is globaal/main programma).
**Side Effects:**
- Wijzigt de programmacode in het geheugen tijdens runtime (self-modifying code).
- Kan variabelen wijzigen.

### EXIT
**Syntax:** `EXIT`  
Verlaat een sub-programma en keert terug naar de `CALL`.
**Effect:**
- Schrijft gewijzigde variabelen terug naar de aanroeper indien van toepassing.
- Pop de context van de stack.

### EXP
**Syntax:** `EXP(num)`  
Geeft `e` tot de macht `num`.

### EXTRACT / EXTRACTRECORD
**Syntax:** `EXTRACT (chn, KEY=k, IND=i) ...`  
Leest een record en lockt deze voor updates.
**Effect:**
- Leest waarden uit het bestand (analoog aan `READ`).
**Verschil met READ:** `EXTRACT` verzet de file pointer **niet**, terwijl `READ` dit wel doet. Dit is cruciaal voor update-operaties op hetzelfde record.
**Side Effects:**
- Zet `last_key` op dit record (voor eventuele `REMOVE` zonder key).

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

### NOT
**Syntax:** `NOT(string)`  
Voert een bitwise NOT (inversie) uit op de karakters (0-255).
- `NOT(CHR$(0))` -> `CHR$(255)`

---

## O

### OPEN
**Syntax:** `OPEN (chn) "filename" [, DIRECT|INDEXED|SERIAL]`  
Opent een bestand op een specifiek kanaalnummer.

### OR
**Syntax:** `OR(str1, str2)`  
Voert een bitwise OR uit op de ASCII-waarden.

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
**Effect:**
- Leest waarden uit het bestand in de opgegeven variabelen.
- Als `KEY` of `IND` wordt gebruikt, wordt direct gesprongen naar dat record.
- Bij sequentiële toegang (zonder `KEY`/`IND`) wordt gelezen vanaf de huidige pointerpositie.
**Side Effects:**
- **File Pointer Update:** Verhoogt de interne file pointer na het lezen (in tegenstelling tot `EXTRACT`).
- Bij `SERIAL` files: wijst naar het volgende record.

### REM / REMARK
**Syntax:** `REM comment`  
Regel met commentaar, wordt genegeerd door de interpreter.
**Effect:** Geen.  
**Side Effects:** Geen.

### REMOVE
**Syntax:** `REMOVE (chn [, KEY=string])`  
Verwijdert een record uit een bestand.
**Effect:**
- Verwijdert het fysieke record uit de dataset van het bestand.
- `KEY=...`: Verwijdert het record met de opgegeven sleutel.
- Zonder KEY: Verwijdert het laatst gelezen of geëxtraheerde record (`last_key`).
**Side Effects:**
- De `last_key` referentie kan na uitvoering ongeldig zijn voor verdere operaties op diezelfde sleutel.
- Ondersteunt `DOM` handling als de sleutel niet bestaat.

### RETURN
**Syntax:** `RETURN`  
Keert terug van een subroutine aangeroepen met `GOSUB`.
**Effect:**
- Hervat executie op de regel direct na de `GOSUB`.
**Side Effects:**
- Verwijdert de bovenste return-adres van de call stack.

### RND
**Syntax:** `RND([seed])`  
Geeft een willekeurig getal tussen 0 en 1.
**Effect:** Retourneert een float.

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
**Effect:** Creëert een nieuw JSON bestand met metadata `type="SERIAL"`.

### SGN
**Syntax:** `SGN(num)`  
Geeft het teken van een getal: 1 (positief), -1 (negatief), 0 (nul).

### SIN
**Syntax:** `SIN(num)`  
Geeft de sinus van een hoek (in radialen).

### SORT
**Syntax:** `SORT "filename", key_len, rec_len`  
Maakt een SORT bestand aan.
**Effect:** Creëert een nieuw JSON bestand met metadata `type="SORT"`.

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
**Effect:**
- "123" -> 123.0
- Probeert intelligente parsing; negeert niet-numerieke suffixen indien mogelijk.

---

## X

### XOR
**Syntax:** `XOR(str1, str2)`  
Voert een bitwise XOR (Exclusive OR) uit op de ASCII-waarden.

---

## W

### WRITE
**Syntax:** `WRITE (chn, KEY=k, IND=i) var1, var2...`  
Schrijft data naar een geopend bestand.
**Effect:**
- Schrijft de waarden uit de variabelen naar het bestand.
- Overschrijft bestaande data als de sleutel al bestaat.
**Side Effects:**
- Update `last_key` van het kanaal.

---

## Terminal Mnemonics

De interpreter ondersteunt de volgende mnemonics in `PRINT` statements (bijv. `PRINT 'CS'`):

| Mnemonic | Functie | Effect |
| :--- | :--- | :--- |
| `'CS'` | Clear Screen | Wist het scherm en zet cursor linksboven. |
| `'BR'` | Begin Reverse | Start omgekeerde video (achtergrond/voorgrond wissel). |
| `'ER'` | End Reverse | Stopt omgekeerde video. |
| `'BU'` | Begin Underline | Start onderstrepen. |
| `'EU'` | End Underline | Stopt onderstrepen. |
| `'VT'` | Vertical Tab / Up | Cursor één regel omhoog. |
| `'LF'` | Line Feed / Down | Cursor één regel omlaag. |
| `'BS'` | Backspace | Cursor één positie naar links. |
| `'CH'` | Cursor Home | Zet cursor linksboven (zonder wissen). |
| `'CE'` | Clear to End of Screen | Wist van cursor tot einde scherm. |
| `'CL'` | Clear to End of Line | Wist van cursor tot einde regel. |
| `'LD'` | Line Delete | Verwijdert huidige regel. |
| `'@' (c, r)` | Cursor Position | Zet cursor op kolom `c`, rij `r`. |
