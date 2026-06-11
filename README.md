# AWS Read Only MCP Server

## Overview
This repository contains a read-only MCP server for investigating AWS S3 usage and supporting improvement decisions across cost, security, and maintainability.

The initial scope is limited to read-only access for:
- Amazon S3
- AWS Cost Explorer
- S3 Storage Lens
- S3 Inventory
- CloudWatch metrics
- AWS Config
- IAM Access Analyzer
- CloudTrail data events
- S3 server access logs

This server is intended to support:
- S3 inventory and usage assessment
- cost breakdown analysis
- security and access review
- lifecycle and operational review
- migration-vs-optimization decision support

## Scope
### In scope
- Read-only information retrieval from AWS
- Bucket metadata and configuration review
- Cost and request pattern analysis
- Security posture inspection
- Lifecycle and operational hygiene checks
- Structured outputs for downstream analysis

### Out of scope
- Deleting objects or buckets
- Updating bucket settings
- Changing lifecycle rules
- Changing IAM, bucket policy, ACL, or KMS configuration
- Executing migrations
- Any write or destructive AWS operation

## Proposed Repository Structure
```text
.
├── README.md
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   └── operations.md
├── src/
│   ├── server/
│   ├── aws/
│   ├── schemas/
│   └── services/
├── tests/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── validate-config.yml
│       └── release.yml
├── .env.example
└── pyproject.toml
```

## Suggested MCP Tools
Initial tool candidates:
- `list_s3_buckets`
- `get_s3_bucket_details`
- `get_s3_bucket_security`
- `get_s3_lifecycle_status`
- `get_s3_cost_summary`
- `get_s3_request_metrics`
- `get_s3_transfer_summary`
- `list_missing_data_for_assessment`

## Authentication Strategy
Preferred approach:
- AssumeRole with a dedicated read-only IAM role
- Temporary credentials over long-lived credentials
- Explicit target AWS account and region scope

## Required Configuration
Expected environment variables:
- `AWS_ROLE_ARN`
- `AWS_REGION`
- `MCP_AUTH_TOKEN`
- `APP_ENV`
- `LOG_LEVEL`
- `DEFAULT_LOOKBACK_MONTHS`
- `ENABLED_SERVICES`

## GitHub Actions
This repository includes workflow skeletons for:
- CI validation
- configuration validation
- release preparation

### CI workflow
Checks:
- lint
- formatting
- unit tests
- type checks

### Config validation workflow
Checks:
- required environment variables
- IAM role ARN format
- region configuration
- configuration completeness

### Release workflow
Supports:
- packaging
- artifact creation
- release preparation
- optional deployment preparation

## Secrets and Variables
### GitHub Secrets
- `AWS_ROLE_ARN`
- `AWS_REGION`
- `MCP_AUTH_TOKEN`
- `KMS_KEY_ID` (optional)

### GitHub Variables
- `APP_ENV`
- `LOG_LEVEL`
- `DEFAULT_LOOKBACK_MONTHS`
- `ENABLED_SERVICES`

## Cloud Shell or Local Terminal Tasks
Only use Cloud Shell or another terminal when GitHub and GitHub Actions cannot complete the task directly.
Typical examples:
- creating the AWS IAM role
- validating AWS identity manually
- enabling or confirming Storage Lens / Inventory
- manual bootstrap steps for first deployment

When documenting those steps, always include:
- purpose
- where to run the command
- command
- expected result
- troubleshooting hints

## Recommended Next Steps
1. Add `docs/architecture.md`
2. Add `docs/setup.md`
3. Implement the minimal server entrypoint
4. Add AWS service wrappers
5. Connect workflows to the actual runtime and packaging approach
