"""Operator CLI for the v0.2 control-plane surface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.models import (
    AgentRecord,
    AgentStatus,
    AgentStatusSummary,
    CapabilityInventoryRecord,
    FleetStatusSummary,
)
from agenticops_control_tower.snapshot import create_api, load_snapshot


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""

    parser = argparse.ArgumentParser(
        prog="deepagent",
        description="Inspect agent inventory and status through the Control Tower surface.",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="Path to a fleet snapshot JSON file. If omitted, the CLI starts with an empty registry.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    agents_parser = subparsers.add_parser("agents", help="Inspect known agents.")
    agents_subparsers = agents_parser.add_subparsers(dest="agents_command", required=True)

    agents_list_parser = agents_subparsers.add_parser("list", help="List known agents.")
    agents_list_parser.add_argument(
        "--status",
        choices=[status.value for status in AgentStatus],
        help="Filter to one health status.",
    )
    agents_list_parser.add_argument("--environment", help="Filter to one environment.")
    agents_list_parser.add_argument(
        "--capability",
        help="Show only agents that report a capability.",
    )
    agents_list_parser.add_argument(
        "--missing-capability",
        help="Show only agents that do not report a capability.",
    )
    agents_list_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Render output as a table or JSON.",
    )

    agents_get_parser = agents_subparsers.add_parser("get", help="Show one agent.")
    agents_get_parser.add_argument("agent_id", help="Agent id to inspect.")
    agents_get_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Render output as a table or JSON.",
    )

    capabilities_parser = subparsers.add_parser(
        "capabilities",
        help="Inspect capability inventory.",
    )
    capabilities_subparsers = capabilities_parser.add_subparsers(
        dest="capabilities_command",
        required=True,
    )
    capabilities_list_parser = capabilities_subparsers.add_parser(
        "list",
        help="List known capabilities across agents.",
    )
    capabilities_list_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Render output as a table or JSON.",
    )

    status_parser = subparsers.add_parser("status", help="Show fleet or agent status.")
    status_parser.add_argument(
        "agent_id",
        nargs="?",
        help="Optional agent id for a single-agent status view.",
    )
    status_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Render output as a table or JSON.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the operator CLI and return an exit code."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        api = load_snapshot(args.snapshot) if args.snapshot is not None else create_api()
        rendered = _dispatch(api, args)
    except AgentNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(rendered)
    return 0


def _dispatch(api: ControlTowerAPI, args: argparse.Namespace) -> str:
    if args.command == "agents" and args.agents_command == "list":
        filtered_agents = api.list_agents(
            status=AgentStatus(args.status) if args.status is not None else None,
            environment=args.environment,
            capability=args.capability,
            missing_capability=args.missing_capability,
        )
        return _render_output(filtered_agents, args.format, _render_agents_table)

    if args.command == "agents" and args.agents_command == "get":
        agent = api.get_agent(args.agent_id)
        return _render_output(agent, args.format, _render_agent_detail)

    if args.command == "capabilities" and args.capabilities_command == "list":
        capabilities = api.list_capabilities()
        return _render_output(capabilities, args.format, _render_capabilities_table)

    if args.command == "status":
        status_summary = api.get_status(args.agent_id)
        if isinstance(status_summary, AgentStatusSummary):
            return _render_output(status_summary, args.format, _render_agent_status)
        return _render_output(status_summary, args.format, _render_fleet_status)

    raise ValueError(f"Unhandled CLI arguments: {args!r}")


def _render_output(
    data: object,
    output_format: str,
    table_renderer: Callable[[Any], str],
) -> str:
    if output_format == "json":
        return _render_json(data)
    return table_renderer(data)


def _render_json(data: object) -> str:
    if isinstance(data, BaseModel):
        payload: object = data.model_dump(mode="json")
    elif isinstance(data, list):
        payload = [
            item.model_dump(mode="json")
            if isinstance(item, BaseModel)
            else item
            for item in data
        ]
    else:
        payload = data
    return json.dumps(payload, indent=2, sort_keys=True)


def _render_agents_table(agents: list[AgentRecord]) -> str:
    rows = [
        [
            agent.agent_id,
            agent.environment,
            agent.runtime,
            agent.framework,
            agent.status.value,
            str(len(agent.capabilities)),
            agent.last_seen.isoformat() if agent.last_seen is not None else "-",
        ]
        for agent in agents
    ]
    return _render_table(
        headers=["AGENT ID", "ENV", "RUNTIME", "FRAMEWORK", "STATUS", "CAPS", "LAST SEEN"],
        rows=rows,
        empty_message="No agents found.",
    )


def _render_agent_detail(agent: AgentRecord) -> str:
    lines = [
        f"Agent ID: {agent.agent_id}",
        f"Name: {agent.name}",
        f"Environment: {agent.environment}",
        f"Runtime: {agent.runtime}",
        f"Framework: {agent.framework}",
        f"Status: {agent.status.value}",
        f"Registered At: {agent.registered_at.isoformat()}",
        f"Last Seen: {agent.last_seen.isoformat() if agent.last_seen is not None else '-'}",
        f"Heartbeat Count: {agent.heartbeat_count}",
        "Capabilities:",
    ]
    if agent.capabilities:
        lines.extend(f"  - {name}: {version}" for name, version in agent.capabilities.items())
    else:
        lines.append("  - none")
    return "\n".join(lines)


def _render_capabilities_table(capabilities: list[CapabilityInventoryRecord]) -> str:
    rows = [
        [
            capability.capability,
            ", ".join(capability.versions),
            str(len(capability.agent_ids)),
            ", ".join(capability.agent_ids),
        ]
        for capability in capabilities
    ]
    return _render_table(
        headers=["CAPABILITY", "VERSIONS", "AGENTS", "AGENT IDS"],
        rows=rows,
        empty_message="No capabilities found.",
    )


def _render_fleet_status(summary: FleetStatusSummary) -> str:
    lines = [
        f"Total Agents: {summary.total_agents}",
        f"Healthy: {summary.healthy_agents}",
        f"Degraded: {summary.degraded_agents}",
        f"Unhealthy: {summary.unhealthy_agents}",
        f"Unknown: {summary.unknown_agents}",
        f"Capabilities Tracked: {summary.capability_count}",
        "",
        "Capability Coverage:",
        _render_table(
            headers=["CAPABILITY", "INSTALLED", "MISSING", "VERSIONS"],
            rows=[
                [
                    coverage.capability,
                    str(coverage.installed_agents),
                    str(coverage.missing_agents),
                    ", ".join(coverage.versions),
                ]
                for coverage in summary.capabilities
            ],
            empty_message="No capabilities found.",
        ),
    ]
    return "\n".join(lines)


def _render_agent_status(summary: AgentStatusSummary) -> str:
    lines = [
        f"Agent ID: {summary.agent_id}",
        f"Name: {summary.name}",
        f"Environment: {summary.environment}",
        f"Runtime: {summary.runtime}",
        f"Framework: {summary.framework}",
        f"Status: {summary.status.value}",
        f"Last Seen: {summary.last_seen or '-'}",
        f"Heartbeat Count: {summary.heartbeat_count}",
        f"Capability Count: {summary.capability_count}",
        "Capabilities:",
    ]
    if summary.capabilities:
        lines.extend(f"  - {name}: {version}" for name, version in summary.capabilities.items())
    else:
        lines.append("  - none")
    return "\n".join(lines)


def _render_table(headers: list[str], rows: list[list[str]], empty_message: str) -> str:
    if not rows:
        return empty_message

    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    rendered_rows = [
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    ]
    header_row = "  ".join(
        header.ljust(widths[index]) for index, header in enumerate(headers)
    )
    separator_row = "  ".join("-" * width for width in widths)
    return "\n".join([header_row, separator_row, *rendered_rows])


if __name__ == "__main__":
    raise SystemExit(main())
