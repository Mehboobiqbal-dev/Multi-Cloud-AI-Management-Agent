import google.generativeai as genai
import os

# --- Configuration ---
# It's recommended to use environment variables for the API key in a real application.
# For this test, we'll use a hardcoded key to ensure it's not a loading issue.
API_KEY = "AIzaSyDyk2EZjWXFL3YiRQyd6LdbXGQ72OcmCDg"

# --- Test Script ---
def test_gemini_api():
    """
    Tests the Gemini API connection and a simple text generation call.
    """
    print("--- Starting Gemini API Test ---")

    # 1. Configure the API key
    try:
        genai.configure(api_key=API_KEY)
        print("✅ API key configured successfully.")
    except Exception as e:
        print(f"❌ Failed to configure API key: {e}")
        return

    # 2. Initialize the model
    try:
        model = genai.GenerativeModel('gemini-pro')
        print("✅ Generative model initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize model: {e}")
        return

    # 3. Generate content
    prompt = "Hello, Gemini! Please say 'Hello, World!'."
    print(f"\nSending prompt: '{prompt}'")
    try:
        response = model.generate_content(prompt)
        print(f"✅ API call successful.")
        print(f"Response Text: {response.text}")
    except Exception as e:
        print(f"❌ API call failed: {e}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_gemini_api()
