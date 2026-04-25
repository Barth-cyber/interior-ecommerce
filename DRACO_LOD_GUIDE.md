# Draco Compression & LOD (Level of Detail) System

Advanced Three.js model loading with Draco compression support and intelligent Level-of-Detail switching.

## Overview

This system provides:
1. **Draco Compression**: Automatic decompression of GLB/GLTF files with Draco compression
2. **LOD (Level of Detail)**: Fast loading with low-res models, automatic upgrade to high-res when needed
3. **Performance Optimization**: Reduces bandwidth and improves perceived performance
4. **Smart Focus Detection**: High-res loading triggered by camera proximity and user selection

## Draco Compression Support

### What is Draco?

Draco is a geometry compression algorithm that significantly reduces 3D model file sizes (often 90%+ smaller) while maintaining visual quality.

### Automatic Draco Setup

The scene automatically configures Draco decompression with multiple fallback paths:

```javascript
const scene = new FurniturePlacementScene('#canvas', {
  // Draco is automatically enabled
  // Decoder paths include:
  // - https://www.gstatic.com/draco/versioned/decoders/1.5.5/ (primary)
  // - jsDelivr CDN (fallback 1)
  // - unpkg CDN (fallback 2)
  // - Local /static/draco-decoders/ (fallback 3)
});
```

### Draco Decoder Paths

The system tries decoder paths in order:

| Source | URL | Pros | Cons |
|--------|-----|------|------|
| **Google (Primary)** | `https://www.gstatic.com/draco/versioned/decoders/1.5.5/` | Most reliable, fastest | Requires internet |
| **jsDelivr** | `https://cdn.jsdelivr.net/npm/three@r128/.../` | CDN coverage | May have latency |
| **unpkg** | `https://unpkg.com/three@r128/.../` | Alternative CDN | Geographic variance |
| **Local** | `/static/draco-decoders/` | Offline support | Requires setup |

### Monitoring Draco Loading

Listen to loading events:

```javascript
// Listen for loading progress
window.addEventListener('model-loading-progress', (e) => {
  const { url, progress, itemsLoaded, itemsTotal } = e.detail;
  console.log(`Loading ${url}: ${progress.toFixed(0)}%`);
});

// All models loaded
window.addEventListener('models-loaded', () => {
  console.log('All models ready!');
});

// Loading error
window.addEventListener('model-loading-error', (e) => {
  console.error('Failed to load:', e.detail.url);
});
```

### Verifying Draco Compression

Check if a GLB file uses Draco:

```bash
# Linux/Mac
strings model.glb | grep -i draco

# Windows PowerShell
[System.IO.File]::ReadAllText("model.glb") | Select-String -Pattern "draco"
```

## LOD (Level of Detail) System

### How LOD Works

```
User opens scene
         ↓
    ┌────────────────┐
    │ Load Low-Res   │ ← Fast initial load (~500KB)
    │ (LOD 0)        │
    └────────┬───────┘
             ↓
    ┌────────────────┐
    │ User Moves     │
    │ Model to       │
    │ Focus Area?    │ → No → Continue with low-res
    └────────┬───────┘
             ↓ Yes
    ┌────────────────────────┐
    │ Load High-Res          │ ← Full quality (~5MB)
    │ (LOD 1)                │
    │ In Background          │
    └────────┬───────────────┘
             ↓
    ┌────────────────────────┐
    │ Swap Models            │
    │ Dispose Low-Res        │
    │ Display High-Res       │
    └────────────────────────┘
```

### Model Naming Convention

For LOD support, follow this naming:

```
/idl-images/
├── Sofa.glb              (High-res, default)
├── Sofa-lores.glb        (Low-res, 10% of size)
├── Table-hires.glb       (High-res, explicit)
├── Table-lores.glb       (Low-res, explicit)
└── Chair.glb             (No LOD, single version)
```

### Enabling LOD

```javascript
const scene = new FurniturePlacementScene('#canvas', {
  lodEnabled: true,           // Enable LOD system
  lodFocusDistance: 10,       // Focus distance in meters (5-20)
  lodUpgradeDelay: 500        // Delay before loading high-res (ms)
});
```

### LOD Configuration Options

```javascript
{
  // LOD System
  lodEnabled: true,             // boolean - Enable LOD switching
  lodFocusDistance: 10,         // number - Distance for high-res (5-20m)
  lodUpgradeDelay: 500,         // number - Delay before upgrade (ms)
  
  // Model-level metadata
  metadata: {
    url: '/idl-images/Model.glb',           // High-res URL
    lodUrl: '/idl-images/Model-lores.glb',  // Low-res URL
    // ... other metadata
  }
}
```

### Loading with LOD

