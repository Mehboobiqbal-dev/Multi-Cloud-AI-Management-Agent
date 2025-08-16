# API Keys Setup Guide

## The Issue
Your agent is showing "All LLM providers failed: 429: LLM quota exceeded" because all your Gemini API keys have hit their daily quota limits.

## Quick Fix: Add Groq API Key (Free & Fast)

### Step 1: Get a Free Groq API Key
1. Go to [https://console.groq.com/](https://console.groq.com/)
2. Sign up with your email (it's free)
3. Go to "API Keys" section
4. Click "Create API Key"
5. Copy the key (starts with `gsk_`)

### Step 2: Update Your .env File
1. Open the `.env` file in your project root
2. Replace this line:
   ```
   LLM_API_KEY=gsk_your_groq_api_key_here
   ```
   With your actual Groq API key:
   ```
   LLM_API_KEY=gsk_your_actual_key_here
   ```

### Step 3: Restart the Backend
1. Stop the backend server (Ctrl+C)
2. Start it again: `cd backend && python main.py`

## Alternative: Add More Gemini API Keys

If you prefer to use Gemini:
1. Go to [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Create additional API keys
3. Add them to the `GEMINI_API_KEYS` line in your `.env` file (comma-separated)

## Why This Happens
- Gemini free tier has daily quota limits
- When all keys hit the limit, the system tries Groq as backup
- Without a valid Groq key, everything fails

## Current Configuration
Your system is set up to:
1. Try all Gemini keys first (you have 7 configured)
2. Fall back to Groq when Gemini quota is exceeded
3. Provide helpful error messages when both fail

Groq is actually faster than Gemini for most tasks, so using it as primary might be better!