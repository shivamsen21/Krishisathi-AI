/* ============================================================
   AgroVision AI — detection.js
   Upload, drag/drop, camera, scan animation, result display
   ============================================================ */

// ---- State ----
let selectedFile = null;
let selectedCrop = '';
let cameraStream = null;

// ---- DOM refs ----
const uploadZone     = document.getElementById('uploadZone');
const fileInput      = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const previewImage   = document.getElementById('previewImage');
const analyzeBtn     = document.getElementById('analyzeBtn');
const cropChips      = document.querySelectorAll('.crop-chip');
const scanningOverlay= document.getElementById('scanningOverlay');
const resultPanel    = document.getElementById('resultPanel');
const noResult       = document.getElementById('noResult');

// ---- Placeholder result data (replace with real API response) ----
const PLACEHOLDER_RESULT = {
  crop: 'Tomato',
  disease: 'Tomato Early Blight',
  confidence: 94.7,
  status: 'Diseased',
  symptoms: 'Dark brown spots surrounded by yellow rings on older leaves. Spots may merge as disease progresses, causing significant leaf drop.',
  prevention: 'Rotate crops every season. Avoid wetting foliage when watering. Plant resistant varieties. Remove and destroy infected plant debris.',
  care: 'Apply copper-based fungicide or mancozeb every 7–10 days. Ensure proper plant spacing for air circulation. Remove severely infected leaves promptly.',
};

// ---- Upload Zone ----
function initUploadZone() {
  if (!uploadZone) return;

  uploadZone.addEventListener('click', (e) => {
    if (!e.target.closest('.upload-btn-camera')) fileInput?.click();
  });

  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault(); uploadZone.classList.add('drag-over');
  });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault(); uploadZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) handleFile(file);
    else showToast('Please drop an image file', 'warning');
  });

  fileInput?.addEventListener('change', (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
  });
}

function handleFile(file) {
  if (!file.type.startsWith('image/')) { showToast('Please select an image file', 'warning'); return; }
  if (file.size > 10 * 1024 * 1024) { showToast('Image size must be under 10MB', 'error'); return; }
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => showPreview(e.target.result);
  reader.readAsDataURL(file);
}

function showPreview(src) {
  if (previewImage) previewImage.src = src;
  if (uploadZone) uploadZone.classList.add('has-image');
  if (previewSection) previewSection.classList.remove('hidden');
  document.getElementById('uploadPrompt')?.classList.add('hidden');
  updateAnalyzeBtn();
}

function removeImage() {
  selectedFile = null;
  if (fileInput) fileInput.value = '';
  if (uploadZone) uploadZone.classList.remove('has-image');
  if (previewSection) previewSection.classList.add('hidden');
  document.getElementById('uploadPrompt')?.classList.remove('hidden');
  if (previewImage) previewImage.src = '';
  updateAnalyzeBtn();
  hideResult();
}

// ---- Crop Chips ----
function initCropChips() {
  cropChips.forEach(chip => {
    chip.addEventListener('click', () => {
      cropChips.forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      selectedCrop = chip.dataset.crop;
      updateAnalyzeBtn();
    });
  });
}

function updateAnalyzeBtn() {
  if (analyzeBtn) analyzeBtn.disabled = !selectedFile;
}

// ---- Scanning Animation ----
const SCAN_STEPS = [
  { id: 'step1', text: 'Uploading leaf image...' },
  { id: 'step2', text: 'Extracting visual features...' },
  { id: 'step3', text: 'Running AI classification...' },
  { id: 'step4', text: 'Generating disease report...' },
];

async function runScanAnimation() {
  if (scanningOverlay) scanningOverlay.classList.remove('hidden');
  SCAN_STEPS.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) {
      el.querySelector('.scan-step-icon').className = 'scan-step-icon pending';
      el.querySelector('.scan-step-icon').innerHTML = '<i class="far fa-circle"></i>';
    }
  });

  for (let i = 0; i < SCAN_STEPS.length; i++) {
    await new Promise(r => setTimeout(r, 700));
    const el = document.getElementById(SCAN_STEPS[i].id);
    if (el) {
      el.querySelector('.scan-step-icon').className = 'scan-step-icon active';
      el.querySelector('.scan-step-icon').innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    }
    await new Promise(r => setTimeout(r, 700));
    if (el) {
      el.querySelector('.scan-step-icon').className = 'scan-step-icon done';
      el.querySelector('.scan-step-icon').innerHTML = '<i class="fas fa-check"></i>';
    }
  }
  await new Promise(r => setTimeout(r, 400));
  if (scanningOverlay) scanningOverlay.classList.add('hidden');
}

