import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class ResponseFormatter:
    """Utility class to format agent responses in a structured way for better frontend presentation."""
    
    @staticmethod
    def format_agent_response(
        status: str,
        message: str,
        history: List[Dict[str, Any]],
        final_result: Optional[str] = None,
        goal: Optional[str] = None,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None
    ) -> Dict[str, Any]:
        """Format an agent response with structured data for better frontend presentation."""
        
        # Parse and structure the final result if available
        structured_result = None
        if final_result:
            structured_result = ResponseFormatter._parse_result_content(final_result)
        
        # Create progress information
        progress = None
        if history:
            completed_steps = len([h for h in history if h.get('result')])
            progress = {
                'completed': completed_steps,
                'total': len(history),
                'current_step': ResponseFormatter._get_current_step_description(history),
                'steps': ResponseFormatter._format_history_steps(history)
            }
        
        # Format the main message content
        formatted_content = ResponseFormatter._format_message_content(
            message, status, goal, structured_result, progress
        )
        
        return {
            'status': status,
            'message': message,
            'content': formatted_content,
            'final_result': final_result,
            'history': history,
            'metadata': {
                'status': status,
                'goal': goal,
                'progress': progress,
                'structured_result': structured_result,
                'timestamp': datetime.now().isoformat(),
                'history': history
            }
        }
    
    @staticmethod
    def _parse_result_content(result: str) -> Dict[str, Any]:
        """Parse result content to extract structured information."""
        try:
            # Try to parse as JSON first
            if result.strip().startswith('{') or result.strip().startswith('['):
                return {
                    'type': 'json',
                    'data': json.loads(result)
                }
        except json.JSONDecodeError:
            pass
        
        # Parse different content patterns
        structured = {
            'type': 'text',
            'sections': [],
            'summary': '',
            'actions_taken': [],
            'results': [],
            'errors': []
        }
        
        lines = result.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect section headers
            if line.startswith('#') or line.endswith(':'):
                if current_section:
                    structured['sections'].append(current_section)
                current_section = {
                    'title': line.replace('#', '').replace(':', '').strip(),
                    'content': [],
                    'type': ResponseFormatter._detect_section_type(line)
                }
            # Detect lists
            elif line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line):
                item = re.sub(r'^[-*]\s*|^\d+\.\s*', '', line)
                if 'completed' in line.lower() or 'success' in line.lower():
                    structured['actions_taken'].append(item)
                elif 'error' in line.lower() or 'failed' in line.lower():
                    structured['errors'].append(item)
                else:
                    structured['results'].append(item)
                    
                if current_section:
                    current_section['content'].append(item)
            # Regular text
            else:
                if not structured['summary'] and not current_section:
                    structured['summary'] = line
                elif current_section:
                    current_section['content'].append(line)
        
        if current_section:
            structured['sections'].append(current_section)
        
        return structured
    
    @staticmethod
    def _detect_section_type(title: str) -> str:
        """Detect the type of section based on title."""
        title_lower = title.lower()
        if any(word in title_lower for word in ['error', 'failed', 'problem']):
            return 'error'
        elif any(word in title_lower for word in ['success', 'completed', 'done']):
            return 'success'
        elif any(word in title_lower for word in ['warning', 'caution', 'note']):
            return 'warning'
        elif any(word in title_lower for word in ['step', 'action', 'process']):
            return 'steps'
        elif any(word in title_lower for word in ['result', 'output', 'data']):
            return 'results'
        elif any(word in title_lower for word in ['code', 'script', 'command']):
            return 'code'
        else:
            return 'info'
    
    @staticmethod
    def _get_current_step_description(history: List[Dict[str, Any]]) -> Optional[str]:
        """Get description of the current step from history."""
        if not history:
            return None
        
        last_step = history[-1]
        action = last_step.get('action', {})
        action_name = action.get('name', 'Unknown action')
        
        # Format action name for display
        formatted_name = action_name.replace('_', ' ').title()
        
        return f"{formatted_name} (Step {last_step.get('step', len(history))})"
    
    @staticmethod
    def _format_history_steps(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format history steps for progress display."""
        formatted_steps = []
        
        for step in history:
            action = step.get('action', {})
            action_name = action.get('name', 'Unknown')
            result = step.get('result', '')
            
            # Determine step status
            status = 'completed'
            if isinstance(result, str):
                if 'error' in result.lower() or 'failed' in result.lower():
                    status = 'failed'
                elif not result.strip():
                    status = 'pending'
            
            formatted_steps.append({
                'name': action_name.replace('_', ' ').title(),
                'description': str(result)[:100] + '...' if len(str(result)) > 100 else str(result),
                'status': status,
                'step_number': step.get('step', len(formatted_steps) + 1)
            })
        
        return formatted_steps
    
    @staticmethod
    def _format_message_content(
        message: str,
        status: str,
        goal: Optional[str] = None,
        structured_result: Optional[Dict[str, Any]] = None,
        progress: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format the main message content with structured information."""
        
        content_parts = []
        
        # Add title based on status
        if status == 'success':
            content_parts.append('# ✅ Task Completed Successfully')
        elif status == 'error':
            content_parts.append('# ❌ Task Failed')
        elif status == 'requires_input':
            content_parts.append('# ⏸️ User Input Required')
        elif status == 'running':
            content_parts.append('# 🔄 Task In Progress')
        else:
            content_parts.append('# 📋 Task Update')
        
        # Add goal if available
        if goal:
            content_parts.append(f'\n**Goal:** {goal}')
        
        # Add main message
        if message:
            content_parts.append(f'\n{message}')
        
        # Add progress information
        if progress and progress.get('steps'):
            content_parts.append('\n## 📊 Progress Summary')
            completed = progress.get('completed', 0)
            total = progress.get('total', 0)
            if total > 0:
                percentage = (completed / total) * 100
                content_parts.append(f'\n**Progress:** {completed}/{total} steps completed ({percentage:.1f}%)')
            
            if progress.get('current_step'):
                content_parts.append(f'\n**Current Step:** {progress["current_step"]}')
        
        # Add structured results
        if structured_result:
            if structured_result.get('summary'):
                content_parts.append(f'\n## 📝 Summary\n\n{structured_result["summary"]}')
            
            if structured_result.get('actions_taken'):
                content_parts.append('\n## ✅ Actions Completed')
                for action in structured_result['actions_taken']:
                    content_parts.append(f'- {action}')
            
            if structured_result.get('results'):
                content_parts.append('\n## 📊 Results')
                for result in structured_result['results']:
                    content_parts.append(f'- {result}')
            
            if structured_result.get('errors'):
                content_parts.append('\n## ⚠️ Issues Encountered')
                for error in structured_result['errors']:
                    content_parts.append(f'- {error}')
            
            # Add sections
            for section in structured_result.get('sections', []):
                icon = ResponseFormatter._get_section_icon(section.get('type', 'info'))
                content_parts.append(f'\n## {icon} {section["title"]}')
                for item in section.get('content', []):
                    content_parts.append(f'\n{item}')
        
        return '\n'.join(content_parts)
    
    @staticmethod
    def _get_section_icon(section_type: str) -> str:
        """Get appropriate icon for section type."""
        icons = {
            'error': '❌',
            'success': '✅',
            'warning': '⚠️',
            'steps': '📋',
            'results': '📊',
            'code': '💻',
            'info': '📝'
        }
        return icons.get(section_type, '📝')
    
    @staticmethod
    def format_websocket_update(
        status: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format websocket updates for real-time communication."""
        return {
            'topic': 'agent_updates',
            'payload': {
                'status': status,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'data': data or {}
            }
        }
    
    @staticmethod
    def format_task_completion_notification(
        goal: str,
        result: str,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format task completion notification with action buttons."""
        return {
            'type': 'task_completion_notification',
            'goal': goal,
            'result': result,
            'history_count': len(history),
            'actions': [
                {
                    'type': 'view_task_results',
                    'label': 'View Task Results',
                    'primary': True
                },
                {
                    'type': 'ask_about_task',
                    'label': 'Ask About Task',
                    'primary': False
                }
            ]
        }