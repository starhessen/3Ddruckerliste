# Python-Oberflaeche

## Starten

1. Oeffne in VS Code ein Terminal in diesem Ordner.
2. Starte das Programm:

```powershell
python main.py
```

3. Oeffne im Browser: http://127.0.0.1:8000
4. Beende den Server im Terminal mit `Strg+C`.

## Eigene Buttons

Die Buttons stehen in `main.py` im HTML-Bereich. Eine neue Aktion braucht:

- einen neuen Button mit `data-action="mein_name"`
- einen passenden `elif action == "mein_name"`-Block in `do_POST`

Dort kann dann beliebiger Python-Code ausgefuehrt werden.
