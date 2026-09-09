# VR Fitness

VR Fitness is a local Windows tool for recording and evaluating VR fitness sessions.  
VR Fitness ist ein lokales Windows-Tool zur Aufzeichnung und Auswertung von VR-Fitness-Sessions.

**Current PC version / Aktuelle PC-Version: V11.17 Preview**

[Download V11.17 Setup ZIP](releases/V11.17/VR_Fitness_V11_17_Preview_Setup.zip) · [Source ZIP](releases/V11.17/vr_fitness_v11_17_source.zip) · [Patch Notes](releases/V11.17/PATCH_NOTES.md)

**Current Android Companion / Aktueller Android Companion: V1.6.2 Preview**

> **AI-assisted development / KI-unterstützte Entwicklung**  
> VR Fitness is developed with substantial assistance from AI tools, especially for implementation, refactoring, documentation and release preparation. The project is still reviewed and tested manually before releases.  
> VR Fitness wird mit umfangreicher Unterstützung durch KI-Werkzeuge entwickelt, insbesondere bei Implementierung, Refactoring, Dokumentation und Release-Vorbereitung. Vor Veröffentlichungen wird das Projekt weiterhin manuell geprüft und getestet.

---

## Deutsch

### Funktionen

Unterstützte Bewegungsquellen:
- VRTI
- FitOSC

Unterstützte Pulsquellen:
- BluetoothHeartrate über VRCOSC
- Pulsoid
- Pulsoid Widget URL (experimentell, ohne separat hinterlegten API-Token in VR Fitness)
- HypeRate

Weitere Funktionen:
- Session-Aufzeichnung mit Distanz, Schritten, Zeit und Puls
- Live-Anzeige geschätzter aktiver kcal
- kcal in „Letzte Sessions“, Session-Historie und 7-Tage-Auswertung
- Session-Historie, Diagramme und Auswertungen
- PDF-/CSV-/JSON-Ausgaben
- Health-Connect-Anbindung über den Android-Companion
- Deutsch und Englisch, automatisch über Systemsprache oder manuell auswählbar
- Einstellungen bleiben bei Versionswechseln erhalten
- GitHub-basierte Update-Prüfung ohne erzwungene Updates
- VRChat-OSC-Reset unter Einstellungen → Diagnose

### Health Connect / Android Companion

Der Android-Companion verbindet VR Fitness über das lokale Netzwerk mit Health Connect. Der aktuelle Entwicklungsstand kann:
- Sessions vom PC empfangen
- Puls-Samples nach Health Connect schreiben
- Distanz und optional Schritte schreiben
- geschätzte aktive kcal schreiben
- heutige Schritte aus Health Connect lesen
- aktuelles Gewicht aus Health Connect lesen
- letzten verfügbaren SpO₂-Wert lesen
- ein lokales Übertragungslog mit Erfolg/Fehler und übertragenen Daten anzeigen
- den PC-Empfänger auf ein freigegebenes WLAN beschränken

Health-Connect-Funktionen bleiben unabhängig von der lokalen WLAN-Sperre verfügbar. Der PC-Empfänger soll außerhalb des freigegebenen WLANs nicht laufen.

### Kalorien

Die aktiven kcal sind Schätzwerte. Die aktuelle Berechnung nutzt Gewicht, Alter, Geschlecht und den bereinigten Pulsverlauf. Wenn Health-Connect-Gewicht verfügbar und aktiviert ist, wird dieses bevorzugt; sonst kann ein Gewicht manuell hinterlegt werden.

Die Schätzung ist kein medizinischer Messwert. Eine spätere Verbesserung mit Ruhepuls, Ruhephasenerkennung und Trennung von Ruheenergie und aktiver Energie ist geplant.

### Updates

VR Fitness nutzt `version.json` als Update-Quelle. Nutzer entscheiden selbst zwischen:
- Jetzt aktualisieren
- Später erinnern
- Diese Version überspringen

Updates werden nicht erzwungen.

### Datenspeicherung

Fitness-, Session- und Programmeinstellungen werden lokal auf dem jeweiligen PC gespeichert. Die Konfiguration liegt versionsunabhängig unter `%LOCALAPPDATA%\VR Fitness`.

Onlinezugriffe erfolgen nur für benötigte Funktionen, insbesondere:
- GitHub-Updateprüfung
- Pulsoid oder HypeRate, falls ausgewählt
- lokale Kommunikation mit dem Android-Companion

