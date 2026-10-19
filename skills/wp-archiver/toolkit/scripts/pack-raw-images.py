#!/usr/bin/env python
"""Pack the unprocessed media library into one reproducible zip (the "raw mirror") plus a checksum manifest.

    python scripts/pack-raw-images.py            # -> raw/images-raw.zip + raw/images-raw.manifest.txt
    python scripts/pack-raw-images.py --verify   # check the zip against the manifest

Why: the optimiser (scripts/optimize_images.py) replaces images in site/ with smaller WebP files, and
wp/uploads is not tracked. This zip keeps every original byte so the optimisation is always reversible or
re-runnable with other settings. Run it BEFORE optimising.

Reproducible: entries sorted, fixed timestamps, so unchanged inputs give a byte-identical zip (git LFS then
stores it once). raw/*.zip is tracked through Git LFS (see .gitattributes).
"""
import hashlib
import sys
import zipfile
from pathlib import Path

from _env import ROOT, env

SRC = ROOT / "wp" / "uploads"
OUT = ROOT / "raw"
ZIP = OUT / "images-raw.zip"
MANIFEST = OUT / "images-raw.manifest.txt"
STAMP = (2020, 1, 1, 0, 0, 0)  # fixed, so the zip is byte-reproducible


def files():
    # The media library: the dated year/month folders. Generated caches (elementor/, fonts) are excluded.
    for year in sorted(p for p in SRC.iterdir() if p.is_dir() and p.name.isdigit()):
        for f in sorted(year.rglob("*")):
            if f.is_file():
                yield f


def sha(path_or_bytes):
    h = hashlib.sha256()
    if isinstance(path_or_bytes, Path):
        with path_or_bytes.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    else:
        h.update(path_or_bytes)
    return h.hexdigest()


def pack():
    OUT.mkdir(exist_ok=True)
    lines, total = [], 0
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in files():
            rel = f.relative_to(SRC).as_posix()
            data = f.read_bytes()
            zi = zipfile.ZipInfo(rel, STAMP)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data, compresslevel=6)
            lines.append(f"{sha(data)}  {len(data):>9}  {rel}")
            total += len(data)
    header = [
        f"# Raw (unprocessed) media library of {env('COMPOSE_PROJECT_NAME', 'this site')}, as downloaded from the original host.",
        "# sha256  bytes  path-inside-zip (relative to wp-content/uploads/). Verify: scripts/pack-raw-images.py --verify",
        f"# {len(lines)} files, {total} bytes uncompressed",
    ]
    MANIFEST.write_text("\n".join(header + lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(lines)} files, {total/1048576:.1f} MB raw -> {ZIP.name} {ZIP.stat().st_size/1048576:.1f} MB (sha256 {sha(ZIP)[:16]}...)")


def verify():
    want = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            digest, _size, rel = line.split(None, 2)
            want[rel] = digest
    bad = 0
    with zipfile.ZipFile(ZIP) as z:
        names = set(z.namelist())
        for rel, digest in want.items():
            if rel not in names or sha(z.read(rel)) != digest:
                bad += 1
                print("MISMATCH", rel)
    extra = names - set(want)
    print(f"verified {len(want)} files, {bad} bad, {len(extra)} unlisted")
    return 1 if bad or extra else 0


if __name__ == "__main__":
    sys.exit(verify() if "--verify" in sys.argv else pack())
