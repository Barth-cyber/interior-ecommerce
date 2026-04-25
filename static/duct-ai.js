// Duct AI Assistant: Chat, escalation, recommender, and payment integration
let chatHistory = [];

async function askDuctAI(query, imageUrl) {
  chatHistory.push({ role: 'user', content: query, image: imageUrl || null });
  try {
    const res = await fetch('/ai-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    if (data.answer) {
      chatHistory.push({ role: 'ai', content: data.answer });
      renderChat();
    } else if (data.escalate) {
      escalateToHuman(query, imageUrl);
    }
  } catch (e) {
    chatHistory.push({ role: 'ai', content: 'Sorry, I could not connect right now. Please try again or contact us on WhatsApp.' });
    renderChat();
  }
}

function renderChat() {
  const chatBox = document.getElementById('duct-ai-chat');
  if (!chatBox) return;
  chatBox.innerHTML = '';
  chatHistory.forEach(msg => {
    const div = document.createElement('div');
    div.className = msg.role;
    div.style.cssText = msg.role === 'user'
      ? 'text-align:right;margin:.4rem 0;'
      : 'text-align:left;margin:.4rem 0;';
    const bubble = document.createElement('span');
    bubble.style.cssText = msg.role === 'user'
      ? 'background:#1B3A6B;color:#fff;padding:.45rem .8rem;border-radius:12px 12px 2px 12px;font-size:.88rem;display:inline-block;max-width:85%;'
      : 'background:#f0f2f7;color:#222;padding:.45rem .8rem;border-radius:12px 12px 12px 2px;font-size:.88rem;display:inline-block;max-width:85%;';
    if (msg.image) {
      const img = document.createElement('img');
      img.src = msg.image;
      img.alt = 'User image';
      img.style.cssText = 'max-width:80px;display:block;margin-bottom:.3rem;border-radius:6px;';
      bubble.appendChild(img);
    }
    bubble.appendChild(document.createTextNode(msg.content));
    div.appendChild(bubble);
    chatBox.appendChild(div);
  });
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function escalateToHuman(query, imageUrl) {
  await fetch('/escalate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, imageUrl }),
  });

  const message = `Hello Interior Duct! I am interested in ${query}.
Please send me a quote and availability.`;

  if (imageUrl && typeof window.shareProductImageToWhatsApp === 'function') {
    shareProductImageToWhatsApp(imageUrl, message);
    return;
  }

  const waMsg = encodeURIComponent(message + (imageUrl ? '\n\nImage: ' + imageUrl : ''));
  window.open('https://wa.me/2348036850229?text=' + waMsg, '_blank');
}

// ── Product Modal & WhatsApp ───────────────────────────────────────────────

function openProductModal(productName, productImage, productPrice, productCategory) {
  const modal = document.getElementById('productModal');
  if (!modal) return;

  window.currentProduct = { name: productName, image: productImage, price: productPrice, category: productCategory };

  const imgEl = document.getElementById('modalProductImage');
  if (imgEl) { imgEl.src = productImage; imgEl.alt = productName; }
  const nameEl = document.getElementById('modalProductName');
  if (nameEl) nameEl.textContent = productName;
  const priceEl = document.getElementById('modalProductPrice');
  if (priceEl) priceEl.textContent = productPrice;
  const catEl = document.getElementById('modalProductCategory');
  if (catEl) catEl.textContent = productCategory;

  modal.style.display = 'flex';
}

function closeProductModal() {
  const modal = document.getElementById('productModal');
  if (modal) modal.style.display = 'none';
  window.currentProduct = null;
}

function openWhatsApp(productName) {
  const whatsappNumber = '2348036850229';
  let message = `Hi, I'm interested in the ${productName}. Can you provide more details and a quote?`;
  if (window.currentProduct && window.currentProduct.name === productName) {
    message = `Hi, I'm interested in the ${window.currentProduct.name} (${window.currentProduct.price}). Category: ${window.currentProduct.category}. Please provide more details and a customized quote.`;
    if (window.currentProduct.image && typeof window.shareProductImageToWhatsApp === 'function') {
      window.shareProductImageToWhatsApp(window.currentProduct.image, message);
      closeProductModal();
      return;
    }
  }
  window.open(`https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`, '_blank');
  closeProductModal();
}

// ── Payment trigger ────────────────────────────────────────────────────────
// Call this from product cards to open checkout:
//   openPayment('Royal Chesterfield Sofa', 2800000, '/idl-images/Chair_Royal.jpg')
function openPayment(productName, priceNgn, productImage) {
  if (window.IDTPayment) {
    window.IDTPayment.open(productName, priceNgn, productImage);
  } else {
    // Fallback to WhatsApp if payment.js not loaded
    openWhatsApp(productName);
  }
}

// ── Product Recommender ────────────────────────────────────────────────────
async function getRecommendations(preferences, budget, room) {
  try {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preferences, budget, room }),
    });
    const data = await res.json();
    return data.recommendations || [];
  } catch (e) {
    console.error('Recommender error:', e);
    return [];
  }
}

function renderRecommendations(containerId, recommendations) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!recommendations.length) {
    container.innerHTML = '<p style="color:#888;font-size:.9rem;">No recommendations found. Try different preferences.</p>';
    return;
  }
  container.innerHTML = recommendations.map(r => `
    <div style="display:flex;gap:1rem;align-items:center;padding:.9rem;background:#f8f9fb;
      border-radius:10px;margin-bottom:.6rem;border:1px solid #eee;">
      <img src="/idl-images/${r.image}" alt="${r.name}"
        style="width:64px;height:64px;object-fit:cover;border-radius:7px;flex-shrink:0;"
        onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI0YyRjRGNSIvPjwvc3ZnPg=='">
      <div style="flex:1;min-width:0;">
        <div style="font-weight:700;color:#1B3A6B;font-size:.93rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${r.name}</div>
        <div style="font-size:.78rem;color:#7B5C3E;font-weight:600;">${r.price}</div>
        <div style="font-size:.76rem;color:#666;margin-top:.2rem;">${r.reason}</div>
      </div>
      <button onclick="openWhatsApp({name:'${r.name.replace(/'/g,"\\'")}',price:'${(r.price||'').replace(/'/g,"\\'")}',desc:'${(r.reason||'').replace(/'/g,"\\'")}',img:'/idl-images/${(r.image||'').replace(/'/g,"\\'")}'})"
        style="flex-shrink:0;padding:.4rem .8rem;background:#1B3A6B;color:#fff;border:none;
        border-radius:6px;font-size:.78rem;cursor:pointer;">Quote</button>
    </div>
  `).join('');
}

// ── Query logging ──────────────────────────────────────────────────────────
async function logUserQuery(query, answer) {
  try {
    await fetch('/user-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, answer, time: Date.now() }),
    });
  } catch (_) {}
}
