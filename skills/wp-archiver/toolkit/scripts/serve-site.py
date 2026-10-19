#!/usr/bin/env python
"""Serve site/ roughly the way Cloudflare static assets does, and log every miss.

    python scripts/serve-site.py [port=9090] [dir=site]

- /about/ -> about/index.html, unknown paths -> 404.html with status 404, query strings ignored.
- Every 404 is appended to .data/export/404.log (path only): that list is what the crawler could not see
  (assets requested at runtime by JavaScript). Add them to scripts/export-extra-urls.txt and re-export.
- Port: avoid 8036-8535 on Windows (dynamic ranges reserved after reboots, ENV-1); 9090 is fine.
"""
import http.server
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9090
SITE = (ROOT / (sys.argv[2] if len(sys.argv) > 2 else "site")).resolve()
LOG = ROOT / ".data" / "export" / "404.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
LOG.write_text("")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            with LOG.open("a", encoding="utf-8") as f:
                f.write(self.path.split("?")[0] + "\n")
            page = SITE / "404.html"
            body = page.read_bytes() if page.exists() else b"404"
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().send_error(code, message, explain)

    def end_headers(self):
        self.send_header("X-Robots-Tag", "noindex, nofollow")
        super().end_headers()

    def log_message(self, fmt, *args):  # quiet
        pass


if __name__ == "__main__":
    print(f"serving {SITE} on http://localhost:{PORT}  (404s -> {LOG})", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
