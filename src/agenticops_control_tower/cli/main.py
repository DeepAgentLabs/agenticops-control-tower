"""Operator CLI (v0.2), talking to the v0.1 HTTP API.

The CLI connects to a running HTTP server, or inspects an offline fleet snapshot.
`serve --database` enables durable SQLite storage; bearer tokens are configured
through environment variables and supplied by `--token` or AGENTICOPS_TOKEN.

Requires the `api` extra for `httpx` (`pip install agenticops-control-tower[api]`).
The import itself stays cheap -- `httpx` is only imported inside the
functions that need it, so `from agenticops_control_tower.cli.main import
main` works even without the extra installed; only actually running a
command that talks to the API requires it.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx

DEFAULT_API_URL = "http://localhost:8000"


def _client(api_url: str, client: httpx.Client | None = None) -> httpx.Client:
    if client is not None:
        return client
    try:
        import httpx
    except ImportError as exc:
        raise SystemExit(
            "This command talks to the Control Tower HTTP API and needs `httpx`. "
            "Install it with: pip install agenticops-control-tower[api]"
        ) from exc
    return httpx.Client(base_url=api_url)


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_error:
        detail = response.text
        with contextlib.suppress(ValueError):
            detail = response.json().get("detail", detail)
        raise SystemExit(f"Control Tower API returned {response.status_code}: {detail}")


def _cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        raise SystemExit(
            "`serve` needs uvicorn. Install it with: pip install agenticops-control-tower[api]"
        ) from None
    from agenticops_control_tower.api.http import create_app

    uvicorn.run(
        create_app(database_path=args.database),
        host=args.host,
        port=args.port,
    )
    return 0


def _load_payload(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _cmd_agents_register(args: argparse.Namespace, client: httpx.Client) -> int:
    payload = _load_payload(args.payload_file)
    response = client.post("/agents/register", json=payload)
    _raise_for_status(response)
    _print_json(response.json())
    return 0


def _cmd_agents_heartbeat(args: argparse.Namespace, client: httpx.Client) -> int:
    payload = _load_payload(args.payload_file)
    response = client.post(f"/agents/{args.agent_id}/heartbeat", json=payload)
    _raise_for_status(response)
    _print_json(response.json())
    return 0


def _cmd_agents_list(args: argparse.Namespace, client: httpx.Client) -> int:
    response = client.get(
        "/agents",
        params={
            key: getattr(args, key)
            for key in ("status", "environment", "capability", "missing_capability")
            if getattr(args, key) is not None
        },
    )
    _raise_for_status(response)
    _print_json(response.json())
    return 0


def _cmd_agents_get(args: argparse.Namespace, client: httpx.Client) -> int:
    response = client.get(f"/agents/{args.agent_id}")
    _raise_for_status(response)
    _print_json(response.json())
    return 0


def _cmd_capabilities_list(_args: argparse.Namespace, client: httpx.Client) -> int:
    response = client.get("/capabilities")
    _raise_for_status(response)
    _print_json(response.json())
    return 0


def _cmd_status(args: argparse.Namespace, client: httpx.Client) -> int:
    response = client.get(
        "/status", params={"environment": args.environment} if args.environment else {}
    )
    _raise_for_status(response)
    _print_json(response.json())
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agenticops-control-tower")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("AGENTICOPS_API_URL", DEFAULT_API_URL),
        help=f"Control Tower API base URL (default: {DEFAULT_API_URL}, or $AGENTICOPS_API_URL)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("AGENTICOPS_TOKEN"),
        help="API bearer token (or $AGENTICOPS_TOKEN)",
    )
    parser.add_argument("--snapshot", help="Inspect a local fleet snapshot without an HTTP server")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the Control Tower HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--database", help="SQLite registry file (or $AGENTICOPS_DATABASE)")
    serve.set_defaults(handler=_cmd_serve, needs_client=False)

    agents = subparsers.add_parser("agents", help="Inspect and register agents")
    agents_sub = agents.add_subparsers(dest="agents_command", required=True)

    register = agents_sub.add_parser("register", help="Register an agent from a JSON payload")
    register.add_argument("payload_file", help="Path to a JSON file matching the AgentRecord shape")
    register.set_defaults(handler=_cmd_agents_register, needs_client=True)

    heartbeat = agents_sub.add_parser("heartbeat", help="Send a heartbeat for an agent")
    heartbeat.add_argument("agent_id")
    heartbeat.add_argument(
        "payload_file", help="Path to a JSON file matching the HeartbeatPayload shape"
    )
    heartbeat.set_defaults(handler=_cmd_agents_heartbeat, needs_client=True)

    agents_list = agents_sub.add_parser("list", help="List all registered agents")
    agents_list.add_argument("--status", choices=["healthy", "degraded", "unhealthy", "unknown"])
    agents_list.add_argument("--unhealthy", dest="status", action="store_const", const="unhealthy")
    agents_list.add_argument("--environment")
    agents_list.add_argument("--capability")
    agents_list.add_argument("--missing-capability")
    agents_list.set_defaults(handler=_cmd_agents_list, needs_client=True)

    agents_get = agents_sub.add_parser("get", help="Get one agent by ID")
    agents_get.add_argument("agent_id")
    agents_get.set_defaults(handler=_cmd_agents_get, needs_client=True)

    capabilities = subparsers.add_parser("capabilities", help="Inspect capability inventory")
    capabilities_sub = capabilities.add_subparsers(dest="capabilities_command", required=True)
    capabilities_list = capabilities_sub.add_parser(
        "list", help="List capability versions across all agents"
    )
    capabilities_list.set_defaults(handler=_cmd_capabilities_list, needs_client=True)

    status = subparsers.add_parser(
        "status", help="Fleet health, capability coverage and version rollups"
    )
    status.add_argument("--environment")
    status.set_defaults(handler=_cmd_status, needs_client=True)
    return parser


def main(argv: list[str] | None = None, *, client: httpx.Client | None = None) -> int:
    """CLI entry point. Returns a process exit code.

    `client` is an injection point for tests -- pass any `httpx.Client`
    (e.g. `fastapi.testclient.TestClient(create_app())`) to exercise commands
    against an in-process app without a running server. See tests/test_cli.py.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.snapshot:
        from agenticops_control_tower.models import AgentStatus
        from agenticops_control_tower.snapshot import load_snapshot

        if args.command == "serve" or (
            args.command == "agents" and args.agents_command in ("register", "heartbeat")
        ):
            parser.error("--snapshot supports read commands only")
        api = load_snapshot(args.snapshot)
        if args.command == "status":
            _print_json(api.get_status(environment=args.environment).model_dump(mode="json"))
        elif args.command == "capabilities":
            _print_json(api.list_all_capabilities())
        elif args.agents_command == "get":
            _print_json(api.get_agent(args.agent_id).model_dump(mode="json"))
        else:
            records = api.list_agents(
                status=AgentStatus(args.status) if args.status else None,
                environment=args.environment,
                capability=args.capability,
                missing_capability=args.missing_capability,
            )
            _print_json([record.model_dump(mode="json") for record in records])
        return 0

    if not args.needs_client:
        return int(args.handler(args))

    if client is not None:
        if args.token:
            client.headers["Authorization"] = f"Bearer {args.token}"
        # Caller-supplied client (tests): don't close something we don't own.
        return int(args.handler(args, client))

    with _client(args.api_url) as owned_client:
        if args.token:
            owned_client.headers["Authorization"] = f"Bearer {args.token}"
        return int(args.handler(args, owned_client))


def run() -> None:
    """Console-script entry point (`agenticops-control-tower`)."""
    sys.exit(main())


if __name__ == "__main__":
    run()
