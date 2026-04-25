/**
 * Furniture Placement Integration Helper
 * 
 * Quick setup functions for integrating the furniture placement scene
 * into existing pages (interior.html, admin panel, etc.)
 */

/**
 * Initialize furniture placement in a page section
 * @param {string} containerId - ID of the container element
 * @param {string} controlsPanelId - ID of the controls panel element
 * @param {Object} options - Configuration options
 * @returns {Object} Scene and UI instances
 */
async function initFurniturePlacement(containerId, controlsPanelId, options = {}) {
  try {
    // Verify elements exist
    const container = document.getElementById(containerId);
    const controlsPanel = document.getElementById(controlsPanelId);

    if (!container || !controlsPanel) {
      throw new Error(`Container or controls panel not found`);
    }

    // Set container size if not already set
    if (!container.style.width) container.style.width = '100%';
    if (!container.style.height) container.style.height = 'auto';

    // Create scene
    const scene = new FurniturePlacementScene(`#${containerId}`, {
      gridSize: options.gridSize || 0.5,
      snapEnabled: options.snapEnabled !== false,
      cameraDistance: options.cameraDistance || 15,
      lightingPreset: options.lightingPreset || 'studio',
      backgroundColor: options.backgroundColor || 0xf5f0e8
    });

    // Create UI
    const ui = new FurniturePlacementUI(scene, `#${controlsPanelId}`);

    console.log('✓ Furniture Placement initialized in:', containerId);

    return { scene, ui };
  } catch (error) {
    console.error('Failed to initialize furniture placement:', error);
    throw error;
  }
}

/**
 * Load models from admin panel into the scene
 * @param {Object} scene - FurniturePlacementScene instance
 * @param {Array} modelList - Array of model filenames or URLs
 */
async function loadModelsFromAdmin(scene, modelList) {
  for (const modelPath of modelList) {
    try {
      const url = modelPath.startsWith('http')
        ? modelPath
        : `/idl-images/${modelPath}`;

      // Fetch metadata if available
      const metadataUrl = modelPath.includes('.')
        ? `/api/model-metadata/${modelPath}`
        : null;

      let metadata = null;
      if (metadataUrl) {
        try {
          const response = await fetch(metadataUrl);
          if (response.ok) {
            metadata = await response.json();
          }
        } catch (e) {
          console.warn('Could not load metadata:', e);
        }
      }

      // Random position on grid
      const position = {
        x: (Math.random() - 0.5) * 10,
        y: 0,
        z: (Math.random() - 0.5) * 10
      };

      await scene.loadModel(url, position, metadata);
      console.log('✓ Loaded:', modelPath);
    } catch (error) {
      console.error('Failed to load model:', modelPath, error);
    }
  }
}

/**
 * Setup drag-and-drop model upload
 * @param {Object} scene - FurniturePlacementScene instance
 * @param {Element} dropZone - Element to use as drop zone
 */
function setupModelDropZone(scene, dropZone) {
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    dropZone.style.borderColor = '#C4A882';
    dropZone.style.backgroundColor = 'rgba(196, 168, 130, 0.1)';
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = '#ddd';
    dropZone.style.backgroundColor = 'transparent';
  });

  dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#ddd';
    dropZone.style.backgroundColor = 'transparent';

    const files = Array.from(e.dataTransfer.files);
    const glbFiles = files.filter(f =>
      f.type === 'application/octet-stream' ||
      f.name.endsWith('.glb') ||
      f.name.endsWith('.gltf')
    );

    for (const file of glbFiles) {
      try {
        const url = URL.createObjectURL(file);
        const position = {
          x: (Math.random() - 0.5) * 10,
          y: 0,
          z: (Math.random() - 0.5) * 10
        };
        await scene.loadModel(url, position);
        console.log('✓ Loaded from file:', file.name);
      } catch (error) {
        console.error('Failed to load file:', file.name, error);
      }
    }
  });
}

/**
 * Create a modal furniture placement viewer
 * @param {Object} options - Configuration
 * @returns {Object} Modal instance with open/close methods
 */
