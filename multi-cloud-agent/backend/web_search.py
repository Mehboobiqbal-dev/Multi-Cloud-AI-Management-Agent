import requests
import time
import random
from typing import List, Dict, Any, Optional
import logging
from core.config import settings
from core.circuit_breaker import circuit_breaker, CircuitBreakerConfig
from core.structured_logging import structured_logger, LogContext, operation_context

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of fallback search engines and their base URLs
SEARCH_ENGINES = [
    {"name": "google", "url": "https://www.google.com/search?q="},
    {"name": "duckduckgo", "url": "https://duckduckgo.com/html/?q="},
    {"name": "bing", "url": "https://www.bing.com/search?q="},
    {"name": "yandex", "url": "https://yandex.com/search/?text="},
]

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
]

@circuit_breaker(
    'web_search',
    CircuitBreakerConfig(
        failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
        recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
        expected_exception=requests.exceptions.RequestException,
        name='web_search'
    )
)
def search(query: str, max_retries: int = 3, fallback_engines: bool = True) -> str:
    """Performs a web search with retry logic and multiple fallback engines.
    
    Args:
        query: The search query string
        max_retries: Maximum number of retry attempts per search engine
        fallback_engines: Whether to try alternative search engines on failure
        
    Returns:
        Search results as text or error message
    """
    context = LogContext(metadata={'query': query, 'max_retries': max_retries, 'fallback_engines': fallback_engines})
    
    with operation_context('web_search', context):
        engines_to_try = SEARCH_ENGINES if fallback_engines else [SEARCH_ENGINES[0]]
        results = []
        errors = []
    
    for engine in engines_to_try:
        engine_name = engine["name"]
        base_url = engine["url"]
        
        # Try this engine with retries
        for attempt in range(max_retries):
            try:
                # Use a random user agent for each request
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                
                # Add jitter to avoid being detected as a bot
                if attempt > 0:
                    jitter = random.uniform(0.5, 2.0) * attempt
                    time.sleep(jitter)
                
                structured_logger.log_retry_attempt('web_search', attempt, f'Searching with {engine_name}', context)
                
                network_timeout = getattr(settings, 'NETWORK_TIMEOUT', 10)
                response = requests.get(
                    f"{base_url}{query}", 
                    headers=headers,
                    timeout=network_timeout
                )
                response.raise_for_status()
                
                # If we get here, the request was successful
                structured_logger.log_tool_execution(
                    'web_search',
                    True,
                    0,  # Duration will be calculated by operation_context
                    context,
                    {'engine': engine_name, 'attempt': attempt+1}
                )
                return f"Search results from {engine_name}: {response.text[:1000]}..."
                
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                structured_logger.log_tool_execution(
                    'web_search',
                    False,
                    0,
                    context,
                    {'engine': engine_name, 'attempt': attempt+1, 'error': error_msg}
                )
                errors.append(f"{engine_name} attempt {attempt+1}: {error_msg}")
                
                # Check if we should retry this engine or move to next one
                is_connection_error = any(msg in error_msg.lower() for msg in [
                    "failed to connect", "connection refused", "timeout", 
                    "socket", "network", "unreachable"
                ])
                
                if not is_connection_error or attempt == max_retries - 1:
                    # Either not a connection error or last attempt, move to next engine
                    break
    
        # If we get here, all engines failed
        error_summary = "\n".join(errors)
        structured_logger.log_tool_execution(
            'web_search',
            False,
            0,
            context,
            {'all_engines_failed': True, 'total_errors': len(errors)}
        )
        return f"All search attempts failed. Details:\n{error_summary}\n\nPlease try again later or with a different query."