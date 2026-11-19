# Snowflake DCM project

Definitions in `sources/definitions/*.sql` (DEFINE, GRANT, ATTACH only).
Use `{{ db }}`; never literal DEV_/PROD_ names.

```
snow dcm plan   --target DEV --connection aidlc_dev_rw --save-output
snow dcm deploy --target DEV --connection aidlc_dev_rw   # after a person confirms the plan
```
PROD deploys only through the `release` workflow.
