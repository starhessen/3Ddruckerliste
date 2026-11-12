# Python-Oberflaeche

## Starten

1. Oeffne in VS Code ein Terminal in diesem Ordner.
2. Starte das Programm:

```powershell
python main.py
```

3. Oeffne im Browser: http://127.0.0.1:8000
4. Beende den Server im Terminal mit `Strg+C`.

Die Effekt-Version kann unter http://127.0.0.1:8000/?version=2 geöffnet werden.
In beiden Versionen gibt es einen Link zum Wechseln.

## Dateien

- `main.py` enthält den Server und die Queue.
- `frontend.html` enthält die Oberfläche, das Design und JavaScript.
- `frontend2.html` enthält die animierte Effekt-Version.
- `auftraege.json` speichert die Aufträge dauerhaft.

## Eigene Buttons

Die Buttons stehen in `frontend.html`. Eine neue Aktion braucht:

- einen neuen Button mit `data-action="mein_name"`
- einen passenden `elif action == "mein_name"`-Block in `do_POST`

Dort kann dann beliebiger Python-Code ausgefuehrt werden.
