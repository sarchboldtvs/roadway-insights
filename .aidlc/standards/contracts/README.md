# Data contract conventions

- Format: Open Data Contract Standard (ODCS) v3.1. Tooling: Data Contract CLI.
- One contract per data product: `contracts/<domain>/<product>.odcs.yaml`.
- Merged = signed. CODEOWNERS for `contracts/` requires the Snowflake lead and the BI lead.
- Version: semver. Breaking (removed/renamed column, type change, new required
  column, grain change) = major, and every consumer team in `consumers` must approve.
- `status`: `draft` on the branch, `active` when merged.
- Servers: `dev` and `prod` only. No credentials in contracts.
- Classification values: `public`, `internal`, `restricted` (PII, masked for
  AIDLC_* roles), `confidential` (aggregates only or no agent access).
- Every contract has at least one SQL reconciliation quality rule.
- Grain is a custom property on each object; ODCS has no grain field.
- Measures and DAX are not in contracts; they live in the semantic model spec.
