const API_BASES = [
  (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:5000'
    : window.DUCT_AI_BACKEND_URL || 'https://duct-ai-backend.onrender.com',
  'https://duct-ai-backend.onrender.com',
  'https://interior-ecommerce-backend.onrender.com',
  'https://interior-ecommerce-lh3e.onrender.com'
];
const CHAT_PATH = '/ai-query';
const TRACK_PATH = '/user-log';
const SESSION_STORAGE_KEY = 'duct_ai_session_id';

function getDuctAiSessionId() {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

function isWeakChatResponse(data) {
  if (!data) return true;
  const text = String(data.answer || data.reply || '').trim();
  const provider = String(data.provider || '').toLowerCase();
  if (data.escalate && !text) return false;
  if (!text) return true;
  if (provider === 'fallback' || provider === 'kb_fallback') return true;
  if (/sorry, something went wrong|could not connect|trouble connecting|no provider available|server error/i.test(text)) {
    return true;
  }
  return false;
}

async function fetchWithBackendFallback(path, options = {}) {
  let lastError = null;
  for (const base of API_BASES) {
    const url = `${base.replace(/\/$/, '')}${path}`;
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        console.error('Duct AI assistant backend error:', { url, status: response.status, statusText: response.statusText, body: errorText, options });
        lastError = new Error(`Backend request failed (${response.status}) ${response.statusText} @ ${url}: ${errorText}`);
        continue;
      }
      if (path === CHAT_PATH) {
        const data = await response.json();
        if (isWeakChatResponse(data)) {
          console.warn('Weak AI response from backend, retrying next endpoint:', { url, provider: data.provider, answer: data.answer || data.reply });
          lastError = new Error(`Weak AI response from ${url}`);
          continue;
        }
        return data;
      }
      return response;
    } catch (error) {
      console.error('Duct AI assistant fetch exception:', { url, error, options });
      lastError = error;
    }
  }
  throw lastError || new Error('All backend endpoints failed');
}

async function sendDuctAiChat(userMessage) {
  const sessionId = getDuctAiSessionId();
  const payload = {
    query: userMessage,
    session_id: sessionId,
    context: {
      page: window.location.pathname,
      user_agent: navigator.userAgent
    }
  };

  try {
    const data = await fetchWithBackendFallback(CHAT_PATH, {
      method: 'POST',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

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