function createFurniturePlacementModal(options = {}) {
  const modalId = 'furniture-placement-modal';
  const containerId = 'furniture-placement-container';
  const controlsId = 'furniture-placement-controls';

  // Create modal HTML
  const modalHTML = `
    <div id="${modalId}" style="
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: none;
      z-index: 1000;
      overflow: auto;
    ">
      <div style="
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border-radius: 12px;
        width: 95vw;
        height: 95vh;
        max-width: 1400px;
        display: flex;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      ">
        <!-- Close button -->
        <button onclick="document.getElementById('${modalId}').style.display='none'" style="
          position: absolute;
          top: 15px;
          right: 15px;
          background: #d9534f;
          color: white;
          border: none;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 18px;
          z-index: 10;
          display: flex;
          align-items: center;
          justify-content: center;
        ">✕</button>

        <!-- Canvas -->
        <div id="${containerId}" style="
          flex: 1;
          background: linear-gradient(135deg, #f5f0e8 0%, #e8dcc8 100%);
          border-radius: 12px 0 0 12px;
        "></div>

        <!-- Controls -->
        <div id="${controlsId}" style="
          width: 320px;
          background: white;
          border-radius: 0 12px 12px 0;
          overflow-y: auto;
          border-left: 1px solid #eee;
        "></div>
      </div>
    </div>
  `;

  // Insert modal into page
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  return {
    open: async function () {
      const modal = document.getElementById(modalId);
      modal.style.display = 'block';

      // Initialize scene if not already done
      if (!this.scene) {
        try {
          const result = await initFurniturePlacement(
            containerId,
            controlsId,
            options
          );
          this.scene = result.scene;
          this.ui = result.ui;
        } catch (error) {
          console.error('Failed to open furniture placement:', error);
          modal.style.display = 'none';
        }
      }
    },
    close: function () {
      document.getElementById(modalId).style.display = 'none';
    },
    getScene: function () {
      return this.scene;
    },
    getLayout: function () {
      return this.scene ? this.scene.getModelPositions() : [];
    }
  };
}

/**
 * Add furniture placement button to a page
 * @param {string} containerSelector - CSS selector for button container
 * @param {Object} sceneOptions - Options for the scene
 */
function addFurniturePlacementButton(containerSelector, sceneOptions = {}) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  const button = document.createElement('button');
  button.textContent = '🛋️ Furniture Placement';
  button.style.cssText = `
    padding: 0.75rem 1.5rem;
    background: #1B3A6B;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  `;

  button.addEventListener('mouseover', () => {
    button.style.background = '#2A5298';
    button.style.transform = 'translateY(-2px)';
    button.style.boxShadow = '0 4px 12px rgba(27, 58, 107, 0.3)';
  });

  button.addEventListener('mouseout', () => {
    button.style.background = '#1B3A6B';
    button.style.transform = 'translateY(0)';
    button.style.boxShadow = 'none';
  });

  const modal = createFurniturePlacementModal(sceneOptions);

  button.addEventListener('click', () => modal.open());

  container.appendChild(button);

  return {
    button,
    modal
  };
}

/**
 * Example usage in a page:
 *
 * // 1. Basic modal with button
 * addFurniturePlacementButton('#page-actions', {
 *   lightingPreset: 'studio',
 *   backgroundColor: 0xf5f0e8
 * });
 *
 * // 2. Inline in container
 * const container = document.getElementById('my-container');
 * container.style.width = '100%';
 * container.style.height = '600px';
 * 
 * initFurniturePlacement('my-container', 'my-controls', {
 *   lightingPreset: 'light'
 * }).then(({scene, ui}) => {
 *   // Load models
 *   loadModelsFromAdmin(scene, ['Sofa.glb', 'Table.glb']);
 * });
 *
 * // 3. With file upload
 * const scene = new FurniturePlacementScene('#canvas');
 * const dropZone = document.getElementById('drop-area');
 * setupModelDropZone(scene, dropZone);
 */

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initFurniturePlacement,
    loadModelsFromAdmin,
    setupModelDropZone,
    createFurniturePlacementModal,
    addFurniturePlacementButton
  };
}
