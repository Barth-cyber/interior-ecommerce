(function () {
  const BACKEND_URLS = [
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
      ? `http://${window.location.hostname}:5000`
      : window.DUCT_AI_BACKEND_URL || 'https://api.interiorductltd.com',
    'https://duct-ai-backend.onrender.com',
    'https://interior-ecommerce-backend.onrender.com',
    'https://interior-ecommerce-lh3e.onrender.com'
  ];

  const widgetStyles = document.createElement('link');
  widgetStyles.rel = 'stylesheet';
  widgetStyles.href = 'duct-ai-widget.css';
  document.head.appendChild(widgetStyles);

  const container = document.createElement('div');
  container.className = 'duct-ai-widget-container';
  container.innerHTML = `
    <button class="duct-ai-widget-toggle">Ask Duct AI</button>
    <div class="duct-ai-widget-panel">
      <div class="duct-ai-widget-header">Duct AI Assistant</div>
      <div class="duct-ai-widget-messages" id="ductAiMessages"></div>
      <div class="duct-ai-widget-footer">
        <input id="ductAiInput" type="text" placeholder="Ask about furniture, materials or design" />
        <button id="ductAiSend">Send</button>
      </div>
    </div>
  `;
  document.body.appendChild(container);

  const panel = container.querySelector('.duct-ai-widget-panel');
  const toggle = container.querySelector('.duct-ai-widget-toggle');
  const messages = container.querySelector('#ductAiMessages');
  const input = container.querySelector('#ductAiInput');
  const send = container.querySelector('#ductAiSend');

  toggle.addEventListener('click', () => {
    panel.classList.toggle('visible');
  });

  send.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      sendMessage();
    }
  });

  function getDuctAiSessionId() {
    let sessionId = localStorage.getItem('duct_ai_session_id');
    if (!sessionId) {
      sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('duct_ai_session_id', sessionId);
    }
    return sessionId;
  }

  async function fetchChatBackend(path, options = {}) {
    let lastError = null;

    for (const base of BACKEND_URLS) {
      const url = `${base.replace(/\/$/, '')}${path}`;
      try {
        const response = await fetch(url, options);
        if (!response.ok) {
          const text = await response.text().catch(() => '');
          const error = new Error(`Backend request failed (${response.status}) at ${url}: ${text}`);
          console.error('Duct AI backend error:', { url, status: response.status, statusText: response.statusText, body: text, options });
          lastError = error;
          continue;
        }
        return response;
      } catch (error) {
        console.error('Duct AI backend fetch exception:', { url, error, options });
        lastError = error;
      }
    }

    throw lastError || new Error('All backend endpoints failed');
  }

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

    try {
      const response = await fetchChatBackend('/ai-query', {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text,
          session_id: getDuctAiSessionId(),
          context: {
            page: window.location.pathname,
            user_agent: navigator.userAgent
          }
        })
      });
      const data = await response.json();
      if (!data || (!data.reply && !data.answer && !data.escalate)) {
        throw new Error('Invalid chat response');
      }
      addMessage(data.reply || data.answer || 'No reply received.', 'assistant');
    } catch (error) {
      addMessage('Sorry, I could not reach Duct AI right now. Please try again or contact us on WhatsApp.', 'assistant');
      console.error('Duct AI widget error:', error);
    }
  }
})();
