# Troubleshooting

Sources: [Diagnose a stalled pipeline or entity](https://docs.molo17.com/gluesync/latest/learn/how-to-diagnose-a-stalled-pipeline-or-entity.html),
[Read Gluesync logs and diagnose errors](https://docs.molo17.com/gluesync/latest/learn/how-to-read-gluesync-logs-and-diagnose-errors.html),
[Troubleshooting](https://docs.molo17.com/gluesync/latest/deploy-and-run/troubleshooting.html),
[Automate with REST, MCP and webhooks](https://docs.molo17.com/gluesync/latest/learn/how-to-automate-gluesync-with-the-rest-api-mcp-and-webhooks.html).

## How to approach it

1. Read the state: entity status and `errorState`, notifications, `get_system_conditions`.
2. Read the **first** ERROR in time, not the last, and the last `Caused by` of its stack trace: the
   database or driver message there is the cause.
3. Prove delivery with a probe row; do not trust a green badge alone.
4. Change one thing, then verify again.

## Symptom → cause → action

| Symptom | Likely cause | Action |
|---|---|---|
| Entity Active, "Idle, no changes yet", nothing arriving | Source database stopped or unreachable; errors only appear after a failed read or write | Check the Timestamp column, insert a probe row, **Count both** |
| **Target write failed** (constraint or type error) | A row the target rejects; later changes queue behind it, retried about once a minute | Fix the cause on the **target** (column length, type, constraint). Do not pause or run Full copy first; fixing the source row does not help |
| Error flag stays after the fix | The flag clears only on the next replicated change | If the probe row arrives, nothing to do |
| Pipeline UNHEALTHY, "Warm-up failed … A new attempt will be made in …", "Cannot start sync, database not initialized" | Database or credentials wrong at startup | Fix them; Core Hub retries (10 s, 20 s, 30 s, then every 5 min). Enter and exit maintenance to retry now |
| "password authentication failed" | Wrong or rotated database password | **Edit source / Edit target** → fix → **Test and continue** |
| "The connection attempt failed." | Wrong host/port, database down, or `localhost` inside a container | Use the host as seen from Core Hub (`host.docker.internal`, Compose service name) |
| "Entity Configuration Changed" | A key or column was changed in Gluesync; the entity was stopped | Check the Fields Editor, then **Start sync** with **Full copy** |
| "replication slot … does not exist" (source position lost) | The source's change log position is gone | Pause, then **Full copy** with **Keep and merge** |
| Pipeline late | A large transaction holds later changes; changes older than **Source change retention in hours** (default 24) are dropped | Watch **Last Transaction ID**; involve support if changes may have been lost |
| Snapshot looks slow | The percentage is an estimate | Compare counts; do not restart a running snapshot |
| HTTP 406 "Pipeline … is in maintenance" | Pipeline in maintenance | Exit maintenance first; it never exits by itself |
| HTTP 410 "License expired or invalid", "Invalid license key" | License missing, invalid or expired; pipelines are paused | Install a valid license and restart Core Hub |
| 401 "Invalid authorization token" | Token missing, wrong, expired or deleted | Create a new token |
| 403 "This token's permission scopes … It needs …" | Wrong scope (e.g. an MCP token used on REST) | Use a token with the scope named in the message |
| MCP 403 "Invalid Host" / "Invalid Origin host" | DNS-rebinding protection | Admin sets `GLUESYNC_MCP_ALLOWED_HOSTS` / `GLUESYNC_MCP_ALLOWED_ORIGINS` and recreates Core Hub |
| HTTP 431 at login | Large cookies from a parent domain | Clear the parent-domain cookies or use a dedicated host name |
| Command answered 202 but nothing changed | Entity named instead of its ID, or the command is still in flight | Use entity IDs; read the status back |

## Logs

- Core Hub log: `logs/core-hub/gluesync-core-hub.log` in the installation folder (archives in
  `logs/core-hub/archived/`); inside the container `/opt/gluesync/logs`.
- Docker Compose: `docker compose logs --tail 200 gluesync-core-hub`.
- Times are UTC unless `TZ` is set. Agent lines carry a tag such as `[postgresql]` or
  `[oracle-cdc]`.
- Support bundle: **Settings → Support**, or `sudo gluesync collect-logs --local-only`.
- Error text can contain row values ("Failing row contains (…)"): share only what is needed.

## When to stop and hand over to support

Reset pipeline checkpoint, Restart platform, suspected data loss, or anything the steps above do
not explain: help the user open a ticket at <https://support.molo17.com> with the pipeline and
entity IDs, the first error with its `Caused by`, the Core Hub version, and what was already tried.
([How to create a support ticket](https://docs.molo17.com/gluesync/latest/learn/how-to-create-a-support-ticket.html))
