# API Configuration Guide - Preventing 429 Errors

## Overview

This guide helps you configure your Gemini API keys properly to prevent 429 (Too Many Requests) errors and ensure your agent continues to function even when APIs are rate-limited.

## Quick Setup

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Primary Gemini API Keys (comma-separated)
GEMINI_API_KEYS=your_key_1,your_key_2,your_key_3,your_key_4,your_key_5

# Backup single key (optional)
GEMINI_API_KEY=your_backup_key

# Model configuration
GEMINI_MODEL_NAME=gemini-1.5-pro

# Rate limiting settings
RATE_LIMIT_PER_MINUTE=30
MAX_RETRIES=3
INITIAL_RETRY_DELAY=2.0
MAX_RETRY_DELAY=60.0
```

### 2. Recommended API Key Setup

For optimal performance and to prevent 429 errors:

- **Minimum**: 3 API keys
- **Recommended**: 5-10 API keys
- **Maximum**: 20 API keys

## Rate Limiting Configuration

### Current Limits (Per API Key)
- **Text Generation**: 30 requests per minute
- **Vision Generation**: 20 requests per minute
- **Chat Sessions**: 30 requests per minute

### Enhanced Features

1. **Exponential Backoff**: Automatically increases wait times after 429 errors
2. **Circuit Breaker**: Temporarily disables failing APIs to prevent cascading failures
3. **Intelligent Key Rotation**: Distributes requests across available keys
4. **Fallback Responses**: Provides intelligent responses when all APIs are exhausted

## Monitoring and Management

### Check API Status

```bash
GET /api/status/gemini
```

Response includes:
- Available vs total API keys
- Circuit breaker status
- Rate limiting status
- Recommendations for optimization

### Reset Circuit Breakers

```bash
POST /api/reset/gemini
```

Use this when you want to retry failed APIs after adding new keys or waiting for quota reset.

## Best Practices

### 1. API Key Management

- **Rotate Keys Regularly**: Use different keys for different time periods
- **Monitor Usage**: Check the status endpoint regularly
- **Add Keys Gradually**: Don't add all keys at once to avoid simultaneous quota exhaustion

### 2. Request Optimization

- **Batch Requests**: Combine multiple operations when possible
- **Cache Responses**: Store frequently requested data
- **Use Fallbacks**: The system automatically provides intelligent responses when APIs are exhausted

### 3. Error Handling

- **429 Errors**: Automatically handled with exponential backoff
- **Quota Exhaustion**: System switches to fallback responses
- **Service Unavailable**: Automatic retry with different keys

## Troubleshooting

### Common Issues

1. **All APIs Returning 429**
   - Check if all keys have exceeded quota
   - Add more API keys
   - Wait for quota reset (usually hourly)

2. **Circuit Breaker Open**
   - Use the reset endpoint
   - Check if APIs are actually available
   - Review error logs

3. **High Backoff Multipliers**
   - Reduce request frequency
   - Add more API keys
   - Check for API service issues

### Getting More API Keys

1. **Google AI Studio**: https://makersuite.google.com/app/apikey
2. **Google Cloud Console**: https://console.cloud.google.com/
3. **Quota Limits**: Check your Google Cloud project quotas

## Advanced Configuration

### Custom Rate Limits

You can adjust rate limits per key by modifying the `gemini.py` file:

```python
# In generate_text function
remaining = rate_limiter.get_remaining_requests(key_id, max_requests=30, window_seconds=60)

# In generate_text_with_image function  
remaining = rate_limiter.get_remaining_requests(key_id, max_requests=20, window_seconds=60)
```

### Circuit Breaker Settings

```python
# In rate_limiter.py
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        # Adjust these values as needed
        self.failure_threshold = failure_threshold  # Number of failures before opening
        self.recovery_timeout = recovery_timeout    # Seconds to wait before retrying
```

## Fallback Response System

When all APIs are exhausted, the system provides intelligent responses based on:

- **Task Classification**: Automatically detects the type of request
- **Context Awareness**: Uses previous interactions and memory
- **Structured Responses**: Provides actionable steps and guidance

### Response Types

1. **Planning**: Step-by-step task breakdown
2. **Analysis**: Framework for data analysis
3. **Research**: Methodology for information gathering
4. **Automation**: Workflow automation strategies
5. **Content Creation**: Content development process
6. **Error Handling**: Troubleshooting procedures

## Performance Monitoring

### Key Metrics to Watch

1. **API Key Availability**: Percentage of working keys
2. **Circuit Breaker Status**: Health of API endpoints
3. **Backoff Multipliers**: Rate limiting severity
4. **Fallback Usage**: How often fallback responses are used

### Log Analysis

Check these log patterns:
- `429 error for gemini_*`: Rate limit exceeded
- `Circuit breaker opened`: API temporarily disabled
- `Successfully generated fallback response`: Using fallback system
- `API key failures reset`: Recovery after issues

## Support

If you continue experiencing 429 errors:

1. **Check Status**: Use `/api/status/gemini` endpoint
2. **Add Keys**: Increase the number of API keys
3. **Review Logs**: Check for patterns in failures
4. **Contact Support**: If issues persist

## Example Configuration

Here's a complete example `.env` configuration:

```bash
# API Keys (replace with your actual keys)
GEMINI_API_KEYS=AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q,AIzaSyB2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R,AIzaSyC3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S

# Model Configuration
GEMINI_MODEL_NAME=gemini-1.5-pro

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30
MAX_RETRIES=3
INITIAL_RETRY_DELAY=2.0
MAX_RETRY_DELAY=60.0

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Logging
LOG_LEVEL=INFO
```

This configuration should provide robust protection against 429 errors while maintaining high availability for your agent. 