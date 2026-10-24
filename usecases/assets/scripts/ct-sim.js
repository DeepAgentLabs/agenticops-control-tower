/* Interactive use-case simulators for the Control Tower use cases.
   Browser-only illustrations of each walkthrough: no Tower server, agent,
   model or network is called. Every name, count and message mirrors the
   walkthrough's expected output on the same page. */
(() => {
  "use strict";

  /* ---------- tiny DOM helpers ---------- */
  const h = (tag, attrs = {}, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid);
    return el;
  };
  const pill = (text, tone = "") => h("span", { class: `ct-pill ${tone}`, text });
  const dotPill = (text, tone = "") => h("span", { class: `ct-pill ${tone}` }, h("i", { class: "ct-dot" }), text);
  const setKids = (el, ...kids) => { el.replaceChildren(...kids.flat().filter(Boolean)); };
  const logLine = (html, isNew) => { const li = h("li", { class: isNew ? "is-new" : "" }); li.innerHTML = html; return li; };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ---------- engine ---------- */
  function mount(root, sc) {
    const reduce = matchMedia("(prefers-reduced-motion: reduce)");
    const caption = root.querySelector("figcaption");
    root.querySelector("noscript")?.remove();
    root.querySelectorAll(".ct-sim-fallback").forEach((n) => n.remove());

    const head = h("div", { class: "ct-sim-head" },
      h("div", {}, h("span", { class: "ct-sim-eyebrow", text: sc.eyebrow }), h("h3", { class: "ct-sim-title", text: sc.title })),
      h("span", { class: "ct-sim-badge", text: "Interactive · fictional data" }));
    const rail = h("div", { class: "ct-sim-rail", role: "group", "aria-label": "Steps" });
    const railBtns = sc.steps.map((s, i) => {
      const b = h("button", { type: "button", onclick: () => go(i, true) },
        h("span", { class: "ct-n", text: String(i + 1) }), h("span", { class: "ct-l", text: s.label }));
      rail.append(b); return b;
    });
    const progress = h("div", { class: "ct-sim-progress", "aria-hidden": "true" }, h("span"));
    const stage = h("div", { class: "ct-sim-stage" });
    const sayStep = h("span", { class: "ct-say-step" });
    const sayTitle = h("p", { class: "ct-say-title" });
    const sayText = h("p", { class: "ct-say-text" });
    const sayCode = h("div", { class: "ct-say-code" }, h("code"));
    const sayChoices = h("div", { class: "ct-say-choices", hidden: true });
    const say = h("div", { class: "ct-sim-say", role: "status", "aria-live": "off" }, sayStep, sayTitle, sayText, sayCode, sayChoices);
    const back = h("button", { type: "button", class: "ct-btn", onclick: () => go(idx - 1, true) }, "◀ Back");
    const play = h("button", { type: "button", class: "ct-btn ct-primary", onclick: () => toggle() });
    const next = h("button", { type: "button", class: "ct-btn", onclick: () => go(idx + 1, true) }, "Next ▶");
    const restart = h("button", { type: "button", class: "ct-btn", onclick: () => { go(0, true); playing = true; schedule(); paint(); } }, "↺ Restart");
    const hint = h("span", { class: "ct-sim-hint", text: "Click any step, or use ← →" });
    const controls = h("div", { class: "ct-sim-controls" }, h("div", {}, back, play, next, restart), hint);
    const metrics = h("div", { class: "ct-sim-metrics" });
    metrics.style.setProperty("--ct-cols", sc.metrics.length);
    const metricEls = sc.metrics.map((label) => {
      const cell = h("div", {}, h("b", { text: "–" }), h("span", { text: label }));
      metrics.append(cell); return cell;
    });

    root.replaceChildren(head, rail, progress, stage, say, controls, metrics);
    if (caption) root.append(caption);
    const refs = sc.build(stage, { h, pill, dotPill, setKids, logLine, esc });

    let idx = 0;
    let playing = !reduce.matches;
    let visible = false;
    let timer = null;

    function paint() {
      const running = playing && visible && !document.hidden;
      root.classList.toggle("ct-running", running);
      play.textContent = playing ? "Ⅱ Pause" : "▶ Play";
      play.setAttribute("aria-pressed", String(playing));
    }
    function schedule() {
      clearTimeout(timer);
      paint();
      const bar = progress.firstChild;
      bar.style.animation = "none"; void bar.offsetWidth; bar.style.animation = "";
      if (!(playing && visible && !document.hidden)) return;
      const last = idx === sc.steps.length - 1;
      const dwell = (sc.steps[idx].dwell || 3600) + (last ? 2200 : 0);
      root.style.setProperty("--ct-dwell", dwell + "ms");
      timer = setTimeout(() => {
          go(last ? 0 : idx + 1, false);
      }, dwell);
    }
    function toggle() {
      playing = !playing;
      if (playing && idx === sc.steps.length - 1) go(0, false);
      else schedule();
    }

    function go(i, manual) {
      if (i < 0 || i >= sc.steps.length) return;
      const prev = idx; idx = i;
      if (manual) playing = false;
      const step = sc.steps[i];
      sc.render(refs, i, prev, step);
      railBtns.forEach((b, j) => {
        b.classList.toggle("done", j < i);
        if (j === i) b.setAttribute("aria-current", "step"); else b.removeAttribute("aria-current");
      });
      if (manual) railBtns[i].scrollIntoView({ block: "nearest", inline: "nearest" });
      sayStep.textContent = `Step ${i + 1} of ${sc.steps.length} · ${step.label}`;
      sayTitle.textContent = step.title;
      sayText.textContent = step.text;
      sayCode.firstChild.textContent = step.code;
      say.setAttribute("aria-live", manual ? "polite" : "off");
      setKids(sayChoices);
      sayChoices.hidden = !step.choices;
      if (step.choices) {
        sayChoices.append(h("span", { text: step.choices.prompt }));
        for (const c of step.choices.options) {
          sayChoices.append(h("button", {
            type: "button", class: `ct-btn ${c.tone || ""}`,
            onclick: () => { if (c.act) { playing = false; c.act(refs); schedule(); } else go(c.goto, true); },
          }, c.label));
        }
      }
      step.metrics.forEach((v, j) => {
        const b = metricEls[j].firstChild;
        const changed = b.textContent !== String(v);
        b.textContent = String(v);
        metricEls[j].classList.remove("ct-bump");
        if (changed && prev !== -1) { void metricEls[j].offsetWidth; metricEls[j].classList.add("ct-bump"); }
      });
      back.disabled = i === 0;
      next.disabled = i === sc.steps.length - 1;
      schedule();
    }
    sc.metricSetter = (j, v) => {
      const b = metricEls[j].firstChild; b.textContent = String(v);
      metricEls[j].classList.remove("ct-bump"); void metricEls[j].offsetWidth; metricEls[j].classList.add("ct-bump");
    };

    root.addEventListener("keydown", (e) => {
      if (e.target.closest("input, textarea")) return;
      if (e.key === "ArrowRight") { go(idx + 1, true); e.preventDefault(); }
      if (e.key === "ArrowLeft") { go(idx - 1, true); e.preventDefault(); }
    });
    root.tabIndex = -1;
    new IntersectionObserver((es) => { visible = es[0].isIntersecting; schedule(); }, { threshold: 0.25 }).observe(root);
    document.addEventListener("visibilitychange", schedule);
    reduce.addEventListener("change", () => { if (reduce.matches) { playing = false; go(sc.steps.length - 1, false); } });
    idx = -1;
    go(reduce.matches ? sc.steps.length - 1 : 0, false);
  }

  /* ---------- scenario: fleet change with a second approver ---------- */
  const fleetChange = {
    eyebrow: "Bulk fleet operation · two-person rule",
    title: "One change for many agents, with a second pair of eyes.",
    metrics: ["Agents in batch", "Agents changed", "Production touched"],
    steps: [
      { label: "Fleet", title: "Four agents run AgenticLens.", text: "Three in staging, one in production. Tower owns their AgenticLens settings, so it is allowed to change them.", code: 'add_agent(...)  # api.register + api.config.declare(authority="tower")', metrics: [0, 0, 0], s: { batch: false } },
      { label: "Preview", title: "Alice previews one change for staging.", text: "The selector staging + agenticlens becomes an exact list of three agents. Production doesn't match, so it is never selected.", code: 'api.bulk.preview(BulkRequest(selector={"environment": "staging", "capability": "agenticlens"}, patch={"values": {"enhanced_tracing": True}}), alice)', metrics: [3, 0, 0], s: { batch: true, log: 1 } },
      { label: "Late agent", title: "A new agent arrives. It doesn't join.", text: "search-agent registers in staging after the preview. Approval only ever covers the list that was reviewed. Now choose who approves.", code: 'add_agent("search-agent", "staging")  # still frozen: checkout, refund, triage', metrics: [3, 0, 0], s: { batch: true, late: true, log: 1 },
        choices: { prompt: "Who approves this batch?", options: [{ label: "Approve as Alice", goto: 3, tone: "ct-danger" }, { label: "Approve as Bob", goto: 4 }] } },
      { label: "Alice?", title: "Alice can't approve her own change.", text: "Even with an approver role, Tower refuses. The person who proposed a batch can never sign it off.", code: 'api.bulk.decide(bulk_id, True, Operator(operator_id="alice", role="approver"))', metrics: [3, 0, 0], s: { batch: true, late: true, approver: "alice", log: 1 } },
      { label: "Bob", title: "Bob approves the frozen list.", text: "Bob is a different operator. His approval covers exactly the three previewed agents, nothing more.", code: "api.bulk.decide(bulk_id, True, bob)", metrics: [3, 0, 0], s: { batch: true, late: true, approver: "bob", log: 2 } },
      { label: "Execute", title: "The change runs on three agents.", text: "Each staging target switches enhanced_tracing on and reports succeeded. search-agent and production are untouched.", code: "api.bulk.execute(bulk_id, alice)", metrics: [3, 3, 0], dwell: 4400, s: { batch: true, late: true, approver: "bob", done: true, log: 7 } },
      { label: "Audit", title: "Anyone can see who did what.", text: "Proposer alice, approver bob, one audit event per agent. The blast radius is exactly what was reviewed.", code: "api.bulk.get(bulk_id, alice).events", metrics: [3, 3, 0], s: { batch: true, late: true, approver: "bob", done: true, log: 7, audit: true } },
    ],
    log: [
      '<span class="k">bulk.previewed</span> alice',
      '<span class="k">bulk.approved</span> bob',
      '<span class="k">bulk.claimed</span> alice',
      '<span class="k">target.succeeded</span> alice checkout-agent',
      '<span class="k">target.succeeded</span> alice refund-agent',
      '<span class="k">target.succeeded</span> alice triage-agent',
      '<span class="k">bulk.completed</span> alice',
    ],
    build(stage, { h }) {
      const tile = (name, sub) => {
        const tags = h("div", { class: "ct-tags" });
        const el = h("div", { class: "ct-tile" }, h("div", { class: "ct-name", text: name }), h("div", { class: "ct-sub", text: sub }), tags);
        return { el, tags };
      };
      const t = {
        checkout: tile("checkout-agent", "agenticlens 0.10.0"),
        refund: tile("refund-agent", "agenticlens 0.10.0"),
        triage: tile("triage-agent", "agenticlens 0.10.0"),
        search: tile("search-agent", "agenticlens 0.10.0"),
        prod: tile("checkout-agent-prod", "agenticlens 0.10.0"),
      };
      const row = (k) => { const b = h("b", { text: "—" }); return { el: h("div", { class: "ct-row" }, h("span", { text: k }), b), b }; };
      const r = { targets: row("Targets"), proposer: row("Proposer"), approver: row("Approver"), status: row("Status") };
      const batch = h("div", { class: "ct-card ct-fc-batch" },
        h("div", { class: "ct-card-label", text: "Bulk batch" }),
        h("div", { class: "ct-card-value", text: "enhanced_tracing → on" }),
        r.targets.el, r.proposer.el, r.approver.el, r.status.el);
      const toast = h("div", { class: "ct-toast bad", hidden: true, text: "ConfigurationError: Approval requires a different operator" });
      const logList = h("ol");
      const board = h("div", {},
        h("div", { class: "ct-lane" }, h("div", { class: "ct-lane-label" }, h("span", { text: "Staging" }), h("span", { text: "agenticlens" })),
          h("div", { class: "ct-tiles" }, t.checkout.el, t.refund.el, t.triage.el, t.search.el)),
        h("div", { class: "ct-lane" }, h("div", { class: "ct-lane-label" }, h("span", { text: "Production" }), h("span", { text: "agenticlens" })),
          h("div", { class: "ct-tiles" }, t.prod.el)));
      stage.append(h("div", { class: "ct-fc-grid" }, board, h("div", {}, batch, toast)),
        h("div", { class: "ct-log" }, h("div", { class: "ct-log-title", text: "Audit trail · api.bulk.get(...).events" }), logList));
      return { t, r, batch, toast, logList, shown: 0 };
    },
    render(x, i, prev, step) {
      const s = step.s;
      const staging = ["checkout", "refund", "triage"];
      staging.forEach((k, n) => {
        const { el, tags } = x.t[k];
        el.className = "ct-tile" + (s.batch && !s.done ? " is-hit" : "");
        const kids = [];
        if (s.done) kids.push(pill("tracing on", "lime"), pill("succeeded", "ok"));
        else { kids.push(pill("tracing off")); if (s.batch) kids.push(pill("in batch", "lime")); }
        setKids(tags, kids);
        if (s.done && !(prev >= 5)) setTimeout(() => { el.classList.remove("is-flash"); void el.offsetWidth; el.classList.add("is-flash"); }, n * 260);
      });
      const se = x.t.search;
      se.el.className = "ct-tile is-ghost" + (s.late ? "" : " is-hidden") + (s.late && !(prev >= 2) ? " is-new" : "");
      setKids(se.tags, pill("tracing off"), pill(s.audit ? "unchanged" : "not in batch", "warn"));
      const p = x.t.prod;
      p.el.className = "ct-tile" + (s.batch && !s.audit ? " is-dim" : "");
      setKids(p.tags, pill("tracing off"), s.batch ? pill(s.audit ? "unchanged" : "not selected", s.audit ? "warn" : "") : null);
      x.r.targets.b.textContent = s.batch ? "3 frozen" : "—";
      x.r.proposer.b.textContent = s.batch ? "alice" : "—";
      x.r.approver.b.textContent = s.approver === "alice" ? "alice ✕" : s.approver === "bob" ? "bob ✓" : "—";
      x.r.approver.b.className = s.approver === "alice" ? "bad" : s.approver === "bob" ? "ok" : "";
      x.r.status.b.textContent = !s.batch ? "—" : s.done ? "completed" : s.approver === "bob" ? "approved" : "pending";
      x.r.status.b.className = s.done ? "ok" : "";
      x.batch.classList.toggle("is-hit", !!s.batch && s.approver !== "alice");
      x.batch.classList.toggle("is-bad", s.approver === "alice");
      x.batch.classList.remove("is-shake");
      x.toast.hidden = s.approver !== "alice";
      if (s.approver === "alice") { void x.batch.offsetWidth; x.batch.classList.add("is-shake"); }
      const n = s.log || 0;
      setKids(x.logList, fleetChange.log.slice(0, n).map((l, j) => logLine(l, j >= x.shown && prev < i)));
      if (!n) x.logList.append(h("li", { text: "(empty)" }));
      x.shown = n;
    },
  };

  /* ---------- scenario: fleet health snapshot ---------- */
  const agentsFH = [
    { id: "research-bot", env: "staging", rt: "aws-lambda · openai-agents", status: "unhealthy", lens: "0.10.0", sidecar: "0.9.0" },
    { id: "triage-bot", env: "staging", rt: "docker · crewai", status: "degraded", lens: "0.9.0", sidecar: null },
    { id: "checkout-agent", env: "production", rt: "kubernetes · langgraph", status: "healthy", lens: "0.10.0", sidecar: "0.9.0" },
  ];
  const toneOf = { healthy: "ok", degraded: "warn", unhealthy: "bad" };
  const fleetHealth = {
    eyebrow: "Offline snapshot · no server",
    title: "Three agents. Four questions. Five minutes.",
    metrics: ["Agents in snapshot", "Matched by this command", "Server needed"],
    steps: [
      { label: "Your fleet", title: "Write the fleet down once.", text: "my-fleet.json holds three registrations and their latest heartbeats. Control Tower reads it directly: no server, token or network.", code: "my-fleet.json  # 3 registrations + 3 heartbeats", metrics: [3, "–", 0], s: { f: null } },
      { label: "status", title: "1 healthy, 1 degraded, 1 unhealthy.", text: "status rolls the reported health into buckets and shows capability coverage: AgenticLens on all three agents, Agentic Sidecar on two.", code: "agenticops-control-tower --snapshot my-fleet.json status", metrics: [3, 3, 0], s: { f: "status" } },
      { label: "--unhealthy", title: "Which agent is down? research-bot.", text: "One filter returns the only agent reporting unhealthy. It last checked in at 08:41, eighteen minutes before the snapshot.", code: "agenticops-control-tower --snapshot my-fleet.json agents list --unhealthy", metrics: [3, 1, 0], s: { f: "unhealthy" } },
      { label: "missing Sidecar", title: "Which staging agent has no guardrail? triage-bot.", text: "Filters combine with AND: environment staging and missing agentic-sidecar. checkout-agent is in production, so it is filtered out.", code: "agenticops-control-tower --snapshot my-fleet.json agents list --environment staging --missing-capability agentic-sidecar", metrics: [3, 1, 0], s: { f: "sidecar" } },
      { label: "version drift", title: "AgenticLens runs two versions.", text: "capabilities list shows 0.10.0 and 0.9.0 in use. triage-bot is the one still on 0.9.0.", code: "agenticops-control-tower --snapshot my-fleet.json capabilities list", metrics: [3, 1, 0], s: { f: "drift" } },
      { label: "Act", title: "Two agents need attention first.", text: "research-bot is down. triage-bot is degraded, has no Sidecar and runs an older AgenticLens. checkout-agent is fine.", code: "# research-bot: investigate  ·  triage-bot: add Sidecar, upgrade AgenticLens", metrics: [3, 2, 0], s: { f: "act" } },
    ],
    build(stage, { h }) {
      const bar = h("div", { class: "ct-bar" }, h("i", { style: "background:#7be3a4" }), h("i", { style: "background:#ffc56b" }), h("i", { style: "background:#ff8a8a" }));
      const legend = h("div", { class: "ct-fh-legend" },
        h("span", {}, h("i", { style: "background:#7be3a4" }), "healthy 1"),
        h("span", {}, h("i", { style: "background:#ffc56b" }), "degraded 1"),
        h("span", {}, h("i", { style: "background:#ff8a8a" }), "unhealthy 1"),
        h("span", {}, h("i", { style: "background:#26414a" }), "unknown 0"));
      const health = h("div", { class: "ct-card" }, h("div", { class: "ct-card-label", text: "Reported health" }), h("div", { style: "margin-top:10px" }, bar), legend);
      const tiles = agentsFH.map((a) => {
        const tags = h("div", { class: "ct-tags" });
        const el = h("div", { class: "ct-tile" }, h("div", { class: "ct-name", text: a.id }), h("div", { class: "ct-sub", text: `${a.env} · ${a.rt}` }), tags);
        return { a, el, tags };
      });
      stage.append(health, h("div", { class: "ct-tiles", style: "margin-top:10px;grid-template-columns:repeat(auto-fill,minmax(190px,1fr))" }, tiles.map((t) => t.el)));
      return { bar, health, tiles };
    },
    render(x, i, prev, step) {
      const f = step.s.f;
      const showHealth = f !== null;
      [...x.bar.children].forEach((seg) => { seg.style.width = showHealth ? "33.333%" : "0"; });
      x.health.classList.toggle("is-hit", f === "status");
      x.tiles.forEach(({ a, el, tags }) => {
        const hit =
          (f === "unhealthy" && a.status === "unhealthy") ||
          (f === "sidecar" && a.env === "staging" && !a.sidecar) ||
          (f === "drift" && a.lens === "0.9.0") ||
          (f === "act" && a.id !== "checkout-agent");
        const filtering = ["unhealthy", "sidecar", "drift", "act"].includes(f);
        el.className = "ct-tile" + (hit ? " is-hit " + (a.status === "unhealthy" ? "bad" : "warn") : "") + (filtering && !hit ? " is-dim" : "");
        const kids = [];
        kids.push(showHealth ? dotPill(a.status, toneOf[a.status]) : pill("heartbeat"));
        const lensTone = f === "drift" || f === "act" ? (a.lens === "0.9.0" ? "warn" : "ok") : "";
        kids.push(pill(`lens ${a.lens}`, lensTone));
        kids.push(a.sidecar ? pill(`sidecar ${a.sidecar}`, f === "sidecar" ? "ok" : "") : pill("no sidecar", f === "sidecar" || f === "act" || f === "status" ? "bad" : ""));
        setKids(tags, kids);
      });
    },
  };

  /* ---------- scenario: failed Lens run to incident ---------- */
  const lensIncident = {
    eyebrow: "Live detection · alerts and incidents",
    title: "A failed run becomes one alert, and an incident someone owns.",
    metrics: ["Scans", "Alerts raised", "Active alerts", "Incident"],
    steps: [
      { label: "Register", title: "checkout-agent reports healthy.", text: "It runs in staging with AgenticLens. Health is always what the agent reports; Tower never infers it from evidence.", code: 'api.register(AgentRegistrationPayload(agent_id="checkout-agent", environment="staging", status="healthy", ...))', metrics: [0, 0, 0, "none"], s: { run: null, scans: 0, alert: null, inc: null, tl: 0 } },
      { label: "Run fails", title: "AgenticLens reports a failed run.", text: "run-41 failed 30 seconds ago, inside the 300-second freshness window. It is pushed to Tower as evidence.", code: 'push_lens_run("run-41", "failed", now - timedelta(seconds=30))', metrics: [0, 0, 0, "none"], s: { run: "fail", scans: 0, alert: null, inc: null, tl: 1 } },
      { label: "Scan", title: "One critical alert. One open incident.", text: "The detection scan (every 30 s on a server) raises lens.failed at critical severity and links it to a new incident. Reported health stays healthy.", code: "api.operations.evaluate(operator)", metrics: [1, 1, 1, "open"], s: { run: "fail", scans: 1, alert: "active", inc: "open", tl: 3 } },
      { label: "Scan again", title: "Scanning again adds nothing.", text: "Same failure, same alert: alerts are deduplicated, so on-call is paged once, not every 30 seconds. Try it yourself.", code: 'api.operations.evaluate(operator)  # alerts after rescan: 1', metrics: [2, 1, 1, "open"], s: { run: "fail", scans: 2, alert: "active", inc: "open", tl: 3, dedup: true },
        choices: { prompt: "Try it", options: [{ label: "↻ Scan again", act: (x) => { x.extraScans = (x.extraScans || 0) + 1; lensIncident.metricSetter(0, 2 + x.extraScans); x.scanEl.textContent = `scans: ${2 + x.extraScans}`; x.toast.hidden = false; x.toast.textContent = `Scan ${2 + x.extraScans}: still 1 alert. No duplicate.`; x.toast.style.animation = "none"; void x.toast.offsetWidth; x.toast.style.animation = ""; } }] } },
      { label: "Acknowledge", title: "On-call takes ownership.", text: "Acknowledging records who picked it up. It is now part of the incident timeline.", code: "api.operations.acknowledge(alert.alert_id, operator)", metrics: [2, 1, 1, "open"], s: { run: "fail", scans: 2, alert: "ack", inc: "open", tl: 4 } },
      { label: "Run recovers", title: "The alert clears. The incident stays open.", text: "run-42 succeeds and the next scan clears the alert. Clearing an alert never resolves an incident: recovery still needs the approved verification workflow.", code: 'push_lens_run("run-42", "succeeded", now); api.operations.evaluate(operator)', metrics: [3, 1, 0, "open"], dwell: 4600, s: { run: "ok", scans: 3, alert: "cleared", inc: "open", tl: 4, final: true } },
    ],
    timeline: ["evidence.observed", "alert.created", "detected", "alert.acknowledged"],
    build(stage, { h }) {
      const runVal = h("div", { class: "ct-card-value" });
      const runSub = h("div", { class: "ct-sub", style: "font:12px/1.5 var(--ct-mono);color:var(--ct-muted);margin-top:4px" });
      const run = h("div", { class: "ct-card ct-li-run" }, h("div", { class: "ct-card-label", text: "AgenticLens · latest run" }), runVal, runSub);
      const scanEl = h("span", { class: "ct-pill info" });
      const tower = h("div", { class: "ct-card", style: "flex:0 0 auto" }, h("div", { class: "ct-card-label", text: "Control Tower" }), h("div", { style: "margin-top:8px" }, scanEl));
      const card = (label) => { const v = h("div", { class: "ct-card-value" }); const tags = h("div", { class: "ct-tags", style: "margin-top:8px;display:flex;gap:4px;flex-wrap:wrap" }); return { el: h("div", { class: "ct-card" }, h("div", { class: "ct-card-label", text: label }), v, tags), v, tags }; };
      const health = card("Reported health"), alert = card("Alert"), inc = card("Incident");
      const toast = h("div", { class: "ct-toast ok", hidden: true });
      const tl = h("ol");
      stage.append(
        h("div", { class: "ct-li-flow" }, run, h("span", { class: "ct-li-arrow", text: "→" }), tower),
        h("div", { class: "ct-li-grid" }, health.el, alert.el, inc.el), toast,
        h("div", { class: "ct-log" }, h("div", { class: "ct-log-title", text: "Incident timeline · api.operations.incident_view(...)" }), tl));
      return { run, runVal, runSub, scanEl, health, alert, inc, toast, tl, shown: 0 };
    },
    render(x, i, prev, step) {
      const s = step.s;
      x.extraScans = 0;
      x.runVal.textContent = s.run === "fail" ? "run-41 · failed" : s.run === "ok" ? "run-42 · succeeded" : "no runs yet";
      x.runVal.style.color = s.run === "fail" ? "var(--ct-bad)" : s.run === "ok" ? "var(--ct-ok)" : "";
      x.runSub.textContent = s.run === "fail" ? "observed 30 s ago · pushed as evidence" : s.run === "ok" ? "newer run · pushed as evidence" : "waiting for evidence";
      x.run.classList.toggle("is-bad", s.run === "fail" && i === 1);
      x.run.classList.toggle("is-hit", s.run === "ok");
      x.scanEl.textContent = `scans: ${s.scans}`;
      x.health.v.textContent = "healthy";
      setKids(x.health.tags, pill("reported by the agent", "ok"));
      x.health.el.classList.toggle("is-hit", !!s.final);
      const a = s.alert;
      x.alert.v.textContent = a ? "lens.failed" : "none";
      setKids(x.alert.tags, a === "active" ? [pill("critical", "bad"), pill("active", "bad")] : a === "ack" ? [pill("critical", "bad"), pill("acknowledged · on-call", "warn")] : a === "cleared" ? [pill("cleared", "ok"), pill("active alerts: 0")] : [pill("—")]);
      x.alert.el.classList.toggle("is-bad", a === "active");
      x.alert.el.classList.toggle("is-hit", a === "cleared");
      x.inc.v.textContent = s.inc ? "open" : "none";
      setKids(x.inc.tags, s.inc ? [pill("open", "warn"), s.final ? pill("needs approved recovery", "warn") : pill("linked to lens.failed")] : [pill("—")]);
      x.inc.el.classList.toggle("is-hit", !!s.final);
      x.toast.hidden = !s.dedup;
      if (s.dedup) x.toast.textContent = "Rescan: alerts after rescan = 1. No duplicate.";
      setKids(x.tl, lensIncident.timeline.slice(0, s.tl).map((e, j) => logLine(`<span class="k">${e}</span>`, j >= x.shown && prev < i)));
      if (!s.tl) x.tl.append(h("li", { text: "(no events yet)" }));
      x.shown = s.tl;
    },
  };

  /* ---------- scenario: ecosystem evidence posture ---------- */
  const producers = [
    { k: "agenticlens", name: "AgenticLens", what: "1 run failed", detail: "failed tool: payments_api", fresh: "fresh" },
    { k: "agentic-sidecar", name: "Agentic Sidecar", what: "ESCALATE", detail: "risk HIGH · 1 escalation required", fresh: "fresh" },
    { k: "agentic-evals", name: "Agentic Evals", what: "gate failed", detail: "gate: 0 passed · 1 failed", fresh: "fresh" },
    { k: "agentic-chaos", name: "Agentic Chaos", what: "report 2026-08-10", detail: "older than a day: 0 recent experiments", fresh: "stale" },
  ];
  const posture = {
    eyebrow: "Ecosystem evidence posture",
    title: "Four tools, four verdicts, one view. Nothing overridden.",
    metrics: ["Records stored", "Fresh", "Stale", "Missing"],
    steps: [
      { label: "Register", title: "payment-agent has four producers installed.", text: "AgenticLens, Evals, Sidecar and Chaos are all on the deployment, but Tower has no evidence from any of them yet.", code: 'api.register(AgentRegistrationPayload(agent_id="payment-agent", capabilities={...4 producers...}))', metrics: [0, 0, 0, 4], s: { pushed: 0 } },
      { label: "Lens", title: "AgenticLens: a run failed on payments_api.", text: "The pipeline pushes the native Lens run with an EvidenceLink (agent, source, version, ref, observed time).", code: 'api.ingest_evidence(request_for(entry), ingested_by="pipeline")  # pushed agenticlens created=True', metrics: [1, 1, 0, 3], s: { pushed: 1 } },
      { label: "Sidecar + Evals", title: "Sidecar escalated. The Evals gate failed.", text: "Two more native results arrive. Each producer keeps its own verdict; Tower only stores a validated projection.", code: "pushed agentic-sidecar created=True  ·  pushed agentic-evals created=True", metrics: [3, 3, 0, 1], s: { pushed: 3 } },
      { label: "Chaos", title: "Chaos is there, but stale.", text: "Its last report was observed on 2026-08-10, more than a day before the 2026-08-15 snapshot, so it shows as stale.", code: "pushed agentic-chaos created=True", metrics: [4, 3, 1, 0], s: { pushed: 4 } },
      { label: "Retry", title: "A retry stores nothing twice.", text: "The pipeline pushes the Lens run again, as retries do. Tower recognises the same observation: created=False.", code: "api.ingest_evidence(request_for(manifest['entries'][0]), ingested_by=\"pipeline\")  # retry created: False", metrics: [4, 3, 1, 0], s: { pushed: 4, retry: true } },
      { label: "Posture", title: "Failures are shown as-is. Health is untouched.", text: "Three fresh results, one stale. Reported health is still healthy: producer outcomes never change it, and Tower never recomputes a verdict.", code: 'api.agent_posture("payment-agent", now=as_of)  # reported health: healthy', metrics: [4, 3, 1, 0], dwell: 4600, s: { pushed: 4, final: true } },
    ],
    build(stage, { h }) {
      const cards = producers.map((p) => {
        const st = h("div", { class: "ct-tags" });
        const el = h("div", { class: "ct-tile" }, h("div", { class: "ct-name", text: p.name }), h("div", { class: "ct-sub", text: p.what }), st);
        return { p, el, st };
      });
      const health = h("span", { class: "ct-pill ok" }, h("i", { class: "ct-dot" }), "reported health: healthy");
      const rows = producers.map((p) => {
        const f = h("span"); const d = h("span");
        const el = h("div", { class: "ct-ep-row" }, h("b", { text: p.k }), f, d);
        return { p, el, f, d };
      });
      const board = h("div", { class: "ct-card ct-ep-board" },
        h("div", { style: "display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px" },
          h("div", {}, h("div", { class: "ct-card-label", text: "Posture · payment-agent" }), h("div", { class: "ct-card-value", text: "as of 2026-08-15 12:00" })), health),
        rows.map((r) => r.el));
      const toast = h("div", { class: "ct-toast ok", hidden: true, text: "retry created: False · same observation, nothing stored twice" });
      stage.append(h("div", { class: "ct-ep-producers" }, cards.map((c) => c.el)), h("div", { style: "text-align:center;color:var(--ct-dim);font:14px var(--ct-mono);margin:8px 0 -4px" }, "↓ push-only ↓"), board, toast);
      return { cards, rows, board, health, toast, was: 0 };
    },
    render(x, i, prev, step) {
      const n = step.s.pushed;
      x.cards.forEach((c, j) => {
        const done = j < n;
        const isNew = done && j >= x.was && prev < i;
        c.el.className = "ct-tile" + (done ? "" : " is-dim") + (isNew ? " is-hit is-flash" : "") + (step.s.retry && j === 0 ? " is-hit is-flash" : "");
        setKids(c.st, done ? pill("pushed", "lime") : pill("not pushed"));
      });
      x.rows.forEach((r, j) => {
        const done = j < n;
        r.el.classList.toggle("is-new", done && j >= x.was && prev < i);
        setKids(r.f, done ? pill(r.p.fresh, r.p.fresh === "fresh" ? "ok" : "warn") : pill("missing", "bad"));
        r.d.textContent = done ? r.p.detail : "no evidence yet";
      });
      x.board.classList.toggle("is-hit", !!step.s.final);
      x.toast.hidden = !step.s.retry;
      x.was = n;
    },
  };

  const scenarios = { "fleet-change": fleetChange, "fleet-health": fleetHealth, "lens-incident": lensIncident, "evidence-posture": posture };
  const init = () => document.querySelectorAll("figure.ct-sim[data-ct-sim]").forEach((root) => {
    if (root.dataset.ctReady) return;
    const sc = scenarios[root.dataset.ctSim];
    if (!sc) return;
    root.dataset.ctReady = "1";
    mount(root, sc);
  });
  if (window.document$ && typeof window.document$.subscribe === "function") window.document$.subscribe(init);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
