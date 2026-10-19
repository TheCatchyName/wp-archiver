#!/usr/bin/env python
"""Trim a raw hosting download down to what is worth keeping, then zip it. Dry run unless --apply.

    python scripts/trim-archive.py            # show the plan, delete nothing
    python scripts/trim-archive.py --apply    # write MANIFEST.md, delete, move history aside, zip, verify

Works from an explicit keep-list: anything under public_html that is not listed is deleted. That is safe because what is
dropped is regenerable (WordPress core, plugins and themes by version from wordpress.org: the manifest records the
versions), junk (logs, caches, a failed export's temp files), or secrets of a host that no longer exists (keys,
licence-bound vendor code). Older snapshots of the same site (backup zips, earlier SQL dumps) are history, not junk:
they are MOVED to archive/historical/, never deleted.

Per-site settings: ACTIVE_THEME / ARCHIVE_NAME in .env, plus EXTRA_KEEP and HISTORICAL below. The keep-list always
includes the host config files, the active theme, every dated uploads/<year> folder and (if present) uploads/elementor.

Result: archive/<name>-<date>.zip (gitignored with the rest of archive/) containing the trimmed tree + MANIFEST.md.
The zip contains wp-config.php (DB credentials, salts): it is a secret (ARC-5).
"""
import argparse
import datetime
import re
import shutil
import sys
import zipfile
from pathlib import Path

from _env import ROOT, env, require

ARCHIVE = ROOT / "archive"
ACTIVE_THEME = require("ACTIVE_THEME")
NAME = env("ARCHIVE_NAME") or f"{env('COMPOSE_PROJECT_NAME', 'site')}-archive"

# PER-SITE. Relative to public_html. Anything else you want to keep (e.g. a custom mu-plugin you wrote):
EXTRA_KEEP = []
# PER-SITE. Older snapshots of the site: moved aside to archive/historical/ (relative to public_html), never deleted.
# Look for backup zips, earlier .sql dumps, backup-plugin folders (ARC-2).
HISTORICAL = []


def find_src():
    found = [d for d in sorted(ARCHIVE.glob("*/")) if (d / "public_html").is_dir() and d.name != "historical"]
    if len(found) != 1:
        sys.exit(f"expected exactly one archive/<host>/public_html, found {len(found)}")
    return found[0]


SRC = find_src()
PUBLIC = SRC / "public_html"


def keep_list():
    keep = [f for f in (".htaccess", "robots.txt") if (PUBLIC / f).exists()]  # host config: optional
    keep += ["wp-config.php", f"wp-content/themes/{ACTIVE_THEME}"]
    keep += [f"wp-content/themes/{t}" for t in env("EXTRA_THEMES").split()]
    uploads = PUBLIC / "wp-content" / "uploads"
    if uploads.is_dir():
        keep += [f"wp-content/uploads/{d.name}" for d in sorted(uploads.iterdir()) if d.is_dir() and re.fullmatch(r"\d{4}", d.name)]
        if (uploads / "elementor").is_dir():  # builder: Elementor (self-hosted font files + generated CSS)
            keep.append("wp-content/uploads/elementor")
    return keep + EXTRA_KEEP


def size(p):
    p = Path(p)
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def header(path, key):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")[:8192]
    except OSError:
        return "?"
    m = re.search(r"^\s*[*#]*\s*" + key + r":\s*(.+)$", text, re.I | re.M)
    return re.sub(r"\s*\*/.*$", "", m.group(1)).strip() if m else "?"   # drop a trailing comment close


