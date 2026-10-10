# Control Tower examples

## Generate customer-managed tokens and open the console

Install the PyPI package, generate two independent tokens, and run the server
in the same terminal (Bash):

```bash
python -m pip install "agenticops-control-tower[api]"
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_WRITE_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
agenticops-control-tower serve --host 127.0.0.1 --port 8000 --database registry.sqlite
```

Open [http://localhost:8000/console/](http://localhost:8000/console/) and enter the
reader value from this deployment. Customers generate tokens themselves; no
DeepAgentLabs account is needed. Save tokens in secret storage and reuse them
on restart. `openssl rand -hex 32` is another generator; use `python3` if that
is the Python command in your environment.

From a source checkout, `bash examples/run_local_console.sh` starts the same
service after you export the tokens. It reuses credentials and never prints them. Set `AGENTICOPS_PORT` to override
the default port 8000, or `AGENTICOPS_DATABASE` to select another SQLite path.

In another terminal, obtain the same writer value from your secret storage and
set `AGENTICOPS_TOKEN` before registering a sample deployment:

```bash
export AGENTICOPS_TOKEN='your-generated-writer-value'
agenticops-control-tower agents register examples/sample_agent_registration.json
```

Refresh the console to see it. Sample payloads also cover containers and
Kubernetes. The files are in the source checkout; PyPI users can create their own
registration JSON following the README contract.

## Share a hosted console link

Localhost works on the computer running the browser. For remote users deploy the
Python service behind HTTPS and share `https://<your-hostname>/console/` along
with the reader token through a secure channel. Route both the console and API
to the same service. Use [docs/hosting.md](../docs/hosting.md) for cloud startup,
persistent storage, network routing, private SSH tunnels and troubleshooting.
[hosting/nginx.conf](hosting/nginx.conf) is a VM reverse-proxy example, requiring
your own hostname and existing certificates.

## Other examples

- `sample_fleet_snapshot.json`: offline read-only inventory using
  `agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json status`.
- `inspect_ecosystem_evidence.py`: native evidence-reader attribution; see
  [ecosystem alignment](../docs/ecosystem-alignment.md).

See [authentication](../docs/authentication.md) for PowerShell, role semantics,
client variables and rotation.
