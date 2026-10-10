# Host Control Tower and share the console URL

The PyPI package contains both the HTTP API and console assets. Run one Python
service and open its `/console/` route; there is no separate frontend build or
static-site deployment. Installing the package does not provision hosting or
create a public link. The customer supplies the server, credentials and network.

These instructions describe the implemented v0.3 console. If your installed
release predates v0.3, use a published release containing the console or install
this checkout locally with `python -m pip install ".[api]"`.

## Local computer

Install and [generate reader/writer tokens](authentication.md), then run:

```bash
python -m pip install "agenticops-control-tower[api]"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

Open [http://localhost:8000/console/](http://localhost:8000/console/). Enter your
reader token and select **Connect / refresh**. Tokens must be configured in the
server's environment before starting it; the command above reuses those values.
The database path is relative to the working directory. Reuse that file across
restarts to retain inventory. With no registered agents the console shows an
empty fleet; registration and heartbeats populate it.

`localhost` refers to the computer running the browser. Sharing this URL with
someone on a different computer does not give them access to your server.

## Another computer on a private network

Bind to the server's network interfaces:

```bash
agenticops-control-tower serve --database registry.sqlite --host 0.0.0.0 --port 8000
```

Allow the intended clients through the host firewall. For a server whose private
address is `192.168.1.20`, its console URL is `http://192.168.1.20:8000/console/`.
`0.0.0.0` is a bind address, not a browser URL. Use HTTPS through a reverse proxy
when sending bearer tokens between machines.

For private access to a remote VM without opening the application port publicly,
leave the service bound to `127.0.0.1` and use an SSH tunnel from your computer:

```bash
ssh -N -L 8000:127.0.0.1:8000 user@your-server
```

Then open `http://localhost:8000/console/` on your computer. The tunnel carries
traffic to the remote service; server token authorization still applies.

## Cloud VM, container service or application platform

The same service can run on a cloud VM or a platform that supports a long-running
Python web process. Configure these deployment inputs:

| Setting | Value |
| --- | --- |
| Installation | `python -m pip install "agenticops-control-tower[api]"` |
| Reader secret | A generated `AGENTICOPS_READ_TOKEN` in the platform's secret settings |
| Writer secret | A separate generated `AGENTICOPS_WRITE_TOKEN` |
| Persistent storage | A writable persistent volume, for example mounted at `/data` |
| Start command | `agenticops-control-tower serve --host 0.0.0.0 --port 8000 --database /data/registry.sqlite` |
| Internal application port | `8000`, or the port assigned by the platform |
| Public ingress | HTTPS routed to that application port |
| HTTP readiness check | `GET /console/` returns 200; this checks shell serving, not authenticated inventory |
| Shared console URL | `https://<your-hostname>/console/` |

If your platform injects a `PORT` variable, a Bash start command can use:

```bash
agenticops-control-tower serve --host 0.0.0.0 --port "${PORT:-8000}" --database /data/registry.sqlite
```

The CLI does not read `PORT` automatically. The command requires a shell to
expand it; with an exec-array launcher, supply a numeric `--port` value or use
an explicit shell launcher. Create/mount `/data` before starting the process.
Without persistent storage, use in-memory mode by omitting `--database`, but
inventory is lost on restart; writing SQLite to an ephemeral filesystem does
not provide durable storage.

For this SQLite deployment use one service instance with its own local persistent
volume. Independent replicas have separate inventory; distributed/shared storage
and a horizontally scaled control plane are not implemented. Have the platform
restart the process after failure and retain configured tokens across redeploys.

A platform-generated HTTPS hostname can be shared immediately after deployment.
For your own hostname, configure DNS and a TLS certificate using the platform's
custom-domain settings or your reverse proxy. The URL is then, for example,
`https://tower.example.com/console/`. Users supply your reader token after opening
that link. A link alone does not grant inventory access.

Route **the whole application** on the same hostname: `/console/`,
`/console/assets/`, `/agents`, `/status`, `/capabilities` and `/versions`.
The console fetches its API from the same origin. Hosting only its HTML/assets
or routing only `/console/` leaves those data requests disconnected. This guide
uses a dedicated hostname at the root; hosting beneath another path prefix has
not been validated.

## Example HTTPS reverse proxy on a VM

Run Control Tower bound to `127.0.0.1:8000`. Install/configure Nginx separately
and adapt [the example configuration](../examples/hosting/nginx.conf) with your
hostname and existing certificate paths. It redirects HTTP to HTTPS and proxies
all application paths to the local service. Expose ports 80/443 and keep 8000
private. On a platform with managed HTTPS ingress, its proxy replaces this step.

Validate your adapted configuration before reloading Nginx:

```bash
sudo nginx -t
```

The example follows the official [Nginx proxy module documentation](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
For process and reverse-proxy deployment guidance, see [Uvicorn deployment](https://www.uvicorn.org/deployment/).

## Verify access and troubleshoot

Open your actual console URL, enter the reader token and select **Connect /
refresh**. From a client shell holding that token, verify the same API:

```bash
export AGENTICOPS_API_URL='https://tower.example.com'
export AGENTICOPS_TOKEN="$AGENTICOPS_READ_TOKEN"
agenticops-control-tower status
```

Set `AGENTICOPS_READ_TOKEN` in this client shell to the deployed value first;
client variables are not automatically copied from your cloud server. Setting
`AGENTICOPS_API_URL` changes the CLI target, not the browser console's API origin.

| Symptom | What to check |
| --- | --- |
| Connection refused or timeout | Process running, correct bind address/port, firewall and ingress routing |
| `/console/` returns 404 | Installed package includes v0.3 console; proxy forwards the full path |
| Shell loads but inventory fails | API routes on the same origin and Authorization header preserved |
| Reader token required or invalid | Browser token matches the running server's configured reader value |
| Writes return 403 | Use the writer value for registration/heartbeats |
| Inventory disappears after restart | Same SQLite file on a persistent volume; same service instance |
| Console loads but is empty | Agents have been registered with this deployment |
| Evidence says unavailable | Expected in v0.3: the service does not collect or persist artifacts |

See [customer-managed authentication](authentication.md) and
[the runnable examples](../examples/README.md).
