#!/usr/bin/env python3
"""Warn when text looks like it contains row-level or personal data (SEC-04).

  leak_scan.py <file>...          scan files
  leak_scan.py --stdin            scan text on stdin (issue / PR comments)
  --blocking                      exit 1 on findings (default: warn only)

Heuristics only: emails, phone numbers, SSN-like numbers, card-like numbers,
and markdown tables or CSV blocks with many rows. Tune before blocking.
"""
import re
import sys

PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b"),
    "ssn-like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "card-like": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
}
ALLOW_EMAIL = re.compile(r"(noreply|example\.(com|org)|users\.noreply\.github\.com|triverusconsulting\.com)", re.I)


def scan(name, text):
    findings = []
    for kind, rx in PATTERNS.items():
        for m in rx.finditer(text):
            if kind == "email" and ALLOW_EMAIL.search(m.group(0)):
                continue
            findings.append(f"{name}: {kind}")
            break
    table_rows = sum(1 for line in text.splitlines() if line.count("|") >= 4 and re.search(r"\d", line))
    csv_rows = sum(1 for line in text.splitlines() if line.count(",") >= 4 and re.search(r"\d", line))
    if table_rows > 25 or csv_rows > 25:
        findings.append(f"{name}: large data-like table ({max(table_rows, csv_rows)} rows); share aggregates only")
    return findings


def main():
    args = sys.argv[1:]
    blocking = "--blocking" in args
    args = [a for a in args if a != "--blocking"]
    findings = []
    if args == ["--stdin"]:
        findings += scan("stdin", sys.stdin.read())
    else:
        for path in args:
            try:
                findings += scan(path, open(path, encoding="utf-8", errors="ignore").read())
            except OSError:
                pass
    for f in findings:
        print(f"::warning::possible data leak (SEC-04): {f}")
    print(f"leak_scan: {len(findings)} finding(s){' (blocking)' if blocking else ' (warn only)'}")
    return 1 if (blocking and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
