// Pocket PC - Windows Mobile 6 style shell for ESP32-S3
const $ = (id) => document.getElementById(id);
const content = $('content'), startMenu = $('startMenu');
let current = 'today', sys = {}, notes = [];

const api = async (path, opt = {}) => {
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error(await r.text());
  const t = await r.text();
  try { return JSON.parse(t); } catch { return t; }
};
const put = (path, body) => api(path, { method: 'PUT', body: typeof body === 'string' ? body : JSON.stringify(body) });
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const kb = (n) => (n >= 1048576 ? (n / 1048576).toFixed(1) + ' MB' : (n / 1024).toFixed(1) + ' KB');

// ---------- chrome ----------
function setSoft(l, lf, r, rf) {
  $('softL').textContent = l || ''; $('softL').onclick = lf || null;
  $('softR').textContent = r || ''; $('softR').onclick = rf || null;
}
function setTitle(t) { $('appTitle').textContent = t; }
function tickClock() {
  const d = new Date();
  $('clock').textContent = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}
setInterval(tickClock, 1000); tickClock();

function ask(title, msg, val = '', type = 'text') {
  return new Promise((res) => {
    $('dTitle').textContent = title; $('dMsg').textContent = msg;
    const i = $('dInput'); i.type = type; i.value = val;
    $('dialogWrap').hidden = false; i.focus();
    const done = (v) => { $('dialogWrap').hidden = true; res(v); };
    $('dOk').onclick = () => done(i.value);
    $('dCancel').onclick = () => done(null);
  });
}

// ---------- start menu ----------
const APPS = [
  { id: 'today', name: 'Today', icon: '🏠' },
  { id: 'chat', name: 'Messenger', icon: '💬' },
  { id: 'browser', name: 'Internet Explorer', icon: '🌐' },
  { id: 'notes', name: 'Notes', icon: '📝' },
  { id: 'files', name: 'File Explorer', icon: '📁' },
  { id: 'wifi', name: 'Wi-Fi', icon: '📶' },
  { id: 'calc', name: 'Calculator', icon: '🧮' },
  { id: 'about', name: 'Settings › About', icon: '⚙️' },
];
startMenu.innerHTML = APPS.map((a) => `<div class="it" data-id="${a.id}"><span class="ic">${a.icon}</span>${a.name}</div>`).join('');
startMenu.onclick = (e) => { const it = e.target.closest('.it'); if (it) open(it.dataset.id); };
$('startBtn').onclick = () => (startMenu.hidden = !startMenu.hidden);

function open(id) {
  startMenu.hidden = true;
  current = id;
  clearInterval(pollTimer);
  ({ today, notes: notesApp, files, wifi, calc, about, chat, browser }[id])();
}

// ---------- data ----------
async function refreshSys() {
  try { sys = await api('/api/sys'); $('sig').style.opacity = sys.staConnected || sys.clients ? 1 : 0.4; } catch { $('sig').style.opacity = 0.2; }
}
async function loadNotes() { try { notes = await api('/api/notes'); } catch { notes = []; } }
const saveNotes = () => put('/api/notes', notes);

// ---------- Today ----------
async function today() {
  setTitle('Today'); setSoft('Calendar', null, 'Menu', () => (startMenu.hidden = false));
  await Promise.all([refreshSys(), loadNotes()]);
  const d = new Date();
  const owner = localStorage.getItem('owner') || 'Tap to enter owner information';
  content.innerHTML = `<div class="today">
    <div class="date">${d.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })}</div>
    <div class="time">${d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</div>
    <div class="trow" id="owner"><span class="ic">👤</span><div>${esc(owner)}</div></div>
    <div class="trow" data-go="wifi"><span class="ic">📶</span><div>${sys.staConnected ? esc(sys.staSsid) : 'Access point mode'}<div class="sub">${sys.staConnected ? sys.staIp : sys.apIp} · ${sys.clients ?? 0} connected</div></div></div>
    <div class="trow" data-go="notes"><span class="ic">📝</span><div>${notes.length} note${notes.length === 1 ? '' : 's'}<div class="sub">Tap to open Notes</div></div></div>
    <div class="trow" data-go="about"><span class="ic">🔋</span><div>Memory ${kb(sys.heapFree || 0)} free<div class="sub">PSRAM ${kb(sys.psramFree || 0)} free</div></div></div>
    <div class="trow"><span class="ic">📅</span><div>No upcoming appointments</div></div>
  </div>`;
  $('owner').onclick = async () => {
    const v = await ask('Owner Information', 'Name:', localStorage.getItem('owner') || '');
    if (v !== null) { localStorage.setItem('owner', v); today(); }
  };
  content.querySelectorAll('[data-go]').forEach((el) => (el.onclick = () => open(el.dataset.go)));
}

