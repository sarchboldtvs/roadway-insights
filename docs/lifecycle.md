# Lifecycle

Six phases. People move cards; Board sync sets labels, owners and checklists;
agents act for the column. Rules for assistants: [AGENTS.md](../AGENTS.md).

## Board columns

| Column | Phase | Labels Board sync sets | Who uses it |
| --- | --- | --- | --- |
| Backlog | 1 Discovery | `phase:1-discovery` | parent |
| Design | 2 Experience Design | `phase:2-design` | parent |
| Technical | 3 Technology Direction | `phase:3-technology` | parent |
| Ready | Plan approved | `plan-approved` | parent, sub-issues |
| In Progress | 4 Engineering | `phase:4-engineering`, `plan-approved` | sub-issues (parent waits here) |
| Acceptance | 5 Verification and Acceptance | `phase:5-acceptance` | sub-issues |
| Release | 6 Release | `phase:6-release` | parent |
| Done | Accepted | `accepted` (+ last phase label) | all; the issue closes |

## Parent and sub-issues

1. The parent runs Discovery, Design, Technical.
2. In Technical the architect drafts one sub-issue per target and the
   contract PR. When a person moves the parent to Ready, they also put the
   sub-issues in Ready. Moving the parent to In Progress means "build".
3. Sub-issues run In Progress and Acceptance in order:
   terraform (DEV applied by CI, re-plan clean) -> snowflake (DEV deployed,
   contract test, `dev-verified` set by the Snowflake lead) -> powerbi.
4. A sub-issue goes to Done when its PR is merged after acceptance.
5. When every sub-issue is Done, a person moves the parent to Release. The
   release-coordinator writes the package; the release approver runs the
   `release` workflow (environment `prod`); then the parent goes to Done.

## Human gates

| Gate | Phase | Who | Mechanism | Type |
| --- | --- | --- | --- | --- |
| Data access approval | 1 | Data owner | PR to `terraform/access/<domain>.tf` (CODEOWNERS), CI applies | Hard |
| Target triage | 1 | Product owner | Targets in the plan; card move | Soft |
| Contract sign-off | 3 | Snowflake + BI leads | `contracts/` PR, CODEOWNERS | Hard |
| Plan approval | 3 | Technology lead | Card to Ready | Hard |
| Terraform plan approval | 4 | Platform lead | `tf-apply` behind `snowflake-dev` environment | Hard |
| DCM DEV deploy | 4 | Snowflake engineer | Confirms plan in chat; CoCo DEPLOY prompt | Soft |
| dev-verified | 4 | Snowflake lead | `contract-test` evidence, then label | Hard |
| Alt text review | 4 | BI developer / PO | powerbi-standards-build Gate 3 | Soft |
| Reconciliation + accessibility | 5 | PO + assurance | Contract quality results; manual tests | Soft |
| Breaking contract change | any | Leads + consumer teams | `contract-check` | Hard |
| Release | 6 | Release approver | `release` workflow, `prod` environment | Hard |

## Exit checklists

Board sync posts them (`.aidlc/scripts/board-sync.sh`).

## Folders

| Folder | What | Phase |
| --- | --- | --- |
| docs/product.md, docs/concepts.md | Product brief, concepts | all |
| docs/plans/ | Requirements, then implementation plan | 1, 3 |
| docs/design/ | Report briefs, wireframes | 2 |
| docs/technology/ | Architecture, decisions, adoption list | 3 |
| contracts/ | ODCS data contracts | 3 |
| terraform/ | Account layer (Terraform) | 4 |
| snowflake/ | DCM project | 4 |
| powerbi/ | PBIP projects | 4 |
| docs/acceptance/, reviews/ | Test plans, summaries, review reports | 5 |
| docs/releases/ | Release packages | 6 |
| docs/solutions/ | Lessons | 5 |

`<issue-name>` = issue number + 2 to 4 lowercase words, e.g. `12-road-issues-monthly`.
