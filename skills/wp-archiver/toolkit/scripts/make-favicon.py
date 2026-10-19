#!/usr/bin/env python
"""Generate the favicon set from the site logo into overlay/ (copied into site/ by scripts/export.py).

    python scripts/make-favicon.py <logo-path>

Source: the header logo from the media library (a small JPEG on pure white). The white is converted to real
transparency with a colour-to-alpha pass (anti-aliased edges stay clean), the mark is cropped, centred on a square
with a margin and upscaled. Outputs: favicon.ico (16/32/48), icon-192.png (transparent), apple-touch-icon.png
(180, white background: iOS does not do transparency). Re-run only when the logo changes.
"""
import sys
from pathlib import Path

from PIL import Image

from _env import ROOT

if len(sys.argv) < 2:
    sys.exit("usage: make-favicon.py <logo-file>   (e.g. wp/uploads/<year>/<month>/logo.png; find it in the header's <img class=custom-logo>)")
LOGO = Path(sys.argv[1])
OUT = ROOT / "overlay"
NOISE = 0.06  # alpha below this is JPEG noise on the white background, not logo


def color_to_alpha(img):
    """White background -> transparency. fg = white - (white - c) / alpha, alpha = distance from white."""
    src = img.convert("RGB")
    out = Image.new("RGBA", src.size)
    px, po = src.load(), out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b = px[x, y]
            a = max(255 - r, 255 - g, 255 - b) / 255.0
            if a < NOISE:
                po[x, y] = (0, 0, 0, 0)
                continue
            f = lambda c: max(0, min(255, round(255 - (255 - c) / a)))
            po[x, y] = (f(r), f(g), f(b), round(min(1.0, a * 1.15) * 255))  # slight boost keeps thin strokes solid
    return out


def square(img, size, margin=0.08):
    box = img.getbbox()
    mark = img.crop(box)
    inner = round(size * (1 - 2 * margin))
    scale = inner / max(mark.size)
    mark = mark.resize((max(1, round(mark.width * scale)), max(1, round(mark.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(mark, ((size - mark.width) // 2, (size - mark.height) // 2), mark)
    return canvas


def main():
    OUT.mkdir(exist_ok=True)
    mark = color_to_alpha(Image.open(LOGO))
    master = square(mark, 512)
    master.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    master.resize((192, 192), Image.LANCZOS).save(OUT / "icon-192.png", optimize=True)
    tile = Image.new("RGB", (180, 180), (255, 255, 255))
    small = square(mark, 180, margin=0.12)
    tile.paste(small, (0, 0), small)
    tile.save(OUT / "apple-touch-icon.png", optimize=True)
    for f in sorted(OUT.iterdir()):
        print(f"{f.name:22s} {f.stat().st_size/1024:6.1f} KB")


if __name__ == "__main__":
    main()
