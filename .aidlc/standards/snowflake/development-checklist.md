# Snowflake (DCM) Development Checklist (Source of Truth)

Applies to `snowflake/` DCM projects. Verify: **AUTO** (script),
**AI** (agent reads definitions), **MANUAL** (a person; never marked passed by an agent).
dbt rules (dbt Labs style guide, dbt-project-evaluator) join in phase 2.

## SRC Source control
| ID | Rule | Verify |
|---|---|---|
| SRC-01 | Every changed schema-level object is defined in `snowflake/sources/definitions/` | AUTO (plan shows only expected objects) |
| SRC-02 | Unmanaged objects are adopted (own commit, no-change plan) before they change | AI + plan |
| SRC-03 | No literal environment names (DEV_, PROD_) in definitions; use templating | AUTO (dcm_lint) |
| SRC-04 | No credentials, account identifiers or tokens in the repo | AUTO (leak_scan) |
| SRC-05 | One owner per object: account objects in Terraform, schema-level in DCM | AI |

## NAM Naming
| ID | Rule | Verify |
|---|---|---|
| NAM-01 | Objects are UPPER_SNAKE_CASE | AUTO |
| NAM-02 | Layer schemas: RAW, STAGING, MARTS (agree others in the technology doc) | AI |
| NAM-03 | Mart objects: FCT_ (facts), DIM_ (dimensions) | AUTO (warn) |

## SQL Style
| ID | Rule | Verify |
|---|---|---|
| SQL-01 | sqlfluff passes with `.aidlc/config/.sqlfluff` | AUTO |
| SQL-02 | No `SELECT *` in views or dynamic tables under MARTS | AUTO |
| SQL-03 | Every object has a COMMENT | AUTO (warn) |

## MOD Modeling
| ID | Rule | Verify |
|---|---|---|
| MOD-01 | Grain is stated in the object COMMENT and matches the contract `grain` | AI |
| MOD-02 | Contracted columns, names and types match the pinned contract | AUTO (contract-test) |
| MOD-03 | Primary key columns are NOT NULL and unique (contract quality rules) | AUTO (contract-test) |

## SEC Security and governance
| ID | Rule | Verify |
|---|---|---|
| SEC-01 | No GRANT to PUBLIC, no grants to users | AUTO (dcm_lint) |
| SEC-02 | Restricted and confidential columns carry the classification tag so tag-based masking applies | AI |
| SEC-03 | Power BI reads MARTS only, through PBI_*_RO roles | AI |
| SEC-04 | No row-level data in repo, issues or PRs | AUTO (leak_scan, warn in pilot) |

## DEP Deployment
| ID | Rule | Verify |
|---|---|---|
| DEP-01 | DEV plan reviewed and confirmed by a person before deploy | Process |
| DEP-02 | No DROP of database, schema, table or stage without technology lead approval recorded on the issue | AUTO (plan_lint) |
| DEP-03 | Agents deploy DEV only; PROD only via the release workflow | Hooks + RBAC |
| DEP-04 | Data-changing steps (backfills) are written as separate, reviewed run steps | AI |

## PRF Cost and performance
| ID | Rule | Verify |
|---|---|---|
| PRF-01 | Dynamic tables state TARGET_LAG and warehouse with a reason | AI |
| PRF-02 | Tasks name a warehouse sized XS unless the technology doc justifies more | AI |
| PRF-03 | Large tables: clustering considered and the decision recorded | AI |
