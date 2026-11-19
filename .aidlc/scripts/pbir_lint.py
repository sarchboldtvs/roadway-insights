#!/usr/bin/env python3
"""
Power BI PBIR standards lint.

Checks a PBIP report folder (PBIR format) against the AUTO rules in
.github/powerbi-standards/development-checklist.md and prints a Markdown findings table.

Usage:
    python pbir_lint.py <path-to-Name.Report-folder> [--json]

Design note: PBIR property paths can change between schema versions, so this script
searches visual JSON recursively by key name (altText, heading, tabOrder, responsive,
title text) instead of hard-coding full paths. Every finding includes the file path so a
reviewer can confirm it.

Status values: FAIL, WARN (likely issue, needs human judgment), MANUAL (cannot be checked
from JSON), INFO.
"""

import json
import re
import sys
from pathlib import Path

# Visual types treated as decorative / non-interactive (no alt text, no tab stop expected).
DECORATIVE_TYPES = {"shape", "basicShape", "image"}
# Visual types exempt from the alt-text requirement but not decorative.
ALT_EXEMPT_TYPES = DECORATIVE_TYPES | {"textbox", "actionButton", "pageNavigator", "bookmarkNavigator"}
SLICER_TYPES = {"slicer", "advancedSlicerVisual", "listSlicer", "textSlicer"}
BUTTON_TYPES = {"actionButton"}
KPI_TYPES = {"card", "cardVisual", "multiRowCard", "kpi", "gauge"}
TABLE_TYPES = {"tableEx", "pivotTable"}
MOUSE_ONLY_TYPES = {"esriVisual", "arcGISMap"}
INSTRUCTION_TRIGGER_TYPES = SLICER_TYPES | KPI_TYPES | {"pivotTable"} | MOUSE_ONLY_TYPES
VISUAL_TYPE_WORDS = [
    "bar chart", "column chart", "line chart", "pie chart", "donut chart", "table", "matrix",
    "card", "map", "scatter", "visual", "graph", "chart",
]

findings = []


def add(rule, status, page, visual, message, path=""):
    findings.append({
        "rule": rule, "status": status, "page": page, "visual": visual,
        "message": message, "file": str(path),
    })


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        add("FMT-02", "FAIL", "", "", f"Invalid JSON: {exc}", path)
        return None


