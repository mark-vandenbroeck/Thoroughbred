# Thoroughbred Basic Reference Manual

Deze handleiding bevat een alfabetisch overzicht van alle geïmplementeerde commando's (directives) en functies in deze interpreter.

Deze handleiding bevat een alfabetisch overzicht van alle geïmplementeerde commando's (directives) en functies in deze interpreter.

---

## Configuratie en Disks

De interpreter ondersteunt het **Thoroughbred Basic 'Disk' concept**. Dit is een mapping van logische schijfnummers naar fysieke directories.

### IPLINPUT
Bij het opstarten leest de interpreter het configuratiebestand `IPLINPUT` in de huidige werkmap.
**Formaat:**
```text
D0 = ./data/d0
D1 = ./data/backup
DA = /var/thoroughbred/data
```
- Elke disk naam begint met `D`, gevolgd door 1 karakter (cijfer of letter).
- Paden kunnen relatief of absoluut zijn.

### Bestanden Zoeken
Bij het openen van een bestand (`OPEN`), zoekt de interpreter het bestand in de gedefinieerde disks in **alfabetische volgorde** van de disk-naam (bijv. eerst `D0`, dan `D1`, dan `DA`...), tenzij een specifiek pad is opgegeven.

### Bestanden Aanmaken
Bij commando's zoals `DIRECT`, `INDEXED`, `SERIAL` en `SORT` kan een disk-nummer worden opgegeven om te bepalen waar het bestand wordt aangemaakt.
De syntax voor deze commando's is uitgebreid met `disk-num` en `sector-num` (waarbij sector-num momenteel gereserveerd is/optioneel, maar in de syntax vereist kan zijn voor compatibiliteit).

### Voorbeelden
**1. IPLINPUT Configuratie:**
```text
D0 = basic_storage/d0
D1 = basic_storage/d1
```

**2. Bestand Aanmaken op D1:**
```basic
10 DIRECT "klanten", 10, 64, 1, 0  : REM Maak aan op D1 (disk_num=1)
```

**3. Bestand Openen (Zoekvolgorde):**
```basic
20 OPEN (1) "klanten"  : REM Zoekt in D0, dan D1... vindt 'klanten' op D1
```

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

### ATH
**Syntax:** `ATH(string)`  
(ASCII to Hex) Converteert een hexadecimale string naar een binaire string (bytes).
- Als de lengte oneven is, wordt een '0' voorgevoegd ("A" -> "0A").
- `ATH("41")` -> `"A"`
- `ATH("414243")` -> `"ABC"`

### ATN
**Syntax:** `ATN(num)`  
Geeft de arctangens van een getal (in radialen).
- `ATN(1)` -> `0.785...` (pi/4)

---

## C

### CALL
**Syntax:** `CALL "program", [ERR=line], [args...]`  
Roept een extern sub-programma aan met optionele argumenten.
**Effect:**
- Start een nieuwe interpreter context, pusht variabelen en keert terug na `EXIT` of `END`.
- Variabelen worden "by value" gekopieerd (tenzij `ENTER`/`EXIT` data terugschrijven).
- `CALL "subprog", A, B`

### CHR$
**Syntax:** `CHR$(code)`  
Geeft het karakter dat overeenkomt met de opgegeven ASCII-code.
- `CHR$(65)` -> `"A"`

### CLOSE
**Syntax:** `CLOSE (channel)`  
Sluit een geopend bestandskanaal.
- Schrijft alle in-memory wijzigingen aan het bestand (JSON) weg naar schijf.
- Maakt het kanaalnummer vrij voor hergebruik.
- `CLOSE (1)`

### COS
**Syntax:** `COS(num)`  
Geeft de cosinus van een hoek (in radialen).
- `COS(3.14159)` -> `-1.0`

### CVS
**Syntax:** `CVS(string, mode)`  
Converteert of manipuleert een string op basis van de modus:
- `1`: Strip leading spaces (LTRIM)
- `2`: Strip trailing spaces (RTRIM)
- `16`: Naar hoofdletters (UpperCase)
- `32`: Naar kleine letters (LowerCase)
**Combinaties:**
- `3` (1+2): Strip beide.
- `19` (1+2+16): Strip beide en converteer naar hoofdletters.
- `CVS("  Test  ", 3)` -> `"Test"`
- `CVS("abc", 16)` -> `"ABC"`

