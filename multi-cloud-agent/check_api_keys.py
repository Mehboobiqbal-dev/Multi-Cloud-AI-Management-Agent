#!/usr/bin/env python3
"""
API Key Status Checker

This script helps diagnose API key issues by testing each configured key.
"""

import os
import sys
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_gemini_keys():
    """Check all Gemini API keys"""
    print("\n🔍 Checking Gemini API Keys...")
    
    gemini_keys = os.getenv('GEMINI_API_KEYS', '').split(',')
    gemini_keys = [key.strip() for key in gemini_keys if key.strip()]
    
    if not gemini_keys:
        print("❌ No Gemini API keys found in GEMINI_API_KEYS")
        return False
    
    working_keys = 0
    for i, key in enumerate(gemini_keys, 1):
        try:
            genai.configure(api_key=key)
            model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash')
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello")
            print(f"✅ Key {i} ({key[:10]}...): Working")
            working_keys += 1
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                print(f"⚠️  Key {i} ({key[:10]}...): Quota exceeded")
            elif "invalid" in error_msg.lower() or "401" in error_msg:
                print(f"❌ Key {i} ({key[:10]}...): Invalid key")
            else:
                print(f"❌ Key {i} ({key[:10]}...): Error - {error_msg}")
    
    print(f"\n📊 Gemini Summary: {working_keys}/{len(gemini_keys)} keys working")
    return working_keys > 0

def check_groq_key():
    """Check Groq API key"""
    print("\n🔍 Checking Groq API Key...")
    
    groq_key = os.getenv('LLM_API_KEY')
    if not groq_key:
        print("❌ No Groq API key found in LLM_API_KEY")
        return False
    
    if not groq_key.startswith('gsk_'):
        print(f"⚠️  Warning: Groq key should start with 'gsk_', found: {groq_key[:10]}...")
    
    try:
        headers = {
            "Authorization": f"Bearer {groq_key}",
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
            print(f"✅ Groq key ({groq_key[:10]}...): Working")
            return True
        elif response.status_code == 429:
            print(f"⚠️  Groq key ({groq_key[:10]}...): Quota exceeded")
            return False
        elif response.status_code == 401:
            print(f"❌ Groq key ({groq_key[:10]}...): Invalid key")
            return False
        else:
            print(f"❌ Groq key ({groq_key[:10]}...): HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Groq key ({groq_key[:10]}...): Error - {e}")
        return False

def main():
    print("🚀 API Key Status Checker")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found! Please create one based on .env.example")
        sys.exit(1)
    
    gemini_ok = check_gemini_keys()
    groq_ok = check_groq_key()
    
    print("\n" + "=" * 40)
    print("📋 Summary:")
    
    if gemini_ok and groq_ok:
        print("✅ Both Gemini and Groq keys are working!")
        print("🎉 Your agent should work properly.")
    elif gemini_ok:
        print("✅ Gemini keys working, but Groq key has issues.")
        print("⚠️  Agent will work until Gemini quota is exhausted.")
    elif groq_ok:
        print("✅ Groq key working, but Gemini keys have issues.")
        print("💡 Consider using Groq as primary (it's faster anyway!).")
    else:
        print("❌ No working API keys found!")
        print("🔧 Please check your .env file and API key configuration.")
        print("\n💡 Quick fixes:")
        print("   1. Get a free Groq key: https://console.groq.com/")
        print("   2. Get Gemini keys: https://makersuite.google.com/app/apikey")
        print("   3. Check setup_api_keys.md for detailed instructions")

if __name__ == "__main__":
    main()