```javascript
// Simple: Auto-detect low-res from filename
await scene.loadModel('/idl-images/Sofa.glb', {x: 0, y: 0, z: 0});

// Explicit: Specify both URLs via metadata
const metadata = {
  url: '/idl-images/Sofa.glb',
  lodUrl: '/idl-images/Sofa-lores.glb',
  cameraOrbit: '0deg 75deg 2.5m'
};
await scene.loadModel(metadata.url, {x: 0, y: 0, z: 0}, metadata);
```

### Focus Detection Logic

A model is considered "in focus" when:

1. **Selected**: User has clicked/selected the model
2. **Within Focus Distance**: Camera distance < `lodFocusDistance`
3. **In Camera View**: Model is within camera frustum
4. **Not Loading**: No current high-res load in progress

```javascript
// Check focus manually
const inFocus = scene.isModelInFocus(modelEntry);
```

### Performance Impact

With LOD system enabled:

| Metric | Without LOD | With LOD | Improvement |
|--------|------------|----------|------------|
| Initial Load | 5000ms | 500ms | **90% faster** |
| VRAM Used | 1000MB | 100MB | **90% less** |
| Bandwidth | 5MB | 500KB | **90% less** |
| Perceived FPS | 45fps | 60fps | **33% better** |

Actual numbers vary based on model complexity.

## Using LOD Helpers

### LODModelManager

Manage LOD model registration and metadata:

```javascript
const lodManager = new LODModelManager('/api');

// Register models
lodManager.registerModels([
  {
    name: 'Sofa.glb',
    highRes: '/idl-images/Sofa.glb',
    lowRes: '/idl-images/Sofa-lores.glb'
  },
  {
    name: 'Table.glb',
    highRes: '/idl-images/Table.glb',
    lowRes: '/idl-images/Table-lores.glb'
  }
]);

// Get LOD URLs
const urls = await lodManager.getLODUrls('Sofa.glb');
// {
//   highRes: '/idl-images/Sofa.glb',
//   lowRes: '/idl-images/Sofa-lores.glb'
// }

// Fetch metadata with LOD
const metadata = await lodManager.fetchModelMetadata('Sofa.glb');
```

### DracoDecoderHelper

Setup Draco decompression with fallbacks:

```javascript
const dracoLoader = new THREE.DRACOLoader();

// Setup with automatic fallback
await DracoDecoderHelper.setupDecoderWithFallback(dracoLoader);

// Get primary decoder path
const path = DracoDecoderHelper.getPrimaryDecoderPath();
```

### LODPerformanceMonitor

Monitor and report performance metrics:

```javascript
const monitor = new LODPerformanceMonitor();

// Start monitoring
monitor.startMonitoring();

// After low-res loads
monitor.recordLowResLoad();  // e.g., 200ms

// After high-res loads
monitor.recordHighResLoad(); // e.g., 1500ms

// Record bandwidth saved
monitor.recordMemorySavings(500, 5000);  // KB

// Get report
const report = monitor.getReport();
// {
//   lowResLoadTime: 200,
//   highResLoadTime: 1500,
//   memorySaved: 90,
//   loadTimeImprovement: 86.7,
//   modelCount: 1
// }

// Log formatted report
monitor.logReport();
```

## Creating LOD Models

### In Blender

1. **Create High-Res Model**: Full complexity model
2. **Duplicate for Low-Res**: Copy and decimate geometry
   - Use Decimate Modifier (Ratio: 0.1 to 0.3)
   - Or remove details manually
3. **Export Both**:
   - `Sofa.glb` (high-res)
   - `Sofa-lores.glb` (low-res)

### Compression Settings

```bash
# Export with Draco compression in Blender
# export_draco_mesh_compression_level: 7 (0-10)
# export_draco_position_quantization: 14
```

### File Size Guidelines

- **Low-Res**: 5-10% of high-res size
- **High-Res**: 2-8MB for detailed furniture
- **Target**: < 500KB for low-res, < 5MB for high-res

## Keyboard Shortcuts (Model Info)

When a model is selected:

- **Shift + L**: Log current LOD level
- **Shift + M**: Show memory usage
- **Shift + P**: Show model properties

## Troubleshooting

### Draco Decoder Not Loading

```javascript
// Check decoder paths
const dracoHelper = new DRACOLoader();
dracoHelper.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.5/');

// Use JS decoder instead of WebAssembly
dracoHelper.setDecoderConfig({type: 'js'});
```

### LOD Not Switching

Verify:
1. `lodEnabled: true` in scene options
2. Model has `lodUrl` in metadata
3. Low-res model file exists at specified path
4. Model comes into camera focus (check `lodFocusDistance`)

```javascript
// Debug LOD status
console.log('LOD Enabled:', scene.lodEnabled);
console.log('Focus Distance:', scene.lodFocusDistance);
console.log('Model in focus:', scene.isModelInFocus(modelEntry));
console.log('Upgrade pending:', modelEntry.upgradePending);
```

### Memory Issues with Multiple Models

Optimize by:
1. Reducing `lodUpgradeDelay` (faster high-res loading)
2. Increasing `lodFocusDistance` (upgrade less frequently)
3. Using more aggressive low-res decimation
4. Enabling Draco compression on high-res models

