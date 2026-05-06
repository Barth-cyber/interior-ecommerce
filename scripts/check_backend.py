#!/usr/bin/env python3
"""
Simple backend health check script.
Usage: python scripts/check_backend.py [base_url]
If no base_url is provided, uses https://api.interiorductltd.com
"""
import sys
import urllib.request
import urllib.error

def probe(base):
    base = base.rstrip('/')
    endpoints = ['/api/health', '/']
    for ep in endpoints:
        url = base + ep
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'eid-check/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.getcode()
                body = resp.read(800).decode('utf-8', errors='replace')
                print(f'OK {url} -> {code}')
                if body:
                    print('BODY PREVIEW:')
                    print(body[:1000])
        except urllib.error.HTTPError as he:
            print(f'HTTP ERROR {url} -> {he.code} {he.reason}')
            try:
                print(he.read(800).decode('utf-8', errors='replace'))
            except Exception:
                pass
        except Exception as e:
            print(f'FAIL {url} -> {e}')

if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else 'https://api.interiorductltd.com'
    print('Probing backend:', base)
    probe(base)
