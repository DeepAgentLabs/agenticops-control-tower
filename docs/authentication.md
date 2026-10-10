# Customer-managed reader and writer tokens

Control Tower is a self-hosted PyPI package. The customer operating the server
creates and manages its tokens; no DeepAgentLabs account or token service is
required. Tokens are shared deployment credentials, not individual user accounts.
There is no built-in token-generation command, sign-in page or token issuance API.

## Generate tokens

Install the package into your Python environment:

```bash
python -m pip install "agenticops-control-tower[api]"
```

Generate independent reader and writer values with Python's standard library:

```bash
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_WRITE_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

These commands use Bash or a compatible shell. Use `python3` instead of `python`
if that is your interpreter name. `openssl rand -hex 32` is an alternative to the
Python generator. Both produce a random 64-character hexadecimal value.

Generate once per deployment and retain the values in your secret manager or a
restricted configuration file. Do not regenerate on every server start: clients
using the previous value would lose access. Environment variables exported in
one terminal do not automatically appear in another terminal or survive logout.

For PowerShell, the equivalent setup is:

```powershell
$env:AGENTICOPS_READ_TOKEN = python -c "import secrets; print(secrets.token_hex(32))"
$env:AGENTICOPS_WRITE_TOKEN = python -c "import secrets; print(secrets.token_hex(32))"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

## Give readers access

Open [http://localhost:8000/console/](http://localhost:8000/console/) on the server's
computer. Retrieve the reader value from your terminal or secret manager and
share it with authorized readers through a secure channel. Paste it into the
console's **Reader token** field and select **Connect / refresh**. The console
holds the token in page memory; reload or **Disconnect** clears it.

For CLI reads, set the client variable to that same reader value:

```bash
# In the server's shell this can reuse the generated value.
# In another shell, first obtain it from your deployment's secret storage.
export AGENTICOPS_TOKEN="$AGENTICOPS_READ_TOKEN"
agenticops-control-tower status
```

| Variable | Set on | Purpose |
| --- | --- | --- |
| `AGENTICOPS_READ_TOKEN` | Server | Authorizes inventory, status, version and evidence-readiness reads |
| `AGENTICOPS_WRITE_TOKEN` | Server | Authorizes reads plus agent registration and heartbeats |
| `AGENTICOPS_TOKEN` | CLI client | Sends a configured reader or writer value to the server |
| `AGENTICOPS_API_URL` | CLI client | Selects the server, e.g. `https://tower.example.com` |

Use the writer value for CLI registration/heartbeats or agent integrations:

```bash
export AGENTICOPS_TOKEN="$AGENTICOPS_WRITE_TOKEN"
agenticops-control-tower agents register examples/sample_agent_registration.json
```

The sample registration file is provided in the source repository; PyPI users
can supply their own JSON file. The console remains read-only even if given a
writer token, but reader tokens are the appropriate credentials to distribute.

## Authorization behavior and rotation

With both server variables unset, the API permits anonymous local development.
With only a reader configured, writes are rejected. With only a writer configured,
reads and writes require that writer. Set different, nonempty values for both roles;
using the same value would give readers writer access.

To rotate a token, generate a new value, update the deployment's secret storage,
restart/redeploy the service, and distribute the replacement to its clients.
The service reads these settings at application startup. It supports one token
per role, with no overlap period, per-user revocation, expiry or tenant isolation.
Do not put tokens in URLs, tracked files, Docker images or shared logs. Use HTTPS
for remote browser/API traffic. See [the hosting guide](hosting.md) for local,
private-network and cloud access.
