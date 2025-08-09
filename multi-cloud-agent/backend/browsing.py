from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import requests
import os
import time
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

browsers: Dict[str, WebDriver] = {}


def search_web(query: str, engine: str = 'duckduckgo') -> str:
    """Searches the web for the given query using DuckDuckGo Instant Answer API or headless browser scraping."""
    
    if engine not in ['duckduckgo', 'google']:
        engine = 'duckduckgo'
    
    if engine == 'google':
        browser_id = None
        try:
            open_browser_output = open_browser('https://www.google.com')
            match = re.search(r"Browser opened with ID: (browser_\d+)", open_browser_output)
            if match:
                browser_id = match.group(1)
                fill_form(browser_id, "textarea[name='q']", query)
                submit_form(browser_id, "textarea[name='q']")
                time.sleep(2) # Give time for results to load
                content = get_page_content(browser_id)
                return f"Google Search Results for '{query}':\n\n{content}"
            else:
                return "Error: Could not open browser for Google search."
        except Exception as e:
            return f"Error during Google search: {e}"
        finally:
            if browser_id:
                close_browser(browser_id)

    # Try DuckDuckGo Instant Answer API first (free, no API key required)
    if engine == 'duckduckgo':
        try:
            # DuckDuckGo Instant Answer API
            duckduckgo_url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
            response = requests.get(duckduckgo_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            summary_parts = []
            
            # Extract Abstract (main answer)
            if data.get('Abstract'):
                summary_parts.append(f"Answer: {data['Abstract']}")
                if data.get('AbstractURL'):
                    summary_parts.append(f"Source: {data['AbstractURL']}")
            
            # Extract Related Topics
            if data.get('RelatedTopics'):
                summary_parts.append("Related Topics:")
                for topic in data['RelatedTopics'][:3]:  # Limit to 3 topics
                    if 'Text' in topic:
                        summary_parts.append(f"  - {topic['Text']}")
                        if 'FirstURL' in topic:
                            summary_parts.append(f"    Link: {topic['FirstURL']}")
            
            if summary_parts:
                return "\n".join(summary_parts)
        except Exception as e:
            return f"Error during DuckDuckGo API search: {e}. Browser-based search is not supported for this engine."

def open_browser(url: str) -> str:
    """Opens a new headless Chrome browser window and navigates to the specified URL."""
    try:
        browser_id = f"browser_{len(browsers)}"
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        browsers[browser_id] = driver
        return f"Browser opened with ID: {browser_id}. Navigated to {url}. You can now read its content or interact with it."
    except Exception as e:
        raise Exception(f"Failed to open browser: {e}")

def get_page_content(browser_id: str) -> str:
    """Gets the clean text content of the current page in the specified browser."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        content = driver.find_element(By.TAG_NAME, 'body').text
        return '\n'.join([line for line in content.split('\n') if line.strip()])
    except Exception as e:
        raise Exception(f"Failed to get page content from browser '{browser_id}': {e}")

def fill_form(browser_id: str, selector: str, value: str) -> str:
    """Fills a form field in the specified browser.

    Args:
        browser_id (str): The ID of the browser to interact with.
        selector (str): The CSS selector of the form field.
        value (str): The value to enter into the form field.

    Returns:
        str: A message indicating success or failure.
    """
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        ).send_keys(value)
        return f"Successfully filled form field '{selector}' in browser '{browser_id}'."
    except TimeoutException:
        raise Exception(f"Timeout: Element with selector '{selector}' not found in browser '{browser_id}'.")
    except Exception as e:
        raise Exception(f"Failed to fill form field '{selector}' in browser '{browser_id}': {e}")

def close_browser(browser_id: str) -> str:
    """Closes the specified browser window and removes it from the list."""
    if browser_id not in browsers:
        return f"Browser with ID '{browser_id}' not found or already closed."
    try:
        driver = browsers.pop(browser_id)
        driver.quit()
        return f"Browser {browser_id} closed successfully."
    except Exception as e:
        if browser_id in browsers:
            browsers.pop(browser_id)
        raise Exception(f"Failed to close browser {browser_id}: {e}")

def submit_form(browser_id: str, selector: str) -> str:
    """Submits a form by pressing Enter on the specified element.

    Args:
        browser_id (str): The ID of the browser to interact with.
        selector (str): The CSS selector of the element to press Enter on.

    Returns:
        str: A message indicating success or failure.
    """
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        ).send_keys(Keys.ENTER)
        return f"Successfully submitted form using element '{selector}' in browser '{browser_id}'."
    except TimeoutException:
        raise Exception(f"Timeout: Element with selector '{selector}' not found in browser '{browser_id}'.")
    except Exception as e:
        raise Exception(f"Failed to submit form using element '{selector}' in browser '{browser_id}': {e}")