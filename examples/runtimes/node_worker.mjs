// Node.js 18+ worker: no npm packages or Python runtime required by the client.
const base = process.env.AGENTICOPS_API_URL || 'http://127.0.0.1:8000';
async function request(path, payload) {
  const response = await fetch(base + path, {
    method: payload === undefined ? 'GET' : 'POST',
    headers: {'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.AGENTICOPS_WRITE_TOKEN || ''}`},
    body: payload === undefined ? undefined : JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
if ((await request('/contracts/capabilities')).contract_version !== 'tower.capabilities.v1')
  throw new Error('Unsupported contract');
await request('/agents/register', {
  agent_id: 'node-worker', name: 'Node worker', runtime: 'nodejs', framework: 'native-fetch',
  environment: 'test', capabilities: {'custom.worker': '1.0'},
});
await request('/agents/node-worker/heartbeat', {status: 'degraded'});
const record = await request('/agents/node-worker');
if (record.status !== 'degraded' || record.heartbeat_count !== 1 ||
    record.capabilities['custom.worker'] !== '1.0') throw new Error('Readback mismatch');
console.log(JSON.stringify(record));
