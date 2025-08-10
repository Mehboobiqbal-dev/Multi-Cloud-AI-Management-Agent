from typing import Dict, List, Optional, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
import os
import json
from datetime import datetime
import re

# Import browsers dict from browsing.py
from browsing import browsers, open_browser, close_browser

def detect_website_type(driver: WebDriver) -> str:
    """Detect the type of website to apply specific strategies."""
    try:
        current_url = driver.current_url.lower()
        page_title = driver.title.lower()
        
        if 'gmail' in current_url or 'accounts.google' in current_url:
            return 'gmail'
        elif 'tempmail' in current_url or 'temp-mail' in current_url:
            return 'tempmail'
        elif 'outlook' in current_url or 'live.com' in current_url:
            return 'outlook'
        elif 'yahoo' in current_url:
            return 'yahoo'
        elif 'signup' in current_url or 'register' in current_url or 'create' in current_url:
            return 'generic_signup'
        else:
            return 'unknown'
    except Exception:
        return 'unknown'

def fill_form(browser_id: str, selector: str, value: str) -> str:
    """Fills a single form field in the specified browser using a CSS selector."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    try:
        driver = browsers[browser_id]
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        element.clear()
        element.send_keys(value)
        return f"Filled field with selector '{selector}' successfully."
    except Exception as e:
        return f"Error: Failed to fill form field '{selector}': {e}"

def fill_multiple_fields(browser_id: str, fields: Dict[str, str]) -> str:
    """Fills multiple form fields in one go. Expects a dictionary of field names/selectors to values.
    Automatically tries multiple selector strategies for each field with website-specific optimizations."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    
    driver = browsers[browser_id]
    results = []
    errors = []
    
    # Detect website type for specific strategies
    website_type = detect_website_type(driver)
    
    # Website-specific field mappings
    gmail_mappings = {
        'firstName': ['input[name="firstName"]', 'input[id="firstName"]'],
        'lastName': ['input[name="lastName"]', 'input[id="lastName"]'],
        'Username': ['input[name="Username"]', 'input[id="Username"]', 'input[type="email"]'],
        'Passwd': ['input[name="Passwd"]', 'input[id="Passwd"]', 'input[type="password"]'],
        'ConfirmPasswd': ['input[name="ConfirmPasswd"]', 'input[id="ConfirmPasswd"]'],
        'RecoveryEmail': ['input[name="RecoveryEmail"]', 'input[id="RecoveryEmail"]'],
        'RecoveryPhone': ['input[name="RecoveryPhone"]', 'input[id="RecoveryPhone"]']
    }
    
    # Common field name mappings for different websites
    field_mappings = {
        'firstName': ['input[name="firstName"]', 'input[id="firstName"]', 'input[name="first_name"]', 'input[placeholder*="first"]', 'input[aria-label*="first"]'],
        'lastName': ['input[name="lastName"]', 'input[id="lastName"]', 'input[name="last_name"]', 'input[placeholder*="last"]', 'input[aria-label*="last"]'],
        'Username': ['input[name="Username"]', 'input[id="Username"]', 'input[name="username"]', 'input[id="username"]', 'input[type="email"]', 'input[placeholder*="username"]', 'input[placeholder*="email"]'],
        'Passwd': ['input[name="Passwd"]', 'input[id="Passwd"]', 'input[name="password"]', 'input[id="password"]', 'input[type="password"]', 'input[placeholder*="password"]'],
        'ConfirmPasswd': ['input[name="ConfirmPasswd"]', 'input[id="ConfirmPasswd"]', 'input[name="confirm_password"]', 'input[name="password_confirm"]', 'input[placeholder*="confirm"]'],
        'RecoveryEmail': ['input[name="RecoveryEmail"]', 'input[id="RecoveryEmail"]', 'input[name="recovery_email"]', 'input[placeholder*="recovery"]', 'input[placeholder*="alternate"]'],
        'RecoveryPhone': ['input[name="RecoveryPhone"]', 'input[id="RecoveryPhone"]', 'input[name="phone"]', 'input[type="tel"]', 'input[placeholder*="phone"]'],
        'email': ['input[type="email"]', 'input[name="email"]', 'input[id="email"]', 'input[placeholder*="email"]']
    }
    
    # Use website-specific mappings if available
    if website_type == 'gmail':
        field_mappings.update(gmail_mappings)
    
    for field_name, value in fields.items():
        field_filled = False
        
        # If it's already a CSS selector (contains brackets or dots), use it directly
        if '[' in field_name or '.' in field_name or '#' in field_name:
            selectors_to_try = [field_name]
        else:
            # Use mapped selectors or create generic ones
            selectors_to_try = field_mappings.get(field_name, [
                f'input[name="{field_name}"]',
                f'input[id="{field_name}"]',
                f'input[placeholder*="{field_name.lower()}"]',
                f'input[aria-label*="{field_name.lower()}"]'
            ])
        
        # Try each selector until one works with enhanced error handling
        for selector in selectors_to_try:
            try:
                # Wait for element to be present and interactable
                element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                # Additional wait for element to be clickable/interactable
                WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                if element.is_displayed() and element.is_enabled():
                    # Scroll element into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.3)
                    
                    # Try multiple filling strategies
                    try:
                        # Strategy 1: Standard clear and send_keys
                        element.clear()
                        element.send_keys(value)
                    except Exception:
                        try:
                            # Strategy 2: JavaScript value setting
                            driver.execute_script("arguments[0].value = arguments[1];", element, value)
                            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
                        except Exception:
                            # Strategy 3: Click then type
                            element.click()
                            time.sleep(0.2)
                            element.clear()
                            element.send_keys(value)
                    
                    # Verify the value was set
                    actual_value = element.get_attribute('value')
                    if actual_value == value or (value and actual_value and value.lower() in actual_value.lower()):
                        results.append(f"Successfully filled {field_name} using selector: {selector}")
                        field_filled = True
                        time.sleep(0.5)  # Small delay between fields
                        break
                    else:
                        # Value verification failed, try next selector
                        continue
                        
            except Exception as e:
                # Log the specific error for debugging
                continue
        
        if not field_filled:
            errors.append(f"Failed to fill field '{field_name}' - no working selector found")
    
    if errors and not results:
        return f"Error: All fields failed - {'; '.join(errors)}"
    elif errors:
        return f"Partial success - {len(results)} fields filled successfully. Errors: {'; '.join(errors)}"
    else:
        return f"Successfully filled all {len(results)} fields: {', '.join([r.split(' using')[0].replace('Successfully filled ', '') for r in results])}"