def walk(obj, key_pred, trail=()):
    """Yield (trail, value) for every key matching key_pred, at any depth."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if key_pred(k):
                yield trail + (k,), v
            yield from walk(v, key_pred, trail + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, key_pred, trail + (i,))


def literal(value):
    """Extract a readable literal from PBIR expr structures like {'expr': {'Literal': {'Value': "'text'"}}}."""
    if isinstance(value, dict):
        if "expr" in value:
            return literal(value["expr"])
        if "Literal" in value:
            return literal(value["Literal"].get("Value"))
        if "Measure" in value or "Aggregation" in value or "Column" in value:
            return "<dynamic>"
        return None
    if isinstance(value, str):
        v = value.strip()
        if len(v) >= 2 and v[0] == "'" and v[-1] == "'":
            v = v[1:-1]
        return v
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return None
    return str(value)


def section_value(visual_json, section, prop):
    """Return literal values for <section>[*].properties.<prop>, at any depth."""
    out = []
    for _, sec in walk(visual_json, lambda k: k == section):
        items = sec if isinstance(sec, list) else [sec]
        for item in items:
            if isinstance(item, dict):
                props = item.get("properties", {})
                if prop in props:
                    out.append(literal(props[prop]))
    return out


def load_glossary(repo_root):
    path = repo_root / ".github/powerbi-standards/development-checklist.md"
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    m = re.search(r"<!-- glossary-start -->(.*?)<!-- glossary-end -->", text, re.S)
    if not m:
        return set()
    return {line.strip("- ").strip() for line in m.group(1).splitlines() if line.strip("- ").strip()}


def find_repo_root(start):
    for p in [start, *start.parents]:
        if (p / ".github").exists():
            return p
    return start


def acronyms(text, glossary):
    if not text or text == "<dynamic>":
        return []
    tokens = re.findall(r"\b[A-Z][A-Z0-9&]{1,}\b", text)
    return sorted({t for t in tokens if t not in glossary})


def heading_level(values):
    for v in values:
        if v:
            m = re.search(r"(\d)", v)
            if m:
                return int(m.group(1))
            if v.lower() not in ("none", "false", "off", ""):
                return v
    return None


def check_report(report_dir):
    report_dir = Path(report_dir)
    repo_root = find_repo_root(report_dir.resolve())
    glossary = load_glossary(repo_root)

    pages_dir = report_dir / "definition" / "pages"
    if not pages_dir.exists():
        if (report_dir / "report.json").exists():
            add("FMT-01", "FAIL", "", "", "Report uses the legacy PBIR-Legacy format (single report.json). "
                "Convert to PBIR before Copilot generation or review.", report_dir / "report.json")
        else:
            add("FMT-01", "FAIL", "", "", "No definition/pages folder found. Is this a PBIP *.Report folder?", report_dir)
        return

    page_files = sorted(pages_dir.glob("*/page.json"))
    if not page_files:
        add("FMT-01", "FAIL", "", "", "No page.json files found.", pages_dir)
        return

    for page_file in page_files:
        page = load(page_file) or {}
        page_name = page.get("displayName", page_file.parent.name)
        page_w = page.get("width", 1280) or 1280
        page_h = page.get("height", 720) or 720

        visuals = []
        for vf in sorted(page_file.parent.glob("visuals/*/visual.json")):
            vj = load(vf)
            if vj is None:
                continue
            vtype = (vj.get("visual") or {}).get("visualType") or ("group" if "visualGroup" in vj else "unknown")
            pos = vj.get("position", {})
            titles = [t for t in section_value(vj, "title", "text") if t]
            name = titles[0] if titles else vj.get("name", vf.parent.name)
            visuals.append({"file": vf, "json": vj, "type": vtype, "pos": pos, "title": titles[0] if titles else None,
                            "name": name})

        has_heading2 = False
        types_on_page = set()

        for v in visuals:
            vj, vtype, vf, label = v["json"], v["type"], v["file"], v["name"]
            types_on_page.add(vtype)
            if vtype == "group":
                continue

            # Headings
            title_heading = heading_level(section_value(vj, "title", "heading"))
            sub_heading = heading_level(section_value(vj, "subTitle", "heading"))
            all_heading_values = [literal(val) for _, val in walk(vj, lambda k: k.lower() == "heading")]
            if any(v_ and re.search(r"1\b", v_) for v_ in all_heading_values if isinstance(v_, str)):
                add("HDG-01", "FAIL", page_name, label, "Heading 1 is used. Level 1 is reserved for the Service.", vf)
            if vtype in SLICER_TYPES | BUTTON_TYPES and (title_heading or any(all_heading_values)):
                add("HDG-03", "FAIL", page_name, label, f"{vtype} has a heading assigned. Remove it.", vf)
            if vtype == "textbox" and heading_level(all_heading_values) == 2:
                has_heading2 = True
            if vtype not in ALT_EXEMPT_TYPES | SLICER_TYPES and v["title"]:
                if title_heading is None:
                    add("HDG-02", "WARN", page_name, label, "Visual title has no heading level. Expected Heading 3.", vf)
                elif title_heading != 3:
                    add("HDG-02", "FAIL", page_name, label, f"Visual title heading is {title_heading}. Expected 3.", vf)
            if sub_heading is not None and sub_heading != 4:
                add("HDG-02", "FAIL", page_name, label, f"Subtitle heading is {sub_heading}. Expected 4.", vf)

            # Titles and acronyms
            if vtype not in ALT_EXEMPT_TYPES and not v["title"]:
                add("TTL-01", "WARN", page_name, label, "No title text found on a non-decorative visual.", vf)
            for text in section_value(vj, "title", "text") + section_value(vj, "subTitle", "text"):
                found = acronyms(text, glossary)
                if found:
                    add("DES-05", "WARN", page_name, label, f"Possible acronyms: {', '.join(found)}. Expand or add to glossary.", vf)

            # Alt text
            alts = [a for a in section_value(vj, "general", "altText") if a]
            if vtype not in ALT_EXEMPT_TYPES and not alts:
                add("ALT-01", "FAIL", page_name, label, "Missing alt text.", vf)
            for alt in alts:
                if alt == "<dynamic>":
                    continue
                if alt.upper().startswith("DRAFT"):
                    add("ALT-04", "FAIL", page_name, label, "Alt text is still a draft placeholder pending review.", vf)
                    continue
                low = alt.lower()
                if v["title"] and v["title"].lower() in low:
                    add("ALT-02", "WARN", page_name, label, "Alt text repeats the title.", vf)
                hits = [w for w in VISUAL_TYPE_WORDS if re.search(rf"\b{re.escape(w)}\b", low)]
                if hits:
                    add("ALT-02", "WARN", page_name, label, f"Alt text names the visual type ({hits[0]}).", vf)
                if len(alt) < 25:
                    add("ALT-02", "WARN", page_name, label, f"Alt text may be too short to be meaningful: \"{alt}\".", vf)

            # Responsive
            resp = [literal(val) for _, val in walk(vj, lambda k: k == "responsive")]
            if any(r == "false" for r in resp):
                add("DES-09", "FAIL", page_name, label, "Responsive is turned off.", vf)

            # Decorative elements and tab order
            if vtype in DECORATIVE_TYPES:
                add("TAB-03", "MANUAL", page_name, label,
                    f"{vtype} should be hidden from tab order. Confirm in Selection pane > Tab order.", vf)

            # Reset button tooltip
            if vtype in BUTTON_TYPES:
                tips = [t for _, t in walk(vj, lambda k: k.lower() == "tooltip")]
                tip_text = " ".join(filter(None, (literal(t) if not isinstance(t, list) else "" for t in tips)))
                if "reset" in label.lower() or "clear" in label.lower():
                    if not tips:
                        add("VIS-02", "WARN", page_name, label, "Reset button has no custom tooltip.", vf)

            # Slicer position
            if vtype in SLICER_TYPES:
                x, y = v["pos"].get("x", 0), v["pos"].get("y", 0)
                if x > page_w * 0.25 and y > page_h * 0.25:
                    add("DES-02", "WARN", page_name, label, "Slicer is not at the top or left of the page.", vf)

            if vtype in MOUSE_ONLY_TYPES:
                add("KEY-02", "MANUAL", page_name, label,
                    "Mouse-only map. Confirm underlying data is on the page and noted in user instructions.", vf)

        # Page title
        if not has_heading2:
            add("HDG-02", "WARN", page_name, "(page)", "No text box with Heading 2 found for the page title.", page_file)

        # Tab order: compare tabOrder to reading order (rows banded by 40px)
        ordered = [v for v in visuals if v["type"] not in DECORATIVE_TYPES | {"group"} and "tabOrder" in v["pos"]]
        tab_values = [v["pos"]["tabOrder"] for v in ordered]
        dupes = sorted({t for t in tab_values if tab_values.count(t) > 1})
        if dupes:
            add("TAB-01", "FAIL", page_name, "(page)",
                f"Duplicate tabOrder values {dupes}. Keyboard order is undefined. Assign a unique, reading-order sequence.",
                page_file)
        missing = [v["name"] for v in visuals if v["type"] not in DECORATIVE_TYPES | {"group"} and "tabOrder" not in v["pos"]]
        if missing:
            add("TAB-01", "WARN", page_name, "(page)", f"No tabOrder set on: {', '.join(missing)}.", page_file)
        if len(ordered) >= 2 and not dupes:
            by_tab = [v["name"] for v in sorted(ordered, key=lambda v: v["pos"]["tabOrder"])]
            by_read = [v["name"] for v in sorted(ordered, key=lambda v: (round(v["pos"].get("y", 0) / 40), v["pos"].get("x", 0)))]
            if by_tab != by_read:
                add("TAB-01", "WARN", page_name, "(page)",
                    "Tab order differs from left-to-right, top-to-bottom. Confirm it follows a documented logical sequence. "
                    f"Tab order: {' > '.join(by_tab)}", page_file)

        # Flow: KPIs should sit above tables
        kpi_y = [v["pos"].get("y", 0) for v in visuals if v["type"] in KPI_TYPES]
        tbl_y = [v["pos"].get("y", 0) for v in visuals if v["type"] in TABLE_TYPES]
        if kpi_y and tbl_y and min(kpi_y) > min(tbl_y):
            add("DES-04", "WARN", page_name, "(page)", "A table or matrix appears above KPI cards.", page_file)

        # User instructions needed
        triggers = types_on_page & INSTRUCTION_TRIGGER_TYPES
        if triggers:
            add("VIS-03..08", "MANUAL", page_name, "(page)",
                f"Page has {', '.join(sorted(triggers))}. Confirm user instructions cover the required notes.", page_file)

    # Report-level manual tests (always listed)
    for rule, msg in [
        ("KEY-01", "Navigate every page with keyboard only."),
        ("KEY-03", "Confirm Show Data Table and Show Visual as Table are labeled and navigable."),
        ("COL-06", "Test with Windows high-contrast settings."),
        ("VIS-01", "Test keyboard order through plot area, legend, and axis on visuals with legends."),
        ("COL-05", "Check palette with a color-blindness simulator."),
    ]:
        add(rule, "MANUAL", "(report)", "", msg, report_dir)


def to_markdown():
    order = {"FAIL": 0, "WARN": 1, "MANUAL": 2, "INFO": 3}
    rows = sorted(findings, key=lambda f: (order.get(f["status"], 9), f["page"], f["rule"]))
    counts = {s: sum(1 for f in findings if f["status"] == s) for s in order}
    lines = [
        f"**Summary:** {counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['MANUAL']} MANUAL",
        "",
        "| Status | Rule | Page | Visual | Finding | File |",
        "|---|---|---|---|---|---|",
    ]
    for f in rows:
        msg = f["message"].replace("|", "\\|")
        lines.append(f"| {f['status']} | {f['rule']} | {f['page']} | {f['visual']} | {msg} | `{f['file']}` |")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    check_report(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(findings, indent=2))
    else:
        print(to_markdown())
    sys.exit(1 if any(f["status"] == "FAIL" for f in findings) else 0)
