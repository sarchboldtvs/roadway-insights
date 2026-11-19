# Credentials come only from CI environment variables (SNOWFLAKE_*), as
# TF_ACCOUNT_CI. Nothing here, nothing on workstations.
provider "snowflake" {
  preview_features_enabled = [] # TF-06: add only with technology lead approval
}
