/**
 * Interior Duct Ltd — Payment Integration
 * Handles Paystack (Nigeria/NGN) and Stripe (International USD/GBP/EUR)
 *
 * Include this script on any page that needs checkout:
 *   <script src="/static/payment.js"></script>
 * Also load Stripe.js in your HTML head:
 *   <script src="https://js.stripe.com/v3/"></script>
 */

(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────────────
  let _config = { paystack_public_key: '', stripe_publishable_key: '' };
  let _stripe = null;
  let _stripeElements = null;
  let _paymentElement = null;
  let _currentOrder = null;

  // ── Bootstrap: fetch public keys from server ───────────────────────────────
  async function loadPaymentConfig() {
    try {
      const res = await fetch('/api/payment-config');
      _config = await res.json();
    } catch (e) {
      console.error('Could not load payment config:', e);
    }
  }

  // ── Currency conversion helpers ────────────────────────────────────────────
  const EXCHANGE_RATES = {
    USD: 0.00064,  // Approximate NGN → USD
    GBP: 0.00051,
    EUR: 0.00059,
  };

  function ngnToForeign(amountNgn, currency) {
    const rate = EXCHANGE_RATES[currency.toUpperCase()] || EXCHANGE_RATES.USD;
    return Math.ceil(amountNgn * rate);
  }

  function formatCurrency(amount, currency) {
    const symbols = { NGN: '₦', USD: '$', GBP: '£', EUR: '€' };
    const sym = symbols[currency.toUpperCase()] || currency;
    return `${sym}${Number(amount).toLocaleString()}`;
  }

  // ── Open the checkout modal ────────────────────────────────────────────────
  function openCheckout(productName, priceNgn, productImage) {
    _currentOrder = { productName, priceNgn, productImage };

    // Inject modal if it doesn't exist yet
    if (!document.getElementById('idt-checkout-modal')) {
      document.body.insertAdjacentHTML('beforeend', _buildModalHTML());
      _attachModalEvents();
    }

    // Update modal product info
    document.getElementById('idt-product-name').textContent = productName;
    document.getElementById('idt-price-ngn').textContent = formatCurrency(priceNgn, 'NGN');
    if (document.getElementById('idt-product-img') && productImage) {
      document.getElementById('idt-product-img').src = productImage;
    }

    // Reset to gateway selector view
    _showView('gateway-select');
    document.getElementById('idt-checkout-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }

  function closeCheckout() {
    const modal = document.getElementById('idt-checkout-modal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
    _stripe = null;
    _stripeElements = null;
    _paymentElement = null;
  }

  function _showView(viewId) {
    ['gateway-select', 'paystack-form', 'stripe-form', 'payment-success', 'payment-error']
      .forEach(id => {
        const el = document.getElementById(`idt-view-${id}`);
        if (el) el.style.display = id === viewId ? 'block' : 'none';
      });
  }

  // ── Modal HTML ─────────────────────────────────────────────────────────────
  function _buildModalHTML() {
    return `
<div id="idt-checkout-modal" style="display:none;position:fixed;inset:0;z-index:99999;
  background:rgba(10,20,40,0.72);align-items:center;justify-content:center;padding:1rem;">
  <div style="background:#fff;border-radius:16px;max-width:480px;width:100%;
    box-shadow:0 24px 64px rgba(0,0,0,0.3);overflow:hidden;position:relative;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1B3A6B 0%,#2d5fa3 100%);
      padding:1.4rem 1.6rem;display:flex;align-items:center;justify-content:space-between;">
      <div>
        <div style="color:#C4A882;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Secure Checkout</div>
        <div style="color:#fff;font-size:1.15rem;font-weight:700;font-family:'Playfair Display',serif;" id="idt-product-name">Product</div>
      </div>
      <button onclick="IDTPayment.close()" style="background:rgba(255,255,255,0.15);border:none;
        color:#fff;width:32px;height:32px;border-radius:50%;cursor:pointer;font-size:1.1rem;
        display:flex;align-items:center;justify-content:center;">&times;</button>
    </div>

    <!-- Price bar -->
    <div style="background:#f8f9fb;padding:.8rem 1.6rem;
      display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #eee;">
      <span style="color:#555;font-size:.88rem;">Order Total</span>
      <span style="color:#1B3A6B;font-size:1.1rem;font-weight:700;" id="idt-price-ngn">₦0</span>
    </div>

    <div style="padding:1.6rem;">

      <!-- View: Gateway selector ────────────────────────────────────────── -->
      <div id="idt-view-gateway-select">
        <div style="font-size:.92rem;color:#444;margin-bottom:1rem;text-align:center;">
          How would you like to pay?
        </div>

        <!-- Paystack -->
        <button onclick="IDTPayment.selectPaystack()"
          style="width:100%;padding:1rem 1.2rem;margin-bottom:.75rem;border:2px solid #eee;
          border-radius:10px;background:#fff;cursor:pointer;display:flex;align-items:center;
          gap:1rem;transition:border-color .2s,box-shadow .2s;"
          onmouseover="this.style.borderColor='#00b94f';this.style.boxShadow='0 2px 12px rgba(0,185,79,.15)'"
          onmouseout="this.style.borderColor='#eee';this.style.boxShadow='none'">
          <div style="width:44px;height:44px;background:#e8faf0;border-radius:8px;
            display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="#00b94f">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 12l3 3 5-5" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/>
            </svg>
          </div>
          <div style="text-align:left;">
            <div style="font-weight:700;color:#1a1a1a;font-size:.95rem;">Nigeria — Paystack</div>
            <div style="font-size:.78rem;color:#777;">Bank transfer, USSD, card, mobile money &bull; NGN</div>
          </div>
          <div style="margin-left:auto;background:#e8faf0;color:#00b94f;font-size:.7rem;
            font-weight:700;padding:.2rem .5rem;border-radius:4px;">NGN</div>
        </button>

        <!-- Stripe -->
        <button onclick="IDTPayment.selectStripe()"
          style="width:100%;padding:1rem 1.2rem;margin-bottom:.75rem;border:2px solid #eee;
          border-radius:10px;background:#fff;cursor:pointer;display:flex;align-items:center;
          gap:1rem;transition:border-color .2s,box-shadow .2s;"
          onmouseover="this.style.borderColor='#6772e5';this.style.boxShadow='0 2px 12px rgba(103,114,229,.15)'"
          onmouseout="this.style.borderColor='#eee';this.style.boxShadow='none'">
          <div style="width:44px;height:44px;background:#f0f1fd;border-radius:8px;
            display:flex;align-items:center;justify-content:circle;flex-shrink:0;">
            <svg width="44" height="44" viewBox="0 0 44 44">
              <rect width="44" height="44" rx="8" fill="#f0f1fd"/>
              <path d="M22 14c-4 0-7 2-7 5.5 0 4.5 7 4.5 7 8 0 1.5-1.5 2.5-3.5 2.5-2 0-4-.8-5.5-2l-1 3.5c1.5 1 4 1.5 6.5 1.5 4.5 0 7.5-2 7.5-6 0-4.5-7-4.5-7-8 0-1.5 1-2.5 3-2.5 1.5 0 3 .5 4.5 1.5l1-3c-1.5-1-3.5-1.5-6-1.5z" fill="#6772e5"/>
            </svg>
          </div>
          <div style="text-align:left;">
            <div style="font-weight:700;color:#1a1a1a;font-size:.95rem;">International — Stripe</div>
            <div style="font-size:.78rem;color:#777;">Visa, Mastercard, Apple Pay, Google Pay</div>
          </div>
          <div style="margin-left:auto;display:flex;gap:4px;">
            <span style="background:#f0f1fd;color:#6772e5;font-size:.7rem;font-weight:700;padding:.2rem .5rem;border-radius:4px;">USD</span>
            <span style="background:#f0f1fd;color:#6772e5;font-size:.7rem;font-weight:700;padding:.2rem .5rem;border-radius:4px;">GBP</span>
            <span style="background:#f0f1fd;color:#6772e5;font-size:.7rem;font-weight:700;padding:.2rem .5rem;border-radius:4px;">EUR</span>
          </div>
        </button>

        <!-- Security badge -->
        <div style="display:flex;align-items:center;justify-content:center;gap:.5rem;
          margin-top:.75rem;padding:.6rem;background:#f8f9fb;border-radius:8px;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1B3A6B" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span style="font-size:.72rem;color:#666;">All transactions TLS 1.3 encrypted &bull; 3D Secure verified</span>
        </div>
      </div>

      <!-- View: Paystack form ──────────────────────────────────────────────── -->
      <div id="idt-view-paystack-form" style="display:none;">
        <button onclick="IDTPayment._showView('gateway-select')"
          style="background:none;border:none;color:#1B3A6B;cursor:pointer;font-size:.85rem;
          display:flex;align-items:center;gap:.3rem;margin-bottom:1rem;padding:0;">
          &#8592; Back
        </button>
        <div style="font-size:1rem;font-weight:700;color:#1B3A6B;margin-bottom:1rem;">Pay with Paystack</div>
        <label style="display:block;font-size:.83rem;color:#555;margin-bottom:.3rem;">Full Name</label>
        <input id="idt-ps-name" type="text" placeholder="Your full name"
          style="width:100%;padding:.7rem .9rem;border:1.5px solid #ddd;border-radius:8px;
          font-size:.92rem;margin-bottom:.8rem;box-sizing:border-box;outline:none;"
          onfocus="this.style.borderColor='#00b94f'" onblur="this.style.borderColor='#ddd'">
        <label style="display:block;font-size:.83rem;color:#555;margin-bottom:.3rem;">Email Address</label>
        <input id="idt-ps-email" type="email" placeholder="your@email.com"
          style="width:100%;padding:.7rem .9rem;border:1.5px solid #ddd;border-radius:8px;
          font-size:.92rem;margin-bottom:.8rem;box-sizing:border-box;outline:none;"
          onfocus="this.style.borderColor='#00b94f'" onblur="this.style.borderColor='#ddd'">
        <label style="display:block;font-size:.83rem;color:#555;margin-bottom:.3rem;">Phone (optional)</label>
        <input id="idt-ps-phone" type="tel" placeholder="+234 800 000 0000"
          style="width:100%;padding:.7rem .9rem;border:1.5px solid #ddd;border-radius:8px;
          font-size:.92rem;margin-bottom:1rem;box-sizing:border-box;outline:none;"
          onfocus="this.style.borderColor='#00b94f'" onblur="this.style.borderColor='#ddd'">
        <div id="idt-ps-error" style="color:#e53e3e;font-size:.83rem;margin-bottom:.6rem;display:none;"></div>
        <button id="idt-ps-btn" onclick="IDTPayment.processPaystack()"
          style="width:100%;padding:.9rem;background:#00b94f;color:#fff;border:none;border-radius:10px;
          font-size:1rem;font-weight:700;cursor:pointer;transition:background .2s;">
          Pay <span id="idt-ps-amount"></span> with Paystack
        </button>
      </div>

      <!-- View: Stripe form ───────────────────────────────────────────────── -->
      <div id="idt-view-stripe-form" style="display:none;">
        <button onclick="IDTPayment._showView('gateway-select')"
          style="background:none;border:none;color:#1B3A6B;cursor:pointer;font-size:.85rem;
          display:flex;align-items:center;gap:.3rem;margin-bottom:1rem;padding:0;">
          &#8592; Back
        </button>
        <div style="font-size:1rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">International Payment</div>

        <!-- Currency selector -->
        <div style="display:flex;gap:.5rem;margin-bottom:1rem;">
          <label style="font-size:.83rem;color:#555;align-self:center;margin-right:.3rem;">Currency:</label>
          <button class="idt-currency-btn" data-cur="USD" onclick="IDTPayment.selectCurrency('USD')"
            style="padding:.35rem .8rem;border:1.5px solid #6772e5;border-radius:6px;background:#f0f1fd;
            color:#6772e5;font-weight:700;font-size:.82rem;cursor:pointer;">USD $</button>
          <button class="idt-currency-btn" data-cur="GBP" onclick="IDTPayment.selectCurrency('GBP')"
            style="padding:.35rem .8rem;border:1.5px solid #ddd;border-radius:6px;background:#fff;
            color:#555;font-weight:700;font-size:.82rem;cursor:pointer;">GBP £</button>
          <button class="idt-currency-btn" data-cur="EUR" onclick="IDTPayment.selectCurrency('EUR')"
            style="padding:.35rem .8rem;border:1.5px solid #ddd;border-radius:6px;background:#fff;
            color:#555;font-weight:700;font-size:.82rem;cursor:pointer;">EUR €</button>
        </div>
        <div id="idt-stripe-amount-display"
          style="font-size:.9rem;color:#555;margin-bottom:.8rem;"></div>

        <label style="display:block;font-size:.83rem;color:#555;margin-bottom:.3rem;">Email Address</label>
        <input id="idt-st-email" type="email" placeholder="your@email.com"
          style="width:100%;padding:.7rem .9rem;border:1.5px solid #ddd;border-radius:8px;
          font-size:.92rem;margin-bottom:.8rem;box-sizing:border-box;outline:none;"
          onfocus="this.style.borderColor='#6772e5'" onblur="this.style.borderColor='#ddd'">

        <!-- Stripe Elements mount point -->
        <div id="idt-stripe-elements"
          style="border:1.5px solid #ddd;border-radius:8px;padding:.75rem;margin-bottom:.8rem;
          min-height:44px;"></div>

        <div id="idt-st-error" style="color:#e53e3e;font-size:.83rem;margin-bottom:.6rem;display:none;"></div>
        <button id="idt-st-btn" onclick="IDTPayment.processStripe()"
          style="width:100%;padding:.9rem;background:#6772e5;color:#fff;border:none;border-radius:10px;
          font-size:1rem;font-weight:700;cursor:pointer;transition:background .2s;">
          Pay <span id="idt-st-amount"></span>
        </button>
      </div>

      <!-- View: Success ───────────────────────────────────────────────────── -->
      <div id="idt-view-payment-success" style="display:none;text-align:center;padding:1rem 0;">
        <div style="font-size:3rem;margin-bottom:.5rem;">✅</div>
        <div style="font-size:1.2rem;font-weight:700;color:#1B3A6B;margin-bottom:.5rem;">Payment Successful!</div>
        <p style="font-size:.9rem;color:#555;" id="idt-success-msg">
          Thank you for your order. Our team will contact you shortly to confirm delivery details.
        </p>
        <button onclick="IDTPayment.close()"
          style="margin-top:1rem;padding:.75rem 2rem;background:#1B3A6B;color:#fff;border:none;
          border-radius:8px;font-size:.95rem;font-weight:700;cursor:pointer;">
          Close
        </button>
      </div>

      <!-- View: Error ─────────────────────────────────────────────────────── -->
      <div id="idt-view-payment-error" style="display:none;text-align:center;padding:1rem 0;">
        <div style="font-size:3rem;margin-bottom:.5rem;">❌</div>
        <div style="font-size:1.1rem;font-weight:700;color:#c53030;margin-bottom:.5rem;">Payment Failed</div>
        <p style="font-size:.88rem;color:#555;" id="idt-error-msg">Something went wrong. Please try again.</p>
        <button onclick="IDTPayment._showView('gateway-select')"
          style="margin-top:.5rem;padding:.7rem 1.5rem;background:#1B3A6B;color:#fff;border:none;
          border-radius:8px;font-size:.9rem;font-weight:700;cursor:pointer;">
          Try Again
        </button>
      </div>

    </div><!-- /padding -->
  </div><!-- /modal card -->
</div><!-- /modal overlay -->`;
  }

  function _attachModalEvents() {
    // Close on backdrop click
    document.getElementById('idt-checkout-modal').addEventListener('click', function (e) {
      if (e.target === this) closeCheckout();
    });
  }

  // ── Paystack flow ──────────────────────────────────────────────────────────
  let _selectedCurrency = 'USD';

  async function selectPaystack() {
    _showView('paystack-form');
    document.getElementById('idt-ps-amount').textContent =
      formatCurrency(_currentOrder.priceNgn, 'NGN');
  }

  async function processPaystack() {
    const email = document.getElementById('idt-ps-email').value.trim();
    const name  = document.getElementById('idt-ps-name').value.trim();
    const errEl = document.getElementById('idt-ps-error');
    errEl.style.display = 'none';

    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      errEl.textContent = 'Please enter a valid email address.';
      errEl.style.display = 'block';
      return;
    }

    const btn = document.getElementById('idt-ps-btn');
    btn.disabled = true;
    btn.textContent = 'Initializing...';

    try {
      await loadPaymentConfig();
      const res = await fetch('/api/paystack/initialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          amount: _currentOrder.priceNgn,
          product_name: _currentOrder.productName,
          callback_url: window.location.origin + '/payment/verify',
        }),
      });
      const data = await res.json();
      if (data.authorization_url) {
        // Redirect to Paystack hosted checkout
        window.location.href = data.authorization_url;
      } else {
        throw new Error(data.error || 'Could not initialize payment');
      }
    } catch (e) {
      errEl.textContent = e.message || 'Payment failed. Please try again.';
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Try Again';
    }
  }

  // ── Stripe flow ────────────────────────────────────────────────────────────
  function selectCurrency(currency) {
    _selectedCurrency = currency;
    document.querySelectorAll('.idt-currency-btn').forEach(b => {
      const active = b.dataset.cur === currency;
      b.style.borderColor = active ? '#6772e5' : '#ddd';
      b.style.background = active ? '#f0f1fd' : '#fff';
      b.style.color = active ? '#6772e5' : '#555';
    });
    const foreignAmt = ngnToForeign(_currentOrder.priceNgn, currency);
    document.getElementById('idt-stripe-amount-display').textContent =
      `Approx. ${formatCurrency(foreignAmt, currency)} (converted from ${formatCurrency(_currentOrder.priceNgn, 'NGN')})`;
    document.getElementById('idt-st-amount').textContent = formatCurrency(foreignAmt, currency);
  }

  async function selectStripe() {
    _showView('stripe-form');
    selectCurrency('USD');

    // Load Stripe.js lazily
    if (!window.Stripe) {
      const s = document.createElement('script');
      s.src = 'https://js.stripe.com/v3/';
      document.head.appendChild(s);
      await new Promise(r => s.onload = r);
    }

    await loadPaymentConfig();
    if (!_config.stripe_publishable_key) {
      document.getElementById('idt-st-error').textContent = 'Stripe is not configured yet.';
      document.getElementById('idt-st-error').style.display = 'block';
      return;
    }

    _stripe = Stripe(_config.stripe_publishable_key);

    // Create PaymentIntent on server
    const foreignAmt = ngnToForeign(_currentOrder.priceNgn, _selectedCurrency);
    const res = await fetch('/api/stripe/create-payment-intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: foreignAmt,
        currency: _selectedCurrency,
        product_name: _currentOrder.productName,
        email: document.getElementById('idt-st-email').value || '',
      }),
    });
    const data = await res.json();
    if (!data.client_secret) {
      document.getElementById('idt-st-error').textContent = data.error || 'Payment setup failed.';
      document.getElementById('idt-st-error').style.display = 'block';
      return;
    }

    _stripeElements = _stripe.elements({ clientSecret: data.client_secret });
    _paymentElement = _stripeElements.create('payment');
    _paymentElement.mount('#idt-stripe-elements');
  }

  async function processStripe() {
    if (!_stripe || !_stripeElements) {
      await selectStripe();
      return;
    }
    const btn = document.getElementById('idt-st-btn');
    const errEl = document.getElementById('idt-st-error');
    errEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Processing...';

    const { error } = await _stripe.confirmPayment({
      elements: _stripeElements,
      confirmParams: {
        return_url: window.location.origin + '/payment/verify',
        receipt_email: document.getElementById('idt-st-email').value || undefined,
      },
    });

    if (error) {
      errEl.textContent = error.message;
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = `Pay ${document.getElementById('idt-st-amount').textContent}`;
    }
    // If no error, Stripe redirects to return_url
  }

  // ── Public API ─────────────────────────────────────────────────────────────
  window.IDTPayment = {
    open: openCheckout,
    close: closeCheckout,
    selectPaystack,
    selectStripe,
    selectCurrency,
    processPaystack,
    processStripe,
    _showView,
  };

})();
