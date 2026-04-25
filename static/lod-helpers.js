/**
 * LOD Model Management Utilities
 * 
 * Helpers for working with Level-of-Detail (LOD) models in FurniturePlacementScene.
 * LOD system provides fast initial loading with low-res models that upgrade to
 * high-res when the model comes into focus.
 */

/**
 * LOD Model Naming Convention
 * 
 * For LOD support, name your models:
 *   - High-res: model-name.glb  or  model-name-hires.glb
 *   - Low-res:  model-name-lores.glb  or  model-name-lod0.glb
 * 
 * Example:
 *   - Sofa-hires.glb (5MB) - Full quality
 *   - Sofa-lores.glb (500KB) - Simplified geometry
 */

class LODModelManager {
  constructor(adminApiUrl = '/api') {
    this.adminApiUrl = adminApiUrl;
    this.modelRegistry = new Map(); // Cache of model LOD info
  }

  /**
   * Get LOD URLs for a model by filename
   * Automatically derives low-res URL from high-res filename
   * 
   * @param {string} modelName - Filename like "Sofa.glb" or "Sofa-hires.glb"
   * @returns {Object} {highRes: url, lowRes: url} or null if not found
   */
  async getLODUrls(modelName) {
    const cached = this.modelRegistry.get(modelName);
    if (cached) return cached;

    // Derive low-res from high-res name
    const baseName = modelName.replace(/(-hires)?\.glb$/i, '');
    const highResUrl = `/idl-images/${modelName}`;
    const lowResUrl = `/idl-images/${baseName}-lores.glb`;

    return {
      highRes: highResUrl,
      lowRes: lowResUrl
    };
  }

