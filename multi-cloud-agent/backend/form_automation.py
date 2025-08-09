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
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        element.clear()
        element.send_keys(value)
        return f"Filled field with selector '{selector}' successfully."
    except Exception as e:
        raise Exception(f"Failed to fill form field '{selector}': {e}")

def fill_multiple_fields(browser_id: str, fields: Dict[str, str]) -> str:
    """Fills multiple form fields in one go. Expects a dictionary of CSS selectors to values."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    
    results = []
    for selector, value in fields.items():
        try:
            fill_form(browser_id, selector, value)
            results.append(f"Successfully filled field: {selector}")
        except Exception as e:
            results.append(f"Failed to fill field {selector}: {str(e)}")
    
    return "\n".join(results)

def click_button(browser_id: str, selector: str) -> str:
    """Clicks a button in the specified browser using a CSS selector."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element.click()
        time.sleep(2)  # Wait for potential page load
        return f"Clicked button with selector '{selector}' successfully. Current URL is now {driver.current_url}"
    except Exception as e:
        raise Exception(f"Failed to click button '{selector}': {e}")


def select_dropdown_option(browser_id: str, selector: str, option_text: str) -> str:
    """Selects an option from a dropdown menu by visible text."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        dropdown_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        select = Select(dropdown_element)
        select.select_by_visible_text(option_text)
        return f"Selected option '{option_text}' from dropdown with selector '{selector}' successfully."
    except Exception as e:
        raise Exception(f"Failed to select option '{option_text}' from dropdown '{selector}': {e}")


def upload_file(browser_id: str, selector: str, file_path: str) -> str:
    """Uploads a file using a file input element."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        # Ensure file path is absolute
        abs_file_path = os.path.abspath(file_path)
        if not os.path.exists(abs_file_path):
            raise Exception(f"File not found: {abs_file_path}")
            
        # Find the file input element and send the file path
        file_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        file_input.send_keys(abs_file_path)
        time.sleep(2)  # Wait for upload to begin
        return f"Uploaded file '{abs_file_path}' using input with selector '{selector}' successfully."
    except Exception as e:
        raise Exception(f"Failed to upload file '{file_path}' using input '{selector}': {e}")


def wait_for_element(browser_id: str, selector: str, timeout: int = 10) -> str:
    """Waits for an element to be present on the page."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        return f"Element with selector '{selector}' found on page."
    except Exception as e:
        raise Exception(f"Timed out waiting for element '{selector}': {e}")


def check_checkbox(browser_id: str, selector: str, check: bool = True) -> str:
    """Checks or unchecks a checkbox element."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        checkbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        
        # Check if the current state matches the desired state
        is_selected = checkbox.is_selected()
        if (check and not is_selected) or (not check and is_selected):
            checkbox.click()
            
        action = "checked" if check else "unchecked"
        raise Exception(f"Failed to {action} checkbox '{selector}': {e}")

        return f"Checkbox with selector '{selector}' {action} successfully."
    except Exception as e:
        action = "check" if check else "uncheck"
        raise Exception(f"Failed to {action} checkbox '{selector}': {e}")