import logging
import json
import time
from typing import Dict
from tools import tool_registry
from gemini import generate_text
from self_learning import SelfLearningCore
from core.config import settings
from core.structured_logging import structured_logger, LogContext, operation_context
from core.circuit_breaker import circuit_breaker, CircuitBreakerConfig

core = SelfLearningCore()
logging.basicConfig(level=logging.INFO)

AGENT_LOOP_PROMPT = """
You are a highly intelligent, self-sufficient AI agent capable of performing any task on the internet autonomously without needing user input. Always think step by step and persist until the goal is achieved. If the goal is null, unclear, or not provided, infer from history or default to useful autonomous tasks like searching the web for trending topics, analyzing information, or performing exploratory actions independently. Never attempt to ask the user for clarification; instead, make reasonable assumptions or choose a default goal.

SPECIAL CAPABILITIES:
- Universal Account Creation: Use 'create_account_universal' to automatically create accounts on ANY website. This tool intelligently detects registration forms, fills them with realistic dummy data, and handles the entire signup process autonomously.
- TempMail Creation: Use 'create_tempmail_account' for quick temporary email addresses.
- When users request account creation on any website, prioritize using 'create_account_universal' as it can handle any site automatically.

GOAL: {goal}

HISTORY: {history}

TOOLS: {tools}

Output ONLY a valid JSON object. No other text, no explanations outside the JSON. The JSON must have exactly:
{{"thought": "Your reasoning",
 "action": {{"name": "tool_name", "params": {{}}}}}}

For completion, use "finish_task" with {{"final_answer": "result"}}.
For any browser-related tool (e.g., `get_page_content`, `fill_form`, `fill_multiple_fields`, `submit_form`, `close_browser`), always include the `browser_id` parameter, inferring it from previous `open_browser` actions in the history.
Never use non-existent tools like 'ask_user'. Persist through errors and adapt autonomously.
"""

@circuit_breaker(
    'agent_execution',
    CircuitBreakerConfig(
        failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
        recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
        expected_exception=Exception,
        name='agent_execution'
    )
)
def run_agent_loop(goal: str, max_loops: int = 30) -> Dict:
    """Enhanced agent loop with proper error handling, retry logic, and recovery mechanisms."""
    history = []
    consecutive_failures = 0
    max_consecutive_failures = getattr(settings, 'MAX_CONSECUTIVE_FAILURES', 3)
    
    context = LogContext(metadata={'goal': goal, 'max_loops': max_loops})
    
    with operation_context('agent_loop', context):
        for i in range(max_loops):
            history_str = "\n".join([f"  - Step {h['step']}: I used '{h['action']['name']}' which resulted in: '{h['result']}'" for h in history]) if history else "  - No actions taken yet."
            prompt = AGENT_LOOP_PROMPT.format(goal=goal, history=history_str, tools=json.dumps(tool_registry.get_all_tools_dict(), indent=2))
            
            # Generate agent decision with retry logic
            decision_data = None
            for decision_attempt in range(3):  # Max 3 attempts to get valid decision
                try:
                    structured_logger.log_agent_action(
                        f"Generating agent decision (attempt {decision_attempt + 1}/3)",
                        context,
                        {"step": i + 1, "attempt": decision_attempt + 1}
                    )
                    response_text = generate_text(prompt)
                    # Use centralized tolerant JSON parsing
                    from core.utils import parse_json_tolerant
                    try:
                        decision_data = parse_json_tolerant(response_text)
                    except Exception:
                        # Final fallback: try raw JSON parse
                        decision_data = json.loads(response_text)
                    break
                except Exception as e:
                    structured_logger.log_error(
                        f"Failed to parse agent decision (attempt {decision_attempt + 1}/3): {e}",
                        context,
                        {"error": str(e), "attempt": decision_attempt + 1}
                    )
                    if decision_attempt == 2:  # Last attempt
                        return {"status": "error", "message": f"Failed to parse agent decision after 3 attempts: {e}", "history": history, "final_result": None}
                    time.sleep(1)  # Brief pause before retry
            
            if not decision_data:
                return {"status": "error", "message": "Failed to generate valid agent decision", "history": history, "final_result": None}
            
            thought = decision_data.get("thought", "No thought provided.")
            action_data = decision_data.get("action", {})
            action_name = action_data.get("name")
            action_params = action_data.get("params", {})
            
            if not action_name:
                consecutive_failures += 1
                structured_logger.log_error(
                    f"Agent generated invalid action (consecutive failures: {consecutive_failures})",
                    context,
                    {"thought": thought, "consecutive_failures": consecutive_failures}
                )
                if consecutive_failures >= max_consecutive_failures:
                    return {"status": "error", "message": f"Too many consecutive failures ({consecutive_failures}). Last thought: {thought}", "history": history, "final_result": None}
                continue
            
            tool = tool_registry.get_tool(action_name)
            if not tool:
                result = f"Error: Tool '{action_name}' not found."
                consecutive_failures += 1
            else:
                # Execute tool with enhanced error handling and retry logic
                result = execute_tool_with_retry(tool, action_name, action_params, context)
                
                # Check if execution was successful
                if isinstance(result, str) and result.startswith("Error"):
                    consecutive_failures += 1
                    
                    # Learn from the error for future improvements
                    try:
                        core.learn_from_error(action_name, action_params, result)
                    except Exception as learning_error:
                        structured_logger.log_error(
                            f"Failed to learn from error: {learning_error}",
                            context,
                            {"original_error": result, "learning_error": str(learning_error)}
                        )
                else:
                    consecutive_failures = 0  # Reset on success
            
            # Log the step execution
            structured_logger.log_agent_action(
                f"Executed step {i + 1}: {action_name}",
                context,
                {
                    "step": i + 1,
                    "action_name": action_name,
                    "success": not (isinstance(result, str) and result.startswith("Error")),
                    "consecutive_failures": consecutive_failures
                }
            )
            
            history.append({
                "step": i + 1,
                "thought": thought,
                "action": action_data,
                "result": str(result)
            })
            
            # Check for task completion
            if action_name == "finish_task":
                structured_logger.log_agent_action(
                    "Agent completed the goal successfully",
                    context,
                    {"total_steps": i + 1, "final_result": str(result)}
                )
                return {"status": "success", "message": "Agent completed the goal.", "history": history, "final_result": result}
            
            # Check if we should abort due to too many consecutive failures
            if consecutive_failures >= max_consecutive_failures:
                structured_logger.log_error(
                    f"Aborting due to {consecutive_failures} consecutive failures",
                    context,
                    {"max_consecutive_failures": max_consecutive_failures, "total_steps": i + 1}
                )
                return {"status": "error", "message": f"Agent aborted after {consecutive_failures} consecutive failures.", "history": history, "final_result": None}
        
        structured_logger.log_error(
            "Agent reached maximum loops without finishing",
            context,
            {"max_loops": max_loops, "total_steps": len(history)}
        )
        return {"status": "error", "message": "Agent reached maximum loops without finishing the goal.", "history": history, "final_result": None}


