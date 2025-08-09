from typing import Dict, Any, Callable, List
from cloud_handlers import handle_clouds
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os
import json
import time
import tweepy
from googleapiclient.discovery import build
import openai
from gtts import gTTS
import io
import requests
import base64
from bs4 import BeautifulSoup
from gemini import generate_text as gemini_generate
from cryptography.fernet import Fernet
import pickle

# Import browser management from browsing module
from browsing import (
    browsers as shared_browsers,
    open_browser as browsing_open_browser,
    get_page_content as browsing_get_page_content,
    close_browser as browsing_close_browser,
)

def search_web(query: str, engine: str = 'duckduckgo') -> str:
    """Searches the web using DuckDuckGo or Google through browser automation."""
    return browsing.search_web(query, engine)

# --- Browser Tools ---

# Alias to shared browser dict so all browser operations use the same sessions
browsers: Dict[str, WebDriver] = shared_browsers

def open_browser(url: str) -> str:
    """Opens a new browser window and navigates to the URL."""
    return browsing_open_browser(url)

def get_page_content(browser_id: str) -> str:
    """Gets the text content of the current page."""
    return browsing_get_page_content(browser_id)

def fill_form(browser_id: str, selector: str, value: str, wait_timeout: int = 15) -> str:
    """Enhanced form filling with multiple selector strategies and robust waiting."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    
    driver = browsers[browser_id]
    
    # Multiple selector strategies to try
    selector_strategies = [
        selector,  # Original selector
        f"input{selector}",  # Add input prefix if missing
        f"[name='{selector.replace('[name=\"', '').replace('"]', '').replace("[name='", '').replace("']", '')}']",  # Extract name and rebuild
        f"#{selector.replace('#', '').replace('[id=\"', '').replace('"]', '').replace("[id='", '').replace("']", '')}",  # Try as ID
        f".{selector.replace('.', '').replace('[class=\"', '').replace('"]', '').replace("[class='", '').replace("']", '')}",  # Try as class
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

def fill_multiple_fields(browser_id: str, fields: Dict[str, str], retry_failed: bool = True, page_analysis: bool = True) -> str:
    """Enhanced multiple field filling with adaptive strategies, retries, and page analysis."""
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
            alt_selectors = [
                selector,
                selector.lower(),
                selector.replace('_', ''),
                selector.replace('_', '-'),
                f"input[name*='{selector.replace('[name=\"', '').replace('"]', '').replace('_', '').replace('-', '')}']",
                f"input[id*='{selector.replace('[name=\"', '').replace('"]', '').replace('_', '').replace('-', '')}']",
                f"*[name*='{selector.replace('[name=\"', '').replace('"]', '').replace('_', '').replace('-', '')}']"
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
tool_registry.register(Tool("get_page_content", "Get the text content of the current page", get_page_content))
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