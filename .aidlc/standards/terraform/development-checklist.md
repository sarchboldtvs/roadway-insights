# Terraform (Snowflake account layer) Checklist (Source of Truth)

Scope: roles and hierarchy, warehouses, databases, integrations, resource
monitors. Schema-level objects and object grants belong to DCM.

| ID | Rule | Verify |
|---|---|---|
| TF-01 | `terraform fmt`, `validate` and tflint pass | AUTO |
| TF-02 | Provider `snowflakedb/snowflake` pinned to a minor version | AUTO (tflint) |
| TF-03 | Every adopted object has an import block and its first plan shows no changes | CI plan |
| TF-04 | Every database has `prevent_destroy = true` | AUTO (plan_lint warn) + AI |
| TF-05 | No destroy or replace of database, schema, role or warehouse without technology lead approval on the issue | AUTO (plan_lint) |
| TF-06 | No preview resources unless the technology doc approves them | AI |
| TF-07 | No ACCOUNTADMIN grants; no grants to PUBLIC | AI |
| TF-08 | Applies only through CI (`tf-apply`, `release`) | Hooks + no credentials |
| TF-09 | Role membership for people comes from the IdP (SCIM), never from Terraform | AI |
| TF-10 | Data access for AIDLC_PROD_RO is granted per domain in `terraform/access/<domain>.tf`, owned by the data owner (CODEOWNERS) | AI + CODEOWNERS |
