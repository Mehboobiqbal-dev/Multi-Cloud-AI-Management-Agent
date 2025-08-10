import logging
import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
from browsing import search_web
from core.config import settings
from core.structured_logging import structured_logger, LogContext, operation_context
from core.circuit_breaker import circuit_breaker, CircuitBreakerConfig
# Assuming a simple JSON-based memory for now; can integrate vector DB later
MEMORY_FILE = 'agent_memory.json'

class SelfLearningCore:
    def __init__(self):
        self.memory = self.load_memory()
        logging.basicConfig(level=logging.INFO, filename='agent.log', format='%(asctime)s - %(levelname)s - %(message)s')

    def load_memory(self) -> Dict:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {'knowledge': [], 'errors': [], 'improvements': []}

    def save_memory(self):
        """Save memory to file with structured logging."""
        try:
            with operation_context('save_memory'):
                with open(MEMORY_FILE, 'w') as f:
                    json.dump(self.memory, f, indent=2)
                
                structured_logger.log_memory_update(
                    "Memory saved to file",
                    LogContext(metadata={'file': MEMORY_FILE}),
                    {
                        "knowledge_count": len(self.memory.get("knowledge", [])),
                        "error_count": len(self.memory.get("errors", [])),
                        "improvement_count": len(self.memory.get("improvements", []))
                    }
                )
        except Exception as e:
            structured_logger.log_memory_update(
                f"Memory save failed: {e}",
                LogContext(metadata={'file': MEMORY_FILE}),
                {"error": str(e)}
            )

    def log_action(self, action: str, details: Dict):
        """Log an action with both traditional and structured logging."""
        try:
            # Use structured logging
            structured_logger.log_self_learning_event(
                f"Agent action: {action}",
                LogContext(metadata={'action_type': action}),
                details
            )
            
            # Also log to Python logging for backward compatibility
            logging.info(f'Action: {action} | Details: {json.dumps(details)}')
            
            self.memory['knowledge'].append({'timestamp': str(datetime.now()), 'type': 'action', 'content': {'action': action, 'details': details}})
            self.save_memory()
            
        except Exception as e:
            logging.error(f"Failed to log action: {e}")

    def log_error(self, error: str, context: Dict):
        logging.error(f'Error: {error} | Context: {json.dumps(context)}')
        if 'errors' not in self.memory:
            self.memory['errors'] = []
        self.memory['errors'].append({'timestamp': str(datetime.now()), 'error': error, 'context': context})
        self.save_memory()
        self.learn_from_error(error, context)

    @circuit_breaker(
        'self_learning',
        CircuitBreakerConfig(
            failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
            recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
            expected_exception=Exception,
            name='self_learning'
        )
    )
    def learn_from_error(self, error: str, context: Dict):
        """Learn from an error and suggest improvements with enhanced resilience."""
        learning_context = LogContext(
            metadata={
                'error_type': type(error).__name__ if hasattr(error, '__class__') else 'string',
                'has_context': context is not None,
                'context_keys': list(context.keys()) if context else []
            }
        )
        
        try:
            with operation_context('learn_from_error', learning_context):
                # Log the error with structured logging
                structured_logger.log_self_learning_event(
                    "Error encountered for learning",
                    learning_context,
                    {
                        "error": error,
                        "context": context or {},
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Check for common parameter naming mistakes
                if "unexpected keyword argument 'css_selector'" in error and 'action' in context and 'params' in context:
                    action = context['action']
                    params = context['params']
                    if action in ['fill_form', 'wait_for_element'] and 'css_selector' in params:
                        corrected_params = params.copy()
                        corrected_params['selector'] = corrected_params.pop('css_selector')
                        fix = {
                            'type': 'parameter_correction',
                            'action': action,
                            'original_params': params,
                            'corrected_params': corrected_params,
                            'description': f"Corrected '{action}' tool call: changed 'css_selector' to 'selector'."
                        }
                        self.memory['improvements'].append(fix)
                        self.save_memory()
                        structured_logger.log_self_learning_event(
                            "Parameter correction applied",
                            learning_context,
                            fix
                        )
                        return # Do not proceed with web search for this type of error

                # If no immediate fix and web search is enabled, search for solutions
                if getattr(settings, 'ENABLE_SELF_LEARNING', True):
                    fix = self.search_for_fix(error)
                    if fix:
                        confidence = self.assess_confidence(fix)
                        if confidence > 0.75:
                            self.apply_fix(fix, context)
                        improvement = {'error': error, 'fix': fix, 'confidence': confidence}
                        self.memory['improvements'].append(improvement)
                        self.save_memory()
                        
                        structured_logger.log_self_learning_event(
                            "Improvement generated from search",
                            learning_context,
                            improvement
                        )
                        
        except Exception as e:
            structured_logger.log_self_learning_event(
                f"Learning from error failed: {e}",
                learning_context,
                {"learning_error": str(e)}
            )

    def search_for_fix(self, error: str) -> str:
        # Use web_search tool
        try:
            results = search_web(f'how to fix {error} in Python')
            return results  # Process and extract fix
        except Exception as e:
            logging.error(f"Web search failed: {e}")
            return None

    def assess_confidence(self, fix: str) -> float:
        # Simple heuristic; improve with ML later
        return 0.8 if 'official' in fix else 0.6

    def apply_fix(self, fix: str, context: Dict):
        # Placeholder for codebase update
        logging.info(f'Applying fix: {fix} to context {context}')

    def post_task_review(self, task: str, success: bool, metrics: Dict):
        review = {'task': task, 'success': success, 'metrics': metrics}
        if not success:
            self.log_error('Task failed', review)
        improvement_plan = self.generate_improvement_plan(review)
        self.apply_improvement(improvement_plan)
        self.memory['improvements'].append(improvement_plan)
        self.save_memory()

    def generate_improvement_plan(self, review: Dict) -> Dict:
        # Logic to create plan
        return {'plan': 'Refactor code', 'details': 'Add caching'}

    def apply_improvement(self, plan: Dict):
        # Update codebase
        logging.info(f'Applying improvement: {json.dumps(plan)}')

# Initialize core
core = SelfLearningCore()