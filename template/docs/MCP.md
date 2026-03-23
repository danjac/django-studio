# MCP Servers

This project ships with project-local [Model Context Protocol](https://modelcontextprotocol.io)
(MCP) servers configured in `.mcp.json`. MCP servers give AI assistants (Claude Code) direct
access to your local environment — databases, browsers, the Django shell, and (post-launch)
your Kubernetes cluster.

`.mcp.json` is gitignored and generated at project creation by the Copier post-gen hook.
Restart Claude Code after running `just install` to activate the servers.

---

## Servers

### PostgreSQL

**Package:** `@modelcontextprotocol/server-postgres`

Connects to the local development database using `DATABASE_URL` from `.env`. Requires
Docker services to be running (`just start`).

**Use for:**
- Inspecting table schema and indexes
- Running ad-hoc SQL queries during debugging
- Verifying migration output
- Checking data state without opening a `psql` shell

### Playwright

**Package:** `@playwright/mcp`

Launches a browser that Claude Code can control directly.

**Use for:**
- Investigating E2E test failures interactively
- Capturing screenshots of UI bugs
- Reproducing flaky test sequences step-by-step

### Django shell

**Package:** `mcp-django` (`uv run python -m mcp_django`)

Starts a Django shell session with the full application context loaded
(`DJANGO_SETTINGS_MODULE=config.settings`).

**Use for:**
- ORM queries and queryset debugging
- Model introspection (`MyModel._meta.get_fields()`)
- Calling service functions and management utilities directly
- Checking signal wiring and middleware state

> **Security warning:** This server gives full Python shell access to your Django project,
> including the database. Use it in development only. Never run it against a database that
> contains production data.

### Kubernetes

**Package:** `mcp-server-kubernetes`

Uses your current `kubectl` context (configured by `just get-kubeconfig` during
`/djstudio launch`). Added to `.mcp.json` at the end of the launch wizard — not present
in fresh projects.

**Use for:**
- Checking pod status and events: `kubectl get pods`
- Reading application logs: `kubectl logs <pod>`
- Describing failing deployments
- Inspecting ConfigMaps and Secrets (non-sensitive values)

To add it manually after launch:

```bash
python3 -c "
import json, pathlib
p = pathlib.Path('.mcp.json')
config = json.loads(p.read_text())
config['mcpServers']['kubernetes'] = {
    'command': 'npx',
    'args': ['-y', 'mcp-server-kubernetes']
}
p.write_text(json.dumps(config, indent=2) + '\n')
"
```

---

## Troubleshooting

**Servers not appearing in Claude Code**
Restart Claude Code after project setup. MCP servers are loaded at startup.

**`postgres` fails to connect**
Run `just start` to ensure Docker services are running, then verify `DATABASE_URL` in `.env`.

**`django` fails to start**
Run `just install` to ensure `mcp-django` is installed in the project virtualenv.
Check that `config/settings.py` loads without errors: `uv run python -m django check`.

**`kubernetes` context is wrong**
Run `just get-kubeconfig` to refresh the kubeconfig from the Hetzner cluster, then
restart Claude Code.
