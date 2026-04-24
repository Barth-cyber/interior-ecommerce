/**
 * Interior Duct Ltd  Payment Integration
 * Handles Paystack (Nigeria/NGN) and Stripe (International USD/GBP/EUR)
 *
 * Include this script on any page that needs checkout:
 *   <script src="/static/payment.js"></script>
 * Also load Stripe.js in your HTML head:
 *   <script src="https://js.stripe.com/v3/"></script>
 */

(function () {
  'use strict';

  // State
  let _config = { paystack_public_key: '', stripe_publishable_key: '' };
  let _stripe = null;
  let _stripeElements = null;
  let _paymentElement = null;
  let _currentOrder = null;

  // Bootstrap: fetch public keys from server
  async function loadPaymentConfig() {
    try {
      const res = await fetch('/api/payment-config');
      _config = await res.json();
    } catch (e) {
      console.error('Could not load payment config:', e);
    }
  }

  // Currency conversion helpers
  const EXCHANGE_RATES = {
    USD: 0.00064,  // Approximate NGN  USD
    GBP: 0.00051,
    EUR: 0.00059,
  };

  function ngnToForeign(amountNgn, currency) {
    const rate = EXCHANGE_RATES[currency.toUpperCase()] || EXCHANGE_RATES.USD;
    return Math.ceil(amountNgn * rate);