import google.generativeai as genai
from core.config import settings
import logging
from fastapi import HTTPException
# Import exceptions with compatibility across google-api-core versions
try:
    from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, TooManyRequests, NotFound, InvalidArgument  # type: ignore
    QUOTA_EXCEPTIONS = (ResourceExhausted, TooManyRequests)
except ImportError:  # Older versions may not have TooManyRequests
    from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, NotFound, InvalidArgument  # type: ignore
    QUOTA_EXCEPTIONS = (ResourceExhausted,)
from typing import List, Optional
from rate_limiter import rate_limiter
import itertools
import time
import random

# Preferred model candidates (first is configured). Will fallback if model not found/unsupported.
_MODEL_CANDIDATES = []
if settings.GEMINI_MODEL_NAME:
    _MODEL_CANDIDATES.append(settings.GEMINI_MODEL_NAME)
# Add safe fallbacks commonly available on v1beta
for m in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-pro"]:
    if m not in _MODEL_CANDIDATES:
        _MODEL_CANDIDATES.append(m)


# Generation Config - Optimized for better performance
generation_config = {
    "temperature": 0.7,  # Reduced from 0.9 for more consistent responses
    "top_p": 0.9,  # Reduced from 1 for better quality
    "top_k": 40,  # Increased from 1 for better diversity
    "max_output_tokens": 2048,
    "candidate_count": 1,
}

