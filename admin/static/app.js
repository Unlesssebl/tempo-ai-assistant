// ═══════════════════════════════════════════════════
//   iTEMPO Admin Panel — Frontend Logic
// ═══════════════════════════════════════════════════

const API = '';  // Same origin
let authToken = localStorage.getItem('admin_token') || '';
let currentPage = 'dashboard';
let usersOffset = 0;
let logsOffset = 0;
const PAGE_SIZE = 50;

// Companies dict (будет загружен с сервера или захардкожен)
const COMPANIES = {
  'itz': 'АО "ИТЗ"',
  'kmk': 'АО "КМК "ТЭМПО"',
  'ntz': 'АО "НТЗ "ТЭМ-ПО"',
  'technotron': 'АО "ПТФК "Технотрон"',
  'metiz': 'ООО "Технотрон-Метиз"',
  'kzmk': 'АО "КЗМК "ТЭМПО"',
  'zteo': 'АО "ПТФК "ЗТЭО"',
  'td': 'АО "ТД "ТЭМПО"',
  'sks': 'АО "СКС "ТЭМПО"',
  'port': 'ООО "ТЭМПО-ПОРТ"',
  'it': 'ООО "АЙТИ "ТЭМПО"',
};

// ── Auth ──────────────────────────────────────────────────────────────────

async function doLogin(e) {
  e.preventDefault();
  const pw = document.getElementById('loginPassword').value;
  const btn = document.getElementById('loginBtn');
  btn.disabled = true;
  btn.innerHTML = '<span>Вход...</span>';

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({password: pw}),
    });
    if (res.ok) {
      const data = await res.json();
      authToken = data.token;
      localStorage.setItem('admin_token', authToken);
      showApp();
    } else {
      document.getElementById('loginError').classList.remove('hidden');
    }
  } catch(err) {
    document.getElementById('loginError').textContent = 'Ошибка соединения';
    document.getElementById('loginError').classList.remove('hidden');
  }
  btn.disabled = false;
  btn.innerHTML = '<span>Войти</span>';
}

async function doLogout() {
  await fetch('/api/auth/logout', {method: 'POST'});
  localStorage.removeItem('admin_token');
  authToken = '';
  document.getElementById('mainApp').classList.add('hidden');
  document.getElementById('loginScreen').classList.remove('hidden');
}

async function checkAuth() {
  if (!authToken) return false;
  try {
    const res = await apiFetch('/api/auth/check');
    return res && res.authenticated;
  } catch(e) {
    return false;
  }
}

function showApp() {
  document.getElementById('loginScreen').classList.add('hidden');
  document.getElementById('mainApp').classList.remove('hidden');
  // Заполняем селекты компаниями
  populateCompanySelects();
  // Загружаем начальную страницу
  loadDashboard();
}

// ── API Helpers ───────────────────────────────────────────────────────────

async function apiFetch(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'Cookie': `admin_token=${authToken}`,
    ...(options.headers || {}),
  };
  // Добавляем токен в cookie через Authorization header
  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers,
  });
  if (res.status === 401) {
    doLogout();
    return null;
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({error: 'Ошибка сервера'}));
    throw new Error(err.error || 'Ошибка запроса');
  }
  return res.json();
}

// ── Navigation ────────────────────────────────────────────────────────────

function showPage(name, navEl) {
  // Скрываем все страницы
  document.querySelectorAll('.page').forEach(p => {
    p.classList.remove('active');
    p.classList.add('hidden');
  });
  // Снимаем активный класс
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // Показываем нужную
  const page = document.getElementById(`page${capitalize(name)}`);
  if (page) {
    page.classList.remove('hidden');
    page.classList.add('active');
  }
  if (navEl) navEl.classList.add('active');
  currentPage = name;

  // Загрузка данных
  const loaders = {
    dashboard: loadDashboard,
    users: loadUsers,
    logs: loadLogs,
    documents: loadDocuments,
    broadcast: () => {},
    keys: loadKeys,
  };
  if (loaders[name]) loaders[name]();
  return false;
}

