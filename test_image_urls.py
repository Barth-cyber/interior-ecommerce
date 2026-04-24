import os
import urllib.request

BASE_URL = os.getenv('ECOMMERCE_TEST_BASE_URL', 'http://localhost:5000')
urls = [
    f'{BASE_URL}/IDL_Product_branding/Door.jpg',
    f'{BASE_URL}/IDL_Product_branding/Door_Vent_mahony.jpg',
    f'{BASE_URL}/IDL_Product_branding/door_milk_color.jpg',
]
for url in urls:
    try:
        r = urllib.request.urlopen(url, timeout=5)
        data = r.read()
        print(url, '->', r.status, 'bytes', len(data))
    except Exception as e:
        print(url, '-> ERROR', e)
