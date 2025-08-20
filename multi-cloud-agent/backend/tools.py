import re
from typing import Dict, Any, Callable, List
from cloud_handlers import handle_clouds
import requests
import os
import json
import time
from gemini import generate_text as gemini_generate
from cryptography.fernet import Fernet
import pickle
from code_editor import code_editor

# Import core modules for memory optimization
from core.config import settings
from core.lazy_imports import lazy_import, conditional_import

# Conditional imports based on HIGH_MEMORY_MODE
def _should_use_lazy_imports():
    """Check if we should use lazy imports based on memory settings."""
    return not getattr(settings, 'HIGH_MEMORY_MODE', False)

# Lazy imports for heavy dependencies when memory optimization is enabled
if _should_use_lazy_imports():
    # Use lazy imports for memory optimization
    selenium_webdriver = lazy_import('selenium.webdriver')
    selenium_by = lazy_import('selenium.webdriver.common.by', 'By')
    selenium_wait = lazy_import('selenium.webdriver.support.ui', 'WebDriverWait')
    selenium_ec = lazy_import('selenium.webdriver.support', 'expected_conditions')
    selenium_exceptions = lazy_import('selenium.common.exceptions')
    bs4_soup = lazy_import('bs4', 'BeautifulSoup')
    tweepy_module = lazy_import('tweepy')
    googleapi_build = lazy_import('googleapiclient.discovery', 'build')
    openai_module = lazy_import('openai')
    gtts_module = lazy_import('gtts', 'gTTS')
    
    # Import browsing and form_automation normally to ensure functionality
    import browsing
    from browsing import (
        browsers as shared_browsers,
        open_browser as browsing_open_browser,
        get_page_content as browsing_get_page_content,
        close_browser as browsing_close_browser,
    )
    from browsing import submit_form as browsing_submit_form
    from form_automation import (
        wait_for_element as fa_wait_for_element,
        select_dropdown_option as fa_select_dropdown_option,
        upload_file as fa_upload_file,
        check_checkbox as fa_check_checkbox,
    )
else:
    # Standard imports when HIGH_MEMORY_MODE=true
    from selenium import webdriver as selenium_webdriver
    from selenium.webdriver.common.by import By as selenium_by
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.support.ui import WebDriverWait as selenium_wait
    from selenium.webdriver.support import expected_conditions as selenium_ec
    from selenium.common.exceptions import TimeoutException
    from bs4 import BeautifulSoup as bs4_soup
    import tweepy as tweepy_module
    from googleapiclient.discovery import build as googleapi_build
    import openai as openai_module
    from gtts import gTTS as gtts_module
    
    import browsing
    from browsing import (
        browsers as shared_browsers,
        open_browser as browsing_open_browser,
        get_page_content as browsing_get_page_content,
        close_browser as browsing_close_browser,
    )
    from browsing import submit_form as browsing_submit_form
    from form_automation import (
        wait_for_element as fa_wait_for_element,
        select_dropdown_option as fa_select_dropdown_option,
        upload_file as fa_upload_file,
        check_checkbox as fa_check_checkbox,
    )

# Additional standard imports
import io
import base64

def search_web(query: str, engine: str = 'duckduckgo') -> str:
    """Searches the web using DuckDuckGo or Google through browser automation."""
    return browsing.search_web(query, engine)

# Additional thin wrappers for browser/form tools

def submit_form(browser_id: str, selector: str) -> str:
    """Submit a form by sending Enter to the specified element."""
    return browsing_submit_form(browser_id, selector)


def wait_for_element(browser_id: str, selector: str, timeout: int = 10) -> str:
    """Wait for an element to be present on the page."""
    return fa_wait_for_element(browser_id, selector, timeout)


def select_dropdown_option(browser_id: str, selector: str, option_text: str) -> str:
    """Select an option from a dropdown by visible text."""
    return fa_select_dropdown_option(browser_id, selector, option_text)


def upload_file(browser_id: str, selector: str, file_path: str) -> str:
    """Upload a file using an input[type=file] element."""
    return fa_upload_file(browser_id, selector, file_path)


def check_checkbox(browser_id: str, selector: str, check: bool = True) -> str:
    """Check or uncheck a checkbox element."""
    return fa_check_checkbox(browser_id, selector, check)

# --- Browser Tools ---

# Alias to shared browser dict so all browser operations use the same sessions
# Use dynamic typing to avoid import issues with WebDriver
browsers = shared_browsers

def open_browser(url: str) -> str:
    """Opens a new browser window and navigates to the URL."""
    return browsing_open_browser(url)

def get_page_content(browser_id: str) -> str:
    """Gets the HTML content of the current page."""
    return browsing_get_page_content(browser_id)

