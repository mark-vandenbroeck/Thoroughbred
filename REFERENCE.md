# Thoroughbred Basic Reference Manual

Deze handleiding bevat een gedetailleerd alfabetisch overzicht van alle geïmplementeerde commando's (directives) en functies in deze interpreter.

---

## Configuratie en Disks

De interpreter maakt gebruik van een **'Disk' systeem** voor bestandsbeheer, waarbij logische disk-namen (zoals `D0`, `D1`) worden gekoppeld aan fysieke directories op het hostsysteem.

### IPLINPUT
Bij het opstarten leest de interpreter configuratie uit `IPLINPUT` in de huidige werkmap.
**Structuur:**
`DISKNAAM = /pad/naar/directory`

**Voorbeeld:**
```text
D0 = ./data/primary
D1 = ./data/backup
```
Bij bestandsoperaties (zoals `OPEN`) wordt standaard gezocht in de volgorde: `D0`, `D1`, enz., tenzij een specifiek pad of disknummer is opgegeven.

### Bestanden Aanmaken
Bij commando's zoals `DIRECT`, `INDEXED`, `SERIAL` en `SORT` kan een disk-nummer worden opgegeven om te bepalen waar het bestand wordt aangemaakt.

---

## Bestandsformaten

De interpreter werkt met vier specifieke bestandstypes:

### DIRECT (Keyed File)
Bestanden met vaste recordlengte, toegankelijk via een unieke sleutel (string).
- Geoptimaliseerd voor willekeurige toegang (Random Access).
- **Aanmaken:** `DIRECT "naam", key_len, rec_len, disk`

### SORT (Sort File)
Bevat alleen sleutels (tot 128 bytes). Wordt gebruikt voor het sorteren van data of als indexbestand.
- **Aanmaken:** `SORT "naam", key_len, folder_len, disk`

### INDEXED
Een Key-Value opslagmechanisme. Vergelijkbaar met DIRECT maar flexibeler in sommige implementaties.
- **Aanmaken:** `INDEXED "naam", 10, 0, disk`

### SERIAL
Sequentiële bestanden. Records worden achter elkaar geschreven.
- Gebruik voor logs of data die sequentieel verwerkt wordt.
- Toegang via 'Random Access' (`READ (chn, IND=i)`) is mogelijk maar minder efficiënt.
- **Aanmaken:** `SERIAL "naam", rec_len, disk`

---

## A

## A

### ABS
**Type:** Numerieke Functie  
**Syntax:** `ABS(num)`  
**Beschrijving:** Retourneert de absolute waarde van een getal `num`.  
**Voorbeelden:**
- `ABS(-5)` &rarr; `5`

### ASC
**Type:** String Functie  
**Syntax:** `ASC(string)`  
**Beschrijving:** Retourneert de decimale ASCII-waarde van het **eerste** karakter van `string`.  
**Voorbeelden:**
- `ASC("A")` &rarr; `65`

### ATH
**Type:** Conversie Functie  
**Syntax:** `ATH(hex_string)`  
**Beschrijving:** Converteert een hexadecimale string naar een binaire string (ASCII).  
Als de input-string een oneven lengte heeft, wordt er automatisch een '0' aan de voorkant toegevoegd.  
**Voorbeelden:**
- `ATH("41")` &rarr; `"A"`
- `ATH("414243")` &rarr; `"ABC"`

### ATN
**Type:** Numerieke Functie  
**Syntax:** `ATN(num)`  
**Beschrijving:** Retourneert de arctangens van `num` in radialen.

---

## C

### CALL
**Type:** Flow Control Directive  
**Syntax:** `CALL "programma", [ERR=regelnr], [argumenten...]`  
**Beschrijving:** Start de uitvoering van een extern Basic-programma als een subroutine.
- Er wordt een **nieuwe context** gecreëerd. Variabelen uit het aanroepende programma zijn **niet** zichtbaar in het aangeroepen programma, tenzij ze expliciet worden doorgegeven.
- Het aangeroepen programma gebruikt `ENTER` om argumenten te ontvangen.
- Met `EXIT` keert de besturing terug naar het aanroepende programma (na de `CALL`).
**Voorbeeld:**
```basic
10 CALL "SUB", A
```

### CHR$
**Type:** String Functie  
**Syntax:** `CHR$(code)`  
**Beschrijving:** Converteert een ASCII-code (0-255) naar het bijbehorende karakter.
**Voorbeelden:**
- `CHR$(65)` &rarr; `"A"`

### CLOSE
**Type:** I/O Directive  
**Syntax:** `CLOSE (channel)`  
**Beschrijving:** Sluit het bestand dat geopend is op kanaalnummer `channel`. Alle buffers worden weggeschreven naar disk.

