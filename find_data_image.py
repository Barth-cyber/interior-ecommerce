import pathlib
files=['interior.html', 'IDL_Product_branding\\email icon.html']
for fn in files:
    p = pathlib.Path(fn)
    if not p.exists():
        print('MISSING', fn)
        continue
    with p.open('r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if 'data:image' in line:
                idx = line.index('data:image')
                print('FILE', fn, 'LINE', i)
                print(line[max(0, idx-80):idx+120].replace('\n', ' '))
                print('---')
