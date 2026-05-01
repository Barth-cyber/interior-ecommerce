import requests

url = "http://127.0.0.1:5000/ai-query"
data = {
    "query": "What is your best sofa?",
    "session_id": "test-session"
}
response = requests.post(url, json=data)
print(response.json())