def click_button(browser_id: str, selector: str) -> str:
    """Clicks a button in the specified browser using a CSS selector."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    try:
        driver = browsers[browser_id]
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element.click()
        time.sleep(2)  # Wait for potential page load
        return f"Clicked button with selector '{selector}' successfully. Current URL is now {driver.current_url}"
    except Exception as e:
        return f"Error: Failed to click button '{selector}': {e}"


def select_dropdown_option(browser_id: str, selector: str, option_text: str) -> str:
    """Selects an option from a dropdown menu by visible text."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    try:
        driver = browsers[browser_id]
        dropdown_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        select = Select(dropdown_element)
        select.select_by_visible_text(option_text)
        return f"Selected option '{option_text}' from dropdown with selector '{selector}' successfully."
    except Exception as e:
        return f"Error: Failed to select option '{option_text}' from dropdown '{selector}': {e}"


def upload_file(browser_id: str, selector: str, file_path: str) -> str:
    """Uploads a file using a file input element."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    try:
        driver = browsers[browser_id]
        # Ensure file path is absolute
        abs_file_path = os.path.abspath(file_path)
        if not os.path.exists(abs_file_path):
            return f"Error: File not found: {abs_file_path}"
            
        # Find the file input element and send the file path
        file_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        file_input.send_keys(abs_file_path)
        time.sleep(2)  # Wait for upload to begin
        return f"Uploaded file '{abs_file_path}' using input with selector '{selector}' successfully."
    except Exception as e:
        return f"Error: Failed to upload file '{file_path}' using input '{selector}': {e}"


def wait_for_element(browser_id: str, selector: str, timeout: int = 10) -> str:
    """Wait for an element to be present on the page with enhanced resilience."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    
    try:
        driver = browsers[browser_id]
        
        # Try multiple strategies to find the element
        strategies = [
            (EC.presence_of_element_located, "presence"),
            (EC.element_to_be_clickable, "clickable"),
            (EC.visibility_of_element_located, "visible")
        ]
        
        for strategy, strategy_name in strategies:
            try:
                element = WebDriverWait(driver, timeout // len(strategies)).until(
                    strategy((By.CSS_SELECTOR, selector))
                )
                return f"Element '{selector}' found successfully using {strategy_name} strategy."
            except Exception as strategy_error:
                # Try next strategy
                continue
        
        # If all strategies failed, try alternative selectors
        alternative_selectors = []
        
        # Extract name attribute if it's an input selector
        if "input[name='" in selector and "']" in selector:
            name_value = selector.replace("input[name='", "").replace("']", "")
            alternative_selectors.extend([
                f"*[name='{name_value}']",
                f"input[name=\"{name_value}\"]",
                f"[name='{name_value}']"
            ])
        
        # Extract ID if it's an ID selector
        if selector.startswith('#'):
            id_value = selector[1:]
            alternative_selectors.extend([
                f"*[id='{id_value}']",
                f"[id='{id_value}']"
            ])
        
        # Extract class if it's a class selector
        if selector.startswith('.'):
            class_value = selector[1:]
            alternative_selectors.extend([
                f"*[class*='{class_value}']",
                f"[class*='{class_value}']"
            ])
        
        for alt_selector in alternative_selectors:
            if alt_selector != selector:  # Don't retry the same selector
                try:
                    element = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, alt_selector))
                    )
                    return f"Element found using alternative selector '{alt_selector}'."
                except:
                    continue
        
        return f"Error: Timed out waiting for element '{selector}' after trying multiple strategies and selectors."
        
    except Exception as e:
        return f"Error: Failed to wait for element '{selector}': {e}"


def check_checkbox(browser_id: str, selector: str, check: bool = True) -> str:
    """Checks or unchecks a checkbox element."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    try:
        driver = browsers[browser_id]
        checkbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        
        # Check if the current state matches the desired state
        is_selected = checkbox.is_selected()
        if (check and not is_selected) or (not check and is_selected):
            checkbox.click()
            
        action = "checked" if check else "unchecked"
        return f"Checkbox with selector '{selector}' {action} successfully."
    except Exception as e:
        action = "check" if check else "uncheck"
        return f"Error: Failed to {action} checkbox '{selector}': {e}"