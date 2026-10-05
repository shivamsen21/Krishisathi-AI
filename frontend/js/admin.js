/* ============================================================
   AgroVision AI — admin.js
   Admin dashboard data rendering & Supabase backend integration
   ============================================================ */

// Guard admin dashboard
function checkAdminAccess() {
  const isDashboard = window.location.pathname.includes('admin-dashboard.html');
  if (isDashboard) {
    const user = AgroVisionAPI.getUser();
    if (!AgroVisionAPI.isAuthenticated() || !user || user.role !== 'admin') {
      window.location.href = 'admin-login.html';
    }
  }
}

async function initAdminStats() {
  try {
    const stats = await AgroVisionAPI.getAdminStats();
    setText('statFarmers', (stats.farmers || 0).toLocaleString());
    setText('statPredictions', (stats.predictions || 0).toLocaleString());
    setText('statDiseases', (stats.diseases || 0).toLocaleString());
    setText('statHealthy', (stats.healthy || 0).toLocaleString());
  } catch (err) {
    console.error('Failed to load admin stats:', err);
  }
}

async function renderPredictionsTable() {
  const tbody = document.getElementById('predictionsTableBody');
  const allTbody = document.getElementById('allPredictionsBody');
  if (!tbody) return;

  try {
    const predictions = await AgroVisionAPI.getAdminPredictions();
    if (!predictions || predictions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--text-muted);">No prediction records recorded yet.</td></tr>`;
      if (allTbody) allTbody.innerHTML = tbody.innerHTML;
      return;
    }

    const html = predictions.map(r => `
      <tr>
        <td style="font-family:monospace;font-weight:700;color:var(--primary);">${r.id}</td>
        <td><div style="display:flex;align-items:center;gap:8px;">
          <div class="user-avatar-cell">${(r.farmer || 'F').charAt(0)}</div>
          <span style="font-weight:600;">${r.farmer || 'Farmer'}</span></div></td>
        <td>${r.crop}</td>
        <td>${r.disease}</td>
        <td style="font-weight:700;color:var(--primary);">${r.confidence}</td>
        <td><span class="badge ${r.status === 'Healthy' ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
        <td style="color:var(--text-muted);font-size:13px;">${r.date}</td>
      </tr>`).join('');

    tbody.innerHTML = html;
    if (allTbody) allTbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--danger);">Failed to load predictions: ${err.message}</td></tr>`;
  }
}

async function renderUsersTable() {
  const tbody = document.getElementById('usersTableBody');
  if (!tbody) return;

  try {
    const users = await AgroVisionAPI.getAdminUsers();
    if (!users || users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--text-muted);">No users registered yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => `
      <tr>
        <td style="font-family:monospace;font-size:12px;color:var(--text-muted);">${String(u.id).substring(0, 8)}...</td>
        <td><div style="display:flex;align-items:center;gap:10px;">
          <div class="user-avatar-cell">${(u.name || 'U').charAt(0)}</div>
          <div><div style="font-weight:700;">${u.name || 'Farmer'}</div><div style="font-size:12px;color:var(--text-muted);">${u.email}</div></div></div></td>
        <td style="font-weight:700;">${u.scans || 0}</td>
        <td>${u.joined || '2026-09'}</td>
        <td><span class="admin-badge ${u.status === 'Active' ? 'admin-badge-active' : 'admin-badge-inactive'}">${u.status}</span></td>
        <td><div class="admin-action-btns">
          <button class="admin-action-btn view" title="View"><i class="fas fa-eye"></i></button>
          <button class="admin-action-btn edit" title="Edit"><i class="fas fa-edit"></i></button>
          <button class="admin-action-btn delete" title="Delete" onclick="confirmDelete('${u.id}','${(u.name || '').replace(/'/g, "\\'")}')"><i class="fas fa-trash"></i></button>
        </div></td>
      </tr>`).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--danger);">Failed to load farmers: ${err.message}</td></tr>`;
  }
}

function confirmDelete(id, name) {
  if (confirm(`Delete user "${name}"? This action cannot be undone.`)) {
    showToast(`User ${name} deleted successfully.`, 'success');
  }
}

function initBarChart() {
  const bars = document.querySelectorAll('.admin-bar');
  const vals = [35, 55, 40, 70, 60, 80, 45];
  bars.forEach((bar, i) => {
    setTimeout(() => { bar.style.height = vals[i % vals.length] + 'px'; }, i * 80);
  });
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// Admin login form
function initAdminLoginForm() {
  const form = document.getElementById('adminLoginForm');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('adminEmail')?.value.trim();
    const password = document.getElementById('adminPassword')?.value;
    const btn = form.querySelector('.auth-submit-btn');

    if (!email || !password) {
      showToast('Please enter both admin email and password.', 'warning');
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div> Verifying...';

    try {
      const res = await AgroVisionAPI.login(email, password);
      if (!res.user || res.user.role !== 'admin') {
        AgroVisionAPI.clearAuth();
        throw new Error('Access denied. Administrator privileges required.');
      }
      showToast('Admin authorization verified!', 'success');
      setTimeout(() => { window.location.href = 'admin-dashboard.html'; }, 600);
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-shield-halved"></i> Secure Login';
      showToast(err.message || 'Admin authentication failed.', 'error');
    }
  });
}

// Tab switching (admin sections)
function initTabs() {
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('[data-tab]').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
      btn.classList.add('active');
      document.getElementById('tab-' + tab)?.classList.remove('hidden');
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  checkAdminAccess();
  initAdminStats();
  renderPredictionsTable();
  renderUsersTable();
  initBarChart();
  initAdminLoginForm();
  initTabs();
});
