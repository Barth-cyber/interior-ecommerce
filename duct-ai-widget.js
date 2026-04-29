(function () {
  // Chat widget for Duct AI integration with WhatsApp escalation
  const DEFAULT_BACKEND_URL = 'https://api.interiorductltd.com';
  const BACKEND_URL = window.DUCT_AI_BACKEND_URL || DEFAULT_BACKEND_URL;
  const DEFAULT_AVATAR_URL = window.DUCT_AI_AVATAR_URL || 'static/duct-ai-agent.jpg';

  function normalizeAvatarPath(url) {
    if (typeof url !== 'string' || !url.length) return url;
    if (window.location.protocol === 'file:' && url.startsWith('/')) {
      return '.' + url;
    }
    if (window.location.protocol !== 'file:' && url.startsWith('./')) {
      return url.slice(1);
    }
    return url;
  }

  const AGENT_AVATAR_URL = normalizeAvatarPath(DEFAULT_AVATAR_URL);
  const CHAT_ENDPOINT = `${BACKEND_URL}/ai-query`;
  const RECOMMEND_ENDPOINT = `${BACKEND_URL}/recommend`;
  const SESSION_STORAGE_KEY = 'duct_ai_session_id';
  const WHATSAPP_NUMBER = '2348036850229';

  function getDuctAiSessionId() {
    let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!sessionId) {
      sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    }
    return sessionId;
  }

  let chatHistory = [];

  // Create and inject widget
  const container = document.createElement('div');
  container.className = 'duct-ai-widget-container';
  container.innerHTML = `
    <button class="duct-ai-widget-toggle" aria-label="Open Duct AI Chat">
      <span class="duct-ai-toggle-avatar">
        <img src="${AGENT_AVATAR_URL}" alt="Duct AI avatar" onerror="this.style.display='none'" />
      </span>
      <span>Ask Duct AI</span>
    </button>
    <div class="duct-ai-widget-overlay"></div>
    <div class="duct-ai-widget-panel">
      <div class="duct-ai-widget-header">
        <div class="duct-ai-widget-avatar">
          <img src="${AGENT_AVATAR_URL}" alt="Agent avatar" onerror="this.style.display='none'" />
        </div>
        <div class="duct-ai-widget-header-copy">
          <h3>Duct AI Assistant</h3>
          <span>Luxury Design Advisor</span>
        </div>
        <button class="duct-ai-widget-close" aria-label="Close chat">×</button>
      </div>
      <div class="duct-ai-widget-messages" id="ductAiMessages"></div>
      <div class="duct-ai-widget-actions">
        <button class="duct-ai-action-btn" id="ductAiWhatsApp" title="Get human agent on WhatsApp">
          <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="18" alt="WhatsApp" />
          Agent
        </button>
        <button class="duct-ai-action-btn" id="ductAiQuote" title="Request quote for products">
          💰 Quote
        </button>
      </div>
      <div class="duct-ai-widget-footer">
        <input id="ductAiInput" type="text" placeholder="Ask about furniture, materials, pricing..." />
        <button id="ductAiSend" aria-label="Send message">→</button>
      </div>
    </div>
  `;
  document.body.appendChild(container);

  const panel = container.querySelector('.duct-ai-widget-panel');
  const overlay = container.querySelector('.duct-ai-widget-overlay');
  const toggle = container.querySelector('.duct-ai-widget-toggle');
  const closeBtn = container.querySelector('.duct-ai-widget-close');
  const messages = container.querySelector('#ductAiMessages');
  const input = container.querySelector('#ductAiInput');
  const send = container.querySelector('#ductAiSend');
  const whatsappBtn = container.querySelector('#ductAiWhatsApp');
  const quoteBtn = container.querySelector('#ductAiQuote');

  toggle.addEventListener('click', () => {
    container.classList.add('panel-open');
    panel.classList.add('visible');
    overlay.classList.add('visible');
    input.focus();
    if (messages.children.length === 0) {
      addMessage('Welcome to Interior Duct Ltd! I\'m Duct AI, your design advisor. Tell me what room you\'re furnishing or what style interests you.', 'assistant');
    }
  });

  closeBtn.addEventListener('click', closePanel);
  overlay.addEventListener('click', closePanel);

  whatsappBtn.addEventListener('click', escalateToWhatsApp);
  quoteBtn.addEventListener('click', requestQuote);
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

  function escalateToWhatsApp() {
    const conversationSummary = chatHistory
      .slice(-6)
      .map(m => `${m.role === 'user' ? 'You' : 'AI'}: ${m.text}`)
      .join('\n');
    
    const message = encodeURIComponent(
      `Hi! I've been chatting with your AI and would like to speak with a human agent.\n\nRecent conversation:\n${conversationSummary}\n\nPlease assist me with furniture recommendations and pricing.`
    );
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${message}`, '_blank');
  }

  function requestQuote() {
    const query = chatHistory.map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.text}`).join('\n');
    const message = encodeURIComponent(
      `Hello! I'd like to request a formal quote for products discussed:\n\n${query}\n\nPlease send me a PDF quote.`
    );
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${message}`, '_blank');
  }

  function closePanel() {
    container.classList.remove('panel-open');
    panel.classList.remove('visible');
    overlay.classList.remove('visible');
  }

  function openDuctAIChat(initialText = '', autoSend = false) {
    container.classList.add('panel-open');
    panel.classList.add('visible');
    overlay.classList.add('visible');
    input.focus();

    if (messages.children.length === 0) {
      addMessage('Welcome to Interior Duct Ltd! I\'m Duct AI, your design advisor. Tell me what room you\'re furnishing or what style interests you.', 'assistant');
    }

    if (initialText) {
      input.value = initialText;
      if (autoSend) {
        sendMessage();
      }
    }
  }

  function processChatActions(actions) {
    if (!Array.isArray(actions) || actions.length === 0) return;

    actions.forEach(action => {
      if (action.type === 'scroll' && action.target) {
        const targetId = action.target.toLowerCase().trim();
        const target = document.getElementById(targetId) || document.querySelector(`[name="${targetId}"]`);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'center' });
          addMessage(`Scrolling to ${targetId} section...`, 'assistant');
        }
      }

      if (action.type === 'highlight_product' && action.name) {
        const match = document.querySelector(`[data-product-name="${action.name}"]`) || [...document.querySelectorAll('.pcard, .product-card, .product-card-item')].find(el => el.textContent.includes(action.name));
        if (match) {
          match.classList.add('duct-ai-highlight');
          setTimeout(() => match.classList.remove('duct-ai-highlight'), 4200);
          addMessage(`Highlighted product: ${action.name}`, 'assistant');
        }
      }
    });
  }

  window.openDuctAIChat = openDuctAIChat;
  window.openDuctAIWidget = openDuctAIChat;

  async function fetchChatData(text) {
    const sessionId = getDuctAiSessionId();
    const response = await fetch(CHAT_ENDPOINT, {
      method: 'POST',
      mode: 'cors',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: text,
        session_id: sessionId,
        context: {
          page: window.location.pathname,
          user_agent: navigator.userAgent
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat failed (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    if (!data || (data.reply == null && data.answer == null && data.escalate == null)) {
      throw new Error('Invalid chat response');
    }

    return data;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    chatHistory.push({ role: 'user', text });
    input.value = '';
    send.disabled = true;

    try {
      const data = await fetchChatData(text);
      const reply = data.reply || data.answer;

      if (reply) {
        addMessage(reply, 'assistant');
        chatHistory.push({ role: 'assistant', text: reply });
      } else if (data.escalate) {
        addMessage('I can connect you with a human agent. Opening WhatsApp now...', 'assistant');
        escalateToWhatsApp();
      } else {
        addMessage('I apologize, I\'m having trouble responding. Please try again.', 'assistant');
        chatHistory.push({ role: 'assistant', text: 'I apologize, I\'m having trouble responding. Please try again.' });
      }

      if (data.recommendation) {
        addMessage(data.recommendation, 'assistant');
        chatHistory.push({ role: 'assistant', text: data.recommendation });
      }
      if (Array.isArray(data.actions)) {
        processChatActions(data.actions);
      }
    } catch (error) {
      console.error('Chat error:', error);
      addMessage('Sorry, I had trouble connecting to the server. Please check your internet and try again.', 'assistant');
    } finally {
      send.disabled = false;
      input.focus();
    }
  }
})();
