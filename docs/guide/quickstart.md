# Quickstart

**Operate: Which agents exist, what evidence do they have, and what needs attention?**

**Input:** Registrations, heartbeats, explicit evidence links, and operator configuration.  
**Output:** Fleet inventory, evidence posture, alerts, incident views, and approved operational workflows.

## Install

```
python -m pip install "agenticops-control-tower[api]"
```

## Read a fleet snapshot offline

Download the repository's sample snapshot. It represents historical fixture data; its embedded package fields are evidence values, not installation recommendations.

[Download sample_fleet_snapshot.json](examples/sample_fleet_snapshot.json)

```
agenticops-control-tower --snapshot sample_fleet_snapshot.json status
agenticops-control-tower --snapshot sample_fleet_snapshot.json agents list
agenticops-control-tower --snapshot sample_fleet_snapshot.json posture
```

**Expected:** the fixture lists two agents and their recorded status/evidence. This reports the snapshot, not a live health check.

## Start a local console

Create separate reader and writer tokens, then configure them in the server terminal. The placeholders below must be replaced with generated secrets.

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Windows PowerShell

```
$env:AGENTICOPS_READ_TOKEN = "YOUR_GENERATED_READER_TOKEN"
$env:AGENTICOPS_WRITE_TOKEN = "YOUR_GENERATED_WRITER_TOKEN"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

macOS / Linux

```
export AGENTICOPS_READ_TOKEN="YOUR_GENERATED_READER_TOKEN"
export AGENTICOPS_WRITE_TOKEN="YOUR_GENERATED_WRITER_TOKEN"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

Open [the local console](http://localhost:8000/console/), supply the reader token, and refresh. A fresh registry is empty until agents register; loading the offline snapshot does not populate the server.

## Connect agents and evidence

Register an agent using the documented registration payload, send heartbeats from its runtime, then push producer artifacts with explicit agent/run links. Use a writer token for mutations. Evidence posture and reported runtime health remain separate signals.

[Register and send heartbeats ↗](../getting-started.md)[Link evidence ↗](../evidence-posture.md)[Authentication ↗](../authentication.md)