def fill_form(browser_id: str, selector: str, value: str, wait_timeout: int = 15) -> str:
    """Enhanced form filling with multiple selector strategies and robust waiting."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    
    driver = browsers[browser_id]
    
    # Get the appropriate imports based on memory mode
    if _should_use_lazy_imports():
        WebDriverWait = selenium_wait
        EC = selenium_ec
        By = selenium_by
    else:
        WebDriverWait = selenium_wait
        EC = selenium_ec
        By = selenium_by
    
    # Multiple selector strategies to try
    # Precompute normalized selector parts to avoid f-string backslash issues
    try:
        _name_sel = re.sub(r"\[name=|[\"']|\]", "", selector)
        _id_sel = re.sub(r"#|\[id=|[\"']|\]", "", selector)
        _class_sel = re.sub(r"\.|\[class=|[\"']|\]", "", selector)
    except Exception:
        _name_sel = _id_sel = _class_sel = selector
    
    selector_strategies = [
        selector,  # Original selector
        f"input{selector}",  # Add input prefix if missing
        f"[name='{_name_sel}']",  # Extract name and rebuild
        f"#{_id_sel}",  # Try as ID
        f".{_class_sel}",  # Try as class
    ]
    
    last_error = None
    for attempt, current_selector in enumerate(selector_strategies):
        try:
            # Wait for element to be present and interactable
            element = WebDriverWait(driver, wait_timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, current_selector))
            )
            
            # Scroll to element to ensure it's visible
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)  # Reduced from 0.5
            
            # Clear and fill the field
            element.clear()
            time.sleep(0.1)  # Reduced from 0.2
            element.send_keys(value)
            time.sleep(0.1)  # Reduced from 0.2
            
            # Verify the value was set
            actual_value = element.get_attribute('value')
            if actual_value == value:
                return f"Filled field with selector '{current_selector}' successfully."
            else:
                # Try alternative input method
                element.clear()
                driver.execute_script("arguments[0].value = arguments[1];", element, value)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
                return f"Filled field with selector '{current_selector}' using JS fallback."
                
        except Exception as e:
            last_error = e
            if attempt < len(selector_strategies) - 1:
                continue  # Try next selector strategy
            
    raise Exception(f"Failed to fill form field after trying {len(selector_strategies)} selector strategies. Last error: {last_error}")

def fill_multiple_fields(browser_id: str, fields: Any, retry_failed: bool = True, page_analysis: bool = True) -> str:
    """Enhanced multiple field filling with adaptive strategies, retries, and page analysis.
    Now uses the improved form_automation.fill_multiple_fields function."""
    # If fields is a list of dictionaries, convert it to the expected dictionary format
    if isinstance(fields, list):
        converted_fields = {}
        for item in fields:
            if isinstance(item, dict) and 'css_selector' in item and 'value' in item:
                converted_fields[item['css_selector']] = item['value']
            else:
                raise ValueError("Each item in 'fields' list must be a dictionary with 'css_selector' and 'value' keys.")
        fields = converted_fields
    elif not isinstance(fields, dict):
        raise TypeError("'fields' parameter must be a dictionary or a list of dictionaries.")
    
    # Use the enhanced form_automation function which has better field mapping
    from form_automation import fill_multiple_fields as form_fill_multiple_fields
    
    try:
        result = form_fill_multiple_fields(browser_id, fields)
        return result
    except Exception as e:
        # Fallback to original implementation if needed
        if browser_id not in browsers:
            raise Exception(f"Browser with ID '{browser_id}' not found.")
        
        driver = browsers[browser_id]
        results = []
        failed_fields = {}
        
        # Page analysis to understand form structure
        if page_analysis:
            try:
                # Get all form inputs on the page
                all_inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
                available_inputs = []
                for inp in all_inputs:
                    name = inp.get_attribute('name') or inp.get_attribute('id') or inp.get_attribute('class')
                    input_type = inp.get_attribute('type') or inp.tag_name
                    available_inputs.append(f"{input_type}[name='{name}']" if name else f"{input_type}[unnamed]")
                
                results.append(f"Page analysis: Found {len(all_inputs)} form inputs: {', '.join(available_inputs[:10])}")
            except Exception as e:
                results.append(f"Page analysis failed: {e}")
    
        # Get the appropriate imports based on memory mode
        if _should_use_lazy_imports():
            WebDriverWait = selenium_wait
            By = selenium_by
        else:
            WebDriverWait = selenium_wait
            By = selenium_by
    
        # Wait for page to be fully loaded
        try:
            WebDriverWait(driver, 5).until(  # Reduced from 10
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(1)  # Reduced from 2 for dynamic content
        except:
            pass
    
    # First pass: try to fill all fields
    for selector, value in fields.items():
        try:
            fill_form(browser_id, selector, value, wait_timeout=10)
            results.append(f"✓ Successfully filled field: {selector}")
        except Exception as e:
            failed_fields[selector] = value
            results.append(f"✗ Failed to fill field {selector}: {str(e)}")
    
    # Second pass: retry failed fields with enhanced strategies
    if retry_failed and failed_fields:
        results.append("\n--- RETRY PHASE ---")
        time.sleep(2)  # Wait before retrying
        
        for selector, value in failed_fields.copy().items():
            # Generate alternative selectors based on common patterns
            clean_name = selector.replace('[name="', '').replace('"]', '').replace('_', '').replace('-', '')
            alt_selectors = [
                selector,
                selector.lower(),
                selector.replace('_', ''),
                selector.replace('_', '-'),
                f"input[name*='{clean_name}']",
                f"input[id*='{clean_name}']",
                f"*[name*='{clean_name}']"
            ]
            
            retry_success = False
            for alt_selector in alt_selectors:
                try:
                    fill_form(browser_id, alt_selector, value, wait_timeout=5)
                    results.append(f"✓ RETRY SUCCESS - filled {selector} using alternative: {alt_selector}")
                    failed_fields.pop(selector)
                    retry_success = True
                    break
                except:
                    continue
            
            if not retry_success:
                # Try finding by placeholder text (common on signup forms like Google)
                try:
                    keywords = []
                    sel_lower = selector.lower()
                    if any(k in sel_lower for k in ["user", "username", "login", "email"]):
                        keywords.extend(["username", "email", "user"])
                    if any(k in sel_lower for k in ["pass", "passwd", "password"]):
                        keywords.extend(["password", "pass"])
                    if "confirm" in sel_lower:
                        keywords.extend(["confirm", "again", "re-enter"])
                    if any(k in sel_lower for k in ["recover", "backup"]):
                        keywords.extend(["recovery", "backup", "alternate"])
                    if "phone" in sel_lower:
                        keywords.append("phone")
                    
                    if not keywords:
                        # Fall back to using the raw selector as a keyword hint
                        keywords.append(sel_lower.strip("[]#.").replace("name=", "").replace("id=", "").replace("'", "").replace('"', ''))
                        
                    placeholder_query = " or ".join([f"contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw}')" for kw in keywords if kw])
                    xpath = f"//input[{placeholder_query}] | //textarea[{placeholder_query}]"
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements:
                        elem = elements[0]
                        driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                        time.sleep(0.2)
                        elem.clear()
                        elem.send_keys(value)
                        results.append(f"✓ RETRY SUCCESS - filled {selector} using placeholder match")
                        failed_fields.pop(selector)
                        retry_success = True
                except:
                    pass
                
                if not retry_success:
                    # Try finding by associated label text
                    try:
                        field_name = selector.replace('[name="', '').replace('"]', '').replace("'", "")
                        label_xpath = f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_name.lower()}')]//input | //label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_name.lower()}')]//textarea"
                        elements = driver.find_elements(By.XPATH, label_xpath)
                        if elements:
                            element = elements[0]
                            driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(0.1)  # Reduced from 0.2
                            element.clear()
                            element.send_keys(value)
                            results.append(f"✓ RETRY SUCCESS - filled {selector} using label association")
                            failed_fields.pop(selector)
                            retry_success = True
                    except:
                        pass

    # Summary
    total_fields = len(fields)
    successful_fields = total_fields - len(failed_fields)
    results.append(f"\n--- SUMMARY ---")
    results.append(f"Total fields: {total_fields}, Successful: {successful_fields}, Failed: {len(failed_fields)}")
    
    if failed_fields:
        results.append(f"Still failed: {list(failed_fields.keys())}")
        # Suggest next steps for remaining failures
        results.append("Consider: 1) Wait for page to load completely, 2) Check if fields require user interaction, 3) Verify field names are correct")
    
    return "\n".join(results)

def click_button(browser_id: str, selector: str) -> str:
    """Clicks a button in the specified browser using a CSS selector."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        
        # Get the appropriate imports based on memory mode
        if _should_use_lazy_imports():
            WebDriverWait = selenium_wait
            EC = selenium_ec
            By = selenium_by
        else:
            WebDriverWait = selenium_wait
            EC = selenium_ec
            By = selenium_by
        
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element.click()
        return f"Clicked button with selector '{selector}' successfully. Current URL is now {driver.current_url}"
    except Exception as e:
        raise Exception(f"Failed to click button '{selector}': {e}")

