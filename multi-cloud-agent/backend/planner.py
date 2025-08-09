from typing import List, Dict, Any
from core.config import settings

PLAN_RULES = {
    'cloud_operation': ['validate_credentials', 'check_quotas', 'execute_api_call'],
    'web_automation': ['open_browser', 'page_interaction', 'close_browser'],
    'data_processing': ['acquire_data', 'transform_data', 'store_result']
}

def generate_plan(intents: List[Dict[str, Any]], kb: 'KnowledgeBase', tool_manager: 'ToolManager', previous_steps: List[Dict[str, Any]] = None, error: str = None) -> List[Dict[str, Any]]:
    """Generates execution plans using deterministic workflow rules"""
    plan = []
    step_counter = 1
    
    for intent in intents:
        intent_type = intent.get('type')
        
        # Handle error recovery first
        if error and previous_steps:
            last_failed_step = previous_steps[-1]
            plan.append({
                'step': step_counter,
                'action': 'retry',
                'params': {'previous_step': last_failed_step}
            })
            step_counter += 1
            continue
        
        # Apply workflow patterns
        if intent_type in PLAN_RULES:
            for pattern_step in PLAN_RULES[intent_type]:
                plan.append({
                    'step': step_counter,
                    'action': pattern_step,
                    'params': intent.get('params', {})
                })
                step_counter += 1
        else:
            # Fallback to tool-based planning
            available_tools = tool_manager.get_tools()
            if available_tools:
                plan.append({
                    'step': step_counter,
                    'action': 'execute_tool_chain',
                    'params': {
                        'tools': available_tools,
                        'input_params': intent.get('params', {})
                    }
                })
                step_counter += 1
    
    return plan