# Safety Settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# API Key Management
class APIKeyManager:
    def __init__(self):
        self.api_keys = []
        self.key_usage = {}
        self.key_failures = {}
        self.last_rotation = time.time()
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load and validate API keys."""
        # First add all keys from the comma-separated list (primary source)
        if settings.GEMINI_API_KEYS_LIST:
            self.api_keys.extend(settings.GEMINI_API_KEYS_LIST)
            logging.info(f"Loaded {len(settings.GEMINI_API_KEYS_LIST)} keys from GEMINI_API_KEYS_LIST")
        
        # Then add the single key as backup if it's not already in the list
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in self.api_keys:
            self.api_keys.append(settings.GEMINI_API_KEY)
            logging.info(f"Added single GEMINI_API_KEY as backup")
        
        # Initialize usage tracking
        for key in self.api_keys:
            self.key_usage[key] = 0
            self.key_failures[key] = 0
    
    def get_best_key(self) -> Optional[str]:
        """Get the best available API key based on usage and failure history."""
        if not self.api_keys:
            return None
        
        # Filter out keys with too many recent failures
        current_time = time.time()
        available_keys = []
        
        for key in self.api_keys:
            # Reset failure count if it's been more than 5 minutes
            if current_time - self.key_failures.get(f"{key}_last_failure", 0) > 300:
                self.key_failures[key] = 0
            
            # Skip keys with too many failures
            if self.key_failures.get(key, 0) < 3:
                available_keys.append(key)
        
        if not available_keys:
            # If all keys have too many failures, reset and try again
            logging.warning("All API keys have too many failures, resetting failure counts")
            for key in self.api_keys:
                self.key_failures[key] = 0
            available_keys = self.api_keys
        
        # Sort by usage (prefer less used keys)
        available_keys.sort(key=lambda k: self.key_usage.get(k, 0))
        
        # Add some randomness to prevent all requests going to the same key
        if len(available_keys) > 1 and random.random() < 0.2:
            available_keys = available_keys[1:] + available_keys[:1]
        
        return available_keys[0] if available_keys else None
    
    def mark_key_usage(self, key: str):
        """Mark a key as used."""
        self.key_usage[key] = self.key_usage.get(key, 0) + 1
    
    def mark_key_failure(self, key: str):
        """Mark a key as failed."""
        self.key_failures[key] = self.key_failures.get(key, 0) + 1
        self.key_failures[f"{key}_last_failure"] = time.time()

# Global API key manager
api_key_manager = APIKeyManager()

def generate_text(prompt: str) -> str:
    """
    Generates text using the Gemini Pro model with enhanced failover and rate limiting.
    """
    if not api_key_manager.api_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured.")

    logging.info(f"Starting Gemini generation with {len(api_key_manager.api_keys)} available API keys")
    
    last_exception = None
    quota_exhausted_count = 0
    attempts = 0
    max_attempts = len(api_key_manager.api_keys) * 2  # Reduced from 3 to prevent excessive retries

    while attempts < max_attempts:
        attempts += 1
        
        # Get the best available key
        key = api_key_manager.get_best_key()
        if not key:
            break
        
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        
        try:
            # Apply enhanced rate limiting per API key
            key_id = f"gemini_{key_prefix}"
            remaining = rate_limiter.get_remaining_requests(key_id, max_requests=30, window_seconds=60)  # Reduced from 50
            
            if remaining <= 0:
                logging.warning(f"Rate limit reached for Gemini key ({key_prefix}...), skipping to next")
                api_key_manager.mark_key_failure(key)
                continue
                
            # Wait if needed to avoid hitting rate limits
            rate_limiter.wait_if_needed(key_id, max_requests=30, window_seconds=60)
            
            logging.info(f"Attempt {attempts}: Trying Gemini generation with key ({key_prefix}...) - {remaining} requests remaining")
            
            genai.configure(api_key=key)

            last_model_exc = None
            for model_name in _MODEL_CANDIDATES:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                    # Add timeout when supported by SDK; fallback if not
                    try:
                        response = model.generate_content(prompt, timeout=30)
                    except TypeError:
                        response = model.generate_content(prompt)

                    # Mark successful usage
                    api_key_manager.mark_key_usage(key)
                    rate_limiter.handle_success(key_id)

                    logging.info(f"✅ Successfully generated text on attempt {attempts} with key ({key_prefix}...) using model {model_name} - {remaining-1} requests remaining")
                    return response.text
                except (NotFound, InvalidArgument) as me:
                    # Only fallback on true model issues; do not swallow key/auth errors
                    msg = str(me).lower()
                    if isinstance(me, NotFound) or "not found" in msg or "not supported" in msg or "unsupported" in msg:
                        last_model_exc = me
                        logging.warning(f"Model {model_name} not available/supported. Trying next candidate. Error: {me}")
                        continue
                    raise
            # If all models failed due to not found/invalid, raise the last one
            if last_model_exc:
                raise last_model_exc
            
        except QUOTA_EXCEPTIONS as e:
            quota_exhausted_count += 1
            api_key_manager.mark_key_failure(key)
            rate_limiter.handle_429_error(f"gemini_{key_prefix}")
            logging.warning(f"❌ Gemini quota exceeded for key ({key_prefix}...): {e}")
            last_exception = e
            
            # Wait before retrying with exponential backoff
            wait_time = min(2 ** attempts, 30)  # Cap at 30 seconds
            logging.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            continue
            
        except ServiceUnavailable as e:
            api_key_manager.mark_key_failure(key)
            logging.warning(f"❌ Gemini service unavailable for key ({key_prefix}...): {e}")
            last_exception = e
            time.sleep(5)  # Short wait for service issues
            continue
            
        except Exception as e:
            api_key_manager.mark_key_failure(key)
            logging.warning(f"❌ Gemini error with key ({key_prefix}...): {e}")
            last_exception = e
            time.sleep(2)  # Short wait for other errors
            continue

    # If we reach here, all attempts failed
    logging.error(f"All {attempts} Gemini API key attempts failed. Quota exhausted: {quota_exhausted_count}, Other errors: {attempts - quota_exhausted_count}")
    
    if quota_exhausted_count >= attempts / 2:  # If more than half were quota errors
        raise HTTPException(status_code=429, detail=f"Multiple Gemini API keys have exceeded quota after {attempts} attempts. Please try again later.")
    
    raise HTTPException(status_code=500, detail=f"Gemini text generation failed after {attempts} attempts: {last_exception}")

def generate_text_with_image(prompt: str, image_path: str) -> str:
    """
    Generates text using the Gemini Pro Vision model with an image and enhanced failover.
    """
    import PIL.Image
    
    if not api_key_manager.api_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured for vision.")

    logging.info(f"Starting Gemini vision generation with {len(api_key_manager.api_keys)} available API keys")
    
    last_exception = None
    quota_exhausted_count = 0
    attempts = 0
    max_attempts = len(api_key_manager.api_keys) * 2

    while attempts < max_attempts:
        attempts += 1
        
        key = api_key_manager.get_best_key()
        if not key:
            break
        
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        
        try:
            # Apply enhanced rate limiting per API key
            key_id = f"gemini_vision_{key_prefix}"
            remaining = rate_limiter.get_remaining_requests(key_id, max_requests=20, window_seconds=60)  # Lower limit for vision
            
            if remaining <= 0:
                logging.warning(f"Rate limit reached for Gemini vision key ({key_prefix}...), skipping to next")
                api_key_manager.mark_key_failure(key)
                continue
                
            # Wait if needed to avoid hitting rate limits
            rate_limiter.wait_if_needed(key_id, max_requests=20, window_seconds=60)
            
            logging.info(f"Attempt {attempts}: Trying Gemini vision generation with key ({key_prefix}...) - {remaining} requests remaining")
            
            genai.configure(api_key=key)
            img = PIL.Image.open(image_path)

            last_model_exc = None
            for model_name in _MODEL_CANDIDATES:
                try:
                    vision_model = genai.GenerativeModel(model_name)
                    try:
                        response = vision_model.generate_content([prompt, img], timeout=30)
                    except TypeError:
                        response = vision_model.generate_content([prompt, img])

                    # Mark successful usage
                    api_key_manager.mark_key_usage(key)
                    rate_limiter.handle_success(key_id)

                    logging.info(f"✅ Successfully generated vision text on attempt {attempts} with key ({key_prefix}...) using model {model_name} - {remaining-1} requests remaining")
                    return response.text
                except (NotFound, InvalidArgument) as me:
                    msg = str(me).lower()
                    if isinstance(me, NotFound) or "not found" in msg or "not supported" in msg or "unsupported" in msg:
                        last_model_exc = me
                        logging.warning(f"Vision model {model_name} not available/supported. Trying next candidate. Error: {me}")
                        continue
                    raise
            if last_model_exc:
                raise last_model_exc
            
        except QUOTA_EXCEPTIONS as e:
            quota_exhausted_count += 1
            api_key_manager.mark_key_failure(key)
            rate_limiter.handle_429_error(f"gemini_vision_{key_prefix}")
            logging.warning(f"❌ Gemini vision quota exceeded for key ({key_prefix}...): {e}")
            last_exception = e
            
            # Wait before retrying with exponential backoff
            wait_time = min(2 ** attempts, 30)
            logging.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            continue
            
        except ServiceUnavailable as e:
            api_key_manager.mark_key_failure(key)
            logging.warning(f"❌ Gemini vision service unavailable for key ({key_prefix}...): {e}")
            last_exception = e
            time.sleep(5)
            continue
            
        except Exception as e:
            api_key_manager.mark_key_failure(key)
            logging.warning(f"❌ Gemini vision error with key ({key_prefix}...): {e}")
            last_exception = e
            time.sleep(2)
            continue

    # If we reach here, all attempts failed
    logging.error(f"All {attempts} Gemini vision API key attempts failed. Quota exhausted: {quota_exhausted_count}, Other errors: {attempts - quota_exhausted_count}")
    
    if quota_exhausted_count >= attempts / 2:
        raise HTTPException(status_code=429, detail=f"Multiple Gemini vision API keys have exceeded quota after {attempts} attempts. Please try again later.")
    
    raise HTTPException(status_code=500, detail=f"Gemini vision generation failed after {attempts} attempts: {last_exception}")

def start_chat_session():
    """
    Starts a new chat session with the Gemini Pro model using enhanced failover.
    """
    if not api_key_manager.api_keys:
        raise HTTPException(status_code=500, detail="No Gemini API keys configured for chat.")

    attempts = 0
    max_attempts = len(api_key_manager.api_keys) * 2

    while attempts < max_attempts:
        attempts += 1
        
        key = api_key_manager.get_best_key()
        if not key:
            break
        
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        
        try:
            genai.configure(api_key=key)
            last_model_exc = None
            for model_name in _MODEL_CANDIDATES:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                    chat_session = model.start_chat(history=[])
                    # Mark successful usage
                    api_key_manager.mark_key_usage(key)
                    logging.info(f"✅ Successfully started chat session on attempt {attempts} with key ({key_prefix}...) using model {model_name}")
                    return chat_session
                except (NotFound, InvalidArgument) as me:
                    msg = str(me).lower()
                    if isinstance(me, NotFound) or "not found" in msg or "not supported" in msg or "unsupported" in msg:
                        last_model_exc = me
                        logging.warning(f"Chat model {model_name} not available/supported. Trying next candidate. Error: {me}")
                        continue
                    raise
            if last_model_exc:
                raise last_model_exc
            
        except Exception as e:
            api_key_manager.mark_key_failure(key)
            logging.warning(f"❌ Failed to start chat session on attempt {attempts} with key ({key_prefix}...): {e}")
            time.sleep(2)
            continue
    
    raise HTTPException(status_code=500, detail=f"Failed to start chat session after {attempts} attempts")

def send_chat_message(chat_session, message: str) -> str:
    """
    Sends a message to the chat session and returns the response.
    Note: This uses the same API key that was used to create the chat session.
    """
    try:
        try:
            response = chat_session.send_message(message, timeout=30)
        except TypeError:
            response = chat_session.send_message(message)
        return response.text
    except QUOTA_EXCEPTIONS as e:
        logging.warning(f"Gemini chat quota exceeded: {e}")
        raise HTTPException(status_code=429, detail="Gemini API quota exceeded during chat. Please try again later.")
    except Exception as e:
        logging.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini chat message failed: {e}")

def get_api_status() -> dict:
    """
    Get status of all API keys for monitoring.
    """
    status = {
        "total_keys": len(api_key_manager.api_keys),
        "available_keys": len([k for k in api_key_manager.api_keys if api_key_manager.key_failures.get(k, 0) < 3]),
        "key_status": {}
    }
    
    for key in api_key_manager.api_keys:
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        status["key_status"][key_prefix] = {
            "usage_count": api_key_manager.key_usage.get(key, 0),
            "failure_count": api_key_manager.key_failures.get(key, 0),
            "last_failure": api_key_manager.key_failures.get(f"{key}_last_failure", 0),
            "rate_limit_status": rate_limiter.get_circuit_breaker_status(f"gemini_{key_prefix}")
        }
    
    return status
