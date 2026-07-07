/* Tourenbuch 6 — Frontend */

const API = '/api';
let charts = {};

// ── Utilities ────────────────────────────────────────────────────────────────

async function get(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function grade(val, text) {
  if (!text && !val) return '–';
  return `<span class="grade">${text || val}</span>`;
}

function tags(list, cls = 'tag') {
  if (!list) return '';
  return list.split(',').map(t => t.trim()).filter(Boolean)
    .map(t => `<span class="${cls}">${t}</span>`).join('');
}

function quality(q) {
  const map = { '-2': '★☆☆☆ sehr schlecht', '-1': '★★☆☆ schlecht',
    '0': '★★★☆ mittel', '1': '★★★☆ gut', '2': '★★★★ sehr gut', '3': '✦ herausragend' };
  return (map[String(q)] || q) ?? '–';
}

function escHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function paginator(total, page, pageSize, onPage) {
  const pages = Math.ceil(total / pageSize) || 1;
  if (pages <= 1) return '';
  const btns = [];
  btns.push(`<button class="btn" ${page===1?'disabled':''} data-p="${page-1}">‹</button>`);
  for (let p = Math.max(1, page-2); p <= Math.min(pages, page+2); p++) {
    btns.push(`<button class="btn ${p===page?'current':''}" data-p="${p}">${p}</button>`);
  }
  btns.push(`<button class="btn" ${page===pages?'disabled':''} data-p="${page+1}">›</button>`);
  const html = `<div class="pagination">
    <span>${total.toLocaleString()} Einträge</span>
    ${btns.join('')}
  </div>`;

  // Attach events after insert
  setTimeout(() => {
    document.querySelectorAll('.pagination button[data-p]').forEach(b => {
      b.addEventListener('click', () => onPage(+b.dataset.p));
    });
  }, 0);
  return html;
}

// ── Detail Panel ─────────────────────────────────────────────────────────────

const overlay = document.getElementById('detail-overlay');
const panel   = document.getElementById('detail-panel');

function openPanel(html) {
  panel.innerHTML = html;
  overlay.classList.add('open');
  panel.classList.add('open');
}

function closePanel() {
  overlay.classList.remove('open');
  panel.classList.remove('open');
}

overlay.addEventListener('click', closePanel);

// ── Tab routing ──────────────────────────────────────────────────────────────

let activeTab = 'gebiete';

document.querySelectorAll('nav button').forEach(btn => {
  btn.addEventListener('click', () => {
    activeTab = btn.dataset.tab;
    document.querySelectorAll('nav button').forEach(b => b.classList.toggle('active', b===btn));
    renderTab(activeTab);
  });
});

function renderTab(tab) {
  const main = document.getElementById('main');
  main.innerHTML = '<div class="loading">Lade…</div>';
  closePanel();
  if (tab === 'gebiete')    renderGebiete();
  if (tab === 'wege')       renderWege();
  if (tab === 'begehungen') renderBegehungen();
  if (tab === 'statistik')  renderStatistik();
}

// ── Tab: Gebiete & Gipfel ────────────────────────────────────────────────────

let gebietState = { view: 'gebiete', gebiet_id: null, gipfel_id: null };

async function renderGebiete() {
  const main = document.getElementById('main');

  // Load regionen for filter
  const [regionen, gebiete] = await Promise.all([
    get('/regionen'),
    get('/gebiete'),
  ]);

  const regionOptions = `<option value="">Alle Regionen</option>` +
    regionen.map(r => `<option value="${r.ID}">${escHtml(r.REGION)}</option>`).join('');

  main.innerHTML = `
    <div class="filters">
      <label><span>Region</span>
        <select id="reg-filter">${regionOptions}</select>
      </label>
      <label><span>Suche</span>
        <input type="search" id="gebiet-search" placeholder="Gebiet oder Gipfel…">
      </label>
    </div>
    <div id="gebiete-content"></div>
  `;

  let currentRegion = null;

  function filterGebiete() {
    const reg = +document.getElementById('reg-filter').value || null;
    const q = document.getElementById('gebiet-search').value.toLowerCase();
    const filtered = gebiete.filter(g =>
      (!reg || g.REGION_ID === reg) &&
      (!q || g.GEBIET.toLowerCase().includes(q))
    );
    renderGebieteCards(filtered);
  }

  document.getElementById('reg-filter').addEventListener('change', filterGebiete);
  document.getElementById('gebiet-search').addEventListener('input', filterGebiete);

  filterGebiete();
}

function renderGebieteCards(gebiete) {
  const el = document.getElementById('gebiete-content');
  if (!gebiete.length) { el.innerHTML = '<div class="empty">Keine Gebiete gefunden.</div>'; return; }

  el.innerHTML = `
    <div class="gebiete-grid">
      ${gebiete.map(g => `
        <div class="gebiet-card" data-id="${g.ID}">
          <div class="name">${escHtml(g.GEBIET)}</div>
          <div class="meta">
            ${escHtml(g.REGION)} &nbsp;·&nbsp;
            ${g.N_GIPFEL} Gipfel &nbsp;·&nbsp; ${g.N_WEGE} Wege
          </div>
        </div>
      `).join('')}
    </div>`;

  el.querySelectorAll('.gebiet-card').forEach(card => {
    card.addEventListener('click', () => showGipfelList(+card.dataset.id,
      gebiete.find(g => g.ID === +card.dataset.id)));
  });
}

async function showGipfelList(gebiet_id, gebiet) {
  const el = document.getElementById('gebiete-content');
  el.innerHTML = '<div class="loading">Lade Gipfel…</div>';

  const data = await get(`/gipfel?gebiet_id=${gebiet_id}&page_size=200`);

  el.innerHTML = `
    <div class="breadcrumb">
      <a id="bc-gebiete">Gebiete</a> <span>›</span>
      <strong>${escHtml(gebiet.GEBIET)}</strong>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Gipfel</th><th>Typ</th><th>Routen</th><th>Begehungen</th>
        </tr></thead>
        <tbody>
          ${data.items.map(g => `
            <tr data-id="${g.ID}">
              <td><strong>${escHtml(g.GIPFEL)}</strong>
                ${g.NAME2 ? `<br><small class="text-dim">${escHtml(g.NAME2)}</small>` : ''}</td>
              <td><span class="tag">${escHtml(g.GIPFELTYP||'–')}</span></td>
              <td>${g.N_WEGE}</td>
              <td>${g.N_BEGEHUNGEN}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;

  document.getElementById('bc-gebiete').addEventListener('click', renderGebiete);
  el.querySelectorAll('tbody tr').forEach(row => {
    row.addEventListener('click', () => showGipfelDetail(+row.dataset.id, gebiet));
  });
}

async function showGipfelDetail(gipfel_id, gebiet) {
  const data = await get(`/gipfel/${gipfel_id}`);
  openPanel(`
    <button class="close-btn" id="panel-close">✕</button>
    <h2>${escHtml(data.GIPFEL)}</h2>
    <div class="sub">${escHtml(data.GEBIET)} · ${escHtml(data.REGION)}</div>
    ${data.H ? `<div class="sub">${data.H} m Höhe</div>` : ''}

    <div class="detail-section">
      <h3>Routen (${data.wege.length})</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Weg</th><th>Grad</th><th>Begeh.</th></tr></thead>
          <tbody>
            ${data.wege.map(w => `
              <tr class="weg-row" data-id="${w.ID}">
                <td>${escHtml(w.WEG)}</td>
                <td>${grade(w.GRDX, w.GRAD_TEXT)}</td>
                <td>${w.N_BEGEHUNGEN}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>
    ${data.NOTIZ ? `<div class="detail-section"><h3>Notiz</h3><p>${escHtml(data.NOTIZ)}</p></div>` : ''}
  `);
  document.getElementById('panel-close').addEventListener('click', closePanel);
  panel.querySelectorAll('.weg-row').forEach(row => {
    row.addEventListener('click', () => showWegDetail(+row.dataset.id));
  });
}

// ── Tab: Wege ────────────────────────────────────────────────────────────────

let wegeState = { page: 1, gebiet_id: '', grdx_min: '', grdx_max: '', search: '' };

async function renderWege() {
  const main = document.getElementById('main');

  const [gebiete, grades] = await Promise.all([
    get('/gebiete'),
    get('/grade_lookup'),
  ]);

  const gebietOptions = `<option value="">Alle Gebiete</option>` +
    gebiete.map(g => `<option value="${g.ID}">${escHtml(g.GEBIET)}</option>`).join('');
  const gradeOptions = grades
    .filter(g => g.GRDX > 0)
    .map(g => `<option value="${g.GRDX}">${escHtml(g.GRDR)}</option>`).join('');

  main.innerHTML = `
    <div class="filters">
      <label><span>Gebiet</span>
        <select id="w-gebiet">${gebietOptions}</select>
      </label>
      <label><span>Grad von</span>
        <select id="w-grdmin"><option value="">–</option>${gradeOptions}</select>
      </label>
      <label><span>Grad bis</span>
        <select id="w-grdmax"><option value="">–</option>${gradeOptions}</select>
      </label>
      <label><span>Suche</span>
        <input type="search" id="w-search" placeholder="Weg- oder Gipfelname…">
      </label>
      <button class="btn primary" id="w-filter-btn">Filtern</button>
    </div>
    <div id="wege-table"></div>`;

  function applyFilter() {
    wegeState = {
      page: 1,
      gebiet_id: document.getElementById('w-gebiet').value,
      grdx_min:  document.getElementById('w-grdmin').value,
      grdx_max:  document.getElementById('w-grdmax').value,
      search:    document.getElementById('w-search').value,
    };
    loadWegeTable();
  }

  document.getElementById('w-filter-btn').addEventListener('click', applyFilter);
  document.getElementById('w-search').addEventListener('keydown', e => { if (e.key === 'Enter') applyFilter(); });

  loadWegeTable();
}

async function loadWegeTable(page = wegeState.page) {
  wegeState.page = page;
  const el = document.getElementById('wege-table');
  if (!el) return;
  el.innerHTML = '<div class="loading">Lade…</div>';

  const p = new URLSearchParams({ page, page_size: 50 });
  if (wegeState.gebiet_id) p.set('gebiet_id', wegeState.gebiet_id);
  if (wegeState.grdx_min)  p.set('grdx_min',  wegeState.grdx_min);
  if (wegeState.grdx_max)  p.set('grdx_max',  wegeState.grdx_max);
  if (wegeState.search)    p.set('search',     wegeState.search);

  const data = await get(`/wege?${p}`);

  el.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Gebiet</th><th>Gipfel</th><th>Weg</th>
          <th>Grad</th><th>Charakter</th><th>Sicherung</th><th>Begeh.</th>
        </tr></thead>
        <tbody>
          ${data.items.map(w => `
            <tr class="weg-row" data-id="${w.ID}">
              <td class="dim">${escHtml(w.GEBIET||'–')}</td>
              <td>${escHtml(w.GIPFEL||'–')}</td>
              <td><strong>${escHtml(w.WEG||'–')}</strong></td>
              <td>${grade(w.GRDX, w.GRAD_TEXT)}</td>
              <td>${tags(w.CHARAKTER)}</td>
              <td>${tags(w.SICHERUNG)}</td>
              <td>${w.N_BEGEHUNGEN}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>
    ${paginator(data.total, data.page, data.page_size, loadWegeTable)}
  `;

  el.querySelectorAll('.weg-row').forEach(row => {
    row.addEventListener('click', () => showWegDetail(+row.dataset.id));
  });
}

async function showWegDetail(weg_id) {
  const w = await get(`/wege/${weg_id}`);

  const begehRows = (w.begehungen || []).map(b => `
    <tr>
      <td>${b.DATUM || '–'}</td>
      <td>${escHtml(b.PARTNER || '–')}</td>
      <td><span class="tag">${escHtml(b.STIL || '–')}</span></td>
    </tr>`).join('');

  openPanel(`
    <button class="close-btn" id="panel-close">✕</button>
    <h2>${escHtml(w.WEG)}</h2>
    <div class="sub">
      ${escHtml(w.GIPFEL)} · ${escHtml(w.GEBIET)} · ${escHtml(w.REGION)}
    </div>

    <div class="detail-section">
      <h3>Bewertung</h3>
      <dl class="kv">
        <dt>Grad</dt><dd>${grade(w.GRDX, w.GRAD_TEXT)}</dd>
        ${w.GRAD_OU_TEXT ? `<dt>Onsight</dt><dd>${grade(w.GRDXOU, w.GRAD_OU_TEXT)}</dd>` : ''}
        ${w.GRAD_RP_TEXT ? `<dt>Rotpunkt</dt><dd>${grade(w.GRDXRP, w.GRAD_RP_TEXT)}</dd>` : ''}
        <dt>Qualität</dt><dd>${quality(w.QW)}</dd>
      </dl>
    </div>

    <div class="detail-section">
      <h3>Charakter</h3>
      <div>${(w.charakter||[]).map(c => `<span class="tag">${escHtml(c.CHARAKTER)}</span>`).join('') || '–'}</div>
      <div style="margin-top:.5rem">
        ${(w.sicherung||[]).map(s => `<span class="tag">${escHtml(s.SIART)}</span>`).join('')}
        ${(w.anforderung||[]).map(a => `<span class="tag">${escHtml(a.ANFORDERUNG)}</span>`).join('')}
        ${(w.neigung||[]).map(n => `<span class="tag">${escHtml(n.NEIGUNG)}</span>`).join('')}
      </div>
    </div>

    ${w.BESCHREIBUNG ? `<div class="detail-section"><h3>Beschreibung</h3><p style="white-space:pre-wrap;font-size:.85rem">${escHtml(w.BESCHREIBUNG)}</p></div>` : ''}
    ${w.CRUX ? `<div class="detail-section"><h3>Crux</h3><p style="font-size:.85rem">${escHtml(w.CRUX)}</p></div>` : ''}
    ${w.TIPP ? `<div class="detail-section"><h3>Tipp</h3><p style="font-size:.85rem">${escHtml(w.TIPP)}</p></div>` : ''}

    ${begehRows ? `
    <div class="detail-section">
      <h3>Begehungen (${w.begehungen.length})</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Datum</th><th>Partner</th><th>Stil</th></tr></thead>
          <tbody>${begehRows}</tbody>
        </table>
      </div>
    </div>` : ''}
  `);
  document.getElementById('panel-close').addEventListener('click', closePanel);
}

// ── Tab: Begehungen ───────────────────────────────────────────────────────────

let begState = { page: 1, person_id: '', year: '' };

async function renderBegehungen() {
  const main = document.getElementById('main');

  const personen = await get('/personen');

  // Gather available years from the data
  const personOptions = `<option value="">Alle Personen</option>` +
    personen.map(p => `<option value="${p.ID}">${escHtml(p.VORNAME)} ${escHtml(p.NAME)}</option>`).join('');

  const currentYear = new Date().getFullYear();
  const yearOptions = `<option value="">Alle Jahre</option>` +
    Array.from({length: currentYear - 1899}, (_, i) => currentYear - i)
      .map(y => `<option value="${y}">${y}</option>`).join('');

  main.innerHTML = `
    <div class="filters">
      <label><span>Person</span>
        <select id="beg-person">${personOptions}</select>
      </label>
      <label><span>Jahr</span>
        <select id="beg-year">${yearOptions}</select>
      </label>
      <button class="btn primary" id="beg-filter-btn">Filtern</button>
    </div>
    <div id="beg-table"></div>`;

  function applyFilter() {
    begState = {
      page: 1,
      person_id: document.getElementById('beg-person').value,
      year:      document.getElementById('beg-year').value,
    };
    loadBegTable();
  }

  document.getElementById('beg-filter-btn').addEventListener('click', applyFilter);
  loadBegTable();
}

async function loadBegTable(page = begState.page) {
  begState.page = page;
  const el = document.getElementById('beg-table');
  if (!el) return;
  el.innerHTML = '<div class="loading">Lade…</div>';

  const p = new URLSearchParams({ page, page_size: 50 });
  if (begState.person_id) p.set('person_id', begState.person_id);
  if (begState.year)      p.set('year',      begState.year);

  const data = await get(`/begehungen?${p}`);

  el.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Datum</th><th>Gebiet</th><th>Gipfel</th><th>Weg</th>
          <th>Grad</th><th>Stil</th><th>Partner</th>
        </tr></thead>
        <tbody>
          ${data.items.map(b => `
            <tr class="beg-row" data-id="${b.ID}">
              <td style="white-space:nowrap">${b.DATUM || '–'}</td>
              <td class="dim">${escHtml(b.GEBIET || '–')}</td>
              <td>${escHtml(b.GIPFEL || '–')}</td>
              <td><strong>${escHtml(b.WEG || '–')}</strong></td>
              <td>${grade(b.GRDX, b.GRAD_TEXT)}</td>
              <td>${b.STIL ? `<span class="tag">${escHtml(b.STIL)}</span>` : '–'}</td>
              <td>${escHtml(b.PARTNER || '–')}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>
    ${paginator(data.total, data.page, data.page_size, loadBegTable)}
  `;

  el.querySelectorAll('.beg-row').forEach(row => {
    row.addEventListener('click', () => showBegDetail(+row.dataset.id));
  });
}

async function showBegDetail(beg_id) {
  const b = await get(`/begehungen/${beg_id}`);

  const teamRows = (b.seilschaft || []).map(s => `
    <tr>
      <td>${escHtml(s.VORNAME||'')} ${escHtml(s.NAME||'')}
        ${s.SPITZNAME ? `<small class="tag">${escHtml(s.SPITZNAME)}</small>` : ''}</td>
      <td><span class="tag">${escHtml(s.ART||'–')}</span></td>
      <td><span class="tag">${escHtml(s.STIL||'–')}</span></td>
      <td>${s.GRAD_BEG_TEXT ? grade(s.GRDXBEG, s.GRAD_BEG_TEXT) : '–'}</td>
    </tr>`).join('');

  openPanel(`
    <button class="close-btn" id="panel-close">✕</button>
    <h2>${b.DATUM || '–'}</h2>
    <div class="sub">${escHtml(b.WEG)} · ${escHtml(b.GIPFEL)} · ${escHtml(b.GEBIET)}</div>

    <div class="detail-section">
      <dl class="kv">
        <dt>Grad</dt><dd>${grade(b.GRDX, b.GRAD_TEXT)}</dd>
        <dt>Region</dt><dd>${escHtml(b.REGION||'–')}</dd>
      </dl>
    </div>

    ${b.NOTIZ ? `<div class="detail-section"><h3>Notiz</h3><p style="white-space:pre-wrap;font-size:.85rem">${escHtml(b.NOTIZ)}</p></div>` : ''}

    ${teamRows ? `
    <div class="detail-section">
      <h3>Seilschaft</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Person</th><th>Art</th><th>Stil</th><th>Grad</th></tr></thead>
          <tbody>${teamRows}</tbody>
        </table>
      </div>
    </div>` : ''}
  `);
  document.getElementById('panel-close').addEventListener('click', closePanel);
}

// ── Tab: Statistik ────────────────────────────────────────────────────────────

async function renderStatistik() {
  const main = document.getElementById('main');

  const stats = await get('/stats');
  const s = stats.summary || {};

  main.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="val">${s.N_BEGEHUNGEN||0}</div><div class="lbl">Begehungen</div></div>
      <div class="stat-card"><div class="val">${s.N_WEGE||0}</div><div class="lbl">verschiedene Wege</div></div>
      <div class="stat-card"><div class="val">${s.N_GIPFEL||0}</div><div class="lbl">Gipfel</div></div>
      <div class="stat-card"><div class="val">${s.N_GEBIETE||0}</div><div class="lbl">Gebiete</div></div>
      <div class="stat-card">
        <div class="val" style="font-size:1.2rem">${(s.ERSTE||'–').substring(0,4)}</div>
        <div class="lbl">Erste Begehung</div>
      </div>
      <div class="stat-card">
        <div class="val" style="font-size:1.2rem">${(s.LETZTE||'–').substring(0,4)}</div>
        <div class="lbl">Letzte Begehung</div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <h3>Begehungen pro Jahr</h3>
        <canvas id="chart-years" height="180"></canvas>
      </div>
      <div class="chart-card">
        <h3>Gradverteilung</h3>
        <canvas id="chart-grades" height="180"></canvas>
      </div>
      <div class="chart-card">
        <h3>Top Seilpartner</h3>
        <canvas id="chart-partners" height="180"></canvas>
      </div>
      <div class="chart-card">
        <h3>Meistbesuchte Gebiete</h3>
        <canvas id="chart-areas" height="180"></canvas>
      </div>
    </div>
  `;

  // Destroy old charts to avoid canvas reuse errors
  Object.values(charts).forEach(c => c.destroy());
  charts = {};

  const chartDefaults = {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#8a8a9a', font: { size: 11 } }, grid: { color: '#2a2a4a' } },
      y: { ticks: { color: '#8a8a9a', font: { size: 11 } }, grid: { color: '#2a2a4a' } },
    },
  };

  // Years
  charts.years = new Chart(document.getElementById('chart-years'), {
    type: 'bar',
    data: {
      labels: stats.per_year.map(r => r.JAHR),
      datasets: [{ data: stats.per_year.map(r => r.N), backgroundColor: '#e94560' }],
    },
    options: chartDefaults,
  });

  // Grades
  charts.grades = new Chart(document.getElementById('chart-grades'), {
    type: 'bar',
    data: {
      labels: stats.grade_dist.map(r => r.GRAD),
      datasets: [{ data: stats.grade_dist.map(r => r.N), backgroundColor: '#f5a623' }],
    },
    options: chartDefaults,
  });

  // Partners
  charts.partners = new Chart(document.getElementById('chart-partners'), {
    type: 'bar',
    data: {
      labels: stats.top_partners.map(r => r.NAME),
      datasets: [{ data: stats.top_partners.map(r => r.N), backgroundColor: '#4caf50' }],
    },
    options: { ...chartDefaults, indexAxis: 'y' },
  });

  // Areas
  charts.areas = new Chart(document.getElementById('chart-areas'), {
    type: 'bar',
    data: {
      labels: stats.areas_visited.map(r => r.GEBIET),
      datasets: [{ data: stats.areas_visited.map(r => r.N_BEGEHUNGEN), backgroundColor: '#0f3460' }],
    },
    options: { ...chartDefaults, indexAxis: 'y' },
  });
}

// ── Boot ─────────────────────────────────────────────────────────────────────

document.querySelector('nav button[data-tab="gebiete"]').click();
