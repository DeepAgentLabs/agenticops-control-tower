# Register agents and send heartbeats

Start the server using [the quickstart](quickstart.md). In a second terminal, activate the same environment and configure the writer token for the CLI client.

## Client credentials

PowerShell

```
$env:AGENTICOPS_TOKEN = "THE_SERVER_WRITER_TOKEN"
```

macOS / Linux

```
export AGENTICOPS_TOKEN="THE_SERVER_WRITER_TOKEN"
```

The server's token setting is not automatically inherited by another terminal.

tower_registration.json · complete file

```json
{
  "agent_id": "support-demo",
  "name": "Support demo",
  "environment": "staging",
  "runtime": "local-python",
  "framework": "custom",
  "status": "unknown",
  "capabilities": {}
}
```

[Download tower_registration.json](examples/tower_registration.json)

tower_heartbeat.json · complete file

```json
{"status":"healthy","capabilities":{}}
```

[Download tower_heartbeat.json](examples/tower_heartbeat.json)

```
agenticops-control-tower agents register tower_registration.json
agenticops-control-tower agents heartbeat support-demo tower_heartbeat.json
agenticops-control-tower status
```

**Expected:** the registered demo deployment reports a healthy heartbeat. Refresh the console to inspect it. This is a manually supplied demo heartbeat, not a runtime probe.
