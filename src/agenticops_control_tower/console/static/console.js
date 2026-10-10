"use strict";
const byId = (id) => document.getElementById(id);
let token = "", generation = 0, detailGeneration = 0, controller;
const node = (tag, value, className) => {
  const element = document.createElement(tag);
  if (value !== undefined) element.textContent = value;
  if (className) element.className = className;
  return element;
};
async function get(path, signal) {
  const response = await fetch(new URL(path, new URL("../", location.href)), {
    method: "GET", headers: token ? {Authorization: `Bearer ${token}`} : {},
    cache: "no-store", signal, credentials: "omit"
  });
  if (!response.ok) throw new Error(response.status === 401 ? "Reader token required or invalid." : `Unable to read inventory (HTTP ${response.status}).`);
  return response.json();
}
function clear() {
  byId("fleet").hidden = true; byId("detail").hidden = true;
  for (const id of ["agents", "metrics", "coverage", "detail-data", "evidence"]) byId(id).replaceChildren();
}
function options(id, values) {
  const select = byId(id), current = select.value;
  while (select.options.length > 1) select.remove(1);
  for (const value of [...new Set(values)].sort()) {const option = node("option", value); option.value = value; select.append(option);}
  if (values.includes(current)) select.value = current;
}
async function detail(agentId, signal, requestGeneration) {
  const selection = ++detailGeneration;
  byId("detail").hidden = true;
  try {
    const [agent, evidence] = await Promise.all([get(`agents/${encodeURIComponent(agentId)}`, signal), get(`agents/${encodeURIComponent(agentId)}/evidence`, signal)]);
    if (generation !== requestGeneration || selection !== detailGeneration) return;
    byId("detail-title").textContent = agent.name;
    byId("detail-data").textContent = JSON.stringify(agent, null, 2);
    byId("evidence").textContent = `${evidence.availability}: ${evidence.reason}`;
    byId("detail").hidden = false;
    byId("detail").scrollIntoView({behavior:"smooth", block:"nearest"});
  } catch (error) {if (generation === requestGeneration && error.name !== "AbortError") byId("message").textContent = error.message;}
}
async function load(refreshOptions = false) {
  controller?.abort(); controller = new AbortController();
  const signal = controller.signal, requestGeneration = ++generation;
  clear(); byId("message").textContent = "Loading fleet…";
  try {
    const params = new URLSearchParams(), environment = byId("environment").value;
    if (environment) params.set("environment", environment);
    if (byId("health").value) params.set("status", byId("health").value);
    const capability = byId("capability").value, minimum = byId("minimum").value.trim();
    if (capability) params.set(byId("presence").value === "missing" ? "missing_capability" : "capability", capability);
    if (minimum && !capability) throw new Error("Select a capability for the minimum version check.");
    const statusParams = new URLSearchParams(environment ? {environment} : {});
    const versionParams = new URLSearchParams({capability, minimum_version:minimum});
    if (environment) versionParams.set("environment", environment);
    const [agents, status, versions, allAgents] = await Promise.all([
      get(`agents?${params}`, signal), get(`status?${statusParams}`, signal),
      minimum ? get(`versions?${versionParams}`, signal) : Promise.resolve([]),
      refreshOptions ? get("agents", signal) : Promise.resolve(null)
    ]);
    if (generation !== requestGeneration) return;
    if (allAgents) {options("environment", allAgents.map(a=>a.environment)); options("capability", allAgents.flatMap(a=>Object.keys(a.capabilities)));}
    for (const [label, key, color] of [["Total", "total_agents", ""], ["Healthy", "healthy_agents", "healthy"], ["Degraded", "degraded_agents", "degraded"], ["Unhealthy", "unhealthy_agents", "unhealthy"], ["Unknown", "unknown_agents", "unknown"]]) {
      const card = node("div", undefined, `metric ${color}`); card.append(node("span", label), node("strong", status[key])); byId("metrics").append(card);
    }
    const checks = new Map(versions.map(v=>[v.agent_id,v])), search = byId("search").value.toLowerCase();
    const visible = agents.filter(a=>`${a.agent_id} ${a.name}`.toLowerCase().includes(search));
    for (const agent of visible) {
      const row = node("tr"), name = node("td"), button = node("button", agent.name);
      button.type = "button"; button.addEventListener("click", ()=>detail(agent.agent_id,signal,requestGeneration));
      name.append(button, node("small", agent.agent_id));
      const runtime = node("td", agent.environment); runtime.append(node("small", `${agent.runtime} / ${agent.framework}`));
      const caps = node("td");
      for (const [name, version] of Object.entries(agent.capabilities)) caps.append(node("div", `${name}: ${version}`));
      if (!Object.keys(agent.capabilities).length) caps.textContent = "None reported";
      const check = checks.get(agent.agent_id);
      const versionCell = node("td", check ? check.assessment.replaceAll("_", " ") : "No minimum set");
      if (check?.reason) versionCell.append(node("small", check.reason));
      row.append(name, runtime, node("td", agent.status, agent.status), node("td", agent.last_seen ? new Date(agent.last_seen).toLocaleString() : "Never reported"), caps, versionCell);
      byId("agents").append(row);
    }
    byId("empty").hidden = visible.length > 0;
    for (const capability of status.capabilities) {
      const card = node("article"); card.append(node("strong", capability.capability));
      const meter = node("meter"); meter.min = 0; meter.max = Math.max(1,status.total_agents); meter.value = capability.installed_agents; meter.setAttribute("aria-label", `${capability.capability} coverage`);
      card.append(meter, node("div", `${capability.installed_agents} installed · ${capability.missing_agents} missing`), node("p", `Versions: ${capability.versions.join(", ")}`)); byId("coverage").append(card);
    }
    if (!status.capabilities.length) byId("coverage").append(node("p", "No capabilities reported."));
    byId("updated").textContent = `Refreshed ${new Date().toLocaleTimeString()}`;
    byId("message").textContent = `${visible.length} agents shown. Select an agent to inspect metadata and evidence readiness.`;
    byId("fleet").hidden = false;
  } catch(error) {if (generation === requestGeneration && error.name !== "AbortError") {clear(); byId("message").textContent = error.message;}}
}
byId("connection").addEventListener("submit", event=>{event.preventDefault(); token = byId("token").value || token; byId("token").value = ""; load(true);});
byId("filters").addEventListener("submit", event=>{event.preventDefault(); load();});
byId("disconnect").addEventListener("click", ()=>{controller?.abort(); generation++; token = ""; byId("token").value = ""; clear(); byId("message").textContent = "Disconnected. Credentials and inventory cleared.";});
