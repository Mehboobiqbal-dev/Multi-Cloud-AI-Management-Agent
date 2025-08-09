import google.generativeai as genai
from core.config import settings
import logging
from fastapi import HTTPException
from google.api_core.exceptions import ResourceExhausted
from typing import List
import google.generativeai as genai

# Generation Config
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

# Safety Settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# No global configuration; will configure per call in functions

def generate_text(prompt: str) -> str:
    """
    Generates text using the Gemini Pro model with API key failover.
    """
    # Prefer the parsed list of API keys from settings; fall back to single key if present
    api_keys = settings.GEMINI_API_KEYS_LIST if settings.GEMINI_API_KEYS_LIST else (
        [settings.GEMINI_API_KEY] if settings.GEMINI_API_KEY else []
    )
    if not api_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured.")

    last_exception = None
    quota_exhausted = False

    for key in api_keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_NAME,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            logging.info(f"Successfully generated text using key: {key[:10]}...")
            return response.text
        except ResourceExhausted as e:
            quota_exhausted = True
            logging.warning(f"Gemini quota exceeded for key {key[:10]}...: {e}")
            last_exception = e
            continue
        except Exception as e:
            # Continue to next key to allow failover on invalid/errored keys
            logging.warning(f"Gemini error with key {key[:10]}...: {e}")
            last_exception = e
            continue

    # If we reach here, all keys failed
    if quota_exhausted:
        raise HTTPException(status_code=429, detail="All Gemini API keys have exceeded quota. Please try again later.")
    raise HTTPException(status_code=500, detail=f"Gemini text generation failed for all keys: {last_exception}")

vision_model = genai.GenerativeModel('gemini-pro-vision')

def generate_text_with_image(prompt: str, image_path: str) -> str:
    """
    Generates text using the Gemini Pro Vision model with an image.
    """
    import PIL.Image

    try:
        img = PIL.Image.open(image_path)
        response = vision_model.generate_content([prompt, img])
        return response.text
    except ResourceExhausted as e:
        logging.warning(f"Gemini quota exceeded (vision): {e}")
        raise HTTPException(status_code=429, detail="Gemini API quota exceeded. Please wait and try again later.")
    except Exception as e:
        logging.error(f"Error generating text with image: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini image generation failed: {e}")

def start_chat_session():
    """
    Starts a new chat session with the Gemini Pro model.
    """
    return model.start_chat(history=[])

def send_chat_message(chat_session, message: str) -> str:
    """
    Sends a message to the chat session and returns the response.
    """
    try:
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        logging.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini chat message failed: {e}")
