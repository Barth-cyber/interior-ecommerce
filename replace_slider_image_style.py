from pathlib import Path

path = Path('hero-popup-slider.js')
text = path.read_text(encoding='utf-8')
old = 'width:220px;height:220px;object-fit:cover;'
new = 'max-width:220px;width:100%;height:auto;object-fit:cover;'
if old in text:
    text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')
    print('Replaced all occurrences of fixed size with responsive sizing.')
else:
    print('No occurrences found to replace.')
