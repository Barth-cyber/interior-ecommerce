# Furniture Placement Scene - Three.js Integration

A complete, interactive furniture placement system built with Three.js featuring drag-and-drop placement, snap-to-grid functionality, and professional lighting presets.

## Features

### 🎯 Core Functionality
- **Drag-and-Drop Placement**: Click and drag furniture models to reposition them
- **Snap-to-Grid**: Automatically align models to customizable grid (0.25m - 2m)
- **Lighting Presets**: Three professional lighting configurations (Studio, Light, Dark)
- **GLB/GLTF Support**: Load 3D models with automatic Draco decompression
- **Shadow Rendering**: Realistic shadows with configurable intensity
- **Interactive Camera**: Zoom, pan, and rotate around the scene

### ⌨️ Keyboard Controls
- **Arrow Keys / WASD**: Move selected model
- **Q / E**: Rotate selected model
- **Delete**: Remove selected model
- **Mouse Wheel**: Zoom in/out
- **Mouse Drag**: Move model (with snap to grid)

### 📊 Scene Management
- Export layout as JSON for saving arrangements
- Clear scene with confirmation
- Real-time model count and info display
- Customizable background colors and grid sizes

## File Structure

```
/static/
├── furniture-placement-scene.js    # Main Three.js scene class
├── furniture-placement-ui.js       # UI controls and event handling
└── (index other assets)

/
└── furniture-placement-demo.html   # Demo page
```

## Usage

### 1. Basic Integration

Include in your HTML:

```html
<!-- Three.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<!-- THREE.js Addons -->
<script src="https://cdn.jsdelivr.net/npm/three@r128/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@r128/examples/js/loaders/DRACOLoader.js"></script>

<!-- Furniture Placement Scripts -->
<script src="/static/furniture-placement-scene.js"></script>
<script src="/static/furniture-placement-ui.js"></script>
```

### 2. HTML Markup

```html
<div id="canvas-container" style="width: 100%; height: 100vh;"></div>
<div id="controls-panel"></div>
```

### 3. JavaScript Initialization

```javascript
// Create scene
const scene = new FurniturePlacementScene('#canvas-container', {
  gridSize: 0.5,           // Grid cell size in meters
  snapEnabled: true,       // Enable snap-to-grid
  cameraDistance: 15,      // Initial camera distance
  lightingPreset: 'studio', // 'studio', 'light', or 'dark'
  backgroundColor: 0xf5f0e8 // Hex color
});

// Create UI controls
const ui = new FurniturePlacementUI(scene, '#controls-panel');

// Load a model
await scene.loadModel('/path/to/model.glb', {
  x: 0,
  y: 0,
  z: 0
});
```

## API Reference

### FurniturePlacementScene

#### Constructor Options

```javascript
{
  gridSize: 0.5,              // number - Grid cell size (0.25 - 2)
  snapEnabled: true,          // boolean - Enable snap-to-grid
  cameraDistance: 15,         // number - Initial camera distance (5-50)
  lightingPreset: 'studio',   // string - 'studio', 'light', or 'dark'
  backgroundColor: 0xf5f0e8   // number - Hex color code
}
```

#### Methods

```javascript
// Load a 3D model
scene.loadModel(url, position, metadata)
  .then(modelEntry => { /* loaded */ })
  .catch(error => { /* error */ })

// Remove a model
scene.removeModel(modelEntry)

// Change lighting
scene.setLightingPreset('studio' | 'light' | 'dark')

// Grid control
scene.setGridSize(size)           // 0.25 - 2.0
scene.toggleSnapToGrid()          // Returns new state

// Scene customization
scene.setBackgroundColor(0xHEXCODE)

// Export and utility
scene.getModelPositions()         // Returns array of model positions
scene.clearScene()                // Remove all models

// Cleanup
scene.dispose()                   // Release resources
```

#### Properties

```javascript
scene.models              // Array of loaded model objects
scene.selectedModel       // Currently selected model
scene.scene              // Three.js Scene instance
scene.camera             // Three.js Camera instance
scene.renderer           // Three.js Renderer instance
scene.gridSize           // Current grid size
scene.snapEnabled        // Grid snap state
scene.lightingPreset     // Current lighting preset name
```

### FurniturePlacementUI

#### Constructor

```javascript
new FurniturePlacementUI(sceneInstance, controlsSelector)
```

#### Methods

```javascript
// Show information message
ui.showInfo(message)

// Create controls UI
ui.createControls()

// Attach event listeners
ui.attachEventListeners()
```

## Lighting Presets

### Studio
- **Ambient**: 0.6 intensity, white
- **Directional**: 1.0 intensity, positioned at (10, 20, 10)
- **Point Lights**: 2 accent lights (warm and cool)
- **Best for**: Product visualization, professional rendering

