"""Minimal Chrome DevTools Protocol client (stdlib only): just enough for one full-page screenshot.

    from _cdp import full_page_screenshot
    png_bytes, css_height, truncated = full_page_screenshot(chrome_exe, url, width=1280, viewport_height=800)

Why: `chrome --screenshot` can only capture the window. A page cannot be captured full-height that way without making
the window as tall as the page, which stretches every section sized in viewport units (`min-height: 90vh`, common in
page builders): the screenshot is then of a different layout than a visitor sees (VIS-8). Here the viewport stays at a
normal size (width x viewport_height), the real content height is measured, and the whole page is captured from the
surface without resizing the layout viewport.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

MAX_CAPTURE_HEIGHT = 16000  # Chrome's texture limit is 16384 px


class _WebSocket:
    def __init__(self, host, port, path, timeout=60):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("websocket handshake failed")
            buf += chunk
        head, _, self.buf = buf.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise ConnectionError("websocket upgrade refused: " + head.split(b"\r\n")[0].decode(errors="replace"))

    def _exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(max(65536, n - len(self.buf)))
            if not chunk:
                raise ConnectionError("websocket closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, text):
        data = text.encode()
        header = bytearray([0x81])
        n = len(data)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = os.urandom(4)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        message = b""
        while True:
            b1, b2 = self._exact(2)
            fin, op, n = b1 & 0x80, b1 & 0x0F, b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._exact(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._exact(8))[0]
            payload = self._exact(n)  # server-to-client frames are not masked
            if op == 8:
                raise ConnectionError("websocket closed by browser")
            if op in (0, 1, 2):
                message += payload
                if fin:
                    return message.decode("utf-8", "replace")


class Page:
    """One page target of a freshly launched headless browser."""

    def __init__(self, ws):
        self.ws, self.next_id, self.events = ws, 0, []

    def call(self, method, params=None, timeout=60):
        self.next_id += 1
        mid = self.next_id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
            if "method" in msg:
                self.events.append(msg["method"])
        raise TimeoutError(method)

    def wait_event(self, name, timeout=60):
        deadline = time.time() + timeout
        while name not in self.events and time.time() < deadline:
            msg = json.loads(self.ws.recv())
            if "method" in msg:
                self.events.append(msg["method"])
        return name in self.events

    def js(self, expression, timeout=120):
        r = self.call("Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True}, timeout)
        return r.get("result", {}).get("value")


def _launch(chrome, profile, width, height):
    proc = subprocess.Popen(
        [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--remote-debugging-port=0",
         f"--user-data-dir={profile}", f"--window-size={width},{height}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=(os.name != "nt"))
    port_file = Path(profile) / "DevToolsActivePort"
    for _ in range(100):
        if port_file.exists() and port_file.read_text().strip():
            return proc, int(port_file.read_text().splitlines()[0])
        time.sleep(0.2)
    raise TimeoutError("browser did not publish its DevTools port")


def _page_target(port):
    for _ in range(50):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10) as r:
            for t in json.load(r):
                if t.get("type") == "page":
                    return t["webSocketDebuggerUrl"]
        time.sleep(0.2)
    raise TimeoutError("no page target")


SCROLL_JS = """(async () => {
  const step = Math.max(200, Math.floor(window.innerHeight * 0.8));
  let y = 0;
  while (y < document.documentElement.scrollHeight) { window.scrollTo(0, y); y += step; await new Promise(r => setTimeout(r, 120)); }
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 300));
  return true;
})()"""


def full_page_screenshot(chrome, url, width=1280, viewport_height=800, settle=3.0, kill=None):
    """Return (png bytes, content height in CSS px, truncated?). `kill(proc)` is called to stop the browser tree."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        proc, port = _launch(chrome, profile, width, viewport_height)
        try:
            host_path = _page_target(port).split("://", 1)[1]
            hostport, _, path = host_path.partition("/")
            host, _, p = hostport.partition(":")
            page = Page(_WebSocket(host, int(p), "/" + path))
            page.call("Page.enable")
            page.call("Emulation.setDeviceMetricsOverride", {"width": width, "height": viewport_height, "deviceScaleFactor": 1, "mobile": False})
            page.call("Page.navigate", {"url": url})
            if not page.wait_event("Page.loadEventFired", 90):
                raise TimeoutError(f"page did not finish loading: {url}")
            time.sleep(settle)                       # let the page builder's JS initialise (VIS-4)
            page.js(SCROLL_JS)                       # trigger lazy-loaded images/sections, then return to the top
            time.sleep(1.0)
            height = int(page.js("Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)"))
            truncated = height > MAX_CAPTURE_HEIGHT
            clip_h = min(height, MAX_CAPTURE_HEIGHT)
            shot = page.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True, "fromSurface": True,
                                                        "clip": {"x": 0, "y": 0, "width": width, "height": clip_h, "scale": 1}}, timeout=120)
            return base64.b64decode(shot["data"]), height, truncated
        finally:
            if kill:
                kill(proc)
            else:
                proc.kill()
