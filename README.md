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
| `references/` | UI guide, MCP tool map, REST reference and troubleshooting table, each linked to its documentation page |

The plugin is instructions only: it runs no code of its own. Claude acts on your Core Hub through
the MCP server built into Core Hub, which you connect yourself.

## Requirements

- A running Gluesync Core Hub (2.3 recommended) that Claude's environment can reach over HTTPS.
- A Personal API Token from the Control Plane: **Settings → Account → Personal API Tokens → New
  token**. Use `gluesync.mcp_read` / `gluesync.api_read` for read-only work, `gluesync.mcp` /
  `gluesync.api` to make changes.

## Install

In Claude Code:

```bash
/plugin install gluesync --marketplace molo17inc/gluesync-claude-plugin
```

On older Claude Code versions, add the marketplace first:
`/plugin marketplace add molo17inc/gluesync-claude-plugin`, then `/plugin install gluesync@gluesync`.

## Setup

To let Claude act on your Core Hub, connect its MCP server once, in your own terminal (never paste
the token into the chat):

```bash
claude mcp add --transport http gluesync https://your-core-hub.example.com/mcp/http \
  --header "Authorization: Bearer gsp_your_token"
```

In the Control Plane, **Settings → AI agents → Copy HTTP URL** gives you the exact address. If the
connection is refused with `Invalid Host`, see the
[Core Hub MCP docs](https://docs.molo17.com/gluesync/latest/gs-modules/corehub-mcp.html).
Without MCP the skill still guides you through the Control Plane and the REST API.

Then ask things like "list my Gluesync pipelines and tell me which entities are in error",
"replicate the orders table from PostgreSQL to Snowflake", or "walk me through starting a snapshot
in the Control Plane".

## Where it works

The skill runs anywhere Claude can use skills. Acting on a Core Hub needs the MCP connection, which
needs network access to your Core Hub: it works in Claude Code and the Claude desktop app on a
machine that can reach it. Where it cannot, the skill still explains the API and guides you through
the UI.

## Privacy Policy

This plugin contains instructions only and runs no code. It does not collect, store or send any
data to MOLO17 or to any third party. Claude reaches only the Core Hub you connect, with the token
you configure in your own MCP client. Data returned by your Core Hub (pipeline configuration, status, error messages, which can
include row values) is shown to Claude in your conversation and is handled under your agreement with
Anthropic. Gluesync itself is covered by the
[MOLO17 privacy policy](https://www.iubenda.com/privacy-policy/51934644). Questions: see Support below.

## Support

- Documentation: <https://docs.molo17.com/gluesync/latest/>
- Support portal: <https://support.molo17.com>
- Security issues: <https://docs.molo17.com/gluesync/latest/contribute/notify-security-issues.html>

## License

Apache License 2.0. See [LICENSE](LICENSE).
