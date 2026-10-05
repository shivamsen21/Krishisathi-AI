/* ============================================================
   AgroVision AI — history.js
   Detection history: Supabase data, render, filter, search, modal
   ============================================================ */

const CROP_EMOJIS = {
  'Tomato': '🍅',
  'Wheat': '🌾',
  'Potato': '🥔',
  'Rice': '🌾',
  'Corn': '🌽',
  'Cotton': '🌱'
};

const PAGE_SIZE = 5;
let currentPage = 1;
let HISTORY_DATA = [];
let filtered = [];

function formatDate(d) {
  if (!d) return '—';
  const date = new Date(d);
  if (isNaN(date.getTime())) return d;
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

async function loadHistory() {
  const tbody = document.getElementById('historyTableBody');
  if (tbody) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading history from Supabase...</td></tr>`;
  }

  try {
    const items = await AgroVisionAPI.getHistory({ limit: 100 });
    if (items && items.length > 0) {
      HISTORY_DATA = items.map((item, idx) => ({
        id: item.id || String(idx + 1),
        crop: item.crop || 'Tomato',
        emoji: CROP_EMOJIS[item.crop] || '🌿',
        disease: item.disease || 'Analyzed Leaf',
        confidence: typeof item.confidence === 'number' ? item.confidence : parseFloat(item.confidence) || 90.0,
        status: item.status || (String(item.disease).toLowerCase().includes('healthy') ? 'Healthy' : 'Diseased'),
        date: item.created_at ? item.created_at.substring(0, 10) : new Date().toISOString().substring(0, 10),
        symptoms: item.symptoms || 'Visual leaf assessment recorded.',
        prevention: item.prevention || 'Standard crop monitoring and balanced nutrition.',
        care: item.treatment || 'No chemical treatment necessary.'
      }));
    } else {
      HISTORY_DATA = [];
    }
  } catch (err) {
    console.warn('History load notice:', err.message);
    HISTORY_DATA = [];
  }

  filtered = [...HISTORY_DATA];
  renderTable();
}

function renderTable() {
  const tbody = document.getElementById('historyTableBody');
  const countEl = document.getElementById('historyCount');
  if (!tbody) return;

  const start = (currentPage - 1) * PAGE_SIZE;
  const page  = filtered.slice(start, start + PAGE_SIZE);

  if (countEl) countEl.innerHTML = `Showing <strong>${filtered.length}</strong> detection${filtered.length !== 1 ? 's' : ''}`;

  if (page.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-state-icon">🔍</div><h3>No records found</h3><p>Upload a leaf in Disease Detection to view scans here.</p></div></td></tr>`;
    renderPagination();
    return;
  }

  tbody.innerHTML = page.map(r => `
    <tr>
      <td>${formatDate(r.date)}</td>
      <td>
        <div class="history-crop-cell">
          <div class="history-image">${r.emoji}</div>
          <div>
            <div class="history-crop-name">${r.crop}</div>
          </div>
        </div>
      </td>
      <td>${r.disease}</td>
      <td>
        <div class="confidence-bar-wrap" style="min-width:120px;">
          <div class="confidence-bar-track" style="flex:1;">
            <div class="confidence-bar-fill" style="width:${r.confidence}%;"></div>
          </div>
          <span style="font-size:13px;font-weight:700;color:var(--primary);min-width:42px;">${r.confidence.toFixed(1)}%</span>
        </div>
      </td>
      <td><span class="badge ${r.status === 'Healthy' ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
      <td><button class="view-btn" onclick="openDetailModal('${r.id}')"><i class="fas fa-eye"></i> View</button></td>
    </tr>`).join('');

  renderPagination();
}

function renderPagination() {
  const pag = document.getElementById('pagination');
  if (!pag) return;
  const total = Math.ceil(filtered.length / PAGE_SIZE);
  let html = `<button class="page-btn" onclick="goPage(${currentPage - 1})" ${currentPage <= 1 ? 'disabled' : ''}><i class="fas fa-chevron-left"></i></button>`;
  for (let i = 1; i <= total; i++) {
    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goPage(${i})">${i}</button>`;
  }
  html += `<button class="page-btn" onclick="goPage(${currentPage + 1})" ${currentPage >= total || total === 0 ? 'disabled' : ''}><i class="fas fa-chevron-right"></i></button>`;
  pag.innerHTML = html;
}

function goPage(n) {
  const total = Math.ceil(filtered.length / PAGE_SIZE);
  if (n < 1 || n > total) return;
  currentPage = n;
  renderTable();
}

function applyFilters() {
  const search  = document.getElementById('searchInput')?.value.toLowerCase() || '';
  const crop    = document.getElementById('cropFilter')?.value || '';
  const status  = document.getElementById('statusFilter')?.value || '';
  const month   = document.getElementById('dateFilter')?.value || '';

  filtered = HISTORY_DATA.filter(r => {
    const matchSearch = !search || r.crop.toLowerCase().includes(search) || r.disease.toLowerCase().includes(search);
    const matchCrop   = !crop   || r.crop === crop;
    const matchStatus = !status || r.status === status;
    const matchMonth  = !month  || r.date.startsWith(month);
    return matchSearch && matchCrop && matchStatus && matchMonth;
  });
  currentPage = 1;
  renderTable();
}

function openDetailModal(id) {
  const r = HISTORY_DATA.find(x => String(x.id) === String(id));
  if (!r) return;
  const modal = document.getElementById('detailModal');
  if (!modal) return;

  document.getElementById('modalCrop').textContent     = r.crop;
  document.getElementById('modalDisease').textContent   = r.disease;
  document.getElementById('modalDate').textContent      = formatDate(r.date);
  document.getElementById('modalConfidence').textContent= r.confidence.toFixed(1) + '%';
  document.getElementById('modalStatus').innerHTML      = `<span class="badge ${r.status === 'Healthy' ? 'badge-success' : 'badge-danger'}">${r.status}</span>`;
  document.getElementById('modalSymptoms').textContent  = r.symptoms;
  document.getElementById('modalPrevention').textContent= r.prevention;
  document.getElementById('modalCare').textContent      = r.care;
  const bar = document.getElementById('modalConfBar');
  if (bar) { bar.style.width = '0%'; setTimeout(() => bar.style.width = r.confidence + '%', 100); }
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeDetailModal() {
  const modal = document.getElementById('detailModal');
  if (modal) modal.classList.add('hidden');
  document.body.style.overflow = '';
}

function resetFilters() {
  ['searchInput','cropFilter','statusFilter','dateFilter'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  filtered = [...HISTORY_DATA];
  currentPage = 1;
  renderTable();
}

document.addEventListener('DOMContentLoaded', () => {
  loadHistory();
  ['searchInput','cropFilter','statusFilter','dateFilter'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', applyFilters);
    document.getElementById(id)?.addEventListener('change', applyFilters);
  });
  document.getElementById('resetFilters')?.addEventListener('click', resetFilters);
  document.getElementById('closeModal')?.addEventListener('click', closeDetailModal);
  document.getElementById('detailModal')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeDetailModal();
  });
});
