import requests
import json

url = "http://localhost:8000/agent/run"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcl9pZCI6NSwiZXhwIjoxNzU0ODEwMzU3fQ.JZt1GpRHUEJqc3ws-kdgOMZdpkSMkvJviTEa6QEV1HM",
    "Content-Type": "application/json"
}
data = {
    "user_input": "Hello, this is a test to trigger LLM.",
    "run_id": "test_run_123"
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()  # Raise an exception for HTTP errors
    print(response.text)
except requests.exceptions.RequestException as e:
    print(f"Error making API call: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response content: {e.response.text}")