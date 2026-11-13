# Configure the server and client

Reference examples below show API composition and configuration fragments. Start with the complete quickstart before adapting these to your application.

## Server (`agenticops-control-tower serve`)

| Option | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Interface to bind. Use `0.0.0.0` to accept other computers on the network ([hosting](../hosting.md)). |
| `--port` | `8000` | Port for the API and the console. |
| `--database PATH` | none (in memory) | SQLite file for inventory, evidence, configuration, alerts and incidents. Relative to the working directory. Without it, everything is lost on restart. |

| Environment variable | Used by | Meaning |
| --- | --- | --- |
| `AGENTICOPS_DATABASE` | server | SQLite path when `--database` is not given. |
| `AGENTICOPS_READ_TOKEN` | server | Bearer token allowed to read. |
| `AGENTICOPS_WRITE_TOKEN` | server | Bearer token allowed to read and write (register, heartbeat, evidence, previews, execution). |
| `AGENTICOPS_APPROVAL_TOKEN` | server | Separate token for approving, denying and revoking actions. Must differ from the reader and writer tokens, or the server refuses to start. |

Token rules, enforced on every HTTP route:

- **No token configured:** anonymous access to inventory routes. Local development

only. Configuration actions, bulk operations and incidents still require

configured credentials.

- **Reader only:** reads work, all writes are rejected.
- A writer token also permits reads. Missing or wrong tokens return `401`; a

reader calling a write route gets `403`.

Generate tokens with `python -c 'import secrets; print(secrets.token_hex(32))'`

or `openssl rand -hex 32`, once per deployment, and keep them in secret storage.

See [Authentication](../authentication.md).

## Built-in limits

| Setting | Value | Where it applies |
| --- | --- | --- |
| Live detection interval | 30 seconds | Scans stored telemetry while the server runs. Python hosts can pass `create_app(detection_interval_seconds=0)` to disable it and call `POST /alerts/evaluate` from their own scheduler. |
| Detection freshness and heartbeat windows | 300 seconds each | `DetectionPolicy`, configurable by a trusted Python host ([live operations](../live-operations.md)). |
| Evidence stale-after | 1 day (max 30 days) | `--stale-after-seconds` / `stale_after_seconds` on posture reads. |
| Evidence history limit | 50 (max 500) | `evidence history --limit`. |
| Request body size | 1 MiB, `Content-Length` required | `POST /evidence` and `POST /bulk/preview`. |
| Action expiry | 1–3600 seconds | Configuration previews ([controlled configuration](../configuration.md)). |

## CLI client

| Option | Environment variable | Default | Meaning |
| --- | --- | --- | --- |
| `--api-url` | `AGENTICOPS_API_URL` | `http://localhost:8000` | Server to talk to. |
| `--token` | `AGENTICOPS_TOKEN` | none | Bearer token sent with every request. |
| `--snapshot FILE` | — | none | Answer read commands from a snapshot file instead of a server. |

Options go **before** the command:

```
agenticops-control-tower --api-url https://tower.example.com --token "$READER_TOKEN" status
```

## Python hosts

Embedding Control Tower in your own service uses the same settings as

arguments, which take precedence over the environment:

```
from agenticops_control_tower.api.http import create_app

app = create_app(
    database_path="registry.sqlite",
    read_token="...",
    write_token="...",
    approval_token="...",
    detection_interval_seconds=30,
)
```

Run it with any ASGI server, for example `uvicorn module:app`.
