/* GPHL125241O: site behaviour. Plain vanilla JS, no dependencies.
 *  1. atmosphere: stars, drifting ghosts, parallax moon, cursor trail
 *  2. typing role line, scroll reveal, active nav link
 *  3. charts rendered from data/modules.json, data/ctfs.json and data/contributions.json
 */
(() => {
  "use strict";

  document.documentElement.classList.add("js");
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;
  const rand = (a, b) => a + Math.random() * (b - a);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ------------------------------------------------------------------ atmosphere */
  function stars() {
    const box = $("#stars");
    if (!box) return;
    const frag = document.createDocumentFragment();
    for (let i = 0; i < 90; i++) {
      const s = document.createElement("i");
      const size = rand(1, 2.3);
      s.style.cssText = `left:${rand(0, 100)}%;top:${rand(0, 72)}%;width:${size}px;height:${size}px;--d:${rand(2.5, 7)}s;--delay:${rand(0, 5)}s;--hi:${rand(0.55, 0.95)};--lo:${rand(0.1, 0.35)}`;
      frag.appendChild(s);
    }
    box.appendChild(frag);
  }

  function ghosts() {
    const box = $("#ghosts");
    if (!box || reduce) return;
    const n = innerWidth < 700 ? 4 : 7;
    for (let i = 0; i < n; i++) {
      const size = rand(34, 108);
      const el = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      el.setAttribute("class", "ghost");
      el.setAttribute("viewBox", "0 0 56 72");
      el.innerHTML = '<use href="#gh"/>';
      el.style.cssText = `--s:${size}px;--x:${rand(2, 92)}%;--y:${rand(8, 78)}%;--op:${(innerWidth < 700 ? rand(0.04, 0.09) : rand(0.05, 0.17)).toFixed(2)};--bl:${(size < 55 ? rand(1, 2.5) : rand(0, 1)).toFixed(1)}px;--bob:${rand(4, 8).toFixed(1)}s;--roam:${rand(16, 34).toFixed(0)}s;--delay:${(-rand(0, 8)).toFixed(1)}s`;
      box.appendChild(el);
    }
  }

  // parallax (mouse + scroll) written to CSS variables, throttled with rAF
  function parallax() {
    if (reduce) return;
    const root = document.documentElement.style;
    let mx = 0, my = 0, ticking = false;
    const apply = () => {
      root.setProperty("--mx", mx.toFixed(3));
      root.setProperty("--my", my.toFixed(3));
      root.setProperty("--sy", String(Math.round(scrollY)));
      ticking = false;
    };
    const queue = () => { if (!ticking) { ticking = true; requestAnimationFrame(apply); } };
    addEventListener("scroll", queue, { passive: true });
    addEventListener("pointermove", (e) => { mx = e.clientX / innerWidth - 0.5; my = e.clientY / innerHeight - 0.5; queue(); }, { passive: true });
    apply();
  }

  // little ghosts that follow the cursor (fine pointers only)
  function cursorTrail() {
    if (reduce || !finePointer) return;
    let lastX = -999, lastY = -999, live = 0;
    addEventListener("pointermove", (e) => {
      if (live > 14 || Math.hypot(e.clientX - lastX, e.clientY - lastY) < 34) return;
      lastX = e.clientX; lastY = e.clientY;
      const t = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      t.setAttribute("class", "trail");
      t.setAttribute("viewBox", "0 0 56 72");
      t.setAttribute("aria-hidden", "true");
      t.innerHTML = '<use href="#gh"/>';
      t.style.setProperty("--tx", `${e.clientX - 9}px`);
      t.style.setProperty("--ty", `${e.clientY - 12}px`);
      document.body.appendChild(t);
      live++;
      t.addEventListener("animationend", () => { t.remove(); live--; }, { once: true });
    }, { passive: true });
  }

  /* ------------------------------------------------------------------ typing + reveal + nav */
  function typeRoles() {
    const el = $("#role");
    if (!el || reduce) return;
    const roles = ["Penetration Tester", "Red Team Operator", "Active Directory Hunter", "Exploit Whisperer", "Haunter of Unpatched Servers", "Ethical Poltergeist"];
    let i = 0, j = roles[0].length, erasing = true;
    const tick = () => {
      const word = roles[i];
      el.textContent = word.slice(0, j);
      if (!erasing && j === word.length) { erasing = true; return setTimeout(tick, 1600); }
      if (erasing && j === 0) { erasing = false; i = (i + 1) % roles.length; return setTimeout(tick, 320); }
      j += erasing ? -1 : 1;
      setTimeout(tick, erasing ? 32 : 68);
    };
    setTimeout(tick, 1800);
  }

  function reveal() {
    const items = $$(".reveal");
    if (reduce || !("IntersectionObserver" in window)) return items.forEach((n) => n.classList.add("in"));
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }), { threshold: 0.08, rootMargin: "0px 0px -6% 0px" });
    items.forEach((n) => io.observe(n));
  }

  function activeNav() {
    if (!("IntersectionObserver" in window)) return;
    const links = new Map($$('.nav a[href^="#"]').map((a) => [a.getAttribute("href").slice(1), a]));
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (!e.isIntersecting) return;
      links.forEach((a) => a.removeAttribute("aria-current"));
      const a = links.get(e.target.id);
      if (a) a.setAttribute("aria-current", "true");
    }), { rootMargin: "-45% 0px -50% 0px" });
    $$("main section[id]").forEach((s) => io.observe(s));
  }

  // links still holding a TODO_ placeholder are hidden instead of shipping dead links
  function hidePlaceholderLinks() {
    $$(".links li").forEach((li) => {
      const a = $("a", li);
      if (a && /TODO_/.test(a.getAttribute("href") || "")) li.hidden = true;
    });
  }

  /* ------------------------------------------------------------------ data helpers */
  const DAY = 86400000;
  const IST_OFFSET = 5.5 * 3600 * 1000; // matches the daily job, which runs on IST
  const istToday = () => { const d = new Date(Date.now() + IST_OFFSET); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()); };
  const parseDay = (s) => { const [y, m, d] = String(s).split("-").map(Number); return Date.UTC(y, m - 1, d); };
  const monthName = (t) => new Date(t).toLocaleString("en", { month: "short", timeZone: "UTC" });
  const fmtShort = (t, span) => (span > 120 ? `${monthName(t)} '${String(new Date(t).getUTCFullYear()).slice(2)}` : `${monthName(t)} ${new Date(t).getUTCDate()}`);
  const fmtLong = (t) => `${new Date(t).getUTCDate()} ${monthName(t)} ${new Date(t).getUTCFullYear()}`;

  async function loadJSON(path) {
    try {
      const r = await fetch(path, { cache: "no-cache" });
      if (!r.ok) return null;
      return await r.json();
    } catch { return null; }
  }
  const entriesOf = (doc) => (doc ? (Array.isArray(doc) ? doc : doc.entries || []) : [])
    .map((e) => ({ ...e, t: parseDay(e.date) })).filter((e) => !Number.isNaN(e.t)).sort((a, b) => a.t - b.t);

  function streaks(days, end) {
    let cur = 0, d = days.has(end) ? end : end - DAY;
    while (days.has(d)) { cur++; d -= DAY; }
    let longest = 0, run = 0, prev = null;
    [...days].sort((a, b) => a - b).forEach((t) => { run = prev !== null && t - prev === DAY ? run + 1 : 1; longest = Math.max(longest, run); prev = t; });
    return { cur, longest };
  }
  const niceStep = (raw) => { raw = Math.max(raw, 1); const p = 10 ** Math.floor(Math.log10(raw)); for (const m of [1, 2, 5, 10]) if (raw <= m * p) return m * p; return 10 * p; };
  const count = (arr, f) => arr.reduce((m, x) => { const k = f(x); m.set(k, (m.get(k) || 0) + 1); return m; }, new Map());
  const topRows = (map, limit) => {
    let rows = [...map].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));
    if (rows.length > limit) rows = [...rows.slice(0, limit - 1), ["Others", rows.slice(limit - 1).reduce((s, r) => s + r[1], 0)]];
    return rows;
  };
  const last30 = (entries, end) => entries.filter((e) => e.t >= end - 29 * DAY && e.t <= end).length;

  /* ------------------------------------------------------------------ chart builders */
  const tiles = (items) => `<div class="tiles">${items.map(([v, l]) => `<div class="tile"><b>${esc(v)}</b><span>${esc(l)}</span></div>`).join("")}</div>`;
  const bars = (rows, cls = "") => rows.length
    ? `<ul class="bars ${cls}">${(() => { const mx = Math.max(...rows.map((r) => r[1])) || 1; return rows.map(([n, v]) => `<li><span class="lbl" title="${esc(n)}">${esc(n)}</span><span class="track"><i style="width:${Math.max(6, (v / mx) * 100).toFixed(1)}%"></i></span><b>${v}</b></li>`).join(""); })()}</ul>`
    : '<p class="muted">Nothing here yet.</p>';

  function cumulativeSVG(entries, end, label) {
    const W = 560, H = 242, L = 36, R = 16, T = 26, B = 28, w = W - L - R, h = H - T - B;
    if (!entries.length) return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}: no entries yet"><text x="${W / 2}" y="${H / 2}" fill="#9fb0ab" text-anchor="middle" font-size="13">No souls collected yet.</text></svg>`;
    const start = Math.min(entries[0].t - DAY, end - 13 * DAY);
    const span = Math.max((end - start) / DAY, 1);
    const X = (t) => L + ((t - start) / DAY / span) * w;
    const total = entries.length, step = niceStep(total / 4), ymax = Math.max(step * Math.ceil(total / step), step * 2);
    const Y = (v) => T + h - (v / ymax) * h;
    let g = "";
    for (let v = 0; v <= ymax; v += step) g += `<line x1="${L}" y1="${Y(v)}" x2="${L + w}" y2="${Y(v)}" stroke="#1a1f26" ${v ? 'stroke-dasharray="3 4"' : ""}/><text x="${L - 8}" y="${Y(v) + 4}" fill="#9fb0ab" font-size="10" text-anchor="end">${v}</text>`;
    for (let i = 0; i <= 5; i++) {
      const t = start + Math.round((i * span) / 5) * DAY;
      g += `<text x="${X(t)}" y="${H - 8}" fill="#9fb0ab" font-size="10" text-anchor="${i === 0 ? "start" : i === 5 ? "end" : "middle"}">${fmtShort(t, span)}</text>`;
    }
    const byDay = count(entries, (e) => e.t);
    let run = 0, prevY = Y(0), d = `M${X(start).toFixed(1)},${prevY.toFixed(1)}`, dots = "", lx = 0, ly = 0;
    [...byDay.keys()].sort((a, b) => a - b).forEach((t) => {
      const x = X(t);
      d += ` L${x.toFixed(1)},${prevY.toFixed(1)}`;
      run += byDay.get(t); prevY = Y(run);
      d += ` L${x.toFixed(1)},${prevY.toFixed(1)}`;
      dots += `<circle cx="${x.toFixed(1)}" cy="${prevY.toFixed(1)}" r="2.8" fill="#0b0d10" stroke="#39ff9c" stroke-width="1.5"/>`;
      lx = x; ly = prevY;
    });
    d += ` L${X(end).toFixed(1)},${prevY.toFixed(1)}`;
    const area = `${d} L${X(end).toFixed(1)},${Y(0)} L${X(start).toFixed(1)},${Y(0)} Z`;
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}: ${total} in total, cumulative over time">${g}
      <path d="${area}" fill="url(#areaG)"/><path d="${d}" fill="none" stroke="#39ff9c" stroke-width="2.2" stroke-linejoin="round" filter="url(#glow)"/>${dots}
      <circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="4" fill="#39ff9c"/>
      ${reduce ? "" : `<circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="4" fill="none" stroke="#39ff9c"><animate attributeName="r" values="4;11;4" dur="2.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.8;0;0.8" dur="2.6s" repeatCount="indefinite"/></circle>`}
      <text x="${lx.toFixed(1)}" y="${(ly - 11).toFixed(1)}" fill="#e6f1ef" font-size="12" font-weight="700" text-anchor="middle">${total}</text></svg>`;
  }

  const recentList = (entries, extra) => entries.length
    ? `<details class="recent"><summary>Recent entries</summary><ol>${entries.slice(-8).reverse().map((e) => `<li>${fmtLong(e.t)}: ${esc(e.name)} <span class="muted">(${esc(e.platform || "")}${extra(e)})</span></li>`).join("")}</ol></details>`
    : "";
  const meta = (id, end, sample) => { const el = $(id); if (el) el.innerHTML = `${sample ? '<span class="badge-sample">SAMPLE DATA</span>' : ""}as of ${new Date(end).toISOString().slice(0, 10)} IST`; };

  function renderModules(entries, end) {
    const el = $("#modules-body");
    if (!el) return;
    const days = new Set(entries.map((e) => e.t)), { cur } = streaks(days, end), plats = count(entries, (e) => e.platform || "Other");
    el.innerHTML = tiles([[entries.length, "Modules done"], [last30(entries, end), "Last 30 days"], [cur, "Day streak"], [plats.size, "Platforms"]])
      + `<p class="chart-label">Cumulative total over time</p><div class="chart">${cumulativeSVG(entries, end, "Modules completed")}</div>`
      + `<p class="chart-label">By platform</p>${bars(topRows(plats, 6))}` + recentList(entries, (e) => (e.category ? `, ${esc(e.category)}` : ""));
    meta("#modules-meta", end, entries.some((e) => e.sample));
  }

  const DIFF = { easy: "#39ff9c", medium: "#8b5cf6", hard: "#b0212d", insane: "#e6f1ef" };
  function renderCtfs(entries, end) {
    const el = $("#ctfs-body");
    if (!el) return;
    const days = new Set(entries.map((e) => e.t)), { cur } = streaks(days, end);
    const points = entries.reduce((s, e) => s + (Number(e.points) || 0), 0);
    const diff = count(entries, (e) => String(e.difficulty || "other").toLowerCase());
    const order = ["easy", "medium", "hard", "insane"].filter((d) => diff.has(d)).concat([...diff.keys()].filter((d) => !DIFF[d]).sort());
    const stackbar = entries.length ? `<div class="stackbar" role="img" aria-label="Difficulty split">${order.map((d) => `<i style="flex:${diff.get(d)};background:${DIFF[d] || "#9fb0ab"}"></i>`).join("")}</div><ul class="legend">${order.map((d) => `<li style="--c:${DIFF[d] || "#9fb0ab"}">${esc(d)} ${diff.get(d)}</li>`).join("")}</ul>` : '<p class="muted">Nothing here yet.</p>';
    el.innerHTML = tiles([[entries.length, "CTFs banished"], [last30(entries, end), "Last 30 days"], [cur, "Day streak"], points ? [points.toLocaleString("en"), "Points"] : [count(entries, (e) => e.platform).size, "Platforms"]])
      + `<p class="chart-label">Cumulative total over time</p><div class="chart">${cumulativeSVG(entries, end, "CTFs completed")}</div>`
      + `<div class="split"><div><p class="chart-label">By difficulty</p>${stackbar}</div><div><p class="chart-label">By category</p>${bars(topRows(count(entries, (e) => e.category || "General"), 5), "is-purple")}</div></div>`
      + recentList(entries, (e) => (e.difficulty ? `, ${esc(e.difficulty)}` : ""));
    meta("#ctfs-meta", end, entries.some((e) => e.sample));
  }

  function renderContributions(doc) {
    const el = $("#contrib-body");
    if (!el) return;
    if (!doc || !Array.isArray(doc.days) || !doc.days.length) {
      el.innerHTML = '<p class="empty">The graveyard is quiet&hellip; the first summoning runs with the next nightly update.</p>';
      return;
    }
    const map = new Map(doc.days.map(([d, c]) => [parseDay(d), c]));
    const end = Math.max(...map.keys());
    const dow = (t) => (new Date(t).getUTCDay()); // 0 = Sunday
    const origin = end - dow(end) * DAY - 52 * 7 * DAY;
    const mx = Math.max(...map.values(), 0);
    const level = (c) => (c <= 0 || mx <= 0 ? 0 : c / mx <= 0.25 ? 1 : c / mx <= 0.5 ? 2 : c / mx <= 0.75 ? 3 : 4);
    const FILL = ["#12161b", "#0f3b2a", "#12704a", "#1fc47a", "#39ff9c"];
    const PITCH = 14, GX = 34, GY = 24, CW = 11, CH = 12, r = CW / 2;
    const groups = [[], [], [], [], []];
    let months = "", lastMonth = -1;
    [...map.keys()].sort((a, b) => a - b).forEach((t) => {
      if (t < origin || t > end) return;
      const col = Math.floor((t - origin) / DAY / 7), row = dow(t), x = GX + col * PITCH, y = GY + row * PITCH, c = map.get(t), lv = level(c);
      const path = `M${x},${y + CH} V${y + r} A${r},${r} 0 0 1 ${x + CW},${y + r} V${y + CH} Z`;
      groups[lv].push(`<path d="${path}" fill="${FILL[lv]}"${lv === 0 ? ' stroke="#1c222a"' : ""}${t === end ? ' stroke="#e6f1ef" stroke-width="1.2"' : ""}><title>${new Date(t).toISOString().slice(0, 10)}: ${c} contribution${c === 1 ? "" : "s"}</title></path>`);
      const m = new Date(t).getUTCMonth();
      if (row === 0 && m !== lastMonth) { if (lastMonth !== -1 || col === 0) months += `<text x="${x}" y="${GY - 8}" fill="#9fb0ab" font-size="10">${monthName(t)}</text>`; lastMonth = m; }
    });
    const W = GX + 53 * PITCH + 4, H = GY + 7 * PITCH + 4;
    const svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Contribution graph: ${doc.total} contributions in the last year"><defs><filter id="g3" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="1.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>${months}
      ${["Mon", "Wed", "Fri"].map((n, i) => `<text x="${GX - 6}" y="${GY + (1 + i * 2) * PITCH + 10}" fill="#9fb0ab" font-size="9.5" text-anchor="end">${n}</text>`).join("")}
      <g>${[...groups[0], ...groups[1], ...groups[2]].join("")}</g><g filter="url(#g3)">${[...groups[3], ...groups[4]].join("")}</g></svg>`;
    const busiest = doc.busiest_day || ["", 0];
    el.innerHTML = tiles([[doc.total.toLocaleString("en"), "Contributions"], [`${doc.current_streak}d`, "Current streak"], [`${doc.longest_streak}d`, "Longest streak"], [busiest[1] ? `${busiest[1]}` : "0", "Busiest day"]])
      + `<div class="contrib">${svg}</div>`;
    const m = $("#contrib-meta");
    if (m) m.textContent = `updated ${doc.generated} IST`;
  }

  async function charts() {
    const [mods, ctfs, contrib] = await Promise.all([loadJSON("data/modules.json"), loadJSON("data/ctfs.json"), loadJSON("data/contributions.json")]);
    const end = istToday();
    renderContributions(contrib);
    renderModules(entriesOf(mods), end);
    renderCtfs(entriesOf(ctfs), end);
  }

  /* ------------------------------------------------------------------ go */
  stars(); ghosts(); parallax(); cursorTrail();
  typeRoles(); reveal(); activeNav(); hidePlaceholderLinks();
  charts();
})();
