/* ============================================================
   AgroVision AI — assistant.js
   Krishi AI Chatbot frontend (placeholder responses)
   ============================================================ */

const SUGGESTED = [
  "My tomato leaves have brown spots. What should I do?",
  "How can I prevent fungal diseases in crops?",
  "How often should I water wheat crops?",
  "What are common potato diseases?",
  "When is the best time to spray pesticides?",
  "How do I improve soil health naturally?",
];

// Placeholder AI responses mapped to keywords
const BOT_RESPONSES = [
  { keywords: ['tomato','brown','spot','blight'], reply: "Brown spots on tomato leaves are often caused by <strong>Early Blight</strong> (Alternaria solani). 🍅\n\n<b>Immediate steps:</b>\n• Remove severely affected leaves\n• Apply copper-based fungicide\n• Avoid overhead watering\n• Ensure proper plant spacing for air circulation\n\nIf spots have yellow halos, it could be Septoria Leaf Spot — consider uploading a leaf image for AI detection!" },
  { keywords: ['fungal','prevent','disease'],      reply: "Great question! Here are proven methods to prevent fungal diseases: 🌿\n\n<b>Cultural practices:</b>\n• Rotate crops every season\n• Use disease-resistant varieties\n• Avoid overwatering and waterlogging\n• Remove plant debris after harvest\n\n<b>Chemical control:</b>\n• Apply preventive fungicides (copper, mancozeb)\n• Start early in the growing season\n\n<b>Biological control:</b>\n• Use Trichoderma-based biofungicides" },
  { keywords: ['water','wheat','irrigat'],         reply: "Wheat has specific water needs at different growth stages: 🌾\n\n<b>Critical stages for irrigation:</b>\n1. Crown root initiation (20-25 days after sowing)\n2. Tillering stage (40-45 days)\n3. Jointing stage (65-70 days)\n4. Grain filling stage (90-95 days)\n\nGenerally, wheat requires <strong>4-6 irrigations</strong> depending on soil type and climate. Sandy soils need more frequent watering." },
  { keywords: ['potato','disease'],               reply: "Common potato diseases include: 🥔\n\n1. <strong>Late Blight</strong> — Water-soaked dark spots; use metalaxyl fungicide\n2. <strong>Early Blight</strong> — Dark concentric rings; apply chlorothalonil\n3. <strong>Potato Scab</strong> — Rough corky lesions on tubers; maintain soil pH 5.0–5.2\n4. <strong>Black Leg</strong> — Stem blackening; use certified disease-free seed\n\nUpload a leaf image for precise AI-based disease identification!" },
  { keywords: ['spray','pesticide','when','time'], reply: "Best practices for pesticide application: ⏰\n\n<b>Timing:</b>\n• Early morning (6–9 AM) or late evening (4–6 PM)\n• Avoid hot midday hours to prevent evaporation\n• Do not spray when rain is expected within 6 hours\n\n<b>Conditions:</b>\n• Wind speed below 10 km/h\n• Temperature below 30°C\n• Relative humidity above 40%\n\n<b>Safety:</b> Always wear protective gear and follow label instructions." },
  { keywords: ['soil','health','improve','organic'],reply: "Improving soil health naturally: 🌱\n\n1. <strong>Add organic matter</strong> — Compost, farmyard manure, green manure\n2. <strong>Crop rotation</strong> — Break pest/disease cycles\n3. <strong>Mulching</strong> — Conserves moisture, reduces weeds\n4. <strong>Biofertilizers</strong> — Rhizobium, Azotobacter, Mycorrhiza\n5. <strong>Minimize tillage</strong> — Preserve soil structure and microbes\n6. <strong>Cover crops</strong> — Legumes fix nitrogen naturally" },
];

const DEFAULT_RESPONSE = "Thank you for your question! 🌿 I'm here to help with crop diseases and farming problems.\n\nFor accurate disease identification, I recommend uploading a clear leaf image to our <a href='detection.html' style='color:var(--primary);font-weight:600;'>AI Detection tool</a>.\n\nCould you provide more details about:\n• Which crop are you growing?\n• What symptoms are you seeing?\n• How long has the problem been there?";

let messages = [];
let isTyping = false;

function getResponse(userMsg) {
  const lower = userMsg.toLowerCase();
  for (const r of BOT_RESPONSES) {
    if (r.keywords.some(k => lower.includes(k))) return r.reply;
  }
  return DEFAULT_RESPONSE;
}

function renderMessage(role, text, time) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const isUser = role === 'user';
  const initials = isUser ? 'You' : '🌱';
  const formattedText = text.replace(/\n/g, '<br>');

  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.innerHTML = `
    <div class="msg-avatar ${role}">${isUser ? 'YOU' : '🌱'}</div>
    <div>
      <div class="msg-bubble">${formattedText}</div>
      <span class="msg-time">${time}</span>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showTyping() {
  const container = document.getElementById('chatMessages');
  if (!container) return;
  const div = document.createElement('div');
  div.className = 'message bot typing-indicator';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="msg-avatar bot">🌱</div>
    <div class="typing-dots">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function hideTyping() {
  document.getElementById('typingIndicator')?.remove();
}

function nowTime() {
  return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

async function sendMessage(text) {
  if (isTyping || !text.trim()) return;
  const input = document.getElementById('chatInput');
  if (input) input.value = '';
  adjustTextarea(input);

  renderMessage('user', text.trim(), nowTime());
  messages.push({ role: 'user', text });

  isTyping = true;
  document.getElementById('sendBtn')?.setAttribute('disabled', true);

  showTyping();

  let reply = '';
  try {
    const data = await AgroVisionAPI.chat(text);
    reply = data.reply;
  } catch (err) {
    console.warn('Using local assistant fallback:', err);
    reply = getResponse(text);
  } finally {
    hideTyping();
  }

  renderMessage('bot', reply, nowTime());
  messages.push({ role: 'bot', text: reply });

  isTyping = false;
  document.getElementById('sendBtn')?.removeAttribute('disabled');
}

function adjustTextarea(el) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function clearChat() {
  messages = [];
  const container = document.getElementById('chatMessages');
  if (!container) return;
  container.innerHTML = '';
  sendWelcomeMessage();
}

function sendWelcomeMessage() {
  setTimeout(() => renderMessage('bot', 'Hello, Farmer! 👋 I am <strong>Krishi AI</strong> — your agricultural assistant.\n\nI can help you with:\n• 🍃 Crop disease identification\n• 💧 Irrigation and watering advice\n• 🌱 Soil health and fertilization\n• 🌾 Pest control and prevention\n\nHow can I help you today?', nowTime()), 300);
}

function renderSuggestions() {
  const container = document.getElementById('suggestedList');
  if (!container) return;
  container.innerHTML = SUGGESTED.map(s =>
    `<div class="suggested-item" onclick="sendMessage('${s.replace(/'/g, "\\'")}')">${s}</div>`
  ).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  renderSuggestions();
  sendWelcomeMessage();

  const sendBtn = document.getElementById('sendBtn');
  const input   = document.getElementById('chatInput');

  sendBtn?.addEventListener('click', () => {
    if (input) sendMessage(input.value);
  });

  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input.value);
    }
  });

  input?.addEventListener('input', () => adjustTextarea(input));

  document.getElementById('clearChatBtn')?.addEventListener('click', clearChat);
});
