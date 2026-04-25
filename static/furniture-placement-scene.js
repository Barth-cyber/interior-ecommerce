/**
 * Furniture Placement Scene
 * 
 * Advanced Three.js scene with:
 * - Drag-and-drop furniture placement
 * - Snap-to-grid functionality
 * - Lighting presets (studio, light, dark)
 * - GLB file loading with Draco decompression
 * - Interactive camera controls
 * 
 * Usage:
 * const scene = new FurniturePlacementScene('#canvas-container');
 * scene.loadModel('path/to/model.glb');
 */

class FurniturePlacementScene {
  constructor(containerSelector, options = {}) {
    this.container = document.querySelector(containerSelector);
    if (!this.container) {
      console.error(`Container not found: ${containerSelector}`);
      return;
    }

    // Configuration
    this.gridSize = options.gridSize || 0.5;
    this.snapEnabled = options.snapEnabled !== false;
    this.cameraDistance = options.cameraDistance || 15;
    this.lightingPreset = options.lightingPreset || 'studio';
    this.backgroundColor = options.backgroundColor || 0xf5f5f5;

    // LOD (Level of Detail) configuration
    this.lodEnabled = options.lodEnabled !== false;
    this.lodFocusDistance = options.lodFocusDistance || 10; // Distance to consider model "in focus"
    this.lodUpgradeDelay = options.lodUpgradeDelay || 500; // Delay before loading high-res

    // Scene objects
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.models = [];
    this.selectedModel = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.dragPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    this.dragPoint = new THREE.Vector3();
    this.isDragging = false;
    this.dragOffset = new THREE.Vector3();

    // Lights
    this.lights = {
      ambient: null,
      directional: null,
      pointLights: []
    };

    // GLTFLoader and Draco
    this.loader = null;
    this.dracoLoader = null;

    this.init();
  }

  init() {
    this.setupScene();
    this.setupCamera();
    this.setupRenderer();
    this.setupLoaders();
    this.setupLighting();
    this.setupGrid();
    this.setupControls();
    this.setupEventListeners();
    this.animate();
  }

  setupScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(this.backgroundColor);
    this.scene.fog = new THREE.Fog(this.backgroundColor, 50, 100);
  }

  setupCamera() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(
      75,
      width / height,
      0.1,
      1000
    );
    this.camera.position.set(10, this.cameraDistance, 10);
    this.camera.lookAt(0, 0, 0);
  }

  setupRenderer() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      shadowMap: { enabled: true, type: THREE.PCFShadowShadowMap }
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.container.appendChild(this.renderer.domElement);
  }

  setupLoaders() {
    this.loader = new THREE.GLTFLoader();
    
    // Setup Draco decompression with robust fallbacks
    this.dracoLoader = new THREE.DRACOLoader();
    
    // Primary decoder path (Google's CDN)
    const decoderPaths = [
      'https://www.gstatic.com/draco/versioned/decoders/1.5.5/',
      'https://cdn.jsdelivr.net/npm/three@r128/examples/js/libs/draco/gltf/',
      'https://unpkg.com/three@r128/examples/js/libs/draco/gltf/'
    ];
    
    // Try to set decoder path, fallback if CDN fails
    this.dracoLoader.setDecoderPath(decoderPaths[0]);
    
    // Provide fallback paths for robustness
    this.dracoLoader.setDecoderConfig({
      type: 'js', // Use JS decoder for broader compatibility
      wasmBinary: null
    });
    
    this.loader.setDRACOLoader(this.dracoLoader);
    
    // Setup loading manager for better control
    this.loadingManager = new THREE.LoadingManager();
    this.loadingManager.onStart = (url, itemsLoaded, itemsTotal) => {
      console.log(`Loading: ${url} (${itemsLoaded}/${itemsTotal})`);
    };
    this.loadingManager.onProgress = (url, itemsLoaded, itemsTotal) => {
      const progress = (itemsLoaded / itemsTotal) * 100;
      // Dispatch custom event for UI updates
      window.dispatchEvent(new CustomEvent('model-loading-progress', {
        detail: { url, progress, itemsLoaded, itemsTotal }
      }));
    };
    this.loadingManager.onLoad = () => {
      console.log('All assets loaded');
      window.dispatchEvent(new Event('models-loaded'));
    };
    this.loadingManager.onError = (url) => {
      console.error('Error loading asset:', url);
      window.dispatchEvent(new CustomEvent('model-loading-error', {
        detail: { url }
      }));
    };
    
    this.loader.manager = this.loadingManager;
  }

  setupLighting() {
    // Remove existing lights
    this.scene.children.forEach(child => {
      if (child instanceof THREE.Light) {
        this.scene.remove(child);
      }
    });

    const presets = {
      studio: {
        ambient: { color: 0xffffff, intensity: 0.6 },
        directional: { color: 0xffffff, intensity: 1.0, pos: [10, 20, 10] },
        points: [
          { color: 0xffd4a3, intensity: 0.4, pos: [-8, 10, 8] },
          { color: 0xa3d4ff, intensity: 0.3, pos: [8, 10, -8] }
        ]
      },
      light: {
        ambient: { color: 0xffffff, intensity: 0.9 },
        directional: { color: 0xffffff, intensity: 0.8, pos: [5, 15, 5] },
        points: []
      },
      dark: {
        ambient: { color: 0x404040, intensity: 0.4 },
        directional: { color: 0xffd4a3, intensity: 0.9, pos: [15, 25, 15] },
        points: [
          { color: 0xffd4a3, intensity: 0.6, pos: [-10, 12, 10] }
        ]
      }
    };

    const preset = presets[this.lightingPreset] || presets.studio;

    // Ambient light
    this.lights.ambient = new THREE.AmbientLight(
      preset.ambient.color,
      preset.ambient.intensity
    );
    this.scene.add(this.lights.ambient);

    // Directional light (sun)
    this.lights.directional = new THREE.DirectionalLight(
      preset.directional.color,
      preset.directional.intensity
    );
    this.lights.directional.position.set(...preset.directional.pos);
    this.lights.directional.castShadow = true;
    this.lights.directional.shadow.mapSize.width = 2048;
    this.lights.directional.shadow.mapSize.height = 2048;
    this.lights.directional.shadow.camera.far = 50;
    this.lights.directional.shadow.camera.left = -30;
    this.lights.directional.shadow.camera.right = 30;
    this.lights.directional.shadow.camera.top = 30;
    this.lights.directional.shadow.camera.bottom = -30;
    this.scene.add(this.lights.directional);

    // Point lights
    this.lights.pointLights = [];
    preset.points.forEach(pointPreset => {
      const pointLight = new THREE.PointLight(
        pointPreset.color,
        pointPreset.intensity,
        50
      );
      pointLight.position.set(...pointPreset.pos);
      pointLight.castShadow = true;
      this.scene.add(pointLight);
      this.lights.pointLights.push(pointLight);
    });
  }

  setupGrid() {
    const gridSize = 20;
    const gridDivisions = 40;

    const gridHelper = new THREE.GridHelper(
      gridSize,
      gridDivisions,
      0xcccccc,
      0xeeeeee
    );
    gridHelper.position.y = -0.01; // Slightly below ground
    this.scene.add(gridHelper);

    // Ground plane for reference
    const groundGeometry = new THREE.PlaneGeometry(gridSize * 2, gridSize * 2);
    const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.3 });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.02;
    ground.receiveShadow = true;
    this.scene.add(ground);
  }

  setupControls() {
    // Orbit-like controls for the camera
    this.controls = {
      autoRotate: false,
      autoRotateSpeed: 2,
      enablePan: true,
      enableZoom: true,
      minDistance: 5,
      maxDistance: 50,
      panSpeed: 1.0,
      rotateSpeed: 1.0
    };
  }

  setupEventListeners() {
    // Mouse events for selection and dragging
    this.container.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.container.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.container.addEventListener('mouseup', (e) => this.onMouseUp(e));
    this.container.addEventListener('wheel', (e) => this.onMouseWheel(e));

    // Handle window resize
    window.addEventListener('resize', () => this.onWindowResize());

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => this.onKeyDown(e));
  }

  onMouseMove(event) {
    if (!this.renderer) return;

    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    if (this.isDragging && this.selectedModel) {
      this.updateDraggedModel();
    } else {
      this.updateHover();
    }
  }

  onMouseDown(event) {
    if (event.button !== 0) return; // Left click only

    this.raycaster.setFromCamera(this.mouse, this.camera);

    const modelObjects = this.models.map(m => m.object).filter(o => o);
    const intersects = this.raycaster.intersectObjects(modelObjects, true);

    if (intersects.length > 0) {
      let selectedObject = intersects[0].object;
      while (selectedObject.parent && !this.models.find(m => m.object === selectedObject)) {
        selectedObject = selectedObject.parent;
      }

      this.selectedModel = this.models.find(m => m.object === selectedObject);
      if (this.selectedModel) {
        this.isDragging = true;
        this.dragOffset.copy(this.selectedModel.object.position).sub(intersects[0].point);
      }
    }
  }

  onMouseUp(event) {
    this.isDragging = false;
  }

  onMouseWheel(event) {
    event.preventDefault();

    const zoomSpeed = 0.5;
    const direction = this.camera.position.clone().normalize();
    const currentDistance = this.camera.position.length();
    const newDistance = event.deltaY > 0
      ? currentDistance + zoomSpeed
      : currentDistance - zoomSpeed;

    const clampedDistance = Math.max(5, Math.min(50, newDistance));
    this.camera.position.copy(direction.multiplyScalar(clampedDistance));
  }

  updateDraggedModel() {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    this.raycaster.ray.intersectPlane(this.dragPlane, this.dragPoint);

    let newPos = this.dragPoint.clone().add(this.dragOffset);

    // Snap to grid if enabled
    if (this.snapEnabled) {
      newPos.x = Math.round(newPos.x / this.gridSize) * this.gridSize;
      newPos.z = Math.round(newPos.z / this.gridSize) * this.gridSize;
    }

    this.selectedModel.object.position.copy(newPos);
  }

  updateHover() {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const modelObjects = this.models.map(m => m.object).filter(o => o);
    const intersects = this.raycaster.intersectObjects(modelObjects, true);

    this.models.forEach(model => {
      if (model.outlinePass) {
        model.outlinePass.selectedObjects = [];
      }
    });

    if (intersects.length > 0) {
      let hoveredObject = intersects[0].object;
      while (hoveredObject.parent && !this.models.find(m => m.object === hoveredObject)) {
        hoveredObject = hoveredObject.parent;
      }

      const hoveredModel = this.models.find(m => m.object === hoveredObject);
      if (hoveredModel && hoveredModel.outlinePass) {
        hoveredModel.outlinePass.selectedObjects = [hoveredObject];
      }

      this.container.style.cursor = 'grab';
    } else {
      this.container.style.cursor = 'default';
    }
  }

  onKeyDown(event) {
    if (!this.selectedModel) return;

    const moveStep = this.snapEnabled ? this.gridSize : 0.1;
    const model = this.selectedModel.object;

    switch (event.key.toLowerCase()) {
      case 'arrowup':
      case 'w':
        model.position.z -= moveStep;
        event.preventDefault();
        break;
      case 'arrowdown':
      case 's':
        model.position.z += moveStep;
        event.preventDefault();
        break;
      case 'arrowleft':
      case 'a':
        model.position.x -= moveStep;
        event.preventDefault();
        break;
      case 'arrowright':
      case 'd':
        model.position.x += moveStep;
        event.preventDefault();
        break;
      case 'q':
        model.rotation.y -= Math.PI / 8;
        event.preventDefault();
        break;
      case 'e':
        model.rotation.y += Math.PI / 8;
        event.preventDefault();
        break;
      case 'delete':
        this.removeModel(this.selectedModel);
        event.preventDefault();
        break;
      default:
        break;
    }
  }

  onMouseWheel(event) {
    event.preventDefault();
    const zoomSpeed = 0.5;
    const direction = this.camera.position.clone().normalize();
    const currentDistance = this.camera.position.length();
    const newDistance = event.deltaY > 0
      ? currentDistance + zoomSpeed
      : currentDistance - zoomSpeed;

    const clampedDistance = Math.max(5, Math.min(50, newDistance));
    this.camera.position.copy(direction.multiplyScalar(clampedDistance));
  }

  onWindowResize() {
    if (!this.renderer) return;

    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  loadModel(url, position = { x: 0, y: 0, z: 0 }, metadata = {}) {
    if (this.lodEnabled) {
      const lowResUrl = metadata.lodUrl || this.deriveLowResUrl(url);
      if (lowResUrl && lowResUrl !== url) {
        return this.loadModelWithLOD(url, lowResUrl, position, metadata);
      }
    }

    // Standard single-LOD loading
    return this.loadSingleModel(url, position, metadata, true);
  }

  deriveLowResUrl(highResUrl) {
    if (!highResUrl || typeof highResUrl !== 'string') return null;

    const url = new URL(highResUrl, window.location.href);
    const pathname = url.pathname;
    const extIndex = pathname.lastIndexOf('.glb');
    if (extIndex === -1) return null;

    const base = pathname.substring(0, extIndex);
    const lowResCandidates = [
      `${base}-lores.glb`,
      `${base}-lod0.glb`,
      `${base}-low.glb`,
      `${base}_lores.glb`
    ];

    // Choose first candidate that is different than the original
    return lowResCandidates.find(candidate => candidate !== pathname) || null;
  }

  loadSingleModel(url, position = { x: 0, y: 0, z: 0 }, metadata = {}, isHighRes = false) {
    return new Promise((resolve, reject) => {
      this.loader.load(
        url,
        (gltf) => {
          const model = gltf.scene;
          
          // Setup shadows
          model.traverse((node) => {
            if (node instanceof THREE.Mesh) {
              node.castShadow = true;
              node.receiveShadow = true;
            }
          });

          // Position model
          model.position.set(position.x, position.y, position.z);

          // Apply metadata
          if (metadata.cameraOrbit) {
            model.userData.cameraOrbit = metadata.cameraOrbit;
          }

          this.scene.add(model);

          const modelEntry = {
            object: model,
            url: url,
            metadata: metadata,
            animations: gltf.animations,
            isHighRes: isHighRes,
            isLoading: false
          };

          this.models.push(modelEntry);
          resolve(modelEntry);
        },
        undefined,
        (error) => {
          console.error('Error loading model:', url, error);
          reject(error);
        }
      );
    });
  }

  loadModelWithLOD(highResUrl, lowResUrl, position = { x: 0, y: 0, z: 0 }, metadata = {}) {
    return new Promise(async (resolve, reject) => {
      try {
        // First, load low-res version
        console.log('Loading low-res LOD:', lowResUrl);
        const lowResEntry = await this.loadSingleModel(lowResUrl, position, metadata, false);
        
        // Mark for high-res upgrade
        lowResEntry.highResUrl = highResUrl;
        lowResEntry.lodLevel = 0; // Currently showing LOD 0
        lowResEntry.upgradePending = true;
        lowResEntry.upgradeTimer = null;

        // Schedule high-res loading when model comes into focus
        this.scheduleModelUpgrade(lowResEntry);

        resolve(lowResEntry);
      } catch (error) {
        console.error('Error loading low-res LOD:', error);
        reject(error);
      }
    });
  }

  scheduleModelUpgrade(modelEntry) {
    if (!this.lodEnabled || !modelEntry.highResUrl) return;

    // Monitor focus and upgrade when needed
    const checkFocus = () => {
      if (!modelEntry.upgradePending) return; // Already upgraded
      if (modelEntry.isLoading) return; // Already loading

      const isInFocus = this.isModelInFocus(modelEntry);

      if (isInFocus) {
        // Clear any pending timers
        if (modelEntry.upgradeTimer) {
          clearTimeout(modelEntry.upgradeTimer);
        }

        // Delay upgrade slightly to avoid loading while dragging
        modelEntry.upgradeTimer = setTimeout(() => {
          this.upgradeModelLOD(modelEntry);
        }, this.lodUpgradeDelay);
      } else {
        // Model out of focus, clear timer
        if (modelEntry.upgradeTimer) {
          clearTimeout(modelEntry.upgradeTimer);
          modelEntry.upgradeTimer = null;
        }
      }

      // Continue checking if still pending
      if (modelEntry.upgradePending) {
        requestAnimationFrame(checkFocus);
      }
    };

    checkFocus();
  }

  isModelInFocus(modelEntry) {
    // Model is in focus if:
    // 1. It's selected
    // 2. It's within focus distance of camera
    // 3. It's visible to the camera (frustum check)

    if (this.selectedModel === modelEntry) {
      return true; // Selected models are always in focus
    }

    const distanceToCamera = this.camera.position.distanceTo(
      modelEntry.object.position
    );

    if (distanceToCamera > this.lodFocusDistance) {
      return false; // Too far away
    }

    // Check if model is in camera frustum
    const frustum = new THREE.Frustum();
    frustum.setFromProjectionMatrix(
      new THREE.Matrix4().multiplyMatrices(
        this.camera.projectionMatrix,
        this.camera.matrixWorldInverse
      )
    );

    return frustum.intersectsObject(modelEntry.object);
  }

  upgradeModelLOD(modelEntry) {
    if (!modelEntry.upgradePending || modelEntry.isLoading) return;

    modelEntry.isLoading = true;
    console.log('Upgrading to high-res LOD:', modelEntry.highResUrl);

    this.loader.load(
      modelEntry.highResUrl,
      (gltf) => {
        const highResModel = gltf.scene;

        // Setup shadows
        highResModel.traverse((node) => {
          if (node instanceof THREE.Mesh) {
            node.castShadow = true;
            node.receiveShadow = true;
          }
        });

        // Copy transformation from low-res
        highResModel.position.copy(modelEntry.object.position);
        highResModel.rotation.copy(modelEntry.object.rotation);
        highResModel.scale.copy(modelEntry.object.scale);

        // Remove low-res from scene
        this.scene.remove(modelEntry.object);
        this.disposeObject(modelEntry.object);

        // Add high-res to scene
        this.scene.add(highResModel);

        // Update entry
        modelEntry.object = highResModel;
        modelEntry.url = modelEntry.highResUrl;
        modelEntry.isHighRes = true;
        modelEntry.animations = gltf.animations;
        modelEntry.lodLevel = 1; // Now showing LOD 1
        modelEntry.upgradePending = false;
        modelEntry.isLoading = false;

        console.log('✓ Model upgraded to high-res');
      },
      undefined,
      (error) => {
        console.error('Error loading high-res LOD:', error);
        modelEntry.isLoading = false;
        // Keep low-res version if high-res fails
      }
    );
  }

  disposeObject(object) {
    // Dispose of geometries and materials
    object.traverse((node) => {
      if (node instanceof THREE.Mesh) {
        if (node.geometry) {
          node.geometry.dispose();
        }
        if (node.material) {
          if (Array.isArray(node.material)) {
            node.material.forEach(m => m.dispose());
          } else {
            node.material.dispose();
          }
        }
      }
    });
  }

  removeModel(modelEntry) {
    if (!modelEntry) return;

    // Cancel any pending LOD upgrades
    if (modelEntry.upgradeTimer) {
      clearTimeout(modelEntry.upgradeTimer);
      modelEntry.upgradeTimer = null;
    }
    modelEntry.upgradePending = false;

    // Dispose of the model
    this.disposeObject(modelEntry.object);
    this.scene.remove(modelEntry.object);

    const index = this.models.indexOf(modelEntry);
    if (index > -1) {
      this.models.splice(index, 1);
    }

    if (this.selectedModel === modelEntry) {
      this.selectedModel = null;
    }
  }

  setLightingPreset(presetName) {
    this.lightingPreset = presetName;
    this.setupLighting();
  }

  setGridSize(size) {
    this.gridSize = size;
  }

  toggleSnapToGrid() {
    this.snapEnabled = !this.snapEnabled;
    return this.snapEnabled;
  }

  setBackgroundColor(hexColor) {
    this.backgroundColor = hexColor;
    this.scene.background = new THREE.Color(this.backgroundColor);
    this.scene.fog.color.setHex(this.backgroundColor);
  }

  clearScene() {
    this.models.forEach(model => {
      this.scene.remove(model.object);
    });
    this.models = [];
    this.selectedModel = null;
  }

  getModelPositions() {
    return this.models.map(model => ({
      url: model.url,
      position: {
        x: model.object.position.x,
        y: model.object.position.y,
        z: model.object.position.z
      },
      rotation: {
        x: model.object.rotation.x,
        y: model.object.rotation.y,
        z: model.object.rotation.z
      }
    }));
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    if (this.renderer) {
      this.renderer.render(this.scene, this.camera);
    }
  }

  dispose() {
    // Cancel all pending LOD upgrades
    this.models.forEach(model => {
      if (model.upgradeTimer) {
        clearTimeout(model.upgradeTimer);
        model.upgradeTimer = null;
      }
      model.upgradePending = false;
      this.disposeObject(model.object);
    });

    // Clear models
    this.clearScene();

    if (this.renderer) {
      this.renderer.dispose();
      this.container.removeChild(this.renderer.domElement);
    }

    if (this.dracoLoader) {
      this.dracoLoader.dispose();
    }

    if (this.loadingManager) {
      this.loadingManager.dispose?.();
    }

    console.log('✓ FurniturePlacementScene disposed');
  }
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FurniturePlacementScene;
}
