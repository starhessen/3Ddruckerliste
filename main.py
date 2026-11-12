from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATEI = Path("auftraege.json")
FERTIGE_AUFTRAEGE_BIS_LOESCHUNG = 3


class Druckerque:
    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def get_jobs(self):
        if self.printer_busy():
            return None

        for job in self.jobs:
            if job['status'] == 'Wartend':
                job['status'] = 'Wird gedruckt'
                return job
        return None

    def printer_busy(self):
        return any(job['status'] == 'Wird gedruckt' for job in self.jobs)

    def finish_job(self):
        for job in self.jobs:
            if job['status'] == 'Wird gedruckt':
                job['status'] = 'Fertig'
                fertige_auftraege = [
                    job for job in self.jobs if job['status'] == 'Fertig'
                ]
                if len(fertige_auftraege) >= FERTIGE_AUFTRAEGE_BIS_LOESCHUNG:
                    self.jobs = [
                        job for job in self.jobs if job['status'] != 'Fertig'
                    ]
                    return job, len(fertige_auftraege)
                return job, 0
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


HTML = Path(__file__).with_name("frontend.html").read_text(encoding="utf-8")
HTML_V2 = Path(__file__).with_name("frontend2.html").read_text(encoding="utf-8")


class AppHandler(BaseHTTPRequestHandler):
    druckerque = Druckerque()
    job_number = 1
    count = 0

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/":
            self.send_error(404)
            return
        version = parse_qs(parsed_url.query).get("version", ["1"])[0]
        page = HTML_V2 if version == "2" else HTML
        content = page.encode("utf-8")
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
            if AppHandler.druckerque.printer_busy():
                message = "Der Drucker ist besetzt."
                auftrag = None
            else:
                auftrag = AppHandler.druckerque.get_jobs()

            if auftrag is None and not AppHandler.druckerque.printer_busy():
                message = "Keine offenen Aufträge vorhanden."
            elif auftrag is not None:
                message = (
                    f"Auftrag {auftrag['nummer']} "
                    f"'{auftrag['name']}' wird jetzt gedruckt."
                )

        elif action == "finish":
            ergebnis = AppHandler.druckerque.finish_job()

            if ergebnis is None:
                message = "Es läuft gerade kein Auftrag."
            else:
                auftrag, geloeschte_anzahl = ergebnis
                message = (
                    f"Auftrag {auftrag['nummer']} "
                    f"'{auftrag['name']}' ist fertig."
                )
                if geloeschte_anzahl:
                    message += (
                        f" {geloeschte_anzahl} fertige Aufträge "
                        "wurden aus der Liste gelöscht."
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
