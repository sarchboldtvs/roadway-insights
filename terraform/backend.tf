# State in S3 with native locking. bucket and region come from CI
# (-backend-config). One key per layer and environment.
terraform {
  backend "s3" {
    key          = "roadway-insights/account-layer.tfstate"
    use_lockfile = true
    encrypt      = true
  }
}
