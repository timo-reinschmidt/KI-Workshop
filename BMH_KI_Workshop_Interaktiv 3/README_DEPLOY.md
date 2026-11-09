# BMH KI-Workshop – Version 3

## Online auf Render (Free)

Das Repository soll diese Struktur behalten:

```
KI-Workshop/
  BMH_KI_Workshop_Interaktiv/
    render.yaml
    ki_workshop.py
    fragen.json
    assets/
    vendor/
```

Blueprint Path: `BMH_KI_Workshop_Interaktiv/render.yaml`.
Die Blueprint-Datei setzt `rootDir: BMH_KI_Workshop_Interaktiv`.

**Achtung bei Updates:** Bestehende Dateien im gleichnamigen GitHub-Ordner durch die Dateien dieser ZIP ersetzen; nicht den Ordner in sich selbst verschachteln. `render.yaml` ebenfalls ersetzen. Vor dem Workshop in Render unter Environment einen selbst gewählten, starken `ADMIN_KEY` setzen (nicht in GitHub hinterlegen). Für Render Free ist `PUBLIC_URL=https://bmh-ki-workshop.onrender.com` konfiguriert.

Moderation: `https://bmh-ki-workshop.onrender.com/moderation?key=DEIN_ADMIN_KEY`
Teilnahme: `https://bmh-ki-workshop.onrender.com/`

## Ablauf

1. Alle 11 Personen scannen den QR-Code und wählen einen eindeutigen Spitznamen.
2. Teil 1: 10 Runden „KI oder Mensch?“ (2 KI-Bilder und 8 Texte). Die Inhalte erscheinen auf dem Beamer und auf Smartphones.
3. Teil 2: Warm-up (5 Fragen), ohne Punkte.
4. Teil 3: Einsatzmöglichkeiten bei BMH (3 Fragen), ohne Punkte.
5. Teil 4: 7 Praxisfälle „Grün, Gelb oder Rot?“, mit Punkten.
6. Moderator schliesst Abstimmung und klickt „Lösung aufdecken“. Erst dadurch werden Punkte gutgeschrieben (100 pro richtige Antwort, einmal pro Frage). Die Rangliste erscheint in der Seitenleiste und auf Smartphones nach der Auflösung.
7. Gesamtauswertung öffnen und CSV exportieren.

## Inhalt / Quellenhinweise

Die beiden Quizbilder stammen aus KI-generierten Illustrationen, die eigens für dieses Projekt erstellt wurden. Die als „Mensch“ bezeichneten Textauszüge sind klassische gemeinfreie Literatur (Kafka, Goethe, Fontane, Schiller); die übrigen Texte wurden für das Quiz KI-generiert. Die Bildauswahl enthält in dieser Version **keine echten Fotos**. Bitte vor dem Workshop die Inhalte und gewünschte Schwierigkeitsstufe prüfen. Die KI-Bilder sind bewusst nicht als echte Fotografien ausgegeben.

## Einschränkungen der kostenlosen Version

- Abstimmungen, Spitznamen und Punkte liegen nur im RAM des Render-Prozesses. Nach einem Neustart/Spin-down gehen sie verloren. Vor der Schulung den Dienst aufwecken und während der Veranstaltung offen halten; Ergebnisse am Schluss sofort exportieren. Der CSV-Export enthält aggregierte Antworten, nicht alle einzelnen Punktestände.
- Die Rangliste ist im Workshop sichtbar, Antworten aus den unbewerteten Umfragen werden nur aggregiert dargestellt.
- Moderationsschlüssel vertraulich halten. Keine echten Gästedaten, Personaldaten oder internen vertraulichen Dokumente in die Freitextfragen eingeben.
- Kein öffentliches Produktivsystem; für wiederholten Betrieb mit Persistenz eine externe Datenbank vorsehen.

## Lokal auf Mac / Windows

`python3 ki_workshop.py` oder die beiliegenden Startskripte. Browser: `http://127.0.0.1:8765`. Für Smartphones muss der Rechner im Netzwerk erreichbar sein.
