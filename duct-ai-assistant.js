const API_BASES = [
  window.DUCT_AI_BACKEND_URL || 'https://api.interiorductltd.com',
  'https://duct-ai-backend.onrender.com',
  'https://interior-ecommerce-lh3e.onrender.com'
];
const CHAT_PATH = '/ai-query';
const TRACK_PATH = '/user-log';
const SESSION_STORAGE_KEY = 'duct_ai_session_id';

async function fetchWithBackendFallback(path, options = {}) {
  let lastError = null;
  for (const base of API_BASES) {
    const url = `${base.replace(/\/$/, '')}${path}`;
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        lastError = new Error(`Backend request failed (${response.status}) ${response.statusText} @ ${url}: ${errorText}`);
        continue;
      }
      return response;
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error('All backend endpoints failed');
}

function getDuctAiSessionId() {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

async function sendDuctAiChat(userMessage) {
  const sessionId = getDuctAiSessionId();
  const payload = {
    query: userMessage,
    session_id: sessionId,
    page: window.location.pathname,
    user_agent: navigator.userAgent
  };

  try {
    const response = await fetchWithBackendFallback(CHAT_PATH, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Duct AI chat send error:', error);
    throw error;
  }
}

async function sendBehaviourEvent(eventData) {
  const sessionId = getDuctAiSessionId();
  const payload = {
    ...eventData,
    session_id: sessionId,
  };

  try {
    await fetchWithBackendFallback(TRACK_PATH, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
  } catch (error) {
    console.warn('Behaviour tracking failed:', error);
  }
}

function initBehaviourTracking() {
  const page = window.location.pathname;

  sendBehaviourEvent({
    event: 'page_view',
    page,
  });

  let heartbeatSeconds = 0;
  setInterval(() => {
    heartbeatSeconds += 30;
    sendBehaviourEvent({
      event: 'heartbeat',
      page,
      seconds: heartbeatSeconds,
    });
  }, 30000);

  document.addEventListener('click', (event) => {
    const productCard = event.target.closest('.pcard');
    if (productCard && productCard.dataset.productName) {
      sendBehaviourEvent({
        event: 'product_view',
        product_name: productCard.dataset.productName,
      });
    }
  });
}

window.addEventListener('DOMContentLoaded', initBehaviourTracking);
window.sendDuctAiChat = sendDuctAiChat;

