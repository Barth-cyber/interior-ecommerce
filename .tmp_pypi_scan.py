import json, urllib.request
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet
from datetime import datetime

with open('requirements.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

requirements = []
for line in lines:
    if '==' in line:
        pkg, ver = line.split('==', 1)
        requirements.append((pkg.strip(), ver.strip()))

old = []
for pkg, current in requirements:
    try:
        with urllib.request.urlopen(f'https://pypi.org/pypi/{pkg}/json', timeout=30) as resp:
            data = json.load(resp)
    except Exception as e:
        print('ERROR', pkg, e)
        continue
    releases = data.get('releases', {})
    current_date = None
    if current in releases:
        files = [f for f in releases[current] if not f.get('yanked')]
        if files:
            dates = [datetime.fromisoformat(f['upload_time_iso_8601'].replace('Z','+00:00')) for f in files if f.get('upload_time_iso_8601')]
            if dates:
                current_date = max(dates)
    candidates = []
    for vstr, files in releases.items():
        try:
            v = Version(vstr)
        except InvalidVersion:
            continue
        if v.is_prerelease:
            continue
        valid = [f for f in files if not f.get('yanked')]
        if not valid:
            continue
        ok = False
        for f in valid:
            req = f.get('requires_python')
            if not req:
                ok = True
                break
            try:
                if Version('3.11.0') in SpecifierSet(req):
                    ok = True
                    break
            except Exception:
                ok = True
                break
        if not ok:
            continue
        dates = [datetime.fromisoformat(f['upload_time_iso_8601'].replace('Z','+00:00')) for f in valid if f.get('upload_time_iso_8601')]
        released = max(dates) if dates else None
        candidates.append((v, vstr, released))
    latest = sorted(candidates, key=lambda x: x[0])[-1] if candidates else None
    latest_ver = latest[1] if latest else None
    latest_date = latest[2] if latest else None
    if current_date and current_date.year < 2024:
        print(pkg, current, current_date.date(), latest_ver, latest_date.date() if latest_date else None)
