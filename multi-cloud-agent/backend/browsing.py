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
                # Wait for the search box to be present
                driver = browsers[browser_id]
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='q']")))
                except TimeoutException:
                    pass  # continue; sometimes input is available without wait
                fill_form(browser_id, "textarea[name='q']", query)
                submit_form(browser_id, "textarea[name='q']")
                time.sleep(1)  # Reduced wait for faster results
                content = get_page_content(browser_id)
                # Simple CAPTCHA awareness
                if re.search(r"captcha|unusual traffic|verify you are human", content, re.IGNORECASE):
                    return "Google results may be blocked by CAPTCHA or traffic protection. Try DuckDuckGo engine."
                return f"Google Search Results for '{query}':\n\n{content}"
            else:
                return "Error: Could not open browser for Google search."
        except Exception as e:
            return f"Error during Google search: {e}"
        finally:
            if browser_id:
                try:
                    close_browser(browser_id)
                except Exception:
                    pass

    # Try DuckDuckGo Instant Answer API first (free, no API key required)
    if engine == 'duckduckgo':
        try:
            duckduckgo_url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}
            response = requests.get(duckduckgo_url, timeout=10, headers=headers)
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
            else:
                return "No direct answer found. Try using google engine for broader results."
        except Exception as e:
            return f"Error during DuckDuckGo API search: {e}. Browser-based search is not supported for this engine."


def open_browser(url: str) -> str:
    """Opens a new headless Chrome browser window and navigates to the specified URL."""
    try:
        browser_id = f"browser_{len(browsers)}"
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--mute-audio")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-cloud-import")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--guest")
        options.add_argument("--disable-speech-api")
        # Performance optimizations
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-media-suspend")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-features=BlinkGenPropertyTrees")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=dsp")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-login-animations")
        options.add_argument("--disable-smooth-scrolling")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
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
        # Prefer executing JS to get textContent which is faster in some cases
        try:
            content = driver.execute_script("return document.body ? document.body.innerText : '';")
        except Exception:
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


def fill_multiple_fields(browser_id: str, fields: list) -> str:
    """Fills multiple form fields in the specified browser.

    Args:
        browser_id (str): The ID of the browser to interact with.
        fields (list): A list of dictionaries, each containing 'selector' and 'value' for a field.

    Returns:
        str: A message indicating success or failure for all fields.
    """
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        results = []
        for field in fields:
            selector = field.get('selector')
            value = field.get('value')
            if selector and value:
                fill_form(browser_id, selector, value)
                results.append(f"Filled '{selector}' with '{value}'.")
            else:
                results.append(f"Skipped invalid field: {field}")
        return "\n".join(results)
    except Exception as e:
        raise Exception(f"Failed to fill multiple fields in browser '{browser_id}': {e}")

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