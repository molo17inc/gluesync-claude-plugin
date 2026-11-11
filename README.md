# Gluesync plugin for Claude

Work with your [Gluesync](https://molo17.com/gluesync/) Core Hub from Claude: build real-time
replication pipelines, start snapshots and CDC, check what is running, and diagnose what is not,
through the Core Hub REST API, its built-in MCP server, or step-by-step guidance in the Control
Plane web UI. Everything the skill teaches is grounded in the official
[Gluesync documentation](https://docs.molo17.com/gluesync/latest/).

## What's inside

| Component | What it does |
|---|---|
| `gluesync-core-hub` skill | Picks the right route (UI, MCP, REST), enforces safe defaults (read first, confirm every change, never reset checkpoints without support), and walks Claude through building, running and troubleshooting pipelines |
| `scripts/mcp.py` | Calls your Core Hub's MCP tools from the command line, including a one-command source-to-target `setup` |
| `scripts/gs_api.py` | Small REST client that reports exactly what Core Hub answered |
| `references/` | UI guide, MCP tool map, REST reference and troubleshooting table, each linked to its documentation page |

The scripts use only the Python 3.8+ standard library.

## Requirements

- A running Gluesync Core Hub (2.3 recommended) that Claude's environment can reach over HTTPS.
- A Personal API Token from the Control Plane: **Settings → Account → Personal API Tokens → New
  token**. Use `gluesync.mcp_read` / `gluesync.api_read` for read-only work, `gluesync.mcp` /
  `gluesync.api` to make changes.

## Setup

Install the plugin, then in your own terminal:

```bash
export GLUESYNC_BASE=https://your-core-hub.example.com
export GLUESYNC_PAT=gsp_...            # your token; never paste it into the chat
# private or self-signed certificate:
export GLUESYNC_CA_FILE=/path/to/ca.pem
```

Optionally connect the Core Hub MCP server to Claude Code directly:

```bash
claude mcp add --transport http gluesync "$GLUESYNC_BASE/mcp/http" --header "Authorization: Bearer $GLUESYNC_PAT"
```

Then ask things like "list my Gluesync pipelines and tell me which entities are in error",
"replicate the orders table from PostgreSQL to Snowflake", or "walk me through starting a snapshot
in the Control Plane".

## Where it works

The skill runs anywhere Claude can use skills. The scripts and the MCP connection need network
access to your Core Hub, so they work in Claude Code and the Claude desktop app on a machine that
can reach it. On claude.ai in the browser, the skill can explain the API and guide you through the
UI but cannot call a Core Hub on a private network.

## Privacy Policy

This plugin does not collect, store or send any data to MOLO17 or to any third party. The scripts
talk only to the Core Hub address you configure, using the token you provide through environment
variables; they keep no files, logs or caches, and the token is held in memory only while a script
runs. Data returned by your Core Hub (pipeline configuration, status, error messages, which can
include row values) is shown to Claude in your conversation and is handled under your agreement with
Anthropic. Gluesync itself is covered by the
[MOLO17 privacy policy](https://molo17.com/privacy-policy/). Questions: see Support below.

## Support

- Documentation: <https://docs.molo17.com/gluesync/latest/>
- Support portal: <https://support.molo17.com>
- Security issues: <https://docs.molo17.com/gluesync/latest/contribute/notify-security-issues.html>

## License

Apache License 2.0. See [LICENSE](LICENSE).