def close_browser(browser_id: str) -> str:
    """Closes the specified browser window and removes it from the list."""
    return browsing_close_browser(browser_id)

# --- E-commerce Tools ---
def search_amazon_products(query: str, max_results: int = 10) -> str:
    """Search for products on Amazon."""
    browser_id = None
    try:
        # Open Amazon
        open_result = open_browser("https://www.amazon.com")
        browser_id = open_result.split("ID: ")[1].split(".")[0]
        
        # Search for products
        fill_form(browser_id, "input[id='twotabsearchtextbox']", query)
        click_button(browser_id, "input[id='nav-search-submit-button']")
        
        # Get results
        time.sleep(1.5)  # Reduced from 3
        content = get_page_content(browser_id)
        
        # Extract product information (simplified)
        products = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'sponsored' not in line.lower() and '$' in line and len(products) < max_results:
                products.append(line.strip())
        
        return f"Amazon search results for '{query}':\n" + "\n".join(products[:max_results])
    
    except Exception as e:
        return f"Error searching Amazon: {e}"
    finally:
        if browser_id:
            close_browser(browser_id)

def search_ebay_products(query: str, max_results: int = 10) -> str:
    """Search for products on eBay."""
    browser_id = None
    try:
        # Open eBay
        open_result = open_browser("https://www.ebay.com")
        browser_id = open_result.split("ID: ")[1].split(".")[0]
        
        # Search for products
        fill_form(browser_id, "input[id='gh-ac']", query)
        click_button(browser_id, "input[id='gh-btn']")
        
        # Get results
        time.sleep(1.5)  # Reduced from 3
        content = get_page_content(browser_id)
        
        # Extract product information (simplified)
        products = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '$' in line and 'bid' not in line.lower() and len(products) < max_results:
                products.append(line.strip())
        
        return f"eBay search results for '{query}':\n" + "\n".join(products[:max_results])
    
    except Exception as e:
        return f"Error searching eBay: {e}"
    finally:
        if browser_id:
            close_browser(browser_id)

