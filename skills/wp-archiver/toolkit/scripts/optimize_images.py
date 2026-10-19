#!/usr/bin/env python
"""Optimise the media-library images in site/: WebP, at most 1080px wide, each file at most 200 KB.

    python scripts/optimize_images.py [--site site] [--max-width 1080] [--max-kb 200] [--dry-run]

Run AFTER scripts/export.py and scripts/pack-raw-images.py (the raw zip keeps every original byte).
Scaling only ever shrinks (never crops). Per image: auto-orient, downscale to the width cap, then try WebP at
falling quality (PNGs try lossless first) and, if even q40 is too big, shrink 10% at a time. An image whose WebP
would be larger than the original is left alone. Images used as CSS backgrounds (`url(...)` in CSS or inline
styles) are never resized -- they may be drawn at natural pixel size -- only recompressed. Every reference (HTML, CSS, JS, JSON; plain and JSON-escaped)
is rewritten to the new file name, and the old file is removed.
"""
import argparse
import io
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

QUALITIES = (82, 76, 70, 64, 58, 52, 46, 40)
TEXT_EXT = {".html", ".css", ".js", ".json", ".svg", ".xml", ".txt"}
RASTER = {".jpg", ".jpeg", ".png"}


def to_webp(im, max_bytes, lossless_first, allow_shrink=True):
    """Return (bytes, label, final_size). Shrinks the image only if quality alone cannot meet the budget."""
    def save(img, **kw):
        buf = io.BytesIO()
        img.save(buf, "WEBP", method=6, **kw)
        return buf.getvalue()

    if lossless_first:
        data = save(im, lossless=True)
        if len(data) <= max_bytes:
            return data, "lossless", im.size
    scale, cur = 1.0, im
    while True:
        for q in QUALITIES:
            data = save(cur, quality=q)
            if len(data) <= max_bytes:
                return data, f"q{q}" + (f" @{scale:.0%}" if scale < 1 else ""), cur.size
        if not allow_shrink:
            return data, "bg: q40, size kept (over budget)", cur.size
        if cur.width <= 320:
            return data, "OVER-BUDGET", cur.size
        scale *= 0.9
        cur = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)


def prepare(path, max_width, keep_dims=False):
    im = Image.open(path)
    if getattr(im, "n_frames", 1) > 1:
        return None, "animated"
    im = ImageOps.exif_transpose(im)
    if im.mode == "P" or "transparency" in im.info or im.mode in ("LA", "RGBA"):
        im = im.convert("RGBA")
        if im.getchannel("A").getextrema()[0] == 255:  # fully opaque: drop the alpha channel
            im = im.convert("RGB")
    elif im.mode != "RGB":
        im = im.convert("RGB")
    if im.width > max_width and not keep_dims:
        im = im.resize((max_width, round(im.height * max_width / im.width)), Image.LANCZOS)
    return im, None


BG_URL = re.compile(r"url\(\s*[\"']?(?:https?:)?[^)\"']*?(/wp-content/uploads/[^)\"']+?\.(?:jpe?g|png))", re.I)


def css_background_images(site):
    """Root-relative paths of uploads images referenced from url(...) anywhere in the site's HTML/CSS."""
    found = set()
    for f in site.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".html", ".css"):
            text = f.read_text(encoding="utf-8", errors="replace").replace("\\/", "/")
            found.update(BG_URL.findall(text))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="site")
    ap.add_argument("--max-width", type=int, default=1080)
    ap.add_argument("--max-kb", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    site = Path(a.site).resolve()
    uploads = site / "wp-content" / "uploads"
    max_bytes = a.max_kb * 1024

    backgrounds = css_background_images(site)
    mapping, before, after, rows = {}, 0, 0, []
    for src in sorted(p for p in uploads.rglob("*") if p.suffix.lower() in RASTER):
        orig = src.stat().st_size
        is_bg = "/" + src.relative_to(site).as_posix() in backgrounds
        im, why = prepare(src, a.max_width, keep_dims=is_bg)
        if im is None:
            rows.append((src, orig, orig, f"kept ({why})"))
            before += orig; after += orig
            continue
        data, label, size = to_webp(im, max_bytes, lossless_first=src.suffix.lower() == ".png", allow_shrink=not is_bg)
        if is_bg and "bg:" not in label:
            label += " (bg, size kept)"
        if len(data) >= orig and orig <= max_bytes and Image.open(src).width <= a.max_width:
            rows.append((src, orig, orig, "kept (webp not smaller)"))
            before += orig; after += orig
            continue
        dest = src.with_suffix(".webp")
        if dest.exists() and dest != src:  # x.jpg and x.png would both become x.webp
            dest = src.with_name(f"{src.stem}-{src.suffix.lstrip('.').lower()}.webp")
        rows.append((src, orig, len(data), f"{label} {size[0]}x{size[1]}"))
        before += orig; after += len(data)
        mapping["/" + src.relative_to(site).as_posix()] = "/" + dest.relative_to(site).as_posix()
        if not a.dry_run:
            dest.write_bytes(data)
            src.unlink()

    # rewrite every reference, plain and JSON-escaped
    n_files = 0
    if mapping and not a.dry_run:
        keys = sorted(mapping, key=len, reverse=True)
        pat = re.compile("(?:" + "|".join(re.escape(k) for k in keys) + r")(?![A-Za-z0-9_-])")
        pat_esc = re.compile("(?:" + "|".join(re.escape(k.replace("/", "\\/")) for k in keys) + r")(?![A-Za-z0-9_-])")
        for f in site.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in TEXT_EXT:
                continue
            t = f.read_text(encoding="utf-8", errors="replace")
            new = pat.sub(lambda m: mapping[m.group(0)], t)
            new = pat_esc.sub(lambda m: mapping[m.group(0).replace("\\/", "/")].replace("/", "\\/"), new)
            if new != t:
                f.write_text(new, encoding="utf-8", newline="")
                n_files += 1

    over = [r for r in rows if "OVER" in r[3]]
    print(f"{len(rows)} images: {before/1048576:.2f} MB -> {after/1048576:.2f} MB "
          f"({100*(1-after/max(before,1)):.0f}% smaller); references rewritten in {n_files} files")
    kept = [r for r in rows if r[3].startswith("kept")]
    n_bg = sum(1 for r in rows if '(bg' in r[3] or r[3].startswith('bg:'))
    print(f"CSS-background images (size kept): {n_bg}; kept as-is: {len(kept)}; over budget: {len(over)}; largest result: {max((r[2] for r in rows), default=0)/1024:.0f} KB")
    for src, o, n, note in sorted(rows, key=lambda r: -r[1])[:8]:
        print(f"  {o/1024:7.0f} KB -> {n/1024:6.0f} KB  {note:22s} {src.relative_to(site).as_posix()}")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
