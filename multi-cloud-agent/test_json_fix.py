import requests
import json

try:
    response = requests.post('http://localhost:8000/agent/run', 
                           json={'user_id': 1, 'goal': 'test json parsing', 'context': 'simple test'}, 
                           timeout=30)
    print('Status:', response.status_code)
    print('Response:', response.text[:500])
except Exception as e:
    print('Error:', str(e))