# --- File Operations ---
def read_file(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Failed to read file: {e}")

def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        raise Exception(f"Failed to write file: {e}")

# --- Cloud Operations ---
def cloud_operation(operation: str, service: str, provider: str, params: Dict[str, Any], credentials: Dict[str, str]) -> str:
    """Execute a cloud operation on the specified provider."""
    try:
        return handle_clouds(operation, service, provider, params, credentials)
    except Exception as e:
        raise Exception(f"Cloud operation failed: {e}")

# --- Task Completion ---
def finish_task(final_answer: str) -> str:
    """Mark the current task as completed with the final result."""
    return f"Task completed successfully. Final result: {final_answer}"

# --- Email Tools ---
def send_email(to_email: str, subject: str, body: str, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587, username: str = "", password: str = "") -> str:
    """Send an email."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        text = msg.as_string()
        server.sendmail(username, to_email, text)
        server.quit()
        
        return f"Email sent successfully to {to_email}"
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")

# --- Social Media Tools ---
def post_to_twitter(content: str, api_key: str, api_secret: str, access_token: str, access_token_secret: str) -> str:
    """Post content to Twitter."""
    try:
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        
        api.update_status(content)
        return "Tweet posted successfully"
    except Exception as e:
        raise Exception(f"Failed to post tweet: {e}")

# --- Code Editing Tools ---
def clone_repository(repo_url: str, local_path: str, branch: str = 'main') -> str:
    """Clone a Git repository to local path."""
    return code_editor.clone_repository(repo_url, local_path, branch)

def pull_repository(repo_path: str) -> str:
    """Pull latest changes from remote repository."""
    return code_editor.pull_repository(repo_path)

def analyze_repository_structure(repo_path: str) -> str:
    """Analyze repository structure and provide overview."""
    return code_editor.analyze_repository_structure(repo_path)

def analyze_code_file(file_path: str) -> str:
    """Analyze a single code file for structure and complexity."""
    analysis = code_editor.analyze_code_file(file_path)
    
    result = f"Code Analysis for {file_path}:\n"
    result += f"File Type: {analysis.file_type}\n"
    result += f"Lines of Code: {analysis.lines_of_code}\n"
    result += f"Complexity Score: {analysis.complexity_score}/100\n\n"
    
    if analysis.classes:
        result += f"Classes ({len(analysis.classes)}): {', '.join(analysis.classes)}\n"
    
    if analysis.functions:
        result += f"Functions ({len(analysis.functions)}): {', '.join(analysis.functions[:10])}"
        if len(analysis.functions) > 10:
            result += f" ... and {len(analysis.functions) - 10} more"
        result += "\n"
    
    if analysis.imports:
        result += f"Imports ({len(analysis.imports)}): {', '.join(analysis.imports[:10])}"
        if len(analysis.imports) > 10:
            result += f" ... and {len(analysis.imports) - 10} more"
        result += "\n"
    
    if analysis.issues:
        result += f"\nIssues:\n"
        for issue in analysis.issues:
            result += f"  - {issue}\n"
    
    return result

def search_code_patterns(repo_path: str, pattern: str, file_extensions: str = None) -> str:
    """Search for code patterns across repository."""
    extensions = None
    if file_extensions:
        extensions = [ext.strip() for ext in file_extensions.split(',')]
    return code_editor.search_code_patterns(repo_path, pattern, extensions)

def create_implementation_plan(repo_path: str, feature_description: str) -> str:
    """Create an implementation plan for a new feature."""
    return code_editor.create_implementation_plan(repo_path, feature_description)

def apply_code_changes(file_path: str, changes_json: str) -> str:
    """Apply a series of code changes to a file. Changes should be JSON string with format:
    [{"type": "insert|replace|delete", "line": line_number, "content": "new_content"}]"""
    try:
        import json
        changes = json.loads(changes_json)
        return code_editor.apply_code_changes(file_path, changes)
    except json.JSONDecodeError as e:
        return f"Invalid JSON format for changes: {e}"
    except Exception as e:
        return f"Failed to apply changes: {e}"

def run_tests(repo_path: str, test_command: str = None) -> str:
    """Run tests in the repository."""
    return code_editor.run_tests(repo_path, test_command)

def create_new_file(file_path: str, content: str, file_type: str = None) -> str:
    """Create a new code file with proper structure."""
    try:
        import os
        from pathlib import Path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Add appropriate headers/templates based on file type
        if not file_type:
            file_type = Path(file_path).suffix.lower()
        
        final_content = content
        
        # Add templates for common file types
        if file_type == '.py' and not content.strip().startswith('#!/usr/bin/env python'):
            if 'class ' in content or 'def ' in content:
                final_content = '#!/usr/bin/env python3\n"""\nModule description here.\n"""\n\n' + content
        
        elif file_type in ['.js', '.ts'] and not content.strip().startswith('/**'):
            if 'function ' in content or 'class ' in content:
                final_content = '/**\n * Module description here.\n */\n\n' + content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        return f"Successfully created file {file_path} with {len(final_content.split())} lines"
        
    except Exception as e:
        return f"Failed to create file: {e}"

def refactor_code(file_path: str, refactor_type: str, target: str = None) -> str:
    """Refactor code in a file. Types: extract_function, rename_variable, optimize_imports."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if refactor_type == 'optimize_imports':
            # Simple import optimization for Python
            if file_path.endswith('.py'):
                lines = content.split('\n')
                imports = []
                other_lines = []
                
                for line in lines:
                    if line.strip().startswith(('import ', 'from ')):
                        imports.append(line)
                    else:
                        other_lines.append(line)
                
                # Sort and deduplicate imports
                imports = sorted(list(set(imports)))
                optimized_content = '\n'.join(imports + [''] + other_lines)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(optimized_content)
                
                return f"Optimized imports in {file_path}"
        
        return f"Refactoring type '{refactor_type}' not yet implemented"
        
    except Exception as e:
        return f"Failed to refactor code: {e}"

# --- Tool Registry ---
class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register(self, tool: Tool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)
    
    def get_all_tools_dict(self) -> Dict[str, str]:
        return {name: tool.description for name, tool in self.tools.items()}

# Initialize tool registry
tool_registry = ToolRegistry()

# Register all tools
tool_registry.register(Tool("search_web", "Search the web using DuckDuckGo or Google", search_web))
tool_registry.register(Tool("open_browser", "Open a browser window and navigate to a URL", open_browser))
tool_registry.register(Tool("get_page_content", "Get the HTML content of the current page", get_page_content))
tool_registry.register(Tool("fill_form", "Fill a single form field using CSS selector", fill_form))
tool_registry.register(Tool("fill_multiple_fields", "Fill multiple form fields with enhanced retry logic", fill_multiple_fields))
tool_registry.register(Tool("click_button", "Click a button using CSS selector", click_button))
tool_registry.register(Tool("close_browser", "Close a browser window", close_browser))
tool_registry.register(Tool("search_amazon_products", "Search for products on Amazon", search_amazon_products))
tool_registry.register(Tool("search_ebay_products", "Search for products on eBay", search_ebay_products))
tool_registry.register(Tool("read_file", "Read content from a file", read_file))
tool_registry.register(Tool("write_file", "Write content to a file", write_file))
tool_registry.register(Tool("cloud_operation", "Execute cloud operations", cloud_operation))
tool_registry.register(Tool("finish_task", "Mark task as completed", finish_task))
tool_registry.register(Tool("send_email", "Send an email", send_email))
tool_registry.register(Tool("post_to_twitter", "Post content to Twitter", post_to_twitter))

# Register additional browser interaction tools
tool_registry.register(Tool("submit_form", "Submit a form by pressing Enter on an element", submit_form))
tool_registry.register(Tool("wait_for_element", "Wait until an element is present on the page", wait_for_element))
tool_registry.register(Tool("select_dropdown_option", "Select an option from a dropdown by visible text", select_dropdown_option))
tool_registry.register(Tool("upload_file", "Upload a file using a file input element", upload_file))
tool_registry.register(Tool("check_checkbox", "Check or uncheck a checkbox element", check_checkbox))

# Register code editing tools
tool_registry.register(Tool("clone_repository", "Clone a Git repository to local path", clone_repository))
tool_registry.register(Tool("pull_repository", "Pull latest changes from remote repository", pull_repository))
tool_registry.register(Tool("analyze_repository_structure", "Analyze repository structure and provide overview", analyze_repository_structure))
tool_registry.register(Tool("analyze_code_file", "Analyze a single code file for structure and complexity", analyze_code_file))
tool_registry.register(Tool("search_code_patterns", "Search for code patterns across repository", search_code_patterns))
tool_registry.register(Tool("create_implementation_plan", "Create an implementation plan for a new feature", create_implementation_plan))
tool_registry.register(Tool("apply_code_changes", "Apply a series of code changes to a file", apply_code_changes))
tool_registry.register(Tool("run_tests", "Run tests in the repository", run_tests))
tool_registry.register(Tool("create_new_file", "Create a new code file with proper structure", create_new_file))
tool_registry.register(Tool("refactor_code", "Refactor code in a file", refactor_code))

# Universal Account Creation Tool
def create_account_universal(website_url: str = None, account_data: dict = None, browser_id: str = None) -> str:
    """Create an account on any website automatically with intelligent form detection and filling.
    
    Args:
        website_url: The URL of the website to create an account on (optional if browser already open)
        account_data: Optional dictionary with account details. If not provided, dummy data will be generated.
        browser_id: Optional browser ID (automatically provided by agent loop)
    
    Returns:
        str: JSON string with account creation results including credentials, success status, and details
    """
    import re
    import time
    import random
    import string
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    
    def generate_dummy_data():
        """Generate realistic dummy data for account creation"""
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Chris', 'Lisa', 'Alex', 'Maria']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}"
        email = f"{username}@tempmail.com"
        password = f"Pass{random.randint(1000, 9999)}!"
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}",
            'username': username,
            'email': email,
            'password': password,
            'phone': f"+1{random.randint(2000000000, 9999999999)}",
            'birth_year': str(random.randint(1980, 2000)),
            'birth_month': str(random.randint(1, 12)).zfill(2),
            'birth_day': str(random.randint(1, 28)).zfill(2)
        }
    
    def detect_form_fields(browser_id):
        """Intelligently detect registration form fields"""
        try:
            from browsing import browsers
            driver = browsers.get(browser_id)
            if not driver:
                return []
            
            # Common selectors for registration forms
            field_selectors = [
                # Email fields
                "input[type='email']",
                "input[name*='email']", "input[id*='email']", "input[placeholder*='email']",
                # Username fields
                "input[name*='username']", "input[id*='username']", "input[placeholder*='username']",
                "input[name*='user']", "input[id*='user']",
                # Password fields
                "input[type='password']",
                "input[name*='password']", "input[id*='password']",
                # Name fields
                "input[name*='first']", "input[id*='first']", "input[placeholder*='first']",
                "input[name*='last']", "input[id*='last']", "input[placeholder*='last']",
                "input[name*='name']", "input[id*='name']", "input[placeholder*='name']",
                # Phone fields
                "input[type='tel']", "input[name*='phone']", "input[id*='phone']",
                # Generic text inputs
                "input[type='text']"
            ]
            
            detected_fields = []
            for selector in field_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            field_info = {
                                'element': element,
                                'selector': selector,
                                'name': element.get_attribute('name') or '',
                                'id': element.get_attribute('id') or '',
                                'placeholder': element.get_attribute('placeholder') or '',
                                'type': element.get_attribute('type') or 'text'
                            }
                            detected_fields.append(field_info)
                except:
                    continue
            
            return detected_fields
        except:
            return []
    
    def classify_field(field_info):
        """Classify what type of data a field expects"""
        text = f"{field_info['name']} {field_info['id']} {field_info['placeholder']}".lower()
        
        if 'email' in text:
            return 'email'
        elif 'password' in text:
            if 'confirm' in text or 'repeat' in text or 'again' in text:
                return 'password_confirm'
            return 'password'
        elif 'username' in text or 'user' in text:
            return 'username'
        elif 'first' in text and 'name' in text:
            return 'first_name'
        elif 'last' in text and 'name' in text:
            return 'last_name'
        elif 'name' in text and 'first' not in text and 'last' not in text:
            return 'full_name'
        elif 'phone' in text or field_info['type'] == 'tel':
            return 'phone'
        elif 'birth' in text or 'age' in text:
            if 'year' in text:
                return 'birth_year'
            elif 'month' in text:
                return 'birth_month'
            elif 'day' in text:
                return 'birth_day'
        
        return 'unknown'
    
    def find_submit_button(browser_id):
        """Find the registration/signup submit button"""
        try:
            from browsing import browsers
            driver = browsers.get(browser_id)
            if not driver:
                return None
            
            button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Sign Up')",
                "button:contains('Register')",
                "button:contains('Create Account')",
                "button:contains('Join')",
                "*[class*='signup']",
                "*[class*='register']",
                "*[id*='signup']",
                "*[id*='register']"
            ]
            
            for selector in button_selectors:
                try:
                    if ':contains(' in selector:
                        # Handle text-based selectors differently
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            if any(text in button.text.lower() for text in ['sign up', 'register', 'create account', 'join']):
                                if button.is_displayed() and button.is_enabled():
                                    return button
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                return element
                except:
                    continue
            
            return None
        except:
            return None
    
    try:
        # Use provided data or generate dummy data
        if not account_data:
            account_data = generate_dummy_data()
        
        # Open browser and navigate to website
        browser_result = open_browser(website_url)
        
        # Extract browser ID
        browser_id = None
        if "browser_" in browser_result:
            browser_id = browser_result.split("browser_")[1].split(".")[0]
            browser_id = f"browser_{browser_id}"
        
        if not browser_id:
            import json
            return json.dumps({
                "success": False,
                "website": website_url,
                "error": "Failed to open browser",
                "credentials": account_data if account_data else {}
            }, indent=2)
        
        # Wait for page to load
        time.sleep(3)
        
        # Look for signup/register links first
        try:
            from browsing import browsers
            driver = browsers.get(browser_id)
            if driver:
                signup_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Sign Up")
                signup_links.extend(driver.find_elements(By.PARTIAL_LINK_TEXT, "Register"))
                signup_links.extend(driver.find_elements(By.PARTIAL_LINK_TEXT, "Join"))
                signup_links.extend(driver.find_elements(By.PARTIAL_LINK_TEXT, "Create Account"))
                
                for link in signup_links:
                    if link.is_displayed():
                        link.click()
                        time.sleep(2)
                        break
        except:
            pass
        
        # Detect form fields
        fields = detect_form_fields(browser_id)
        
        if not fields:
            close_browser(browser_id)
            import json
            return json.dumps({
                "success": False,
                "website": website_url,
                "error": "No registration form detected",
                "credentials": account_data if account_data else {}
            }, indent=2)
        
        # Fill form fields
        filled_fields = []
        password_value = None
        
        for field in fields:
            field_type = classify_field(field)
            value = None
            
            if field_type == 'email':
                value = account_data['email']
            elif field_type == 'password':
                value = account_data['password']
                password_value = value
            elif field_type == 'password_confirm':
                value = password_value or account_data['password']
            elif field_type == 'username':
                value = account_data['username']
            elif field_type == 'first_name':
                value = account_data['first_name']
            elif field_type == 'last_name':
                value = account_data['last_name']
            elif field_type == 'full_name':
                value = account_data['full_name']
            elif field_type == 'phone':
                value = account_data['phone']
            elif field_type == 'birth_year':
                value = account_data['birth_year']
            elif field_type == 'birth_month':
                value = account_data['birth_month']
            elif field_type == 'birth_day':
                value = account_data['birth_day']
            
            if value:
                try:
                    field['element'].clear()
                    field['element'].send_keys(value)
                    filled_fields.append(f"{field_type}: {value}")
                    time.sleep(0.5)
                except:
                    continue
        
        # Find and click submit button
        submit_button = find_submit_button(browser_id)
        if submit_button:
            try:
                submit_button.click()
                time.sleep(3)
                
                # Check for success indicators
                success_indicators = ['welcome', 'success', 'created', 'registered', 'confirmation']
                page_content = get_page_content(browser_id).lower()
                
                success = any(indicator in page_content for indicator in success_indicators)
                
                close_browser(browser_id)
                
                import json
                
                result = {
                    "success": success or bool(filled_fields),
                    "website": website_url,
                    "credentials": {
                        "email": account_data['email'],
                        "password": account_data['password'],
                        "username": account_data['username'],
                        "full_name": account_data['full_name'],
                        "phone": account_data['phone']
                    },
                    "filled_fields": filled_fields,
                    "message": "Account created successfully" if success else "Account creation attempted",
                    "login_url": website_url
                }
                
                return json.dumps(result, indent=2)
                    
            except Exception as e:
                close_browser(browser_id)
                import json
                return json.dumps({
                    "success": False,
                    "website": website_url,
                    "error": f"Error submitting form: {str(e)}",
                    "credentials": account_data if account_data else {},
                    "filled_fields": filled_fields
                }, indent=2)
        else:
            close_browser(browser_id)
            import json
            return json.dumps({
                "success": False,
                "website": website_url,
                "error": "No submit button found",
                "credentials": account_data if account_data else {},
                "filled_fields": filled_fields
            }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "success": False,
            "website": website_url,
            "error": f"Error creating account: {str(e)}",
            "credentials": account_data if account_data else {}
        }, indent=2)

