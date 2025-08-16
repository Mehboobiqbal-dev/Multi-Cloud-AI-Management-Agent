#!/usr/bin/env python3
"""
Test script to verify the enhanced agent execution loop with resilience features.
This test simulates form automation scenarios that previously caused the agent to get stuck.
"""

import json
import time
import logging
from typing import Dict, Any
from unittest.mock import Mock, patch

# Import the enhanced autonomy module
from autonomy import run_agent_loop, execute_tool_with_retry
from tools import tool_registry
from core.config import settings
from core.structured_logging import structured_logger, LogContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_form_automation_resilience():
    """Test that the agent can handle form automation failures gracefully."""
    logger.info("Testing form automation resilience...")
    
    # Mock a form filling scenario that previously caused issues
    goal = "Fill out a contact form on a website"
    
    # Mock the tool registry to simulate form automation tools
    original_get_tool = tool_registry.get_tool
    
    def mock_get_tool(tool_name):
        if tool_name == "wait_for_element":
            mock_tool = Mock()
            # Simulate initial failures followed by success
            mock_tool.func = Mock(side_effect=[
                "Error: Timed out waiting for element 'input[name='email']'",  # First failure
                "Error: Connection refused",  # Second failure
                "Element 'input[name='email']' found successfully using presence strategy."  # Success
            ])
            return mock_tool
        elif tool_name == "fill_form":
            mock_tool = Mock()
            mock_tool.func = Mock(return_value="Form field 'input[name='email']' filled with 'test@example.com' successfully.")
            return mock_tool
        elif tool_name == "finish_task":
            mock_tool = Mock()
            mock_tool.func = Mock(return_value="Form filled successfully")
            return mock_tool
        else:
            return original_get_tool(tool_name)
    
    # Mock the generate_text function to simulate agent decisions
    def mock_generate_text(prompt):
        if "wait_for_element" not in prompt:
            return json.dumps({
                "thought": "I need to wait for the email input field to be available",
                "action": {
                    "name": "wait_for_element",
                    "params": {
                        "browser_id": "browser_0",
                        "css_selector": "input[name='email']",
                        "timeout": 10
                    }
                }
            })
        elif "fill_form" not in prompt:
            return json.dumps({
                "thought": "Now I'll fill the email field",
                "action": {
                    "name": "fill_form",
                    "params": {
                        "browser_id": "browser_0",
                        "selector": "input[name='email']",
                        "value": "test@example.com"
                    }
                }
            })
        else:
            return json.dumps({
                "thought": "Form filling completed successfully",
                "action": {
                    "name": "finish_task",
                    "params": {
                        "final_answer": "Contact form filled successfully"
                    }
                }
            })
    
    with patch('tools.tool_registry.get_tool', side_effect=mock_get_tool), \
         patch('gemini.generate_text', side_effect=mock_generate_text):
        
        start_time = time.time()
        result = run_agent_loop(goal, max_loops=10)
        end_time = time.time()
        
        logger.info(f"Agent execution completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Result: {result}")
        
        # Verify the agent completed successfully despite initial failures
        assert result["status"] == "success", f"Expected success, got {result['status']}"
        assert "Contact form filled successfully" in str(result["final_result"]), "Expected successful form filling"
        assert len(result["history"]) >= 2, "Expected at least 2 steps in history"
        
        # Verify retry logic worked
        wait_steps = [step for step in result["history"] if step["action"]["name"] == "wait_for_element"]
        assert len(wait_steps) >= 1, "Expected at least one wait_for_element step"
        
        logger.info("✅ Form automation resilience test passed!")

def test_consecutive_failure_handling():
    """Test that the agent aborts gracefully after too many consecutive failures."""
    logger.info("Testing consecutive failure handling...")
    
    goal = "Perform a task that will consistently fail"
    
    # Mock tools that always fail
    def mock_get_tool(tool_name):
        mock_tool = Mock()
        mock_tool.func = Mock(side_effect=Exception("Simulated persistent failure"))
        return mock_tool
    
    def mock_generate_text(prompt):
        return json.dumps({
            "thought": "Attempting to execute a failing task",
            "action": {
                "name": "failing_tool",
                "params": {}
            }
        })
    
    with patch('tools.tool_registry.get_tool', side_effect=mock_get_tool), \
         patch('gemini.generate_text', side_effect=mock_generate_text):
        
        result = run_agent_loop(goal, max_loops=10)
        
        logger.info(f"Result: {result}")
        
        # Verify the agent aborted due to consecutive failures
        assert result["status"] == "error", f"Expected error status, got {result['status']}"
        assert "consecutive failures" in result["message"], "Expected consecutive failures message"
        assert len(result["history"]) <= settings.MAX_CONSECUTIVE_FAILURES + 1, "Expected early termination"
        
        logger.info("✅ Consecutive failure handling test passed!")

def test_execute_tool_with_retry():
    """Test the enhanced tool execution with retry logic."""
    logger.info("Testing tool execution with retry logic...")
    
    # Mock a tool that fails initially but succeeds on retry
    mock_tool = Mock()
    mock_tool.func = Mock(side_effect=[
        Exception("Connection refused"),  # First attempt fails
        Exception("Timeout"),  # Second attempt fails
        "Success!"  # Third attempt succeeds
    ])
    
    context = LogContext(metadata={"test": "retry_logic"})
    
    result = execute_tool_with_retry(mock_tool, "test_tool", {}, context)
    
    logger.info(f"Tool execution result: {result}")
    
    # Verify the tool eventually succeeded
    assert result == "Success!", f"Expected success, got {result}"
    assert mock_tool.func.call_count == 3, f"Expected 3 calls, got {mock_tool.func.call_count}"
    
    logger.info("✅ Tool retry logic test passed!")

def test_browser_error_handling():
    """Test specific browser error handling with extra delays."""
    logger.info("Testing browser error handling...")
    
    # Mock a browser tool that fails with browser-specific errors
    mock_tool = Mock()
    mock_tool.func = Mock(side_effect=[
        Exception("no such element: Unable to locate element"),  # Browser error
        Exception("element not interactable"),  # Another browser error
        "Element clicked successfully"  # Success
    ])
    
    context = LogContext(metadata={"test": "browser_errors"})
    
    start_time = time.time()
    result = execute_tool_with_retry(mock_tool, "click_button", {}, context)
    end_time = time.time()
    
    logger.info(f"Browser tool execution result: {result}")
    logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
    
    # Verify the tool eventually succeeded
    assert result == "Element clicked successfully", f"Expected success, got {result}"
    assert mock_tool.func.call_count == 3, f"Expected 3 calls, got {mock_tool.func.call_count}"
    
    # Verify extra delay was applied for browser errors (should take longer than normal retries)
    assert end_time - start_time > 4, "Expected extra delay for browser errors"
    
    logger.info("✅ Browser error handling test passed!")

def run_all_tests():
    """Run all resilience tests."""
    logger.info("🚀 Starting resilience tests...")
    
    try:
        test_form_automation_resilience()
        test_consecutive_failure_handling()
        test_execute_tool_with_retry()
        test_browser_error_handling()
        
        logger.info("🎉 All resilience tests passed successfully!")
        logger.info("The agent should no longer get stuck on form automation failures.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()