// ---------- Notes ----------
async function notesApp() {
  setTitle('Notes'); await loadNotes();
  setSoft('New', () => editNote(-1), 'Menu', async () => {
    if (!notes.length) return;
    const v = await ask('Delete all', 'Type YES to delete every note.');
    if (v === 'YES') { notes = []; await saveNotes(); notesApp(); }
  });
  if (!notes.length) { content.innerHTML = '<div class="empty">No notes.<br>Tap New to create one.</div>'; return; }
  content.innerHTML = '<div class="hdr">All Folders ▾</div><div class="list">' + notes.map((n, i) =>
    `<div data-i="${i}"><span>${esc((n.text.split('\n')[0] || 'Untitled').slice(0, 40))}</span><span class="sub">${new Date(n.t).toLocaleDateString()}</span></div>`).join('') + '</div>';
  content.querySelectorAll('.list>div').forEach((el) => (el.onclick = () => editNote(+el.dataset.i)));
}
function editNote(i) {
  setTitle('Notes');
  content.innerHTML = `<textarea class="ed" id="ed" placeholder="Start typing..."></textarea>`;
  const ed = $('ed'); ed.value = i >= 0 ? notes[i].text : ''; ed.focus();
  setSoft('OK', async () => {
    const text = ed.value.trim();
    if (text) {
      if (i >= 0) notes[i] = { text, t: Date.now() }; else notes.unshift({ text, t: Date.now() });
      await saveNotes();
    }
    notesApp();
  }, i >= 0 ? 'Delete' : 'Cancel', async () => {
    if (i >= 0) { notes.splice(i, 1); await saveNotes(); }
    notesApp();
  });
}

// ---------- Files ----------
async function files() {
  setTitle('File Explorer'); setSoft('Up', () => open('today'), 'Menu', null);
  const list = await api('/api/files');
  content.innerHTML = '<div class="hdr">Internal Storage ▾</div><div class="list">' + list.map((f) =>
    `<div data-n="${esc(f.name)}"><span>${f.dir ? '📁' : '📄'} ${esc(f.name.slice(1))}</span><span class="sub">${kb(f.size)}</span></div>`).join('') + '</div>';
  content.querySelectorAll('.list>div').forEach((el) => (el.onclick = () => fileView(el.dataset.n)));
}
async function fileView(name) {
  setTitle(name.slice(1));
  const hidden = name === '/wifi.json';
  const txt = hidden ? '(hidden)' : await api('/api/file?path=' + encodeURIComponent(name));
  content.innerHTML = `<textarea class="ed" id="ed" ${hidden ? 'readonly' : ''}></textarea>`;
  $('ed').value = typeof txt === 'string' ? txt : JSON.stringify(txt, null, 2);
  setSoft('Save', async () => { if (!hidden) await put('/api/file?path=' + encodeURIComponent(name), $('ed').value); files(); },
    'Delete', async () => { await api('/api/file?path=' + encodeURIComponent(name), { method: 'DELETE' }); files(); });
}

