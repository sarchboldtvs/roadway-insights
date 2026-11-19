---
applyTo: "**/*.Report/**,**/_brief/**"
description: "Team Power BI report standards. Overlays the powerbi-report-cli skill (microsoft/skills-for-fabric). Applies whenever Copilot plans, reads, creates, or edits PBIP report files."
---

# Power BI Report Standards (Always On)

## How this fits with the Fabric skills

- **`powerbi-report-cli`** (from `microsoft/skills-for-fabric`, plugin `powerbi-authoring`) is the **builder**.
  It owns planning, design, PBIR authoring, `powerbi-report-author validate`, preview, screenshots, and publishing.
  Follow its mode workflow and approval gates as written.
- **This repository's standards are the acceptance criteria.** The full standard is
  `.aidlc/standards/powerbi/development-checklist.md`. Rule IDs below refer to it.
- **When the two conflict, the team standard wins.** The known conflicts are listed below. Do not edit the
  Fabric skill files; they are updated by the plugin. Apply the override at the point of use.
- For the full end-to-end workflow use the `powerbi-standards-build` skill. For audits use `powerbi-standards-review`.

## Known conflicts with powerbi-report-cli defaults (team standard wins)

| Topic | Fabric skill default or example | Team standard |
|---|---|---|
| Alt text | Template "Chart Structure + Notable Finding" begins with the chart type ("Bar chart showing...") | Never name the visual type or repeat the title. Describe purpose, measures, categories, or key insight (ALT-02) |
| Alt text process | Written directly into `visual.json` | Draft in `docs/alt-text/<Report>-alt-text.md` first; apply only after human review (ALT-04) |
| Tab order | Examples set `tabOrder: 1000` on most visuals; "usually matches z"; shapes get a tabOrder | Unique values in reading order (left to right, top to bottom). Shapes and decorative images excluded (TAB-01, TAB-03) |
| Headings | No heading hierarchy defined | Never Heading 1. Page title Heading 2, visual title Heading 3, subtitle Heading 4. Slicers and reset buttons: none (HDG-01 to HDG-03) |
| Palette | Base theme `dataColors` (Okabe-Ito) include `#E69F00`, `#56B4E9`, `#CC79A7`, `#F0E442`, which fall below 3:1 on the default `#F3F2F1` page background | Every data color at least 3:1 against the actual page background; run `contrast_check.py` on any theme before use (COL-03) |
| Layout | Archetype layouts may place slicers anywhere | Slicers top or left; legends top or left; KPIs, then charts, then tables (DES-02 to DES-04) |
| Responsive / page view | Not specified | Visuals Responsive on; page view per DES-08 |
| User instructions | Not generated | Required notes for slicers, cards, matrices, ESRI maps, drill-down (VIS-03 to VIS-08) |

## Rules for every change

1. Work only in PBIR format. If the report is `.pbix` or legacy `report.json`, stop and point to the README conversion steps.
2. Use the `powerbi-report-author` CLI metadata to get property names and enum values. Never invent schema.
3. Headings, alt text, tab order, titles, layout, color, and responsive settings follow the table above and the checklist.
4. Never rely on color alone; add data labels, markers, or text (COL-04).
5. Reset button tooltip: "Clear all slicers in the filter panel" (VIS-02).

## Honesty about verification

`powerbi-report-author validate` confirms schema validity only, not standards compliance.
Keyboard navigation, screen reader output, high-contrast mode, and Show Data Table behavior
cannot be verified from JSON or screenshots. Never state that these pass; list them as manual tests.
Never describe a report as "accessible" or "compliant"; say it passed automated checks.
