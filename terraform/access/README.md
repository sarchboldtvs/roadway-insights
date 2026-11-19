# Data access grants for agents

One file per domain: `<domain>.tf`, granting that domain's read database role
in PROD to `AIDLC_PROD_RO`. CODEOWNERS for this folder is the data owners
team: merging the PR is the **data access approval**. Revoke by removing the
grant in a PR. Record the PR link on any issue that profiles that domain.
