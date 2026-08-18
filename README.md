# VR Fitness

VR Fitness ist ein lokales Windows-Tool zur Aufzeichnung und Auswertung von VR-Fitness-Sessions.

## Aktueller Stand

Aktuelle PC-Version: **V11.12 Preview**

Unterstützte Bewegungsquellen:
- VRTI
- FitOSC

Unterstützte Pulsquellen:
- BluetoothHeartrate über VRCOSC
- Pulsoid
- HypeRate

Zusätzlich kann ein Android-Companion Health-Connect-Daten mit VR Fitness austauschen.

## Updates

Ab **V11.12 Preview** verwendet VR Fitness dieses GitHub-Repository als feste Update-Quelle.

Die App liest dafür die Datei `version.json` aus diesem Repository. Dort stehen:
- aktuelle Versionsnummer
- Download-/Projektlink
- kurze Änderungen der Version

VR Fitness prüft beim Programmstart im Hintergrund auf eine neuere Version. Wenn keine neue Version vorhanden ist, wird beim automatischen Check kein Fenster angezeigt. Unter **Einstellungen / Diagnose → Update prüfen** kann die Prüfung jederzeit manuell gestartet werden.

### Neue Version veröffentlichen

Für zukünftige Updates reicht grundsätzlich:
1. Neue Version und Installer erstellen.
2. Installer auf GitHub bereitstellen bzw. eine Release-Seite anlegen.
3. `version.json` auf die neue Versionsnummer, Downloadadresse und Release Notes aktualisieren.

Bereits installierte VR-Fitness-Versionen ab V11.12 erkennen das Update anschließend automatisch.

## Datenspeicherung

VR Fitness speichert Fitness- und Sessiondaten lokal auf dem jeweiligen PC. Onlinezugriff wird für die Updateprüfung und – je nach gewählten Datenquellen – für deren jeweilige Dienste verwendet.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE`.

## Status

Das Projekt befindet sich aktuell noch im Preview-/Testbetrieb. Vor allem neue Datenquellen und Android-/Health-Connect-Funktionen sollten vor breiter Nutzung weiter getestet werden.