function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ── Dashboard ─────────────────────────────────────────────────────────────

let weeklyChart = null;
let hourlyChart = null;

async function loadDashboard() {
  try {
    const data = await apiFetch('/api/stats');
    if (!data) return;

    // Stats cards
    animateNumber('statTotalMsg', data.total_messages || 0);
    animateNumber('statTodayMsg', data.today_messages || 0);
    animateNumber('statTotalUsers', data.total_users || 0);
    animateNumber('statActiveToday', data.active_today || 0);

    // Bot status
    updateBotStatus('tg', data.tg_status);
    updateBotStatus('max', data.max_status);

    // Charts
    renderWeeklyChart(data.daily || []);
    renderHourlyChart(data.hourly || []);

  } catch(e) {
    toast('Ошибка загрузки дашборда: ' + e.message, 'error');
  }
}

function updateBotStatus(bot, status) {
  const badge = document.getElementById(`${bot}Badge`);
  const dot = document.getElementById(`${bot}StatusDot`);
  const text = document.getElementById(`${bot}StatusText`);
  if (badge) {
    badge.textContent = status === 'online' ? '🟢 Работает' : '🔴 Офлайн';
    badge.className = `status-badge ${status}`;
  }
  if (dot) {
    dot.className = `status-dot ${status}`;
  }
}

function animateNumber(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  const diff = target - start;
  const steps = 30;
  let step = 0;
  const timer = setInterval(() => {
    step++;
    el.textContent = Math.round(start + diff * (step / steps)).toLocaleString('ru');
    if (step >= steps) clearInterval(timer);
  }, 16);
}

function renderWeeklyChart(daily) {
  const ctx = document.getElementById('weeklyChart');
  if (!ctx) return;
  if (weeklyChart) weeklyChart.destroy();

  const labels = daily.map(d => {
    const dt = new Date(d.day);
    return dt.toLocaleDateString('ru', {day: 'numeric', month: 'short'});
  });
  const values = daily.map(d => d.count);

  weeklyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: 'rgba(79,156,249,0.5)',
        borderColor: 'rgba(79,156,249,1)',
        borderWidth: 2,
        borderRadius: 4,
      }]
    },
    options: getChartOptions('Запросов'),
  });
}

function renderHourlyChart(hourly) {
  const ctx = document.getElementById('hourlyChart');
  if (!ctx) return;
  if (hourlyChart) hourlyChart.destroy();

  const labels = hourly.map(h => {
    const dt = new Date(h.ts * 1000);
    return dt.toLocaleTimeString('ru', {hour: '2-digit', minute: '2-digit'});
  });
  const values = hourly.map(h => h.count);

  hourlyChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: '#a78bfa',
        backgroundColor: 'rgba(167,139,250,0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: '#a78bfa',
      }]
    },
    options: getChartOptions('Запросов'),
  });
}

function getChartOptions(label) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1a2035',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#e2e8f0',
        bodyColor: '#94a3b8',
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: { color: '#4a5568', font: { size: 11 } }
      },
      y: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: { color: '#4a5568', font: { size: 11 } },
        beginAtZero: true,
      }
    }
  };
}

// ── Users ─────────────────────────────────────────────────────────────────

let allUsers = [];

async function loadUsers() {
  usersOffset = 0;
  try {
    const data = await apiFetch(`/api/users?limit=200`);
    if (!data) return;
    allUsers = data.users || [];
    renderUsersTable(allUsers);
  } catch(e) {
    document.getElementById('usersBody').innerHTML = `<tr><td colspan="6" class="loading-cell">Ошибка: ${e.message}</td></tr>`;
  }
}

function filterUsers() {
  const q = document.getElementById('userSearch').value.toLowerCase();
  const filtered = allUsers.filter(u =>
    u.user_id.toLowerCase().includes(q) ||
    (u.company_id || '').toLowerCase().includes(q) ||
    (u.company_name || '').toLowerCase().includes(q)
  );
  renderUsersTable(filtered);
}

