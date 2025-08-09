from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import PromptRequest, PromptResponse
from core.db import get_db
from planner import generate_plan
from intent_extractor import extract_intents
from execution_engine import execute_step
from knowledge_base import KnowledgeBase
from tool_manager import ToolManager
from evaluation import evaluate_plan_execution
# from self_learning import learn_from_execution

router = APIRouter()

MAX_ITERATIONS = 10

@router.post("/prompt", response_model=PromptResponse)
def handle_prompt(request: PromptRequest, db: Session = Depends(get_db)):
    tool_manager = ToolManager()
    """Handles a user prompt by generating a plan and executing it with self-correction."""
    try:
        kb = KnowledgeBase()
        intents = extract_intents(request.prompt)
        plan = generate_plan(intents, kb, tool_manager)
        
        executed_steps = []
        for i in range(MAX_ITERATIONS):
            if not plan:
                break

            step = plan.pop(0)
            result, error = execute_step(step, kb, tool_manager)

            executed_steps.append({"step": step, "result": result, "error": error})

            if error:
                plan = generate_plan(intents, kb, tool_manager, executed_steps, error)
            elif not plan:
                break

        # learn_from_execution(executed_steps, kb)
        evaluation_score = evaluate_plan_execution(executed_steps)

        return {
            "status": "success",
            "message": "Plan executed successfully.",
            "steps": executed_steps,
            "evaluation_score": evaluation_score
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))