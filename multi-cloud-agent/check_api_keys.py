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

# Groq support has been removed - using Gemini only
# This function is kept for backward compatibility but does nothing
def check_groq_key():
    """Groq support has been removed"""
    print("\n🔍 Groq API support has been removed")
    print("✅ Using Gemini APIs only for better reliability")
    return True

def main():
    print("🚀 API Key Status Checker")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found! Please create one based on .env.example")
        sys.exit(1)
    
    gemini_ok = check_gemini_keys()
    check_groq_key()  # Just for informational purposes
    
    print("\n" + "=" * 40)
    print("📋 Summary:")
    
    if gemini_ok:
        print("✅ Gemini keys are working!")
        print("🎉 Your agent should work properly.")
        print("💡 The system now uses Gemini APIs exclusively for better reliability.")
    else:
        print("❌ No working Gemini API keys found!")
        print("🔧 Please check your .env file and Gemini API key configuration.")
        print("\n💡 Quick fixes:")
        print("   1. Get Gemini keys: https://makersuite.google.com/app/apikey")
        print("   2. Add them to GEMINI_API_KEYS in your .env file")
        print("   3. Check setup_api_keys.md for detailed instructions")
        print("   4. Restart your backend server after updating keys")

if __name__ == "__main__":
    main()