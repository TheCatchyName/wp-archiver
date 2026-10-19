"""Tiny .env reader shared by the toolkit's Python scripts (stdlib only).

    from _env import ROOT, env, require

`env("KEY", default)` reads the process environment first, then `<repo>/.env`. `require("KEY")` exits with a
clear message when a per-site value has not been filled in yet. Values may be quoted ("a b c").
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    values = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            val = val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            values[key.strip()] = val
    return values


_FILE = _load()


def env(key, default=""):
    return os.environ.get(key) or _FILE.get(key) or default


def require(key):
    val = env(key)
    if not val:
        sys.exit(f"{key} is not set: fill it in .env (see .env.example)")
    return val
