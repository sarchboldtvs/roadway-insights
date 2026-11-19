terraform {
  required_version = ">= 1.10"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.23" # pin a minor version; review the migration guide before bumping
    }
  }
}
