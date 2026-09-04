# Android Companion V1.6.2 – Patch Notes

## Deutsch

### Neu in V1.6.2
- PC-Empfänger standardmäßig nur im freigegebenen WLAN aktiv.
- Aktuelles WLAN kann direkt als erlaubte SSID gespeichert werden.
- Beim Verlassen des freigegebenen WLANs beendet sich der lokale PC-Empfänger automatisch.
- Fremdes WLAN, Mobilfunk oder kein WLAN: PC-Empfänger bleibt aus.
- Health Connect selbst bleibt davon unabhängig aktiv.
- WLAN-Status und Sperrgrund werden in der App angezeigt.
- Übertragungslog aus V1.6.1 bleibt enthalten.

### Neu in V1.6.1
- Sichtbares Health-Connect-Übertragungslog direkt in der Android-App.
- Zeigt pro Session Erfolg/Fehler, Sessionname, Distanz, Schritte, aktive kcal und Anzahl übertragener Puls-Samples.
- Fehlgeschlagene Health-Connect-Schreibvorgänge werden inklusive Fehlermeldung protokolliert.
- Log kann aktualisiert und gelöscht werden.
- Bis zu 100 Einträge werden lokal gespeichert.

### Health-Vitals aus V1.6
- Health-Connect-Schritte lesen.
- Aktuelles Gewicht lesen.
- Letzten verfügbaren SpO₂-Wert lesen.
- VR-Fitness-Sessions nach Health Connect schreiben.
- Herzfrequenz, Distanz, optional Schritte und geschätzte aktive kcal übertragen.

### Hinweise
- V1.6.2 bleibt Preview/Test.
- Der zuletzt bereitgestellte Quellstand enthält den Build-Fix für `LayoutParams` und `ActivityCompat`.
- Vor Veröffentlichung einer APK weiterhin in Android Studio bauen und auf einem echten Gerät testen.

---

## English

### New in V1.6.2
- PC receiver is restricted to the approved Wi-Fi network by default.
- The current Wi-Fi can be saved directly as the approved SSID.
- The local receiver stops automatically when the approved Wi-Fi is left.
- Other Wi-Fi, mobile data or no Wi-Fi: receiver stays off.
- Health Connect background functions remain independent.
- Wi-Fi status and block reason are shown in the app.
- The V1.6.1 transfer log remains included.

### New in V1.6.1
- Visible Health Connect transfer log in the Android app.
- Shows success/failure, session name, distance, steps, active kcal and HR sample count.
- Failed writes include the returned error message.
- The log can be refreshed and cleared.
- Up to 100 entries are stored locally.

### Health Vitals from V1.6
- Read Health Connect steps.
- Read current body weight.
- Read latest available SpO₂ value.
- Write VR Fitness sessions to Health Connect.
- Write heart rate, distance, optional steps and estimated active kcal.

### Notes
- V1.6.2 remains preview/testing.
- The latest source package includes the build fix for `LayoutParams` and `ActivityCompat`.
- Build in Android Studio and test on a real device before publishing an APK.
