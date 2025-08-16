import google.generativeai as genai
from core.config import settings
import logging
from fastapi import HTTPException
from google.api_core.exceptions import ResourceExhausted
from typing import List
import google.generativeai as genai
from rate_limiter import rate_limiter

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
    # Build the list of API keys to try - prioritize GEMINI_API_KEYS_LIST first
    api_keys = []
    
    # First add all keys from the comma-separated list (primary source)
    if settings.GEMINI_API_KEYS_LIST:
        api_keys.extend(settings.GEMINI_API_KEYS_LIST)
        logging.info(f"Added {len(settings.GEMINI_API_KEYS_LIST)} keys from GEMINI_API_KEYS_LIST")
    
    # Then add the single key as backup if it's not already in the list
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in api_keys:
        api_keys.append(settings.GEMINI_API_KEY)
        logging.info(f"Added single GEMINI_API_KEY as backup")
    
    if not api_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured.")

    logging.info(f"Starting Gemini generation with {len(api_keys)} available API keys")
    
    last_exception = None
    quota_exhausted_count = 0
    keys_attempted = 0

    for i, key in enumerate(api_keys):
        keys_attempted += 1
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        
        try:
            # Apply rate limiting per API key
            key_id = f"gemini_{key_prefix}"
            remaining = rate_limiter.get_remaining_requests(key_id, max_requests=50, window_seconds=60)
            
            if remaining <= 0:
                logging.warning(f"Rate limit reached for Gemini key #{i+1} ({key_prefix}...), skipping")
                continue
                
            # Wait if needed to avoid hitting rate limits
            rate_limiter.wait_if_needed(key_id, max_requests=50, window_seconds=60)
            
            logging.info(f"Attempting Gemini generation with key #{i+1} ({key_prefix}...) - {remaining} requests remaining")
            
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_NAME,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            logging.info(f"✅ Successfully generated text using key #{i+1} ({key_prefix}...) - {remaining-1} requests remaining")
            return response.text
            
        except ResourceExhausted as e:
            quota_exhausted_count += 1
            logging.warning(f"❌ Gemini quota exceeded for key #{i+1} ({key_prefix}...): {e}")
            last_exception = e
            continue
            
        except Exception as e:
            # Continue to next key to allow failover on invalid/errored keys
            logging.warning(f"❌ Gemini error with key #{i+1} ({key_prefix}...): {e}")
            last_exception = e
            continue

    # If we reach here, all keys failed
    logging.error(f"All {keys_attempted} Gemini API keys failed. Quota exhausted: {quota_exhausted_count}, Other errors: {keys_attempted - quota_exhausted_count}")
    
    if quota_exhausted_count == keys_attempted and quota_exhausted_count > 0:
        raise HTTPException(status_code=429, detail=f"All {keys_attempted} Gemini API keys have exceeded quota. Please try again later.")
    
    raise HTTPException(status_code=500, detail=f"Gemini text generation failed for all {keys_attempted} keys: {last_exception}")

def generate_text_with_image(prompt: str, image_path: str) -> str:
    """
    Generates text using the Gemini Pro Vision model with an image and API key failover.
    """
    import PIL.Image
    
    # Build the list of API keys to try - same logic as generate_text
    api_keys = []
    
    if settings.GEMINI_API_KEYS_LIST:
        api_keys.extend(settings.GEMINI_API_KEYS_LIST)
        logging.info(f"Added {len(settings.GEMINI_API_KEYS_LIST)} keys from GEMINI_API_KEYS_LIST for vision")
    
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in api_keys:
        api_keys.append(settings.GEMINI_API_KEY)
        logging.info(f"Added single GEMINI_API_KEY as backup for vision")
    
    if not api_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured for vision.")

    logging.info(f"Starting Gemini vision generation with {len(api_keys)} available API keys")
    
    last_exception = None
    quota_exhausted_count = 0
    keys_attempted = 0

    for i, key in enumerate(api_keys):
        keys_attempted += 1
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        
        try:
            # Apply rate limiting per API key
            key_id = f"gemini_vision_{key_prefix}"
            remaining = rate_limiter.get_remaining_requests(key_id, max_requests=50, window_seconds=60)
            
            if remaining <= 0:
                logging.warning(f"Rate limit reached for Gemini vision key #{i+1} ({key_prefix}...), skipping")
                continue
                
            # Wait if needed to avoid hitting rate limits
            rate_limiter.wait_if_needed(key_id, max_requests=50, window_seconds=60)
            
            logging.info(f"Attempting Gemini vision generation with key #{i+1} ({key_prefix}...) - {remaining} requests remaining")
            
            genai.configure(api_key=key)
            vision_model = genai.GenerativeModel('gemini-pro-vision')
            img = PIL.Image.open(image_path)
            response = vision_model.generate_content([prompt, img])
            logging.info(f"✅ Successfully generated vision text using key #{i+1} ({key_prefix}...) - {remaining-1} requests remaining")
            return response.text
            
        except ResourceExhausted as e:
            quota_exhausted_count += 1
            logging.warning(f"❌ Gemini vision quota exceeded for key #{i+1} ({key_prefix}...): {e}")
            last_exception = e
            continue
            
        except Exception as e:
            logging.warning(f"❌ Gemini vision error with key #{i+1} ({key_prefix}...): {e}")
            last_exception = e
            continue

    # If we reach here, all keys failed
    logging.error(f"All {keys_attempted} Gemini vision API keys failed. Quota exhausted: {quota_exhausted_count}, Other errors: {keys_attempted - quota_exhausted_count}")
    
    if quota_exhausted_count == keys_attempted and quota_exhausted_count > 0:
        raise HTTPException(status_code=429, detail=f"All {keys_attempted} Gemini vision API keys have exceeded quota. Please try again later.")
    
    raise HTTPException(status_code=500, detail=f"Gemini vision generation failed for all {keys_attempted} keys: {last_exception}")

def start_chat_session():
    """
    Starts a new chat session with the Gemini Pro model using API key failover.
    """
    # Build the list of API keys to try
    api_keys = []
    
    if settings.GEMINI_API_KEYS_LIST:
        api_keys.extend(settings.GEMINI_API_KEYS_LIST)
    
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in api_keys:
        api_keys.append(settings.GEMINI_API_KEY)
    
    if not api_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured for chat.")

    # Try each API key until one works
    for i, key in enumerate(api_keys):
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_NAME,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            chat_session = model.start_chat(history=[])
            logging.info(f"✅ Successfully started chat session using key #{i+1} ({key_prefix}...)")
            return chat_session
        except Exception as e:
            logging.warning(f"❌ Failed to start chat session with key #{i+1} ({key_prefix}...): {e}")
            continue
    
    raise HTTPException(status_code=500, detail=f"Failed to start chat session with all {len(api_keys)} API keys")

def send_chat_message(chat_session, message: str) -> str:
    """
    Sends a message to the chat session and returns the response.
    Note: This uses the same API key that was used to create the chat session.
    """
    try:
        response = chat_session.send_message(message)
        return response.text
    except ResourceExhausted as e:
        logging.warning(f"Gemini chat quota exceeded: {e}")
        raise HTTPException(status_code=429, detail="Gemini API quota exceeded during chat. Please try again later.")
    except Exception as e:
        logging.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini chat message failed: {e}")
