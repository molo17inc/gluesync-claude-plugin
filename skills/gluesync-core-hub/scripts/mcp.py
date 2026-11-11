#!/usr/bin/env python3
"""Drives the MCP server built into a Gluesync Core Hub, from the command line.

Useful when the Core Hub MCP server is not connected to Claude as a connector: the same tools, called
over JSON-RPC. Two details make this a script rather than curl: the endpoint only accepts a Personal
API Token (the login session token is rejected), and a streamable-HTTP answer can come back as an SSE
frame even for a single call, so the reply has to be unwrapped.

Configure through the environment: GLUESYNC_BASE and GLUESYNC_PAT (see gs_common.py). Database
passwords for `setup` come from GLUESYNC_SOURCE_PASSWORD and GLUESYNC_TARGET_PASSWORD.

    python3 mcp.py tools                                  # names + one-line descriptions
    python3 mcp.py schema <tool>                          # one tool's input schema
    python3 mcp.py call list_pipelines '{}'
    python3 mcp.py setup --help                           # a whole source-to-target pipeline

`setup` runs pipeline -> agents -> assign -> connections -> attach -> leave Draft -> specific config ->
draft entity -> validate -> upsert (-> start), printing each step so a failure names the call that rejected what. It creates
objects on the Core Hub: confirm the plan with the user before running it.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gs_common import request  # noqa: E402

MCP_PATH = os.environ.get("GLUESYNC_MCP_PATH", "/mcp/http")


class Mcp:
    """One MCP session: initialize, then as many tool calls as you like."""

    def __init__(self):
        self.token = os.environ.get("GLUESYNC_PAT")
        if not self.token:
            raise SystemExit(
                "!! GLUESYNC_PAT is not set. The Core Hub MCP endpoint needs a Personal API Token "
                "(gsp_...); create one in the Core Hub UI and export it."
            )
        self.session = None
        self.counter = 0
        self.rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "gluesync-core-hub-skill", "version": "1"},
        })
        self.rpc("notifications/initialized", {}, notify=True)

    def rpc(self, method, params=None, notify=False):
        self.counter += 1
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            body["id"] = self.counter
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json, text/event-stream",
        }
        if self.session:
            headers["mcp-session-id"] = self.session
        _, response_headers, text = request("POST", MCP_PATH, body, headers)
        if response_headers.get("mcp-session-id"):
            self.session = response_headers["mcp-session-id"]
        if notify or not text.strip():
            return None
        for line in text.splitlines():  # streamable HTTP may answer as SSE
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return json.loads(text)

    def tools(self):
        return self.rpc("tools/list", {})["result"]["tools"]

    def call(self, tool, arguments):
        result = self.rpc("tools/call", {"name": tool, "arguments": arguments})
        if "error" in result:
            raise SystemExit(f"!! {tool} -> {result['error']}")
        content = result["result"]["content"][0]["text"]
        if result["result"].get("isError"):
            raise SystemExit(f"!! {tool} -> {content}")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content


def credentials(args, side):
    value = lambda name: getattr(args, f"{side}_{name}")
    password = os.environ.get(f"GLUESYNC_{side.upper()}_PASSWORD")
    if password is None:
        raise SystemExit(f"!! Set GLUESYNC_{side.upper()}_PASSWORD for the {side} database.")
    return {
        "host": value("host"),
        "port": value("port"),
        "databaseName": value("db"),
        "username": value("user"),
        "password": password,
        "enableTls": args.tls,
        "trustServerCertificate": args.trust_server_certificate,
    }


def setup(args):
    mcp = Mcp()
    # Tool names differ between Core Hub releases, so check what this one exposes.
    names = {t["name"] for t in mcp.tools()}
    pipeline_id = mcp.call("create_pipeline", {"name": args.name, "description": args.description})["pipelineId"]
    print(f"pipeline '{args.name}' created: {pipeline_id}")

    agents = {}
    for side, agent_type in (("source", "SOURCE"), ("target", "TARGET")):
        tag = getattr(args, f"{side}_agent")
        agent_id = mcp.call("add_agent", {
            "pipeline_id": pipeline_id, "agent_type": agent_type,
            "agent_internal_name": tag, "agent_user_tag": f"{tag}-{side}",
        })["agentId"]
        # Adding only mints the id; assigning is what binds the agent to the pipeline.
        mcp.call("assign_agent", {"pipeline_id": pipeline_id, "agent_id": agent_id, "agent_type": agent_type})
        connection_id = mcp.call("create_connection", {
            "name": f"{args.name}-{side}", "agent_tag": tag,
            "host_credentials": credentials(args, side),
        })["connectionId"]
        # Attaching pushes the credentials and opens the database, so it must precede discovery.
        mcp.call("attach_connection", {
            "pipeline_id": pipeline_id, "agent_id": agent_id, "connection_id": connection_id,
        })
        agents[side] = agent_id
        print(f"{side} agent {tag} added, assigned and connected: {agent_id}")

    # A new pipeline is a Draft until both sides have saved connections; this moves it out of Draft.
    # Older Core Hubs do not have the tool and leave Draft on their own.
    if "complete_pipeline_configuration" in names:
        mcp.call("complete_pipeline_configuration", {"pipeline_id": pipeline_id})
        print("pipeline configuration completed (out of Draft)")

    if args.source_specific:
        mcp.call("set_agent_specific_config", {
            "pipeline_id": pipeline_id, "agent_id": agents["source"],
            "configuration": json.loads(args.source_specific),
        })
        print(f"source specific configuration set: {args.source_specific}")

    draft = mcp.call("draft_entity", {
        "pipeline_id": pipeline_id,
        "source_agent_id": agents["source"], "target_agent_id": agents["target"],
        "source_schema": args.source_schema, "source_table": args.source_table,
        "target_schema": args.target_schema, "target_table": args.target_table,
        "key_columns": args.key or [],
        "entity_name": args.entity_name or args.source_table,
    })
    for warning in draft.get("warnings", []):
        print(f"  ! {warning}")

    report = mcp.call("validate_entities", {"pipeline_id": pipeline_id, "entities": [draft["entity"]]})
    for issue in report.get("issues", []):
        print(f"  {issue['severity']}: {issue['message']}")
    if not report["valid"]:
        raise SystemExit("!! the drafted entity does not validate; nothing was written")

    mcp.call("upsert_entities", {"pipeline_id": pipeline_id, "entities": [draft["entity"]]})
    print(f"entity '{draft['entity']['entityName']}' configured")

    if args.start:
        # Newer Core Hubs have one sync_command tool; earlier 2.3 releases have start_sync.
        if "sync_command" in names:
            mcp.call("sync_command", {"pipeline_id": pipeline_id, "command": "start", "with_snapshot": True})
        else:
            mcp.call("start_sync", {"pipeline_id": pipeline_id, "with_snapshot": True})
        print("sync started with a snapshot")
    print(f"\npipeline {pipeline_id} ready.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tools", help="list the tools this Core Hub exposes")
    schema_parser = commands.add_parser("schema", help="print one tool's input schema")
    schema_parser.add_argument("tool")
    call_parser = commands.add_parser("call", help="call one tool")
    call_parser.add_argument("tool")
    call_parser.add_argument("arguments", nargs="?", default="{}", help="JSON object of arguments")

    s = commands.add_parser("setup", help="configure a whole source-to-target pipeline")
    s.add_argument("--name", required=True, help="pipeline name")
    s.add_argument("--description", default="", help="pipeline description")
    s.add_argument("--entity-name", help="entity name (defaults to the source table)")
    for side in ("source", "target"):
        s.add_argument(f"--{side}-agent", required=True, help=f"{side} agent tag, e.g. postgresql-cdc")
        s.add_argument(f"--{side}-host", required=True)
        s.add_argument(f"--{side}-port", type=int, required=True)
        s.add_argument(f"--{side}-db", required=True)
        s.add_argument(f"--{side}-user", required=True)
        s.add_argument(f"--{side}-schema", required=True, help="schema, or scope on a NoSQL side")
        s.add_argument(f"--{side}-table", required=True, help="table, or collection on a NoSQL side")
    s.add_argument("--source-specific", help='agent-specific JSON, e.g. \'{"changeReadMode": "DCP"}\'')
    s.add_argument("--key", action="append", help="source column to key on (repeatable)")
    s.add_argument("--tls", action="store_true", help="connect to both databases over TLS")
    s.add_argument("--trust-server-certificate", action="store_true",
                   help="accept the databases' certificates without validation (test only)")
    s.add_argument("--start", action="store_true", help="start the sync with a snapshot when done")

    args = parser.parse_args()
    if args.command == "tools":
        for tool in Mcp().tools():
            print(f"{tool['name']:<36} {(tool.get('description') or '').splitlines()[0][:90] if tool.get('description') else ''}")
    elif args.command == "schema":
        match = [t for t in Mcp().tools() if t["name"] == args.tool]
        if not match:
            raise SystemExit(f"!! no tool named {args.tool}")
        print(json.dumps(match[0].get("inputSchema"), indent=1))
    elif args.command == "call":
        print(json.dumps(Mcp().call(args.tool, json.loads(args.arguments)), indent=1))
    else:
        setup(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
