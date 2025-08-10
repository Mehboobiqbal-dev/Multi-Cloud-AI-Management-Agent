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

# Import browsers dict from browsing.py
from browsing import browsers, open_browser, close_browser

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
    """Fills multiple form fields in one go. Expects a dictionary of CSS selectors to values."""
    if browser_id not in browsers:
        return f"Error: Browser with ID '{browser_id}' not found."
    
    results = []
    errors = []
    for selector, value in fields.items():
        result = fill_form(browser_id, selector, value)
        if result.startswith("Error:"):
            errors.append(f"Failed to fill field {selector}: {result}")
        else:
            results.append(f"Successfully filled field: {selector}")
    
    if errors and not results:
        return f"Error: All fields failed - {'; '.join(errors)}"
    elif errors:
        return f"Partial success - {'; '.join(results)}. Errors: {'; '.join(errors)}"
    else:
        return "\n".join(results)

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