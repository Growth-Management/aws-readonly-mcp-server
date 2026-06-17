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

## Implemented HTTP Endpoints
The server exposes health and read-only tool endpoints:

- `GET /health`
- `GET /mcp/actions`
- `GET /tools/get_caller_identity`
- `GET /tools/list_s3_buckets`
- `GET /tools/get_s3_bucket_details?bucket=<bucket-name>`
- `GET /tools/get_s3_bucket_security?bucket=<bucket-name>`
- `POST /mcp`

All `/mcp/actions`, `/tools/*`, and `/mcp` endpoints require:

```text
Authorization: Bearer <MCP_AUTH_TOKEN>
```

## Implemented MCP Tools
The `/mcp` endpoint supports the JSON-RPC methods needed for basic MCP tool discovery and tool calls:

- `initialize`
- `tools/list`
- `tools/call`

The `/mcp` endpoint also supports lightweight action discovery requests:

- `list_actions`
- `get_action_definition`

Available tools:

- `get_caller_identity`
- `list_s3_buckets`
- `get_s3_bucket_details`
- `get_s3_bucket_security`

Example MCP tool list request:

```bash
curl -sS -X POST \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  "${SERVICE_URL}/mcp" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Example MCP action list request:

```bash
curl -sS -X POST \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  "${SERVICE_URL}/mcp" \
  -d '{"action":"list_actions","params":{}}'
```

Example MCP tool call:

```bash
curl -sS -X POST \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  "${SERVICE_URL}/mcp" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_s3_bucket_security","arguments":{"bucket_name":"hbs-report"}}}'
```

## ChatGPT MCP Connection Readiness
The repository now provides a remote MCP-compatible endpoint at:

```text
POST <Cloud Run service URL>/mcp
```

The current Cloud Run deployment is private. Direct ChatGPT connection requires one of these connection decisions before registering the endpoint:

1. Keep Cloud Run private and front it with an approved authenticated gateway or tunnel.
2. Allow unauthenticated Cloud Run ingress while keeping the app-level `MCP_AUTH_TOKEN` bearer check.
3. Add an OAuth-based authentication layer if the ChatGPT MCP connection flow requires OAuth for this workspace.

Until that exposure/authentication decision is made, use `gcloud run services proxy` for validation from Cloud Shell.

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

## Authentication Strategy
Preferred approach:
- AssumeRole with a dedicated read-only IAM role
- Temporary credentials over long-lived credentials
- Explicit target AWS account and region scope

The current speed-priority bootstrap path uses GitHub Secrets for an AWS bootstrap access key, then assumes `AWS_ROLE_ARN` at runtime.

## Required Configuration
Expected environment variables:
- `AWS_ROLE_ARN`
- `AWS_REGION`
- `MCP_AUTH_TOKEN`
- `APP_ENV`
- `LOG_LEVEL`
- `DEFAULT_LOOKBACK_MONTHS`
- `ENABLED_SERVICES`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_EXTERNAL_ID` (optional)
- `AWS_ROLE_SESSION_NAME` (optional)

## GitHub Actions
This repository includes workflows for:
- CI validation
- Cloud Run deployment

The Cloud Run deployment workflow runs on manual dispatch or when `.github/deploy-triggers/cloud-run.txt` is updated.

## Cloud Shell Validation
Use Cloud Shell only for private Cloud Run validation or cloud-side checks that cannot be completed from GitHub Actions.

```bash
PROJECT_ID=sysmgmt-cloudrun-bridge
REGION=asia-northeast1
SERVICE=aws-readonly-mcp-server

gcloud config set project "$PROJECT_ID"

gcloud run services proxy "$SERVICE" \
  --region="$REGION" \
  --port=8081 &
PROXY_PID=$!

sleep 5

MCP_AUTH_TOKEN="$(
  gcloud run services describe "$SERVICE" \
    --region="$REGION" \
    --format=json \
  | jq -r '.spec.template.spec.containers[0].env[] | select(.name=="MCP_AUTH_TOKEN").value'
)"

curl -sS \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  "http://localhost:8081/tools/get_s3_bucket_details?bucket=hbs-report" \
  | jq .

curl -sS \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  "http://localhost:8081/tools/get_s3_bucket_security?bucket=hbs-report" \
  | jq .

curl -sS \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  http://localhost:8081/mcp/actions \
  | jq .

curl -sS -X POST \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  http://localhost:8081/mcp \
  -d '{"action":"list_actions","params":{}}' \
  | jq .

curl -sS -X POST \
  -H "Authorization: Bearer ${MCP_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  http://localhost:8081/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | jq .

kill "$PROXY_PID"
```

## Recommended Next Steps
1. Deploy the updated Cloud Run revision.
2. Validate `get_s3_bucket_details`, `get_s3_bucket_security`, `/mcp/actions`, `list_actions`, and `/mcp` through Cloud Shell proxy.
3. Decide how ChatGPT will reach the private Cloud Run service.
4. Add Cost Explorer and Storage Lens tools after the S3 metadata/security path is stable.