def manifest(keep, delete, move):
    cfg = (PUBLIC / "wp-config.php").read_text(errors="replace")
    wp = re.search(r"\$wp_version\s*=\s*'([^']+)'", (PUBLIC / "wp-includes/version.php").read_text())
    prefix = re.search(r"\$table_prefix\s*=\s*'([^']+)'", cfg)
    plugins = []
    for d in sorted((PUBLIC / "wp-content/plugins").iterdir()):
        if d.is_dir():
            ver = next((v for f in sorted(d.glob("*.php")) if (v := header(f, "Version")) != "?"), "?")
            flag = "" if (d / "readme.txt").exists() else "   <-- no readme.txt: possibly premium / not on wordpress.org; verify"
            plugins.append(f"- {d.name} {ver}{flag}")
    themes = [f"- {d.name} {header(d / 'style.css', 'Version')}" + (" (active; kept in this archive)" if d.name == ACTIVE_THEME else "")
              for d in sorted((PUBLIC / "wp-content/themes").iterdir()) if d.is_dir()]
    mu = sorted(p.name for p in (PUBLIC / "wp-content/mu-plugins").iterdir()) if (PUBLIC / "wp-content/mu-plugins").exists() else []
    defines = sorted(set(re.findall(r"define\(\s*['\"]([A-Z_0-9]+)['\"]", cfg)))
    dumps = sorted(p.name for p in SRC.glob("*.sql"))
    deleted = "\n".join(f"- {p.relative_to(PUBLIC).as_posix()} ({size(p)/1048576:.1f} MB)" for p in sorted(delete, key=size, reverse=True))
    moved = "\n".join(f"- {p.relative_to(PUBLIC).as_posix()}" for p in move) or "- (none)"
    return f"""# {NAME} -- trimmed {datetime.date.today()}

Trimmed by `scripts/trim-archive.py` from the full hosting download. WordPress {wp.group(1) if wp else '?'}, table prefix
`{prefix.group(1) if prefix else '?'}`. The live static site is built from the git repo, not from this archive.

## What is in this zip
- `{dumps[0] if dumps else '(dump missing)'}` -- the authoritative, UNSCRUBBED database dump (user hashes, visitor logs, spam
  comments, removed plugins' tables). The git repo only has the scrubbed seed.
- Kept under `public_html/`: {', '.join('`' + k + '`' for k in keep)}
- **wp-config.php holds the old DB credentials and salts: treat this zip as secret.**

## What was deleted, and how to get it back
- WordPress core (wp-admin, wp-includes, root php files): download WordPress {wp.group(1) if wp else '?'} from wordpress.org.
- Plugins (re-downloadable by version from wordpress.org unless flagged):
{chr(10).join(plugins)}
- Themes (re-downloadable unless premium):
{chr(10).join(themes)}
- Licence-bound code (premium plugins/themes, mu-plugins: {', '.join(mu) or 'none'}): anything flagged above cannot be
  re-downloaded without a licence, and this trim deleted it. Confirm that was intended before you retire the host.
- Everything deleted, top level, largest first:
{deleted}
- wp-config.php defines (names only): {', '.join(defines)}

## History kept OUTSIDE this zip
Moved to `archive/historical/` (not deleted):
{moved}

## Restoring the original WordPress site (rough)
WordPress {wp.group(1) if wp else '?'} + the plugin/theme versions above + this database dump + `uploads/`.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    apply = ap.parse_args().apply

    keep_rel = keep_list()
    keep = {(PUBLIC / k).resolve() for k in keep_rel}
    hist = {(PUBLIC / h).resolve() for h in HISTORICAL}
    delete, move = [], []

    def walk(d):
        for e in sorted(d.iterdir()):
            r = e.resolve()
            if r in keep:
                continue
            if r in hist:
                move.append(e)
            elif any(k == r or k.is_relative_to(r) for k in keep):  # a parent of something we keep: look inside
                walk(e)
            else:
                delete.append(e)

    if not PUBLIC.exists():
        sys.exit(f"{PUBLIC} not found")
    for k in keep_rel:
        if not (PUBLIC / k).exists():
            sys.exit(f"keep entry missing: {k}")
    for h in HISTORICAL:
        if not (PUBLIC / h).exists():
            sys.exit(f"HISTORICAL entry missing: {h}")
    walk(PUBLIC)

    before = size(SRC)
    print(f"{SRC.relative_to(ROOT)} is {before/1048576:.0f} MB. Plan:")
    print(f"  KEEP   : {', '.join(keep_rel)} + {', '.join(p.name for p in SRC.glob('*.sql'))}")
    print("  MOVE   : -> archive/historical/")
    for p in move:
        print(f"           {size(p)/1048576:8.1f} MB  {p.relative_to(PUBLIC)}")
    print(f"  DELETE : {len(delete)} items, {sum(size(p) for p in delete)/1048576:.0f} MB")
    for p in sorted(delete, key=size, reverse=True):
        print(f"           {size(p)/1048576:8.1f} MB  {p.relative_to(PUBLIC)}")
    if not apply:
        print("\ndry run: nothing changed. Review the DELETE list (premium code? history? anything the owner wants), then re-run with --apply.")
        return 0

    text = manifest(keep_rel, delete, move)   # BEFORE deleting: it reads the plugin/theme/core files
    (SRC / "MANIFEST.md").write_text(text, encoding="utf-8", newline="\n")
    hist_dir = ARCHIVE / "historical"
    hist_dir.mkdir(exist_ok=True)
    for p in move:
        shutil.move(str(p), str(hist_dir / p.name))
    for p in delete:
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    for d in sorted((p for p in PUBLIC.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):          # prune empty folders left behind
            d.rmdir()

    out = ARCHIVE / f"{NAME}-{datetime.date.today()}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(SRC.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(SRC.parent).as_posix())
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        names = z.namelist()
    print(f"\ntrimmed tree: {size(SRC)/1048576:.0f} MB -> {out.name}: {out.stat().st_size/1048576:.0f} MB, {len(names)} files, integrity: {'OK' if bad is None else 'BAD ' + bad}")
    return 0 if bad is None else 1


if __name__ == "__main__":
    sys.exit(main())