---

## D

### DIM
**Syntax:** `DIM var[size](len), ...`  
Definieert arrays of reserveert geheugen voor string-arrays.
**Effect:**
- Initialiseert arrays met 0 of lege strings.
- `DIM A(10), B$[20](30)`

### DIRECT
**Syntax:** `DIRECT "filename", key_len, rec_len, disk_num, sector_num`  
Maakt een nieuw DIRECT bestand aan.
**Params:**
- `key_len`: Lengte van de sleutel.
- `rec_len`: Lengte van het record.
- `disk_num`: Integer (bijv. `0` voor `D0`, `1` voor `D1`).
- `sector_num`: Integer (gereserveerd, bijv. `0` of `10`).
- Creëert een nieuw JSON bestand op de opgegeven disk.
- `DIRECT "klanten", 10, 64, 0, 0`

---

- `DIRECT "klanten", 10, 64, 0, 0`

### DTN
**Syntax:** `DTN(string [, mask])`  
Converteert een datumstring volgens het masker naar een SQL numerieke datum (Julian Day Number).
**Masker opties:**
- `YYYY`, `YY`, `YYY`: Jaar.
- `MM`, `MON`, `MONTH`: Maand.
- `DD`, `DDD`: Dag.
- `HH`, `MI`, `SS`: Tijd.
**Default:** "DD-MON-YYYY HH:MI:SS"
- `DTN("25-DEC-2023", "DD-MON-YYYY")` -> `2460306.0`

---

### END
**Syntax:** `END`  
Beëindigt de uitvoering van het programma en sluit alle open bestanden.
**Side Effects:**
- Forceert `CLOSE` op alle open kanalen.
- `END`

### ENDTRACE
**Syntax:** `ENDTRACE`  
Beëindigt de trace modus gestart door `SETTRACE`.
**Effect:**
- Stopt het printen van trace regels.
- `ENDTRACE`

### ENTER
**Syntax:** `ENTER var1, var2...`  
Gebruikt in een aangeroepen sub-programma (`CALL`) om argumenten te ontvangen variabele namen te binden.
- `ENTER Namen$, Leeftijd`

### ERASE
**Syntax:** `ERASE "filename"`  
Verwijdert een bestand van de schijf.
**Side Effects:**
- Het bestand is permanent verwijderd.
- `ERASE "oude_data"`

### EXECUTE
**Syntax:** `EXECUTE string_expr [, OPT="LOCAL"]`  
Voert dynamisch Basic-code uit.
**Effect:**
- Parsed de string `string_expr` en voert deze uit.
- Zonder regelnummer: Directe uitvoering (console mode equivalent).
- Met regelnummer: Voegt regel toe of wijzigt regel in het huidige programma (**Self-Modifying Code**).
- `OPT="LOCAL"`: Voert uit in een tijdelijke context. Variabelen worden niet permanent in het hoofdprogramma gewijzigd.
**Side Effects:**
- Wijzigt de programmacode in het geheugen tijdens runtime indien een regelnummer wordt gebruikt.
- Kan variabelen wijzigen in de globale scope (zonder `OPT="LOCAL"`).
**Voorbeelden:**
- `EXECUTE "PRINT 'Hello'"` (Directe uitvoer)
- `EXECUTE "100 PRINT 'New Line'"` (Wijzigt regel 100)
- `EXECUTE "LET A=10"` (Zet A=10 in globale scope)
- `EXECUTE "LET A=20", OPT="LOCAL"` (Zet A=20 lokaal)

### EXIT
**Syntax:** `EXIT`  
Verlaat een sub-programma en keert terug naar de `CALL`.
- Schrijft gewijzigde variabelen terug naar de aanroeper indien van toepassing.
- Pop de context van de stack.
- `EXIT`

### EXP
**Syntax:** `EXP(num)`  
Geeft `e` tot de macht `num`.
- `EXP(1)` -> `2.718...`

