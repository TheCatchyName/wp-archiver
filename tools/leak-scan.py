#!/usr/bin/env python
"""Scan the files that would be committed for private or site-specific material. Run before every commit and before publishing.

    python tools/leak-scan.py

Checks every non-ignored file (git ls-files -co --exclude-standard) for:
  - terms listed in `.private-terms` (untracked, one per line, case-insensitive): real site names, domains, hosts, people.
    Keep that file local; listing the terms in a tracked file would publish them.
  - email addresses outside example/test domains, IPv4 addresses other than loopback/documentation ranges,
    private-key blocks, WordPress password hashes.
Exit 1 on any hit.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".md", ".py", ".sh", ".sql", ".php", ".json", ".jsonc", ".yml", ".yaml", ".txt", ".ini", ".example", ".lock", ""}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
OK_MAIL = re.compile(r"(^|\.)(example\.(com|org|net|site)|[a-z0-9-]*\.test|example)$|users\.noreply\.github\.com|noreply@anthropic\.com", re.I)
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
OK_IP = re.compile(r"^(127\.|0\.0\.0\.0|192\.0\.2\.|198\.51\.100\.|203\.0\.113\.|1\.1\.1\.1|8\.8\.8\.8)")
SECRETS = re.compile(r"BEGIN (?:EC |RSA |OPENSSH |PGP )?PRIVATE KEY|\$P\$[./0-9A-Za-z]{20,}|\$wp\$2y\$")


def main():
    terms = []
    pt = ROOT / ".private-terms"
    if pt.exists():
        terms = [l.strip().lower() for l in pt.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    else:
        print("note: no .private-terms file; only the generic patterns are checked")
    files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    hits = 0
    for rel in filter(None, files):
        p = ROOT / rel
        if not p.is_file() or p.suffix.lower() not in TEXT or "icon" in p.name:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        low = text.lower()
        for term in terms:
            if term in low:
                hits += 1
                print(f"TERM    {rel}: contains private term '{term[:2]}…' ({len(term)} chars)")
        for m in EMAIL.finditer(text):
            if not OK_MAIL.search(m.group(1)) and not OK_MAIL.search(m.group(0)):
                hits += 1
                print(f"EMAIL   {rel}: {m.group(0)}")
        for m in IPV4.finditer(text):
            if not OK_IP.match(m.group(0)) and all(int(x) < 256 for x in m.group(0).split(".")):
                hits += 1
                print(f"IPV4    {rel}: {m.group(0)}")
        if SECRETS.search(text):
            hits += 1
            print(f"SECRET  {rel}: key block or password hash")
    print(f"{hits} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
