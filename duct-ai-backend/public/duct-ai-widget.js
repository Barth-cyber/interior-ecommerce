(function () {
  const currentScript = document.currentScript || Array.from(document.getElementsByTagName('script')).pop();
  const BACKEND_URL = (currentScript && currentScript.dataset.backendUrl) || window.DUCT_AI_BACKEND_URL || window.location.origin;
  const API_PATH = `${BACKEND_URL.replace(/\/$/, '')}/api/chat`;
  const scriptBase = (currentScript && currentScript.src)
    ? currentScript.src.replace(/\/[^\/]*$/, '/')
    : '';

  const widgetStyles = document.createElement('link');
  widgetStyles.rel = 'stylesheet';
  widgetStyles.href = scriptBase + 'duct-ai-widget.css';
  document.head.appendChild(widgetStyles);

  const container = document.createElement('div');
  container.className = 'duct-ai-widget-container';
  container.innerHTML = `
    <button class="duct-ai-widget-toggle">Ask Duct AI</button>
    <div class="duct-ai-widget-panel">
      <div class="duct-ai-widget-header">Duct AI Assistant</div>
      <div class="duct-ai-widget-messages" id="ductAiMessages"></div>
      <div class="duct-ai-widget-footer">
        <input id="ductAiInput" type="text" placeholder="Ask about furniture, materials or design" autocomplete="off" />
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
    if (panel.classList.contains('visible')) {
      input.focus();
    }
  });

  send.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
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

    try {
      const response = await fetch(API_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [{ role: 'user', content: text }] })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Request failed');
      }
      addMessage(data.reply || 'I’m sorry, I’m having trouble answering right now. Please try again in a moment or contact WhatsApp at +234 803 685 0229.', 'assistant');
    } catch (error) {
      addMessage('Error: ' + error.message, 'assistant');
    }
  }
})();
