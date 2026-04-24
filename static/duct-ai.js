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
      img.style.maxWidth = '80px';
      img.style.display = 'block';
      div.appendChild(img);
    }
    div.appendChild(document.createTextNode(msg.content));
    chatBox.appendChild(div);
  });
}

async function escalateToHuman(query, imageUrl) {
  // Send to backend for logging, then redirect to WhatsApp
  await fetch('/escalate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, imageUrl }),
  });
  let waMsg = encodeURIComponent('User query: ' + query);
  if (imageUrl) waMsg += '%0A[Image attached]';
  let waUrl = 'https://wa.me/2348036850229?text=' + waMsg;
  window.open(waUrl, '_blank');
}

// Product Modal & WhatsApp Integration
function openProductModal(productName, productImage, productPrice, productCategory) {
  const modal = document.getElementById('productModal');
  if (!modal) {
    console.warn('Product modal not found');
    return;
  }
  
  // Store current product for escalation
  window.currentProduct = {
    name: productName,
    image: productImage,
    price: productPrice,
    category: productCategory
  };
  
  // Update modal content
  document.getElementById('modalProductImage').src = productImage;
  document.getElementById('modalProductImage').alt = productName;
  document.getElementById('modalProductName').textContent = productName;
  document.getElementById('modalProductPrice').textContent = productPrice;
  document.getElementById('modalProductCategory').textContent = productCategory;
  
  // Show modal
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
    message = `Hi, I'm interested in the **${window.currentProduct.name}** (₦${window.currentProduct.price}). This is from the ${window.currentProduct.category} category. Can you provide more details and a customized quote?`;
  }
  
  const encodedMsg = encodeURIComponent(message);
  const waUrl = `https://wa.me/${whatsappNumber}?text=${encodedMsg}`;
  window.open(waUrl, '_blank');
  
  // Close modal if it's open
  closeProductModal();
}

// Self-learn: log all queries for future improvement
async function logUserQuery(query, answer) {
  await fetch('/user-log', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({query, answer, time:Date.now()})
  });
}