### COS
**Type:** Numerieke Functie  
**Syntax:** `COS(num)`  
**Beschrijving:** Retourneert de cosinus van hoek `num` (in radialen).

### CVS
**Type:** String Functie  
**Syntax:** `CVS(string, mode)`  
**Beschrijving:** Converteert `string` volgens de opgegeven bitwise `mode`.
- **1:** Strip spaties links (LTRIM)
- **2:** Strip spaties rechts (RTRIM)
- **16:** Converteer naar Hoofdletters
- **32:** Converteer naar Kleine letters
**Voorbeelden:**
- `CVS("   test   ", 3)` &rarr; `"test"` (1+2 = Strip beiden)
- `CVS("a", 16)` &rarr; `"A"`

---

## D

### DIM
**Type:** Declaratie Directive  
**Syntax:** `DIM var[size](len), ...`  
**Beschrijving:** Reserveert geheugen voor arrays.
**Voorbeelden:**
- `DIM A(10)`: Numerieke array.
- `DIM B$(5)`: String array.

### DIRECT
**Type:** File Directive  
**Syntax:** `DIRECT "filename", key_len, rec_len, disk_num, sector_num`  
**Beschrijving:** Creëert een nieuw 'DIRECT' (Keyed) bestand.
- `key_len`: Max lengte van de sleutel.
- `rec_len`: Max lengte van een record.
- `disk_num`: Doel disk (bijv. 0 voor D0).

### DTN
**Type:** datum Functie  
**Syntax:** `DTN(string [, mask])`  
**Beschrijving:** Converteert datumtekst naar een Julian Day Number. Standaardmasker: "DD-MON-YYYY HH:MI:SS".
**Voorbeelden:**
- `DTN("01-JAN-2023", "DD-MON-YYYY")`

---

## E

### END
**Type:** Flow Control Directive  
**Syntax:** `END`  
**Beschrijving:** Stopt de uitvoering van het programma onmiddellijk en sluit alle bestanden.

### ENDTRACE
**Type:** Debug Directive  
**Syntax:** `ENDTRACE`  
**Beschrijving:** Schakelt de trace-modus uit.

### ENTER
**Type:** Flow Control Directive  
**Syntax:** `ENTER var1, var2...`  
**Beschrijving:** Ontvangt argumenten in een aangeroepen programma (`CALL`).

### ERASE
**Type:** File Directive  
**Syntax:** `ERASE "filename"`  
**Beschrijving:** Verwijdert een bestand fysiek van de disk.

### EXECUTE
**Type:** Meta Directive  
**Syntax:** `EXECUTE string_expr [, OPT="LOCAL"]`  
**Beschrijving:** Compileert en voert Basic-code uit die in `string_expr` staat tijdens runtime.

### EXIT
**Type:** Flow Control Directive  
**Syntax:** `EXIT`  
**Beschrijving:** Beëindigt een programma dat gestart is met `CALL`. Schrijft gewijzigde referentie-variabelen (via `ENTER`) terug naar de aanroeper.

### EXP
**Type:** Numerieke Functie  
**Syntax:** `EXP(num)`  
**Beschrijving:** Berekent *e* tot de macht `num`.

### EXTRACT / EXTRACTRECORD
**Type:** I/O Directive  
**Syntax:** `EXTRACT (chn, KEY=k, IND=i) vars...`  
**Beschrijving:** Leest record data en plaatst een **lock** op het record.
- **Belangrijk:** Verplaatst de file pointer **niet**.
- Vergelijk met `READ`.

---

## F

### FOR
**Type:** Flow Control Directive  
**Syntax:** `FOR var = start TO end [STEP step]`  
**Beschrijving:** Start een lusteller. De lus wordt afgesloten met `NEXT var`.
- `start`, `end`, `step` kunnen expressies zijn.
- Als `step` ontbreekt, is de stapgrootte 1.
- De lus voert minimaal 0 keer uit (als start > end en step > 0).

### FPT
**Type:** Numerieke Functie  
**Syntax:** `FPT(num)`  
**Beschrijving:** Retourneert het fractionele deel (achter de komma) van `num`.
- `FPT(3.14)` &rarr; `0.14`

---

## G

### GOSUB
**Type:** Flow Control Directive  
**Syntax:** `GOSUB line`  
**Beschrijving:** Springt naar een subroutine op `line`. Het programma keert terug naar de regel na `GOSUB` zodra een `RETURN` wordt bereikt.
- Nesting is toegestaan.

