(function () {
  // Chat widget for Duct AI integration
  const BACKEND_URL = window.DUCT_AI_BACKEND_URL || window.location.origin;
  const CHAT_ENDPOINT = `${BACKEND_URL}/chat`;
  const SESSION_STORAGE_KEY = 'duct_ai_session_id';

  function getDuctAiSessionId() {
    let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    }
    return sessionId;
  }

  // Create and inject widget
  const container = document.createElement('div');
  container.className = 'duct-ai-widget-container';
  container.innerHTML = `
    <button class="duct-ai-widget-toggle" aria-label="Open Duct AI Chat">💬 Ask Duct AI</button>
    <div class="duct-ai-widget-panel">
      <div class="duct-ai-widget-header">
        <h3>Duct AI Assistant</h3>
        <button class="duct-ai-widget-close" aria-label="Close chat">×</button>
      </div>
      <div class="duct-ai-widget-messages" id="ductAiMessages"></div>
      <div class="duct-ai-widget-footer">
        <input id="ductAiInput" type="text" placeholder="Ask about furniture, materials or design..." />
        <button id="ductAiSend" aria-label="Send message">→</button>
      </div>
    </div>
  `;
  document.body.appendChild(container);

  const panel = container.querySelector('.duct-ai-widget-panel');
  const toggle = container.querySelector('.duct-ai-widget-toggle');
  const closeBtn = container.querySelector('.duct-ai-widget-close');
  const messages = container.querySelector('#ductAiMessages');
  const input = container.querySelector('#ductAiInput');
  const send = container.querySelector('#ductAiSend');

  toggle.addEventListener('click', () => {
    panel.classList.toggle('visible');
    if (panel.classList.contains('visible')) {
      input.focus();
    }
  });

  closeBtn.addEventListener('click', () => {
    panel.classList.remove('visible');
  });

  send.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      sendMessage();
    }
  });

  function addMessage(text, role) {
    const item = document.createElement('div');
    item.className = `duct-ai-widget-message ${role}`;
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    input.value = '';
    send.disabled = true;

    try {
      const sessionId = getDuctAiSessionId();
      const payload = {
        message: text,
        session_id: sessionId,
        page: window.location.pathname,
        user_agent: navigator.userAgent
      };

      const response = await fetch(CHAT_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Chat failed (${response.status}): ${errorText}`);
      }

      const data = await response.json();
      addMessage(data.reply || 'No reply received.', 'assistant');
    } catch (error) {
      console.error('Chat error:', error);
      addMessage('Sorry, I had trouble responding. Please try again.', 'assistant');
    } finally {
      send.disabled = false;
      input.focus();
    }
  }
})();
