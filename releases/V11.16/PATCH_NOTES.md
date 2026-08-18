# VR Fitness V11.16 Preview

## Deutsch

### Neu
- Health Connect Companion V1.6-Unterstützung.
- Anzeige des letzten SpO₂-Werts von Health Connect.
- Anzeige/Übernahme des aktuellen Gewichts aus Health Connect.
- Manuelles Gewicht als Fallback.
- Profilfelder für Alter und Geschlecht zur Kalorienschätzung.
- Geschätzte aktive Kalorien aus bereinigtem Pulsverlauf + Gewicht + Alter + Geschlecht.
- Kalorien können nach der Session an Health Connect übertragen werden.
- Pulsoid/VRCOSC/HypeRate-Pulsdaten werden für Health Connect auf ungefähr 15-Sekunden-Abstände reduziert; die lokale CSV bleibt vollständig.

### Kalorien
- Methode: Keytel et al. (2005), HR-basierte Schätzung ohne VO₂max.
- Der Wert ist ausdrücklich ein Schätzwert und kein medizinischer Messwert.
- Ohne verwertbares Gewicht, Alter, Geschlecht und Puls wird kein Kalorienwert geschrieben.

### Hinweise
- SpO₂ und Gewicht stammen nur aus Health Connect, wenn dort passende Messwerte vorhanden sind.
- Android V1.6 muss vor Veröffentlichung in Android Studio und auf einem echten Gerät getestet werden.
- `version.json` sollte erst nach erfolgreichem Test auf diese Version umgestellt werden.

---

## English

### New
- Health Connect Companion V1.6 support.
- Shows the latest SpO₂ value from Health Connect.
- Reads/displays the current Health Connect weight.
- Manual weight fallback.
- Profile age and sex fields for calorie estimation.
- Estimated active calories from cleaned heart-rate history + weight + age + sex.
- Estimated calories can be written to Health Connect after a session.
- HR data sent to Health Connect is reduced to roughly 15-second intervals; the local CSV keeps full resolution.

### Calories
- Method: Keytel et al. (2005), heart-rate-based estimate without VO₂max.
- This is explicitly an estimate, not a medical measurement.
- No calorie value is written when required inputs are missing.

### Notes
- Weight and SpO₂ only appear when Health Connect already contains those values.
- Android V1.6 should be compiled in Android Studio and tested on a real device before release.
- Do not switch `version.json` to this version until testing is complete.
