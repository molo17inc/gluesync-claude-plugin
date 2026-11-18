# Core Hub REST API

Source: [Core Hub APIs](https://docs.molo17.com/gluesync/latest/core-hub/core-hub-apis.html),
[Swagger](https://docs.molo17.com/gluesync/latest/apis/swagger.html),
[Automate Gluesync with the REST API, MCP and webhooks](https://docs.molo17.com/gluesync/latest/learn/how-to-automate-gluesync-with-the-rest-api-mcp-and-webhooks.html).

The docs present the REST API as the advanced route. For firing an action or a chain from another
system, Chronos webhook triggers are simpler (**Scheduler → Events → New → Webhook trigger**).
For configuring pipelines from Claude, the MCP tools are safer ([mcp.md](mcp.md)).

**The user's own Swagger is the authority**: `https://<core-hub>/swagger`. Sign in to the Control
Plane in the same browser first, then **Authorize** with a token. An OpenAPI 3.0.3 file is also
downloadable from the docs. Payloads and paths have changed between releases; check there before
shaping a body by hand.

## Basics

- Base: the Core Hub address (`https://<host>` behind the reverse proxy, `https://<host>:1717`
  without it). Endpoints sit at the root: no `/api` prefix.
- JSON over HTTPS. Request headers are capped at 8 KB.
- Unknown paths may be redirected to the Control Plane instead of answering 404: a redirect to the
  UI means the path is wrong. Do not follow redirects automatically, so you see it.
- A failed call explains itself in the response body: always show the body, not just the status.

```http
GET /pipelines
Authorization: Bearer <token>

POST /pipelines
Authorization: Bearer <token>
Content-Type: application/json

{"name": "orders"}
```

With a self-signed certificate, trust the Core Hub's CA in the HTTP client; skip certificate checks
only on a test installation.

## Authentication

Either a Personal API Token or a session token, as `Authorization: Bearer <token>`.

- **Personal API Token** (`gsp_…`), scope `gluesync.api` (read and write) or `gluesync.api_read`
  (reads only; it also refuses the few GETs that change state, such as
  `GET /pipelines/{id}/agents/add`). Tokens cannot create, revoke or delete tokens: that is done in
  the Control Plane. `GET /api-tokens/current-scope` shows what the current token may do.
  ([Personal API Tokens](https://docs.molo17.com/gluesync/latest/security/personal-api-tokens.html))
- **Session token**: `POST /authentication/login` with `{"username", "password"}`. The token is in
  `apiToken` or `token` depending on the release; `changeRequired: true` means the password must be
  changed first (`POST /authentication/reset-password` with `oldPassword`, `newPassword`). Sessions
  last 72 hours by default. OIDC (SSO) users cannot log in programmatically: automation needs a
  local account.
- 401 "Invalid authorization token…": missing, wrong, expired or deleted token. 403 "This token's
  permission scopes (…) do not allow this request. It needs …": wrong scope. 403 "This token is
  limited to specific agents…": agent scope too narrow.

## Configure a pipeline

| Step | Call | Notes |
|---|---|---|
| Create | `POST /pipelines` `{"name", "description"}` | returns the `pipelineId` |
| Read | `GET /pipelines`, `GET /pipelines/{id}` | |
| Agents | `GET /pipelines/{id}/agents` | `id`, `agentName`, `agentTag`, `agentType` |
| Attach an agent | `PUT /pipelines/{id}/agents/{agentId}` | 409 if attached elsewhere; `GET /unassigned-agents` lists free ones |
| Credentials | `PUT /pipelines/{id}/agents/{agentId}/config/credentials` | HostCredentials: `connectionName`, `host`, `databaseName`, `additionalHosts` required; `port`, `username`, `password`, `enableTls`, … optional. 202 |
| Agent capabilities | `GET /pipelines/{id}/agents/{agentId}/discovery/node-info` | entity types, credential fields, specific-config keys with defaults |
| Specific config | `PUT /pipelines/{id}/agents/{agentId}/config/specific` | agent-specific keys from `node-info`. 202 |
| Discovery | `GET …/discovery/schemas`, `…/discovery/tables?schema=<s>`, `…/discovery/columns?tableschema=<s>&tablename=<t>` | parameter names differ per call |
| Entities | `PUT /pipelines/{id}/agents/{agentId}/config/entities` `{"entities": [ … ]}` | batch them in one call; the entity schema is in Swagger (or MCP `describe_entity_schema`) |
| Push config | `PUT /pipelines/{id}/config` | dispatches stored config to agents; push credentials and entities first |

Reusable connections and the agent-adding call are not documented as REST; use the MCP tools
`create_connection` / `attach_connection` / `add_agent` for those.

## Run it

```
POST /pipelines/{id}/commands/sync/start?withSnapshot=true&snapshotWriteMethod=UPSERT
POST /pipelines/{id}/commands/sync/stop
POST /pipelines/{id}/commands/sync/redo                 # discards progress: needs user approval
POST /pipelines/{id}/commands/sync/one-time-snapshot
```

`entity=<entityId>` (repeatable) limits a command to some entities; without it the whole pipeline
is affected. **Use entity IDs**: a name is accepted with 202 and changes nothing. IDs come from
`GET /pipelines/{id}/entities` (`.entity.entityId`). `snapshotWriteMethod` is `UPSERT` or `INSERT`.

Every command answers **202 = dispatched, not done**. 408 means Core Hub could not reach the agents
in time and the command may still land; verify before retrying. 406 = pipeline in maintenance.
410 = license expired or invalid.

## Read state back

```
GET /pipelines/{id}/entities           # entities and their ids
GET /pipelines/{id}/entities-status    # isSyncActive, isMigrationActive, isBusy, errorState{errorType,message,occurredAtMs}
GET /pipelines/{id}/config             # full configuration
GET /pipelines/{id}/metrics            # per-pipeline metrics
GET /metrics                           # Prometheus text, all pipelines
GET /notifications                     # what the Control Plane shows, errors included
GET /version
```

Entities never started are not listed in `entities-status`.

## Users (SUPER ADMIN or MANAGER)

`GET /users`, `POST /users` (`username`, `password`, `role`), `PUT /users/{username}`,
`DELETE /users/{username}`. Roles: SUPER ADMIN (everything), MANAGER (everything except managing
SUPER ADMINs), VIEWER (read-only).
([User management](https://docs.molo17.com/gluesync/latest/security/user-management-rbac.html))
