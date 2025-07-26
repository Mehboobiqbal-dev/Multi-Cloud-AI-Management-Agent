import json
import re
from typing import List, Dict, Any
import google.generativeai as genai
from config import settings

def generate_plan_rule_based(intents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes intents and generates a multi-step execution plan if necessary.
    For now, this is a simple rule-based planner.
    """
    planned_steps = []
    for intent in intents:
        # Example of a complex task that requires planning
        if intent['resource'] == 'vm' and intent['operation'] == 'create' and 'web server' in intent.get('params', {}).get('name', ''):
            # This is a high-level goal. Break it down.
            vm_name = intent['params'].get('name', 'web-server-instance')
            planned_steps.append({
                'step': 1,
                'action': 'create_security_group',
                'cloud': intent['cloud'],
                'params': {'name': f'{vm_name}-sg', 'rules': [{'port': 80, 'protocol': 'tcp'}, {'port': 443, 'protocol': 'tcp'}]}
            })
            planned_steps.append({
                'step': 2,
                'action': 'create_vm',
                'cloud': intent['cloud'],
                'params': {'name': vm_name, 'security_group': f'{vm_name}-sg'}
            })
            planned_steps.append({
                'step': 3,
                'action': 'install_web_server',
                'cloud': intent['cloud'],
                'params': {'instance_name': vm_name}
            })
        else:
            # Simple, single-step task
            planned_steps.append({
                'step': 1,
                'action': f"{intent['operation']}_{intent['resource']}",
                'cloud': intent['cloud'],
                'params': intent['params']
            })
            
    # This is a placeholder for a more sophisticated planning result.
    # In a real scenario, you might return a more structured plan object.
    return planned_steps

def generate_plan(intents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not settings.LLM_API_KEY:
        return generate_plan_rule_based(intents)

    try:
        genai.configure(api_key=settings.LLM_API_KEY)
        model = genai.GenerativeModel(settings.LLM_MODEL_NAME)
        
        system_prompt = """
        You are a world-class AI agent. Your task is to create a multi-step execution plan based on a list of intents.
        The plan should be a JSON object, which is a list of steps. Each step should have the following fields:
        - "step": The step number.
        - "action": The action to perform (e.g., "search_web", "read_file", "execute_command").
        - "params": A dictionary of parameters for the action.

        Example:
        Intents:
        [
            {
                "action": "search_web",
                "params": {
                    "query": "latest news on AI"
                }
            }
        ]

        JSON output:
        [
            {
                "step": 1,
                "action": "search_web",
                "params": {
                    "query": "latest news on AI"
                }
            }
        ]
        """

        response = model.generate_content(f"{system_prompt}\n\nIntents: {json.dumps(intents)}")
        
        # The response from Gemini is not guaranteed to be a JSON object, so we need to extract it.
        json_match = re.search(r'```json\n(.*)\n```', response.text, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group(1))
        else:
            plan = json.loads(response.text)
            
        return plan

    except Exception as e:
        print(f"Error calling LLM: {e}")
        # Fallback to rule-based planner if LLM fails
        return generate_plan_rule_based(intents)