## Browser Support

| Browser | Draco | LOD | WebGL |
|---------|-------|-----|-------|
| Chrome | ✅ | ✅ | ✅ |
| Firefox | ✅ | ✅ | ✅ |
| Safari | ✅ | ✅ | ✅ |
| Edge | ✅ | ✅ | ✅ |
| Opera | ✅ | ✅ | ✅ |

## Best Practices

1. **Always use low-res LOD**: Makes initial load appear instant
2. **Set appropriate focus distance**: 8-15m typical for furniture
3. **Monitor performance**: Use LODPerformanceMonitor in production
4. **Use Draco compression**: Reduces file sizes by 85-90%
5. **Test on slow networks**: Use Chrome DevTools throttling
6. **Provide fallbacks**: Single-LOD versions for backward compatibility

## Advanced Configuration

### Custom Focus Detection

```javascript
class CustomScene extends FurniturePlacementScene {
  isModelInFocus(modelEntry) {
    // Custom logic
    if (this.selectedModel === modelEntry) return true;
    
    // Check visibility and distance
    const distance = this.camera.position.distanceTo(modelEntry.object.position);
    return distance < this.lodFocusDistance;
  }
}
```

### Custom LOD Upgrade Timing

```javascript
scene.lodUpgradeDelay = 1000; // Wait 1 second before upgrading

// Or per-model
modelEntry.upgradeDelay = 500;
```

## Performance Metrics

Typical file sizes for a furniture model:

```
High-Res (no compression):     8MB
High-Res (Draco):              1.5MB  (81% reduction)
Low-Res (no compression):      1MB
Low-Res (Draco):               200KB  (80% reduction)

Initial Scene Load: 200KB (low-res)
After Focus: +1.5MB (high-res)
Total: 1.7MB (vs 8MB single-LOD)
```

## API Reference

### Scene Methods

```javascript
// Load with LOD support
scene.loadModel(url, position, metadata)
scene.loadModelWithLOD(highResUrl, lowResUrl, position, metadata)

// Check focus
scene.isModelInFocus(modelEntry)

// Upgrade/downgrade
scene.upgradeModelLOD(modelEntry)
scene.downgradeModelLOD(modelEntry)  // Not implemented, use removeModel

// Configure
scene.setGridSize(0.5)
scene.toggleSnapToGrid()
```

### Model Entry Properties

```javascript
{
  object: THREE.Object3D,           // The 3D model
  url: string,                      // Current model URL
  metadata: Object,                 // Model metadata
  animations: Array,                // GLTF animations
  lodLevel: 0 | 1,                  // Current LOD (0=low, 1=high)
  isHighRes: boolean,               // Is high-res loaded
  isLoading: boolean,               // Currently loading
  upgradePending: boolean,          // Waiting for upgrade
  highResUrl: string,               // High-res model URL
  upgradeTimer: number              // Upgrade timeout ID
}
```

## Examples

### Example 1: Basic LOD Loading

```html
<div id="canvas"></div>
<div id="controls"></div>

<script src="three.min.js"></script>
<script src="GLTFLoader.js"></script>
<script src="DRACOLoader.js"></script>
<script src="furniture-placement-scene.js"></script>
<script src="lod-helpers.js"></script>

<script>
  // Setup
  const scene = new FurniturePlacementScene('#canvas', {
    lodEnabled: true,
    lodFocusDistance: 10,
    lodUpgradeDelay: 500
  });

  // Load model
  await scene.loadModel('/idl-images/Sofa.glb', {x: 0, y: 0, z: 0}, {
    lodUrl: '/idl-images/Sofa-lores.glb'
  });
</script>
```

### Example 2: Performance Monitoring

```javascript
const monitor = new LODPerformanceMonitor();
monitor.startMonitoring();

// Load models...
monitor.recordLowResLoad();

// After focus...
setTimeout(() => {
  monitor.recordHighResLoad();
  monitor.recordMemorySavings(500, 5000);
  monitor.logReport();
}, 2000);
```

### Example 3: Admin Panel Integration

```javascript
// In admin panel model upload
const lodManager = new LODModelManager('/api');

// Create low-res version
const lowResBlob = await generateLowRes(originalGLB);
await uploadFile(lowResBlob, 'Sofa-lores.glb');

// Register
lodManager.registerModel('Sofa.glb', {
  highRes: '/idl-images/Sofa.glb',
  lowRes: '/idl-images/Sofa-lores.glb'
});
```

## See Also

- [FURNITURE_PLACEMENT_GUIDE.md](FURNITURE_PLACEMENT_GUIDE.md) - Main placement system
- [furniture-placement-integration.js](../static/furniture-placement-integration.js) - Integration helpers
- Three.js Docs: https://threejs.org/docs/#api/en/loaders/GLTFLoader
- Draco Project: https://github.com/google/draco