def execute_tool_with_retry(tool, action_name: str, action_params: dict, context: LogContext) -> str:
    """Execute a tool with intelligent retry logic and error recovery."""
    max_retries = getattr(settings, 'MAX_RETRIES', 3)
    retry_delay = float(getattr(settings, 'INITIAL_RETRY_DELAY', 2.0))
    max_retry_delay = float(getattr(settings, 'MAX_RETRY_DELAY', 60.0))
    
    # Check for and apply parameter corrections from self-learning
    applied_correction = False
    if 'improvements' in core.memory:
        for i, improvement in enumerate(core.memory['improvements']):
            if (improvement.get('type') == 'parameter_correction' and 
                improvement.get('action') == action_name and 
                improvement.get('original_params') == action_params):
                action_params = improvement['corrected_params']
                core.memory['improvements'].pop(i)
                core.save_memory()
                applied_correction = True
                structured_logger.log_agent_action(
                    f"Applied parameter correction for {action_name}: {improvement['description']}",
                    context,
                    {"correction_applied": True, "original_params": improvement['original_params']}
                )
                break
    
    # Determine if this is a network/browser operation that needs special handling
    is_network_operation = any(term in action_name.lower() for term in 
                              ['browser', 'form', 'web', 'search', 'http', 'api', 'wait_for'])
    
    last_error = None
    for attempt in range(max_retries):
        try:
            structured_logger.log_tool_execution(
                f"Executing {action_name} (attempt {attempt + 1}/{max_retries})",
                context,
                {"attempt": attempt + 1, "is_network_operation": is_network_operation, "params": action_params}
            )
            
            result = tool.func(**action_params)
            
            # Success - reset any failure tracking
            if attempt > 0:
                structured_logger.log_tool_execution(
                    f"Tool {action_name} succeeded after {attempt + 1} attempts",
                    context,
                    {"success_after_retries": True, "total_attempts": attempt + 1}
                )
            
            return result
            
        except Exception as e:
            last_error = e
            error_msg = str(e)
            
            # Check if it's a recoverable error
            is_network_error = any(msg in error_msg.lower() for msg in [
                "failed to connect", "connection refused", "timeout", 
                "socket", "network", "unreachable", "dns", "http error",
                "certificate", "ssl", "proxy", "gateway", "no such element",
                "element not found", "stale element", "element not interactable"
            ])
            
            is_browser_error = any(msg in error_msg.lower() for msg in [
                "no such element", "element not found", "stale element", 
                "element not interactable", "element click intercepted",
                "element not visible", "invalid session", "chrome not reachable"
            ])
            
            should_retry = (is_network_error or is_browser_error) and attempt < max_retries - 1
            
            structured_logger.log_error(
                f"Tool {action_name} failed (attempt {attempt + 1}/{max_retries}): {error_msg}",
                context,
                {
                    "error": error_msg,
                    "attempt": attempt + 1,
                    "is_network_error": is_network_error,
                    "is_browser_error": is_browser_error,
                    "will_retry": should_retry
                }
            )
            
            if should_retry:
                # Add extra delay for browser errors to allow page to stabilize
                actual_delay = retry_delay * 2 if is_browser_error else retry_delay
                time.sleep(actual_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            else:
                # Not retryable or last attempt
                break
    
    # All retries exhausted
    final_error_msg = f"Error executing tool '{action_name}' after {max_retries} attempts: {str(last_error)}"
    structured_logger.log_error(
        f"Tool {action_name} failed permanently after all retries",
        context,
        {"final_error": str(last_error), "total_attempts": max_retries}
    )
    
    return final_error_msg