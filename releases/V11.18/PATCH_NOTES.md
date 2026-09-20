# VR Fitness V11.18 Preview

## Deutsch

- Neuer Tab **Einstellungen → Discord** für Discord Rich Presence.
- Optionale Anzeige von Puls, Session-Schritten, Distanz, geschätzten kcal und Sessionzeit. Die Anzeige verwendet dieselben Sessiondaten unabhängig von der gewählten Puls- und Bewegungsquelle.
- Discord und Pulsanzeige sind standardmäßig ausgeschaltet. Nur gespeicherte Einstellungen werden angewendet. Es werden keine Sessionnamen, Notizen, Zugangsdaten oder Rohdaten übertragen.
- Aktualisierung alle 15 Sekunden; Änderungen der Sichtbarkeit und Sessionende werden zeitnah übernommen. Veralteter oder fehlender Puls wird nicht angezeigt; bei ungültigem Pulssignal werden auch keine Live-kcal veröffentlicht.
- Aktivität wird standardmäßig beim Sessionende entfernt, ebenso beim Deaktivieren und Beenden. Optional bleibt nach Sessionende ein neutraler Hinweis ohne Fitnesswerte stehen.
- Lokale Kommunikation mit Discord Desktop in einem separaten Thread, automatische Wiederverbindung, eigene Discord-Diagnosemeldungen. Keine zusätzliche Python-Abhängigkeit und kein Discord-Token nötig.
- Diagnosefilter nach Quelle (inklusive Discord), Schweregrad und Suchtext. Bestehende Meldungen werden anhand ihrer Kategorien und Fehlermarker eingeordnet.
- Optionales Logo über den Namen eines in der Discord-Application hochgeladenen Rich-Presence-Assets.

### Einrichtung

1. V11.18 öffnen und **Einstellungen → Discord** wählen.
2. Die öffentliche VR-Fitness-Application-ID **1551173400385294349** ist voreingestellt. Eine eigene ID kann weiterhin eingetragen werden. Kein Bot-Token oder Client Secret nötig.
3. Gewünschte Werte auswählen, Discord-Aktivität aktivieren und **Speichern** drücken. Puls muss ausdrücklich eingeschaltet werden.
4. Discord Desktop öffnen und eine Session starten. Die Anzeige setzt erlaubte Aktivitätsfreigabe in Discord voraus.
5. Optional ein Logo bei dieser Application hochladen und dessen Assetnamen eintragen.

Die vom Projektinhaber bereitgestellte Application-ID ist enthalten. Discord und Puls bleiben standardmäßig ausgeschaltet. Bereits gespeicherte eigene IDs werden nicht überschrieben.

### Prüfung und Grenzen

- 10 automatisierte Tests: Auswahl/Privatsphäre, fehlende Werte/ID, 15-s-Intervall, Beenden, Wiederverbindung, Application-Wechsel, Sessionende während Verbindungsaufbau, Diagnosefilter, RPC-Framing und echter Windows-Named-Pipe-Austausch mit einem isolierten Testserver.
- Tk-Oberfläche, Einstellungen speichern und Diagnosefilter mit isolierter Konfiguration geprüft.
- Python-Syntax, ZIP-Integrität, Installer-Payload und `.LastIndexOf`-Fix geprüft; SHA-256 in `SHA256SUMS.txt`.
- Noch kein End-to-End-Test mit einer registrierten Discord-Application oder einer tatsächlich sichtbaren Discord-Aktivität. Installer wurde statisch geprüft, nicht auf einem frischen Windows installiert.
- Die bisherige kcal-Schätzformel bleibt unverändert. Android bleibt auf V1.6.2.

## English

V11.18 adds optional Discord Rich Presence with individually selected session heart rate, steps, distance, estimated calories and elapsed time. Discord sharing and heart-rate sharing default to off. Settings are saved explicitly; no names, notes, tokens or raw samples are shared. Updates run every 15 seconds outside the UI thread, with automatic reconnection and prompt clearing at session end, disable and exit. Stale heart rate and related live calorie estimates are omitted.

Diagnostics now support source, severity and text filters. The public VR Fitness Application ID 1551173400385294349 is preconfigured; the desktop client is required. An optional uploaded logo asset key can be configured. Ten automated checks and an isolated Tk smoke check pass. Real Discord-profile behavior and clean-machine installation still require manual validation. Android and calorie-estimation logic are unchanged.

Protocol reference: [Discord RPC documentation](https://github.com/discord/discord-rpc/blob/master/documentation/hard-mode.md).
