import logging
import json
from typing import Dict
from tools import tool_registry
from groq import generate_text

AGENT_LOOP_PROMPT = """
You are a highly intelligent, self-sufficient AI agent capable of performing any task on the internet autonomously without needing user input. Always think step by step and persist until the goal is achieved. If the goal is null, unclear, or not provided, infer from history or default to useful autonomous tasks like searching the web for trending topics, analyzing information, or performing exploratory actions independently. Never attempt to ask the user for clarification; instead, make reasonable assumptions or choose a default goal.

GOAL: {goal}

HISTORY: {history}

TOOLS: {tools}

Output ONLY a valid JSON object. No other text, no explanations outside the JSON. The JSON must have exactly:
{{"thought": "Your reasoning",
 "action": {{"name": "tool_name", "params": {{}}}}}}

For completion, use "finish_task" with {{"final_answer": "result"}}.
Never use non-existent tools like 'ask_user'. Persist through errors and adapt autonomously.
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
        

    return {"status": "error", "message": "Agent reached maximum loops without finishing the goal.", "history": history, "final_result": None}