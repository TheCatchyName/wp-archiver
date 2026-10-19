#!/usr/bin/env python
"""Integrity checks for the skills, so "open one phase file at a time" stays true as the repo grows.

    python tools/check-docs.py

Checks (exit 1 on any failure):
  1. every SKILL.md has frontmatter whose `name` equals its folder name and a non-empty `description`;
  2. every relative markdown link in README/CLAUDE/CONTRIBUTING/docs/skills resolves (http(s), mailto, #anchor skipped);
  3. every gotcha ID cited anywhere (ENV-3, VIS-1 ...) is defined in skills/wp-archiver/reference/gotchas.md;
  4. every script named in reference/tool-index.md exists in the toolkit;
  5. every phase file is linked from skills/wp-archiver/SKILL.md;
  6. toolkit syntax: every .py compiles, every .sh passes `bash -n`.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "wp-archiver"
TOOLKIT = SKILL / "toolkit"
GOTCHAS = SKILL / "reference" / "gotchas.md"
TOOLS = SKILL / "reference" / "tool-index.md"

LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")
ID = re.compile(r"\b(ENV|RST|VIS|PRN|DB|EXP|IMG|PUB|ARC|SES)-(\d+)\b")
DEFINED = re.compile(r"^- \*\*((?:ENV|RST|VIS|PRN|DB|EXP|IMG|PUB|ARC|SES)-\d+)\*\*", re.M)
SCRIPT = re.compile(r"\b([\w.-]+\.(?:py|sh|sql|php|txt|example))\b")
# Names that appear in the tool index as examples or as files that are not shipped scripts.
EXAMPLE_NAMES = {"x.php", "file.sql", "home.html", "images-raw.manifest.txt", "MANIFEST.md", "seed.sql", "requirements.txt",
                 "export.sql", "logo.png", "<db>.sql", "dump.sql", "archive-form-notice.php", "env.example"}


def markdown_files():
    return [p for p in ROOT.glob("*.md")] + sorted((ROOT / "docs").glob("*.md")) + sorted((ROOT / "skills").rglob("*.md"))


def main():
    problems = []
    files = sorted({p for p in markdown_files()})
    defined = set(DEFINED.findall(GOTCHAS.read_text(encoding="utf-8")))

    # 1. skill frontmatter
    for sk in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = sk.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not m:
            problems.append(f"{sk.relative_to(ROOT)}: no frontmatter")
            continue
        name = re.search(r"^name:\s*(.+)$", m.group(1), re.M)
        desc = re.search(r"^description:\s*(.+)$", m.group(1), re.M)
        if not name or name.group(1).strip() != sk.parent.name:
            problems.append(f"{sk.relative_to(ROOT)}: frontmatter name must equal folder name '{sk.parent.name}'")
        if not desc or not desc.group(1).strip():
            problems.append(f"{sk.relative_to(ROOT)}: empty description")

    for f in files:
        text = f.read_text(encoding="utf-8")
        # 2. links (skip fenced code blocks)
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in LINK.findall(prose):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#")[0]
            if path and not (f.parent / path).exists():
                problems.append(f"{f.relative_to(ROOT)}: broken link -> {target}")
        # 3. gotcha IDs
        for prefix, num in ID.findall(text):
            if f"{prefix}-{num}" not in defined:
                problems.append(f"{f.relative_to(ROOT)}: cites undefined gotcha {prefix}-{num}")

    # 4. scripts in the tool index
    tools = TOOLS.read_text(encoding="utf-8")
    for name in sorted(set(SCRIPT.findall(tools))):
        if name in EXAMPLE_NAMES:
            continue
        if not any((TOOLKIT / d / name).exists() for d in ("scripts", ".", "docker/wordpress")) \
                and not any((SKILL / "builders" / "elementor" / name).exists() for _ in [0]):
            problems.append(f"tool-index.md: script not found -> {name}")

    # 5. phase files linked from SKILL.md
    index = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for p in sorted((SKILL / "phases").glob("*.md")):
        if f"phases/{p.name}" not in index:
            problems.append(f"SKILL.md: phase file not linked -> {p.name}")

    # 6. toolkit syntax
    for py in sorted(TOOLKIT.rglob("*.py")):
        try:
            compile(py.read_text(encoding="utf-8"), str(py), "exec")
        except SyntaxError as e:
            problems.append(f"{py.relative_to(ROOT)}: {e}")
    bash = shutil.which("bash")
    for cand in ("C:/Program Files/Git/bin/bash.exe", "C:/Program Files (x86)/Git/bin/bash.exe"):
        if sys.platform == "win32" and Path(cand).exists():
            bash = cand  # Git Bash: `bash` on PATH may be WSL's, which cannot read Windows paths
            break
    if bash:
        for sh in sorted(TOOLKIT.rglob("*.sh")):
            r = subprocess.run([bash, "-n", sh.relative_to(ROOT).as_posix()], cwd=ROOT, capture_output=True, text=True)
            if r.returncode:
                problems.append(f"{sh.relative_to(ROOT)}: {r.stderr.strip()}")
    else:
        print("note: bash not found, shell syntax not checked")

    print(f"checked {len(files)} markdown files, {len(defined)} gotchas defined")
    for p in problems:
        print("PROBLEM ", p)
    print(f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
