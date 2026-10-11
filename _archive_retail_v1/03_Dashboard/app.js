/* ===========================================================================
   Live Decision Dashboard - shared runtime.

   Every page loads this file, then calls LDD.start(render). The page supplies
   only its own render(data) function; polling, the live indicator, tooltips,
   theming and number formatting all live here so no page reimplements them.

   No framework, no CDN, no build step.
   =========================================================================== */

const LDD = (() => {
  const POLL_MS = 1000;

  /* ------------------------------------------------------------ formatting */
  const nf = new Intl.NumberFormat('en-US');
  const fmt = {
    int: n => nf.format(Math.round(n)),
    money: n => '$' + nf.format(Math.round(n)),
    compact: n => {
      const a = Math.abs(n);
      if (a >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M';
      if (a >= 1e3) return '$' + Math.round(n / 1e3) + 'k';
      return '$' + Math.round(n);
    },
    pct: (n, d = 1) => (n * 100).toFixed(d) + '%',
    month: s => {
      const [y, m] = s.split('-');
      return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m - 1] + ' ' + y.slice(2);
    },
    clock: iso => {
      try { return new Date(iso).toLocaleTimeString(); } catch (e) { return iso; }
    }
  };

  /* --------------------------------------------------------------- colours */
  // Fixed slot order. A category keeps its colour even when a filter removes
  // its neighbours - colour follows the entity, never its rank.
  const CATEGORY_ORDER = ['Apparel', 'Beauty', 'Books', 'Electronics', 'Home Decor'];
  const slotVar = i => `var(--series-${(i % 5) + 1})`;
  const colorFor = name => {
    const i = CATEGORY_ORDER.indexOf(name);
    return slotVar(i < 0 ? 0 : i);
  };
  const seqStep = t => {
    // t in [0,1] -> one-hue sequential ramp, light to dark
    const steps = ['var(--seq-100)', 'var(--seq-250)', 'var(--seq-400)',
                   'var(--seq-500)', 'var(--seq-600)', 'var(--seq-700)'];
    return steps[Math.min(steps.length - 1, Math.max(0, Math.round(t * (steps.length - 1))))];
  };

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

  // Attach hover behaviour to any element, with keyboard parity.
  function hoverable(el, htmlFn) {
    el.addEventListener('mousemove', e => showTip(e, htmlFn()));
    el.addEventListener('mouseleave', hideTip);
    el.addEventListener('focus', e => {
      const r = el.getBoundingClientRect();
      showTip({ clientX: r.left + r.width / 2, clientY: r.top }, htmlFn());
    });
    el.addEventListener('blur', hideTip);
  }

  /* ----------------------------------------------------------------- theme */
  function initTheme() {
    const KEY = 'ldd-theme';
    let saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
    if (saved) document.documentElement.setAttribute('data-theme', saved);

    const btn = document.querySelector('.theme-btn');
    if (!btn) return;
    const paint = () => {
      const cur = document.documentElement.getAttribute('data-theme');
      const dark = cur === 'dark' || (!cur &&
        window.matchMedia('(prefers-color-scheme: dark)').matches);
      btn.textContent = dark ? 'Light' : 'Dark';
      btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    };
    btn.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme');
      const dark = cur === 'dark' || (!cur &&
        window.matchMedia('(prefers-color-scheme: dark)').matches);
      const next = dark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
      paint();
      if (lastData && renderFn) renderFn(lastData);   // repaint SVG that reads tokens
    });
    paint();
  }


  /* --------------------------------------------------- live text bindings */
  // Any prose that quotes a live figure carries one of these classes, so a
  // headline can never contradict the tiles beneath it after the data changes.
  function bindLiveText(d) {
    const set = (sel, val) =>
      document.querySelectorAll(sel).forEach(n => { n.textContent = val; });
    set('.js-rows', fmt.int(d.row_count));
    set('.js-revenue', fmt.compact(d.kpis.total_revenue));
    set('.js-avg-transaction', fmt.money(d.kpis.avg_transaction));
    set('.js-transactions', fmt.int(d.kpis.transactions));
    set('.js-months', String(d.trend.length));
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
      const res = await fetch('live_data.json?t=' + Date.now(), { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      failures = 0;
      if (data.last_updated !== lastStamp) {
        lastStamp = data.last_updated;
        lastData = data;
        bindLiveText(data);
        if (renderFn) renderFn(data);
      }
      setLive('live', 'Live · ' + fmt.clock(data.last_updated));
    } catch (e) {
      failures++;
      if (failures > 2) {
        setLive('stale', 'Not connected — is watcher.py running?');
      }
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

  /**
   * Horizontal bar list with a direct value label on every row.
   * The label is not decoration: three light-mode palette slots sit below 3:1
   * contrast, so the visible label is the required relief.
   */
  function barList(mount, rows, opts = {}) {
    const max = Math.max(...rows.map(r => r.value), 1);
    mount.innerHTML = '';
    const box = el('div', 'bars');
    rows.forEach((r, i) => {
      const row = el('div', 'bar-row');
      row.appendChild(el('div', 'name', r.label));
      const track = el('div', 'bar-track');
      const fill = el('div', 'bar-fill');
      fill.style.width = (r.value / max * 100).toFixed(2) + '%';
      fill.style.background = r.color || (opts.sequential
        ? seqStep(1 - i / Math.max(1, rows.length - 1))
        : colorFor(r.label));
      track.appendChild(fill);
      track.tabIndex = 0;
      track.setAttribute('role', 'img');
      track.setAttribute('aria-label', `${r.label}: ${r.valueText || fmt.money(r.value)}`);
      hoverable(track, () => r.tip || `<div class="t-title">${r.label}</div>
        <div class="t-row"><span>Revenue</span><span>${fmt.money(r.value)}</span></div>`);
      row.appendChild(track);
      row.appendChild(el('div', 'val', r.valueText || fmt.compact(r.value)));
      box.appendChild(row);
    });
    mount.appendChild(box);
  }

  /** Simple data table, used as the accessible view behind every chart. */
  function dataTable(mount, head, rows) {
    const t = el('table', 'data');
    const thead = el('thead');
    const hr = el('tr');
    head.forEach(h => {
      const th = el('th', h.num ? 'num' : '', h.label);
      hr.appendChild(th);
    });
    thead.appendChild(hr);
    t.appendChild(thead);
    const tb = el('tbody');
    rows.forEach(r => {
      const tr = el('tr');
      r.forEach((c, i) => tr.appendChild(el('td', head[i].num ? 'num' : '', c)));
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    mount.innerHTML = '';
    mount.appendChild(t);
  }

  /* ======================================================================
     CROSS-FILTER ENGINE
     The raw feed is small enough to ship whole, so every visual on the
     comprehensive page reads the same filtered row set. Clicking a slice
     filters every other visual, which is the behaviour people mean when
     they say "like Power BI".
     ====================================================================== */
  const F = { date: 0, cat: 1, city: 2, gender: 3, age: 4, qty: 5, rev: 6 };

  function bandOf(age) {
    return age < 30 ? '18-29' : age < 40 ? '30-39'
         : age < 50 ? '40-49' : age < 60 ? '50-59' : '60+';
  }

  function newFilters() {
    return { cat: new Set(), city: new Set(), gender: new Set(),
             band: new Set(), month: new Set() };
  }

  function filterRows(raw, f) {
    if (!raw || !raw.rows) return [];
    return raw.rows.filter(r =>
      (!f.cat.size    || f.cat.has(raw.cats[r[F.cat]])) &&
      (!f.city.size   || f.city.has(raw.cities[r[F.city]])) &&
      (!f.gender.size || f.gender.has(raw.genders[r[F.gender]])) &&
      (!f.band.size   || f.band.has(bandOf(r[F.age]))) &&
      (!f.month.size  || f.month.has(r[F.date].slice(0, 7))));
  }

  function anyFilter(f) {
    return !!(f.cat.size || f.city.size || f.gender.size || f.band.size || f.month.size);
  }

  /** Group rows by a key function -> [{name, revenue, units, lines}], desc by revenue. */
  function groupBy(rows, keyFn, order) {
    const m = new Map();
    rows.forEach(r => {
      const k = keyFn(r);
      let e = m.get(k);
      if (!e) { e = { name: k, revenue: 0, units: 0, lines: 0 }; m.set(k, e); }
      e.revenue += r[F.rev]; e.units += r[F.qty]; e.lines += 1;
    });
    const out = Array.from(m.values());
    if (order) out.sort((a, b) => order.indexOf(a.name) - order.indexOf(b.name));
    else out.sort((a, b) => b.revenue - a.revenue);
    return out;
  }

  const totalRev = rows => rows.reduce((s, r) => s + r[F.rev], 0);
  const totalQty = rows => rows.reduce((s, r) => s + r[F.qty], 0);

  /* ======================================================================
     SLICERS
     ====================================================================== */
  function slicer(mount, opts) {
    // opts: {label, values, selected:Set, onChange(), colorFn?}
    mount.innerHTML = '';
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
      if (opts.colorFn) {
        const sw = el('span', 'swatch');
        sw.style.background = opts.colorFn(v);
        b.appendChild(sw);
      }
      b.appendChild(document.createTextNode(v));
      b.addEventListener('click', () => {
        if (opts.selected.has(v)) opts.selected.delete(v); else opts.selected.add(v);
        opts.onChange();
      });
      box.appendChild(b);
    });
    wrap.appendChild(box);
    mount.appendChild(wrap);
  }

  /* ======================================================================
     CHART PRIMITIVES
     All hand-written SVG. No library, no build step.
     ====================================================================== */
  const svgNS = 'http://www.w3.org/2000/svg';
  function svg(w, h, cls) {
    const s = document.createElementNS(svgNS, 'svg');
    s.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    s.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    s.setAttribute('class', cls || 'chart');
    s.setAttribute('role', 'img');
    return s;
  }
  function node(tag, attrs) {
    const n = document.createElementNS(svgNS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  /** Donut. slices: [{name, value, color}]. Centre shows the total. */
  function donut(mount, slices, opts) {
    opts = opts || {};
    mount.innerHTML = '';
    const total = slices.reduce((s, x) => s + x.value, 0);
    const size = 260, cx = size / 2, cy = size / 2, rOuter = 104, rInner = 66;
    const s = svg(size, size);
    if (total <= 0) { mount.appendChild(s); return; }

    let a0 = -Math.PI / 2;
    slices.forEach(sl => {
      const frac = sl.value / total;
      const a1 = a0 + frac * Math.PI * 2;
      // a full-circle single slice cannot be drawn as an arc; use two rings
      const big = (a1 - a0) > Math.PI ? 1 : 0;
      const p = (r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
      const [x0, y0] = p(rOuter, a0), [x1, y1] = p(rOuter, a1);
      const [x2, y2] = p(rInner, a1), [x3, y3] = p(rInner, a0);
      const d = frac >= 0.9999
        ? 'M ' + (cx - rOuter) + ' ' + cy + ' a ' + rOuter + ' ' + rOuter + ' 0 1 0 ' + (rOuter * 2) + ' 0'
          + ' a ' + rOuter + ' ' + rOuter + ' 0 1 0 ' + (-rOuter * 2) + ' 0 Z'
          + 'M ' + (cx - rInner) + ' ' + cy + ' a ' + rInner + ' ' + rInner + ' 0 1 1 ' + (rInner * 2) + ' 0'
          + ' a ' + rInner + ' ' + rInner + ' 0 1 1 ' + (-rInner * 2) + ' 0 Z'
        : ['M', x0, y0, 'A', rOuter, rOuter, 0, big, 1, x1, y1,
           'L', x2, y2, 'A', rInner, rInner, 0, big, 0, x3, y3, 'Z'].join(' ');
      const path = node('path', { d: d, fill: sl.color, stroke: 'var(--surface-1)', 'stroke-width': 2 });
      path.style.cursor = 'pointer';
      path.setAttribute('tabindex', '0');
      path.setAttribute('aria-label', sl.name + ': ' + fmt.money(sl.value) + ', ' + fmt.pct(frac));
      hoverable(path, () => '<div class="t-title">' + sl.name + '</div>'
        + '<div class="t-row"><span>Revenue</span><span>' + fmt.money(sl.value) + '</span></div>'
        + '<div class="t-row"><span>Share</span><span>' + fmt.pct(frac) + '</span></div>');
      if (opts.onClick) path.addEventListener('click', () => opts.onClick(sl.name));
      s.appendChild(path);
      a0 = a1;
    });

    const t1 = node('text', { x: cx, y: cy - 4, 'text-anchor': 'middle',
                              fill: 'var(--text-primary)', 'font-size': 22, 'font-weight': 700 });
    t1.textContent = fmt.compact(total);
    const t2 = node('text', { x: cx, y: cy + 18, 'text-anchor': 'middle',
                              fill: 'var(--text-muted)', 'font-size': 11.5 });
    t2.textContent = opts.centreLabel || 'total revenue';
    s.appendChild(t1); s.appendChild(t2);
    mount.appendChild(s);
  }

  /**
   * Stacked composition bars. rows: [{name, parts:[{name,value,color}]}]
   * Each segment carries a 2px surface gap, per the mark spec.
   */
  function stackedBars(mount, rows, opts) {
    opts = opts || {};
    mount.innerHTML = '';
    const box = el('div', 'stack-list');
    const max = Math.max.apply(null, rows.map(r =>
      r.parts.reduce((s, p) => s + p.value, 0)).concat([1]));
    rows.forEach(r => {
      const total = r.parts.reduce((s, p) => s + p.value, 0);
      const line = el('div', 'stack-row');
      line.appendChild(el('div', 'name', r.name));
      const track = el('div', 'stack-track');
      r.parts.forEach(p => {
        if (p.value <= 0) return;
        const seg = el('div', 'stack-seg');
        seg.style.width = (p.value / max * 100) + '%';
        seg.style.background = p.color;
        seg.tabIndex = 0;
        seg.setAttribute('role', 'img');
        seg.setAttribute('aria-label', r.name + ', ' + p.name + ': ' + fmt.money(p.value));
        hoverable(seg, () => '<div class="t-title">' + r.name + ' &middot; ' + p.name + '</div>'
          + '<div class="t-row"><span>Revenue</span><span>' + fmt.money(p.value) + '</span></div>'
          + '<div class="t-row"><span>Of row</span><span>'
          + fmt.pct(total ? p.value / total : 0) + '</span></div>');
        if (opts.onClick) seg.addEventListener('click', () => opts.onClick(p.name, r.name));
        track.appendChild(seg);
      });
      line.appendChild(track);
      line.appendChild(el('div', 'val', fmt.compact(total)));
      box.appendChild(line);
    });
    mount.appendChild(box);
  }

  /** Tiny inline sparkline for a KPI tile. Returns an SVG string. */
  function sparkline(values, opts) {
    opts = opts || {};
    if (!values || values.length < 2) return '';
    const w = opts.width || 108, h = opts.height || 26, pad = 2;
    const lo = Math.min.apply(null, values), hi = Math.max.apply(null, values);
    const span = (hi - lo) || 1;
    const X = i => pad + i / (values.length - 1) * (w - pad * 2);
    const Y = v => h - pad - (v - lo) / span * (h - pad * 2);
    const pts = values.map((v, i) => X(i) + ',' + Y(v)).join(' ');
    const area = 'M ' + X(0) + ' ' + h + ' L ' + values.map((v, i) => X(i) + ' ' + Y(v)).join(' L ')
               + ' L ' + X(values.length - 1) + ' ' + h + ' Z';
    const c = opts.color || 'var(--series-1)';
    return '<svg class="spark" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" aria-hidden="true">'
      + '<path d="' + area + '" fill="' + c + '" opacity="0.14"></path>'
      + '<polyline points="' + pts + '" fill="none" stroke="' + c
      + '" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"></polyline>'
      + '</svg>';
  }

  /**
   * Vertical column chart with an optional dashed mean line.
   * rows: [{name, value}]. Single series, so no legend needed.
   */
  function columns(mount, rows, opts) {
    opts = opts || {};
    mount.innerHTML = '';
    const W = 880, H = 260, L = 64, R = 860, T = 20, B = 212;
    const s = svg(W, H);
    const max = Math.max.apply(null, rows.map(r => r.value).concat([1]));
    const n = rows.length || 1;
    const slot = (R - L) / n, bw = Math.max(6, Math.min(46, slot * 0.62));

    for (let g = 0; g <= 4; g++) {
      const y = T + (B - T) * g / 4;
      s.appendChild(node('line', { class: 'gridline', x1: L, y1: y, x2: R, y2: y }));
      const lab = node('text', { class: 'axis-label', x: L - 10, y: y + 4, 'text-anchor': 'end' });
      lab.textContent = fmt.compact(max * (1 - g / 4));
      s.appendChild(lab);
    }

    rows.forEach((r, i) => {
      const x = L + slot * i + (slot - bw) / 2;
      const h = (r.value / max) * (B - T);
      const y = B - h;
      const rect = node('rect', { x: x, y: y, width: bw, height: Math.max(1, h),
                                  rx: 4, fill: r.color || 'var(--series-1)' });
      rect.style.cursor = opts.onClick ? 'pointer' : 'default';
      rect.setAttribute('tabindex', '0');
      rect.setAttribute('aria-label', r.name + ': ' + fmt.money(r.value));
      hoverable(rect, () => '<div class="t-title">' + r.name + '</div>'
        + '<div class="t-row"><span>Revenue</span><span>' + fmt.money(r.value) + '</span></div>'
        + (r.lines !== undefined
            ? '<div class="t-row"><span>Transactions</span><span>' + fmt.int(r.lines) + '</span></div>' : ''));
      if (opts.onClick) rect.addEventListener('click', () => opts.onClick(r.name));
      s.appendChild(rect);

      const lab = node('text', { class: 'axis-label', x: x + bw / 2, y: B + 18, 'text-anchor': 'middle' });
      lab.textContent = r.label || r.name;
      s.appendChild(lab);
    });

    if (opts.mean !== undefined && max > 0) {
      const y = B - (opts.mean / max) * (B - T);
      s.appendChild(node('line', { class: 'crosshair', x1: L, y1: y, x2: R, y2: y, 'stroke-width': 1.5 }));
      const lab = node('text', { class: 'axis-label', x: R, y: y - 7, 'text-anchor': 'end',
                                 style: 'fill:var(--text-secondary)' });
      lab.textContent = 'average ' + fmt.compact(opts.mean);
      s.appendChild(lab);
    }
    mount.appendChild(s);
  }

  /** Scatter. points: [{x, y, name, color}] with axis labels. */
  function scatter(mount, points, opts) {
    opts = opts || {};
    mount.innerHTML = '';
    const W = 880, H = 300, L = 66, R = 860, T = 18, B = 246;
    const s = svg(W, H);
    if (!points.length) { mount.appendChild(s); return; }
    // Fitted domains rather than zero-based: the question here is whether the
    // points fall on a line, not how large they are against zero. A zero-based
    // pair of axes would crush ten similar cities into one corner.
    const xs = points.map(p => p.x), ys = points.map(p => p.y);
    const xLo0 = Math.min.apply(null, xs), xHi0 = Math.max.apply(null, xs);
    const yLo0 = Math.min.apply(null, ys), yHi0 = Math.max.apply(null, ys);
    const xPad = (xHi0 - xLo0) * 0.12 || 1, yPad = (yHi0 - yLo0) * 0.12 || 1;
    const xLo = xLo0 - xPad, xMax = xHi0 + xPad;
    const yLo = yLo0 - yPad, yMax = yHi0 + yPad;
    const X = v => L + (v - xLo) / (xMax - xLo) * (R - L);
    const Y = v => B - (v - yLo) / (yMax - yLo) * (B - T);

    for (let g = 0; g <= 4; g++) {
      const y = T + (B - T) * g / 4;
      s.appendChild(node('line', { class: 'gridline', x1: L, y1: y, x2: R, y2: y }));
      const lab = node('text', { class: 'axis-label', x: L - 10, y: y + 4, 'text-anchor': 'end' });
      lab.textContent = fmt.compact(yLo + (yMax - yLo) * (1 - g / 4));
      s.appendChild(lab);
    }
    // x tick labels, so a fitted axis still reads as a real scale
    for (let g = 0; g <= 4; g++) {
      const v = xLo + (xMax - xLo) * g / 4;
      const lab = node('text', { class: 'axis-label', x: X(v), y: B + 18, 'text-anchor': 'middle' });
      lab.textContent = fmt.int(v);
      s.appendChild(lab);
    }
    s.appendChild(node('line', { class: 'baseline', x1: L, y1: B, x2: R, y2: B }));

    points.forEach(p => {
      const c = node('circle', { cx: X(p.x), cy: Y(p.y), r: 6,
                                 fill: p.color || 'var(--series-1)',
                                 stroke: 'var(--surface-1)', 'stroke-width': 2 });
      c.setAttribute('tabindex', '0');
      c.style.cursor = 'pointer';
      c.setAttribute('aria-label', p.name + ': ' + fmt.int(p.x) + ' by ' + fmt.money(p.y));
      hoverable(c, () => '<div class="t-title">' + p.name + '</div>'
        + '<div class="t-row"><span>' + (opts.xLabel || 'x') + '</span><span>' + fmt.int(p.x) + '</span></div>'
        + '<div class="t-row"><span>' + (opts.yLabel || 'y') + '</span><span>' + fmt.money(p.y) + '</span></div>');
      if (opts.onClick) c.addEventListener('click', () => opts.onClick(p.name));
      s.appendChild(c);
    });

    if (opts.xLabel) {
      const lx = node('text', { class: 'axis-label', x: (L + R) / 2, y: H - 4, 'text-anchor': 'middle' });
      lx.textContent = opts.xLabel; s.appendChild(lx);
    }
    mount.appendChild(s);
  }

  return { fmt, colorFor, seqStep, slotVar, CATEGORY_ORDER, showTip, hideTip,
           hoverable, barList, dataTable, el, start,
           // cross-filter engine
           F, bandOf, newFilters, filterRows, anyFilter, groupBy, totalRev, totalQty,
           // visuals
           slicer, donut, stackedBars, sparkline, columns, scatter,
           get data() { return lastData; } };
})();
