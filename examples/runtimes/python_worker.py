"""Register a Python worker using only the standard library; server must be running."""

import json
import os
import urllib.request

base = os.environ.get("AGENTICOPS_API_URL", "http://127.0.0.1:8000")
token = os.environ.get("AGENTICOPS_WRITE_TOKEN", "")


def request(path, payload=None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = None if payload is None else json.dumps(payload).encode()
    with urllib.request.urlopen(urllib.request.Request(base + path, data, headers)) as response:
        return json.load(response)


assert request("/contracts/capabilities")["contract_version"] == "tower.capabilities.v1"
request("/agents/register", {
    "agent_id": "python-worker", "name": "Python worker", "runtime": "cpython",
    "framework": "stdlib", "environment": "test", "capabilities": {"custom.worker": "1.0"},
})
request("/agents/python-worker/heartbeat", {"status": "healthy"})
record = request("/agents/python-worker")
assert record["status"] == "healthy" and record["heartbeat_count"] == 1
assert record["capabilities"] == {"custom.worker": "1.0"}
print(json.dumps(record))
