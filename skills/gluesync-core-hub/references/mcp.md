# Core Hub MCP server

Source: [Core Hub MCP](https://docs.molo17.com/gluesync/latest/gs-modules/corehub-mcp.html) and
[Automate Gluesync with the REST API, MCP and webhooks](https://docs.molo17.com/gluesync/latest/learn/how-to-automate-gluesync-with-the-rest-api-mcp-and-webhooks.html).

## What it is

An MCP server embedded in Core Hub, enabled by default, served on the same origin and port as the
REST API. It has no privileges of its own: every tool call is forwarded to Core Hub's REST API with
the caller's token, so roles, license and audit apply exactly as in the Control Plane.

- Streamable HTTP: `<core-hub>/mcp/http` (preferred). SSE: `<core-hub>/mcp`.
- The Control Plane shows the address under **Settings → AI agents** → **Connect** →
  **Copy HTTP URL**.
- Authentication: `Authorization: Bearer <token>` with a Personal API Token carrying
  `gluesync.mcp` (all tools) or `gluesync.mcp_read` (read-only: write tools are still listed but
  answer an error naming the scope). A Core Hub session token also works.
- An MCP session belongs to the token that opened it.

## Connect it to Claude

The user does this once, in their own terminal or client settings, so the token never passes
through the conversation. Claude Code:

```bash
claude mcp add --transport http gluesync https://<core-hub>/mcp/http \
  --header "Authorization: Bearer <personal-api-token>"
```

Other clients: add a remote MCP server with the same URL and header. Give an assistant the
read-only scope (`gluesync.mcp_read`) unless it has to change something.

If the client gets **HTTP 403 `Invalid Host: …`**: Core Hub's DNS-rebinding protection only allows
`localhost` by default. The Core Hub administrator sets `GLUESYNC_MCP_ALLOWED_HOSTS=<host>` (and
`GLUESYNC_MCP_ALLOWED_ORIGINS` for browser clients) and recreates Core Hub, or makes the reverse
proxy send `Host: localhost` for `/mcp` paths. The protection cannot be switched off.

A certificate without the host in its subjectAltName makes Node-based clients fail with
`ERR_TLS_CERT_ALTNAME_INVALID`
([TLS](https://docs.molo17.com/gluesync/latest/security/setup-https-and-wss-encryption.html)).

## Tools

The catalog changes between releases: always check the tool list the client shows for the user's
Core Hub and read a tool's schema before calling it. The documented groups:

| Group | Tools (as documented) |
|---|---|
| Pipelines | `create_pipeline`, `update_pipeline`, `list_pipelines`, `get_pipeline`, `get_pipeline_status`, `get_pipeline_snapshot_status`, `get_pipeline_entities_status`, `verify_pipeline_connections`, `delete_pipeline`, `reset_pipeline_checkpoint`, `get_pipeline_draft_status`, `complete_pipeline_configuration` |
| Agents | `add_agent`, `assign_agent`, `attach_connection`, `set_agent_specific_config`, `list_pipeline_agents`, `list_agent_types`, `get_agent`, `get_agent_raw`, `get_agent_node_info`, `discover_schemas`, `discover_tables`, `discover_columns`, `verify_agent_connection`, `unassign_agent` |
| Entities | `get_pipeline_entities`, `get_entity`, `describe_entity_schema`, `list_field_functions`, `draft_entity`, `create_entity`, `validate_entities`, `upsert_entities`, `delete_entities` |
| Sync | `start_sync`, `stop_sync`, `redo_sync`, `one_time_snapshot`, `start_group_sync`, `stop_group_sync`, `enter_maintenance_mode`, `exit_maintenance_mode`. Newer releases merge the first four into `sync_command` (`command`: `start`, `stop`, `redo`, `one_time_snapshot`) |
| Connections | `create_connection`, `list_connections`, `get_connection`, `get_connection_usages`, `delete_connection` (refused while an agent uses it) |
| Notifications and metrics | `get_notifications`, `get_notification`, `get_notification_count`, `mark_notifications_read`, `get_pipeline_metrics`, `get_agent_metrics`, `get_entity_metrics`, `get_global_metrics`, `get_prometheus_metrics`, `get_agent_prometheus_metrics`, `get_system_conditions` |
| Alerts | webhook tools (`get_webhook_configurations`, `send_test_webhook`, …) and email tools (`get_email_notification_configuration`, `send_test_email_notification`, …) |
| Query Studio | `list_sql_capable_agents`, `execute_sql`, `explain_sql`, `get_table_ddl`, `classify_table`, `classify_schema`, `list_saved_queries`, `get_saved_query`; plus per-agent `db_<pipelineId>_<agentId>_<tool>` tools |
| Validator | `trigger_data_comparison`, `list_data_comparison_runs`, `get_data_comparison_run`, `list_data_comparison_differences`, `reconcile_data_comparison_differences`, `cancel_data_comparison_run` |
| Scheduler (Chronos) | schedules, trigger flows and settings: `list_schedules`, `create_schedule`, `run_schedule`, `fire_trigger_flow`, … |
| Other | `list_mapping_functions`, `compile_mapping_function`, `list_groups`, `get_global_config`, `set_log_level`, `get_license_info`, `get_corehub_version`, `export_pipeline_yaml`, `search_documentation`, `search_support_knowledge`, visualization and AI-agent tools |

`execute_sql` masks classified PII. `classify_table` / `classify_schema` count as writes because
they store verdicts.

## The tools that save the most time

- **`draft_entity`** builds a complete entity from the two agents and the two tables: it runs
  discovery, maps columns, and reuses the ids of an entity already configured under that name.
  Optional `key_columns`, `column_mappings`, `document_key`, `mapping_function`.
- **`validate_entities`** checks an entity payload without writing it and names what is wrong (an
  unassigned agent, a missing column mapping, a key nothing maps to). Run it on anything you
  assembled or edited by hand.
- **`describe_entity_schema`** returns the real JSON Schema of an entity payload.
- **`get_pipeline_draft_status`** explains why a pipeline is still a Draft;
  **`complete_pipeline_configuration`** leaves Draft once source and target have saved connections.
- **`verify_pipeline_connections`** tests every agent's database connection live.
- **`search_documentation`** searches the Gluesync docs from inside Core Hub.

## Never call without explicit user approval

`delete_pipeline`, `delete_entities`, `delete_connection`, `unassign_agent`, `redo` / `redo_sync`,
`reconcile_data_comparison_differences`, `enter_maintenance_mode` / `exit_maintenance_mode`, and any
`execute_sql` that is not a read. **`reset_pipeline_checkpoint`**: only under Gluesync support's
supervision
([stalled pipelines](https://docs.molo17.com/gluesync/latest/learn/how-to-diagnose-a-stalled-pipeline-or-entity.html)).
