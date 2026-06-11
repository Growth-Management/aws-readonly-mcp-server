# Service Layer

This directory contains business-level services for the AWS Read Only MCP Server.

## Responsibilities
- aggregate AWS data into stable outputs
- keep MCP handlers thin
- separate domain logic from raw AWS SDK calls

## Current placeholders
- `s3_inventory.py`
- `s3_security.py`
- `s3_costs.py`
- `s3_metrics.py`

## Recommended next additions
- shared response schema helpers
- structured error mapping
- dependency service for cross-system impact analysis
- tests for each service module