### EXTRACT / EXTRACTRECORD
**Syntax:** `EXTRACT (chn, KEY=k, IND=i) ...`  
Leest een record en lockt deze voor updates.
**Effect:**
- Leest waarden uit het bestand (analoog aan `READ`).
**Verschil met READ:** `EXTRACT` verzet de file pointer **niet**, terwijl `READ` dit wel doet. Dit is cruciaal voor update-operaties op hetzelfde record.
**Side Effects:**
- Zet `last_key` op dit record (voor eventuele `REMOVE` zonder key).
- `EXTRACT (1, KEY="Klant1") A$, B$`

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
- `GOSUB 1000`

### GOTO
**Syntax:** `GOTO line`  
Springt onvoorwaardelijk naar het opgegeven regelnummer.
- `GOTO 10`

---

---

## H

### HTA
**Syntax:** `HTA(string)`  
(Hex to ASCII) Converteert een string naar zijn hexadecimale representatie.
- `HTA("A")` -> `"41"`
- `HTA("ABC")` -> `"414243"`

---

## I

### IF
**Syntax:** `IF condition THEN line` / `IF condition THEN statement`  
Voert conditionele logica uit.
- `IF A < 10 THEN 100`
- `IF A = B THEN PRINT "GELIJK"`

### INDEXED
**Syntax:** `INDEXED "filename", num_recs, rec_len, disk_num, sector_num`  
Maakt een INDEXED bestand aan.
- `INDEXED "voorraad", 100, 128, 0, 0`

### INPUT
**Syntax:** `INPUT "Prompt: ", var`  
Vraagt invoer van de gebruiker.
- `INPUT "Naam: ", N$`

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
- `LCS("ABC")` -> `"abc"`

### LEN
**Syntax:** `LEN(string)`  
Geeft de lengte van een string.
- `LEN("Test")` -> `4`

### LET
**Syntax:** `LET var = expr`  
Wijst een waarde toe aan een variabele. Het woord `LET` is optioneel (impliciete assignment supported).
- `A$ = "Hello"`

### LOG
**Syntax:** `LOG(num)`  
Geeft de natuurlijke logaritme van een getal.
- `LOG(2.718)` -> `~1`

---

## M

### MOD
**Syntax:** `MOD(num, div)`  
Geeft de restwaarde van een deling (modulo).
- `MOD(10, 3)` -> `1`

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
Opent een bestand op een specifiek kanaalnummer. Zoekt in `IPLINPUT` disks indien geen pad is opgegeven.

### OR
**Syntax:** `OR(str1, str2)`  
Voert een bitwise OR uit op de ASCII-waarden.
- `OR(CHR$(1), CHR$(2))` -> `CHR$(3)`

---

## P

### POS
**Syntax:** `POS(heystack, needle, start)` OF `POS(relational_expression [, step [, count]])`  
Zoekt de positie van een substring.  
**Geavanceerd Gebruik:**
De POS functie evalueert een relationele expressie over de hele string en zoekt matches.
- `POS("A" = A$)`: Zoek eerste voorkomen waar karakter gelijk is aan "A".
- `POS("A" = A$, 1, 2)`: Zoek het **2e** voorkomen, stapgrootte 1.
- `POS("A" = A$, -1, 1)`: Zoek achterstevoren (stap -1).
- `POS(A$ = "Hello")`: Zoek waar substring A$ gelijk is aan "Hello" (substring match).
- `POS(A$ > "B")`: Zoek positie waar karakters groter zijn dan "B".
**Parameters:**
- `relational_expression`: Formaat `"needle" RELOP "haystack"` of andersom. RELOPs: `=`, `<>`, `<`, `>`, `<=`, `>=`.
- `step`: Stapgrootte voor de zoekloop (positief = vooruit, negatief = achteruit). Default `1`.
- `count`: Welke match teruggeven (1e, 2e...). Indien `0`, geeft het **totaal aantal matches** terug.

**Voorbeelden:**
- `POS("S" = "MISSISSIPPI")` -> `3`
- `POS("S" = "MISSISSIPPI", 1, 0)` -> `4` (totaal aantal 'S'-en)
- `POS("S" = "MISSISSIPPI", -1, 1)` -> `7` (laatste 'S', gezien vanaf eind)

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
- `READ (1, KEY="Klant1") Naam$, Adres$`
- `READ (1) VolgendeRegel$`

