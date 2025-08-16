import json
import re

# Test the exact JSON string that was failing
test_json = '''{ 
   "thought": "To scrape all data from the Wikipedia page, I'll open a browser and navigate to the URL, then get the page content.", 
   "action": { 
     "name": "open_browser", 
     "params": { 
       "url": " `https://en.wikipedia.org/wiki/Portal:Current_events` " 
     } 
   } 
 }'''

print("Original JSON:")
print(test_json)
print("\n" + "="*50 + "\n")

# Apply the same cleaning logic as in main.py
cleaned_json = test_json

# Remove backticks from quoted strings more comprehensively
cleaned_json = re.sub(r'"\s*`([^`]*)`\s*"', r'"\1"', cleaned_json)
cleaned_json = re.sub(r'"([^"]*)`([^`]*)`([^"]*?)"', r'"\1\2\3"', cleaned_json)
# Handle the specific case: " `url` " -> "url"
cleaned_json = re.sub(r'"\s+`([^`]+)`\s+"', r'"\1"', cleaned_json)
cleaned_json = re.sub(r':\s*"\s+([^"]*?)\s+"\s*', r': "\1"', cleaned_json)
# Handle newlines more carefully - only escape unescaped newlines
cleaned_json = re.sub(r'(?<!\\)\n', r'\\n', cleaned_json)
# Remove invalid control characters but preserve newlines and tabs
cleaned_json = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', cleaned_json)

print("Cleaned JSON:")
print(cleaned_json)
print("\n" + "="*50 + "\n")

try:
    parsed = json.loads(cleaned_json)
    print("SUCCESS: JSON parsed successfully!")
    print("Parsed data:")
    print(json.dumps(parsed, indent=2))
except json.JSONDecodeError as e:
    print(f"FAILED: JSONDecodeError - {e}")
except Exception as e:
    print(f"FAILED: Other error - {e}")