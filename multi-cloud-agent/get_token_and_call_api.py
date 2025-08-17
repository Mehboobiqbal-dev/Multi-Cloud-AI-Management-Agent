import requests
import json

# User credentials
USER_EMAIL = "test@example.com"
USER_PASSWORD = "testpassword"
USER_NAME = "Test User"

# API endpoint URLs
BASE_URL = "https://multi-cloud-ai-management-agent.onrender.com/"
signup_url = f"{BASE_URL}/signup"
token_url = f"{BASE_URL}/token"
agent_run_url = f"{BASE_URL}/agent/run"

# --- Step 1: Sign up a new user ---
print("--- Step 1: Attempting to sign up user ---")
signup_data = {
    "email": USER_EMAIL,
    "password": USER_PASSWORD,
    "name": USER_NAME
}

try:
    signup_response = requests.post(signup_url, json=signup_data)
    # Raise an exception for bad status codes (4xx or 5xx)
    signup_response.raise_for_status()
    print(f"User '{USER_NAME}' signed up successfully.")
except requests.exceptions.HTTPError as e:
    # Check if the error is because the user already exists
    if e.response.status_code == 400 and "Email already registered" in e.response.text:
        print(f"User with email '{USER_EMAIL}' already exists. Proceeding to login.")
    else:
        # Handle other HTTP errors
        print(f"Error during signup: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        exit() # Exit the script if signup fails for an unexpected reason
except requests.exceptions.RequestException as e:
    # Handle network-related errors (e.g., connection refused)
    print(f"A connection error occurred during signup: {e}")
    exit()

# --- Step 2: Get access token by logging in ---
print("\n--- Step 2: Getting access token ---")
login_data = {
    "username": USER_EMAIL, # The /token endpoint expects 'username', not 'email'
    "password": USER_PASSWORD
}

access_token = None
try:
    # The token endpoint typically expects form data, not JSON
    token_response = requests.post(token_url, data=login_data)
    token_response.raise_for_status()
    token_info = token_response.json()
    access_token = token_info.get("access_token")
    if access_token:
        print("Successfully obtained access token.")
    else:
        print("Error: 'access_token' not found in the response.")
        exit()
except requests.exceptions.RequestException as e:
    print(f"Error obtaining token: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response content: {e.response.text}")
    exit()

# --- Step 3: Call the protected /agent/run endpoint ---
print("\n--- Step 3: Calling the /agent/run endpoint ---")
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
agent_run_data = {
    "user_input": "Hello, this is a test to trigger LLM.",
    "run_id": "test_run_123"
}

try:
    print(f"Calling /agent/run with payload: {json.dumps(agent_run_data)}")
    agent_run_response = requests.post(agent_run_url, headers=headers, json=agent_run_data)
    
    print(f"Status code: {agent_run_response.status_code}")
    print(f"Response headers: {agent_run_response.headers}")
    
    # Check if the response is JSON before trying to print it prettily
    try:
        # Try to parse and print formatted JSON
        response_json = agent_run_response.json()
        print("Response JSON:")
        print(json.dumps(response_json, indent=4))
    except json.JSONDecodeError:
        # If it's not JSON, print as plain text
        print(f"Response text: {agent_run_response.text}")

    agent_run_response.raise_for_status()

    # Save the raw response text to a file
    try:
        with open("agent_run_response.txt", "w", encoding="utf-8") as f:
            f.write(agent_run_response.text)
        print("\nSuccessfully called /agent/run endpoint. Full response saved to agent_run_response.txt")
    except IOError as e:
        print(f"\nFailed to write response to file: {e}")

except requests.exceptions.RequestException as e:
    print(f"\nError calling /agent/run: {e}")
    if hasattr(e, 'response') and e.response is not None:
        # This is the corrected and de-duplicated error handling block
        print(f"Response status code: {e.response.status_code}")
        print(f"Response headers: {e.response.headers}")
        print(f"Response content: {e.response.text}")