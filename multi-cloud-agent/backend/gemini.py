import google.generativeai as genai
from config import settings
import logging
from fastapi import HTTPException

genai.configure(api_key=settings.GEMINI_API_KEY)

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

# Initialize the models
model = genai.GenerativeModel(
    model_name=settings.GEMINI_MODEL_NAME,
    generation_config=generation_config,
    safety_settings=safety_settings
)

vision_model = genai.GenerativeModel('gemini-pro-vision')

def generate_text(prompt: str) -> str:
    """
    Generates text using the Gemini Pro model.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error generating text: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini text generation failed: {e}")

def generate_text_with_image(prompt: str, image_path: str) -> str:
    """
    Generates text using the Gemini Pro Vision model with an image.
    """
    import PIL.Image

    try:
        img = PIL.Image.open(image_path)
        response = vision_model.generate_content([prompt, img])
        return response.text
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
