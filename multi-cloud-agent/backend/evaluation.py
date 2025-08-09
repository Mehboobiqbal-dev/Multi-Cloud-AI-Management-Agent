from typing import List, Dict, Any

def evaluate_plan_execution(executed_steps: List[Dict[str, Any]]) -> float:
    """Evaluates the success of a plan execution based on errors."""
    if not executed_steps:
        return 0.0

    error_count = sum(1 for step in executed_steps if step.get('error'))
    success_rate = 1 - (error_count / len(executed_steps))
    return success_rate