from gemini import generate_text as gemini_generate

def detect_language(text: str) -> str:
    """Detects the language of the given text using Gemini."""
    prompt = f"Detect the language of this text: {text}"
    return gemini_generate(prompt).strip()

def translate_text(text: str, target_lang: str) -> str:
    """Translates text to the target language using Gemini."""
    prompt = f"Translate this text to {target_lang}: {text}"
    return gemini_generate(prompt)