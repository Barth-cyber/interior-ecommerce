// Load products from server
let heroPopupProducts = [];
let seatingProducts = [];
let diningProducts = [];
let bedroomProducts = [];
let doorsProducts = [];
let livingProducts = [];
let officeProducts = [];
let aiCarouselInterval;

function safeAttributeString(value) {
  return String(value || '')
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

async function loadProducts() {
  const sampleProducts = [
    {
      name: 'Royal Chesterfield Sofa Set',
      img: 'IDL_Product_branding/Chair_Royal.jpg',
      desc: 'Elegant chesterfield sofa set with premium leather upholstery and classic design.',
      price: 'NGN 2,800,000',
      category: 'Chairs & Seating'
    },
    {
      name: 'Mahogany Dining Table',
      img: 'IDL_Product_branding/Dining_Set.jpg',
      desc: 'Modern dining table with premium wood finish and glass top.',
      price: 'NGN 3,200,000',
      category: 'Dining & Tables'
    },
    {
      name: 'Tufted Master Bedroom Suite',
      img: 'IDL_Product_branding/IMG_20251216_WA0032.jpg',
      desc: 'Luxury bedroom suite with plush headboard and bespoke finishes.',
      price: 'NGN 4,800,000',
      category: 'Bedroom'
    },
    {
      name: 'Executive Reception Counter',
      img: 'IDL_Product_branding/Reception_Counter.jpg',
      desc: 'Statement reception counter perfect for high-end corporate spaces.',
      price: 'NGN 2,900,000',
      category: 'Office & Commercial'
    },
    {
      name: 'Premium Mahogany Door',
      img: 'IDL_Product_branding/Door_White.jpg',
      desc: 'Hand-crafted mahogany door with elegant detailing and finish.',
      price: 'NGN 750,000',
      category: 'Doors'
    }
  ];

  try {
    const res = await fetch('/content');
    const data = await res.json();
    const products = Array.isArray(data.products) ? data.products : [];
    heroPopupProducts = products.length ? products.map(p => ({
      name: p.name,
      img: `IDL_Product_branding/${p.image}`,
      desc: p.description,
      price: p.price,
      category: p.category
    })) : sampleProducts;
  } catch (e) {
    console.error('Failed to load products:', e);
    heroPopupProducts = sampleProducts;
  }

  initializeSliders();
  if (heroPopupProducts.length > 0) {
    renderHeroPopupSlides();
    updateHeroPopupSlider();
    startHeroPopupAuto();
  }
  refreshAICarousel();
}

function initializeSliders() {
  // Filter products by category
  seatingProducts = heroPopupProducts.filter(p => p.category === 'Chairs & Seating');
  diningProducts = heroPopupProducts.filter(p => p.category === 'Dining & Tables');
  bedroomProducts = heroPopupProducts.filter(p => p.category === 'Bedroom');
  doorsProducts = heroPopupProducts.filter(p => p.category === 'Doors');
  livingProducts = heroPopupProducts.filter(p => p.category === 'Living Room');
  officeProducts = heroPopupProducts.filter(p => ['Office & Commercial', 'Office & Reception', 'Storage & Media', 'Kitchen'].includes(p.category));

  renderSeatingSlides(seatingProducts);
  renderDiningSlides(diningProducts);
  renderBedroomSlides(bedroomProducts);
  renderDoorsSlides(doorsProducts);
  renderLivingSlides(livingProducts);
  renderOfficeSlides(officeProducts);

  updateSeatingSlider();
  updateDiningSlider();
  updateBedroomSlider();
  updateDoorsSlider();
  updateLivingSlider();
  updateOfficeSlider();
}

// Load products on page load
loadProducts();

// Render category slides
function renderSeatingSlides(products) {
  const track = document.getElementById('seatingTrack');
  if (!track) return;
  track.innerHTML = products.map((p, i) => `
    <div class="hero-popup-slide fade-up" style="min-width:100%;display:flex;align-items:center;justify-content:center;padding:2.5rem 1.5rem;background:rgba(255,255,255,0.97);box-shadow:0 8px 32px rgba(27,58,107,0.12);border-radius:12px;transition:opacity 1.2s, transform 1.2s;min-height:320px;gap:2rem;flex-wrap:nowrap;">
      <img src="${p.img}" alt="${p.name}" loading="lazy" style="max-width:220px;width:100%;height:220px;object-fit:cover;border-radius:8px;margin-right:2.2rem;box-shadow:0 2px 12px rgba(13,27,42,0.08);" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIwIiBoZWlnaHQ9IjIyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5QUE1QjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBMb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg=='">
      <div>
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">${p.name}</div>
        <div style="font-size:.98rem;color:#3D4F63;margin-bottom:.7rem;">${p.desc}</div>
        <div style="font-size:1.1rem;color:#7B5C3E;font-weight:600;margin-bottom:.5rem;">${p.price}</div>
        <div style="font-size:.78rem;color:#C4A882;text-transform:uppercase;">${p.category}</div>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;">
          <button class="btn btn-brown" style="flex:1;min-width:120px;" onclick="window.openCheckoutForProduct({name:'${safeAttributeString(p.name)}',price:'${safeAttributeString(p.price)}',img:'${safeAttributeString(p.img)}'})">Checkout</button>
          <button class="btn btn-outline-navy" style="flex:1;min-width:120px;" onclick="openWhatsApp('${safeAttributeString(p.name)}')">Quote</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderDiningSlides(products) {
  const track = document.getElementById('diningTrack');
  if (!track) return;
  track.innerHTML = products.map((p, i) => `
    <div class="hero-popup-slide fade-up" style="min-width:100%;display:flex;align-items:center;justify-content:center;padding:2.5rem 1.5rem;background:rgba(255,255,255,0.97);box-shadow:0 8px 32px rgba(27,58,107,0.12);border-radius:12px;transition:opacity 1.2s, transform 1.2s;min-height:320px;gap:2rem;flex-wrap:nowrap;">
      <img src="${p.img}" alt="${p.name}" loading="lazy" style="max-width:220px;width:100%;height:220px;object-fit:cover;border-radius:8px;margin-right:2.2rem;box-shadow:0 2px 12px rgba(13,27,42,0.08);" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIwIiBoZWlnaHQ9IjIyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5QUE1QjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBMb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg=='">
      <div>
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">${p.name}</div>
        <div style="font-size:.98rem;color:#3D4F63;margin-bottom:.7rem;">${p.desc}</div>
        <div style="font-size:1.1rem;color:#7B5C3E;font-weight:600;margin-bottom:.5rem;">${p.price}</div>
        <div style="font-size:.78rem;color:#C4A882;text-transform:uppercase;">${p.category}</div>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;">
          <button class="btn btn-brown" style="flex:1;min-width:120px;" onclick="window.openCheckoutForProduct({name:'${safeAttributeString(p.name)}',price:'${safeAttributeString(p.price)}',img:'${safeAttributeString(p.img)}'})">Checkout</button>
          <button class="btn btn-outline-navy" style="flex:1;min-width:120px;" onclick="openWhatsApp('${safeAttributeString(p.name)}')">Quote</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderBedroomSlides(products) {
  const track = document.getElementById('bedroomTrack');
  if (!track) return;
  track.innerHTML = products.map((p, i) => `
    <div class="hero-popup-slide fade-up" style="min-width:100%;display:flex;align-items:center;justify-content:center;padding:2.5rem 1.5rem;background:rgba(255,255,255,0.97);box-shadow:0 8px 32px rgba(27,58,107,0.12);border-radius:12px;transition:opacity 1.2s, transform 1.2s;min-height:320px;gap:2rem;flex-wrap:nowrap;">
      <img src="${p.img}" alt="${p.name}" loading="lazy" style="max-width:220px;width:100%;height:220px;object-fit:cover;border-radius:8px;margin-right:2.2rem;box-shadow:0 2px 12px rgba(13,27,42,0.08);" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIwIiBoZWlnaHQ9IjIyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5QUE1QjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBMb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg=='">
      <div>
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">${p.name}</div>
        <div style="font-size:.98rem;color:#3D4F63;margin-bottom:.7rem;">${p.desc}</div>
        <div style="font-size:1.1rem;color:#7B5C3E;font-weight:600;margin-bottom:.5rem;">${p.price}</div>
        <div style="font-size:.78rem;color:#C4A882;text-transform:uppercase;">${p.category}</div>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;">
          <button class="btn btn-brown" style="flex:1;min-width:120px;" onclick="window.openCheckoutForProduct({name:'${safeAttributeString(p.name)}',price:'${safeAttributeString(p.price)}',img:'${safeAttributeString(p.img)}'})">Checkout</button>
          <button class="btn btn-outline-navy" style="flex:1;min-width:120px;" onclick="openWhatsApp('${safeAttributeString(p.name)}')">Quote</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderDoorsSlides(products) {
  const track = document.getElementById('doorsTrack');
  if (!track) return;
  track.innerHTML = products.map((p, i) => `
    <div class="hero-popup-slide fade-up" style="min-width:100%;display:flex;align-items:center;justify-content:center;padding:2.5rem 1.5rem;background:rgba(255,255,255,0.97);box-shadow:0 8px 32px rgba(27,58,107,0.12);border-radius:12px;transition:opacity 1.2s, transform 1.2s;min-height:320px;gap:2rem;flex-wrap:nowrap;">
      <img src="${p.img}" alt="${p.name}" loading="lazy" style="max-width:220px;width:100%;height:220px;object-fit:cover;border-radius:8px;margin-right:2.2rem;box-shadow:0 2px 12px rgba(13,27,42,0.08);" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIwIiBoZWlnaHQ9IjIyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5QUE1QjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBMb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg=='">
      <div>
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">${p.name}</div>
        <div style="font-size:.98rem;color:#3D4F63;margin-bottom:.7rem;">${p.desc}</div>
        <div style="font-size:1.1rem;color:#7B5C3E;font-weight:600;margin-bottom:.5rem;">${p.price}</div>
        <div style="font-size:.78rem;color:#C4A882;text-transform:uppercase;">${p.category}</div>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;">
          <button class="btn btn-brown" style="flex:1;min-width:120px;" onclick="window.openCheckoutForProduct({name:'${safeAttributeString(p.name)}',price:'${safeAttributeString(p.price)}',img:'${safeAttributeString(p.img)}'})">Checkout</button>
          <button class="btn btn-outline-navy" style="flex:1;min-width:120px;" onclick="openWhatsApp('${safeAttributeString(p.name)}')">Quote</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderLivingSlides(products) {
  const track = document.getElementById('livingTrack');
  if (!track) return;
  track.innerHTML = products.map((p, i) => `
    <div class="hero-popup-slide fade-up" style="min-width:100%;display:flex;align-items:center;justify-content:center;padding:2.5rem 1.5rem;background:rgba(255,255,255,0.97);box-shadow:0 8px 32px rgba(27,58,107,0.12);border-radius:12px;transition:opacity 1.2s, transform 1.2s;min-height:320px;gap:2rem;flex-wrap:nowrap;">
      <img src="${p.img}" alt="${p.name}" loading="lazy" style="max-width:220px;width:100%;height:220px;object-fit:cover;border-radius:8px;margin-right:2.2rem;box-shadow:0 2px 12px rgba(13,27,42,0.08);" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIwIiBoZWlnaHQ9IjIyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5QUE1QjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBMb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg=='">
      <div>
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">${p.name}</div>
        <div style="font-size:.98rem;color:#3D4F63;margin-bottom:.7rem;">${p.desc}</div>
        <div style="font-size:1.1rem;color:#7B5C3E;font-weight:600;margin-bottom:.5rem;">${p.price}</div>
        <div style="font-size:.78rem;color:#C4A882;text-transform:uppercase;">${p.category}</div>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;">
          <button class="btn btn-brown" style="flex:1;min-width:120px;" onclick="window.openCheckoutForProduct({name:'${safeAttributeString(p.name)}',price:'${safeAttributeString(p.price)}',img:'${safeAttributeString(p.img)}'})">Checkout</button>
          <button class="btn btn-outline-navy" style="flex:1;min-width:120px;" onclick="openWhatsApp('${safeAttributeString(p.name)}')">Quote</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderOfficeSlides(products) {
  const track = document.getElementById('officeTrack');
  if (!track) return;
  track.innerHTML = products.map((p, i) => `
    <div class="hero-popup-slide fade-up" style="min-width:100%;display:flex;align-items:center;justify-content:center;padding:2.5rem 1.5rem;background:rgba(255,255,255,0.97);box-shadow:0 8px 32px rgba(27,58,107,0.12);border-radius:12px;transition:opacity 1.2s, transform 1.2s;min-height:320px;gap:2rem;flex-wrap:nowrap;">
      <img src="${p.img}" alt="${p.name}" loading="lazy" style="max-width:220px;width:100%;height:220px;object-fit:cover;border-radius:8px;margin-right:2.2rem;box-shadow:0 2px 12px rgba(13,27,42,0.08);" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIwIiBoZWlnaHQ9IjIyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5QUE1QjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBMb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg=='">
      <div>
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">${p.name}</div>
        <div style="font-size:.98rem;color:#3D4F63;margin-bottom:.7rem;">${p.desc}</div>
        <div style="font-size:1.1rem;color:#7B5C3E;font-weight:600;margin-bottom:.5rem;">${p.price}</div>
        <div style="font-size:.78rem;color:#C4A882;text-transform:uppercase;">${p.category}</div>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;">
          <button class="btn btn-brown" style="flex:1;min-width:120px;" onclick="window.openCheckoutForProduct({name:'${safeAttributeString(p.name)}',price:'${safeAttributeString(p.price)}',img:'${safeAttributeString(p.img)}'})">Checkout</button>
          <button class="btn btn-outline-navy" style="flex:1;min-width:120px;" onclick="openWhatsApp('${safeAttributeString(p.name)}')">Quote</button>
        </div>
      </div>
    </div>
  `).join('');
}

// Slider logic for categories
function setCategorySlideState(trackId, activeIndex) {
  const track = document.getElementById(trackId);
  if (!track) return;

  Array.from(track.children).forEach((slide, idx) => {
    const isActive = idx === activeIndex;
    slide.style.display = isActive ? 'flex' : 'none';
    slide.classList.toggle('active', isActive);
  });

  const dots = track.parentElement.querySelectorAll('.slider-nav .slider-dot');
  dots.forEach((dot, idx) => dot.classList.toggle('active', idx === activeIndex));
}

let seatingSlide = 0;
function updateSeatingSlider() {
  setCategorySlideState('seatingTrack', seatingSlide);
}
function nextSeatingSlide() {
  if (!seatingProducts.length) return;
  seatingSlide = safeSlideIndex(seatingSlide + 1, seatingProducts.length);
  updateSeatingSlider();
}
function prevSeatingSlide() {
  if (!seatingProducts.length) return;
  seatingSlide = safeSlideIndex(seatingSlide - 1, seatingProducts.length);
  updateSeatingSlider();
}

let diningSlide = 0;
function updateDiningSlider() {
  setCategorySlideState('diningTrack', diningSlide);
}
function nextDiningSlide() {
  if (!diningProducts.length) return;
  diningSlide = safeSlideIndex(diningSlide + 1, diningProducts.length);
  updateDiningSlider();
}
function prevDiningSlide() {
  if (!diningProducts.length) return;
  diningSlide = safeSlideIndex(diningSlide - 1, diningProducts.length);
  updateDiningSlider();
}

let bedroomSlide = 0;
function updateBedroomSlider() {
  setCategorySlideState('bedroomTrack', bedroomSlide);
}
function nextBedroomSlide() {
  if (!bedroomProducts.length) return;
  bedroomSlide = safeSlideIndex(bedroomSlide + 1, bedroomProducts.length);
  updateBedroomSlider();
}
function prevBedroomSlide() {
  if (!bedroomProducts.length) return;
  bedroomSlide = safeSlideIndex(bedroomSlide - 1, bedroomProducts.length);
  updateBedroomSlider();
}

let doorsSlide = 0;
function updateDoorsSlider() {
  setCategorySlideState('doorsTrack', doorsSlide);
}
function nextDoorsSlide() {
  if (!doorsProducts.length) return;
  doorsSlide = safeSlideIndex(doorsSlide + 1, doorsProducts.length);
  updateDoorsSlider();
}
function prevDoorsSlide() {
  if (!doorsProducts.length) return;
  doorsSlide = safeSlideIndex(doorsSlide - 1, doorsProducts.length);
  updateDoorsSlider();
}

let livingSlide = 0;
function updateLivingSlider() {
  setCategorySlideState('livingTrack', livingSlide);
}
function nextLivingSlide() {
  if (!livingProducts.length) return;
  livingSlide = safeSlideIndex(livingSlide + 1, livingProducts.length);
  updateLivingSlider();
}
function prevLivingSlide() {
  if (!livingProducts.length) return;
  livingSlide = safeSlideIndex(livingSlide - 1, livingProducts.length);
  updateLivingSlider();
}

let officeSlide = 0;
function updateOfficeSlider() {
  setCategorySlideState('officeTrack', officeSlide);
}
function nextOfficeSlide() {
  if (!officeProducts.length) return;
  officeSlide = safeSlideIndex(officeSlide + 1, officeProducts.length);
  updateOfficeSlider();
}
function prevOfficeSlide() {
  if (!officeProducts.length) return;
  officeSlide = safeSlideIndex(officeSlide - 1, officeProducts.length);
  updateOfficeSlider();
}

// Render pop-up slides
function renderHeroPopupSlides() {
  const track = document.getElementById('heroPopupTrack');
  if (!track) return;
  track.innerHTML = heroPopupProducts.map((p, i) => `
    <div class="hero-popup-slide fade-up" style="min-width:100%;display:flex;align-items:center;justify-content:center;padding:2.5rem 1.5rem;background:rgba(255,255,255,0.97);box-shadow:0 8px 32px rgba(27,58,107,0.12);border-radius:12px;transition:opacity 1.2s, transform 1.2s;max-height:420px;overflow:hidden;gap:2rem;flex-wrap:nowrap;">
      <img src="${encodeURI(p.img)}" alt="${p.name}" style="max-width:220px;width:100%;max-height:220px;height:220px;object-fit:cover;border-radius:8px;flex-shrink:0;box-shadow:0 2px 12px rgba(13,27,42,0.08);cursor:pointer;" onclick="openProductModal('${safeAttributeString(p.name)}', '${safeAttributeString(p.img)}', '${safeAttributeString(p.price)}', '${safeAttributeString(p.category)}')">
      <div class="hero-popup-content" style="flex:1;min-width:250px;">
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">${p.name}</div>
        <div style="font-size:.98rem;color:#3D4F63;margin-bottom:.7rem;">${p.desc}</div>
        <div style="font-size:1.1rem;color:#7B5C3E;font-weight:600;margin-bottom:.5rem;">${p.price}</div>
        <div style="font-size:.78rem;color:#C4A882;text-transform:uppercase;">${p.category}</div>
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;">
          <button class="btn btn-brown" style="flex:1;min-width:120px;" onclick="window.openCheckoutForProduct({name:'${safeAttributeString(p.name)}',price:'${safeAttributeString(p.price)}',img:'${safeAttributeString(p.img)}'})">Checkout</button>
          <button class="btn btn-outline-navy" style="flex:1;min-width:120px;" onclick="openWhatsApp('${safeAttributeString(p.name)}')">Quote</button>
        </div>
      </div>
    </div>
  `).join('');
  // Remove corrupted nested divs and incomplete base64 cards
  Array.from(track.children).forEach(slide => {
    if (!slide.querySelector('img') || slide.innerHTML.includes('base64') || slide.querySelectorAll('div').length < 2) {
      slide.remove();
    }
  });
}

// Slider logic
function safeSlideIndex(index, length) {
  if (!length) return 0;
  return ((index % length) + length) % length;
}

let heroPopupSlide = 0;
function updateHeroPopupSlider() {
  const track = document.getElementById('heroPopupTrack');
  if (!track || !heroPopupProducts.length) return;

  heroPopupSlide = safeSlideIndex(heroPopupSlide, heroPopupProducts.length);
  Array.from(track.children).forEach((slide, idx) => {
    slide.style.opacity = idx === heroPopupSlide ? 1 : 0;
    slide.style.transform = idx === heroPopupSlide ? 'scale(1)' : 'scale(0.98)';
    slide.style.zIndex = idx === heroPopupSlide ? 2 : 1;
    slide.style.position = idx === heroPopupSlide ? 'relative' : 'absolute';
    slide.style.pointerEvents = idx === heroPopupSlide ? 'auto' : 'none';
  });
}
function nextHeroPopupSlide() {
  if (!heroPopupProducts.length) return;
  heroPopupSlide = safeSlideIndex(heroPopupSlide + 1, heroPopupProducts.length);
  updateHeroPopupSlider();
}
function prevHeroPopupSlide() {
  if (!heroPopupProducts.length) return;
  heroPopupSlide = safeSlideIndex(heroPopupSlide - 1, heroPopupProducts.length);
  updateHeroPopupSlider();
}
let heroPopupInterval;
function startHeroPopupAuto() {
  if (heroPopupInterval) clearInterval(heroPopupInterval);
  heroPopupInterval = setInterval(nextHeroPopupSlide, 5000);
}
function stopHeroPopupAuto() {
  clearInterval(heroPopupInterval);
}

document.addEventListener('DOMContentLoaded', () => {
  const heroPopupNext = document.getElementById('heroPopupNext');
  const heroPopupPrev = document.getElementById('heroPopupPrev');
  const heroPopupTrack = document.getElementById('heroPopupTrack');

  if (heroPopupNext) heroPopupNext.onclick = nextHeroPopupSlide;
  if (heroPopupPrev) heroPopupPrev.onclick = prevHeroPopupSlide;
  if (heroPopupTrack) {
    heroPopupTrack.addEventListener('mouseenter', stopHeroPopupAuto);
    heroPopupTrack.addEventListener('mouseleave', startHeroPopupAuto);
  }

  startHeroCollageAuto();

  // Button events
  const attach = (id, fn) => {
    const el = document.getElementById(id);
    if (el) el.onclick = fn;
  };
  attach('seatingNext', nextSeatingSlide);
  attach('seatingPrev', prevSeatingSlide);
  attach('diningNext', nextDiningSlide);
  attach('diningPrev', prevDiningSlide);
  attach('bedroomNext', nextBedroomSlide);
  attach('bedroomPrev', prevBedroomSlide);
  attach('doorsNext', nextDoorsSlide);
  attach('doorsPrev', prevDoorsSlide);
  attach('livingNext', nextLivingSlide);
  attach('livingPrev', prevLivingSlide);
  attach('officeNext', nextOfficeSlide);
  attach('officePrev', prevOfficeSlide);
});

const heroCollageSets = [
  [
    "IDL_Product_branding/IDL_Cover_Photo.jpg",
    "IDL_Product_branding/Chair_Royal.jpg",
    "IDL_Product_branding/Dining_Set.jpg",
    "IDL_Product_branding/Door_White.jpg"
  ],
  [
    "IDL_Product_branding/Living_Room_set.jpg",
    "IDL_Product_branding/Kitchen_Cabinet.jpg",
    "IDL_Product_branding/tv_console1.jpg",
    "IDL_Product_branding/Bedside.jpg"
  ],
  [
    "IDL_Product_branding/Chair_Dining_Single.jpg",
    "IDL_Product_branding/Reception_Counter.jpg",
    "IDL_Product_branding/IMG_20251216_WA0033.jpg",
    "IDL_Product_branding/IMG_20251217_WA0007.jpg"
  ],
  [
    "IDL_Product_branding/Reception_Counter.jpg",
    "IDL_Product_branding/Dining_Sets.jpg",
    "IDL_Product_branding/Door_black.jpg",
    "IDL_Product_branding/Table_cofee_mahogany.jpg"
  ]
];

let currentCollageSet = 0;
function updateHeroCollage() {
  const imgs = document.querySelectorAll('.hero-collage img');
  const set = heroCollageSets[currentCollageSet];
  imgs.forEach((img, idx) => {
    if (set[idx]) {
      img.style.transition = 'opacity 0.6s ease';
      img.style.opacity = 0;
      setTimeout(() => {
        img.src = encodeURI(set[idx]);
        img.style.opacity = 1;
      }, 300);
    }
  });
}

function nextHeroCollageSet() {
  currentCollageSet = (currentCollageSet + 1) % heroCollageSets.length;
  updateHeroCollage();
}

let heroCollageInterval;
function startHeroCollageAuto() {
  heroCollageInterval = setInterval(nextHeroCollageSet, 6000);
}

// AI Assistant Floating Button with Product Carousel
function initAIChatButton() {
  // Create AI button HTML
  const aiButtonHTML = `
    <div id="aiChatContainer" style="position:fixed;bottom:5.5rem;right:2rem;z-index:450;width:380px;max-width:90vw;display:none;background:#fff;border-radius:12px;box-shadow:0 8px 48px rgba(27,58,107,0.25);overflow:hidden;animation:slideUp 0.3s ease;">
      <div style="background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%);padding:1.5rem;color:#fff;display:flex;justify-content:space-between;align-items:center;">
        <div>
          <h3 style="margin:0;font-size:1.1rem;margin-bottom:0.3rem;">AI Product Assistant</h3>
          <p style="margin:0;font-size:0.8rem;opacity:0.9;">Product recommendations for you</p>
        </div>
        <button onclick="closeAIChat()" style="background:none;border:none;color:#fff;font-size:1.5rem;cursor:pointer;padding:0;width:30px;height:30px;display:flex;align-items:center;justify-content:center;">×</button>
      </div>
      <div id="aiProductCarousel" style="height:280px;position:relative;overflow:hidden;background:#f9f9f9;">
        <div id="aiCarouselTrack" style="display:flex;height:100%;transition:transform 0.5s cubic-bezier(.77,0,.175,1);">
          <!-- Products will be injected here -->
        </div>
      </div>
      <div style="padding:1rem;text-align:center;background:#fff;border-top:1px solid #e0e0e0;">
        <a id="aiChatLink" target="_blank"
           class="btn"
           style="width:100%;background:#C9956B;color:#fff;border:none;text-decoration:none;display:inline-block;box-sizing:border-box;padding:0.75rem 1.5rem;border-radius:4px;font-weight:600;font-size:0.9rem;transition:all 0.3s ease;"
           href="https://wa.me/2348036850229?text=Hello%20Interior%20Duct%21%20I%20am%20interested%20in%20your%20products">
          Chat with AI
        </a>
      </div>
    </div>
    <button id="aiChatButton" onclick="toggleAIChat()" style="position:fixed;bottom:2rem;right:2rem;z-index:400;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%);border:none;color:#fff;font-size:1.8rem;cursor:pointer;box-shadow:0 6px 24px rgba(27,58,107,0.4);transition:all 0.3s ease;animation:bounce 2s infinite;">
      🤖
    </button>
  `;
  
  document.body.insertAdjacentHTML('beforeend', aiButtonHTML);
  initAICarousel();
}

function initAICarousel() {
  const track = document.getElementById('aiCarouselTrack');
  if (!track) return;
  window.aiFeaturedProducts = heroPopupProducts.slice(0, 6);
  window.currentAIProductIndex = 0;
  refreshAICarousel();

  aiCarouselInterval = setInterval(() => {
    if (!window.aiFeaturedProducts || window.aiFeaturedProducts.length === 0) return;
    window.currentAIProductIndex = (window.currentAIProductIndex + 1) % window.aiFeaturedProducts.length;
    track.style.transform = `translateX(-${window.currentAIProductIndex * 100}%)`;
    updateAIChatLink();
  }, 4000);

  updateAIChatLink();
}

function refreshAICarousel() {
  const track = document.getElementById('aiCarouselTrack');
  if (!track) return;
  const products = (heroPopupProducts.length > 0 ? heroPopupProducts : [{
    name: 'Loading products...',
    img: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiNGRkYiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkxvYWRpbmcgLi4uPC90ZXh0Pjwvc3ZnPg=='
  }]).slice(0, 6);
  window.aiFeaturedProducts = products;
  window.currentAIProductIndex = 0;

  track.innerHTML = products.map((p, i) => `
    <div style="min-width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:1.5rem;cursor:pointer;transition:all 0.3s ease;" onclick="window.currentAIProductIndex=${i}; openWhatsApp(window.aiFeaturedProducts[${i}])">
      <img src="${encodeURI(p.img)}" alt="${p.name}" style="width:180px;height:180px;object-fit:cover;border-radius:8px;margin-bottom:1rem;box-shadow:0 4px 12px rgba(13,27,42,0.15);" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjRjJGNEY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiNGRkYiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkxvYWRpbmcgLi4uPC90ZXh0Pjwvc3ZnPg=='">
      <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif;font-size:1rem;font-weight:600;color:#1B3A6B;margin-bottom:0.3rem;line-height:1.3;">${p.name}</div>
        <div style="font-size:0.85rem;color:#7B5C3E;font-weight:600;margin-bottom:0.5rem;">${p.price || ''}</div>
        <div style="font-size:0.75rem;color:#999;text-transform:uppercase;">${p.category || 'Featured'}</div>
      </div>
    </div>
  `).join('');

  updateAIChatLink();
}


function toggleAIChat() {
  const container = document.getElementById('aiChatContainer');
  const button = document.getElementById('aiChatButton');

  if (container.style.display === 'none' || !container.style.display) {
    container.style.display = 'block';
    button.textContent = '✕';
    button.style.backgroundColor = 'rgba(27,58,107,0.8)';
  } else {
    closeAIChat();
  }
}

function closeAIChat() {
  const container = document.getElementById('aiChatContainer');
  const button = document.getElementById('aiChatButton');
  container.style.display = 'none';
  button.textContent = '🤖';
  button.style.backgroundColor = '';
}

function getCurrentAIProduct() {
  return window.aiFeaturedProducts && window.aiFeaturedProducts[window.currentAIProductIndex];
}

function updateAIChatLink() {
  const link = document.getElementById('aiChatLink');
  if (!link) return;

  const product = getCurrentAIProduct();
  if (!product) {
    link.href = 'https://wa.me/2348036850229?text=' + encodeURIComponent('Hello, I am interested in your sales services');
    return;
  }

  const text = `Hello Interior Duct! I am interested in ${product.name}. Price: ${product.price}. Description: ${product.desc}. Image: ${product.img}. Please send me a quote and availability.`;
  link.href = 'https://wa.me/2348036850229?text=' + encodeURIComponent(text);
}

function openAIConversation() {
  updateAIChatLink();
  const link = document.getElementById('aiChatLink');
  if (link) {
    link.click();
  } else {
    const message = "Hi! I'm interested in your furniture and interior design products. Can you help me find the perfect piece?";
    openWhatsApp(message);
  }
  closeAIChat();
}

// Add styles for animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }
  #aiChatButton:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 32px rgba(27,58,107,0.4);
  }
`;
document.head.appendChild(style);

// Initialize AI chat when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAIChatButton);
} else {
  initAIChatButton();
}

