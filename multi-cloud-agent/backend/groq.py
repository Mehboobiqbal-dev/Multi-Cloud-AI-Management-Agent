import os
import requests
import logging
from fastapi import HTTPException
from config import settings

# Fetch the API key and model name from settings or environment variables
API_KEY = settings.LLM_API_KEY or os.getenv("LLM_API_KEY")
DEFAULT_MODEL = settings.LLM_MODEL_NAME or os.getenv("LLM_MODEL_NAME") or "llama3-70b-8192"

if not API_KEY:
    raise RuntimeError("LLM_API_KEY is not set in .env or settings")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_text(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 429:
            raise HTTPException(status_code=429, detail="LLM quota exceeded. Please wait and try again later.")
        if resp.status_code != 200:
            logging.error("Groq API error %s: %s", resp.status_code, resp.text)
            raise HTTPException(status_code=500, detail="LLM request failed.")

        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as exc:
        logging.error("Exception while calling Groq API: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="LLM request exception.")
