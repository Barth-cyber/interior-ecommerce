import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

with app.test_client() as c:
    res = c.get('/api/promotions')
    print('status:', res.status_code)
    print(res.get_data(as_text=True)[:2000])
