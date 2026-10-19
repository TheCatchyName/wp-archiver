#!/usr/bin/env python
"""Full-page screenshots of every published URL (headless Chrome/Edge) plus a pixel diff.

    python scripts/visual.py shot baseline        # before changing anything
    python scripts/visual.py shot pruned-1
    python scripts/visual.py diff baseline pruned-1

Companion to snapshot.sh / diff-snapshots.sh: the HTML diff says *what markup* changed, this says
whether anything *looks* different. URLs come from .data/snapshots/<label>.urls (written by
snapshot.sh; a missing one falls back to baseline.urls). Output is under .data/snapshots/ (gitignored).
"""
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / ".data" / "snapshots"
WIDTH = 1280
# Must exceed the tallest page (measure real heights first: VIS-1); Chrome caps screenshots at 16384. Override: SHOT_HEIGHT=12000
HEIGHT = int(os.environ.get("SHOT_HEIGHT", "10000"))
# How long Chrome waits before the shot. The slow WordPress server needs the plain timeout (virtual time hangs
# on it); the instant static server needs virtual time, or the shot lands mid-way through the page builder's JS init.
CAPTURE = (["--virtual-time-budget=15000"] if os.environ.get("CAPTURE") == "vtb" else ["--timeout=20000"])
BROWSERS = [  # first hit wins; override with BROWSER=/path/to/chrome
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
BROWSER_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "chrome"]


def browser() -> str:
    if os.environ.get("BROWSER"):
        return os.environ["BROWSER"]
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    for name in BROWSER_NAMES:
        if shutil.which(name):
            return shutil.which(name)
    sys.exit("no Chrome/Edge found; set BROWSER=/path/to/chrome or edit BROWSERS in scripts/visual.py")


def kill_tree(proc) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # started in its own session below
        except ProcessLookupError:
            pass


def slug(url: str) -> str:
    n = re.sub(r"^http://localhost(:\d+)?/?", "", url).strip("/").replace("/", "_")  # the origin is always local
    return n or "home"


def urls_for(label: str) -> list[str]:
    for name in (label, "baseline"):
        f = SNAP / f"{name}.urls"
        if f.exists():
            # SITE_ORIGIN=http://localhost:9090 re-points the same page list at another server (e.g. the static site)
            origin = os.environ.get("SITE_ORIGIN", "http://localhost")
            return [origin + u[len("http://localhost"):] for u in f.read_text().split() if u.startswith("http://localhost")]
    sys.exit(f"no URL list for {label}; run scripts/snapshot.sh {label} first")


def shoot(url: str, out: Path) -> str:
    """Headless Chrome sometimes writes the PNG but never exits on very tall pages: on timeout kill the
    whole process tree and accept the file if it was written."""
    out.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        proc = subprocess.Popen(
            [browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
             f"--user-data-dir={profile}", f"--window-size={WIDTH},{HEIGHT}",
             *CAPTURE, f"--screenshot={out}", url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=(os.name != "nt"))
        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            kill_tree(proc)
    ok = out.exists() and out.stat().st_size > 0
    note = ""
    if ok:  # a page taller than the window would be silently cut off: the bottom rows must be plain background
        with Image.open(out) as im:
            if im.convert("RGB").crop((0, im.height - 50, im.width, im.height)).getcolors(maxcolors=1) is None:
                note = f"  WARNING: bottom rows not uniform -- page may be taller than {HEIGHT}px, raise HEIGHT"
    return f"{'ok ' if ok else 'FAIL'} {out.name}{note}"


def cmd_shot(label: str, only: list[str]) -> None:
    out_dir = SNAP / f"{label}-png"
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(u, out_dir / f"{slug(u)}.png") for u in urls_for(label) if not only or slug(u) in only]
    with ThreadPoolExecutor(max_workers=int(os.environ.get('SHOT_WORKERS', '3'))) as ex:
        for line in ex.map(lambda j: shoot(*j), jobs):
            print(line)


def cmd_diff(a: str, b: str) -> None:
    da, db = SNAP / f"{a}-png", SNAP / f"{b}-png"
    out = SNAP / f"{b}-vs-{a}-diff"
    out.mkdir(parents=True, exist_ok=True)
    worst = 0.0
    for fa in sorted(da.glob("*.png")):
        fb = db / fa.name
        if not fb.exists():
            if len(list(db.glob("*.png"))) == len(list(da.glob("*.png"))):
                print(f"MISSING in {b}: {fa.name}")
            continue  # a partial (filtered) shot set only compares the pages it has
        ia, ib = Image.open(fa).convert("RGB"), Image.open(fb).convert("RGB")
        if ia.size != ib.size:
            print(f"{'SIZE':>8}  {fa.name}  {ia.size} vs {ib.size}")
            continue
        diff = ImageChops.difference(ia, ib).convert("L").point(lambda p: 255 if p > 24 else 0)
        n = diff.histogram()[255]
        pct = 100.0 * n / (ia.size[0] * ia.size[1])
        worst = max(worst, pct)
        bbox = diff.getbbox()
        print(f"{pct:7.3f}%  {fa.name}  bbox={bbox}")
        if n:
            diff.save(out / fa.name)
    print(f"worst page: {worst:.3f}% of pixels differ (diff masks in {out})")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "shot":
        cmd_shot(a[1], a[2:])  # optional page slugs, e.g.: shot try1 about contact
    elif len(a) == 3 and a[0] == "diff":
        cmd_diff(a[1], a[2])
    else:
        sys.exit(__doc__)
