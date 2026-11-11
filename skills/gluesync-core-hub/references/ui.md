# Control Plane (web UI) guide

Labels are quoted as the documentation writes them; the UI is translated (English, Italian,
Spanish, Japanese) and evolves, so if a label differs on the user's screen, describe the intent
and let them find the closest match. Sources are linked per section.

## Sign in and find your way

- Open the Core Hub address from installation. First sign-in: `admin` / `admin`, then a new
  password is required. Change it before exposing the Control Plane beyond a trusted network.
  ([installers](https://docs.molo17.com/gluesync/latest/deploy-and-run/default-installers.html))
- Left menu: **Pipelines** (the landing page; some guides say **Data pipelines**), **Schedules**,
  **Metrics & Insights** (Grafana), **Modules Manager**, **Query Studio**, **Query Forge**,
  **Automator**. What shows depends on the role.
  ([Control Plane tour](https://docs.molo17.com/gluesync/latest/core-hub/control-plane-features.html))
- Header: notifications (bell), documentation, support, and the user menu with **Settings**.
- **Settings** tabs: Account, Global settings, AI agents, Notifications, Smart alerts, User
  management, OIDC configuration, License, Support, Danger zone, Developer mode, About.
  ([Settings](https://docs.molo17.com/gluesync/latest/core-hub/control-plane-settings.html))
- Pipeline statuses: Active, Draft (source or target incomplete), In maintenance, On warm-up,
  On error.

## Create a pipeline

([Get started](https://docs.molo17.com/gluesync/latest/core-hub/get-started.html),
[Adding agents](https://docs.molo17.com/gluesync/latest/core-hub/adding-agents.html))

1. **Pipelines** → **Pipeline** (the button with the plus icon).
2. **Setup source**: pick the technology, then the flavor if it has several capture methods
   (Oracle, SQL Server, Db2 LUW). Choose an available agent. Fill **Base settings** (host, port,
   database, username, password); **Advanced settings** only if needed. **Test and continue**.
3. **Setup target(s)**: same, for each target.
4. **Ready**: name the pipeline (technology, environment and role help, e.g.
   `postgres-orders-prod-source`) → **Finish**. It opens with no entities.

Host names are resolved from where the agent runs: in containers `localhost` is the container
itself; use `host.docker.internal` or the Compose service name.

## Choose tables and map fields

([Get started](https://docs.molo17.com/gluesync/latest/core-hub/get-started.html),
[Fields Editor](https://docs.molo17.com/gluesync/latest/core-hub/fields-editor.html),
[Import entities](https://docs.molo17.com/gluesync/latest/core-hub/import-entities-from-a-file.html))

1. In the pipeline, **Entities** → pick tables or collections in the **Objects Browser**.
2. Review the proposed target names and field mappings. The **Fields Editor** shows source on the
   left, target on the right; arrows map columns 1:1, N:1 (with a function) or 1:N. Toolbar:
   **Undo**, **Show all columns / Hide columns**, **Clear mapping**, **Reset mapping**. Anything on
   the **Error** tab blocks **Confirm**.
3. Confirm, then save the entity.
4. Many entities at once (Core Hub 2.3.2+): **Import entities** → drop a YAML or ZIP → **Validate**
   → **Add n entities to the selection** → **Confirm and continue**. Imported entities are not
   started.

## Start, pause, restart

([Start a snapshot and CDC](https://docs.molo17.com/gluesync/latest/learn/how-to-start-a-snapshot-and-cdc.html))

- **Start one entity**: **Start sync** (play icon) in its row.
  - **Start from**: **Full copy** (first start), **Where it stopped**, or **Now**.
  - **Data already in the target**: **Keep and merge** (safe), **Empty the table first**, or
    **Delete only some rows first**. The last two delete data and need the confirmation box.
  - **Speed**: Standard, Faster or Custom. Read **What will happen**, then **Start entity**.
  - When the snapshot finishes, CDC takes over by itself.
- **Several entities**: tick them, then **Start CDC**, **Snapshot** or **Pause** in the blue bar.
- **Copy once without CDC**: entity on hold → **Run one-time snapshot** → **Start snapshot**.
- **Pause**: **Stop sync** (pause icon) → **Pause entity**. Keeps the checkpoint; deletes nothing.
- **Restart from zero**: pause → **Start sync** with **Full copy** + **Empty the table first** +
  the confirmation → **Start entity**. This deletes target rows: make sure the user means it.

## Is it working?

([Diagnose a stalled pipeline](https://docs.molo17.com/gluesync/latest/learn/how-to-diagnose-a-stalled-pipeline-or-entity.html))

- Entity groups: **Hold**, **Snapshot**, **Active**, **Error**. The header shows "(N out of M
  operational)".
- **Open entity detail** (chevron): **Replication Status** and **Performance Metrics**; **Last
  Transaction ID** shows whether a late pipeline is still moving.
- **Count both** compares source and target row counts; the **Timestamp** column shows the last
  change. Grafana dashboards are under **Metrics & Insights**.
- A green entity is not proof: insert a probe row on the source and look for it on the target.

## Errors, notifications and logs

([Notifications hub](https://docs.molo17.com/gluesync/latest/core-hub/notifications-hub.html),
[Read logs](https://docs.molo17.com/gluesync/latest/learn/how-to-read-gluesync-logs-and-diagnose-errors.html))

- An entity in error shows a red banner (**Source read failed**, **Target write failed**,
  **Pipeline error**, **Connection pool couldn't start**, **Agent unhealthy**) with **View
  notifications** and **Copy error**.
- Bell icon → **Notifications hub**: search, filter by Info / Warning / Error / System and dates,
  expand a row for the **Stack trace**.
- **Settings → Support**: **Upload Logs to Support** (email + ticket ID) or **Collect Local**; log
  level and retention.
- Fix credentials on an existing pipeline: gear icon → **Edit source** / **Edit target** → correct
  the field → **Test and continue**. A failed test still stores the value: correct it and test
  again before leaving the page.

## Maintenance mode

([Maintenance mode](https://docs.molo17.com/gluesync/latest/core-hub/maintenance-mode.html))

Pauses a whole pipeline for changes such as replacing a connector. Enter it from the pipeline
header (gear icon → **Enter maintenance**, or the pause button, depending on the release); leave it
from the **In maintenance** chip → **Exit maintenance**. Gluesync never leaves maintenance by
itself. Starting an entity in maintenance fails with 406.

## Account, users, license, AI agents

- **API tokens**: user menu → **Settings → Account → Personal API Tokens → New token**: name,
  **Expiry**, at least one **Permission scope** → **Create**. Copy it now: it is shown once.
  ([PATs](https://docs.molo17.com/gluesync/latest/security/personal-api-tokens.html))
- **Users** (SUPER ADMIN): **Settings → User management → Add New Account** (username, role MANAGER
  or VIEWER) → **Create**; the generated password is shown once.
  ([RBAC](https://docs.molo17.com/gluesync/latest/security/user-management-rbac.html))
- **License**: **Settings → License**: type and expiry; upload a new `.dat` file (docker-compose
  deployments). An expired license keeps the UI available but pauses all pipelines.
  ([License](https://docs.molo17.com/gluesync/latest/core-hub/license-management.html))
- **MCP**: **Settings → AI agents** → **Connect** → **Copy HTTP URL**. See [mcp.md](mcp.md).
- **Danger zone** (Restart platform, Reset pipeline checkpoint): only with Gluesync support.