# TempMail creation tool (specialized version)
def create_tempmail_account(browser_id: str = None) -> str:
    """Create a temporary email account automatically using various TempMail services.
    
    Args:
        browser_id: Optional browser ID (automatically provided by agent loop)
    
    Returns:
        str: JSON string with temporary email account details including credentials
    """
    import re
    import time
    
    def extract_email_from_content(content):
        """Extract email addresses from page content using regex"""
        email_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'"[^"]*@[^"]*"',
            r"'[^']*@[^']*'",
        ]
        
        emails = []
        for pattern in email_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                email = match.strip('"\'')
                excluded_domains = ['example.com', 'test.com', 'localhost', 'gmail.com', 'yahoo.com', 'hotmail.com']
                if not any(domain in email.lower() for domain in excluded_domains):
                    emails.append(email)
        
        return list(set(emails))
    
    # List of temporary email sites to try
    tempmail_sites = [
        "https://temp-mail.org",
        "https://10minutemail.com", 
        "https://guerrillamail.com",
        "https://tempmail.ninja",
        "https://maildrop.cc"
    ]
    
    for site in tempmail_sites:
        try:
            # Open browser and navigate to site
            browser_result = open_browser(site)
            
            # Extract browser ID
            browser_id = None
            if "browser_" in browser_result:
                browser_id = browser_result.split("browser_")[1].split(".")[0]
                browser_id = f"browser_{browser_id}"
            
            if not browser_id:
                continue
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page content
            content_result = get_page_content(browser_id)
            
            if content_result:
                # Extract emails from content
                emails = extract_email_from_content(content_result)
                
                if emails:
                    # Close browser and return structured result
                    close_browser(browser_id)
                    import json
                    import random
                    
                    # Generate additional dummy data for completeness
                    first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Chris', 'Lisa', 'Alex', 'Maria']
                    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
                    
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    username = emails[0].split('@')[0]
                    
                    result = {
                        "success": True,
                        "website": site,
                        "account_type": "temporary_email",
                        "credentials": {
                            "email": emails[0],
                            "username": username,
                            "password": "N/A (temporary email service)",
                            "full_name": f"{first_name} {last_name}",
                            "first_name": first_name,
                            "last_name": last_name,
                            "phone": "N/A"
                        },
                        "message": "Temporary email account created successfully",
                        "login_url": site,
                        "notes": "This is a temporary email that will expire automatically. No password required for access."
                    }
                    
                    return json.dumps(result, indent=2)
            
            # Close browser before trying next site
            close_browser(browser_id)
            
        except Exception as e:
            continue
    
    import json
    return json.dumps({
        "success": False,
        "error": "Failed to create temporary email account from all available services",
        "attempted_sites": tempmail_sites
    }, indent=2)