### Nächste Entwicklungsschritte

Geplant für kommende PC-Versionen:
- Diagnosefilter nach Quelle, z. B. VRCOSC, VRTI, FitOSC, Pulsoid, HypeRate, Health Connect, Session, Update und System
- Filter nach Info, Warnung, Fehler und Debug
- Textsuche im Diagnose-Log
- später verbesserte kcal-Berechnung mit Ruhephasen
- mittelfristig eine richtige Windows-EXE anstelle der BAT-basierten Installation

### Releases und Patchnotes

PC-Versionen werden unter `releases/Vxx.xx/` abgelegt. Android-Versionen liegen unter `android/releases/Vx.x.x/`.

Release-Ablauf:
1. neue Version bauen
2. prüfen/testen
3. Patchnotes erstellen
4. Dateien in den Versionsordner legen
5. `version.json` auf die freigegebene PC-Version aktualisieren

### Status

VR Fitness befindet sich weiterhin im Preview-/Testbetrieb. Insbesondere neue Health-Connect-, Android- und Kalorienfunktionen sollten auf realen Geräten und in echten Sessions getestet werden.

---

## English

### Features

Supported movement sources:
- VRTI
- FitOSC

Supported heart-rate sources:
- BluetoothHeartrate via VRCOSC
- Pulsoid
- Pulsoid Widget URL (experimental, no separate API token stored in VR Fitness)
- HypeRate

Additional features:
- session recording with distance, steps, time and heart rate
- live estimated active kcal
- kcal in Recent Sessions, session history and 7-day summaries
- session history, charts and statistics
- PDF, CSV and JSON exports
- Health Connect integration through the Android companion
- German and English
- settings preserved across upgrades
- GitHub update checking without forced updates
- VRChat OSC reset under Settings → Diagnostics

### Health Connect / Android Companion

The Android companion bridges VR Fitness to Health Connect over the local network. The current development version can:
- receive sessions from the PC
- write heart-rate samples to Health Connect
- write distance and optional steps
- write estimated active kcal
- read today's Health Connect steps
- read the latest body weight
- read the latest available SpO₂ value
- show a local transfer log with success/failure and transmitted data
- restrict the PC receiver to one approved Wi-Fi network

Health Connect background functions remain independent from the local Wi-Fi restriction.

### Calories

Active kcal are estimates. The current calculation uses weight, age, sex and cleaned heart-rate data. Health Connect weight is preferred when enabled, otherwise a manual weight can be configured.

This is not a medical measurement. Future work is planned for resting heart rate, rest-phase detection and separating resting energy from active energy.

### Updates

VR Fitness uses `version.json` as its update source. Users decide between:
- Update now
- Remind me later
- Skip this version

Updates are never forced.

### Data storage

Fitness data, sessions and settings are stored locally on the PC. Configuration is stored independently of the installed version under `%LOCALAPPDATA%\VR Fitness`.

Online access is only used where needed, especially:
- GitHub update checks
- Pulsoid or HypeRate when selected
- local communication with the Android companion

### Next development steps

Planned for future PC versions:
- diagnostic filtering by source such as VRCOSC, VRTI, FitOSC, Pulsoid, HypeRate, Health Connect, Session, Update and System
- filtering by Info, Warning, Error and Debug
- text search in diagnostic logs
- improved calorie estimation with rest-phase handling
- eventually a proper Windows EXE instead of BAT-based installation

### Releases and patch notes

PC versions are stored under `releases/Vxx.xx/`. Android versions are stored under `android/releases/Vx.x.x/`.

Release workflow:
1. build
2. test/verify
3. write patch notes
4. place files in the version folder
5. update `version.json` for the released PC version

### Status

VR Fitness remains a preview/testing project. New Health Connect, Android and calorie features should be tested on real devices and in real sessions before wider distribution.

---

## License / Lizenz

This project is licensed under the MIT License. See `LICENSE`.  
Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE`.

## Verified release files / Geprüfte Release-Dateien

PC V11.17: Installer and application match the original SHA-256 values. ZIP archives were repacked from those verified bytes; their new hashes are in [SHA256SUMS.txt](releases/V11.17/SHA256SUMS.txt). / Installer und Programmcode entsprechen den Original-Hashes; die neu gepackten ZIPs haben eigene Prüfsummen.

Android V1.6.2: [source and debug APK](android/releases/V1.6.2/). The APK is an existing local debug build, not a production release; no device test was performed as part of publication.