### GOTO
**Type:** Flow Control Directive  
**Syntax:** `GOTO line`  
**Beschrijving:** Springt onvoorwaardelijk naar `line`.

---

## H

### HTA
**Type:** Conversie Functie  
**Syntax:** `HTA(string)`  
**Beschrijving:** (Hex to ASCII) Converteert de bytes in `string` naar hun hexadecimale representatie.
**Voorbeelden:**
- `HTA("A")` &rarr; `"41"`

---

## I

### IF
**Type:** Flow Control Directive  
**Syntax:** `IF condition THEN line` / `IF condition THEN statement`  
**Beschrijving:** Voert een actie uit als `condition` waar is (niet nul).
- `THEN line`: Springt naar regelnummer (impliciete GOTO).
- `THEN statement`: Voert statement uit.
**Operatoren:** `=`, `<>`, `<`, `>`, `<=`, `>=`.

### INDEXED
**Type:** File Directive  
**Syntax:** `INDEXED "filename", key_len, rec_len, disk_num, sector_num`  
**Beschrijving:** Creëert een INDEXED bestand.
- Gedrag is vergelijkbaar met DIRECT in deze implementatie (Key-Value store).

### INPUT
**Type:** I/O Directive  
**Syntax:** `INPUT [channel, opties] "Prompt: ", var1, var2...`  
**Beschrijving:** Vraagt invoer van de gebruiker (standaard kanaal 0) of leest van een terminal-kanaal.
- `INPUT "Naam: ", N$`
- Ondersteunt `IOL=` opties voor geformatteerde invoer.

### INT
**Type:** Numerieke Functie  
**Syntax:** `INT(num)`  
**Beschrijving:** Retourneert het grootste gehele getal kleiner dan of gelijk aan `num` (Floor).
- `INT(3.9)` &rarr; `3`
- `INT(-3.9)` &rarr; `-4`

### IOLIST
**Type:** I/O Directive  
**Syntax:** `line IOLIST item [, item ...]`  
**Beschrijving:** Definieert een herbruikbare lijst van variabelen en formatters voor I/O statements (`READ`, `WRITE`, `PRINT`, `INPUT`).
**Items:**
- **Variabelen:** `A$`, `B` (leest/schrijft waarde)
- **Mnemonics:** `'CS'`, `'LF'` (alleen Terminal I/O)
- **Cursor:** `@(col, row)` (alleen Terminal I/O)
- **Literals:** `"Tekst"` (Schrijft tekst / Verwacht tekst bij Input)
- **Skip:** `*` (Slaat veld over bij Input)
**Gebruik:**
Gerefereerd via `IOL=line` optie in I/O statement.
```basic
100 IOLIST A$, B, "Label", *
200 READ (1, IOL=100)
```

### IPT
**Type:** Numerieke Functie  
**Syntax:** `IPT(num)`  
**Beschrijving:** Retourneert het gehele deel van een getal door het af te kappen (Truncate).
- `IPT(3.9)` &rarr; `3`
- `IPT(-3.9)` &rarr; `-3`

---

## K

### KEY
**Type:** I/O Functie  
**Syntax:** `KEY(channel [, ERR=line, END=line])`  
**Beschrijving:** Retourneert de sleutel (key) van het **volgende** record in een DIRECT of SORT bestand zonder het record te lezen.
- Gebruik dit om door keys te itereren (`KEY(1)`).

---

## L

### LCS
**Type:** String Functie  
**Syntax:** `LCS(string)`  
**Beschrijving:** Converteert `string` naar kleine letters (LowerCase).

### LEN
**Type:** String Functie  
**Syntax:** `LEN(string)`  
**Beschrijving:** Retourneert het aantal karakters in `string`.

### LET
**Type:** Assignment Directive  
**Syntax:** `LET var = expr`  
**Beschrijving:** Wijst de waarde van `expr` toe aan variabele `var`.
- Het sleutelwoord `LET` is optioneel (`A = 10` is geldig).
- Ondersteunt substrings: `A$(1,3) = "ABC"`.

### LOG
**Type:** Numerieke Functie  
**Syntax:** `LOG(num)`  
**Beschrijving:** Retourneert de natuurlijke logaritme van `num`.

---

## M

### MAX
**Type:** Numerieke/String Functie  
**Syntax:** `MAX(item1, item2, ...)`  
**Beschrijving:** Retourneert de grootste waarde uit de lijst.

### MIN
**Type:** Numerieke/String Functie  
**Syntax:** `MIN(item1, item2, ...)`  
**Beschrijving:** Retourneert de kleinste waarde uit de lijst.

