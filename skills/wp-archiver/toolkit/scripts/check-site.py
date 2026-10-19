#!/usr/bin/env python
"""Asset-integrity check for the static site: every local reference must resolve to a file in site/.

    python scripts/check-site.py [site]

Reads HTML (href/src/srcset/poster/data-*, inline url()), CSS (url(), @import) and the root-relative URLs hidden in
JSON/JS strings, resolves each against site/ the way Cloudflare would (clean URLs -> index.html), and lists:
  - MISSING   local references with no file behind them (broken images/links/assets)
  - EXTERNAL  third-party hosts the pages load resources from (informational)
Exit code 1 if anything is MISSING. This is the "link/asset integrity" validator from decisions.md.
"""
import html
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

SITE = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
ATTR = re.compile(r"""(?:href|src|data-src|data-lazy-src|poster)\s*=\s*["']([^"']+)["']""", re.I)
SRCSET = re.compile(r"""(?:srcset|data-srcset)\s*=\s*["']([^"']+)["']""", re.I)
CSSURL = re.compile(r"""url\(\s*["']?([^"')]+)""")
IMPORT = re.compile(r"""@import\s+["']([^"']+)""")
JSONPATH = re.compile(r"""["']((?:\\?/)wp-(?:content|includes)(?:\\?/)[^"'\s<>\\]*(?:\\/[^"'\s<>\\]*)*)""")
# Things that are not files on disk by design.
IGNORE = re.compile(r"^(data:|mailto:|tel:|javascript:|#|about:|blob:)")
DIR_ONLY = {"/wp-content/plugins/elementor/assets/", "/wp-content/uploads", "/wp-content/uploads/"}  # JS config base URLs


def exists(path):
    p = urllib.parse.unquote(urllib.parse.urlsplit(path).path)
    if p in DIR_ONLY:
        return True
    f = SITE / p.lstrip("/")
    return f.is_file() or (f.is_dir() and (f / "index.html").is_file()) or (not f.suffix and (f.parent / (f.name) / "index.html").is_file())


def refs(text, base_dir, kind):
    out = set()
    t = text.replace("\\/", "/")
    if kind == "html":
        for rx in (ATTR,):
            for m in rx.finditer(text):
                out.add(m.group(1))
        for m in SRCSET.finditer(text):
            for cand in m.group(1).split(","):
                if cand.strip():
                    out.add(cand.strip().split()[0])
    if kind in ("html", "css"):
        out.update(CSSURL.findall(html.unescape(text)))
        out.update(IMPORT.findall(text))
    for m in JSONPATH.finditer(text):
        out.add(m.group(1).replace("\\/", "/"))
    res = []
    for r in out:
        r = html.unescape(r.strip())
        if not r or IGNORE.match(r) or r.startswith("//") or re.search(r"[*{}$<>\s,]", r):  # globs, templates, prose
            continue
        if re.match(r"https?://", r):
            res.append(("EXTERNAL", r))
            continue
        full = urllib.parse.urljoin("/" + base_dir.as_posix().lstrip("./") + "/", r) if not r.startswith("/") else r
        res.append(("LOCAL", full))
    return res


def main():
    missing, external, checked = [], Counter(), 0
    for f in sorted(SITE.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in (".html", ".css"):
            continue
        kind = "html" if f.suffix.lower() == ".html" else "css"
        base = f.parent.relative_to(SITE)
        text = f.read_text(encoding="utf-8", errors="replace")
        for tag, ref in refs(text, base, kind):
            if tag == "EXTERNAL":
                external[urllib.parse.urlsplit(ref).netloc] += 1
            else:
                checked += 1
                if not exists(ref):
                    missing.append((f.relative_to(SITE).as_posix(), ref))
    print(f"checked {checked} local references in {SITE.name}/")
    seen = set()
    for src, ref in missing:
        if (src, ref) not in seen:
            seen.add((src, ref))
            print(f"MISSING  {ref}   (in {src})")
    print(f"{len(seen)} missing")
    resource_hosts = {h: n for h, n in external.items() if any(k in h for k in ("fonts.", "gravatar", "cdn", "gstatic", "googleapis"))}
    print("third-party resource hosts:", dict(resource_hosts) or "none")
    return 1 if seen else 0


if __name__ == "__main__":
    sys.exit(main())
