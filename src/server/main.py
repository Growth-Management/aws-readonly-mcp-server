from __future__ import annotations

from typing import Any

from .config import load_settings


class MCPServer:
    def __init__(self) -> None:
        self.settings = load_settings()

    def healthcheck(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "app_env": self.settings.app_env,
            "aws_region": self.settings.aws_region,
        }

    def list_s3_buckets(self) -> dict[str, Any]:
        """Placeholder tool implementation.

        Replace this with a real AWS client call through a dedicated
        service layer and AWS wrapper.
        """
        return {
            "status": "not_implemented",
            "message": "list_s3_buckets is not implemented yet",
        }


def create_server() -> MCPServer:
    return MCPServer()


if __name__ == "__main__":
    server = create_server()
    print(server.healthcheck())