### REM / REMARK
**Syntax:** `REM comment`  
Regel met commentaar, wordt genegeerd door de interpreter.
**Effect:** Geen.  
**Side Effects:** Geen.
- `REM Dit is commentaar`
- `! Dit is ook commentaar`

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
- `REMOVE (1, KEY="1001")`
- `REMOVE (1)` (verwijdert laatst gelezen record)

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
- `RND(1)` -> `0.123...`

### ROUND
**Syntax:** `ROUND(num, decimals)`  
Rondt een getal af op het opgegeven aantal decimalen.
- `ROUND(3.14159, 2)` -> `3.14`

---

## S

### SELECT
**Syntax:** `SELECT (chn) ...`  
(Gedeeltelijke implementatie) Selecteert records uit een bestand.
- `SELECT (1) WHERE Naam$ > "M"` (hypothetisch voorbeeld)

### SERIAL
**Syntax:** `SERIAL "filename", rec_len, disk_num, sector_num`  
Maakt een SERIAL bestand aan (oplopend, geen sleutel).
**Effect:** Creëert een nieuw JSON bestand met metadata `type="SERIAL"` op de opgegeven disk.
- `SERIAL "log", 80`

### SETTRACE
**Syntax:** `SETTRACE [(channel)]`  
Start het tracen van programma-executie. Standaard op kanaal 0 (console).
**Effect:**
- Toont regelnummer en broncode voor elke regel die wordt uitgevoerd (in FULL mode).
- `SETTRACE`
- `SETTRACE (2)`

### SET TRACEMODE
**Syntax:** `SET TRACEMODE string`  
Configureert de details van de trace output.
**Opties (string):**
- `"FULL"`: Volledige regel (default).
- `"PARTIAL"`: Geparseerde tokens/directives.
- `"SKIPCALLS"`: Trace niet in `CALL` sub-programma's.
- `"SKIPGOSUBS"`: Trace niet in `GOSUB` routines.
- `"DELAY=n"`: Pauzeer `n` seconden na elke regel.
**Combinaties:** Gebruik `|` (pipe).
- `SET TRACEMODE "PARTIAL|D=0.2"`
- `SET TRACEMODE "SKIPCALLS|F"`

### SGN
**Syntax:** `SGN(num)`  
Geeft het teken van een getal: 1 (positief), -1 (negatief), 0 (nul).
- `SGN(-10)` -> `-1`

### SIN
**Syntax:** `SIN(num)`  
Geeft de sinus van een hoek (in radialen).
- `SIN(1.57)` -> `~1`

### SORT
**Syntax:** `SORT "filename", key_len, rec_len, disk_num, sector_num`  
Maakt een SORT bestand aan.
**Effect:** Creëert een nieuw JSON bestand met metadata `type="SORT"` op de opgegeven disk.
- `SORT "klant_index", 10, 128`

### SQR
**Syntax:** `SQR(num)`  
Geeft de vierkantswortel van een getal.
- `SQR(16)` -> `4`

### STOP
**Syntax:** `STOP`  
Stopt de uitvoering van het programma onmiddellijk.
**Effect:**
- Beëindigt programma/trace.
- `STOP`

### STR$
**Syntax:** `STR$(num)`  
Converteert een getal naar een string.
- `STR$(123)` -> `"123"`

---

## T

### TAN
**Syntax:** `TAN(num)`  
Geeft de tangens van een hoek (in radialen).
- `TAN(0.785)` -> `~1`

---

## U

### UCS
**Syntax:** `UCS(string)`  
Converteert een string naar hoofdletters (UpperCase).
- `UCS("abc")` -> `"ABC"`

---

## V

### VAL
**Syntax:** `VAL(string)`  
Converteert een string naar een getal.
**Effect:**
- "123" -> 123.0
- Probeert intelligente parsing; negeert niet-numerieke suffixen indien mogelijk.
- `VAL("100")` -> `100.0`

---

## X

### XOR
**Syntax:** `XOR(str1, str2)`  
Voert een bitwise XOR (Exclusive OR) uit op de ASCII-waarden.
- `XOR("A", "C")` -> resultaat met bitwise XOR

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
- `WRITE (1, KEY="100") "Jan", "Amsterdam"`

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
