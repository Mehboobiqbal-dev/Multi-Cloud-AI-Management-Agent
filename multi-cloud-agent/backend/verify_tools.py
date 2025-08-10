#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import tool_registry

def verify_universal_account_tool():
    """Verify that the universal account creation tool is properly registered"""
    print("=== Tool Registry Verification ===")
    print(f"Total tools registered: {len(tool_registry.tools)}")
    print("\nAll registered tools:")
    
    for tool_name, tool in tool_registry.tools.items():
        print(f"  - {tool_name}: {tool.description}")
    
    print("\n" + "="*50)
    
    # Check for our new tools
    universal_tool = tool_registry.get_tool("create_account_universal")
    tempmail_tool = tool_registry.get_tool("create_tempmail_account")
    
    if universal_tool:
        print("✅ Universal Account Creation Tool: REGISTERED")
        print(f"   Description: {universal_tool.description}")
        print(f"   Function: {universal_tool.func.__name__}")
    else:
        print("❌ Universal Account Creation Tool: NOT FOUND")
    
    if tempmail_tool:
        print("✅ TempMail Creation Tool: REGISTERED")
        print(f"   Description: {tempmail_tool.description}")
        print(f"   Function: {tempmail_tool.func.__name__}")
    else:
        print("❌ TempMail Creation Tool: NOT FOUND")
    
    print("\n" + "="*50)
    
    # Test tool function signature
    if universal_tool:
        try:
            import inspect
            sig = inspect.signature(universal_tool.func)
            print(f"\n🔍 Universal Tool Function Signature:")
            print(f"   Parameters: {list(sig.parameters.keys())}")
            print(f"   Full signature: {sig}")
        except Exception as e:
            print(f"   Error inspecting function: {e}")
    
    print("\n🎉 Tool verification complete!")

if __name__ == "__main__":
    verify_universal_account_tool()