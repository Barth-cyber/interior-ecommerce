import requests

BASE_URL = 'http://localhost:5000'

def test_ai_query(query):
    resp = requests.post(f'{BASE_URL}/ai-query', json={'query': query})
    print(f'Query: {query}')
    print('Response:', resp.json())
    print('-' * 40)

def test_escalate(query, image_url=None):
    payload = {'query': query}
    if image_url:
        payload['imageUrl'] = image_url
    resp = requests.post(f'{BASE_URL}/escalate', json=payload)
    print(f'Escalate: {query} (image: {image_url})')
    print('Response:', resp.json())
    print('-' * 40)

if __name__ == '__main__':
    # Test known question
    test_ai_query('What materials do you use?')
    # Test unknown question (should escalate)
    test_ai_query('What is your return policy?')
    # Test escalation with image
    test_escalate('Tell me about this product', 'http://localhost:5000/idl-images/sample.jpg')
