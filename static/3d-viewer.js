// Lightweight 3D viewer using <model-viewer> (Web Components)
// Usage: <model-viewer src="/idl-images/model.glb" ...></model-viewer>
// This script ensures <model-viewer> is loaded if not present
(function(){
  if (!window.customElements.get('model-viewer')) {
    const script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js';
    document.head.appendChild(script);
  }
})();