// ---------- Wi-Fi ----------
async function wifi() {
  setTitle('Wireless Manager'); setSoft('Scan', wifi, 'Back', () => open('today'));
  content.innerHTML = '<div class="empty">Scanning…</div>';
  let nets = [];
  try { nets = await api('/api/scan'); } catch {}
  content.innerHTML = '<div class="hdr">Available networks</div><div class="list">' + (nets.map((n, i) =>
    `<div data-i="${i}"><span>${n.open ? '' : '🔒 '}${esc(n.ssid || '(hidden)')}</span><span class="sub">${n.rssi} dBm</span></div>`).join('') || '<div class="empty">None found</div>') + '</div>';
  content.querySelectorAll('.list>div[data-i]').forEach((el) => (el.onclick = async () => {
    const n = nets[+el.dataset.i];
    const pass = n.open ? '' : await ask('Connect', `Password for ${n.ssid}:`, '', 'password');
    if (pass === null) return;
    setTitle('Connecting…');
    try {
      const r = await api('/api/connect', { method: 'POST', body: JSON.stringify({ ssid: n.ssid, pass }) });
      await ask(r.ok ? 'Connected' : 'Failed', r.ok ? `IP address: ${r.ip}` : 'Could not connect.');
    } catch { await ask('Failed', 'Could not connect.'); }
    wifi();
  }));
}

// ---------- Calculator ----------
function calc() {
  setTitle('Calculator'); setSoft('', null, 'Back', () => open('today'));
  const keys = ['C', '±', '%', '÷', '7', '8', '9', '×', '4', '5', '6', '−', '1', '2', '3', '+', '0', '.', '⌫', '='];
  content.innerHTML = '<div class="calc"><div class="disp" id="cd">0</div>' + keys.map((k) => `<button class="${'÷×−+='.includes(k) ? 'op' : ''}">${k}</button>`).join('') + '</div>';
  let expr = '';
  const cd = $('cd');
  const show = () => (cd.textContent = expr || '0');
  content.querySelectorAll('button').forEach((b) => (b.onclick = () => {
    const k = b.textContent;
    if (k === 'C') expr = '';
    else if (k === '⌫') expr = expr.slice(0, -1);
    else if (k === '±') expr = expr.startsWith('-') ? expr.slice(1) : expr ? '-' + expr : '';
    else if (k === '%') { try { expr = String(parseFloat(expr) / 100); } catch {} }
    else if (k === '=') {
      const e = expr.replace(/÷/g, '/').replace(/×/g, '*').replace(/−/g, '-');
      if (/^[0-9+\-*/.() ]+$/.test(e)) { try { expr = String(Function('"use strict";return (' + e + ')')()); } catch { expr = 'Error'; } }
    } else { if (expr === 'Error') expr = ''; expr += k; }
    show();
  }));
}

// ---------- About ----------
async function about() {
  setTitle('About'); setSoft('OK', () => open('today'), 'Reboot', async () => {
    if ((await ask('Reboot', 'Type YES to restart the device.')) === 'YES') { try { await api('/api/reboot', { method: 'POST' }); } catch {} }
  });
  await refreshSys();
  const row = (k, v) => `<div class="kv"><b>${k}</b><span>${v}</span></div>`;
  const bar = (used, total) => `<div class="bar"><i style="width:${total ? Math.round((used / total) * 100) : 0}%"></i></div>`;
  const s = sys;
  content.innerHTML = '<div class="hdr">Device information</div>' +
    row('Processor', `${s.model} · ${s.cores} cores · ${s.mhz} MHz`) +
    row('Temperature', (s.tempC || 0).toFixed(1) + ' °C') +
    row('Uptime', Math.floor((s.uptime || 0) / 60) + ' min') +
    row('Program memory', `${kb(s.heapTotal - s.heapFree)} / ${kb(s.heapTotal)}`) + bar(s.heapTotal - s.heapFree, s.heapTotal) +
    row('PSRAM', `${kb(s.psramTotal - s.psramFree)} / ${kb(s.psramTotal)}`) + bar(s.psramTotal - s.psramFree, s.psramTotal) +
    row('Storage', `${kb(s.fsUsed)} / ${kb(s.fsTotal)}`) + bar(s.fsUsed, s.fsTotal) +
    row('AP address', s.apIp) + row('Network', s.staConnected ? `${esc(s.staSsid)} (${s.staIp})` : 'Not connected');
}