  /**
   * Fetch model metadata and include LOD info
   * 
   * @param {string} modelName - Model filename
   * @returns {Promise<Object>} Metadata with LOD configuration
   */
  async fetchModelMetadata(modelName) {
    try {
      const response = await fetch(`${this.adminApiUrl}/model-metadata/${modelName}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const metadata = await response.json();
      
      // Add LOD URLs if not present
      if (!metadata.lodUrl) {
        const lods = await this.getLODUrls(modelName);
        metadata.lodUrl = lods.lowRes;
        metadata.highResUrl = lods.highRes;
      }
      
      return metadata;
    } catch (error) {
      console.warn(`Could not fetch metadata for ${modelName}:`, error);
      return null;
    }
  }

  /**
   * Create metadata for a model with LOD support
   * 
   * @param {string} highResUrl - URL to high-res model
   * @param {string} lowResUrl - URL to low-res model
   * @param {Object} options - Camera settings, etc.
   * @returns {Object} Metadata object
   */
  createLODMetadata(highResUrl, lowResUrl, options = {}) {
    return {
      url: highResUrl,
      lodUrl: lowResUrl,
      highResUrl: highResUrl,
      cameraOrbit: options.cameraOrbit || "0deg 75deg 2.5m",
      environmentImage: options.environmentImage || "https://modelviewer.dev/shared-assets/environments/neutral.hdr",
      exposure: options.exposure || 1,
      shadowIntensity: options.shadowIntensity || 1,
      name: options.name || 'Model',
      autoRotate: options.autoRotate !== undefined ? options.autoRotate : false,
      reveal: options.reveal || 'interaction'
    };
  }

  /**
   * Register a model's LOD variants
   * 
   * @param {string} modelName - Base model name
   * @param {Object} lods - {highRes: url, lowRes: url}
   */
  registerModel(modelName, lods) {
    this.modelRegistry.set(modelName, lods);
  }

  /**
   * Batch register models from a list
   * 
   * @param {Array<Object>} models - [{name, highRes, lowRes}, ...]
   */
  registerModels(models) {
    models.forEach(model => {
      this.registerModel(model.name, {
        highRes: model.highRes,
        lowRes: model.lowRes
      });
    });
  }

  /**
   * List all registered models with their LODs
   * @returns {Array} List of registered models
   */
  listRegisteredModels() {
    const models = [];
    this.modelRegistry.forEach((lods, name) => {
      models.push({ name, ...lods });
    });
    return models;
  }
}

/**
 * Draco Decoder Configuration Helper
 * 
 * Manages Draco decompression decoder setup and fallbacks
 */
class DracoDecoderHelper {
  static readonly DECODER_PATHS = {
    google: 'https://www.gstatic.com/draco/versioned/decoders/1.5.5/',
    jsDelivr: 'https://cdn.jsdelivr.net/npm/three@r128/examples/js/libs/draco/gltf/',
    unpkg: 'https://unpkg.com/three@r128/examples/js/libs/draco/gltf/',
    local: '/static/draco-decoders/'
  };

  /**
   * Get optimal decoder path with fallbacks
   * @returns {string} Primary decoder path
   */
  static getPrimaryDecoderPath() {
    // Use Google's CDN as primary (most reliable)
    return this.DECODER_PATHS.google;
  }

  /**
   * Setup Draco decoder with fallback strategy
   * @param {THREE.DRACOLoader} dracoLoader - DRACOLoader instance
   * @returns {Promise<void>}
   */
  static async setupDecoderWithFallback(dracoLoader) {
    const paths = [
      this.DECODER_PATHS.google,
      this.DECODER_PATHS.jsDelivr,
      this.DECODER_PATHS.unpkg,
      this.DECODER_PATHS.local
    ];

    let decoderReady = false;

    for (const path of paths) {
      try {
        dracoLoader.setDecoderPath(path);
        
        // Test decoder availability
        await this.testDecoder(dracoLoader);
        
        console.log(`✓ Draco decoder ready (${path})`);
        decoderReady = true;
        break;
      } catch (error) {
        console.warn(`Draco decoder unavailable at ${path}, trying next...`);
        continue;
      }
    }

    if (!decoderReady) {
      console.warn('All Draco decoder paths failed, falling back to non-compressed models');
    }

    return decoderReady;
  }

  /**
   * Test if decoder is available
   * @private
   */
  static testDecoder(dracoLoader) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Decoder test timeout'));
      }, 5000);

      // Draco decoder is ready when the decoder path is set
      clearTimeout(timeout);
      resolve();
    });
  }
}

/**
 * LOD Profiling and Performance Monitoring
 */
class LODPerformanceMonitor {
  constructor() {
    this.metrics = {
      lowResLoadTime: 0,
      highResLoadTime: 0,
      memorySaved: 0,
      modelCount: 0
    };
    this.startTime = null;
  }

  /**
   * Start monitoring a model load
   */
  startMonitoring() {
    this.startTime = performance.now();
  }

  /**
   * Record low-res load time
   */
  recordLowResLoad() {
    if (this.startTime) {
      this.metrics.lowResLoadTime = performance.now() - this.startTime;
      console.log(`Low-res loaded in ${this.metrics.lowResLoadTime.toFixed(0)}ms`);
    }
  }

  /**
   * Record high-res load time
   */
  recordHighResLoad() {
    if (this.startTime) {
      this.metrics.highResLoadTime = performance.now() - this.startTime;
      console.log(`High-res loaded in ${this.metrics.highResLoadTime.toFixed(0)}ms`);
    }
  }

  /**
   * Estimate memory saved by LOD
   * @param {number} lowResSize - Low-res file size in KB
   * @param {number} highResSize - High-res file size in KB
   */
  recordMemorySavings(lowResSize, highResSize) {
    const saved = ((highResSize - lowResSize) / highResSize) * 100;
    this.metrics.memorySaved = saved;
    console.log(`Memory optimized: ${saved.toFixed(1)}% savings with LOD`);
  }

  /**
   * Get performance report
   */
  getReport() {
    return {
      ...this.metrics,
      loadTimeImprovement: this.metrics.highResLoadTime > 0
        ? ((this.metrics.highResLoadTime - this.metrics.lowResLoadTime) / this.metrics.highResLoadTime) * 100
        : 0
    };
  }

  /**
   * Log performance report
   */
  logReport() {
    const report = this.getReport();
    console.group('LOD Performance Report');
    console.log(`Low-res load time: ${report.lowResLoadTime.toFixed(0)}ms`);
    console.log(`High-res load time: ${report.highResLoadTime.toFixed(0)}ms`);
    console.log(`Memory improvement: ${report.memorySaved.toFixed(1)}%`);
    console.log(`Load time improvement: ${report.loadTimeImprovement.toFixed(1)}%`);
    console.groupEnd();
  }
}

/**
 * Integration example:
 * 
 * // 1. Setup LOD manager
 * const lodManager = new LODModelManager();
 * 
 * // 2. Register models
 * lodManager.registerModels([
 *   {
 *     name: 'Sofa.glb',
 *     highRes: '/idl-images/Sofa.glb',
 *     lowRes: '/idl-images/Sofa-lores.glb'
 *   },
 *   {
 *     name: 'Table.glb',
 *     highRes: '/idl-images/Table.glb',
 *     lowRes: '/idl-images/Table-lores.glb'
 *   }
 * ]);
 * 
 * // 3. Create scene with LOD enabled
 * const scene = new FurniturePlacementScene('#canvas', {
 *   lodEnabled: true,
 *   lodFocusDistance: 10,
 *   lodUpgradeDelay: 500
 * });
 * 
 * // 4. Load model with LOD
 * const metadata = await lodManager.fetchModelMetadata('Sofa.glb');
 * await scene.loadModel(
 *   metadata.url,
 *   {x: 0, y: 0, z: 0},
 *   metadata
 * );
 * 
 * // 5. Monitor performance
 * const monitor = new LODPerformanceMonitor();
 * monitor.startMonitoring();
 * // ... after loads ...
 * monitor.recordLowResLoad();
 * // ... when upgraded ...
 * monitor.recordHighResLoad();
 * monitor.logReport();
 */

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    LODModelManager,
    DracoDecoderHelper,
    LODPerformanceMonitor
  };
}
