/* ============================================================
   AgroVision AI — dashboard.js
   Dashboard data rendering: Supabase farmer metrics & detections
   ============================================================ */

const CROP_EMOJIS = {
  'Tomato': '🍅',
  'Wheat': '🌾',
  'Potato': '🥔',
  'Rice': '🌾',
  'Corn': '🌽',
  'Cotton': '🌱'
};

async function renderDashboard() {
  // Update user name in sidebar / nav if logged in
  const user = AgroVisionAPI.getUser();
  if (user && user.full_name) {
    const userNames = document.querySelectorAll('.sidebar-user-name');
    userNames.forEach(el => el.textContent = user.full_name);
    const avatars = document.querySelectorAll('.sidebar-avatar');
    avatars.forEach(el => el.textContent = user.full_name.charAt(0).toUpperCase());
  }

  let detections = [];
  try {
    const items = await AgroVisionAPI.getHistory({ limit: 10 });
    if (items && items.length > 0) {
      detections = items.map(d => ({
        id: d.id,
        crop: d.crop || 'Tomato',
        emoji: CROP_EMOJIS[d.crop] || '🌿',
        disease: d.disease || 'Leaf Scan',
        status: d.status || (String(d.disease).toLowerCase().includes('healthy') ? 'Healthy' : 'Diseased'),
        date: d.created_at ? d.created_at.substring(0, 10) : 'Today'
      }));
    }
  } catch (err) {
    console.warn('Dashboard history fetch error:', err);
  }

  renderRecentDetections(detections);
  renderStatCards(detections);
}

function renderRecentDetections(detections) {
  const container = document.getElementById('recentDetections');
  if (!container) return;

  if (!detections || detections.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:30px;color:var(--text-muted);">
        <i class="fas fa-leaf" style="font-size:28px;margin-bottom:10px;opacity:0.4;"></i>
        <p>No leaf scans performed yet.</p>
        <a href="detection.html" class="btn btn-primary btn-sm" style="margin-top:10px;display:inline-block;">Start First Scan</a>
      </div>`;
    return;
  }

  container.innerHTML = detections.slice(0, 5).map(d => `
    <div class="detection-item">
      <div class="detection-thumb">${d.emoji}</div>
      <div class="detection-info">
        <div class="detection-crop">${d.crop}</div>
        <div class="detection-disease">${d.disease}</div>
      </div>
      <div class="detection-meta">
        <span class="badge ${d.status === 'Healthy' ? 'badge-success' : 'badge-danger'}">${d.status}</span>
        <div class="detection-date">${d.date}</div>
      </div>
    </div>`).join('');
}

function renderStatCards(detections) {
  const totalScans = detections.length;
  const healthyCount = detections.filter(d => d.status === 'Healthy').length;
  const diseaseCount = totalScans - healthyCount;

  const stats = [
    { id: 'statScans',     value: totalScans > 0 ? String(totalScans) : '0' },
    { id: 'statDiseases',  value: totalScans > 0 ? String(diseaseCount) : '0' },
    { id: 'statHealthy',   value: totalScans > 0 ? String(healthyCount) : '0' },
    { id: 'statLast',      value: totalScans > 0 ? 'Recent' : '—' },
  ];
  stats.forEach(({ id, value }) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  });
}

function animateChartBars() {
  const bars = document.querySelectorAll('.chart-bar');
  const heights = [40, 65, 50, 80, 55, 70, 45];
  bars.forEach((bar, i) => {
    setTimeout(() => {
      bar.style.height = (heights[i % heights.length]) + 'px';
    }, i * 100);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  renderDashboard();
  animateChartBars();
});
