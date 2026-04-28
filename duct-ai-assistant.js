const API_BASE = 'https://api.interiorductltd.com';
const CHAT_ENDPOINT = `${API_BASE}/chat`;
const TRACK_ENDPOINT = `${API_BASE}/track`;
const SESSION_STORAGE_KEY = 'duct_ai_session_id';

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
    message: userMessage,
    session_id: sessionId,
    page: window.location.pathname,
    user_agent: navigator.userAgent
  };

  try {
    const response = await fetch(CHAT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat request failed (${response.status} ${response.statusText}): ${errorText}`);
    }

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
    await fetch(TRACK_ENDPOINT, {
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

