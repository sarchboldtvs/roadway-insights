#!/usr/bin/env python3
"""
WCAG contrast checker for Power BI themes and report colors.

Implements the WCAG 2.x relative luminance and contrast ratio formulas.

Usage:
    python contrast_check.py --pair "#FFFFFF" "#0075A9"          Check one foreground/background pair
    python contrast_check.py --theme path/to/theme.json            Check a Power BI theme file
    python contrast_check.py --report path/to/Name.Report          Find hex colors in visual.json files
                             [--background "#FFFFFF"]              Page background (default white)

Rules checked:
    COL-01  normal text  >= 4.5:1 against background
    COL-02  large text   >= 3:1   against background
    COL-03  data colors  >= 3:1   against background (FAIL) and against the next data color
            (WARN: the checklist allows white space or borders between neighbors instead)

Exit code 1 if any FAIL.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HEX = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")
results = []


def norm(color):
    m = HEX.match(color.strip().strip("'"))
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def luminance(hex_color):
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def record(rule, fg, bg, minimum, context, soft=False):
    r = ratio(fg, bg)
    status = "PASS" if r >= minimum else ("WARN" if soft else "FAIL")
    results.append({"rule": rule, "status": status, "fg": fg, "bg": bg, "ratio": round(r, 2),
                    "min": minimum, "context": context})


def check_theme(path, override_bg=None):
    theme = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    bg = override_bg or norm(theme.get("background", "#FFFFFF")) or "#FFFFFF"
    fg = norm(theme.get("foreground", "")) if theme.get("foreground") else None
    data = [norm(c) for c in theme.get("dataColors", []) if norm(c)]

    if fg:
        record("COL-01", fg, bg, 4.5, "theme foreground text")
    for i, c in enumerate(data):
        record("COL-03", c, bg, 3.0, f"dataColors[{i}] vs background")
    for i in range(len(data) - 1):
        record("COL-03", data[i], data[i + 1], 3.0,
               f"dataColors[{i}] vs dataColors[{i + 1}] (neighbors: if adjacent in a visual, separate with white space or borders)",
               soft=True)

    for cls, spec in (theme.get("textClasses") or {}).items():
        col = norm(spec.get("color", "")) if isinstance(spec, dict) and spec.get("color") else None
        if not col:
            continue
        size = spec.get("fontSize", 0) or 0
        large = size >= 18 or (size >= 14 and "bold" in str(spec.get("fontFace", "")).lower())
        record("COL-02" if large else "COL-01", col, bg, 3.0 if large else 4.5, f"textClasses.{cls} ({size}pt)")


def check_report(report_dir, bg):
    for vf in sorted(Path(report_dir).rglob("visual.json")):
        text = vf.read_text(encoding="utf-8-sig")
        for m in re.finditer(r"'(#[0-9a-fA-F]{6})'", text):
            col = norm(m.group(1))
            r = ratio(col, bg)
            status = "PASS" if r >= 4.5 else ("REVIEW" if r >= 3.0 else "FAIL")
            results.append({"rule": "COL-01/02/03", "status": status, "fg": col, "bg": bg, "ratio": round(r, 2),
                            "min": "4.5 text / 3.0 large text or data",
                            "context": f"{vf.parent.parent.parent.name}/{vf.parent.name}"})


def print_table():
    print("| Status | Rule | Color | Background | Ratio | Minimum | Context |")
    print("|---|---|---|---|---|---|---|")
    for r in sorted(results, key=lambda r: {"FAIL": 0, "WARN": 1, "REVIEW": 1, "PASS": 2}[r["status"]]):
        print(f"| {r['status']} | {r['rule']} | {r['fg']} | {r['bg']} | {r['ratio']}:1 | {r['min']} | {r['context']} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="WCAG contrast checker for Power BI")
    ap.add_argument("--pair", nargs=2, metavar=("FOREGROUND", "BACKGROUND"))
    ap.add_argument("--theme")
    ap.add_argument("--report")
    ap.add_argument("--background", default=None, help="Page background hex (default: theme background or #FFFFFF)")
    args = ap.parse_args()
    args.background_set = args.background is not None
    args.background = args.background or "#FFFFFF"

    if args.pair:
        a, b = norm(args.pair[0]), norm(args.pair[1])
        if not a or not b:
            sys.exit("Colors must be hex, for example #0075A9")
        r = ratio(a, b)
        print(f"{a} on {b}: {r:.2f}:1  normal text {'PASS' if r >= 4.5 else 'FAIL'}, "
              f"large text/data {'PASS' if r >= 3 else 'FAIL'}")
        sys.exit(0)
    if args.theme:
        check_theme(args.theme, norm(args.background) if args.background_set else None)
    if args.report:
        check_report(args.report, norm(args.background) or "#FFFFFF")
    if not (args.theme or args.report):
        ap.print_help()
        sys.exit(2)
    print_table()
    sys.exit(1 if any(r["status"] == "FAIL" for r in results) else 0)
