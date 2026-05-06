// Central backend config + lightweight fetch proxy for frontend-only deployments
;(function(){
  try {
    // Resolve backend URL from meta tag, global override, or sensible default
    const meta = document.querySelector && document.querySelector('meta[name="backend-url"]');
    const fromMeta = meta && meta.content && meta.content.trim();
    const envOverride = window.DUCT_AI_BACKEND_URL || window.__BACKEND_URL__ || null;
    const isLocal = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:');
    const defaultLocal = isLocal ? 'http://localhost:5000' : '';
    const BACKEND = (envOverride || fromMeta || defaultLocal || '').replace(/\/$/, '');

    if (!BACKEND) {
      // No backend configured — nothing to proxy
      window.getBackendUrl = () => '';
      return;
    }

    // Expose canonical variables used across the frontend
    window.DUCT_AI_BACKEND_URL = window.DUCT_AI_BACKEND_URL || BACKEND;
    window.__BACKEND_URL__ = window.__BACKEND_URL__ || BACKEND;

    // Lightweight fetch wrapper: prepend BACKEND for same-origin relative paths
    if (window.fetch) {
      const _fetch = window.fetch.bind(window);
      window.fetch = function(input, init) {
        try {
          // string URL
          if (typeof input === 'string') {
            if (input.startsWith('/')) {
              input = BACKEND + input;
            } else if (!/^https?:\/\//i.test(input) && !input.startsWith('data:') && !input.startsWith('blob:')) {
              input = BACKEND + '/' + input;
            }
            return _fetch(input, init);
          }

          // Request object
          if (input && input.url) {
            const reqUrl = input.url;
            if (reqUrl.startsWith(window.location.origin)) {
              const path = reqUrl.replace(window.location.origin, '');
              input = new Request(BACKEND + path, input);
            }
          }
          return _fetch(input, init);
        } catch (e) {
          return _fetch(input, init);
        }
      };
    }

    window.getBackendUrl = () => BACKEND;
  } catch (e) {
    console && console.warn && console.warn('backend-config init failed', e);
  }
})();
