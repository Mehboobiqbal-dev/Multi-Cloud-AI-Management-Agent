import json
from typing import List, Dict, Any
import google.generativeai as genai
from core.config import settings
from fastapi import HTTPException

def extract_intents(prompt: str) -> List[Dict[str, Any]]:
    """Extracts intents from a user prompt using an LLM."""
    if not settings.LLM_API_KEY:
        raise HTTPException(status_code=500, detail="LLM API key not configured.")

    try:
        genai.configure(api_key=settings.LLM_API_KEY)
        model = genai.GenerativeModel(settings.LLM_MODEL_NAME)

        system_prompt = f"""
        You are an expert at extracting structured information from user requests.
        Convert the following prompt into a JSON array of intents, where each intent has an 'action' and 'params'.

        Prompt: "{prompt}"
        """

        response = model.generate_content(system_prompt)
        from core.utils import parse_json_tolerant
        return parse_json_tolerant(response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent extraction failed: {e}")