// ---------- Messenger (everyone connected to this board shares one chat) ----------
var pollTimer = null;
async function chat() {
  setTitle('Messenger');
  setSoft('Name', async () => {
    const v = await ask('Your name', 'Shown next to your messages:', localStorage.getItem('chatName') || '');
    if (v !== null && v.trim()) localStorage.setItem('chatName', v.trim().slice(0, 20));
  }, 'Back', () => open('today'));
  let name = localStorage.getItem('chatName');
  if (!name) {
    const v = await ask('Your name', 'Pick a name for Messenger:', '');
    name = (v || 'Guest').trim().slice(0, 20) || 'Guest';
    localStorage.setItem('chatName', name);
  }
  content.innerHTML = '<div class="chat"><div class="msgs" id="msgs"><div class="empty">No messages yet.</div></div>' +
    '<div class="sendrow"><input id="msgIn" placeholder="Type a message" maxlength="500" autocomplete="off"><button id="msgSend">Send</button></div></div>';
  const box = $('msgs'), input = $('msgIn');
  let since = 0, first = true;
  const draw = (m) => {
    const me = m.from === localStorage.getItem('chatName');
    const el = document.createElement('div');
    el.className = 'm' + (me ? ' me' : '');
    const who = document.createElement('div'); who.className = 'who'; who.textContent = m.from;
    const tx = document.createElement('div'); tx.textContent = m.text;
    const tm = document.createElement('div'); tm.className = 'tm';
    tm.textContent = new Date(m.t * 1000).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    el.append(who, tx, tm); box.appendChild(el);
  };
  const poll = async () => {
    if (current !== 'chat') return;
    try {
      const r = await api('/api/chat?since=' + since);
      if (r.msgs.length) {
        if (first) box.innerHTML = '';
        const stick = box.scrollTop + box.clientHeight >= box.scrollHeight - 40;
        r.msgs.forEach(draw);
        if (stick || first) box.scrollTop = box.scrollHeight;
        first = false;
      }
      since = r.last;
    } catch {}
  };
  const send = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    try {
      await api('/api/chat', { method: 'POST', body: JSON.stringify({ from: localStorage.getItem('chatName'), text }) });
      await poll();
      box.scrollTop = box.scrollHeight;
    } catch { input.value = text; }
    input.focus();
  };
  $('msgSend').onclick = send;
  input.onkeydown = (e) => { if (e.key === 'Enter') send(); };
  await poll();
  pollTimer = setInterval(poll, 2000);
}

