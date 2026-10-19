#!/usr/bin/env python
"""Static export: crawl the local WordPress, write site/, rewrite URLs to root-relative, strip WP cruft.

    python scripts/export.py                 # crawl http://localhost -> site/   (use the venv's python)
    python scripts/export.py --out .data/export/crawl --origin http://localhost

Why a crawler rather than wget: query strings (?ver=1.2) become filenames on Windows and break MIME types,
wget does not follow URLs hidden in Elementor's JSON, and we need control over host rewriting.
Stdlib only. Per-site settings are FINAL_URL in .env, HEAD_STRIP/SKIP below, plus scripts/export-extra-urls.txt (assets that are
only requested at runtime by JavaScript; found by serving site/ and reading the 404 log).
"""
import argparse
import html
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _env import ROOT, env

FINAL = env("FINAL_URL").rstrip("/")  # .env FINAL_URL: where it will live (canonical/OG URLs only; links stay root-relative)
OVERLAY = ROOT / "overlay"  # files that exist only in the static build (favicon set); copied over the crawl


def icon_tags():
    """<link> tags for whichever icon files the overlay provides (see scripts/make-favicon.py)."""
    tags = []
    if (OVERLAY / "favicon.ico").exists():
        tags.append('<link rel="icon" href="/favicon.ico" sizes="48x48">')
    if (OVERLAY / "icon-192.png").exists():
        tags.append('<link rel="icon" type="image/png" href="/icon-192.png" sizes="192x192">')
    if (OVERLAY / "apple-touch-icon.png").exists():
        tags.append('<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
    return "\n".join(tags)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
# Never crawl: WordPress machinery that has no meaning on a static host.
SKIP = re.compile(r"(wp-json|xmlrpc\.php|/feed(/|$)|wp-login|wp-admin|wp-comments-post|/oembed/|/embed/?$|\.php$|[?&](p|s|replytocom|page_id|cat|tag|author)=)")
TEXT_EXT = {".html", ".css", ".js", ".json", ".svg", ".xml", ".txt"}

# WP head cruft that points at endpoints/hosts that will not exist.
HEAD_STRIP = [
    r"<meta name=[\"']generator[\"'][^>]*>",
    r"<link rel=[\"']https://api\.w\.org/[\"'][^>]*>",
    r"<link rel=[\"']EditURI[\"'][^>]*>",
    r"<link rel=[\"']shortlink[\"'][^>]*>",
    r"<link rel=[\"']pingback[\"'][^>]*>",
    r"<link rel=[\"']profile[\"'] href=[\"']https?://gmpg\.org/xfn/11[\"'][^>]*>",
    r"<link rel=[\"']alternate[\"'][^>]*(?:application/(?:json|rss\+xml)|oembed)[^>]*>",
    r"<link rel=[\"']alternate[\"'] title=[\"'](?:JSON|oEmbed)[^>]*>",
    r"<link rel=[\"']dns-prefetch[\"'] href=[\"']//s\.w\.org[\"'][^>]*>",
    r"<script[^>]*>\s*window\._wpemojiSettings[\s\S]*?</script>",
    r"<script type=[\"']module[\"']>[\s\S]*?_wpemojiSettings[\s\S]*?</script>",
    r"<style id=[\"']wp-emoji-styles-inline-css[\"'][\s\S]*?</style>",
    r"<script id=[\"']wp-emoji-settings[\"'][\s\S]*?</script>",
    r"<script[^>]*wp-emoji[^>]*>\s*</script>",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read(), url


def norm(path):
    """Path only: no query, no fragment, percent-decoded once for the filesystem."""
    return urllib.parse.urlsplit(path).path or "/"


class Exporter:
    def __init__(self, origin, out):
        self.origin, self.out = origin.rstrip("/"), Path(out)
        self.host = urllib.parse.urlsplit(self.origin).netloc
        self.seen, self.queue, self.missing = set(), [], []
        self.abs_re = re.compile(r"https?:/{2}" + re.escape(self.host) + r"(/[^\s\"'<>()\\]*)?")

    # ---- discovery -------------------------------------------------------------------------
    def find(self, text, base, kind):
        found = set()
        t = text.replace("\\/", "/")  # Elementor JSON escapes slashes
        for m in self.abs_re.finditer(t):
            found.add(m.group(1) or "/")
        if kind == "html":
            for m in re.finditer(r"""(?:href|src|data-src|data-lazy-src|poster)\s*=\s*["']([^"']+)["']""", text, re.I):
                found.add(self._rel(m.group(1), base))
            for m in re.finditer(r"""(?:srcset|data-srcset)\s*=\s*["']([^"']+)["']""", text, re.I):
                for cand in m.group(1).split(","):
                    if cand.strip():
                        found.add(self._rel(cand.strip().split()[0], base))
        if kind in ("html", "css"):
            for m in re.finditer(r"""url\(\s*["']?([^"')]+)""", html.unescape(text)):
                found.add(self._rel(m.group(1), base))
            for m in re.finditer(r"""@import\s+["']([^"']+)""", text):
                found.add(self._rel(m.group(1), base))
        return {p for p in found if p}

    def _rel(self, ref, base):
        ref = html.unescape(ref.strip())
        if ref.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
            return None
        full = urllib.parse.urljoin(base, ref)
        parts = urllib.parse.urlsplit(full)
        return parts.path if parts.netloc == self.host else None

    # ---- crawl -----------------------------------------------------------------------------
    def enqueue(self, paths):
        for p in paths:
            p = norm(p)
            if p not in self.seen and not SKIP.search(p):
                self.seen.add(p)
                self.queue.append(p)

    def save(self, path, ctype, body, final_path):
        is_html = "text/html" in ctype
        rel = urllib.parse.unquote(final_path).lstrip("/")
        if rel == "" or rel.endswith("/"):
            rel += "index.html"
        elif is_html and not Path(rel).suffix:
            rel += "/index.html"
        dest = self.out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        return dest

    def crawl(self, seeds):
        self.enqueue(seeds)
        done = 0
        while self.queue:
            batch, self.queue = self.queue, []
            with ThreadPoolExecutor(max_workers=6) as ex:
                results = list(ex.map(lambda p: (p, fetch(self.origin + urllib.parse.quote(p, safe="/%:@!$&'()*+,;=-._~"))), batch))
            for path, (status, ctype, body, final) in results:
                if status != 200:
                    self.missing.append((path, status))
                    continue
                final_path = norm(final.replace(self.origin, "")) if final.startswith(self.origin) else path
                dest = self.save(path, ctype, body, final_path)
                done += 1
                kind = "html" if "text/html" in ctype else "css" if dest.suffix == ".css" else "js" if dest.suffix == ".js" else None
                if kind:
                    self.enqueue(self.find(body.decode("utf-8", "replace"), self.origin + final_path, kind))
        return done

    # ---- rewrite ---------------------------------------------------------------------------
    def rewrite(self):
        host = re.escape(self.host)
        n_files = 0
        for f in self.out.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in TEXT_EXT:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            new = re.sub(r"https?:(?:\\?/){2}" + host + r"(?=\\?/)", "", text)       # http://host/x -> /x  (also JSON-escaped)
            new = re.sub(r"https?:(?:\\?/){2}" + host + r"(?![\w.-])", "/", new)     # bare origin -> /
            new = re.sub(r"(?<![:\w/\\])(?:\\?/){2}" + host + r"(?=\\?/)", "", new)  # protocol-relative //host/x -> /x (inline CSS url(), JSON)
            if f.suffix.lower() == ".html":
                for pat in HEAD_STRIP:
                    new = re.sub(pat, "", new, flags=re.I)
                if icon_tags() and not re.search(r"<link rel=[\"'](?:shortcut )?icon[\"']", new):
                    new = new.replace("</head>", icon_tags() + "\n</head>", 1)
                # canonical / social URLs must be absolute and point at the final host
                new = re.sub(r"(<link rel=[\"']canonical[\"'] href=[\"'])(/[^\"']*)", lambda m: m.group(1) + FINAL + m.group(2), new)
                new = re.sub(r"(<meta (?:property|name)=[\"'](?:og:url|og:image|twitter:image)[\"'] content=[\"'])(/[^\"']*)", lambda m: m.group(1) + FINAL + m.group(2), new)
            if new != text:
                f.write_text(new, encoding="utf-8", newline="")
                n_files += 1
        return n_files


def wp_urls():
    """Published page/post paths from WP-CLI (the sitemap is off while blog_public=0). Empty on failure."""
    try:
        out = subprocess.run(
            ["docker", "compose", "--profile", "tools", "run", "--rm", "wpcli", "wp", "post", "list",
             "--post_type=page,post", "--post_status=publish", "--field=url"],
            cwd=ROOT, capture_output=True, text=True, timeout=180).stdout
    except Exception:
        return []
    return [urllib.parse.urlsplit(u).path for u in out.split() if u.startswith("http")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", default="http://localhost")
    ap.add_argument("--out", default=str(ROOT / "site"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    ex = Exporter(a.origin, out)
    extra = ROOT / "scripts" / "export-extra-urls.txt"
    extras = [l.strip() for l in extra.read_text().splitlines() if l.strip() and not l.startswith("#")] if extra.exists() else []
    seeds = ["/"] + wp_urls() + extras
    print(f"seeds: {len(seeds)} ({len(extras)} extra)")
    n = ex.crawl(seeds)
    print(f"fetched {n} files; {len(ex.missing)} failed")
    for p, s in sorted(ex.missing)[:25]:
        print(f"  {s} {p}")

    # /favicon.ico redirects to the uploaded site icon; browsers ask for the root path, so give them a copy.
    status, ctype, body, _ = fetch(a.origin + "/favicon.ico")
    if status == 200 and "text/html" not in ctype:
        (out / "favicon.ico").write_bytes(body)

    # A proper 404 page, a robots.txt that does not hide the noindex header, and the header itself.
    status, ctype, body, _ = fetch(a.origin + "/this-page-does-not-exist-404/")
    if status == 404:
        (out / "404.html").write_bytes(body)
        # The 404 page can load assets no normal page does (Divi: et-cache/notfound/*.css): crawl what it references too.
        n404 = ex.crawl(sorted(ex.find(body.decode("utf-8", "replace"), a.origin + "/this-page-does-not-exist-404/", "html")))
        print(f"404 page: fetched {n404} more files it references")
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8", newline="\n")
    (out / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n", encoding="utf-8", newline="\n")

    changed = ex.rewrite()
    if OVERLAY.exists():  # hand-made / generated files that override anything the crawl produced
        for f in OVERLAY.rglob("*"):
            if f.is_file():
                dest = out / f.relative_to(OVERLAY)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
        print(f"overlay: copied {sum(1 for f in OVERLAY.rglob('*') if f.is_file())} files from {OVERLAY.name}/")
    for junk in ("wp-includes/js/wp-emoji-loader.min.js", "wp-includes/js/wp-emoji-release.min.js", "wp-includes/js/wp-emoji.min.js"):
        (out / junk).unlink(missing_ok=True)  # fetched before their <script> tags were stripped
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"rewrote {changed} text files; site is {sum(1 for f in out.rglob('*') if f.is_file())} files, {total/1048576:.1f} MB -> {out}")


if __name__ == "__main__":
    sys.exit(main())