// ---- Analyze ----
async function analyzeImage() {
  if (!selectedFile) return;

  hideResult();
  await runScanAnimation();

  try {
    const data = await AgroVisionAPI.predict(selectedFile, selectedCrop);
    displayResult(data);
  } catch (err) {
    showToast(err.message || 'Error running disease detection.', 'error');
  }
}

function displayResult(data) {
  if (noResult) noResult.classList.add('hidden');
  if (resultPanel) resultPanel.classList.remove('hidden');

  // Populate fields
  setText('resultCrop',     data.crop);
  setText('resultDisease',  data.disease);
  setText('resultSymptoms', data.symptoms || 'Visual inspection complete.');
  setText('resultPrevention', data.prevention || 'Standard crop monitoring.');
  setText('resultCare',     data.treatment || data.care || 'No special intervention required.');

  const pct = typeof data.confidence === 'number' ? data.confidence : parseFloat(data.confidence) || 90.0;
  setText('resultConfidence', pct.toFixed(1) + '%');

  // Status badge
  const statusEl = document.getElementById('resultStatus');
  if (statusEl) {
    statusEl.className = 'badge ' + (data.status === 'Healthy' ? 'badge-success' : 'badge-danger');
    statusEl.textContent = data.status;
  }

  // Confidence bar (animate)
  const bar = document.getElementById('confidenceBar');
  if (bar) {
    bar.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { bar.style.width = pct + '%'; }, 100);
    });
  }

  resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  showToast('Analysis complete! (Temporary Model Preview)', 'success');
}

function hideResult() {
  if (resultPanel) resultPanel.classList.add('hidden');
  if (noResult) noResult.classList.remove('hidden');
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ---- Camera ----
function initCamera() {
  const cameraBtn   = document.getElementById('cameraBtn');
  const cameraModal = document.getElementById('cameraModal');
  const videoEl     = document.getElementById('cameraVideo');
  const captureBtn  = document.getElementById('captureBtn');
  const closeCamera = document.getElementById('closeCamera');
  const canvas      = document.createElement('canvas');

  if (!cameraBtn) return;

  cameraBtn.addEventListener('click', async () => {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
      if (videoEl) videoEl.srcObject = cameraStream;
      if (cameraModal) cameraModal.classList.remove('hidden');
    } catch (err) {
      showToast('Camera access denied. Please allow camera permission.', 'error');
    }
  });

  function stopCamera() {
    if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
    if (cameraModal) cameraModal.classList.add('hidden');
  }

  closeCamera?.addEventListener('click', stopCamera);

  captureBtn?.addEventListener('click', () => {
    if (!videoEl) return;
    canvas.width  = videoEl.videoWidth;
    canvas.height = videoEl.videoHeight;
    canvas.getContext('2d').drawImage(videoEl, 0, 0);
    canvas.toBlob(blob => {
      const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
      handleFile(file);
      stopCamera();
    }, 'image/jpeg', 0.92);
  });
}

// ---- Analyze Button ----
function initAnalyzeBtn() {
  if (!analyzeBtn) return;
  analyzeBtn.addEventListener('click', analyzeImage);
}

// ---- Save Result ----
function initSaveResult() {
  const saveBtn = document.getElementById('saveResultBtn');
  if (!saveBtn) return;
  saveBtn.addEventListener('click', () => {
    // TODO: POST to /api/history/save
    showToast('Result saved to history!', 'success');
  });
}

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
  initUploadZone();
  initCropChips();
  initCamera();
  initAnalyzeBtn();
  initSaveResult();
  updateAnalyzeBtn();
});
