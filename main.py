from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlparse


HTML = """<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Meine Python-Oberflaeche</title>
    <style>
        :root {
            color-scheme: light;
            font-family: system-ui, sans-serif;
            background: #eef4f7;
            color: #173042;
        }
        body {
            display: grid;
            place-items: center;
            min-height: 100vh;
            margin: 0;
        }
        main {
            width: min(680px, calc(100% - 32px));
            padding: 32px;
            background: white;
            border: 1px solid #d5e0e6;
            border-radius: 16px;
            box-shadow: 0 16px 40px #17304218;
        }
        h1 { margin-top: 0; }
        .buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin: 24px 0;
        }
        button {
            padding: 14px 16px;
            border: 0;
            border-radius: 10px;
            background: #167d9a;
            color: white;
            font-size: 1rem;
            cursor: pointer;
        }
        button:hover { background: #12677e; }
        #status {
            min-height: 24px;
            padding: 14px;
            border-radius: 10px;
            background: #edf6f8;
        }
    </style>
</head>
<body>
    <main>
        <h1>Meine Python-Oberflaeche</h1>
        <p>Klicke auf einen Button. Jede Aktion wird von Python verarbeitet.</p>
        <div class="buttons">
            <button data-action="hello">Sag Hallo</button>
            <button data-action="time">Zeige die Uhrzeit</button>
            <button data-action="count">Zaehler erhoehen</button>
        </div>
        <p id="status">Bereit.</p>
    </main>
    <script>
        const status = document.querySelector('#status');
        document.querySelectorAll('button').forEach((button) => {
            button.addEventListener('click', async () => {
                status.textContent = 'Wird verarbeitet ...';
                const response = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: button.dataset.action})
                });
                const result = await response.json();
                status.textContent = result.message;
            });
        });
    </script>
</body>
</html>"""


class AppHandler(BaseHTTPRequestHandler):
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

        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            action = data.get("action")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Ungueltige Daten")
            return

        if action == "hello":
            message = "Hallo! Diese Nachricht kommt aus Python."
        elif action == "time":
            from datetime import datetime
            message = f"Es ist {datetime.now():%H:%M:%S} Uhr."
        elif action == "count":
            AppHandler.count += 1
            message = f"Der Zaehler steht auf {AppHandler.count}."
        else:
            self.send_error(400, "Unbekannte Aktion")
            return

        content = json.dumps({"message": message}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8000), AppHandler)
    print("Oberflaeche gestartet: http://127.0.0.1:8000")
    print("Beenden mit Strg+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
