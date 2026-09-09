# VR Fitness Android Companion

Android companion for VR Fitness / Android-Companion für VR Fitness.

**Current development version / Aktueller Entwicklungsstand: V1.6.2 Preview**

## Deutsch

Der Companion verbindet die Windows-App über das lokale Netzwerk mit Android Health Connect.

Aktueller Funktionsstand:
- Health-Connect-Schritte lesen
- aktuelles Gewicht lesen
- letzten verfügbaren SpO₂-Wert lesen
- VR-Fitness-Session nach Health Connect schreiben
- Herzfrequenz, Distanz, optional Schritte und geschätzte aktive kcal übertragen
- lokales Health-Connect-Übertragungslog mit Erfolg/Fehler
- PC-Empfänger nur im freigegebenen WLAN aktivieren
- Hintergrundaktualisierung über WorkManager

Aktuelle Patchnotes:

`android/releases/V1.6.2/PATCH_NOTES.md`

Der zuletzt bereitgestellte V1.6.2-Quellstand enthält außerdem den Build-Fix für die gemeldeten `LayoutParams`- und `ActivityCompat`-Compilerfehler.

Eine aktuelle APK sollte erst nach erfolgreichem Android-Studio-Build und Test auf einem echten Gerät veröffentlicht werden.

## English

The companion links the Windows app with Android Health Connect over the local network.

Current feature set:
- read Health Connect steps
- read current body weight
- read the latest available SpO₂ value
- write VR Fitness sessions to Health Connect
- write heart rate, distance, optional steps and estimated active kcal
- local Health Connect transfer log with success/error status
- restrict the PC receiver to an approved Wi-Fi network
- WorkManager background refresh

Current patch notes:

`android/releases/V1.6.2/PATCH_NOTES.md`

The latest V1.6.2 source package also contains the build fix for the reported `LayoutParams` and `ActivityCompat` compiler errors.

A current APK should only be published after a successful Android Studio build and real-device test.

## Verified release files / Geprüfte Release-Dateien

- [V1.6.2 source ZIP](releases/V1.6.2/VR_Fitness_Health_Companion_V1_6_2_WifiGuard_FIXED.zip)
- [V1.6.2 debug APK](releases/V1.6.2/VR_Fitness_Companion_V1_6_2_debug.apk)
- [SHA-256 checksums](releases/V1.6.2/SHA256SUMS.txt)

The APK is an existing local Android Studio debug build (versionName 1.6.2, versionCode 8, de.vrfitness.companion according to build metadata). Archive integrity was checked; installation and device behavior were not tested during publication. / Vorhandener lokaler Debug-Build; ZIP-Integrität geprüft, kein Gerätetest bei dieser Veröffentlichung.
