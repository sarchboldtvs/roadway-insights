# Power BI Development Checklist (Source of Truth)

This file is the single source of truth for report standards. The build skill, the review skill,
and the always-on instructions all reference it. Update standards here only.

Each rule has an ID and a verification method:

- **AUTO**: checked by `.aidlc/scripts/pbir_lint.py` or `contrast_check.py`
- **AI**: Copilot checks by reading page and visual JSON
- **MANUAL**: requires a person testing in Power BI Desktop or the Service. Copilot must never mark these as Pass.

## Design

| ID | Rule | Verify |
|---|---|---|
| DES-01 | Recurring filters, navigation, titles, and instructional elements appear consistently (same position, size, style) across all pages | AI |
| DES-02 | Filters (slicers) are at the top or left of the page | AUTO |
| DES-03 | Legends are above or to the left of the plot area | AI |
| DES-04 | Visuals flow from high level to detail, top to bottom (KPI cards, then line/bar charts, then tables/matrices) | AUTO + AI |
| DES-05 | No acronyms or jargon in titles, labels, or instructions (unless on the approved glossary) | AUTO + AI |
| DES-06 | Overly complicated visuals are simplified or split | AI |
| DES-07 | Unnecessary gridlines, labels, and repetitive text are removed | AI |
| DES-08 | Report page view is set to fixed width by default (confirm team meaning; see README) | AI |
| DES-09 | Visuals have Responsive turned on | AUTO |

## Colors

| ID | Rule | Verify |
|---|---|---|
| COL-01 | Normal text has at least 4.5:1 contrast with its background | AUTO |
| COL-02 | Large text (18pt+, or 14pt+ bold) has at least 3:1 contrast with its background | AUTO |
| COL-03 | Data categories have at least 3:1 contrast with the background and with neighboring category colors; otherwise use white space or borders between them | AUTO |
| COL-04 | Color is never the only way meaning is conveyed (add data labels, markers, patterns, or text) | AI |
| COL-05 | Avoid color combinations that are hard to distinguish with color blindness (for example red/green pairs) | AI + MANUAL |
| COL-06 | Report tested with Windows high-contrast settings | MANUAL |

## Tab Order

| ID | Rule | Verify |
|---|---|---|
| TAB-01 | Tab order is generally left to right, top to bottom, unless a documented logical sequence differs | AUTO |
| TAB-02 | Related visuals (for example slicers in a filter panel) are grouped so keyboard users can skip the group | AI |
| TAB-03 | Non-interactive elements (shapes, images, data as-of tables) are excluded from tab order | AUTO + MANUAL |

## Headings

| ID | Rule | Verify |
|---|---|---|
| HDG-01 | Heading level 1 is never used (reserved for the Service) | AUTO |
| HDG-02 | Page title = Heading 2, visual titles = Heading 3, visual subtitles = Heading 4 | AUTO |
| HDG-03 | Slicer titles and reset button labels have no heading assigned | AUTO |

## Titles, Labels, Markers, Legends

| ID | Rule | Verify |
|---|---|---|
| TTL-01 | Every non-decorative visual has a descriptive title, without jargon or acronyms | AUTO + AI |
| TTL-02 | Axis labels, units, and legend values are descriptive and understandable | AI |
| TTL-03 | Labels and markers do not create unnecessary clutter | AI |
| TTL-04 | If category labels are shown in the plot area, the legend is turned off | AI |
| TTL-05 | Consider a subtitle measure that dynamically lists the filters applied to the visual | AI (recommendation) |

## Alt Text

| ID | Rule | Verify |
|---|---|---|
| ALT-01 | Every non-decorative visual and object has alt text | AUTO |
| ALT-02 | Alt text describes purpose, measures, categories, or key insight. It does not repeat the title or name the visual type | AUTO + AI |
| ALT-03 | Use dynamic (measure-based) alt text where filtering could make static text inaccurate | AI |
| ALT-04 | Alt text is drafted in a separate document and reviewed before being added to the report | Process |

## Keyboard Navigation and Data Tables

| ID | Rule | Verify |
|---|---|---|
| KEY-01 | Every page can be fully navigated without a mouse | MANUAL |
| KEY-02 | Mouse-only visuals (for example ESRI maps) have the underlying data elsewhere on the page and a note in the user instructions | AI + MANUAL |
| KEY-03 | Show Data Table and Show Visual as Table are labeled and navigable as expected | MANUAL |

## Specific Visualizations

| ID | Visual | Rule | Verify |
|---|---|---|---|
| VIS-01 | All with legends | Keyboard order through plot area, legend, and axis is tested; user instructions note any mismatch | MANUAL |
| VIS-02 | Reset button | Tooltip is descriptive (for example "Clear all slicers in the filter panel"); no heading on its label | AUTO + AI |
| VIS-03 | Slicer | No heading on its title. User instructions note that slicers do not announce selections; filter context is added to subtitles or alt text of affected visuals | AUTO + AI |
| VIS-04 | Card | Included in tab order. User instructions note it may be announced as a table and is not interactive | AI |
| VIS-05 | Heatmap / gradient | Data labels or legend present; high-contrast outline or white space between cells | AI |
| VIS-06 | Matrix | User instructions explain expand/collapse and keyboard navigation | AI |
| VIS-07 | Map | ESRI maps: underlying data shown elsewhere on page; keyboard limitation noted in user instructions | AI + MANUAL |
| VIS-08 | Drill-down | Prefer splitting into separate visuals; if used, include navigation instructions | AI |

## Data Contract (AI-DLC multi-stack)

| ID | Rule | Verify |
|---|---|---|
| CON-01 | Every Snowflake source object used by the semantic model is in the pinned contract | AUTO (`contract_pbi_check.py`) |
| CON-02 | Every source column used by the model exists in the contract | AUTO |
| CON-03 | Column display names match the contract `businessName`; descriptions copied from the contract | AUTO (warn) + AI |
| CON-04 | The model connects through `PBI_DEV_RO` (DEV workspace) or `PBI_PROD_RO` (PROD), never a person's account | AI + MANUAL |

## Approved Glossary (acronyms allowed without expansion)

Add terms your audience universally understands. The lint script reads this list.

<!-- glossary-start -->
- FY
- YTD
- ID
<!-- glossary-end -->
