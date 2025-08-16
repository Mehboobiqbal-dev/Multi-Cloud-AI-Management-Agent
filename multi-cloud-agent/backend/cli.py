import requests
import json

API_URL = "http://localhost:8000"

def main():
    print("Elch - AI Agent CLI")
    print("Enter 'exit' to quit.")

    # For simplicity, using a fixed dummy token. In a real scenario, you'd implement a login flow.
    token = "dummy-token"
    headers = {"Authorization": f"Bearer {token}"}

    while True:
        prompt = input("> ")
        if prompt.lower() == 'exit':
            break

        try:
            # Get plan
            response = requests.post(f"{API_URL}/prompt", headers=headers, json={"prompt": prompt})
            response.raise_for_status()
            plan = response.json().get("plan")
            print("Generated Plan:")
            print(json.dumps(plan, indent=2))

            # Execute plan
            execute = input("Execute this plan? (y/n): ")
            if execute.lower() == 'y':
                execute_response = requests.post(f"{API_URL}/execute_plan", headers=headers, json=plan)
                execute_response.raise_for_status()
                result = execute_response.json()
                print("Execution Result:")
                print(json.dumps(result, indent=2))

        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
