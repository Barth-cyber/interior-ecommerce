/**
 * Furniture Placement UI Controller
 * 
 * Provides UI controls for the FurniturePlacementScene:
 * - Model loading and management
 * - Lighting preset controls
 * - Grid snap controls
 * - Model position export/import
 */

class FurniturePlacementUI {
  constructor(sceneInstance, controlsSelector) {
    this.scene = sceneInstance;
    this.controlsContainer = document.querySelector(controlsSelector);
    this.init();
  }

  init() {
    if (!this.controlsContainer) return;
    this.createControls();
    this.attachEventListeners();
  }

  createControls() {
    this.controlsContainer.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1rem; padding: 1.5rem; background: rgba(255, 255, 255, 0.95); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 320px;">
        
        <!-- Model Loading -->
        <div>
          <label style="display: block; font-weight: 600; margin-bottom: 0.5rem; color: #1B3A6B;">Load Model</label>
          <select id="modelSelect" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-size: 0.9rem;">
            <option value="">Select a furniture model...</option>
            <option value="https://modelviewer.dev/shared-assets/models/Astronaut.glb">Astronaut (Demo)</option>
            <option value="https://modelviewer.dev/shared-assets/models/RobotExpressive.glb">Robot (Demo)</option>
            <option value="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Avocado/glTF-Binary/Avocado.glb">Avocado (Demo)</option>
          </select>
          <button id="loadModelBtn" style="width: 100%; margin-top: 0.5rem; padding: 0.5rem; background: #1B3A6B; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">Load Model</button>
        </div>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 0.5rem 0;">

        <!-- Lighting Presets -->
        <div>
          <label style="display: block; font-weight: 600; margin-bottom: 0.5rem; color: #1B3A6B;">Lighting</label>
          <div style="display: flex; gap: 0.5rem;">
            <button class="lighting-btn" data-preset="studio" style="flex: 1; padding: 0.5rem; background: #C4A882; color: white; border: 2px solid #C4A882; border-radius: 4px; cursor: pointer; font-weight: 600;">Studio</button>
            <button class="lighting-btn" data-preset="light" style="flex: 1; padding: 0.5rem; background: #f5f5f5; color: #1B3A6B; border: 2px solid #ddd; border-radius: 4px; cursor: pointer; font-weight: 600;">Light</button>
            <button class="lighting-btn" data-preset="dark" style="flex: 1; padding: 0.5rem; background: #333; color: white; border: 2px solid #333; border-radius: 4px; cursor: pointer; font-weight: 600;">Dark</button>
          </div>
        </div>

        <!-- Grid Controls -->
        <div>
          <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
            <input type="checkbox" id="snapToggle" checked style="width: 18px; height: 18px; cursor: pointer;">
            <span style="font-weight: 600; color: #1B3A6B;">Snap to Grid (0.5m)</span>
          </label>
          <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; align-items: center;">
            <label style="font-size: 0.9rem; color: #666;">Grid Size:</label>
            <input type="range" id="gridSize" min="0.25" max="2" step="0.25" value="0.5" style="flex: 1;">
            <span id="gridValue" style="font-size: 0.9rem; color: #666; min-width: 40px;">0.5m</span>
          </div>
        </div>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 0.5rem 0;">

        <!-- Scene Management -->
        <div>
          <label style="display: block; font-weight: 600; margin-bottom: 0.5rem; color: #1B3A6B;">Scene</label>
          <button id="exportBtn" style="width: 100%; padding: 0.5rem; background: #7B5C3E; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; margin-bottom: 0.5rem;">Export Layout</button>
          <button id="clearBtn" style="width: 100%; padding: 0.5rem; background: #d9534f; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">Clear Scene</button>
        </div>

        <!-- Keyboard Hints -->
        <div style="background: #f9f9f9; padding: 0.75rem; border-radius: 4px; font-size: 0.85rem; color: #666; border-left: 3px solid #C4A882;">
          <strong style="color: #1B3A6B;">Keyboard Shortcuts:</strong>
          <div style="margin-top: 0.5rem; line-height: 1.6;">
            <div>↑↓←→ or WASD: Move</div>
            <div>Q/E: Rotate</div>
            <div>DEL: Delete</div>
            <div>Scroll: Zoom</div>
          </div>
        </div>

        <!-- Info -->
        <div id="infoBox" style="background: #f0f8ff; padding: 0.75rem; border-radius: 4px; font-size: 0.85rem; color: #1B3A6B; border-left: 3px solid #1B3A6B; display: none;">
          <strong>Model Info:</strong>
          <div id="modelInfo" style="margin-top: 0.3rem;"></div>
        </div>
      </div>
    `;
  }

  attachEventListeners() {
    // Load model
    const loadModelBtn = this.controlsContainer.querySelector('#loadModelBtn');
    const modelSelect = this.controlsContainer.querySelector('#modelSelect');
    
    loadModelBtn?.addEventListener('click', async () => {
      const url = modelSelect.value;
      if (!url) {
        alert('Please select a model');
        return;
      }
      
      loadModelBtn.disabled = true;
      loadModelBtn.textContent = 'Loading...';
      
      try {
        const position = {
          x: (Math.random() - 0.5) * 10,
          y: 0,
          z: (Math.random() - 0.5) * 10
        };
        await this.scene.loadModel(url, position);
        this.showInfo(`Model loaded! Models in scene: ${this.scene.models.length}`);
      } catch (error) {
        alert('Error loading model: ' + error.message);
      } finally {
        loadModelBtn.disabled = false;
        loadModelBtn.textContent = 'Load Model';
      }
    });

    // Lighting presets
    this.controlsContainer.querySelectorAll('.lighting-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const preset = btn.dataset.preset;
        this.scene.setLightingPreset(preset);
        
        // Update button styling
        this.controlsContainer.querySelectorAll('.lighting-btn').forEach(b => {
          b.style.borderWidth = '2px';
        });
        btn.style.borderWidth = '3px';
      });
    });

    // Snap to grid
    const snapToggle = this.controlsContainer.querySelector('#snapToggle');
    snapToggle?.addEventListener('change', () => {
      const enabled = this.scene.toggleSnapToGrid();
      this.showInfo(enabled ? 'Grid snap enabled' : 'Grid snap disabled');
    });

    // Grid size
    const gridSizeSlider = this.controlsContainer.querySelector('#gridSize');
    const gridValue = this.controlsContainer.querySelector('#gridValue');
    gridSizeSlider?.addEventListener('input', (e) => {
      const size = parseFloat(e.target.value);
      this.scene.setGridSize(size);
      gridValue.textContent = `${size.toFixed(2)}m`;
    });

    // Export layout
    const exportBtn = this.controlsContainer.querySelector('#exportBtn');
    exportBtn?.addEventListener('click', () => {
      const positions = this.scene.getModelPositions();
      const jsonStr = JSON.stringify(positions, null, 2);
      console.log('Layout exported:', positions);
      
      // Copy to clipboard
      navigator.clipboard.writeText(jsonStr).then(() => {
        this.showInfo('Layout copied to clipboard!');
      }).catch(err => {
        // Fallback: create download
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'furniture-layout.json';
        a.click();
        URL.revokeObjectURL(url);
      });
    });

    // Clear scene
    const clearBtn = this.controlsContainer.querySelector('#clearBtn');
    clearBtn?.addEventListener('click', () => {
      if (confirm('Clear all models from the scene?')) {
        this.scene.clearScene();
        this.showInfo('Scene cleared');
      }
    });
  }

  showInfo(message) {
    const infoBox = this.controlsContainer.querySelector('#infoBox');
    const modelInfo = this.controlsContainer.querySelector('#modelInfo');
    
    if (infoBox && modelInfo) {
      modelInfo.textContent = message;
      infoBox.style.display = 'block';
      
      setTimeout(() => {
        infoBox.style.display = 'none';
      }, 3000);
    }
  }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FurniturePlacementUI;
}
