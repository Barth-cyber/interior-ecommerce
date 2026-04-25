#!/usr/bin/env python3
"""
Download GLB files into the local IDL_Product_branding folder.
Run: python scripts/download_glbs.py
"""
import os
import sys
from urllib.request import urlopen

TARGET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'IDL_Product_branding')

DEMOS = {
    'Avocado.glb': 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Avocado/glTF-Binary/Avocado.glb',
    'BoomBox.glb': 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/BoomBox/glTF-Binary/BoomBox.glb'
}

os.makedirs(TARGET_DIR, exist_ok=True)

def download(url, path):
    print(f"Downloading {url} -> {path}")
    try:
        with urlopen(url) as r, open(path, 'wb') as out:
            out.write(r.read())
        print('Saved', path)
    except Exception as e:
        print('Failed to download', url, e)


def main():
    for name, url in DEMOS.items():
        dest = os.path.join(TARGET_DIR, name)
        if os.path.exists(dest) and os.path.getsize(dest) > 1024:
            print(name, 'already exists, skipping')
            continue
        download(url, dest)

if __name__ == '__main__':
    main()
