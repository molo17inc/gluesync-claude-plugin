---
name: gluesync-core-hub
description: >-
  Work with a Gluesync Core Hub (MOLO17's real-time data replication and CDC platform): create and
  run pipelines, add source and target agents, map entities, start snapshots and CDC, check status
  and metrics, and diagnose stalled or failing replication, through the Core Hub REST API, its
  built-in MCP server, or step-by-step guidance in the Control Plane web UI. Use whenever the user
  mentions Gluesync, Core Hub, Control Plane, a Gluesync pipeline, entity or agent, a gsp_ token,
  or asks to replicate or sync data between databases with Gluesync.
---

# Gluesync Core Hub

Gluesync replicates data between databases in real time: a **pipeline** connects a **source agent**
(reads, usually by change data capture) to one or more **target agents** (writes), and each table
or collection it carries is an **entity**. Core Hub is the server that runs it all; the **Control
Plane** is its web UI. Everything here is grounded in the official documentation at
<https://docs.molo17.com/gluesync/latest/>. When this skill and the user's Core Hub disagree, the
Core Hub wins: releases differ, so check its live Swagger (`<core-hub>/swagger`) or the MCP tool
list rather than insisting.

## Pick the route

| The user wants to… | Use |
|---|---|
| Be guided through a task, or has no API access | The Control Plane UI: [references/ui.md](references/ui.md) |
| Let Claude act on their Core Hub | Connect the Core Hub MCP server, then use its tools: [references/mcp.md](references/mcp.md) |
| Script or automate outside Claude | REST with `curl`: [references/rest-api.md](references/rest-api.md) |
| Fix something that is stuck or failing | [references/troubleshooting.md](references/troubleshooting.md) |

Prefer MCP over raw REST when both are available: its tools encode the order of operations and
the payload shapes, and `validate_entities` checks an entity before anything is written.

## Before calling anything

1. **Ask for the Core Hub address.** It is the HTTPS address from installation: `https://<host>`
   behind the bundled reverse proxy (port 443), or `https://<host>:1717` without it. TLS is on by
   default, often with a self-signed certificate on trial kits.
   ([TLS](https://docs.molo17.com/gluesync/latest/security/setup-https-and-wss-encryption.html),
   [REST](https://docs.molo17.com/gluesync/latest/core-hub/core-hub-apis.html))
2. **Get a Personal API Token, with the narrowest scope that does the job.** The user creates it in
   the Control Plane: user menu → **Settings** → **Account** → **Personal API Tokens** →
   **New token**; it starts with `gsp_` and is shown once. Scopes: `gluesync.mcp_read` or
   `gluesync.api_read` to look, `gluesync.mcp` or `gluesync.api` to change things. MCP scopes do not
   open REST, and API scopes do not open MCP.
   ([Personal API Tokens](https://docs.molo17.com/gluesync/latest/security/personal-api-tokens.html))
3. **Never ask the user to paste a token or password into the chat.** The user puts the token into
   their MCP client configuration themselves, as [references/mcp.md](references/mcp.md) shows. Never
   echo, log or write secrets to a file.
4. Once connected, check access with a read-only call such as `list_pipelines` or
   `get_corehub_version`, and list the tools: names differ between Core Hub releases.

## Rules that keep replication data safe

- **Read first, then change.** Show the user what you will create, start, stop or delete, and get
  a yes before any write: pipelines, agents, connections, entities, sync commands, maintenance.
- **Never without the user's explicit, informed yes:** deleting pipelines, entities or connections;
  **Empty the table first** / **Delete only some rows first**; `redo` / restart from zero.
- **Reset pipeline checkpoint and Restart platform are support-supervised operations.** Do not run
  them; tell the user to involve Gluesync support
  ([stalled pipelines](https://docs.molo17.com/gluesync/latest/learn/how-to-diagnose-a-stalled-pipeline-or-entity.html)).
- **A 202 means dispatched, not done.** After a command, read the state back
  (`get_pipeline_status` / `GET /pipelines/{id}/entities-status`, metrics) before saying it worked.
  Retries are not idempotent; check before re-sending.
  ([REST](https://docs.molo17.com/gluesync/latest/core-hub/core-hub-apis.html))
- **Commands take entity IDs, not names.** A name is accepted with 202 and does nothing. (The MCP
  `sync_command` tool, where present, accepts `entity_names`.)
  ([automate how-to](https://docs.molo17.com/gluesync/latest/learn/how-to-automate-gluesync-with-the-rest-api-mcp-and-webhooks.html))
- **Green is not proof.** An entity can sit Active with "Idle, no changes yet" while its database
  is down. Prove delivery with a probe row on the source, then look for it on the target.
- **Error text can contain row values.** Treat notifications, logs and copied errors as personal
  data: quote only what is needed.

## Build a pipeline end to end

Through MCP, the order is fixed; each step depends on the previous one:

1. `create_pipeline` → 2. `add_agent` (source, then target; `agent_internal_name` is the agent tag,
see `list_agent_types`) → 3. `assign_agent` (without it, later steps fail) → 4. `create_connection`
→ 5. `attach_connection` (pushes credentials; must precede discovery) → 6. leave Draft with
`complete_pipeline_configuration` where the tool exists → 7. `set_agent_specific_config` if needed
→ 8. `draft_entity` (runs discovery and maps columns) → 9. `validate_entities` → 10.
`upsert_entities` → 11. start: `sync_command {"command": "start", "with_snapshot": true}` on newer
releases, `start_sync` on earlier ones.

Show the user the whole plan (pipeline name, agents, tables, keys) before the first write, and read
a tool's input schema before calling a tool whose arguments you have not seen on this Core Hub.
Database passwords go into `create_connection`: ask the user to enter them in the Control Plane
(**Edit source** / **Edit target**) if they prefer not to pass them through the conversation.

Then follow a change through: insert, update **and** delete a probe row on the source and confirm
each on the target. Deletes and updates are where mapping problems show up.

In the UI the same job is the **Pipeline** wizard (Setup source → Setup target(s) → Ready), then
**Entities** → Objects Browser → Fields Editor → **Start sync**. See [references/ui.md](references/ui.md).

## Answering "is it working?"

1. `get_pipeline_status` (MCP) or `GET /pipelines/{id}/entities-status` (REST): look at
   `errorState`, `isSyncActive`, `isMigrationActive`.
2. `get_system_conditions` where available: problems affecting the whole Core Hub (`[]` = healthy).
3. Notifications: `get_notifications`, or the bell icon → **Notifications hub**.
4. Snapshot progress: `get_pipeline_snapshot_status`; for counts use **Count both** or a SQL count,
   because the percentage is approximate.
5. Then the probe row. Diagnose with [references/troubleshooting.md](references/troubleshooting.md).

## Where to send the user

- Documentation: <https://docs.molo17.com/gluesync/latest/>
- Support tickets: <https://support.molo17.com>
  ([how to open one](https://docs.molo17.com/gluesync/latest/learn/how-to-create-a-support-ticket.html))
- Service status: <https://status.molo17.com/>
