import urllib.request

urls = [
    'http://localhost:8000/IDL_Product_branding/Door.jpg',
    'http://localhost:8000/IDL_Product_branding/Door_Vent_mahony.jpg',
    'http://localhost:8000/IDL_Product_branding/door_milk_color.jpg',
]
for url in urls:
    try:
        r = urllib.request.urlopen(url, timeout=5)
        data = r.read()
        print(url, '->', r.status, 'bytes', len(data))
    except Exception as e:
        print(url, '-> ERROR', e)
