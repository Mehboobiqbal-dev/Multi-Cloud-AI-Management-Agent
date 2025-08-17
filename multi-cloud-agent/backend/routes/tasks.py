from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import os

from core.db import get_db
from auth import get_current_user
from models import User, AgentSession
import schemas

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/results", response_model=dict)
async def get_task_results(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get task results for the current user
    """
    try:
        # Query agent sessions for the current user
        query = db.query(AgentSession).filter(AgentSession.user_id == current_user.id)
        
        if status:
            query = query.filter(AgentSession.status == status)
        
        # Order by most recent first
        query = query.order_by(AgentSession.updated_at.desc())
        
        # Apply pagination
        total_count = query.count()
        sessions = query.offset(offset).limit(limit).all()
        
        # Convert sessions to task results format
        results = []
        for session in sessions:
            task_result = {
                "id": session.id,
                "goal": session.goal,
                "description": session.goal or "Agent Task",
                "status": session.status,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "result": session.result if hasattr(session, 'result') else None,
                "steps_completed": len(session.history) if session.history else 0,
                "total_steps": len(session.history) if session.history else 0,
                "user_id": session.user_id
            }
            
            # Try to extract more detailed information from history
            if session.history:
                try:
                    history = json.loads(session.history) if isinstance(session.history, str) else session.history
                    if isinstance(history, list) and history:
                        # Get the last step for result information
                        last_step = history[-1]
                        if isinstance(last_step, dict):
                            task_result["result"] = last_step.get("result", last_step.get("observation", "Task completed"))
                except (json.JSONDecodeError, TypeError):
                    pass
            
            results.append(task_result)
        
        return {
            "results": results,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task results: {str(e)}")

@router.get("/statistics", response_model=dict)
async def get_task_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get task statistics for the current user
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query sessions within date range
        sessions = db.query(AgentSession).filter(
            AgentSession.user_id == current_user.id,
            AgentSession.created_at >= start_date,
            AgentSession.created_at <= end_date
        ).all()
        
        # Calculate statistics
        total = len(sessions)
        completed = len([s for s in sessions if s.status == 'completed'])
        failed = len([s for s in sessions if s.status == 'failed'])
        running = len([s for s in sessions if s.status in ['running', 'in_progress']])
        paused = len([s for s in sessions if s.status == 'paused'])
        
        success_rate = completed / total if total > 0 else 0
        
        # Calculate average duration for completed tasks
        completed_sessions = [s for s in sessions if s.status == 'completed' and s.created_at and s.updated_at]
        avg_duration = 0
        if completed_sessions:
            total_duration = sum([(s.updated_at - s.created_at).total_seconds() for s in completed_sessions])
            avg_duration = total_duration / len(completed_sessions)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "paused": paused,
            "success_rate": success_rate,
            "average_duration_seconds": avg_duration,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task statistics: {str(e)}")

@router.get("/{task_id}/download")
async def download_task_result(
    task_id: int,
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download task result in specified format
    """
    try:
        # Get the specific task/session
        session = db.query(AgentSession).filter(
            AgentSession.id == task_id,
            AgentSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Prepare task data
        task_data = {
            "id": session.id,
            "goal": session.goal,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "history": session.history,
            "user_id": session.user_id
        }
        
        # Format the response based on requested format
        if format.lower() == "json":
            content = json.dumps(task_data, indent=2)
            media_type = "application/json"
            filename = f"task-{task_id}-result.json"
        elif format.lower() == "txt":
            # Create a readable text format
            content = f"Task ID: {task_data['id']}\n"
            content += f"Goal: {task_data['goal']}\n"
            content += f"Status: {task_data['status']}\n"
            content += f"Created: {task_data['created_at']}\n"
            content += f"Updated: {task_data['updated_at']}\n\n"
            
            if task_data['history']:
                content += "History:\n"
                try:
                    history = json.loads(task_data['history']) if isinstance(task_data['history'], str) else task_data['history']
                    if isinstance(history, list):
                        for i, step in enumerate(history, 1):
                            content += f"\nStep {i}:\n"
                            if isinstance(step, dict):
                                for key, value in step.items():
                                    content += f"  {key}: {value}\n"
                            else:
                                content += f"  {step}\n"
                except (json.JSONDecodeError, TypeError):
                    content += f"  {task_data['history']}\n"
            
            media_type = "text/plain"
            filename = f"task-{task_id}-result.txt"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'txt'")
        
        # Return file response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading task result: {str(e)}")

@router.delete("/{task_id}")
async def delete_task_result(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a task result
    """
    try:
        # Get the specific task/session
        session = db.query(AgentSession).filter(
            AgentSession.id == task_id,
            AgentSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Delete the session
        db.delete(session)
        db.commit()
        
        return {"message": "Task result deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting task result: {str(e)}")