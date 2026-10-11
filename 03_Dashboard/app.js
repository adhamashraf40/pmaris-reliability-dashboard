/* ===========================================================================
   Live Decision Dashboard - shared runtime (PMARIS asset reliability).

   Every page loads this file, then calls LDD.start(render). The page supplies
   only its own render(data) function; polling, the live indicator, tooltips,
   theming, number formatting, the cross-filter engine and the chart
   primitives all live here so no page reimplements them.

   Dimension-keyed per Playbook s14.6: filters are a map keyed by dimension
   name and read d.raw.dimensions, so nothing here names a column.

   No framework, no CDN, no build step.
   =========================================================================== */

const LDD = (() => {
  // The full feed is ~300 KB, so pages poll a tiny stamp file every 250 ms and
  // fetch live_data.json only when the stamp changes (and at least every 5 s).
  // A 1 s poll of the full feed measured 972 ms mean / 1,262 ms max save-to-screen,
  // which misses the D3 target; this split keeps the same contract and fits it.
  const POLL_MS = 250, FULL_EVERY_MS = 5000;
  // On GitHub Pages there is no watcher.py: the page shows the committed
  // live_data.json, so the badge says "Snapshot" rather than claiming "Live".
  const SNAPSHOT = /\.github\.io$/.test(location.hostname);
  let lastFull = 0;

  /* ------------------------------------------------------------ formatting */
  const nf = new Intl.NumberFormat('en-US');
  const fmt = {
    int: n => nf.format(Math.round(n)),
    dec: (n, d = 1) => Number(n).toFixed(d),
    egp: n => 'EGP ' + nf.format(Math.round(n)),
    compact: n => {
      const a = Math.abs(n);
      if (a >= 1e9) return (n / 1e9).toFixed(2) + 'B';
      if (a >= 1e6) return (n / 1e6).toFixed(a >= 1e8 ? 0 : 2) + 'M';
      if (a >= 1e3) return Math.round(n / 1e3) + 'k';
      return String(Math.round(n));
    },
    egpc: n => 'EGP ' + fmt.compact(n),
    hrs: n => Number(n).toFixed(1) + ' h',
    pct: (n, d = 1) => Number(n).toFixed(d) + '%',
    month: s => {
      const [y, m] = s.split('-');
      return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m - 1] + ' ' + y.slice(2);
    },
    clock: iso => { try { return new Date(iso).toLocaleTimeString(); } catch (e) { return iso; } },
    label: s => s.replace(/_/g, ' ')
  };

  /* --------------------------------------------------------------- colours */
  // Categorical identity is reserved for maintenance strategy: four fixed slots,
  // assigned by entity, never by rank, never recycled when a filter hides one.
  const STRATEGY_ORDER = ['Reactive', 'Preventive', 'Condition-Based', 'Predictive'];
  const STRATEGY_SLOT = { 'Reactive': 2, 'Preventive': 1, 'Condition-Based': 4, 'Predictive': 3 };
  const strategyColor = name => `var(--series-${STRATEGY_SLOT[name] || 1})`;
  // Priority and spares are states, so they wear the reserved status palette.
  const PRIORITY_COLOR = { 'P1 - Immediate': 'var(--critical)', 'P2 - High': 'var(--serious)',
                           'P3 - Planned': 'var(--warning)', 'P4 - Monitor': 'var(--neutral)' };
  const seqStep = t => {
    const steps = ['var(--seq-100)', 'var(--seq-250)', 'var(--seq-400)',
                   'var(--seq-500)', 'var(--seq-600)', 'var(--seq-700)'];
    return steps[Math.min(steps.length - 1, Math.max(0, Math.round(t * (steps.length - 1))))];
  };
  // Magnitude: colour by value share of the max, one hue light to dark
  const seqFor = (v, max) => seqStep(max ? 0.15 + 0.85 * (v / max) : 0.5);

  /* --------------------------------------------------------------- tooltip */
  let tipEl = null;
  function tip() {
    if (!tipEl) {
      tipEl = document.createElement('div');
      tipEl.className = 'viz-tooltip';
      tipEl.setAttribute('role', 'status');
      document.body.appendChild(tipEl);
    }
    return tipEl;
  }
  function showTip(evt, html) {
    const t = tip();
    t.innerHTML = html;
    t.classList.add('show');
    const pad = 14, r = t.getBoundingClientRect();
    let x = evt.clientX + pad, y = evt.clientY + pad;
    if (x + r.width > window.innerWidth - 8) x = evt.clientX - r.width - pad;
    if (y + r.height > window.innerHeight - 8) y = evt.clientY - r.height - pad;
    t.style.left = Math.max(8, x) + 'px';
    t.style.top = Math.max(8, y) + 'px';
  }
  function hideTip() { if (tipEl) tipEl.classList.remove('show'); }
  function hoverable(el, htmlFn) {
    el.addEventListener('mousemove', e => showTip(e, htmlFn()));
    el.addEventListener('mouseleave', hideTip);
    el.addEventListener('focus', () => {
      const r = el.getBoundingClientRect();
      showTip({ clientX: r.left + r.width / 2, clientY: r.top }, htmlFn());
    });
    el.addEventListener('blur', hideTip);
  }
  const tipHtml = (title, rows, note) => '<div class="t-title">' + title + '</div>'
    + rows.map(([k, v]) => '<div class="t-row"><span>' + k + '</span><span>' + v + '</span></div>').join('')
    + (note ? '<div class="t-note">' + note + '</div>' : '');

  /* ----------------------------------------------------------------- theme */
  function initTheme() {
    const KEY = 'ldd-theme';
    let saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
    if (saved) document.documentElement.setAttribute('data-theme', saved);
    const btn = document.querySelector('.theme-btn');
    if (!btn) return;
    const isDark = () => {
      const cur = document.documentElement.getAttribute('data-theme');
      return cur === 'dark' || (!cur && window.matchMedia('(prefers-color-scheme: dark)').matches);
    };
    const paint = () => {
      btn.textContent = isDark() ? 'Light' : 'Dark';
      btn.setAttribute('aria-label', isDark() ? 'Switch to light theme' : 'Switch to dark theme');
    };
    btn.addEventListener('click', () => {
      const next = isDark() ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
      paint();
      if (lastData && renderFn) renderFn(lastData);
    });
    paint();
  }

  /* --------------------------------------------------- live text bindings */
  // Prose that quotes a live figure carries one of these classes, so a headline
  // can never contradict the tiles beneath it after the source changes.
  function bindLiveText(d) {
    const k = d.kpis;
    const set = (sel, val) => document.querySelectorAll(sel).forEach(n => { n.textContent = val; });
    set('.js-rows', fmt.int(d.row_count));
    set('.js-loss-total', fmt.egpc(k.loss_total));
    set('.js-loss-mean', fmt.egpc(k.loss_mean));
    set('.js-downtime-mean', fmt.hrs(k.downtime_mean));
    set('.js-hr-n', fmt.int(k.high_risk_n));
    set('.js-hr-pct', fmt.pct(k.high_risk_pct));
    set('.js-hr-loss-share', fmt.pct(k.high_risk_loss_share));
    set('.js-gap', fmt.int(k.escalation_gap));
    set('.js-gap-exposure', fmt.egpc(k.escalation_gap_exposure));
    set('.js-escalated', fmt.int(k.escalated_n));
    set('.js-rule-adds', fmt.int(k.rule_adds));
    set('.js-top10', fmt.pct(k.top10_loss_share));
    set('.js-months', String(d.trend.length));
    set('.js-dates', fmt.month(d.date_min.slice(0, 7)) + ' to ' + fmt.month(d.date_max.slice(0, 7)));
    // ratio sentences computed live from the feed
    const by = (dim, name) => (d.by_dimension[dim] || []).find(x => x.name === name);
    const ratio = (a, b, key) => (a && b && b[key]) ? (a[key] / b[key]).toFixed(1) + 'x' : 'n/a';
    set('.js-reactive-vs-predictive', ratio(by('Maintenance_Strategy', 'Reactive'), by('Maintenance_Strategy', 'Predictive'), 'downtime_mean'));
    set('.js-shortage-vs-available', ratio(by('Spare_Parts_Status', 'Shortage'), by('Spare_Parts_Status', 'Available'), 'downtime_mean'));
    set('.js-basic-vs-expert', ratio(by('Technician_Skill_Level', 'Basic'), by('Technician_Skill_Level', 'Expert'), 'downtime_mean'));
    set('.js-cost-mean', fmt.egpc(k.cost_mean));
    set('.js-cost-total', fmt.egpc(k.cost_total));
    set('.js-loss-to-cost', k.loss_to_cost.toFixed(1) + 'x');
    set('.js-reactive-cost', ratio(by('Maintenance_Strategy', 'Reactive'), by('Maintenance_Strategy', 'Predictive'), 'cost_mean'));
    set('.js-shortage-spare', ratio(by('Spare_Parts_Status', 'Shortage'), by('Spare_Parts_Status', 'Available'), 'spare_mean'));
    set('.js-critical-vs-low', ratio(by('Criticality_Class', 'Critical'), by('Criticality_Class', 'Low'), 'loss_mean'));
    staleCheck(d);
  }

  // Study constants were measured on one file. Warn when the live feed differs.
  function staleCheck(d) {
    const st = d.study;
    document.querySelectorAll('.js-stale').forEach(n => {
      const stale = !st || st.row_count !== d.row_count;
      n.hidden = !stale;
      if (stale) n.querySelector('.js-stale-text').textContent = st
        ? `Study constants (tests, intervals) were measured on ${fmt.int(st.row_count)} rows; the live file now has ${fmt.int(d.row_count)}. Live tiles are current; re-run analyze_pmaris.py to refresh the tests.`
        : 'Study constants not loaded. Run 02_Analysis/analyze_pmaris.py, then restart watcher.py.';
    });
  }

  /* -------------------------------------------------------------- polling */
  let lastData = null, renderFn = null, lastStamp = null, failures = 0;
  function setLive(state, text) {
    const el = document.querySelector('.live');
    if (!el) return;
    el.classList.toggle('is-live', state === 'live');
    el.classList.toggle('is-stale', state === 'stale');
    const label = el.querySelector('.live-text');
    if (label) label.textContent = text;
  }
  async function poll() {
    try {
      if (lastStamp && Date.now() - lastFull < FULL_EVERY_MS) {
        try {
          const sr = await fetch('live_stamp.json?t=' + Date.now(), { cache: 'no-store' });
          if (sr.ok) {
            const st = await sr.json();
            failures = 0;
            if (st.last_updated === lastStamp) {
              setLive('live', SNAPSHOT
                ? 'Snapshot · data as of ' + new Date(st.last_updated).toLocaleDateString() + ' · ' + fmt.int(st.row_count) + ' rows'
                : 'Live · ' + fmt.clock(st.last_updated) + ' · ' + fmt.int(st.row_count) + ' rows');
              return;
            }
          }
        } catch (e) { /* no stamp yet: fall through to the full feed */ }
      }
      lastFull = Date.now();
      const res = await fetch('live_data.json?t=' + Date.now(), { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      failures = 0;
      if (data.last_updated !== lastStamp) {
        lastStamp = data.last_updated;
        lastData = data;
        window.__lddRenderedAt = Date.now();   // used by the D3 latency check
        bindLiveText(data);
        if (renderFn) renderFn(data);
      }
      setLive('live', SNAPSHOT
        ? 'Snapshot · data as of ' + new Date(data.last_updated).toLocaleDateString() + ' · ' + fmt.int(data.row_count) + ' rows'
        : 'Live · ' + fmt.clock(data.last_updated) + ' · ' + fmt.int(data.row_count) + ' rows');
    } catch (e) {
      failures++;
      if (failures > 2) setLive('stale', 'Not connected — is watcher.py running?');
    }
  }
  function start(render) {
    renderFn = render;
    initTheme();
    markNav();
    poll();
    setInterval(poll, POLL_MS);
  }
  function markNav() {
    const here = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('nav.pages a').forEach(a => {
      if (a.getAttribute('href') === here) a.setAttribute('aria-current', 'page');
    });
  }

  /* ------------------------------------------------------- render helpers */
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html !== undefined) n.innerHTML = html;
    return n;
  };
  const mount = id => document.getElementById(id);

  /**
   * Horizontal bar list, direct value label on every row (the contrast relief).
   * rows: [{label, value, valueText, color, tip, onClick}]
   */
  function barList(m, rows, opts = {}) {
    m.innerHTML = '';
    if (!rows.length) { m.appendChild(el('div', 'empty-state', 'No rows match the current filters.')); return; }
    const max = Math.max(...rows.map(r => r.value), opts.max || 0, 1e-9);
    const box = el('div', 'bars');
    rows.forEach(r => {
      const row = el('div', 'bar-row' + (r.selected ? ' is-selected' : ''));
      if (opts.wide) row.classList.add('is-wide');
      row.appendChild(el('div', 'name', r.label));
      const track = el('div', 'bar-track');
      const fill = el('div', 'bar-fill');
      fill.style.width = (Math.max(0, r.value) / max * 100).toFixed(2) + '%';
      fill.style.background = r.color || seqFor(r.value, max);
      track.appendChild(fill);
      track.tabIndex = 0;
      track.setAttribute('role', 'img');
      track.setAttribute('aria-label', `${r.label}: ${r.valueText || r.value}`);
      hoverable(track, () => r.tip || tipHtml(r.label, [['Value', r.valueText || r.value]]));
      if (r.onClick) { track.style.cursor = 'pointer'; track.addEventListener('click', r.onClick); }
      row.appendChild(track);
      row.appendChild(el('div', 'val', r.valueText || String(r.value)));
      box.appendChild(row);
    });
    m.appendChild(box);
  }

  function dataTable(m, head, rows) {
    const t = el('table', 'data');
    const thead = el('thead'), hr = el('tr');
    head.forEach(h => hr.appendChild(el('th', h.num ? 'num' : '', h.label)));
    thead.appendChild(hr); t.appendChild(thead);
    const tb = el('tbody');
    rows.forEach(r => {
      const tr = el('tr');
      r.forEach((c, i) => tr.appendChild(el('td', head[i].num ? 'num' : '', c)));
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    m.innerHTML = '';
    const sc = el('div', 'panel-scroll');
    sc.appendChild(t);
    m.appendChild(sc);
  }

  /* ======================================================================
     CROSS-FILTER ENGINE (dimension-keyed)
     raw.rows: [monthIdx, dim0Idx, dim1Idx, ..., downtime, loss, fp, health, exposure, priorityIdx]
     ====================================================================== */
  function newFilters(raw) {
    const f = { month: new Set() };
    raw.dimensions.forEach(d => { f[d] = new Set(); });
    return f;
  }
  function measureIndex(raw) {
    const base = 1 + raw.dimensions.length;
    return { downtime: base, loss: base + 1, fp: base + 2, health: base + 3, exposure: base + 4, priority: base + 5 };
  }
  function filterRows(raw, f, except) {
    if (!raw || !raw.rows) return [];
    const dims = raw.dimensions;
    return raw.rows.filter(r => {
      if (except !== 'month' && f.month.size && !f.month.has(raw.months[r[0]])) return false;
      for (let i = 0; i < dims.length; i++) {
        const d = dims[i];
        if (d === except) continue;
        if (f[d] && f[d].size && !f[d].has(raw.lookups[d][r[1 + i]])) return false;
      }
      return true;
    });
  }
  function anyFilter(f) { return Object.values(f).some(s => s.size); }
  function summarize(raw, rows, threshold) {
    const M = measureIndex(raw);
    const n = rows.length;
    let dt = 0, loss = 0, hr = 0, hrLoss = 0, gap = 0, health = 0, exp = 0;
    rows.forEach(r => {
      dt += r[M.downtime]; loss += r[M.loss]; health += r[M.health]; exp += r[M.exposure];
      if (r[M.fp] >= threshold) { hr++; hrLoss += r[M.loss]; if (r[M.priority] > 1) gap++; }
    });
    return { n, downtime_mean: n ? dt / n : 0, loss_mean: n ? loss / n : 0, loss_total: loss,
             high_risk_n: hr, high_risk_pct: n ? 100 * hr / n : 0,
             high_risk_loss_share: loss ? 100 * hrLoss / loss : 0, gap, health_mean: n ? health / n : 0,
             exposure_total: exp };
  }
  /** Group filtered rows by one dimension -> [{name, n, downtime_mean, loss_mean, loss_total, high_risk_pct}] */
  function groupDim(raw, rows, dim, threshold) {
    const M = measureIndex(raw);
    const i = raw.dimensions.indexOf(dim);
    const names = raw.lookups[dim];
    const acc = names.map(name => ({ name, n: 0, dt: 0, loss: 0, hr: 0 }));
    rows.forEach(r => {
      const a = acc[r[1 + i]];
      a.n++; a.dt += r[M.downtime]; a.loss += r[M.loss]; if (r[M.fp] >= threshold) a.hr++;
    });
    return acc.map(a => ({ name: a.name, n: a.n, downtime_mean: a.n ? a.dt / a.n : 0,
                           loss_mean: a.n ? a.loss / a.n : 0, loss_total: a.loss,
                           high_risk_pct: a.n ? 100 * a.hr / a.n : 0 }));
  }
  function groupMonth(raw, rows, threshold) {
    const M = measureIndex(raw);
    const acc = raw.months.map(m => ({ name: m, n: 0, dt: 0, loss: 0, hr: 0 }));
    rows.forEach(r => { const a = acc[r[0]]; a.n++; a.dt += r[M.downtime]; a.loss += r[M.loss]; if (r[M.fp] >= threshold) a.hr++; });
    return acc.map(a => ({ name: a.name, n: a.n, downtime_mean: a.n ? a.dt / a.n : 0,
                           loss_mean: a.n ? a.loss / a.n : 0, loss_total: a.loss,
                           high_risk_pct: a.n ? 100 * a.hr / a.n : 0 }));
  }

  /* ======================================================================
     SLICERS
     ====================================================================== */
  function slicer(m, opts) {
    m.innerHTML = '';
    const wrap = el('div', 'slicer');
    const head = el('div', 'slicer-head');
    head.appendChild(el('span', 'slicer-label', opts.label));
    const clear = el('button', 'slicer-clear', 'Clear');
    clear.type = 'button';
    clear.hidden = opts.selected.size === 0;
    clear.addEventListener('click', () => { opts.selected.clear(); opts.onChange(); });
    head.appendChild(clear);
    wrap.appendChild(head);
    const box = el('div', 'slicer-items');
    opts.values.forEach(v => {
      const on = opts.selected.has(v);
      const b = el('button', 'slicer-item' + (on ? ' is-on' : ''));
      b.type = 'button';
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      if (opts.colorFn) { const sw = el('span', 'swatch'); sw.style.background = opts.colorFn(v); b.appendChild(sw); }
      b.appendChild(document.createTextNode(opts.labelFn ? opts.labelFn(v) : v));
      b.addEventListener('click', () => {
        if (opts.selected.has(v)) opts.selected.delete(v); else opts.selected.add(v);
        opts.onChange();
      });
      box.appendChild(b);
    });
    wrap.appendChild(box);
    m.appendChild(wrap);
  }

  /* ======================================================================
     CHART PRIMITIVES - hand-written SVG
     ====================================================================== */
  const svgNS = 'http://www.w3.org/2000/svg';
  function svg(w, h) {
    const s = document.createElementNS(svgNS, 'svg');
    s.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    s.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    s.setAttribute('class', 'chart');
    s.setAttribute('role', 'img');
    return s;
  }
  function node(tag, attrs) {
    const n = document.createElementNS(svgNS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  function text(s, x, y, str, attrs) {
    const t = node('text', Object.assign({ class: 'axis-label', x, y }, attrs || {}));
    t.textContent = str;
    s.appendChild(t);
    return t;
  }

  /** Vertical columns with optional dashed mean line. rows: [{name,label,value,tip,selected}] */
  function columns(m, rows, opts) {
    opts = opts || {};
    m.innerHTML = '';
    const W = 880, H = 250, L = 64, R = 864, T = 18, B = 206;
    const s = svg(W, H);
    const max = Math.max(...rows.map(r => r.value), 1e-9) * 1.08;
    const n = rows.length || 1;
    const slot = (R - L) / n, bw = Math.max(6, Math.min(48, slot - 2));
    const f = opts.fmt || fmt.compact;
    for (let g = 0; g <= 4; g++) {
      const y = T + (B - T) * g / 4;
      s.appendChild(node('line', { class: g === 4 ? 'baseline' : 'gridline', x1: L, y1: y, x2: R, y2: y }));
      text(s, L - 10, y + 4, f(max * (1 - g / 4)), { 'text-anchor': 'end' });
    }
    const anySel = rows.some(r => r.selected);
    rows.forEach((r, i) => {
      const x = L + slot * i + (slot - bw) / 2;
      const h = (r.value / max) * (B - T);
      // 4px rounded data-end anchored to a square baseline
      const y = B - h, rr = Math.min(4, h, bw / 2);
      const d = `M${x},${B} L${x},${y + rr} Q${x},${y} ${x + rr},${y} L${x + bw - rr},${y} Q${x + bw},${y} ${x + bw},${y + rr} L${x + bw},${B} Z`;
      const p = node('path', { d, fill: r.color || 'var(--series-1)' });
      if (anySel && !r.selected) p.setAttribute('opacity', '0.35');
      p.setAttribute('tabindex', '0');
      p.style.cursor = opts.onClick ? 'pointer' : 'default';
      hoverable(p, () => r.tip || tipHtml(r.label || r.name, [['Value', f(r.value)]]));
      if (opts.onClick) p.addEventListener('click', () => opts.onClick(r.name));
      s.appendChild(p);
      // hit target taller than the mark
      const hit = node('rect', { class: 'hit', x: L + slot * i, y: T, width: slot, height: B - T });
      hoverable(hit, () => r.tip || tipHtml(r.label || r.name, [['Value', f(r.value)]]));
      if (opts.onClick) hit.addEventListener('click', () => opts.onClick(r.name));
      s.appendChild(hit);
      text(s, x + bw / 2, B + 18, r.label || r.name, { 'text-anchor': 'middle' });
    });
    if (opts.mean !== undefined) {
      const y = B - (opts.mean / max) * (B - T);
      s.appendChild(node('line', { class: 'crosshair', x1: L, y1: y, x2: R, y2: y }));
      text(s, R, y - 6, 'average ' + f(opts.mean), { 'text-anchor': 'end', style: 'fill:var(--text-secondary)' });
    }
    m.appendChild(s);
  }

  /** Line with crosshair snapping to nearest point. pts: [{name,label,value}] */
  function line(m, pts, opts) {
    opts = opts || {};
    m.innerHTML = '';
    const W = 880, H = 250, L = 64, R = 860, T = 18, B = 206;
    const s = svg(W, H);
    if (pts.length < 2) { m.appendChild(s); return; }
    const vals = pts.map(p => p.value);
    const lo0 = Math.min(...vals), hi0 = Math.max(...vals);
    const pad = (hi0 - lo0) * 0.25 || hi0 * 0.1 || 1;
    const lo = opts.zero ? 0 : Math.max(0, lo0 - pad), hi = hi0 + pad;
    const f = opts.fmt || fmt.compact;
    const X = i => L + i / (pts.length - 1) * (R - L);
    const Y = v => B - (v - lo) / (hi - lo) * (B - T);
    for (let g = 0; g <= 4; g++) {
      const y = T + (B - T) * g / 4;
      s.appendChild(node('line', { class: 'gridline', x1: L, y1: y, x2: R, y2: y }));
      text(s, L - 10, y + 4, f(hi - (hi - lo) * g / 4), { 'text-anchor': 'end' });
    }
    pts.forEach((p, i) => { if (i % Math.ceil(pts.length / 12) === 0) text(s, X(i), B + 18, p.label || p.name, { 'text-anchor': 'middle' }); });
    const dPath = pts.map((p, i) => (i ? 'L' : 'M') + X(i) + ',' + Y(p.value)).join(' ');
    s.appendChild(node('path', { d: dPath + ` L${X(pts.length - 1)},${B} L${X(0)},${B} Z`, fill: 'var(--series-1)', opacity: 0.08 }));
    s.appendChild(node('path', { d: dPath, class: 'series-line' }));
    const last = pts[pts.length - 1];
    s.appendChild(node('circle', { class: 'series-dot', cx: X(pts.length - 1), cy: Y(last.value), r: 4.5 }));
    text(s, X(pts.length - 1) - 6, Y(last.value) - 10, f(last.value), { 'text-anchor': 'end', style: 'fill:var(--text-primary);font-weight:600' });
    const cross = node('line', { class: 'crosshair', x1: 0, y1: T, x2: 0, y2: B, visibility: 'hidden' });
    const dot = node('circle', { class: 'series-dot', r: 5, visibility: 'hidden' });
    s.appendChild(cross); s.appendChild(dot);
    const hit = node('rect', { class: 'hit', x: L, y: T, width: R - L, height: B - T });
    hit.addEventListener('mousemove', e => {
      const box = s.getBoundingClientRect();
      const vx = (e.clientX - box.left) / box.width * W;
      const i = Math.max(0, Math.min(pts.length - 1, Math.round((vx - L) / (R - L) * (pts.length - 1))));
      const p = pts[i];
      cross.setAttribute('x1', X(i)); cross.setAttribute('x2', X(i)); cross.setAttribute('visibility', 'visible');
      dot.setAttribute('cx', X(i)); dot.setAttribute('cy', Y(p.value)); dot.setAttribute('visibility', 'visible');
      showTip(e, p.tip || tipHtml(p.label || p.name, [[opts.name || 'Value', f(p.value)]]));
    });
    hit.addEventListener('mouseleave', () => { cross.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden'); hideTip(); });
    s.appendChild(hit);
    m.appendChild(s);
  }

  /** Donut. slices: [{name, value, color}] */
  function donut(m, slices, opts) {
    opts = opts || {};
    m.innerHTML = '';
    const total = slices.reduce((a, x) => a + x.value, 0);
    const size = 260, cx = 130, cy = 130, rO = 104, rI = 66;
    const s = svg(size, size);
    const wrap = el('div', 'donut-wrap');
    if (total > 0) {
      let a0 = -Math.PI / 2;
      slices.forEach(sl => {
        const frac = sl.value / total;
        if (frac <= 0) return;
        const a1 = a0 + frac * Math.PI * 2 - (frac < 0.9999 ? 0.012 : 0);
        const big = (a1 - a0) > Math.PI ? 1 : 0;
        const P = (r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
        const [x0, y0] = P(rO, a0), [x1, y1] = P(rO, a1), [x2, y2] = P(rI, a1), [x3, y3] = P(rI, a0);
        const d = frac >= 0.9999
          ? `M${cx - rO},${cy} a${rO},${rO} 0 1 0 ${2 * rO},0 a${rO},${rO} 0 1 0 ${-2 * rO},0 Z M${cx - rI},${cy} a${rI},${rI} 0 1 1 ${2 * rI},0 a${rI},${rI} 0 1 1 ${-2 * rI},0 Z`
          : `M${x0},${y0} A${rO},${rO} 0 ${big} 1 ${x1},${y1} L${x2},${y2} A${rI},${rI} 0 ${big} 0 ${x3},${y3} Z`;
        const p = node('path', { d, fill: sl.color, 'fill-rule': 'evenodd' });
        p.setAttribute('tabindex', '0');
        p.style.cursor = opts.onClick ? 'pointer' : 'default';
        hoverable(p, () => tipHtml(sl.name, [[opts.measure || 'Value', (opts.fmt || fmt.compact)(sl.value)], ['Share', fmt.pct(100 * frac)]]));
        if (opts.onClick) p.addEventListener('click', () => opts.onClick(sl.name));
        s.appendChild(p);
        a0 = a0 + frac * Math.PI * 2;
      });
    }
    const t1 = node('text', { x: cx, y: cy - 2, 'text-anchor': 'middle', fill: 'var(--text-primary)', 'font-size': 21, 'font-weight': 700 });
    t1.textContent = (opts.fmt || fmt.compact)(total);
    const t2 = node('text', { x: cx, y: cy + 19, 'text-anchor': 'middle', fill: 'var(--text-muted)', 'font-size': 11.5 });
    t2.textContent = opts.centreLabel || 'total';
    s.appendChild(t1); s.appendChild(t2);
    wrap.appendChild(s);
    const leg = el('div', 'donut-legend');
    slices.forEach(sl => {
      const row = el('div', 'row');
      const sw = el('span', 'swatch'); sw.style.background = sl.color;
      row.appendChild(sw);
      row.appendChild(el('span', '', sl.name));
      row.appendChild(el('span', 'v', total ? fmt.pct(100 * sl.value / total) : '–'));
      leg.appendChild(row);
    });
    wrap.appendChild(leg);
    m.appendChild(wrap);
  }

  /** Heatmap: rows x cols with one sequential hue and per-cell labels. */
  function heatmap(m, rowNames, colNames, values, opts) {
    opts = opts || {};
    m.innerHTML = '';
    const cw = 220, ch = 46, L = 160, T = 32;
    const W = L + cw * colNames.length + 8, H = T + ch * rowNames.length + 6;
    const s = svg(W, H);
    const flat = values.flat().filter(v => v !== null);
    const max = Math.max(...flat, 1e-9), min = Math.min(...flat, 0);
    const f = opts.fmt || fmt.dec;
    colNames.forEach((c, j) => text(s, L + cw * j + cw / 2, T - 10, c, { 'text-anchor': 'middle' }));
    rowNames.forEach((rn, i) => {
      text(s, L - 10, T + ch * i + ch / 2 + 4, rn, { 'text-anchor': 'end' });
      colNames.forEach((cn, j) => {
        const v = values[i][j];
        const t = v === null ? 0 : (v - min) / ((max - min) || 1);
        const cell = node('rect', { class: 'heat-cell', x: L + cw * j, y: T + ch * i, width: cw, height: ch, rx: 4,
                                    fill: v === null ? 'var(--surface-2)' : seqStep(t) });
        cell.setAttribute('tabindex', '0');
        hoverable(cell, () => tipHtml(rn + ' · ' + cn, [[opts.measure || 'Value', v === null ? 'no rows' : f(v)],
          ...(opts.counts ? [['Observations', fmt.int(opts.counts[i][j])]] : [])]));
        if (opts.onClick) cell.addEventListener('click', () => opts.onClick(rn, cn));
        s.appendChild(cell);
        const lab = text(s, L + cw * j + cw / 2, T + ch * i + ch / 2 + 4, v === null ? '–' : f(v), { 'text-anchor': 'middle' });
        lab.setAttribute('style', `fill:${t > 0.5 ? 'var(--on-dark)' : 'var(--text-primary)'};font-weight:600;pointer-events:none`);
      });
    });
    const sc = el('div', 'panel-scroll');
    sc.appendChild(s);
    m.appendChild(sc);
  }

  /** Dot-and-whisker: an estimate with its 95% interval. rows: [{name, mean, lo, hi, color}] */
  function dotWhisker(m, rows, opts) {
    opts = opts || {};
    m.innerHTML = '';
    const W = 620, rowH = 38, L = 168, R = 566, T = 22;
    const H = T + rowH * rows.length + 30;
    const s = svg(W, H);
    const lo = Math.min(...rows.map(r => r.lo)), hi = Math.max(...rows.map(r => r.hi));
    const pad = (hi - lo) * 0.1;
    const x0 = opts.zero ? 0 : Math.max(0, lo - pad), x1 = hi + pad;
    const X = v => L + (v - x0) / (x1 - x0) * (R - L);
    const f = opts.fmt || fmt.dec;
    for (let g = 0; g <= 4; g++) {
      const v = x0 + (x1 - x0) * g / 4;
      s.appendChild(node('line', { class: 'gridline', x1: X(v), y1: T - 8, x2: X(v), y2: H - 26 }));
      text(s, X(v), H - 8, f(v), { 'text-anchor': 'middle' });
    }
    rows.forEach((r, i) => {
      const y = T + rowH * i + rowH / 2;
      text(s, L - 12, y + 4, r.name, { 'text-anchor': 'end', style: 'fill:var(--text-secondary);font-size:12.5px' });
      s.appendChild(node('line', { x1: X(r.lo), y1: y, x2: X(r.hi), y2: y, stroke: r.color || 'var(--series-1)', 'stroke-width': 2.5, 'stroke-linecap': 'round' }));
      [r.lo, r.hi].forEach(v => s.appendChild(node('line', { x1: X(v), y1: y - 7, x2: X(v), y2: y + 7, stroke: r.color || 'var(--series-1)', 'stroke-width': 2 })));
      const c = node('circle', { cx: X(r.mean), cy: y, r: 6.5, fill: r.color || 'var(--series-1)', stroke: 'var(--surface-1)', 'stroke-width': 2 });
      c.setAttribute('tabindex', '0');
      hoverable(c, () => tipHtml(r.name, [['Mean', f(r.mean)], ['95% interval', f(r.lo) + ' – ' + f(r.hi)], ['Observations', fmt.int(r.n || 0)]], 'Study constant: bootstrap, 2,000 resamples'));
      s.appendChild(c);
      text(s, X(r.hi) + 10, y + 4, f(r.mean), { style: 'fill:var(--text-primary);font-weight:600' });
    });
    m.appendChild(s);
  }

  /** Tiny sparkline for a KPI tile. Returns an SVG string. */
  function sparkline(values, opts) {
    opts = opts || {};
    if (!values || values.length < 2) return '';
    const w = 108, h = 26, pad = 2;
    const lo = Math.min(...values), hi = Math.max(...values), span = (hi - lo) || 1;
    const X = i => pad + i / (values.length - 1) * (w - pad * 2);
    const Y = v => h - pad - (v - lo) / span * (h - pad * 2);
    const pts = values.map((v, i) => X(i) + ',' + Y(v)).join(' ');
    const c = opts.color || 'var(--series-1)';
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">`
      + `<polyline points="${pts}" fill="none" stroke="${c}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"></polyline></svg>`;
  }

  return { fmt, tipHtml, strategyColor, STRATEGY_ORDER, PRIORITY_COLOR, seqStep, seqFor,
           showTip, hideTip, hoverable, barList, dataTable, el, mount, start,
           newFilters, filterRows, anyFilter, summarize, groupDim, groupMonth, measureIndex,
           slicer, columns, line, donut, heatmap, dotWhisker, sparkline,
           get data() { return lastData; } };
})();
