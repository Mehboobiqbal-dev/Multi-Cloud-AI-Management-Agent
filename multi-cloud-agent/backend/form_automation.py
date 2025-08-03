from typing import Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
import time

# Assuming browsers dict is shared or imported from browsing.py
extern browsers: Dict[str, WebDriver]

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