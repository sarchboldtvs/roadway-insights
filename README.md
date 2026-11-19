# Roadway Insights (AI-DLC pilot)

Delivered with the Triverus AI-DLC (kit version in `.aidlc/KIT_VERSION`).

| Folder | What |
|---|---|
| `terraform/` | Snowflake account layer (roles, warehouses, databases, integrations). CI applies. |
| `snowflake/` | Snowflake DCM project: schemas and objects in them. |
| `powerbi/` | PBIP projects (semantic models and reports). |
| `contracts/` | ODCS data contracts between Snowflake and Power BI. |
| `docs/` | Phase documents (see docs/lifecycle.md). |
| `.aidlc/` | Standards and scripts synced from the kit. Don't edit. |

## Getting started

1. Workstation: run `Install-AidlcPrereqs.ps1 -Role <lead|snowflake|platform|bi>` from the kit's `bootstrap/workstation`.
2. Open this folder in the GitHub Copilot App. Trust the repo when asked
   (plugins and hooks load from `.github/copilot/settings.json` and `.github/hooks/`).
3. Start a new session and run `/aidlc-ready`.
4. Ask: "Which rules are you following in this repo?" It should describe six phases.
