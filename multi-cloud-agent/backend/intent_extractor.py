import re
import json
from typing import Dict, List, Any
import google.generativeai as genai
from config import settings
import logging
from fastapi import HTTPException

# --- Keyword Mapping (Fallback) ---
CLOUD_KEYWORDS = {
    'aws': ['aws', 'amazon'],
    'azure': ['azure'],
    'gcp': ['gcp', 'google'],
}

OPERATION_KEYWORDS = {
    'create': ['create', 'make', 'build', 'provision'],
    'delete': ['delete', 'remove', 'terminate', 'destroy'],
    'list': ['list', 'show', 'get', 'find'],
    'start': ['start', 'power on', 'turn on'],
    'stop': ['stop', 'power off', 'turn off'],
}

RESOURCE_KEYWORDS = {
    'vm': ['vm', 'virtual machine', 'instance', 'ec2', 'compute engine'],
    'storage': ['storage', 'bucket', 's3', 'blob'],
    'database': ['database', 'rds', 'sql'],
}

def extract_intents_keyword(prompt: str) -> List[Dict[str, Any]]:
    prompt_lower = prompt.lower()
    
    # --- Cloud Extraction ---
    clouds = []
    for cloud, keywords in CLOUD_KEYWORDS.items():
        if any(keyword in prompt_lower for keyword in keywords):
            clouds.append(cloud)
    if not clouds:
        clouds = ['aws', 'azure', 'gcp']  # Default to all if none specified

    # --- Operation and Resource Extraction ---
    operation = 'unknown'
    resource = 'unknown'

    for op, keywords in OPERATION_KEYWORDS.items():
        if any(keyword in prompt_lower for keyword in keywords):
            operation = op
            break

    for res, keywords in RESOURCE_KEYWORDS.items():
        if any(keyword in prompt_lower for keyword in keywords):
            resource = res
            break
            
    # --- Parameter Extraction (e.g., names, regions) ---
    params = {}
    name_match = re.search(r'(?:named|called)\s+["\']?([a-zA-Z0-9_-]+)["\']?', prompt_lower)
    if name_match:
        params['name'] = name_match.group(1)

    region_match = re.search(r'in\s+(?:region\s+)?([a-z0-9-]+)', prompt_lower)
    if region_match:
        params['region'] = region_match.group(1)

    return [
        {
            'cloud': cloud,
            'operation': operation,
            'resource': resource,
            'params': params,
        }
        for cloud in clouds
    ]

def extract_intents(prompt: str) -> List[Dict[str, Any]]:
    if not settings.LLM_API_KEY:
        return extract_intents_keyword(prompt)

    try:
        genai.configure(api_key=settings.LLM_API_KEY)
        model = genai.GenerativeModel(settings.LLM_MODEL_NAME)
        
        system_prompt = """
        You are an expert at understanding user requests for cloud infrastructure management.
        Your task is to extract the key information from the user's prompt and return it as a JSON object.
        The JSON object should be a list of intents, where each intent has the following fields:
        - "cloud": The cloud provider (e.g., "aws", "azure", "gcp"). If not specified, default to all three.
        - "operation": The action to perform (e.g., "create", "delete", "list", "start", "stop").
        - "resource": The type of resource (e.g., "vm", "storage", "database").
        - "params": A dictionary of additional parameters, such as "name" or "region".

        Example:
        User prompt: "create a new ec2 instance named my-vm in us-east-1"
        JSON output:
        [
            {
                "cloud": "aws",
                "operation": "create",
                "resource": "vm",
                "params": {
                    "name": "my-vm",
                    "region": "us-east-1"
                }
            }
        ]
        """

        response = model.generate_content(f"{system_prompt}\n\nUser prompt: {prompt}")
        
        # The response from Gemini is not guaranteed to be a JSON object, so we need to extract it.
        json_match = re.search(r'```json\n(.*)\n```', response.text, re.DOTALL)
        if json_match:
            intents = json.loads(json_match.group(1))
        else:
            intents = json.loads(response.text)
            
        return intents

    except Exception as e:
        logging.error(f"Error calling LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Intent extraction failed: {e}")
