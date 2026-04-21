import re
from pathlib import Path

files = [Path('interior-duct.html'), Path('hero-popup-slider.js')]
pattern = re.compile(r"[\"']([^\"']*\.(?:jpg|jpeg|png|gif))[\"']", re.IGNORECASE)
seen = set()
for f in files:
    txt = f.read_text(encoding='utf-8')
    for m in pattern.finditer(txt):
        seen.add(m.group(1))

imgs = sorted(x for x in seen if 'IDL_Product_branding' in x)
print('Found', len(imgs), 'image references (in IDL_Product_branding):')
for i in imgs:
    print(' ', i)

renames = []
for img in imgs:
    if ' ' in img or '%20' in img or '|' in img:
        dirpart, fname = img.rsplit('/', 1)
        newfname = re.sub(r'[\s%]+', '_', fname)
        newfname = re.sub(r'[^A-Za-z0-9._-]', '_', newfname)
        newpath = f"{dirpart}/{newfname}"
        if newpath != img:
            renames.append((img, newpath))

print('\nRenames to apply:')
for old,new in renames:
    print(old, '->', new)

# Rename files in filesystem
for old, new in renames:
    oldp = Path(old)
    newp = Path(new)
    if oldp.exists():
        print('Renaming', oldp, '->', newp)
        newp.parent.mkdir(parents=True, exist_ok=True)
        oldp.rename(newp)
    else:
        print('WARNING: file not found', oldp)

# Update references
for f in files:
    txt = f.read_text(encoding='utf-8')
    changed = False
    for old,new in renames:
        if old in txt:
            txt = txt.replace(old, new)
            changed = True
    if changed:
        f.write_text(txt, encoding='utf-8')
        print('Updated references in', f)
