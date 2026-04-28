// ================= SECTION SWITCHING =================
function showSection(section) {
  const sections = [
    'images',
    'models',
    'content',
    'settings',
    'products',
    'faq-manager'
  ];

  sections.forEach(sec => {
    const el = document.getElementById(`${sec}-section`) || document.getElementById(sec);
    if (el) el.style.display = sec === section ? '' : 'none';
  });
}

// ================= IMAGE MANAGEMENT =================
const imageList = document.getElementById('imageList');
const uploadForm = document.getElementById('uploadForm');

async function fetchImages() {
  try {
    const res = await fetch('/images');
    const files = await res.json();
    renderImages(files.map(f => `/idl-images/${encodeURIComponent(f)}`));
  } catch (err) {
    console.error('Failed to fetch images:', err);
  }
}

function renderImages(images) {
  if (!imageList) return;
  imageList.innerHTML = '';

  images.forEach(img => {
    const div = document.createElement('div');
    div.className = 'img-item';

    const imageEl = document.createElement('img');
    imageEl.src = img;
    imageEl.onerror = () => imageEl.src = 'https://via.placeholder.com/120?text=No+Image';

    const delBtn = document.createElement('button');
    delBtn.innerHTML = '&times;';
    delBtn.className = 'delete-btn';
    delBtn.onclick = () => deleteImage(img);

    div.appendChild(imageEl);
    div.appendChild(delBtn);
    imageList.appendChild(div);
  });
}

async function deleteImage(imgUrl) {
  const filename = decodeURIComponent(imgUrl.split('/').pop());

  const res = await fetch('/delete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ filename })
  });

  if (res.ok) fetchImages();
  else alert('Delete failed');
}

if (uploadForm) {
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const files = document.getElementById('imageUpload').files;
    if (!files.length) return;

    const formData = new FormData();
    for (const f of files) formData.append('images', f);

    const res = await fetch('/upload', { method: 'POST', body: formData });

    if (res.ok) {
      fetchImages();
      uploadForm.reset();
    } else {
      alert('Upload failed');
    }
  });

  fetchImages();
}

// ================= 3D MODELS =================
const modelUploadForm = document.getElementById('modelUploadForm');

async function fetchModels() {
  try {
    const res = await fetch('/admin/3dmodels');
    const models = await res.json();
    renderModels(models);
  } catch (err) {
    console.error(err);
  }
}

function renderModels(models) {
  const list = document.getElementById('modelList');
  if (!list) return;

  list.innerHTML = '';

  if (!models.length) {
    list.innerHTML = '<p>No models uploaded.</p>';
    return;
  }

  models.forEach(model => {
    const filename = typeof model === 'string' ? model : model.filename;
    const url = `/idl-images/${encodeURIComponent(filename)}`;

    const card = document.createElement('div');

    const title = document.createElement('strong');
    title.textContent = filename;

    const viewer = document.createElement('model-viewer');
    viewer.src = url;
    viewer.setAttribute('camera-controls', '');
    viewer.style.height = '150px';

    const del = document.createElement('button');
    del.textContent = 'Delete';
    del.onclick = () => deleteModel(filename);

    card.appendChild(title);
    card.appendChild(viewer);
    card.appendChild(del);

    list.appendChild(card);
  });
}

async function deleteModel(filename) {
  const res = await fetch('/delete-model', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ filename })
  });

  if (res.ok) fetchModels();
  else alert('Delete failed');
}

if (modelUploadForm) {
  modelUploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const files = document.getElementById('modelUpload').files;
    const formData = new FormData();

    for (const f of files) formData.append('models', f);

    const res = await fetch('/upload-model', { method: 'POST', body: formData });

    if (res.ok) {
      fetchModels();
      modelUploadForm.reset();
    } else {
      alert('Upload failed');
    }
  });

  fetchModels();
}

// ================= CONTENT =================
const contentForm = document.getElementById('contentForm');

async function loadContent() {
  const res = await fetch('/content');
  const data = await res.json();

  document.getElementById('homepageInput').value = data.homepage || '';
  document.getElementById('aboutInput').value = data.about || '';
  document.getElementById('contactInput').value = data.contact || '';
}

if (contentForm) {
  contentForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      homepage: homepageInput.value,
      about: aboutInput.value,
      contact: contactInput.value
    };

    const res = await fetch('/content', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      contentSaveMsg.style.display = '';
      setTimeout(()=>contentSaveMsg.style.display='none',2000);
    }
  });

  loadContent();
}

