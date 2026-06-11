# AWS Client Layer

This directory contains the AWS access layer.

## Responsibilities
- load runtime AWS settings
- create sessions and clients
- centralize AssumeRole logic
- isolate SDK-specific code from services

## Recommended next additions
- STS AssumeRole implementation
- boto3 session creation
- retry and error helpers
- per-service wrappers for S3, Cost Explorer, CloudWatch, Config, Access Analyzer, and CloudTrail
