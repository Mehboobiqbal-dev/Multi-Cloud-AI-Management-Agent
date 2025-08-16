import json
from typing import List, Dict, Any
from gemini import generate_text
from fastapi import HTTPException

def extract_intents(prompt: str) -> List[Dict[str, Any]]:
    """Extracts intents from a user prompt using Gemini with API key failover."""
    try:
        system_prompt = f"""
        You are an expert at extracting structured information from user requests.
        Convert the following prompt into a JSON array of intents, where each intent has an 'action' and 'params'.

        Prompt: "{prompt}"
        """

        response_text = generate_text(system_prompt)
        from core.utils import parse_json_tolerant
        return parse_json_tolerant(response_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent extraction failed: {e}")
