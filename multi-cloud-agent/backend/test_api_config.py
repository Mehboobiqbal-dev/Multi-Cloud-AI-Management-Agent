#!/usr/bin/env python3
"""
API Configuration Test Script

This script helps you test your Gemini API configuration and identify potential issues
that could cause 429 errors.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_keys() -> Dict[str, Any]:
    """Test all configured API keys and return their status."""
    results = {
        "total_keys": 0,
        "valid_keys": 0,
        "invalid_keys": 0,
        "quota_exceeded": 0,
        "key_details": []
    }
    
    # Get API keys from environment
    gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
    single_key = os.getenv("GEMINI_API_KEY", "")
    
    api_keys = []
    
    # Add keys from comma-separated list
    if gemini_keys_str:
        keys_from_list = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
        api_keys.extend(keys_from_list)
        logger.info(f"Found {len(keys_from_list)} keys in GEMINI_API_KEYS")
    
    # Add single key if not already in list
    if single_key and single_key not in api_keys:
        api_keys.append(single_key)
        logger.info("Added single GEMINI_API_KEY")
    
    results["total_keys"] = len(api_keys)
    
    if not api_keys:
        logger.error("No API keys found! Please configure GEMINI_API_KEYS or GEMINI_API_KEY")
        return results
    
    logger.info(f"Testing {len(api_keys)} API keys...")
    
    # Test each key
    for i, key in enumerate(api_keys):
        key_prefix = key[:10] if len(key) >= 10 else key[:6]
        logger.info(f"Testing key {i+1}/{len(api_keys)}: {key_prefix}...")
        
        key_result = test_single_key(key, key_prefix)
        results["key_details"].append(key_result)
        
        if key_result["status"] == "valid":
            results["valid_keys"] += 1
        elif key_result["status"] == "quota_exceeded":
            results["quota_exceeded"] += 1
        else:
            results["invalid_keys"] += 1
        
        # Small delay between tests to avoid rate limiting
        time.sleep(1)
    
    return results

def test_single_key(api_key: str, key_prefix: str) -> Dict[str, Any]:
    """Test a single API key."""
    result = {
        "key_prefix": key_prefix,
        "status": "unknown",
        "error": None,
        "response_time": None,
        "quota_info": None
    }
    
    try:
        # Test with a simple prompt
        test_prompt = "Hello, this is a test message. Please respond with 'API test successful'."
        
        start_time = time.time()
        
        # Make API request
        response = make_gemini_request(api_key, test_prompt)
        
        end_time = time.time()
        result["response_time"] = round(end_time - start_time, 2)
        
        if response.get("success"):
            result["status"] = "valid"
            logger.info(f"✅ Key {key_prefix}... is valid (response time: {result['response_time']}s)")
        else:
            error_msg = response.get("error", "Unknown error")
            result["error"] = error_msg
            
            if "quota" in error_msg.lower() or "429" in error_msg:
                result["status"] = "quota_exceeded"
                logger.warning(f"⚠️ Key {key_prefix}... quota exceeded")
            else:
                result["status"] = "invalid"
                logger.error(f"❌ Key {key_prefix}... is invalid: {error_msg}")
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"❌ Error testing key {key_prefix}...: {e}")
    
    return result

def make_gemini_request(api_key: str, prompt: str) -> Dict[str, Any]:
    """Make a request to the Gemini API."""
    try:
        import google.generativeai as genai
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Create model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate content
        response = model.generate_content(prompt)
        
        return {
            "success": True,
            "response": response.text,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "error": str(e)
        }

def check_rate_limiting_config() -> Dict[str, Any]:
    """Check rate limiting configuration."""
    config = {
        "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", 60)),
        "max_retries": int(os.getenv("MAX_RETRIES", 3)),
        "initial_retry_delay": float(os.getenv("INITIAL_RETRY_DELAY", 2.0)),
        "max_retry_delay": float(os.getenv("MAX_RETRY_DELAY", 60.0)),
        "circuit_breaker_failure_threshold": int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5)),
        "circuit_breaker_recovery_timeout": int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", 60))
    }
    
    # Validate configuration
    issues = []
    
    if config["rate_limit_per_minute"] > 50:
        issues.append("Rate limit per minute is quite high (>50). Consider reducing to 30-40.")
    
    if config["max_retries"] < 2:
        issues.append("Max retries is low (<2). Consider increasing to 3-5.")
    
    if config["initial_retry_delay"] < 1.0:
        issues.append("Initial retry delay is very low (<1s). Consider increasing to 2-5 seconds.")
    
    if config["circuit_breaker_failure_threshold"] < 3:
        issues.append("Circuit breaker failure threshold is low (<3). Consider increasing to 5-10.")
    
    config["issues"] = issues
    return config

def generate_recommendations(api_results: Dict[str, Any], rate_limit_config: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on test results."""
    recommendations = []
    
    # API Key recommendations
    if api_results["total_keys"] == 0:
        recommendations.append("🚨 No API keys configured! Add GEMINI_API_KEYS to your .env file.")
    elif api_results["valid_keys"] == 0:
        recommendations.append("🚨 No valid API keys found! Check your API key configuration.")
    elif api_results["valid_keys"] < 3:
        recommendations.append("⚠️ Few valid API keys (<3). Consider adding more keys for better reliability.")
    elif api_results["quota_exceeded"] > 0:
        recommendations.append(f"⚠️ {api_results['quota_exceeded']} keys have exceeded quota. Wait for quota reset or add new keys.")
    
    # Rate limiting recommendations
    for issue in rate_limit_config.get("issues", []):
        recommendations.append(f"⚙️ {issue}")
    
    # General recommendations
    if api_results["valid_keys"] >= 3:
        recommendations.append("✅ Good number of API keys configured.")
    
    if not rate_limit_config.get("issues"):
        recommendations.append("✅ Rate limiting configuration looks good.")
    
    return recommendations