// ---------- Internet Explorer (text-mode; the board fetches pages for you) ----------
const HOME = [
  ['DuckDuckGo search', 'https://html.duckduckgo.com/html/'],
  ['Wikipedia (mobile)', 'https://en.m.wikipedia.org'],
  ['NPR text news', 'https://text.npr.org'],
  ['Hacker News', 'https://news.ycombinator.com'],
  ['Example.com', 'http://example.com'],
];
const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME', 'SVG', 'IMG', 'VIDEO', 'AUDIO', 'CANVAS', 'FORM', 'INPUT', 'BUTTON', 'SELECT', 'TEXTAREA', 'HEAD', 'TEMPLATE', 'OBJECT', 'EMBED']);
const BLOCK = new Set(['P', 'DIV', 'SECTION', 'ARTICLE', 'HEADER', 'FOOTER', 'MAIN', 'ASIDE', 'NAV', 'TABLE', 'TR', 'UL', 'OL', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'PRE', 'BLOCKQUOTE', 'DL', 'DT', 'DD', 'FIGURE', 'BR', 'HR']);
const KEEP = new Set(['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'UL', 'OL', 'LI', 'PRE', 'BLOCKQUOTE', 'B', 'STRONG', 'I', 'EM']);
let hist = [], hi = -1;

// Builds a safe copy of the remote page: only whitelisted tags, text via textContent,
// and links stored as data attributes (never raw remote HTML in this origin).
function safeCopy(src, dst, base) {
  for (const n of src.childNodes) {
    if (n.nodeType === 3) { dst.appendChild(document.createTextNode(n.textContent)); continue; }
    if (n.nodeType !== 1 || SKIP.has(n.tagName.toUpperCase())) continue;
    const tag = n.tagName.toUpperCase();
    let out = dst;
    if (tag === 'A') {
      let href = '';
      try { href = new URL(n.getAttribute('href') || '', base).href; } catch {}
      if (/^https?:/i.test(href)) { out = document.createElement('a'); out.dataset.href = href; out.href = '#'; dst.appendChild(out); }
    } else if (KEEP.has(tag)) {
      out = document.createElement(tag.toLowerCase()); dst.appendChild(out);
    } else if (BLOCK.has(tag)) {
      out = document.createElement('div'); dst.appendChild(out);
    }
    safeCopy(n, out, base);
  }
}

function browser() {
  setTitle('Internet Explorer');
  content.innerHTML = '<div class="browser"><div class="sendrow"><input id="url" placeholder="Search or enter address" autocapitalize="off" autocorrect="off" autocomplete="off"><button id="go">Go</button></div>' +
    '<div class="page" id="page"></div></div>';
  setSoft('Back', () => (hi > 0 ? (hi--, load(hist[hi], true)) : home()), 'Home', home);
  $('go').onclick = () => go($('url').value);
  $('url').onkeydown = (e) => { if (e.key === 'Enter') go($('url').value); };
  if (hi >= 0) load(hist[hi], true); else home();
}
function home() {
  $('url').value = '';
  $('page').innerHTML = '<div class="hdr">Favorites</div><div class="list">' + HOME.map((h, i) => `<div data-i="${i}"><span>🌐 ${h[0]}</span></div>`).join('') +
    '</div><div class="empty">Text-only browser. The board must be joined to a Wi-Fi network with internet (Wireless Manager).</div>';
  $('page').querySelectorAll('.list>div').forEach((el) => (el.onclick = () => go(HOME[+el.dataset.i][1])));
}
function go(input) {
  let u = input.trim();
  if (!u) return;
  if (!/^https?:\/\//i.test(u)) u = /\s/.test(u) || !u.includes('.') ? 'https://html.duckduckgo.com/html/?q=' + encodeURIComponent(u) : 'https://' + u;
  hist = hist.slice(0, hi + 1); hist.push(u); hi = hist.length - 1;
  load(u, true);
}
async function load(u, fromHist) {
  const page = $('page'); $('url').value = u; setTitle('Loading…');
  page.innerHTML = '<div class="empty">Loading…</div>';
  try {
    const r = await fetch('/api/browse?url=' + encodeURIComponent(u));
    const html = await r.text();
    if (!r.ok) { page.innerHTML = ''; const d = document.createElement('div'); d.className = 'empty'; d.textContent = html; page.appendChild(d); setTitle('Internet Explorer'); return; }
    const doc = new DOMParser().parseFromString(html, 'text/html');
    page.innerHTML = '';
    const wrap = document.createElement('div'); wrap.className = 'doc';
    safeCopy(doc.body || doc, wrap, u);
    page.appendChild(wrap);
    if (!wrap.textContent.trim()) wrap.textContent = '(This page has no readable text.)';
    wrap.onclick = (e) => { const a = e.target.closest('a'); if (a && a.dataset.href) { e.preventDefault(); go(a.dataset.href); } };
    page.scrollTop = 0;
    setTitle((doc.title || u).slice(0, 40));
  } catch (e) {
    page.innerHTML = ''; const d = document.createElement('div'); d.className = 'empty'; d.textContent = 'Could not load the page.'; page.appendChild(d);
    setTitle('Internet Explorer');
  }
}

// ---------- boot ----------
document.addEventListener('click', (e) => { if (!startMenu.hidden && !e.target.closest('#startMenu,#startBtn')) startMenu.hidden = true; });
api('/api/time', { method: 'POST', body: JSON.stringify({ epoch: Math.floor(Date.now() / 1000) }) }).catch(() => {});
today();
setInterval(() => { if (current === 'today' && $('dialogWrap').hidden) today(); }, 30000);
