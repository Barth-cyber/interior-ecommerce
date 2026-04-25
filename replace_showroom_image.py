#!/usr/bin/env python3
"""Replace showroom image with model-viewer component."""

from pathlib import Path
import re

html_file = Path(r'c:\ecommerce\interior.html')
content = html_file.read_text(encoding='utf-8')

# Find and replace the image with model-viewer
# Match the img tag with the base64 data URI
pattern = r'<img[^>]*src="data:image/jpeg;base64,[^"]*"[^>]*alt="TV Media Wall"[^>]*>'

replacement = '''<model-viewer 
          id="showroomModelViewer" 
          src="https://modelviewer.dev/shared-assets/models/Astronaut.glb" 
          alt="Interactive furniture preview" 
          ar 
          ar-modes="webxr scene-viewer quick-look" 
          environment-image="https://modelviewer.dev/shared-assets/environments/neutral.hdr" 
          camera-controls 
          auto-rotate 
          shadow-intensity="1" 
          loading="lazy" 
          reveal="interaction" 
          style="width:100%;height:320px;max-height:320px;border-radius:8px;background:#fff;transform-origin:center center;">
        </model-viewer>'''

new_content, count = re.subn(pattern, replacement, content, count=1)

if count == 0:
    print('ERROR: Pattern not found!')
    exit(1)

html_file.write_text(new_content, encoding='utf-8')
print(f'✓ Successfully replaced showroom image with model-viewer ({count} replacement)')
