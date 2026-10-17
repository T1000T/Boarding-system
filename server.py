#!/usr/bin/env python3
"""Tiny local server: serves index.html and uses data.json (next to this file) as the database."""
import json, os, sys, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data.json")
PAGE = os.path.join(ROOT, "index.html")

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(PAGE, "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/data":
            if os.path.exists(DATA):
                with open(DATA, "rb") as f:
                    self._send(200, f.read())
            else:
                self._send(200, b"null")  # no file yet: the app starts empty and creates it on first save
        else:
            self._send(404, b"{}")

    def do_PUT(self):
        if self.path.split("?")[0] != "/api/data":
            return self._send(404, b"{}")
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            obj = json.loads(raw)
        except ValueError:
            return self._send(400, b'{"error":"invalid json"}')
        fd, tmp = tempfile.mkstemp(dir=ROOT, suffix=".tmp")  # atomic write: never leaves a half-written file
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA)
        self._send(200, b'{"ok":true}')

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Open http://127.0.0.1:{port}   (data file: {DATA})")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
