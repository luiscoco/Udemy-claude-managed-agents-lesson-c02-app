const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  // Render Claude's Markdown, but never raw HTML from the model.
  marked.use({ renderer: { html: ({ text }) => esc(text) } });

  const cols = { manual: $("#col-manual"), managed: $("#col-managed") };
  const promptEl = $("#prompt");
  try { promptEl.value = sessionStorage.getItem('c02-prompt') || ''; } catch {}
  promptEl.addEventListener('input', () => { try { sessionStorage.setItem('c02-prompt', promptEl.value); } catch {} });
  window.addEventListener('pagehide', () => { try { sessionStorage.setItem('c02-prompt', promptEl.value); } catch {} });
  const buttons = ["#run-both", "#run-manual", "#run-managed", "#clear"].map((s) => $(s));

  function setStatus(flow, kind, text) {
    const el = $(".status", cols[flow]);
    el.className = "status " + kind;
    el.textContent = text;
  }

  function resetColumn(flow) {
    const col = cols[flow];
    $(".timeline", col).innerHTML = "";
    $(".empty", col).hidden = false;
    $(".result", col).hidden = true;
    $(".result", col).innerHTML = "";
    const s = $(".session", col); if (s) s.textContent = "";
    setStatus(flow, "", "Idle");
  }

  function addItem(flow, cls, who, html) {
    const tl = $(".timeline", cols[flow]);
    const li = document.createElement("li");
    li.className = "item " + cls;
    li.innerHTML = `<span class="who">${esc(who)}</span>${html}`;
    tl.insertBefore(li, $(".pending", tl));
    return li;
  }

  function setPending(flow, on) {
    const tl = $(".timeline", cols[flow]);
    $(".pending", tl)?.remove();
    if (on) {
      const li = document.createElement("li");
      li.className = "item step pending";
      li.innerHTML = `<span class="who"></span><span class="line">Waiting for Claude…</span>`;
      tl.append(li);
    }
  }

  function renderStock(stock) {
    const rows = stock.map((s) => {
      const changed = s.available !== s.initial;
      return `<tr><td><code>${esc(s.sku)}</code></td><td>${esc(s.name)}</td><td class="n">${s.initial}</td>` +
        `<td class="n ${changed ? "changed" : ""}">${changed ? "−" + (s.initial - s.available) : "0"}</td><td class="n">${s.available}</td></tr>`;
    }).join("");
    return `<div class="stock"><span class="eyebrow">Warehouse after this run</span><table>
      <thead><tr><th>SKU</th><th>Product</th><th class="n">Before</th><th class="n">Reserved</th><th class="n">After</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
  }

  function render(flow, e) {
    const col = cols[flow];
    switch (e.type) {
      case "start":
        $("#model").textContent = e.model;
        if (e.sessionId) $(".session", col).textContent = " · " + e.sessionId;
        addItem(flow, "", "You", `<div class="bubble user">${esc(e.prompt)}</div>`);
        break;
      case "step":
        addItem(flow, "step", "", `<span class="line">${esc(e.text)}</span>`);
        break;
      case "tool": {
        const { sku, quantity } = e.input || {};
        let r; try { r = JSON.parse(e.result); } catch { r = { ok: false, error: e.result }; }
        const outcome = r.ok
          ? `<span class="ok">✓ ${esc(r.reservationId)} · ${esc(r.remaining)} left</span>`
          : `<span class="err">✗ ${esc(r.error)}</span>`;
        addItem(flow, "", "Your host", `<div class="bubble host">
          <span class="dim">on ${esc(e.trigger)}</span>
          <span><span class="fn">reserveStock</span>(${esc(JSON.stringify(sku))}, ${esc(quantity)})</span>
          ${outcome}</div>`);
        break;
      }
      case "assistant":
        addItem(flow, "", "Claude", `<div class="bubble claude">${marked.parse(e.text)}</div>`);
        break;
      case "done": {
        setPending(flow, false);
        setStatus(flow, "done", `Done · ${(e.ms / 1000).toFixed(1)} s`);
        const stats = e.stats.map((s) => {
          const small = typeof s.value === "string" && s.value.length > 12;
          return `<div class="stat"><b class="${small ? "small" : ""}">${esc(s.value)}</b><span>${esc(s.label)}</span></div>`;
        }).join("");
        const result = $(".result", col);
        result.innerHTML = `<div class="stats">${stats}</div>${renderStock(e.stock)}`;
        result.hidden = false;
        return;
      }
      case "error":
        setPending(flow, false);
        setStatus(flow, "failed", "Failed");
        addItem(flow, "", "Error", `<div class="error-box">${esc(e.message)}</div>`);
        return;
    }
    setPending(flow, true);
  }

  function run(flow) {
    resetColumn(flow);
    $(".empty", cols[flow]).hidden = true;
    setStatus(flow, "running", "Running");
    setPending(flow, true);
    const qs = new URLSearchParams({ flow, prompt: promptEl.value });
    return new Promise((resolve) => {
      const es = new EventSource("/api/run?" + qs);
      es.onmessage = (m) => {
        const e = JSON.parse(m.data);
        render(flow, e);
        if (e.type === "done" || e.type === "error") { es.close(); resolve(); }
      };
      // Close on any drop so EventSource does not reconnect and start a second run.
      es.onerror = () => { es.close(); render(flow, { type: "error", message: "Lost the connection to the local server. Is `npm run dev` still running?" }); resolve(); };
    });
  }

  async function guarded(fn) {
    buttons.forEach((b) => (b.disabled = true));
    try { await fn(); } finally { buttons.forEach((b) => (b.disabled = false)); }
  }

  $("#run-manual").onclick = () => guarded(() => run("manual"));
  $("#run-managed").onclick = () => guarded(() => run("managed"));
  $("#run-both").onclick = () => guarded(async () => { resetColumn("managed"); await run("manual"); await run("managed"); });
  $("#clear").onclick = () => { resetColumn("manual"); resetColumn("managed"); };
  document.querySelectorAll("[data-sample]").forEach((b) => (b.onclick = () => { promptEl.value = b.dataset.sample; promptEl.focus(); }));
  promptEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && !$("#run-both").disabled) $("#run-both").click();
  });

  fetch("/api/config").then((r) => r.json()).then((c) => {
    $("#model").textContent = c.model;
    if (!promptEl.value) promptEl.value = c.defaultPrompt;
    $("#managed-banner").hidden = c.managedReady;
  }).catch(() => {});