function renderUsersTable(users) {
  const tbody = document.getElementById('usersBody');
  if (!users.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">Нет пользователей</td></tr>';
    return;
  }
  tbody.innerHTML = users.map(u => {
    const blocked = u.is_blocked;
    const lastActivity = u.last_activity
      ? new Date(u.last_activity * 1000).toLocaleString('ru', {day:'2-digit',month:'2-digit',year:'2-digit',hour:'2-digit',minute:'2-digit'})
      : '—';
    const platform = u.platform || '?';
    const platformTag = platform === 'telegram'
      ? `<span class="tag tag-tg">TG</span>`
      : platform === 'max'
      ? `<span class="tag tag-max">MAX</span>`
      : `<span class="tag">${platform}</span>`;

    return `
      <tr>
        <td><code style="font-size:12px">${u.user_id}</code></td>
        <td>${platformTag}</td>
        <td>${u.company_name || '—'}</td>
        <td style="font-size:12px">${lastActivity}</td>
        <td>
          ${blocked ? '<span class="tag" style="background:rgba(248,113,113,0.15);color:#f87171">🚫 Блок</span>'
                    : '<span class="tag" style="background:rgba(52,211,153,0.15);color:#34d399">✓ Активен</span>'}
        </td>
        <td>
          <div class="cell-actions">
            <button class="btn btn-ghost btn-sm" onclick="showUserModal('${u.user_id}', '${u.company_id || ''}', ${blocked})">⚙️</button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

function showUserModal(userId, currentCompany, isBlocked) {
  const companyOptions = Object.entries(COMPANIES).map(([k,v]) =>
    `<option value="${k}" ${k===currentCompany?'selected':''}>${v}</option>`
  ).join('');

  document.getElementById('modalTitle').textContent = `Пользователь ${userId}`;
  document.getElementById('modalBody').innerHTML = `
    <div class="form-group">
      <label>Предприятие</label>
      <select class="select-input" id="modalCompany">
        <option value="">— Не выбрано —</option>
        ${companyOptions}
      </select>
    </div>
    <p style="font-size:13px;color:var(--text-secondary);margin-top:8px;">
      Статус: ${isBlocked ? '🚫 Заблокирован' : '✓ Активен'}
    </p>
  `;
  document.getElementById('modalFooter').innerHTML = `
    <button class="btn btn-ghost" onclick="closeModal()">Отмена</button>
    ${isBlocked
      ? `<button class="btn btn-secondary" onclick="doUnblock('${userId}')">✓ Разблокировать</button>`
      : `<button class="btn btn-danger" onclick="doBlock('${userId}')">🚫 Заблокировать</button>`
    }
    <button class="btn btn-danger btn-sm" onclick="doClearHistory('${userId}')">🗑 Очистить историю</button>
    <button class="btn btn-primary" onclick="doSetCompany('${userId}')">💾 Сохранить</button>
  `;
  document.getElementById('modalOverlay').classList.remove('hidden');
}

async function doSetCompany(userId) {
  const companyId = document.getElementById('modalCompany').value;
  try {
    await apiFetch(`/api/users/${userId}/company`, {
      method: 'POST',
      body: JSON.stringify({company_id: companyId}),
    });
    toast('Предприятие обновлено', 'success');
    closeModal();
    loadUsers();
  } catch(e) { toast(e.message, 'error'); }
}

async function doBlock(userId) {
  try {
    await apiFetch(`/api/users/${userId}/block`, {method: 'POST'});
    toast('Пользователь заблокирован', 'success');
    closeModal();
    loadUsers();
  } catch(e) { toast(e.message, 'error'); }
}

async function doUnblock(userId) {
  try {
    await apiFetch(`/api/users/${userId}/unblock`, {method: 'POST'});
    toast('Пользователь разблокирован', 'success');
    closeModal();
    loadUsers();
  } catch(e) { toast(e.message, 'error'); }
}

async function doClearHistory(userId) {
  if (!confirm(`Очистить историю диалога пользователя ${userId}?`)) return;
  try {
    await apiFetch(`/api/users/${userId}/history`, {method: 'DELETE'});
    toast('История очищена', 'success');
    closeModal();
  } catch(e) { toast(e.message, 'error'); }
}

// ── Logs ──────────────────────────────────────────────────────────────────

async function loadLogs() {
  logsOffset = 0;
  await searchLogs();
}

async function searchLogs() {
  const search = document.getElementById('logSearch')?.value || '';
  const platform = document.getElementById('logPlatform')?.value || '';
  const params = new URLSearchParams({limit: PAGE_SIZE, offset: logsOffset});
  if (search) params.set('search', search);
  if (platform) params.set('platform', platform);

  try {
    const data = await apiFetch(`/api/logs?${params}`);
    if (!data) return;
    renderLogsTable(data.logs || []);
    renderLogsPagination(data.total || 0);
  } catch(e) {
    document.getElementById('logsBody').innerHTML = `<tr><td colspan="5" class="loading-cell">Ошибка: ${e.message}</td></tr>`;
  }
}

function renderLogsTable(logs) {
  const tbody = document.getElementById('logsBody');
  if (!logs.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="loading-cell">Нет записей</td></tr>';
    return;
  }
  tbody.innerHTML = logs.map(log => {
    const time = log.timestamp
      ? new Date(log.timestamp * 1000).toLocaleString('ru', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})
      : '—';
    const roleTag = log.role === 'user'
      ? '<span class="tag tag-user">Пользователь</span>'
      : '<span class="tag tag-assistant">Ассистент</span>';
    const platformTag = log.platform === 'telegram'
      ? '<span class="tag tag-tg">TG</span>'
      : `<span class="tag tag-max">${log.platform}</span>`;
    const msg = escapeHtml(log.message || '').substring(0, 150);
    return `
      <tr>
        <td style="font-size:11px;white-space:nowrap">${time}</td>
        <td><code style="font-size:11px">${log.session_id}</code></td>
        <td>${platformTag}</td>
        <td>${roleTag}</td>
        <td><span class="msg-preview" title="${escapeHtml(log.message||'')}">${msg}</span></td>
      </tr>`;
  }).join('');
}

function renderLogsPagination(total) {
  const pages = Math.ceil(total / PAGE_SIZE);
  const current = Math.floor(logsOffset / PAGE_SIZE);
  const el = document.getElementById('logsPagination');
  if (!el || pages <= 1) { if(el) el.innerHTML=''; return; }

  let html = `<span>${total} записей</span>`;
  html += `<button class="page-btn" onclick="logsGoPage(${Math.max(0,current-1)})">‹</button>`;
  for (let i = Math.max(0, current-2); i <= Math.min(pages-1, current+2); i++) {
    html += `<button class="page-btn ${i===current?'active':''}" onclick="logsGoPage(${i})">${i+1}</button>`;
  }
  html += `<button class="page-btn" onclick="logsGoPage(${Math.min(pages-1,current+1)})">›</button>`;
  el.innerHTML = html;
}

function logsGoPage(page) {
  logsOffset = page * PAGE_SIZE;
  searchLogs();
}

async function exportLogs() {
  window.location.href = '/api/logs/export';
}

// ── Documents ─────────────────────────────────────────────────────────────

let selectedFile = null;
let docMode = 'file';

async function loadDocuments() {
  const loading = document.getElementById('docsLoading');
  const grid = document.getElementById('docsGrid');
  if (loading) loading.classList.remove('hidden');
  if (grid) grid.innerHTML = '';

  try {
    const data = await apiFetch('/api/documents');
    if (!data) return;
    if (loading) loading.classList.add('hidden');

    const docs = data.documents || [];
    if (!docs.length) {
      if (grid) grid.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted)">Документы не найдены</div>';
      return;
    }

    if (grid) {
      grid.innerHTML = docs.map(doc => {
        const isCommon = !doc.company;
        const size = doc.size < 1024 ? `${doc.size} B` : doc.size < 1048576 ? `${(doc.size/1024).toFixed(1)} KB` : `${(doc.size/1048576).toFixed(1)} MB`;
        const modified = doc.modified ? new Date(doc.modified * 1000).toLocaleDateString('ru') : '';
        return `
          <div class="doc-card">
            <div>
              <span class="company-badge ${isCommon?'common':''}">${doc.company_name}</span>
            </div>
            <div class="doc-name">📄 ${doc.name}</div>
            <div class="doc-meta">${size} · ${modified}</div>
            <div class="doc-meta" style="font-size:11px;color:var(--text-muted)">${doc.path}</div>
            <div class="doc-actions">
              <button class="btn btn-danger btn-sm" onclick="deleteDocument('${escapeHtml(doc.path)}')">🗑</button>
            </div>
          </div>`;
      }).join('');
    }
  } catch(e) {
    if (loading) loading.textContent = 'Ошибка: ' + e.message;
  }
}

function showDocUpload() {
  document.getElementById('docUploadPanel').classList.remove('hidden');
  document.getElementById('docPreviewSection').classList.add('hidden');
}

function hideDocUpload() {
  document.getElementById('docUploadPanel').classList.add('hidden');
  selectedFile = null;
}

function switchDocTab(mode, btn) {
  docMode = mode;
  document.querySelectorAll('#docUploadPanel .tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('docTabFile').classList.toggle('hidden', mode !== 'file');
  document.getElementById('docTabText').classList.toggle('hidden', mode !== 'text');
}

function fileSelected() {
  const input = document.getElementById('fileInput');
  selectedFile = input.files[0];
  if (selectedFile) {
    const el = document.getElementById('selectedFile');
    el.textContent = `📎 ${selectedFile.name} (${(selectedFile.size/1024).toFixed(1)} KB)`;
    el.classList.remove('hidden');
  }
}

function handleDrop(e) {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (file) {
    selectedFile = file;
    const el = document.getElementById('selectedFile');
    el.textContent = `📎 ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
    el.classList.remove('hidden');
  }
}

async function previewDocument() {
  const btn = document.getElementById('previewBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Обрабатываю...';

  try {
    const formData = new FormData();
    const companyId = document.getElementById('docCompany').value;
    const title = document.getElementById('docTitle').value;

    if (docMode === 'file' && selectedFile) {
      formData.append('file', selectedFile);
    } else if (docMode === 'text') {
      const text = document.getElementById('docTextContent').value;
      if (!text.trim()) { toast('Введите текст', 'error'); return; }
      formData.append('text_content', text);
    } else {
      toast('Выберите файл или введите текст', 'error');
      return;
    }
    if (companyId) formData.append('company_id', companyId);
    if (title) formData.append('doc_title', title);

    const res = await fetch('/api/documents/preview', {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Ошибка обработки');
    }
    const data = await res.json();

    document.getElementById('docPreview').value = data.preview || '';
    document.getElementById('docFilename').value = data.suggested_filename || 'document.md';
    document.getElementById('docPreviewSection').classList.remove('hidden');
    document.getElementById('saveResult').classList.add('hidden');
    toast('ИИ обработал документ. Проверьте и отредактируйте.', 'info');
  } catch(e) {
    toast('Ошибка: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 Обработать через ИИ';
  }
}

async function saveDocument() {
  const content = document.getElementById('docPreview').value;
  const filename = document.getElementById('docFilename').value;
  const company_id = document.getElementById('docCompany').value || null;

  if (!content.trim()) { toast('Содержимое пустое', 'error'); return; }

  try {
    const data = await apiFetch('/api/documents/save', {
      method: 'POST',
      body: JSON.stringify({content, filename, company_id}),
    });
    const el = document.getElementById('saveResult');
    el.textContent = data.message;
    el.className = 'success';
    el.classList.remove('hidden');
    toast('Документ сохранён!', 'success');
    setTimeout(loadDocuments, 2000);
  } catch(e) {
    const el = document.getElementById('saveResult');
    el.textContent = 'Ошибка: ' + e.message;
    el.className = 'error';
    el.classList.remove('hidden');
  }
}

async function deleteDocument(path) {
  if (!confirm(`Удалить документ "${path}"?\nПереиндексация потребуется.`)) return;
  try {
    await apiFetch('/api/documents', {
      method: 'DELETE',
      body: JSON.stringify({path}),
    });
    toast('Документ удалён', 'success');
    loadDocuments();
  } catch(e) { toast(e.message, 'error'); }
}

// ── Broadcast ─────────────────────────────────────────────────────────────

function previewBroadcast() {
  const text = document.getElementById('broadcastText').value;
  const preview = document.getElementById('broadcastPreview');
  if (!text.trim()) {
    preview.innerHTML = '<div class="preview-placeholder">Введите текст сообщения</div>';
    return;
  }
  preview.innerHTML = `<div class="tg-preview">${text}</div>`;
}

async function sendBroadcast() {
  const text = document.getElementById('broadcastText').value;
  if (!text.trim()) { toast('Введите текст', 'error'); return; }

  const platform = document.getElementById('broadcastPlatform').value;
  const company_id = document.getElementById('broadcastCompany').value || null;
  const activeDays = document.getElementById('broadcastDays').value;

  const btn = document.getElementById('sendBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Отправляю...';

  try {
    const body = {text, platform};
    if (company_id) body.company_id = company_id;
    if (activeDays) body.active_days = parseInt(activeDays);

    const data = await apiFetch('/api/broadcast', {method: 'POST', body: JSON.stringify(body)});
    const el = document.getElementById('broadcastResult');
    el.innerHTML = `✅ Отправлено: <b>${data.sent}</b> из <b>${data.total_targeted}</b> пользователей${data.failed ? ` (ошибок: ${data.failed})` : ''}`;
    el.className = 'broadcast-result success';
    el.classList.remove('hidden');
    toast(`Рассылка завершена: ${data.sent} сообщений`, 'success');
  } catch(e) {
    const el = document.getElementById('broadcastResult');
    el.textContent = 'Ошибка: ' + e.message;
    el.className = 'broadcast-result error';
    el.classList.remove('hidden');
    toast('Ошибка рассылки', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '📨 Отправить';
  }
}

// ── API Keys ──────────────────────────────────────────────────────────────

async function loadKeys() {
  try {
    const data = await apiFetch('/api/keys');
    if (!data) return;
    const el = document.getElementById('keysBody');
    if (!data.keys.length) {
      el.innerHTML = '<div class="loading-cell">Ключи не найдены</div>';
      return;
    }
    el.innerHTML = `<div class="keys-list">` + data.keys.map(k => `
      <div class="key-item">
        <div class="key-info">
          <span class="key-index">#${k.index + 1}</span>
          <span class="key-value">${k.masked}</span>
        </div>
        ${k.is_active ? '<span class="key-active">● Активный</span>' : ''}
      </div>
    `).join('') + `</div>`;
  } catch(e) {
    document.getElementById('keysBody').innerHTML = `<div class="loading-cell">Ошибка: ${e.message}</div>`;
  }
}

// ── Modal ─────────────────────────────────────────────────────────────────

function closeModal() {
  document.getElementById('modalOverlay').classList.add('hidden');
}

// ── Toast ─────────────────────────────────────────────────────────────────

function toast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(20px)'; }, 3000);
  setTimeout(() => el.remove(), 3300);
}

// ── Helpers ───────────────────────────────────────────────────────────────

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function populateCompanySelects() {
  const selects = ['docCompany', 'broadcastCompany'];
  selects.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const defaultOpt = el.options[0];
    el.innerHTML = '';
    if (defaultOpt) el.appendChild(defaultOpt);
    Object.entries(COMPANIES).forEach(([k,v]) => {
      const opt = document.createElement('option');
      opt.value = k; opt.textContent = v;
      el.appendChild(opt);
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────

(async function init() {
  const authenticated = await checkAuth();
  if (authenticated) {
    showApp();
  }
  // Автообновление дашборда каждые 60 секунд
  setInterval(() => {
    if (currentPage === 'dashboard') loadDashboard();
  }, 60000);
})();