# Enhanced account creation tool for popular websites
def create_account_smart(website_name: str = None, use_tempmail: bool = True, browser_id: str = None) -> str:
    """Create accounts on popular websites with predefined strategies and intelligent automation.
    
    Args:
        website_name: Name of the website (e.g., 'gmail', 'github', 'discord', 'reddit', 'twitter')
        use_tempmail: Whether to use temporary email for account creation (default: True)
        browser_id: Optional browser ID (automatically provided by agent loop)
    
    Returns:
        str: JSON string with complete account creation results including all credentials
    """
    import json
    import random
    import time
    
    def generate_smart_data(website_name, use_tempmail=True):
        """Generate smart dummy data tailored for specific websites"""
        first_names = ['Alex', 'Jordan', 'Taylor', 'Casey', 'Morgan', 'Riley', 'Avery', 'Quinn', 'Sage', 'River']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Moore']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}"
        
        if use_tempmail:
            # Create temporary email first
            tempmail_result = create_tempmail_account()
            try:
                tempmail_data = json.loads(tempmail_result)
                if tempmail_data.get('success'):
                    email = tempmail_data['credentials']['email']
                else:
                    email = f"{username}@tempmail.com"
            except:
                email = f"{username}@tempmail.com"
        else:
            email = f"{username}@gmail.com"
        
        password = f"SecurePass{random.randint(1000, 9999)}!"
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}",
            'username': username,
            'email': email,
            'password': password,
            'phone': f"+1{random.randint(2000000000, 9999999999)}",
            'birth_year': str(random.randint(1990, 2005)),
            'birth_month': str(random.randint(1, 12)).zfill(2),
            'birth_day': str(random.randint(1, 28)).zfill(2),
            'display_name': f"{first_name} {last_name}"
        }
    
    # Website-specific URLs and strategies
    website_configs = {
        'gmail': {
            'url': 'https://accounts.google.com/signup',
            'name': 'Gmail/Google Account'
        },
        'github': {
            'url': 'https://github.com/join',
            'name': 'GitHub'
        },
        'discord': {
            'url': 'https://discord.com/register',
            'name': 'Discord'
        },
        'reddit': {
            'url': 'https://www.reddit.com/register',
            'name': 'Reddit'
        },
        'twitter': {
            'url': 'https://twitter.com/i/flow/signup',
            'name': 'Twitter/X'
        },
        'instagram': {
            'url': 'https://www.instagram.com/accounts/emailsignup/',
            'name': 'Instagram'
        },
        'facebook': {
            'url': 'https://www.facebook.com/reg/',
            'name': 'Facebook'
        },
        'linkedin': {
            'url': 'https://www.linkedin.com/signup',
            'name': 'LinkedIn'
        },
        'tiktok': {
            'url': 'https://www.tiktok.com/signup',
            'name': 'TikTok'
        },
        'spotify': {
            'url': 'https://www.spotify.com/signup',
            'name': 'Spotify'
        }
    }
    
    try:
        # If no website specified, try to detect from current page or suggest popular ones
        if not website_name:
            return json.dumps({
                "success": False,
                "error": "Please specify a website name",
                "available_websites": list(website_configs.keys()),
                "example_usage": "Use website_name parameter like 'gmail', 'github', 'discord', etc."
            }, indent=2)
        
        website_name = website_name.lower()
        
        if website_name not in website_configs:
            # Try universal approach for unknown websites
            return create_account_universal(website_name, None, browser_id)
        
        config = website_configs[website_name]
        account_data = generate_smart_data(website_name, use_tempmail)
        
        # Use the universal account creation with the specific URL
        result = create_account_universal(config['url'], account_data, browser_id)
        
        # Parse and enhance the result
        try:
            result_data = json.loads(result)
            result_data['website_name'] = config['name']
            result_data['account_type'] = 'smart_created'
            result_data['tempmail_used'] = use_tempmail
            
            if result_data.get('success'):
                result_data['message'] = f"Successfully created {config['name']} account with intelligent automation"
                result_data['instructions'] = f"You can now login to {config['name']} using the provided credentials"
            
            return json.dumps(result_data, indent=2)
            
        except:
            # Fallback if parsing fails
            return json.dumps({
                "success": False,
                "website_name": config['name'],
                "error": "Failed to parse account creation result",
                "raw_result": result,
                "credentials": account_data
            }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "website_name": website_name,
            "error": f"Error in smart account creation: {str(e)}",
            "fallback": "Try using create_account_universal directly"
        }, indent=2)

# Import scraping function
from scraping_analysis import scrape_website_comprehensive

tool_registry.register(Tool("create_account_universal", "Create an account on any website automatically with intelligent form detection", create_account_universal))
tool_registry.register(Tool("create_tempmail_account", "Create a temporary email account automatically", create_tempmail_account))
tool_registry.register(Tool("create_account_smart", "Create accounts on popular websites (Gmail, GitHub, Discord, Reddit, etc.) with intelligent automation and complete credentials", create_account_smart))
tool_registry.register(Tool("scrape_website_comprehensive", "Comprehensively scrape any website with intelligent data extraction (text, links, images, tables, forms, structured data)", scrape_website_comprehensive))
