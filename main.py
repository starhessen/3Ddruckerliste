from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

DATEI = Path("auftraege.json")


class Druckerque:
    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def get_jobs(self):
        for job in self.jobs:
            if job['status'] == 'Wartend':
                job['status'] = 'Wird gedruckt'
                return job
        return None

    def finish_job(self):
        for job in self.jobs:
            if job['status'] == 'Wird gedruckt':
                job['status'] = 'Fertig'
                return job
        return None

    def show_jobs(self):
        return self.jobs

    def save(self):
        DATEI.write_text(
            json.dumps(self.jobs, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def load(self):
        if not DATEI.exists():
            return

        try:
            jobs = json.loads(DATEI.read_text(encoding="utf-8"))
            if not isinstance(jobs, list):
                raise ValueError("Die Datei muss eine Liste enthalten.")
            status_uebersetzung = {
                "pending": "Wartend",
                "printing": "Wird gedruckt",
                "completed": "Fertig",
            }
            for job in jobs:
                job["status"] = status_uebersetzung.get(
                    job.get("status"), job.get("status")
                )
            self.jobs = jobs
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"Warnung: Aufträge konnten nicht geladen werden: {error}")
            self.jobs = []


HTML = """<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Meine Python-Oberflaeche</title>
    <style>
        :root {
            color-scheme: light;
            font-family: Arial, sans-serif;
            background: #f2f2f2;
            color: #222;
        }
        body {
            min-height: 100vh;
            margin: 0;
            background: #f2f2f2;
        }
        main {
            width: min(700px, calc(100% - 32px));
            margin: 32px auto;
            padding: 24px;
            background: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            box-shadow: 0 2px 8px #00000018;
        }
        h1 { margin: 0 0 8px; font-size: 1.8rem; }
        .intro { margin-top: 0; color: #555; }
        .form-area {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 12px;
            margin: 24px 0 12px;
        }
        input {
            min-width: 0;
            padding: 14px 16px;
            border: 1px solid #aaa;
            border-radius: 4px;
            color: #222;
            font: inherit;
        }
        input:focus { outline: 2px solid #9bbbd3; border-color: #477ea5; }
        .buttons {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        button {
            padding: 14px 16px;
            border: 1px solid #477ea5;
            border-radius: 4px;
            background: #477ea5;
            color: white;
            font-size: 1rem;
            cursor: pointer;
        }
        button:hover { background: #356789; }
        button.secondary { background: #eee; color: #333; border-color: #aaa; }
        button.secondary:hover { background: #ddd; }
        #status {
            min-height: 24px;
            margin: 20px 0 0;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #f7f7f7;
        }
        .section-title {
            margin: 28px 0 10px;
            font-size: 1.1rem;
        }
        #queue {
            display: grid;
            gap: 8px;
        }
        .job {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #fafafa;
        }
        .job-name { font-weight: 700; }
        .job-status { color: #555; font-size: .9rem; }
        @media (max-width: 600px) {
            main { margin: 16px auto; }
            .form-area, .buttons { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <main>
        <h1>Meine Python-3D-Drucker</h1>
        <p class="intro">Druckaufträge hinzufügen und in der richtigen Reihenfolge starten.</p>
        <div class="form-area">
            <input type="text" id="input_data" placeholder="Zum Beispiel: Gehäuse drucken" aria-label="Auftragsname">
            <button data-action="add">+ Auftrag hinzufügen</button>
        </div>
        <div class="buttons">
            <button data-action="start">Nächsten Auftrag starten</button>
            <button data-action="finish">Auftrag fertig</button>
            <button class="secondary" data-action="show">Warteschlange aktualisieren</button>
        </div>
        <p id="status" aria-live="polite">Bereit. Noch keine Aktion ausgeführt.</p>
        <h2 class="section-title">Aktuelle Aufträge</h2>
        <div id="queue"><p>Noch keine Aufträge vorhanden.</p></div>
    </main>
    <script>
        const status = document.querySelector('#status');
        const input = document.querySelector('#input_data');
        const queue = document.querySelector('#queue');

        function showJobs(message) {
            if (message === 'Keine Aufträge vorhanden.') {
                queue.innerHTML = '<p>Noch keine Aufträge vorhanden.</p>';
                return;
            }

            const jobs = message.split(' | ');
            queue.innerHTML = jobs.map((job) => {
                const match = job.match(/^(\\d+): (.+) \\((.+)\\)$/);
                if (!match) return `<div class="job"><span>${job}</span></div>`;
                return `<div class="job"><span class="job-name">#${match[1]} ${match[2]}</span><span class="job-status">${match[3]}</span></div>`;
            }).join('');
        }

        async function loadJobs() {
            const response = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'show'})
            });
            const result = await response.json();
            showJobs(result.message);
        }

        document.querySelectorAll('button').forEach((button) => {
            button.addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/action', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({action: button.dataset.action, input_data: input.value})
                    });
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.message || 'Anfrage fehlgeschlagen');
                    if (button.dataset.action === 'add') input.value = '';
                    if (button.dataset.action === 'show' || button.dataset.action === 'start' || button.dataset.action === 'finish') showJobs(result.message);
                    if (button.dataset.action === 'add') {
                        document.querySelector('[data-action="show"]').click();
                    }
                } catch (error) {
                    status.textContent = error.message;
                }
            });
        });

        loadJobs();
    </script>
</body>
</html>"""


class AppHandler(BaseHTTPRequestHandler):
    druckerque = Druckerque()
    job_number = 1
    count = 0

    def do_GET(self):
        if urlparse(self.path).path != "/":
            self.send_error(404)
            return
        content = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if urlparse(self.path).path != "/api/action":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            action = data.get("action")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Ungültige Eingabe")
            return

        if action == "add":
            input_data = data.get("input_data", "").strip()

            if not input_data:
                self.send_error(400, "Bitte einen Auftragsnamen eingeben")
                return

            auftrag = {
                "nummer": AppHandler.job_number,
                "name": input_data,
                "status": "Wartend"
            }
            AppHandler.druckerque.add_job(auftrag)
            AppHandler.job_number += 1
            message = (
                f"Auftrag {auftrag['nummer']} "
                f"'{auftrag['name']}' wurde hinzugefügt."
            )

        elif action == "start":
            auftrag = AppHandler.druckerque.get_jobs()

            if auftrag is None:
                message = "Keine offenen Aufträge vorhanden."
            else:
                message = (
                    f"Auftrag {auftrag['nummer']} "
                    f"'{auftrag['name']}' wird jetzt gedruckt."
                )

        elif action == "finish":
            auftrag = AppHandler.druckerque.finish_job()

            if auftrag is None:
                message = "Es läuft gerade kein Auftrag."
            else:
                message = (
                    f"Auftrag {auftrag['nummer']} "
                    f"'{auftrag['name']}' ist fertig."
                )

        elif action == "show":
            auftraege = AppHandler.druckerque.show_jobs()

            if not auftraege:
                message = "Keine Aufträge vorhanden."
            else:
                message = " | ".join(
                    f"{auftrag['nummer']}: {auftrag['name']} "
                    f"({auftrag['status']})"
                    for auftrag in auftraege
                )

        else:
            self.send_error(400, "Unbekannte Aktion")
            return

        if action != "show":
            AppHandler.druckerque.save()

        content = json.dumps({"message": message}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


def main():
    AppHandler.druckerque.load()
    if AppHandler.druckerque.jobs:
        AppHandler.job_number = max(
            job["nummer"] for job in AppHandler.druckerque.jobs
        ) + 1

    server = ThreadingHTTPServer(("127.0.0.1", 8000), AppHandler)
    print("Oberflaeche gestartet: http://127.0.0.1:8000")
    print("Beenden mit Strg+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
