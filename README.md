# VR Fitness

VR Fitness is a local Windows tool for recording and evaluating VR fitness sessions.  
VR Fitness ist ein lokales Windows-Tool zur Aufzeichnung und Auswertung von VR-Fitness-Sessions.

**Published PC version / Veröffentlichte PC-Version: V11.14 Preview**  
**Current development PC version / Aktueller PC-Entwicklungsstand: V11.17 Preview**  
**Current Android Companion / Aktueller Android-Companion: V1.6.2 Preview**

[Download published V11.14](releases/V11.14/VR_Fitness_V11_14_Preview_Setup.bat) · [V11.17 Patch Notes](releases/V11.17/PATCH_NOTES.md) · [Android V1.6.2 Patch Notes](android/releases/V1.6.2/PATCH_NOTES.md)

> **AI-assisted development / KI-unterstützte Entwicklung**  
> VR Fitness is developed with substantial assistance from AI tools, especially for implementation, debugging, refactoring, documentation, translations and release preparation. Project decisions, practical testing and release approval are still performed manually.  
> VR Fitness wird mit umfangreicher Unterstützung durch KI-Werkzeuge entwickelt, insbesondere bei Implementierung, Fehlersuche, Refactoring, Dokumentation, Übersetzungen und Release-Vorbereitung. Projektentscheidungen, Praxistests und die Freigabe neuer Versionen erfolgen weiterhin manuell.

---

## Deutsch

### Funktionen

**Bewegungsquellen**
- VRTI
- FitOSC

**Pulsquellen**
- BluetoothHeartrate über VRCOSC
- Pulsoid über Access-Token
- Pulsoid Widget URL (experimentell, ohne separaten API-Token in VR Fitness)
- HypeRate

**Sessions und Auswertung**
- Session-Aufzeichnung mit Distanz, Schritten, Zeit und Puls
- Session-Historie, Letzte Sessions, Diagramme und Auswertungen
- PDF-/CSV-/JSON-Ausgaben
- Pulszonen und Datenqualitätsprüfung
- ab V11.17: geschätzte aktive kcal live auf der Hauptseite
- ab V11.17: kcal in Letzte Sessions, Session-Historie und 7-Tage-Zusammenfassung

### Health Connect

Der Android-Companion verbindet VR Fitness über das lokale Netzwerk mit Android Health Connect.

Aktueller Funktionsstand:
- VR-Fitness-Sessions nach Health Connect schreiben
- Herzfrequenz, Distanz, optional Schritte und geschätzte aktive kcal übertragen
- Health-Connect-Schritte lesen
- aktuelles Gewicht lesen und optional für die kcal-Schätzung verwenden
- letzten verfügbaren SpO₂-Wert lesen
- Übertragungslog für erfolgreiche/fehlgeschlagene Health-Connect-Schreibvorgänge
- PC-Empfänger auf ein freigegebenes WLAN beschränken

Die kcal-Werte sind **Schätzwerte** und keine medizinischen Messwerte.

### Updates

VR Fitness verwendet `version.json` in diesem Repository als feste Update-Quelle. Seit V11.14 entscheidet der Nutzer selbst:
- **Jetzt aktualisieren**
- **Später erinnern**
- **Diese Version überspringen**

Updates werden nicht erzwungen.

`version.json` bleibt bewusst auf der zuletzt vollständig veröffentlichten PC-Version, bis die Dateien einer neueren Version im Release-Ordner vorhanden sind.

### Datenspeicherung

Fitness-, Session- und Programmeinstellungen werden lokal gespeichert. Die Konfiguration liegt versionsunabhängig unter:

`%LOCALAPPDATA%\VR Fitness`

Onlinezugriffe erfolgen nur für Funktionen, die sie benötigen, insbesondere GitHub-Updateprüfung, Pulsoid/HypeRate und die lokale Kommunikation mit dem Android-Companion.

### Releases und Patchnotes

PC-Versionen liegen unter:

`releases/Vxx.xx/`

Android-Versionen liegen unter:

`android/releases/Vx.x.x/`

Aktuell vorbereitet:
- `releases/V11.17/PATCH_NOTES.md`
- `android/releases/V1.6.2/PATCH_NOTES.md`

Der Release-Ablauf bleibt:
1. Version bauen
2. prüfen/testen
3. Patchnotes erstellen
4. Dateien im Versionsordner ablegen
5. `version.json` auf die freigegebene PC-Version aktualisieren

### Nächster PC-Ausbau

Für die nächste PC-Version ist ein strukturierter Diagnosefilter vorgesehen: Quellen wie VRCOSC, VRTI, FitOSC, Pulsoid und Health Connect sowie Filter nach Info/Warnung/Fehler und Textsuche.

---

## English

### Features

**Movement sources**
- VRTI
- FitOSC

**Heart-rate sources**
- BluetoothHeartrate via VRCOSC
- Pulsoid via access token
- Pulsoid Widget URL (experimental, without a separate API token stored in VR Fitness)
- HypeRate

**Sessions and analysis**
- session recording with distance, steps, time and heart rate
- Recent Sessions, session history, charts and statistics
- PDF, CSV and JSON outputs
- heart-rate zones and data-quality checks
- V11.17 development build: live estimated active kcal on the main screen
- V11.17 development build: kcal in Recent Sessions, session history and 7-day summary

### Health Connect

The Android companion links VR Fitness with Android Health Connect over the local network.

Current feature set:
- write VR Fitness sessions to Health Connect
- write heart rate, distance, optional steps and estimated active kcal
- read Health Connect steps
- read current body weight and optionally use it for kcal estimation
- read the latest available SpO₂ value
- transfer log for successful/failed Health Connect writes
- restrict the PC receiver to an approved Wi-Fi network

Calorie values are **estimates**, not medical measurements.

### Updates

VR Fitness uses `version.json` in this repository as its update source. Since V11.14 the user decides what to do with an available update:
- **Update now**
- **Remind me later**
- **Skip this version**

Updates are never forced.

`version.json` intentionally remains on the latest fully published PC version until the files for a newer version are present in its release folder.

### Data storage

Fitness data, sessions and settings are stored locally. Version-independent configuration is stored under:

`%LOCALAPPDATA%\VR Fitness`

Online access is only used for features that require it, especially GitHub update checks, Pulsoid/HypeRate and local communication with the Android companion.

### Releases and patch notes

PC versions:
`releases/Vxx.xx/`

Android versions:
`android/releases/Vx.x.x/`

Currently prepared:
- `releases/V11.17/PATCH_NOTES.md`
- `android/releases/V1.6.2/PATCH_NOTES.md`

Release workflow:
1. build
2. test/verify
3. write patch notes
4. place files in the version folder
5. update `version.json` for the published PC release

### Next PC development step

The next PC release is planned to add structured diagnostic filtering by source (VRCOSC, VRTI, FitOSC, Pulsoid, Health Connect), severity (Info/Warning/Error) and text search.

---

## License / Lizenz

This project is licensed under the MIT License. See `LICENSE`.  
Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE`.
