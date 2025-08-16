#!/usr/bin/env python3
"""
Groq API Key Setup Helper

This script helps you get and configure a free Groq API key.
"""

import os
import webbrowser
import time
from dotenv import load_dotenv, set_key

def main():
    print("🚀 Groq API Key Setup Helper")
    print("=" * 40)
    
    # Check current status
    load_dotenv()
    current_key = os.getenv('LLM_API_KEY', '')
    
    if current_key and current_key != 'gsk_your_groq_api_key_here':
        print(f"✅ You already have a Groq key configured: {current_key[:10]}...")
        print("\n🔍 Testing current key...")
        
        # Test the key
        import requests
        try:
            headers = {
                "Authorization": f"Bearer {current_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Your Groq key is working perfectly!")
                print("🎉 Your agent should work now.")
                return
            else:
                print(f"❌ Key test failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ Key test failed: {e}")
    
    print("\n📋 Steps to get a free Groq API key:")
    print("1. 🌐 Opening Groq Console in your browser...")
    
    # Open Groq console
    webbrowser.open('https://console.groq.com/')
    
    print("2. 📝 Sign up with your email (it's completely free!)")
    print("3. 🔑 Go to 'API Keys' section")
    print("4. ➕ Click 'Create API Key'")
    print("5. 📋 Copy the key (starts with 'gsk_')")
    
    print("\n⏳ Waiting for you to get the key...")
    print("(Press Enter when you have copied your Groq API key)")
    input()
    
    # Get the key from user
    while True:
        api_key = input("\n🔑 Paste your Groq API key here: ").strip()
        
        if not api_key:
            print("❌ Please enter a valid API key")
            continue
            
        if not api_key.startswith('gsk_'):
            print("⚠️  Warning: Groq keys usually start with 'gsk_'")
            confirm = input("Continue anyway? (y/n): ").lower()
            if confirm != 'y':
                continue
        
        # Test the key
        print("\n🧪 Testing your API key...")
        
        import requests
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ API key is working!")
                
                # Update .env file
                print("\n💾 Updating .env file...")
                set_key('.env', 'LLM_API_KEY', api_key)
                
                print("✅ .env file updated successfully!")
                print("\n🎉 Setup complete! Your agent should work now.")
                print("\n🚀 Next steps:")
                print("   1. Restart your backend server")
                print("   2. Try sending a message to your agent")
                print("   3. Enjoy fast AI responses with Groq!")
                
                break
                
            elif response.status_code == 401:
                print("❌ Invalid API key. Please check and try again.")
            elif response.status_code == 429:
                print("⚠️  API key is valid but quota exceeded. Try again later.")
                break
            else:
                print(f"❌ API test failed with status {response.status_code}")
                print("Please check your key and try again.")
                
        except Exception as e:
            print(f"❌ Error testing API key: {e}")
            print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main()