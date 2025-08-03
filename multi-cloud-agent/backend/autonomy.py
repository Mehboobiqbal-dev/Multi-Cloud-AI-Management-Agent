import logging
import json
from typing import Dict
from tools import tool_registry
from groq import generate_text

AGENT_LOOP_PROMPT = """
You are an autonomous AI agent. Your goal is: {goal}

Past actions and results:
{history}

Available tools:
{tools}

Think step-by-step. Output a JSON object with:
- "thought": Your reasoning.
- "action": {{"name": tool_name, "params": {}}}
Or to finish: {{"name": "finish_task", "params": {"final_answer": "..."}}}
"""

def run_agent_loop(goal: str, max_loops: int = 15) -> Dict:
    history = []
    for i in range(max_loops):
        history_str = "\n".join([f"  - Step {h['step']}: I used '{h['action']['name']}' which resulted in: '{h['result']}'" for h in history]) if history else "  - No actions taken yet."
        prompt = AGENT_LOOP_PROMPT.format(goal=goal, history=history_str, tools=json.dumps(tool_registry.get_all_tools_dict(), indent=2))
        
        try:
            response_text = generate_text(prompt)
            decision_data = json.loads(response_text)
            thought = decision_data.get("thought", "No thought provided.")
            action_data = decision_data.get("action", {})
            action_name = action_data.get("name")
            action_params = action_data.get("params", {})
        except Exception as e:
            return {"status": "error", "message": f"Failed to parse agent decision: {e}", "history": history, "final_result": None}

        if not action_name:
            return {"status": "error", "message": f"Agent generated an invalid action. Last thought: {thought}", "history": history, "final_result": None}

        tool = tool_registry.get_tool(action_name)
        if not tool:
            result = f"Error: Tool '{action_name}' not found."
        else:
            try:
                result = tool.func(**action_params)
            except Exception as e:
                result = f"Error executing tool '{action_name}': {e}"
        
        history.append({
            "step": i + 1,
            "thought": thought,
            "action": action_data,
            "result": str(result)
        })

        if action_name == "finish_task":
            return {"status": "success", "message": "Agent completed the goal.", "history": history, "final_result": result}
        if action_name == "ask_user":
            return {"status": "requires_input", "message": "Agent requires user input.", "history": history, "final_result": result}

    return {"status": "error", "message": "Agent reached maximum loops without finishing the goal.", "history": history, "final_result": None}