def main():
    """Main test function."""
    print("🔧 Gemini API Configuration Test")
    print("=" * 50)
    
    # Test API keys
    print("\n📋 Testing API Keys...")
    api_results = test_api_keys()
    
    print(f"\n📊 API Key Results:")
    print(f"  Total Keys: {api_results['total_keys']}")
    print(f"  Valid Keys: {api_results['valid_keys']}")
    print(f"  Invalid Keys: {api_results['invalid_keys']}")
    print(f"  Quota Exceeded: {api_results['quota_exceeded']}")
    
    # Check rate limiting configuration
    print("\n⚙️ Checking Rate Limiting Configuration...")
    rate_limit_config = check_rate_limiting_config()
    
    print(f"\n📊 Rate Limiting Configuration:")
    for key, value in rate_limit_config.items():
        if key != "issues":
            print(f"  {key}: {value}")
    
    # Generate recommendations
    print("\n💡 Recommendations:")
    recommendations = generate_recommendations(api_results, rate_limit_config)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    # Summary
    print("\n" + "=" * 50)
    if api_results["valid_keys"] > 0 and not rate_limit_config.get("issues"):
        print("✅ Configuration looks good! Your agent should work properly.")
    elif api_results["valid_keys"] > 0:
        print("⚠️ Configuration has some issues but should work. Review recommendations above.")
    else:
        print("❌ Configuration has critical issues. Please fix before using the agent.")
    
    print("\n📝 Next Steps:")
    if api_results["valid_keys"] == 0:
        print("  1. Get API keys from https://makersuite.google.com/app/apikey")
        print("  2. Add them to your .env file as GEMINI_API_KEYS=key1,key2,key3")
        print("  3. Run this test again")
    else:
        print("  1. Start your agent server")
        print("  2. Monitor API usage with GET /api/status/gemini")
        print("  3. Check logs for any 429 errors")

if __name__ == "__main__":
    main() 