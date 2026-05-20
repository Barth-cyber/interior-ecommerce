(function () {
  const currentScript = document.currentScript || Array.from(document.getElementsByTagName('script')).find(s => s.src && s.src.includes('duct-ai-widget.js'));
  const CANONICAL_BACKEND = (currentScript && currentScript.dataset && currentScript.dataset.backendUrl) || (window.getBackendUrl && window.getBackendUrl()) || window.DUCT_AI_BACKEND_URL || window.__BACKEND_URL__ || '';
  const LOCAL_DEFAULT = (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? `http://${window.location.hostname === '127.0.0.1' ? '127.0.0.1' : 'localhost'}:5000`
    : '';
  const BACKEND_URLS = [];
  if (LOCAL_DEFAULT) BACKEND_URLS.push(LOCAL_DEFAULT);
  if (CANONICAL_BACKEND) BACKEND_URLS.push(CANONICAL_BACKEND);
  if (!BACKEND_URLS.includes('https://interior-ecommerce-production.up.railway.app')) BACKEND_URLS.push('https://interior-ecommerce-production.up.railway.app');
  const DEFAULT_AVATAR_URL = window.DUCT_AI_AVATAR_URL || 'static/duct-ai-agent.jpg';

  function fetchWithTimeout(url, options = {}, timeout = 3000) {
    const controller = new AbortController();
    const signal = controller.signal;
    const timer = setTimeout(() => controller.abort(), timeout);
    return fetch(url, { ...options, signal }).finally(() => clearTimeout(timer));
  }

  async function fetchChatBackend(path, options = {}) {
    let lastError = null;

    for (const base of BACKEND_URLS) {
      const url = `${base.replace(/\/$/, '')}${path}`;
      try {
        const response = await fetchWithTimeout(url, options, 3000);
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
  const SESSION_STORAGE_KEY = 'duct_ai_session_id';
  const WHATSAPP_NUMBER = '2348036850229';
  let knowledgeBase = null;

  function getDuctAiSessionId() {
    let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!sessionId) {
      sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    }
    return sessionId;
  }

  async function loadKnowledgeBase() {
    try {
      const response = await fetchChatBackend('/kb', {
        method: 'GET',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' }
      });
      knowledgeBase = await response.json();
    } catch (error) {
      console.warn('Duct AI knowledge base load failed:', error);
      knowledgeBase = null;
    }
  }

  const knowledgeBaseReady = loadKnowledgeBase();
  async function ensureKnowledgeBaseReady() {
    if (!knowledgeBaseReady) return;
    try {
      await knowledgeBaseReady;
    } catch (error) {
      console.warn('Knowledge base preparation failed:', error);
    }
  }

  function normalizeText(text) {
    return String(text || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function findLocalKbAnswer(query, kb) {
    if (!query || !kb) return null;
    const lowerQuery = query.toLowerCase();
    const normalized = normalizeText(query);
    const queryWords = normalized.split(' ').filter(Boolean);

    const quickResponses = [
      {
        triggers: ['mahogany', 'glass top', 'luxury dining', 'premium wood', 'modern dining table', 'dining room'],
        response: 'A luxury mahogany dining table with a glass top is a beautiful choice for modern interiors. I can recommend matching chairs, finishes, and a tailored quote for your room.'
      },
      {
        triggers: ['living room', 'sofa', 'lounge', 'sectional', 'coffee table', 'tv console'],
        response: 'For a luxury living room, I recommend a statement sofa, a premium coffee table, and layered accents. Share your room style and I’ll help you choose the right pieces.'
      },
      {
        triggers: ['office', 'desk', 'workstation', 'executive desk', 'reception', 'conference'],
        response: 'For a refined office, our executive desks, storage units, and reception systems combine premium wood finishes with modern functionality. I can help you select the right solution.'
      },
      {
        triggers: ['quote', 'pricing', 'price', 'budget', 'estimate'],
        response: 'I can prepare an instant quote for your chosen furniture or room package. Tell me the product, style, and room so I can tailor it to your budget.'
      }
    ];

    for (const item of quickResponses) {
      if (item.triggers.some(trigger => lowerQuery.includes(trigger))) {
        return item.response;
      }
    }

    if (Array.isArray(kb.greetings)) {
      for (const greeting of kb.greetings) {
        const triggers = Array.isArray(greeting.trigger) ? greeting.trigger : [];
        for (const trigger of triggers) {
          if (typeof trigger === 'string' && trigger.length > 0 && lowerQuery.includes(trigger.toLowerCase())) {
            return greeting.response;
          }
        }
      }
    }

    if (Array.isArray(kb.faqs)) {
      for (const faq of kb.faqs) {
        const question = String(faq.q || '').toLowerCase();
        if (!question) continue;
        if (lowerQuery === question || question.includes(lowerQuery) || lowerQuery.includes(question)) {
          return faq.a;
        }
      }
      for (const faq of kb.faqs) {
        const question = String(faq.q || '').toLowerCase();
        if (!question) continue;
        const words = question.split(/\W+/).filter(Boolean);
        if (words.some(word => lowerQuery.includes(word) && word.length > 3)) {
          return faq.a;
        }
      }
    }

    if (Array.isArray(kb.products)) {
      for (const product of kb.products) {
        const name = String(product.name || '').toLowerCase();
        const category = String(product.category || '').toLowerCase();
        const description = String(product.description || '').toLowerCase();
        const fields = [name, category, description].filter(Boolean);
        if (fields.some(field => queryWords.some(word => word.length > 3 && field.includes(word)))) {
          return `${product.name} — ${product.description || product.category || 'Premium custom furniture for your space.'}`.trim();
        }
      }
    }

    return null;
  }

  loadKnowledgeBase();

  let chatHistory = [];

  const container = document.createElement('div');
  container.className = 'duct-ai-widget-container';
  container.innerHTML = `
    <button class="duct-ai-widget-toggle" aria-label="Open Duct AI Chat">
      <span class="duct-ai-toggle-avatar"><img src="${AGENT_AVATAR_URL}" alt="Duct AI avatar" onerror="this.style.display='none'" /></span>
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
      <div class="duct-ai-widget-footer">
        <input id="ductAiInput" type="text" placeholder="Ask about furniture, materials, pricing, room design..." />
        <button id="ductAiSend" aria-label="Send message">→</button>
      </div>
      <div class="duct-ai-widget-actions">
        <button class="duct-ai-action-btn" id="ductAiWhatsApp" title="Get human agent on WhatsApp">
          <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="18" alt="WhatsApp" />Agent
        </button>
        <button class="duct-ai-action-btn" id="ductAiQuote" title="Request quote for products">💰 Quote</button>
      </div>
    </div>
  `;
  document.body.appendChild(container);

  const panel = container.querySelector('.duct-ai-widget-panel');
  const overlay = container.querySelector('.duct-ai-widget-overlay');
  const toggle = container.querySelector('.duct-ai-widget-toggle');
  const closeBtn = container.querySelector('.duct-ai-widget-close');
  const messages = container.querySelector('#ductAiMessages');
  // Promotion area (rotating recommended products & second-hand items)
  const promoArea = document.createElement('div');
  promoArea.className = 'duct-ai-widget-promo-area';
  promoArea.style.cssText = 'padding:0.6rem;border-top:1px solid rgba(13,27,42,0.04);background:linear-gradient(90deg,rgba(250,250,250,0.98),rgba(255,255,255,0.99));';
  panel.insertBefore(promoArea, panel.querySelector('.duct-ai-widget-messages'));
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

  // Promotions: fetch social posts and second-hand listings and rotate them
  let promotions = [];
  let promoIndex = 0;
  async function loadPromotions() {
    try {
      const [socialRes, secondRes] = await Promise.all([
        fetch('social_posts.json').catch(() => null),
        fetch('second_hand_products.json').catch(() => null)
      ]);
      const social = socialRes && socialRes.ok ? await socialRes.json() : [];
      const second = secondRes && secondRes.ok ? await secondRes.json() : [];
      promotions = [];
      // map social posts to promo items
      for (const s of social) promotions.push({ type: 'social', title: s.title || s.platform, desc: s.desc || '', url: s.url });
      // map second-hand products
      for (const p of second.products || []) promotions.push({ type: 'second', title: p.name, desc: p.description || p.desc || '', img: p.image || '', url: 'marketplace.html#' + encodeURIComponent(p.id || p.name) });
      renderPromo();
      startPromoRotation();
    } catch (e) {
      console.warn('Failed to load promotions', e);
    }
  }

  function renderPromo() {
    promoArea.innerHTML = '';
    if (!promotions.length) return;
    const item = promotions[promoIndex % promotions.length];
    const card = document.createElement('div');
    card.style.cssText = 'display:flex;gap:0.6rem;align-items:center';
    const img = document.createElement('img');
    img.src = item.img || 'static/duct-ai-agent.jpg';
    img.alt = item.title || '';
    img.style.cssText = 'width:56px;height:56px;object-fit:cover;border-radius:6px;flex-shrink:0;';
    const copy = document.createElement('div');
    copy.style.cssText = 'flex:1;min-width:0';
    const title = document.createElement('div');
    title.textContent = item.title || '';
    title.style.cssText = 'font-weight:600;font-size:0.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
    const desc = document.createElement('div');
    desc.textContent = item.desc || '';
    desc.style.cssText = 'font-size:0.84rem;color:#556;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
    copy.appendChild(title);
    copy.appendChild(desc);
    const cta = document.createElement('button');
    cta.textContent = item.type === 'social' ? 'View' : 'Open';
    cta.style.cssText = 'background:var(--navy);color:#fff;border:none;padding:.45rem .7rem;border-radius:6px;flex-shrink:0;margin-left:0.5rem';
    cta.addEventListener('click', () => { window.open(item.url, '_blank'); });
    card.appendChild(img);
    card.appendChild(copy);
    card.appendChild(cta);
    promoArea.appendChild(card);
  }

  let promoTimer = null;
  function startPromoRotation() {
    if (promoTimer) clearInterval(promoTimer);
    promoTimer = setInterval(() => {
      if (!promotions.length) return;
      promoIndex = (promoIndex + 1) % promotions.length;
      renderPromo();
    }, 8000);
  }

  // Load promotions after widget loads
  setTimeout(loadPromotions, 800);

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

  // Smart AI response patterns for enhanced responses
  const SMART_RESPONSES = {
    furniture: {
      keywords: ['chair', 'table', 'sofa', 'bed', 'cabinet', 'desk', 'shelf', 'couch', 'seating', 'dining'],
      responses: [
        'We offer premium furniture crafted from solid timber with exquisite detail. What type of furniture are you looking for?',
        'Our furniture collections range from luxury seating to bespoke dining sets. What room are you furnishing?',
        'All our furniture is locally manufactured with quality materials. Tell me your style preference - modern, classic, or traditional?'
      ]
    },
    doors: {
      keywords: ['door', 'entrance', 'entrance door', 'exit', 'portal'],
      responses: [
        'We specialize in bespoke doors and entrances in Benin City, Abuja, and Port Harcourt. What style interests you?',
        'Our doors feature premium finishes and durable hardware. Are you looking for interior or exterior doors?',
        'Customized door designs available with various wood types and finishes. What\'s your requirement?'
      ]
    },
    pricing: {
      keywords: ['price', 'cost', 'how much', 'quote', 'payment', 'afford', 'budget'],
      responses: [
        'Our pricing is competitive with factory-direct savings. Send me details of what you need and I\'ll get you a quote via WhatsApp!',
        'We offer flexible payment options including Paystack and Stripe. Let me collect your preferences for a formal quote.',
        'Each product is customized, so pricing varies. Tell me what you\'re looking for and I can provide an estimate.'
      ]
    },
    delivery: {
      keywords: ['delivery', 'shipping', 'transport', 'send', 'available', 'location'],
      responses: [
        'We serve Benin City, Abuja, and Port Harcourt with reliable delivery. What\'s your location?',
        'We offer factory-direct delivery to multiple Nigerian cities. Where are you located?',
        'Delivery arrangements available nationwide. Which city should we deliver to?'
      ]
    },
    design: {
      keywords: ['design', 'style', 'aesthetic', 'customize', 'bespoke', 'custom', 'visualize', 'see'],
      responses: [
        'Our 3D room visualization tool helps you see furniture in your space before purchasing. Would you like to try it?',
        'We offer AI-powered design recommendations. Tell me about your room dimensions and style preferences!',
        'Custom design available - describe your vision and we\'ll create it for you.',
        'Try our 3D visualizer to see how furniture fits your room. What\'s your room style?'
      ]
    },
    luxury: {
      keywords: ['luxury', 'premium', 'mahogany', 'glass top', 'fine wood', 'dining table', 'dining room'],
      responses: [
        'A luxury mahogany dining table with a glass top looks stunning with warm metallic accents and premium leather or velvet chairs. Would you like matching chair options?',
        'For a modern premium dining table, I recommend rich wood finishes and a tempered glass top for a luxury feel that still feels light and contemporary.',
        'I can suggest luxury dining tables with premium wood and glass finishes, plus quote options matched to your style. Shall I focus on modern or classic designs?'
      ]
    }
  };

  function generateSmartResponse(query) {
    const lowerQuery = query.toLowerCase();
    
    // Find matching response category
    for (const category in SMART_RESPONSES) {
      const { keywords, responses } = SMART_RESPONSES[category];
      if (keywords.some(keyword => lowerQuery.includes(keyword))) {
        // Return a random response from the category
        return responses[Math.floor(Math.random() * responses.length)];
      }
    }
    
    return null;
  }

  window.openDuctAIChat = openDuctAIChat;
  window.openDuctAIWidget = openDuctAIChat;

  async function fetchChatData(text) {
    await ensureKnowledgeBaseReady();
    const localReply = findLocalKbAnswer(text, knowledgeBase);
    if (localReply) {
      return { reply: localReply, source: 'knowledge_base' };
    }

    const sessionId = getDuctAiSessionId();
    try {
      const pageTitle = document.title || '';
      const metaDescEl = document.querySelector('meta[name="description"]');
      const pageDescription = metaDescEl && metaDescEl.content ? String(metaDescEl.content).slice(0, 1000) : '';
      const productEls = Array.from(document.querySelectorAll('[data-product-name]')).map(e => e.dataset.productName).filter(Boolean).slice(0,8);
      const recentMessages = chatHistory.slice(-6).map(m => ({ role: m.role, text: m.text }));

      const payload = {
        query: text,
        session_id: sessionId,
        context: {
          page: window.location.pathname,
          page_title: pageTitle,
          page_description: pageDescription,
          url: window.location.href,
          user_agent: navigator.userAgent,
          locale: navigator.language || '',
          visible_products: productEls,
          recent_messages: recentMessages
        }
      };

      const response = await fetchChatBackend('/ai-query', {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (!data || (!data.reply && !data.answer && !data.escalate)) {
        throw new Error('Invalid chat response');
      }
      return data;
    } catch (error) {
      const fallback = await fetchChatDataFallback(text);
      if (fallback) {
        return fallback;
      }
      throw error;
    }
  }

  async function fetchChatDataFallback(queryText) {
    const smartResponse = generateSmartResponse(queryText);

    if (!knowledgeBase) {
      if (smartResponse) {
        return { reply: smartResponse, source: 'smart_response' };
      }
      return {
        reply: 'I’m having trouble reaching the server right now, but I can still help with furniture recommendations and quotes. Tell me what room or style you are planning.',
        source: 'fallback'
      };
    }

    const reply = findLocalKbAnswer(queryText, knowledgeBase) || smartResponse;
    if (reply) {
      return { reply, source: smartResponse ? 'smart_response' : 'knowledge_base' };
    }

    return {
      reply: 'I’m having trouble reaching the server right now, but I can still help with furniture recommendations and quotes. Tell me what room or style you are planning.',
      source: 'fallback'
    };
  }

  function addTypingIndicator() {
    const item = document.createElement('div');
    item.className = 'duct-ai-widget-message assistant duct-ai-typing active';
    let dotCount = 0;
    item.textContent = 'Typing';
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;

    item.typingInterval = setInterval(() => {
      dotCount = (dotCount + 1) % 4;
      item.textContent = 'Typing' + '.'.repeat(dotCount);
      messages.scrollTop = messages.scrollHeight;
    }, 450);

    return item;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    chatHistory.push({ role: 'user', text });
    input.value = '';
    send.disabled = true;

    const typingIndicator = addTypingIndicator();

    try {
      const data = await fetchChatData(text);
      const reply = data.reply || data.answer;

      if (typingIndicator) {
        clearInterval(typingIndicator.typingInterval);
        if (typingIndicator.parentNode) {
          typingIndicator.parentNode.removeChild(typingIndicator);
        }
      }

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
      if (typingIndicator) {
        clearInterval(typingIndicator.typingInterval);
        if (typingIndicator.parentNode) {
          typingIndicator.parentNode.removeChild(typingIndicator);
        }
      }
      console.error('Chat error:', error);
      const fallback = await fetchChatDataFallback(text);
      if (fallback && fallback.reply) {
        addMessage(fallback.reply, 'assistant');
        chatHistory.push({ role: 'assistant', text: fallback.reply });
      } else {
        addMessage('Sorry, I had trouble connecting to the server. Please check your internet and try again.', 'assistant');
      }
    } finally {
      send.disabled = false;
      input.focus();
    }
  }
})();