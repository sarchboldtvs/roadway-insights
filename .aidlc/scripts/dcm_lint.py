#!/usr/bin/env python3
"""Deterministic checks on DCM definitions (SRC-03, SQL-02, SQL-03, SEC-01, NAM-01).

  dcm_lint.py <dcm project dir>     exit 1 on FAIL
"""
import pathlib
import re
import sys

CHECKS = [
    ("SRC-03", "FAIL", re.compile(r"\b(DEV|PROD)_[A-Z0-9_]+\b"), "literal environment name; use templating"),
    ("SEC-01", "FAIL", re.compile(r"\bGRANT\b[^;]*\bTO\s+(ROLE\s+)?PUBLIC\b", re.I | re.S), "grant to PUBLIC"),
    ("SEC-01", "FAIL", re.compile(r"\bGRANT\b[^;]*\bTO\s+USER\b", re.I | re.S), "grant to a user"),
]
DEFINE = re.compile(r"\bDEFINE\s+(?:SECURE\s+)?(TABLE|VIEW|DYNAMIC TABLE|SCHEMA|TASK|FUNCTION|STAGE)\s+((?:\{\{[^}]*\}\}|[^\s(])+)(.*?);", re.I | re.S)


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "snowflake")
    files = sorted((root / "sources").rglob("*.sql")) if (root / "sources").exists() else sorted(root.rglob("*.sql"))
    fails = warns = 0
    for f in files:
        text = f.read_text(errors="ignore")
        body = re.sub(r"--[^\n]*", "", text)
        for rid, level, rx, msg in CHECKS:
            for m in rx.finditer(body):
                print(f"{level}  {rid}  {f}: {msg}: {m.group(0)[:60]!r}")
                fails += level == "FAIL"
        for m in DEFINE.finditer(body):
            kind, name, rest = m.group(1).upper(), m.group(2), m.group(3)
            leaf = re.sub(r"\{\{.*?\}\}\.?", "", name).split(".")[-1].strip('"')
            if leaf and leaf != leaf.upper():
                print(f"FAIL  NAM-01  {f}: {name} is not UPPER_SNAKE_CASE"); fails += 1
            if "COMMENT" not in rest.upper():
                print(f"WARN  SQL-03  {f}: {kind} {name} has no COMMENT"); warns += 1
            if kind in ("VIEW", "DYNAMIC TABLE") and ".MARTS." in name.upper() and re.search(r"SELECT\s+\*", rest, re.I):
                print(f"FAIL  SQL-02  {f}: SELECT * in mart {name}"); fails += 1
    print(f"dcm_lint: {len(files)} files, {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
