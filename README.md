# VR Fitness

VR Fitness is a local Windows tool for recording and evaluating VR fitness sessions.  
VR Fitness ist ein lokales Windows-Tool zur Aufzeichnung und Auswertung von VR-Fitness-Sessions.

**Current PC version / Aktuelle PC-Version: V11.14 Preview**

[Download V11.14 Preview](releases/V11.14/VR_Fitness_V11_14_Preview_Setup.bat) · [Patch Notes](releases/V11.14/PATCH_NOTES.md)

---

## Deutsch

### Funktionen

Unterstützte Bewegungsquellen:
- VRTI
- FitOSC

Unterstützte Pulsquellen:
- BluetoothHeartrate über VRCOSC
- Pulsoid
- HypeRate

Zusätzlich kann ein Android-Companion Health-Connect-Daten mit VR Fitness austauschen.

Weitere Funktionen:
- Session-Aufzeichnung mit Distanz, Schritten, Zeit und Puls
- Session-Historie, Diagramme und Auswertungen
- PDF-/CSV-/JSON-Ausgaben
- Health-Connect-Anbindung über den Android-Companion
- Deutsch und Englisch, automatisch über die Systemsprache oder manuell auswählbar
- Einstellungen bleiben bei Versionswechseln erhalten
- GitHub-basierte Update-Prüfung

### Updates

Ab V11.12 nutzt VR Fitness dieses Repository als feste Update-Quelle. Die Datei `version.json` enthält die aktuell freigegebene Version, den Downloadpfad und eine kurze Änderungsbeschreibung.

Ab V11.14 entscheidet immer der Nutzer selbst, wie mit einem Update umgegangen wird:
- **Jetzt aktualisieren**
- **Später erinnern**
- **Diese Version überspringen**

Updates werden nicht erzwungen. Eine übersprungene Version wird bei automatischen Prüfungen nicht erneut angeboten; eine neuere Version wird wieder normal angezeigt. Unter **Einstellungen → Diagnose → Update prüfen** kann jederzeit manuell geprüft werden.

### Datenspeicherung

Fitness-, Session- und Programmeinstellungen werden lokal auf dem jeweiligen PC gespeichert. Die Konfiguration liegt versionsunabhängig unter `%LOCALAPPDATA%\VR Fitness` und wird bei Updates weiterverwendet.

Onlinezugriffe erfolgen nur für Funktionen, die sie benötigen, insbesondere:
- GitHub-Updateprüfung
- Pulsoid oder HypeRate, falls ausgewählt
- lokale Kommunikation mit dem Android-Companion

### Android Companion

Der Android-Companion befindet sich ebenfalls noch im Testbetrieb. Er kann Daten mit Health Connect austauschen und über das lokale Netzwerk mit VR Fitness kommunizieren. Eine Play-Store-Veröffentlichung ist derzeit nicht Bestandteil der Distribution.

### Releases und Patchnotes

Neue PC-Versionen werden unter `releases/Vxx.xx/` abgelegt. Jede Version erhält eigene `PATCH_NOTES.md` mit den Änderungen der jeweiligen Version.

Der Release-Ablauf ist:
1. neue Version bauen
2. Version prüfen/testen
3. Patchnotes erstellen
4. Dateien unter `releases/Vxx.xx/` ablegen
5. `version.json` auf die freigegebene Version aktualisieren

### Status

VR Fitness befindet sich weiterhin im Preview-/Testbetrieb. Insbesondere neue Datenquellen und Android-/Health-Connect-Funktionen sollten vor breiter Nutzung getestet werden.

---

## English

### Features

Supported movement sources:
- VRTI
- FitOSC

Supported heart-rate sources:
- BluetoothHeartrate via VRCOSC
- Pulsoid
- HypeRate

An Android companion can also exchange Health Connect data with VR Fitness.

Additional features:
- session recording with distance, steps, time and heart rate
- session history, charts and statistics
- PDF, CSV and JSON exports
- Health Connect integration through the Android companion
- German and English, selected automatically from the system language or manually
- settings are preserved across version upgrades
- GitHub-based update checking

### Updates

Since V11.12, VR Fitness uses this repository as its fixed update source. The `version.json` file contains the currently released version, download path and a short change summary.

Starting with V11.14, the user always decides what to do with an available update:
- **Update now**
- **Remind me later**
- **Skip this version**

Updates are never forced. A skipped version is not shown again during automatic checks, while a newer version will be offered normally. A manual check is always available under **Settings → Diagnostics → Check for updates**.

### Data storage

Fitness data, sessions and application settings are stored locally on the PC. Configuration is stored independently of the installed version under `%LOCALAPPDATA%\VR Fitness` and is reused after upgrades.

Online access is only used for features that require it, especially:
- GitHub update checking
- Pulsoid or HypeRate when selected
- local communication with the Android companion

### Android Companion

The Android companion is also still in testing. It can exchange data with Health Connect and communicate with VR Fitness over the local network. A Google Play release is currently not part of the distribution.

### Releases and patch notes

New PC versions are stored under `releases/Vxx.xx/`. Every version gets its own `PATCH_NOTES.md` containing the changes for that release.

Release workflow:
1. build the new version
2. test and verify it
3. write patch notes
4. place the files under `releases/Vxx.xx/`
5. update `version.json` to publish the release

### Status

VR Fitness is still in preview/testing. New data sources and Android/Health Connect functionality should be tested carefully before wider distribution.

---

## License / Lizenz

This project is licensed under the MIT License. See `LICENSE`.  
Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE`.