### MOD
**Type:** Numerieke Functie  
**Syntax:** `MOD(num, div)`  
**Beschrijving:** Retourneert de restwaarde van de deling `num / div`.

---

## N

### NEXT
**Type:** Flow Control Directive  
**Syntax:** `NEXT var`  
**Beschrijving:** Sluit een `FOR` lus af. Verhoogt de teller en springt terug als de eindconditie nog niet bereikt is.

### NOT
**Type:** String Functie  
**Syntax:** `NOT(string)`  
**Beschrijving:** Voert een bitwise NOT (inversie) uit op alle bytes in de string.

### NUM
**Type:** Conversie Functie  
**Syntax:** `NUM(string [, NTP=type, SIZ=round, ERR=line, ERC=code])`  
**Beschrijving:** Converteert `string` naar een getal en valideert dit.
- `SIZ`: Rondt af op veelvoud van deze waarde (bijv. `0.01` voor geld).
- `ERR`: Springt naar regelnummer bij ongeldige input.

---

## O

### ON ... GOTO / GOSUB
**Type:** Flow Control Directive  
**Syntax:** `ON val GOTO/GOSUB line1, line2...`  
**Beschrijving:** Springt naar het `val`-de regelnummer in de lijst.
- Als `val` <= 0: Eerste regel.
- Als `val` > aantal: Laatste regel.

### OPEN
**Type:** I/O Directive  
**Syntax:** `OPEN (chn) "filename" [, Opties]`  
**Beschrijving:** Opent een bestand op kanaalnummer `chn` (1-255). Kanaal 0 is de terminal.
- Zoekt bestand via `IPLINPUT` paden.
- Bestandsmodus (DIRECT, SERIAL) wordt automatisch gedetecteerd of kan geforceerd worden.

### OR
**Type:** String Functie  
**Syntax:** `OR(str1, str2)`  
**Beschrijving:** Voert een bitwise OR uit op de bytes van twee strings.

---

## P

### POS
**Type:** String/Logic Functie  
**Syntax:** `POS(heystack, needle, start)` OF `POS(relational_expr [, step [, count]])`  
**Beschrijving:** 
1. `POS("Data", "a", 1)`: Zoekt "a" in "Data" vanaf index 1.
2. `POS("A" = A$, 1, 1)`: Zoekt locatie waar conditie waar is.
**Voorbeelden:**
- `POS("abc" = "a..b..c", 1, 2)` &rarr; Zoekt 2e match.

### PRINT
**Type:** I/O Directive  
**Syntax:** `PRINT (chn) expr, ...`  
**Beschrijving:** Schrijft tekst naar kanaal.
- Kanaal 0 (of weggelaten): Scherm.
- Ondersteunt Mnemonics (`'CS'`, `'@(c,r)'`) op terminals.
- Komma `,` tabs, puntkomma `;` plakt aan elkaar.

---

## R

### READ
**Type:** I/O Directive  
**Syntax:** `READ (chn [, KEY=k, IND=i, IOL=line]) var1, ...`  
**Beschrijving:** Leest velden uit een record.
- **Sequentieel:** Leest volgend record en verhoogt file pointer.
- **Random Access:** `KEY="k"` leest specifiek record en verhoogt pointer NIET (tenzij SERIAL?). *Correctie:* READ verhoogt pointer normaal wel, EXTRACT niet.
- `DOM=line`: Spring naar line bij "Duplicate/Key Not Found" (voor READ meestal KNF).
- `END=line`: Spring naar line bij EOF.
- `ERR=line`: Spring naar line bij algemene fout.

### REM
**Type:** Commentaar  
**Syntax:** `REM tekst` of `! tekst`  
**Beschrijving:** Wordt genegeerd.

### REMOVE
**Type:** File Directive  
**Syntax:** `REMOVE (chn [, KEY=k])`  
**Beschrijving:** Verwijdert een record.
- Zonder `KEY`: Verwijdert het laatst benaderde record.

### RETRY
**Type:** Flow Control Directive  
**Syntax:** `RETRY`  
**Beschrijving:** Keert terug naar de regel die de laatste fout veroorzaakte en voert deze opnieuw uit.
- Werkt in combinatie met `SETERR`, `ERR=`, `DOM=`, `END=`.
- Herstelt automatisch de waarde van `SETERR` naar de status vóór de fout.

### RETURN
**Type:** Flow Control Directive  
**Syntax:** `RETURN`  
**Beschrijving:** Keert terug van `GOSUB`.

### RND
**Type:** Numerieke Functie  
**Syntax:** `RND([seed])`  
**Beschrijving:** Retourneert een pseudo-willekeurig getal tussen 0.0 en 1.0.

