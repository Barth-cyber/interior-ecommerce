function showSection(section) {
  document.getElementById('images-section').style.display = section === 'images' ? '' : 'none';
  document.getElementById('models-section').style.display = section === 'models' ? '' : 'none';
  document.getElementById('content-section').style.display = section === 'content' ? '' : 'none';
  document.getElementById('settings-section').style.display = section === 'settings' ? '' : 'none';
  document.getElementById('products-section').style.display = section === 'products' ? '' : 'none';
  var faqSection = document.getElementById('faq-manager');
  if (faqSection) faqSection.style.display = section === 'faq-manager' ? '' : 'none';
}

// Image and 3D Model Management
const imageList = document.getElementById('imageList');
const uploadForm = document.getElementById('uploadForm');

async function fetchImages() {
  const res = await fetch('/images');
  const files = await res.json();
  renderImages(files.map(f => `/idl-images/${encodeURIComponent(f)}`));
}

async function fetchModels() {
  const res = await fetch('/3dmodels');
  const files = await res.json();
  renderModels(files);
}

async function deleteModel(filename) {
  const res = await fetch('/delete-model', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename })
  });
  if (res.ok) {
    await fetchModels();
  } else {
    alert('3D model delete failed.');
  }
}

function renderModels(models) {
  const modelList = document.getElementById('modelList');
  if (!modelList) return;
  modelList.innerHTML = '';
  if (!models.length) {
    modelList.innerHTML = '<p style="grid-column:1/-1;color:#555;">No 3D models uploaded yet.</p>';
    return;
  }
  models.forEach(name => {
    const card = document.createElement('div');
    card.style = 'border:1px solid #ddd;padding:.7rem;border-radius:8px;display:flex;flex-direction:column;gap:.6rem;';
    const title = document.createElement('strong');
    title.textContent = name;
    const viewer = document.createElement('model-viewer');
    viewer.setAttribute('src', `/idl-images/${encodeURIComponent(name)}`);
    viewer.setAttribute('alt', name);
    viewer.setAttribute('ar', '');
    viewer.setAttribute('auto-rotate', '');
    viewer.setAttribute('camera-controls', '');
    viewer.style = 'width:100%;height:160px;border-radius:6px;overflow:hidden;background:#eee;';
    const btnRow = document.createElement('div');
    btnRow.style = 'display:flex;gap:.5rem;';
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.style = 'flex:1;padding:.5rem;background:#e74c3c;color:#fff;border:none;border-radius:5px;cursor:pointer;';
    deleteBtn.addEventListener('click', () => deleteModel(name));
    btnRow.appendChild(deleteBtn);
    const openBtn = document.createElement('button');
    openBtn.textContent = 'Open Demo';
    openBtn.style = 'flex:1;padding:.5rem;background:#1b3a6b;color:#fff;border:none;border-radius:5px;cursor:pointer;';
    openBtn.addEventListener('click', () => window.open(`/3d-demo?model=${encodeURIComponent(name)}`, '_blank'));
    btnRow.appendChild(openBtn);
    card.appendChild(title);
    card.appendChild(viewer);
    card.appendChild(btnRow);
    modelList.appendChild(card);
  });
}

if (uploadForm) {
  uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const files = document.getElementById('imageUpload').files;
    if (!files.length) return;
    const formData = new FormData();
    for (const file of files) formData.append('images', file);
    const res = await fetch('/upload', { method: 'POST', body: formData });
    if (res.ok) {
      await fetchImages();
      uploadForm.reset();
    } else {
      alert('Upload failed.');
    }
  });
  fetchImages();
}

const modelUploadForm = document.getElementById('modelUploadForm');
if (modelUploadForm) {
  modelUploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const files = document.getElementById('modelUpload').files;
    if (!files.length) return;
    const formData = new FormData();
    for (const file of files) formData.append('models', file);
    const res = await fetch('/upload-model', { method: 'POST', body: formData });
    if (res.ok) {
      await fetchModels();
      modelUploadForm.reset();
    } else {
      alert('3D model upload failed.');
    }
  });
  fetchModels();
}


