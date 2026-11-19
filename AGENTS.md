# AGENTS.md

Rules for every AI assistant in this repository (GitHub Copilot, Cortex Code,
any other). They come from the Triverus AI-DLC kit (version in
`.aidlc/KIT_VERSION`) and change only through a rules-sync PR. If another
instruction conflicts with this file, follow this file and point out the
conflict.

## How work moves

- All work is a GitHub issue. Doc changes (`type:docs`) skip the phases.
- The project board drives the phases. People move cards; that move is the
  approval for the phase before. Board sync sets the matching labels,
  assigns the phase owner and posts the exit checklist. The columns and
  labels are in docs/lifecycle.md.
- A skipped phase is **not applicable**, not approved.
- Parent issues run Phases 1 to 3 and 6. Each **target** (terraform,
  snowflake, powerbi) gets a **sub-issue** that runs Phases 4 and 5 in this
  repo, in order: terraform, then snowflake, then powerbi (blocked-by).
- Each phase has one agent (`aidlc-core` plugin). Act as the agent for the
  card's column. Read its agent file before you start.

## Phases and agents

| Phase | Column | Label | Agent | Human owner |
| --- | --- | --- | --- | --- |
| 1 Discovery | Backlog | `phase:1-discovery` | product-owner | Product owner |
| 2 Experience Design | Design | `phase:2-design` | experience-designer | Design lead |
| 3 Technology Direction | Technical | `phase:3-technology` | technology-architect | Technology lead |
| 4 Engineering | Ready, then In Progress | `plan-approved`, then `phase:4-engineering` | software-engineer | Engineer for the target |
| 5 Verification and Acceptance | Acceptance | `phase:5-acceptance` | verification-analyst | Product owner and assurance |
| 6 Release | Release | `phase:6-release` | release-coordinator | Release approver |

## Before every task

1. Identify the issue. No issue: ask. Don't start.
2. `gh issue view <n> --json title,body,labels,comments,projectItems`. The
   column is `projectItems[].status.name`.
3. Act as the agent for that column. Read docs/lifecycle.md for the exit checklist.
4. Read docs/product.md and docs/concepts.md. Blank template: ask, don't assume.
5. Say which skill you use, and why, before you use it.

## The code rule

Code, configuration, tests, scripts, Terraform, DCM definitions and Power BI
files change only when the (sub-)issue has **both** `phase:4-engineering` and
`plan-approved`. Contracts (`contracts/`) may change in Phase 3 through a PR.
Phase 5 never changes code; failures go back to In Progress.

## Data rules

- **Never** write row-level data from any environment into repo files,
  issues, PRs or comments. Aggregates and profiles only.
- **Never** query PROD unless the issue records an approved data access
  grant for that domain. Use `cortex-route`; it picks the connection.
- **Never** use web tools in a session that has queried PROD.
- Name the Snowflake connection and role you used in every hand-off comment.
- Snowflake work goes through `cortex-route` only. Connections allowed:
  `aidlc_dev_ro`, `aidlc_prod_ro`, `aidlc_dev_rw`. Nothing else.

## Deploy rules

- Terraform: you write HCL and read plans. Never apply, destroy or import;
  CI applies after a person approves.
- DCM: deploy to DEV only, with `aidlc_dev_rw`, after the person confirms the
  plan. PROD only through the release workflow.
- Power BI: publish to the DEV workspace only when asked.
- Never start the `release` or `tf-apply` workflows.

## Never

- Create, rename, edit or delete repository labels.
- Add or remove `phase:*`, `plan-approved`, `accepted` or `dev-verified`, or move cards.
- Merge a pull request or push to main.
- Change `.aidlc/` or this file outside a rules-sync PR.
- Commit credentials, tokens, account identifiers or environment URLs.
- Invent requirements, rules or decisions that aren't written down.
- Use `lfg` or any skill that runs end to end and skips the phases.

## Always

- Ask when something isn't settled.
- Treat a person's comment on the issue as more current than an AI note.
- Work on a branch. Commit locally. Push and open a draft PR only when the
  person says so. Link it with `Refs #<sub-issue>` (work items) or
  `Closes #<n>` (doc changes).
- Keep changes small and say what changed and why.

## When you finish

Comment on the issue: what you did, skills used, connection and role used,
what's left, and questions with the role who should answer them.