### ROUND
**Type:** Numerieke Functie  
**Syntax:** `ROUND(num, prec)`  
**Beschrijving:** Rondt `num` af op `prec` decimalen.

---

## S

### SELECT
**Type:** I/O Directive  
**Syntax:** `SELECT (chn) ...`  
**Beschrijving:** (Gedeeltelijk) Filtert records.

### SERIAL
**Type:** File Directive  
**Syntax:** `SERIAL "filename", rec_len, disk_num`  
**Beschrijving:** Creëert een serieel bestand (alleen toevoegen/lezen).

### SETERR
**Type:** Flow Control Directive  
**Syntax:** `SETERR line | OFF | ON`  
**Beschrijving:** Definieert een globale error-handler routine.
- Als er een fout optreedt (en geen `ERR=` aanwezig is), springt de interpreter naar `line`.
- `SETERR` wordt automatisch op 0 (uit) gezet bij het binnengaan van de handler.
- Gebruik `RETRY` (nog niet geïmplementeerd) om terug te keren.

### SETTRACE
**Type:** Debug Directive  
**Syntax:** `SETTRACE [(chn)]`  
**Beschrijving:** Activeert regel-voor-regel logging van executie.

### SET TRACEMODE
**Type:** Debug Directive  
**Syntax:** `SET TRACEMODE "mode"`  
**Beschrijving:** "FULL", "PARTIAL", "SKIPCALLS".

### SGN
**Type:** Numerieke Functie  
**Syntax:** `SGN(num)`  
**Beschrijving:** Teken functie: -1, 0, of 1.

### SIN
**Type:** Numerieke Functie  
**Syntax:** `SIN(num)`  
**Beschrijving:** Sinus.

### SORT
**Type:** File Directive  
**Syntax:** `SORT "name", klen, rlen...`  
**Beschrijving:** Creëert een SORT bestand (External Sort Index).

### SQR
**Type:** Numerieke Functie  
**Syntax:** `SQR(num)`  
**Beschrijving:** Vierkantswortel.

### STOP
**Type:** Flow Control Directive  
**Syntax:** `STOP`  
**Beschrijving:** Stopt programma.

### STR$
**Type:** Conversie Functie  
**Syntax:** `STR$(num)`  
**Beschrijving:** Getal naar string.

---

## T

### TAN
**Type:** Numerieke Functie  
**Syntax:** `TAN(num)`  
**Beschrijving:** Tangens.

---

## U

### UCS
**Type:** String Functie  
**Syntax:** `UCS(string)`  
**Beschrijving:** Converteert naar Hoofdletters.

---

## V

### VAL
**Type:** String Functie  
**Syntax:** `VAL(string)`  
**Beschrijving:** Converteert string naar getal.
- `VAL("123abc")` &rarr; `123`

---

## X

### XOR
**Type:** String Functie  
**Syntax:** `XOR(str1, str2)`  
**Beschrijving:** Bitwise XOR.

---

## W

### WRITE
**Type:** I/O Directive  
**Syntax:** `WRITE (chn [, KEY=k, IND=i, IOL=line]) val1, ...`  
**Beschrijving:** Schrijft data naar een record.
- **Nieuw Record:** Als KEY niet bestaat.
- **Update:** Als KEY bestaat.
- `DOM=line`: "Duplicate or Missing". Bij WRITE, als record al bestaat en niet mag (is dat zo? Meestal overwrite WRITE gewoon).

---

## Terminal Mnemonics

De interpreter ondersteunt Mnemonics in `PRINT` statements (bijv. `PRINT 'CS'`).

| Mnemonic | Functie | Effect |
| :--- | :--- | :--- |
| `'CS'` | Clear Screen | Wist het scherm en zet cursor linksboven. |
| `'BR'` | Begin Reverse | Start omgekeerde video. |
| `'ER'` | End Reverse | Stopt omgekeerde video. |
| `'BU'` | Begin Underline | Start onderstrepen. |
| `'EU'` | End Underline | Stopt onderstrepen. |
| `'VT'` | Vertical Tab | Cursor één regel omhoog. |
| `'LF'` | Line Feed | Cursor één regel omlaag. |
| `'BS'` | Backspace | Cursor links. |
| `'CH'` | Cursor Home | Cursor naar 0,0. |
| `'CE'` | Clear to EOS | Wist tot einde scherm. |
| `'CL'` | Clear to EOL | Wist tot einde regel. |
| `'LD'` | Line Delete | Verwijdert regel. |
| `'@'(c,r)`| Cursor Pos | Zet cursor op (col, row). |

