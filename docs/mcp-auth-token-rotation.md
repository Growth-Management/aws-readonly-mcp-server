# MCP_AUTH_TOKEN Rotation Runbook

## Purpose
Safely reissue the bearer token used by clients when calling the Cloud Run MCP server.

## Policy
- Generate a new high-entropy random token.
- Store the token only in the secret manager or deployment secret store used by Cloud Run.
- Do not commit the token to GitHub, documents, logs, shell history, or issue comments.
- Do not print the token in application logs.

## Rotation Steps
1. Generate a new token in a trusted terminal.

   ```bash
   openssl rand -base64 48
   ```

2. Update the Cloud Run runtime secret or environment value for `MCP_AUTH_TOKEN`.

3. Redeploy or restart the Cloud Run service so the new environment value is loaded.

4. Update the trusted MCP client configuration with the new bearer token.

5. Test the Cloud Run MCP endpoint.

   - Request with `Authorization: Bearer <new-token>` should succeed.
   - Request with the old token should return `401`.
   - Request without `Authorization` should return `401`.

6. Confirm Cloud Run logs contain only generic authentication failure messages and do not contain either token value.

## Rollback
If the client cannot connect after rotation, temporarily restore the previous `MCP_AUTH_TOKEN` in Cloud Run and redeploy. Then repeat the rotation with a newly generated token.

## Review Checklist
- `MCP_AUTH_TOKEN` is set in the Cloud Run runtime configuration.
- GitHub Secrets and Variables do not expose the token in workflow logs.
- Client-side token storage is restricted to authorized operators.
- The old token no longer works after successful rotation.