// ================= PRODUCTS (FIXED) =================
let products = [];

async function loadProducts() {
  const res = await fetch('/content');
  const data = await res.json();
  products = data.products || [];
  renderProducts();
}

// ================= PART 4: CHAT LOGS (ADMIN DASHBOARD) =================
async function loadChatLogs() {
  const container = document.getElementById('chatLogsContainer');
  container.innerHTML = '<p style="color:#999;">Loading chat logs...</p>';

  try {
    const res = await fetch('/admin/chat-logs');
    const data = await res.json();

    if (data.error) {
      container.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
      return;
    }

    const chats = data.chats || [];
    if (!chats.length) {
      container.innerHTML = '<p style="color:#999;">No chat logs found.</p>';
      return;
    }

    container.innerHTML = '';
    chats.forEach(chat => {
      const div = document.createElement('div');
      div.style.cssText = 'border-bottom:1px solid #eee;padding:1rem 0;';
      
      const timestamp = chat.timestamp ? new Date(chat.timestamp).toLocaleString() : 'N/A';
      
      div.innerHTML = `
        <div style="font-size:0.9rem;color:#666;">
          <strong>Session:</strong> ${chat.session_id || 'N/A'} | <strong>Time:</strong> ${timestamp}
        </div>
        <div style="margin:0.5rem 0;">
          <strong style="color:#2c3e50;">User:</strong> ${escapeHtml(chat.user || '')}
        </div>
        <div>
          <strong style="color:#27ae60;">Bot:</strong> ${escapeHtml(chat.bot || '')}
        </div>
      `;
      container.appendChild(div);
    });
  } catch (err) {
    container.innerHTML = `<p style="color:red;">Error loading chat logs: ${err.message}</p>`;
    console.error(err);
  }
}

function exportChatLogs() {
  alert('CSV export functionality coming soon!');
}

// ================= PART 5: ANALYTICS DASHBOARD =================
async function loadAnalytics() {
  try {
    const res = await fetch('/admin/analytics');
    const data = await res.json();

    if (data.error) {
      document.getElementById('analyticsContainer').innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
      return;
    }

    // Update metrics
    document.getElementById('totalChats').textContent = data.total_chats || 0;
    document.getElementById('totalUsers').textContent = data.total_users || 0;

    // Update top questions
    const topQuestionsContainer = document.getElementById('topQuestionsContainer');
    const topQuestions = data.top_questions || [];

    if (!topQuestions.length) {
      topQuestionsContainer.innerHTML = '<p style="color:#999;">No questions found yet.</p>';
      return;
    }

    topQuestionsContainer.innerHTML = '';
    topQuestions.forEach((q, idx) => {
      const div = document.createElement('div');
      div.style.cssText = 'padding:0.8rem;border-bottom:1px solid #eee;';
      
      div.innerHTML = `
        <div style="font-weight:bold;margin-bottom:0.3rem;">
          #${idx + 1} (asked ${q.count} times)
        </div>
        <div style="color:#555;font-size:0.95rem;">
          ${escapeHtml(q._id || '')}
        </div>
      `;
      topQuestionsContainer.appendChild(div);
    });
  } catch (err) {
    console.error('Error loading analytics:', err);
  }
}

// Helper function to escape HTML
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function renderProducts() {
  const list = document.getElementById('productsList');
  if (!list) return;

  list.innerHTML = '';

  products.forEach(p => {
    const div = document.createElement('div');

    div.innerHTML = `
      <strong>${p.name}</strong><br>
      ${p.price}<br>
      <button onclick="editProduct(${p.id})">Edit</button>
      <button onclick="deleteProduct(${p.id})">Delete</button>
    `;

    list.appendChild(div);
  });
}

function addProduct() {
  const p = {
    id: Date.now(),
    name: 'New Product',
    price: '0'
  };
  products.push(p);
  saveProducts();
}

function editProduct(id) {
  const p = products.find(x => x.id === id);
  if (!p) return;

  p.name = prompt('Name', p.name) || p.name;
  p.price = prompt('Price', p.price) || p.price;

  saveProducts();
}

function deleteProduct(id) {
  products = products.filter(p => p.id !== id);
  saveProducts();
}

async function saveProducts() {
  const res = await fetch('/content');
  const data = await res.json();

  data.products = products;

  await fetch('/content', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(data)
  });

  renderProducts();
}

loadProducts();