function renderImages(images) {
  imageList.innerHTML = '';
  images.forEach(img => {
    const div = document.createElement('div');
    div.className = 'img-item';
    const imageEl = document.createElement('img');
    imageEl.src = img;
    imageEl.alt = 'Admin Image';
    imageEl.onerror = function() { this.src = 'https://via.placeholder.com/120?text=No+Image'; };
    div.appendChild(imageEl);
    const delBtn = document.createElement('button');
    delBtn.className = 'delete-btn';
    delBtn.innerHTML = '&times;';
    delBtn.onclick = () => deleteImage(img);
    div.appendChild(delBtn);
    imageList.appendChild(div);
  });
}

async function deleteImage(imgUrl) {
  const filename = decodeURIComponent(imgUrl.split('/').pop());
  const res = await fetch('/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename })
  });
  if (res.ok) {
    await fetchImages();
  } else {
    alert('Delete failed.');
  }
}

// Content Management
const contentForm = document.getElementById('contentForm');
const homepageInput = document.getElementById('homepageInput');
const aboutInput = document.getElementById('aboutInput');
const contactInput = document.getElementById('contactInput');
const contentSaveMsg = document.getElementById('contentSaveMsg');
const adminSettingsForm = document.getElementById('adminSettingsForm');
const adminUsernameInput = document.getElementById('adminUsername');
const adminPasswordInput = document.getElementById('adminPassword');
const adminPasswordConfirmInput = document.getElementById('adminPasswordConfirm');
const settingsSaveMsg = document.getElementById('settingsSaveMsg');

async function loadContent() {
  const res = await fetch('/content');
  const data = await res.json();
  if (homepageInput) homepageInput.value = data.homepage || '';
  if (aboutInput) aboutInput.value = data.about || '';
  if (contactInput) contactInput.value = data.contact || '';
}

async function loadAdminSettings() {
  if (!adminSettingsForm) return;
  const res = await fetch('/api/admin-settings');
  if (!res.ok) return;
  const data = await res.json();
  adminUsernameInput.value = data.username || '';
}

if (contentForm) {
  contentForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = {
      homepage: homepageInput.value.trim(),
      about: aboutInput.value.trim(),
      contact: contactInput.value.trim()
    };
    const res = await fetch('/content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (res.ok) {
      contentSaveMsg.style.display = '';
      setTimeout(() => { contentSaveMsg.style.display = 'none'; }, 2000);
      await loadContent();
    } else {
      alert('Save failed.');
    }
  });
  loadContent();
}

  if (adminSettingsForm) {
    adminSettingsForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const username = adminUsernameInput.value.trim();
      const password = adminPasswordInput.value;
      const passwordConfirm = adminPasswordConfirmInput.value;

      if (!username) {
        alert('Username is required.');
        return;
      }
      if (password && password !== passwordConfirm) {
        alert('Password confirmation does not match.');
        return;
      }

      const res = await fetch('/api/admin-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, passwordConfirm })
      });

      if (res.ok) {
        settingsSaveMsg.textContent = password
          ? 'Admin username and password updated successfully.'
          : 'Admin username updated successfully.';
        settingsSaveMsg.style.display = '';
        setTimeout(() => { settingsSaveMsg.style.display = 'none'; }, 3000);
        adminPasswordInput.value = '';
        adminPasswordConfirmInput.value = '';
      } else {
        const data = await res.json();
        alert(data.error || 'Save failed.');
      }
    });
    loadAdminSettings();
  }
      <p><strong>Image:</strong> ${product.image}</p>
      <button onclick="editProduct(${product.id})">Edit</button>
      <button onclick="deleteProduct(${product.id})" style="background:#e74c3c;color:#fff;">Delete</button>
    `;
    productsList.appendChild(div);
  });
}

function addProduct() {
  const product = {
    id: Date.now(),
    name: 'New Product',
    category: 'Chairs & Seating',
    price: 'NGN 0',
    description: 'Description',
    image: 'placeholder.jpg'
  };
  products.push(product);
  renderProducts();
  editProduct(product.id);
}

function editProduct(id) {
  const product = products.find(p => p.id === id);
  if (!product) return;
  const newName = prompt('Name:', product.name);
  if (newName) product.name = newName;
  const newCategory = prompt('Category:', product.category);
  if (newCategory) product.category = newCategory;
  const newPrice = prompt('Price:', product.price);
  if (newPrice) product.price = newPrice;
  const newDesc = prompt('Description:', product.description);
  if (newDesc) product.description = newDesc;
  const newImage = prompt('Image:', product.image);
  if (newImage) product.image = newImage;
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
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  renderProducts();
}

loadProducts();
