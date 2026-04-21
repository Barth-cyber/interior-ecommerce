import re
from pathlib import Path

FILES = [Path('interior.html'), Path('hero-popup-slider.js')]

# Match quoted paths ending with an image extension
img_regex = re.compile(r"([\"'])(IDL(?:%20|_|\s)Product(?:%20|_|\s)branding/[^\"']+?\.(?:jpe?g|png|gif))(\1)", re.IGNORECASE)

# Normalize a path to canonical form

def canonicalize(path: str) -> str:
    # Decode %20 to space, and any % encoded sequences (basic)
    path = path.replace('%20', ' ')
    # Ensure folder name uses underscores
    path = re.sub(r'IDL[ _]Product[ _]branding', 'IDL_Product_branding', path, flags=re.IGNORECASE)
    # Replace spaces with underscores
    path = path.replace(' ', '_')
    # Replace any remaining invalid chars except / . _ -
    path = re.sub(r"[^A-Za-z0-9._\-/]", '_', path)
    # Collapse multiple underscores
    path = re.sub(r'_+', '_', path)
    return path

# Collect all referenced paths
refs = set()
for f in FILES:
    txt = f.read_text(encoding='utf-8')
    for m in img_regex.finditer(txt):
        refs.add(m.group(2))

print('Found', len(refs), 'image references:')
for r in sorted(refs):
    print(' ', r)

# Determine renames
renames = {}
for r in refs:
    canon = canonicalize(r)
    if canon != r:
        renames[r] = canon

if not renames:
    print('No renames needed.')
else:
    print('\nRenames to apply:')
    for old, new in renames.items():
        print(old, '->', new)

# Apply file renames (if present)
for old, new in renames.items():
    # Determine existing file on disk (try both old and its decoded form)
    possible = []
    # use folder name in old, which might include %20 or spaces
    old_fs = old.replace('%20', ' ')
    possible.append(Path(old_fs))
    possible.append(Path(old))
    # also try canonical folder name with spaces
    if 'IDL_Product_branding' not in old_fs:
        possible.append(Path(old_fs.replace('IDL Product branding', 'IDL_Product_branding')))
        possible.append(Path(old_fs.replace('IDL Product branding', 'IDL_Product_branding').replace(' ', '_')))
    # Try to find existing file
    found = None
    for p in possible:
        if p.exists():
            found = p
            break
    if not found:
        print('WARNING: could not locate file for', old, 'tried', possible)
        continue
    newp = Path(canonicalize(str(found)))
    if found.resolve() == newp.resolve():
        continue
    newp.parent.mkdir(parents=True, exist_ok=True)
    print('Renaming file:', found, '->', newp)
    found.rename(newp)

# Update references in source files
for f in FILES:
    txt = f.read_text(encoding='utf-8')
    changed = False
    for old, new in renames.items():
        if old in txt:
            txt = txt.replace(old, new)
            changed = True
    if changed:
        f.write_text(txt, encoding='utf-8')
        print('Updated references in', f)
