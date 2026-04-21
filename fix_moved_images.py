from pathlib import Path

root = Path('.')
folder = Path('IDL_Product_branding')

for f in root.glob('IDL_Product_branding_*'):
    if f.is_file():
        # remove the leading prefix and underscore
        name = f.name[len('IDL_Product_branding_'):]
        target = folder / name
        if target.exists():
            print('Target already exists:', target, '- skipping', f)
            continue
        print('Moving', f, '->', target)
        f.rename(target)
