<!-- File as: Doc change form. Title: "Docs: Pilot 0 readiness check" -->
# Pilot 0: readiness check

Run `/aidlc-ready` for each person and role, record results in
`docs/solutions/pilot-0-readiness.md`, and update the kit's `docs/VERIFY.md`
with findings.

## Who
- [ ] Lead / product owner: <name>
- [ ] Snowflake engineer: <name>
- [ ] Platform engineer: <name>
- [ ] BI developer: <name>

## Checks beyond /aidlc-ready
- [ ] Guard hook refuses `terraform apply -help`, `gh issue edit <n> --add-label dev-verified`, `git push origin main`
- [ ] `tf-plan` workflow on an empty Terraform change posts a plan; `tf-apply` waits for `snowflake-dev` approval
- [ ] `dcm-plan` workflow plans an empty DCM project
- [ ] `contract-test` workflow runs (expect "no contract" failure is fine)
- [ ] `leak-scan` warns on a test comment containing a fake email
- [ ] Board sync labels a test issue moved Backlog -> Design -> Backlog
- [ ] CoCo: SQL write refused under the read-only lock; masking hides INSPECTOR_EMAIL for AIDLC_DEV_RO
