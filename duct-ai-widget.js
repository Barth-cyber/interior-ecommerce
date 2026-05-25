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

  // Startup validation — log resolved backend URLs so connection issues are visible in DevTools
  console.log('[Duct AI] Widget initialising. Backend URL candidates:', BACKEND_URLS);
  if (!CANONICAL_BACKEND) {
    console.warn('[Duct AI] No explicit backend URL found (data-backend-url / DUCT_AI_BACKEND_URL). Falling back to hardcoded Railway URL.');
  }

  function fetchWithTimeout(url, options = {}, timeout = 5000) {
    const controller = new AbortController();
    const signal = controller.signal;
    const timer = setTimeout(() => controller.abort(), timeout);
    return fetch(url, { ...options, signal }).finally(() => clearTimeout(timer));
  }

  async function fetchChatBackend(path, options = {}) {
    let lastError = null;

    if (!BACKEND_URLS.length) {
      console.error('Duct AI: No backend URLs configured. Set data-backend-url on the script tag or window.DUCT_AI_BACKEND_URL.');
    } else {
      console.log('Duct AI: Attempting backend request to', BACKEND_URLS, 'path:', path);
    }

    for (const base of BACKEND_URLS) {
      const url = `${base.replace(/\/$/, '')}${path}`;
      try {
        console.log('Duct AI: Fetching', url);
        const response = await fetchWithTimeout(url, options, 5000);
        if (!response.ok) {
          const text = await response.text().catch(() => '');
          const error = new Error(`Backend request failed (${response.status}) at ${url}: ${text}`);
          console.error('Duct AI backend error:', { url, status: response.status, statusText: response.statusText, body: text, options });
          lastError = error;
          continue;
        }
        console.log('Duct AI: Successful response from', url);
        return response;
      } catch (error) {
        console.error('Duct AI backend fetch exception:', { url, error: error.message, options });
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

  // ============ USER PROFILE & PERSONALIZATION SYSTEM ============
  class UserProfile {
    constructor() {
      this.storageKey = 'duct_ai_user_profile_v1';
      this.data = this.load();
    }

    load() {
      try {
        const stored = localStorage.getItem(this.storageKey);
        if (stored) {
          const profile = JSON.parse(stored);
          profile.lastUpdated = new Date(profile.lastUpdated || Date.now());
          return profile;
        }
      } catch (e) {
        console.warn('Failed to load user profile:', e);
      }
      return {
        sessionId: this.generateSessionId(),
        name: null,
        phone: null,
        interests: [],
        viewedCategories: [],
        searchHistory: [],
        productInteractions: {},
        recommendationEngagements: [],
        conversationCount: 0,
        firstVisit: new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        preferences: {
          style: null,
          budget: null,
          rooms: []
        }
      };
    }

    save() {
      try {
        this.data.lastUpdated = new Date().toISOString();
        localStorage.setItem(this.storageKey, JSON.stringify(this.data));
      } catch (e) {
        console.warn('Failed to save user profile:', e);
      }
    }

    generateSessionId() {
      return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setName(name) {
      this.data.name = name || null;
      this.save();
      return this.data.name;
    }

    setPhone(phone) {
      this.data.phone = phone || null;
      this.save();
      return this.data.phone;
    }

    addInterest(interest) {
      if (interest && !this.data.interests.includes(interest)) {
        this.data.interests.push(interest);
        this.save();
      }
    }

    trackCategoryView(category) {
      if (category && !this.data.viewedCategories.includes(category)) {
        this.data.viewedCategories.push(category);
        this.save();
      }
    }

    trackSearch(query) {
      if (query) {
        this.data.searchHistory.push({ query, timestamp: Date.now() });
        if (this.data.searchHistory.length > 50) {
          this.data.searchHistory = this.data.searchHistory.slice(-50);
        }
        this.save();
      }
    }

    trackProductInteraction(productName, action = 'view') {
      if (!this.data.productInteractions[productName]) {
        this.data.productInteractions[productName] = { views: 0, clicks: 0, recommendations: 0 };
      }
      if (action === 'view') this.data.productInteractions[productName].views += 1;
      if (action === 'click') this.data.productInteractions[productName].clicks += 1;
      if (action === 'recommend') this.data.productInteractions[productName].recommendations += 1;
      this.save();
    }

    addRecommendationEngagement(recommendation) {
      this.data.recommendationEngagements.push({
        text: recommendation,
        timestamp: Date.now(),
        engaged: false
      });
      if (this.data.recommendationEngagements.length > 20) {
        this.data.recommendationEngagements = this.data.recommendationEngagements.slice(-20);
      }
      this.save();
    }

    getTopInterests() {
      return this.data.interests.slice(0, 5);
    }

    getTopCategories() {
      return this.data.viewedCategories.slice(0, 3);
    }

    incrementConversationCount() {
      this.data.conversationCount += 1;
      this.save();
    }

    isReturningUser() {
      return this.data.conversationCount > 1;
    }
  }

  const userProfile = new UserProfile();

  function extractPhoneFromWhatsAppContext() {
    // Try to get phone number from window object (set after WhatsApp escalation)
    if (window.userPhoneNumber) {
      return window.userPhoneNumber;
    }
    // Try to extract from URL parameters if callback is received
    const urlParams = new URLSearchParams(window.location.search);
    const phone = urlParams.get('user_phone') || urlParams.get('phone');
    if (phone) {
      userProfile.setPhone(phone);
      return phone;
    }
    return null;
  }

  function createNameInputDialog() {
    return new Promise((resolve) => {
      const dialogOverlay = document.createElement('div');
      dialogOverlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10001;';
      
      const dialogBox = document.createElement('div');
      dialogBox.style.cssText = 'background:#fff;padding:2rem;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.2);max-width:400px;width:90%;';
      
      dialogBox.innerHTML = `
        <div style="text-align:center;">
          <h2 style="margin:0 0 0.5rem 0;font-size:1.4rem;color:#1b3a6b;">Welcome to Interior Duct!</h2>
          <p style="margin:0 0 1.5rem 0;color:#666;font-size:0.95rem;">Let me personalize your experience. What's your name?</p>
          <input type="text" id="userName" placeholder="Your name" style="width:100%;padding:0.8rem;border:2px solid rgba(27,58,107,0.2);border-radius:8px;font-size:1rem;margin-bottom:1rem;box-sizing:border-box;" />
          <button id="confirmName" style="width:100%;padding:0.8rem;background:#1b3a6b;color:#fff;border:none;border-radius:8px;font-size:1rem;cursor:pointer;font-weight:600;transition:all 0.3s;">Start Chatting!</button>
        </div>
      `;
      
      document.body.appendChild(dialogOverlay);
      
      const input = dialogBox.querySelector('#userName');
      const btn = dialogBox.querySelector('#confirmName');
      
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') btn.click();
      });
      
      btn.addEventListener('click', () => {
        const name = input.value.trim();
        if (name) {
          userProfile.setName(name);
          dialogOverlay.remove();
          resolve(name);
        } else {
          input.style.borderColor = '#d32f2f';
          input.focus();
        }
      });
      
      dialogOverlay.appendChild(dialogBox);
      input.focus();
    });
  }

  async function initializeUserGreeting() {
    if (!userProfile.data.name) {
      const name = await createNameInputDialog();
      return name;
    }
    return userProfile.data.name;
  }

  function getPersonalizedGreeting() {
    const name = userProfile.data.name;
    const isReturning = userProfile.isReturningUser();
    const topCategories = userProfile.getTopCategories();
    
    if (isReturning && name) {
      let greeting = `Welcome back, ${name}! 👋 `;
      if (topCategories.length > 0) {
        greeting += `I noticed you're interested in ${topCategories.join(', ')}. How can I help you today?`;
      } else {
        greeting += `Ready to explore more furniture options?`;
      }
      return greeting;
    } else if (name) {
      return `Hi ${name}! 👋 I'm Duct AI, your personal design advisor. What room are you furnishing or what style interests you?`;
    }
    return `Welcome to Interior Duct Ltd! I'm Duct AI, your design advisor. Tell me what room you're furnishing or what style interests you.`;
  }

  function generateContextAwareRecommendation(query) {
    const name = userProfile.data.name;
    const topInterests = userProfile.getTopInterests();
    const topCategories = userProfile.getTopCategories();
    
    let recommendation = '';
    
    if (name && topInterests.length > 0) {
      recommendation = `${name}, based on your interest in ${topInterests.slice(0, 2).join(' and ')}, `;
    }
    
    if (topCategories.length > 0) {
      recommendation += `I think you'd love checking out our ${topCategories[0]} collection. `;
    } else {
      recommendation += `I'd recommend exploring our luxury furniture options. `;
    }
    
    return recommendation.trim();
  }

  // ============ END USER PROFILE SYSTEM ============

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

  toggle.addEventListener('click', async () => {
    container.classList.add('panel-open');
    panel.classList.add('visible');
    overlay.classList.add('visible');
    input.focus();
    
    // Initialize user name on first interaction if not already done
    if (!userProfile.data.name && messages.children.length === 0) {
      await initializeUserGreeting();
      addMessage(getPersonalizedGreeting(), 'assistant');
      renderRecommendations();
    } else if (messages.children.length === 0) {
      addMessage(getPersonalizedGreeting(), 'assistant');
      renderRecommendations();
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
      .map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.text}`)
      .join('\n');

    const userName = userProfile.data.name ? `Name: ${userProfile.data.name}\n` : '';
    const userPreferences = userProfile.data.preferences.style ? `Preferred Style: ${userProfile.data.preferences.style}\n` : '';
    
    const message = encodeURIComponent(
      `Hi! I've been chatting with your AI and would like to speak with a human agent.\n\n${userName}${userPreferences}Recent conversation:\n${conversationSummary}\n\nPlease assist me with furniture recommendations and pricing.`
    );
    
    // Store phone number in user profile after escalation
    window.userPhoneNumber = WHATSAPP_NUMBER;
    userProfile.setPhone(WHATSAPP_NUMBER);
    
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${message}`, '_blank');
  }

  // Promotions: fetch social posts and second-hand listings and rotate them
  let promotions = [];
  let promoIndex = 0;
  async function loadPromotions() {
    try {
      // Try backend promotions API first
      const apiRes = await fetch('/api/promotions').catch(() => null);
      if (apiRes && apiRes.ok) {
        const data = await apiRes.json();
        const social = data.social || [];
        const second = data.second_hand || { products: [] };
        promotions = [];
        for (const s of social) promotions.push({ type: 'social', title: s.title || s.platform, desc: s.desc || '', url: s.url });
        for (const p of second.products || []) promotions.push({ type: 'second', title: p.name, desc: p.description || p.desc || '', img: p.image || '', url: 'https://www.interiorductltd.com/marketplace.html#' + encodeURIComponent(p.id || p.name) });
        renderPromo();
        startPromoRotation();
        return;
      }

      // Fallback to static JSON files for environments without the API
      const [socialRes, secondRes] = await Promise.all([
        fetch('social_posts.json').catch(() => null),
        fetch('second_hand_products.json').catch(() => null)
      ]);
      const social = socialRes && socialRes.ok ? await socialRes.json() : [];
      const second = secondRes && secondRes.ok ? await secondRes.json() : [];
      promotions = [];
      for (const s of social) promotions.push({ type: 'social', title: s.title || s.platform, desc: s.desc || '', url: s.url });
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
    img.src = item.type === 'second' ? 'static/for-sale-badge.jpg' : (item.img || 'static/duct-ai-agent.jpg');
    img.alt = item.title || '';
    img.style.cssText = 'width:56px;height:56px;object-fit:cover;border-radius:6px;flex-shrink:0;cursor:pointer;transition:all 0.2s;';
    img.title = 'Click to inquire about this product via WhatsApp';
    
    // Add click handler to escalate product to WhatsApp directly
    img.addEventListener('click', async () => {
      escalateProductToWhatsApp(item);
    });
    
    img.addEventListener('mouseover', () => {
      img.style.opacity = '0.8';
      img.style.transform = 'scale(1.05)';
    });
    
    img.addEventListener('mouseout', () => {
      img.style.opacity = '1';
      img.style.transform = 'scale(1)';
    });
    
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

  function escalateProductToWhatsApp(product) {
    const userName = userProfile.data.name || 'Customer';
    const userPhone = userProfile.data.phone || '';
    
    // Build a comprehensive product inquiry message
    let whatsappMessage = `Hi! I'm interested in the following product:\n\n`;
    whatsappMessage += `📦 *Product: ${product.title}*\n`;
    
    if (product.desc) {
      whatsappMessage += `📝 Description: ${product.desc}\n`;
    }
    
    if (product.img) {
      whatsappMessage += `🖼️ Product Image: ${product.img}\n`;
    }
    
    whatsappMessage += `\nCustomer Name: ${userName}\n`;
    
    // Add recent chat context if available
    if (chatHistory.length > 0) {
      const recentContext = chatHistory.slice(-3).map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.text}`).join('\n');
      whatsappMessage += `\n📋 Recent Chat Context:\n${recentContext}\n`;
    }
    
    whatsappMessage += `\n${userPhone ? 'User Phone: ' + userPhone + '\n' : ''}Please provide me with:\n✓ Pricing details\n✓ Availability\n✓ Customization options\n✓ Delivery information`;
    
    const encodedMessage = encodeURIComponent(whatsappMessage);
    
    // Open WhatsApp with the complete product inquiry
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${encodedMessage}`, '_blank');
    
    // Track the product interaction
    userProfile.trackProductInteraction(product.title, 'click');
    
    // Show confirmation to user
    addMessage(`I'm connecting you to our sales team with details about ${product.title}. Opening WhatsApp now...`, 'assistant');
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
      addMessage(getPersonalizedGreeting(), 'assistant');
      renderRecommendations();
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

  const RECOMMENDATION_TOPICS = [
    { label: '🪑 Furniture Questions', question: 'What types of furniture do you offer?' },
    { label: '🚪 Custom Doors', question: 'Tell me about your custom doors and entrance designs.' },
    { label: '💰 Pricing & Options', question: 'What are your pricing and payment options?' },
    { label: '🚚 Delivery Info', question: 'Where do you deliver and what are shipping costs?' },
    { label: '🎨 Room Design', question: 'Can you help me design my room?' },
    { label: '🏭 Used Machinery', question: 'What used machinery do you have available?' }
  ];

  function renderRecommendations() {
    if (!messages) return;
    const existing = messages.querySelector('.duct-ai-recommendations');
    if (existing) return;
    
    const recContainer = document.createElement('div');
    recContainer.className = 'duct-ai-recommendations';
    recContainer.style.cssText = 'padding:0.8rem;display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;background:rgba(27,58,107,0.02);border-radius:8px;margin:0.6rem 0;';
    
    RECOMMENDATION_TOPICS.forEach(topic => {
      const btn = document.createElement('button');
      btn.style.cssText = 'padding:0.6rem 0.8rem;background:#fff;border:1px solid rgba(27,58,107,0.15);border-radius:6px;font-size:0.8rem;cursor:pointer;transition:all 0.2s;text-align:left;font-weight:500;';
      btn.textContent = topic.label;
      btn.addEventListener('click', () => {
        input.value = topic.question;
        recContainer.remove();
        sendMessage();
      });
      btn.addEventListener('mouseover', () => {
        btn.style.background = 'rgba(27,58,107,0.05)';
        btn.style.borderColor = 'rgba(27,58,107,0.3)';
      });
      btn.addEventListener('mouseout', () => {
        btn.style.background = '#fff';
        btn.style.borderColor = 'rgba(27,58,107,0.15)';
      });
      recContainer.appendChild(btn);
    });
    
    messages.appendChild(recContainer);
  }

  window.openDuctAIChat = openDuctAIChat;
  window.openDuctAIWidget = openDuctAIChat;

  // Smart AI response patterns for enhanced responses
  const SMART_RESPONSES = {
    greeting: {
      keywords: ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy', 'hiya', 'what\'s up', 'what is up'],
      responses: [
        'Hello! How are you doing today?',
        'Hi there! Great to see you. What can I help you with?',
        'Hey! Welcome to Interior Duct. How are you doing?',
        'Hello! Ready to explore some amazing furniture options?',
        'Hi! Happy to assist you today. What\'s on your mind?'
      ],
      noEscalate: true
    },
    gratitude: {
      keywords: ['thank', 'thanks', 'appreciate', 'grateful', 'appreciate it', 'thank you', 'thankyou', 'you\'re great', 'you\'re the best', 'excellent', 'awesome', 'amazing', 'perfect', 'much appreciated'],
      responses: [
        'You\'re very welcome! I\'m so glad I could help you get what you need. Is there anything else I can assist you with?',
        'Thank you! It\'s my pleasure to help. Do you need anything else today?',
        'You\'re welcome! I\'m thrilled I could be of assistance. How else can I support you?',
        'That\'s so kind of you! I\'m happy I could help. What else can I do for you?',
        'You\'re welcome! Thank you for letting me assist you. Is there anything else you\'d like to explore?'
      ],
      noEscalate: true
    },
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
      keywords: ['price', 'cost', 'how much', 'quote', 'payment', 'afford', 'budget', 'prices', 'costs', 'pricing'],
      responses: [
        'For detailed pricing and customized quotes, please click the "Agent" button below to speak with one of our sales specialists on WhatsApp. They\'ll provide you with the most accurate pricing tailored to your needs.',
        'Pricing varies based on customization and materials. Click the "Agent" button to connect with our team and get a personalized quote instantly via WhatsApp.',
        'I\'d love to help! For the best pricing and payment options, please click the "Agent" button below. Our team will discuss your budget and provide a formal quote.'
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
    const name = userProfile.data.name;
    const style = userProfile.data.preferences.style;
    const rooms = userProfile.data.preferences.rooms || [];
    
    // Find matching response category
    for (const category in SMART_RESPONSES) {
      const { keywords, responses } = SMART_RESPONSES[category];
      if (keywords.some(keyword => lowerQuery.includes(keyword))) {
        let response = responses[Math.floor(Math.random() * responses.length)];
        
        // Special handling for greeting responses
        if (category === 'greeting' && name) {
          response = response.replace('Hello!', `Hello ${name}!`)
                            .replace('Hi there!', `Hi ${name}!`)
                            .replace('Hey!', `Hey ${name}!`)
                            .replace('How are you', `How are you`);
          // Add name context if response contains "How are you"
          if (response.includes('How are you') && !response.includes(name)) {
            response = response.replace('How are you', `How are you ${name}`);
          }
        }
        
        // Special handling for gratitude responses
        if (category === 'gratitude' && name) {
          response = response.replace(/I\'m so glad/gi, `${name}, I'm so glad`)
                            .replace(/I\'m thrilled/gi, `${name}, I'm thrilled`)
                            .replace(/I\'m happy/gi, `${name}, I'm happy`)
                            .replace(/I\'m so kind/gi, `That's so kind of you`)
                            .replace(/Thank you!/gi, `Thank you!`);
          // If name not yet added, add it at the beginning
          if (!response.includes(name)) {
            response = `${name}, ` + response;
          }
        }
        
        // Personalize the response with user name if available (for non-greeting/gratitude)
        if (name && category !== 'greeting' && category !== 'gratitude' && !response.includes(name)) {
          response = response.replace(/^/, `${name}, `);
        }
        
        // Add style preference context if available
        if (style && category === 'design' && !response.includes(style)) {
          response = response.replace(/style/, `${style} style`);
        }
        
        // Add room context if available
        if (rooms.length > 0 && !response.includes('room')) {
          const roomContext = rooms[0];
          if (!response.includes(roomContext)) {
            response = response.replace(/your space/, `your ${roomContext}`);
          }
        }
        
        return response;
      }
    }
    
    // If no category match, provide a contextual fallback
    if (name && rooms.length > 0) {
      return `Hi ${name}! I can help you with your ${rooms[0]}. Could you tell me more about what you're looking for?`;
    } else if (name) {
      return `${name}, I'm here to help! Tell me about the room you're furnishing and your style preferences.`;
    }
    
    return null;
  }

  window.openDuctAIChat = openDuctAIChat;
  window.openDuctAIWidget = openDuctAIChat;

  async function fetchChatData(text) {
    await ensureKnowledgeBaseReady();

    const sessionId = getDuctAiSessionId();
    try {
      const pageTitle = document.title || '';
      const metaDescEl = document.querySelector('meta[name="description"]');
      const pageDescription = metaDescEl && metaDescEl.content ? String(metaDescEl.content).slice(0, 1000) : '';
      const productEls = Array.from(document.querySelectorAll('[data-product-name]')).map(e => e.dataset.productName).filter(Boolean).slice(0, 8);
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

      console.log('Duct AI: Sending query to /ai-query:', text);
      const response = await fetchChatBackend('/ai-query', {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      console.log('Duct AI: Received response from /ai-query:', data);

      const aiReply = data && (data.reply || data.answer);
      if (!aiReply && !data.escalate) {
        console.warn('Duct AI: Backend returned no usable reply field. Response was:', data);
        throw new Error('Backend response missing reply/answer field');
      }
      // Normalise so callers always see data.reply
      if (!data.reply && data.answer) {
        data.reply = data.answer;
      }
      return data;
    } catch (error) {
      console.warn('Duct AI: Backend request failed, falling back to local KB/smart response. Error:', error.message);
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

    // Track user search and preferences
    userProfile.trackSearch(text);
    userProfile.incrementConversationCount();
    
    // Extract and track interests/preferences from query
    const lowerText = text.toLowerCase();
    const styleKeywords = { modern: 'Modern', classic: 'Classic', traditional: 'Traditional', minimalist: 'Minimalist', luxury: 'Luxury', industrial: 'Industrial', contemporary: 'Contemporary', rustic: 'Rustic' };
    for (const [key, label] of Object.entries(styleKeywords)) {
      if (lowerText.includes(key)) {
        userProfile.data.preferences.style = label;
        userProfile.addInterest(label + ' style');
      }
    }
    
    const roomKeywords = { bedroom: 'Bedroom', living: 'Living Room', office: 'Office', kitchen: 'Kitchen', dining: 'Dining Room', bathroom: 'Bathroom' };
    for (const [key, label] of Object.entries(roomKeywords)) {
      if (lowerText.includes(key)) {
        if (!userProfile.data.preferences.rooms.includes(label)) {
          userProfile.data.preferences.rooms.push(label);
        }
        userProfile.trackCategoryView(label);
      }
    }
    userProfile.save();

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
        const personalizedReply = userProfile.data.name && !reply.includes(userProfile.data.name) 
          ? reply 
          : reply;
        addMessage(personalizedReply, 'assistant');
        chatHistory.push({ role: 'assistant', text: personalizedReply });
      } else if (data.escalate) {
        addMessage('I can connect you with a human agent. Opening WhatsApp now...', 'assistant');
        escalateToWhatsApp();
      } else {
        addMessage('I apologize, I\'m having trouble responding. Please try again.', 'assistant');
        chatHistory.push({ role: 'assistant', text: 'I apologize, I\'m having trouble responding. Please try again.' });
      }

      if (data.recommendation) {
        userProfile.addRecommendationEngagement(data.recommendation);
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