### Light
- **Ambient**: 0.9 intensity, white
- **Directional**: 0.8 intensity, positioned at (5, 15, 5)
- **Point Lights**: None
- **Best for**: Bright, clean environments

### Dark
- **Ambient**: 0.4 intensity, dark
- **Directional**: 0.9 intensity, warm color at (15, 25, 15)
- **Point Lights**: 1 warm accent light
- **Best for**: Dramatic, mood-focused scenes

## Loading Models with Metadata

When loading models from the admin panel, metadata is automatically generated:

```json
{
  "filename": "Sofa.glb",
  "thumbnail": "/idl-images/Sofa_thumb.png",
  "url": "/idl-images/Sofa.glb",
  "cameraOrbit": "0deg 75deg 2.5m",
  "environmentImage": "https://modelviewer.dev/shared-assets/environments/neutral.hdr",
  "exposure": 1,
  "shadowIntensity": 1,
  "name": "Sofa",
  "uploadDate": "2026-04-25T...",
  "arModes": ["webxr", "scene-viewer", "quick-look"],
  "autoRotate": false,
  "reveal": "interaction"
}
```

Pass metadata when loading:

```javascript
const metadata = {
  cameraOrbit: "0deg 75deg 2.5m",
  exposure: 1,
  shadowIntensity: 1
};

await scene.loadModel(url, {x: 0, y: 0, z: 0}, metadata);
```

## Performance Optimization

### Draco Compression
Models are automatically decompressed using Draco for faster loading:

```javascript
const dracoLoader = new THREE.DRACOLoader();
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.5/');
```

### Shadow Optimization
- Directional light shadow map: 2048x2048
- PCF shadow filtering enabled
- Optimized shadow camera bounds

### Memory Management
```javascript
// Clean up when done
scene.dispose()

// Or remove individual models
scene.removeModel(modelEntry)
```

## Export/Import Layouts

### Export Layout

```javascript
const positions = scene.getModelPositions();
// Returns:
[
  {
    "url": "/idl-images/Sofa.glb",
    "position": { "x": 0, "y": 0, "z": 0 },
    "rotation": { "x": 0, "y": 0, "z": 0 }
  },
  // ... more models
]
```

### Import Layout

```javascript
const layout = [
  {
    url: "/idl-images/Sofa.glb",
    position: { x: 0, y: 0, z: 0 },
    rotation: { x: 0, y: 0.785, z: 0 }
  }
];

for (const item of layout) {
  await scene.loadModel(item.url, item.position);
  // Apply rotation if needed
}
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires WebGL support and ES6 JavaScript.

## Common Use Cases

### 1. Interior Design Tool
```javascript
const scene = new FurniturePlacementScene('#canvas', {
  lightingPreset: 'studio',
  gridSize: 0.25  // Finer grid for precision
});
```

### 2. Room Planner
```javascript
const scene = new FurniturePlacementScene('#canvas', {
  lightingPreset: 'light',
  cameraDistance: 20,
  backgroundColor: 0xffffff
});
```

### 3. AR Preview
```javascript
const scene = new FurniturePlacementScene('#canvas', {
  lightingPreset: 'light',
  snapEnabled: false  // Continuous positioning
});
```

## Troubleshooting

### Models not loading
1. Verify GLB file is valid and publicly accessible
2. Check console for CORS errors
3. Ensure Draco decoder path is correct

### Performance issues
1. Reduce shadow map resolution (scene.lights.directional.shadow.mapSize)
2. Limit number of loaded models
3. Use Draco-compressed models

### Camera not responding
1. Ensure container has valid dimensions
2. Check for JavaScript errors in console
3. Verify mouse events are not being prevented

## Integration with Admin Panel

Models uploaded via the admin panel automatically generate:
1. **Thumbnail PNG** (400x300)
2. **Metadata JSON** with camera settings
3. **GLTF/GLB file** (stored locally or on S3)

Access via:
- `GET /api/model-metadata/<filename>` - Retrieve metadata
- `PUT /api/model-metadata/<filename>` - Update camera settings

## Advanced Customization

### Custom Grid Colors
Modify the GridHelper in `setupGrid()`:
```javascript
const gridHelper = new THREE.GridHelper(
  20, 40,
  0x0099ff,  // Center line color
  0xeeeeee   // Grid color
);
```

### Custom Lighting
Override `setupLighting()` to add custom light configurations.

### Event Hooks
Extend the class to add custom event handling:
```javascript
class CustomFurnitureScene extends FurniturePlacementScene {
  onModelSelected(model) {
    console.log('Selected:', model);
  }
}
```

## License

Part of Interior Duct Ltd. — Functionality, Durability & Aesthetics

## Support

For issues, feature requests, or questions, please refer to the admin panel documentation or contact support.
