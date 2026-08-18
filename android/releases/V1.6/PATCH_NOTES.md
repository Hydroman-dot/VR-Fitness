# Android Companion V1.6 – Patch Notes

## Deutsch

### Neu
- Liest das aktuelle Gewicht aus Health Connect.
- Liest den letzten verfügbaren SpO₂-Wert aus Health Connect.
- `/status` liefert jetzt Schritte, Gewicht, SpO₂ und Zeitstempel.
- VR-Fitness-Sessions können geschätzte aktive Kalorien als `ActiveCaloriesBurnedRecord` schreiben.
- Herzfrequenz, Distanz, Schritte und Trainingssession bleiben Bestandteil der Synchronisierung.

### Hinweise
- SpO₂ und Gewicht werden nur angezeigt, wenn Health Connect passende Daten und Berechtigungen bereitstellt.
- Kalorien sind ein Schätzwert, kein medizinischer Messwert.
- Die App fordert zusätzliche Health-Connect-Berechtigungen für Gewicht, Sauerstoffsättigung und aktive Kalorien an.
- Vor Veröffentlichung bitte in Android Studio kompilieren und auf einem echten Gerät testen.

---

## English

### New
- Reads the latest body weight from Health Connect.
- Reads the latest available SpO₂ value from Health Connect.
- `/status` now returns steps, weight, SpO₂ and timestamps.
- VR Fitness sessions can write estimated active calories as `ActiveCaloriesBurnedRecord`.
- Heart rate, distance, steps and the exercise session remain part of synchronization.

### Notes
- Weight and SpO₂ are only shown when Health Connect contains the data and permissions are granted.
- Calories are an estimate, not a medical measurement.
- Additional Health Connect permissions are requested for weight, oxygen saturation and active calories.
- Compile in Android Studio and test on a real device before release.
