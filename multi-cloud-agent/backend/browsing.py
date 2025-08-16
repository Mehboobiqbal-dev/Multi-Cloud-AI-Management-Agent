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
from core.config import settings

browsers: Dict[str, WebDriver] = {}


def search_web(query: str, engine: str = 'duckduckgo') -> str:
    """Searches the web for the given query using DuckDuckGo Instant Answer API or headless browser scraping.
    Enhanced with retry logic and multiple engine fallback.
    """
    
    if engine not in ['duckduckgo', 'google']:
        engine = 'duckduckgo'
    
    # Try the specified engine first, then fall back to the other if needed
    engines_to_try = [engine]
    if engine == 'duckduckgo':
        engines_to_try.append('google')
    elif engine == 'google':
        engines_to_try.append('duckduckgo')
    
    errors = []
    
    for current_engine in engines_to_try:
        max_retries = getattr(settings, "MAX_RETRIES", 3)
        retry_delay = float(getattr(settings, "INITIAL_RETRY_DELAY", 2.0))  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                if current_engine == 'google':
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
                            if re.search(r"captcha|unusual traffic|verify you are human|robot", content, re.IGNORECASE):
                                errors.append("Google results may be blocked by CAPTCHA or traffic protection.")
                                break  # Try next engine
                            return f"Google Search Results for '{query}':\n\n{content}"
                        else:
                            errors.append("Could not open browser for Google search.")
                            break  # Try next engine
                    except Exception as e:
                        error_msg = str(e)
                        errors.append(f"Error during Google search: {error_msg}")
                        
                        # Check if we should retry with this engine
                        if attempt < max_retries - 1:
                            # Check if it's a connection-related error
                            is_connection_error = any(msg in error_msg.lower() for msg in [
                                "failed to connect", "connection refused", "timeout", 
                                "socket", "network", "unreachable", "chrome not reachable"
                            ])
                            
                            if is_connection_error:
                                time.sleep(retry_delay)
                                retry_delay = min(retry_delay * 2, float(getattr(settings, "MAX_RETRY_DELAY", 60.0)))  # Exponential backoff with cap
                                continue
                        # If not a retriable error or max retries reached, try next engine
                        break
                    finally:
                        if browser_id:
                            try:
                                close_browser(browser_id)
                            except Exception:
                                pass

                # Try DuckDuckGo Instant Answer API
                elif current_engine == 'duckduckgo':
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
                            errors.append("No direct answer found from DuckDuckGo.")
                            break  # Try next engine
                    except Exception as e:
                        error_msg = str(e)
                        errors.append(f"Error during DuckDuckGo API search: {error_msg}")
                        
                        # Check if we should retry with this engine
                        if attempt < max_retries - 1:
                            # Check if it's a connection-related error
                            is_connection_error = any(msg in error_msg.lower() for msg in [
                                "failed to connect", "connection refused", "timeout", 
                                "socket", "network", "unreachable"
                            ])
                            
                            if is_connection_error:
                                time.sleep(retry_delay)
                                retry_delay = min(retry_delay * 2, float(getattr(settings, "MAX_RETRY_DELAY", 60.0)))  # Exponential backoff with cap
                                continue
                        # If not a retriable error or max retries reached, try next engine
                        break
            except Exception as e:
                errors.append(f"Unexpected error with {current_engine}: {str(e)}")
                break  # Try next engine
    
    # If we get here, all engines failed
    error_summary = "\n".join(errors)
    return f"All search attempts failed. Details:\n{error_summary}\n\nPlease try again later or with a different query."


def open_browser(url: str, max_retries: int = None, retry_delay: float = None) -> str:
    """Opens a new headless Chrome browser window and navigates to the specified URL.
    
    Args:
        url (str): The URL to navigate to
        max_retries (int): Maximum number of retry attempts (defaults to settings)
        retry_delay (float): Initial delay between retries in seconds (defaults to settings)
    """
    browser_id = f"browser_{len(browsers)}"
    
    # Sanitize and normalize the URL input to prevent crashes due to invalid characters (e.g., backticks)
    if url:
        try:
            match = re.search(r"(https?://[^\s`'\"]+)", url)
            if match:
                url = match.group(1)
            else:
                url = url.strip().strip("`'\"")
        except Exception:
            url = str(url).strip().strip("`'\"")

    # Use centralized settings if not provided
    if max_retries is None:
        max_retries = getattr(settings, "MAX_RETRIES", 3)
    if retry_delay is None:
        retry_delay = float(getattr(settings, "INITIAL_RETRY_DELAY", 2.0))
    
    for attempt in range(max_retries):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")
            # Comprehensive GPU and WebGL disabling
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-gpu-sandbox")
            # NOTE: Do NOT disable software rasterizer; we want SwiftShader for headless stability
            # options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-gpu-rasterization")
            options.add_argument("--disable-gpu-memory-buffer-compositor-resources")
            options.add_argument("--disable-gpu-memory-buffer-video-frames")
            options.add_argument("--disable-accelerated-2d-canvas")
            options.add_argument("--disable-accelerated-jpeg-decoding")
            options.add_argument("--disable-accelerated-mjpeg-decode")
            options.add_argument("--disable-accelerated-video-decode")
            options.add_argument("--disable-accelerated-video-encode")
            options.add_argument("--disable-webgl")
            options.add_argument("--disable-webgl2")
            options.add_argument("--disable-3d-apis")
            options.add_argument("--disable-webgl-image-chromium")
            options.add_argument("--disable-webgl-draft-extensions")
            options.add_argument("--use-gl=swiftshader")
            options.add_argument("--enable-unsafe-swiftshader")
            # Additional GPU context fixes for virtualization
            options.add_argument("--disable-gpu-process-crash-limit")
            options.add_argument("--disable-gpu-process-for-dx12-vulkan-info-collection")
            options.add_argument("--disable-vulkan")
            options.add_argument("--disable-vulkan-fallback-to-gl-for-testing")
            options.add_argument("--disable-features=VizDisplayCompositor,VizHitTestSurfaceLayer")
            options.add_argument("--disable-gl-drawing-for-tests")
            options.add_argument("--disable-gl-error-limit")
            options.add_argument("--disable-canvas-aa")
            options.add_argument("--disable-2d-canvas-clip-aa")
            options.add_argument("--disable-gl-extensions")
            options.add_argument("--use-angle=swiftshader")
            options.add_argument("--ignore-gpu-blocklist")
            options.add_argument("--disable-gpu-driver-bug-workarounds")
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
            options.add_argument("--page-load-strategy=eager")  # Interactive instead of complete
            options.add_argument("--dns-prefetch-disable")  # Network optimization
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)  # 30 seconds timeout
            driver.set_script_timeout(30)
            
            # Test with a simple page load first
            driver.get("about:blank")
            
            # Now navigate to the requested URL
            driver.get(url)
            browsers[browser_id] = driver
            return f"Browser opened with ID: {browser_id}. Navigated to {url}. You can now read its content or interact with it."
            
        except Exception as e:
            error_msg = str(e)
            # Check if we should retry
            if attempt < max_retries - 1:
                # Check if it's a connection-related error
                is_connection_error = any(msg in error_msg.lower() for msg in [
                    "failed to connect", "connection refused", "timeout",
                    "socket", "network", "unreachable", "chrome not reachable",
                    "connection aborted", "connection reset", "err_connection_reset", "err_connection_closed"
                ])
                
                if is_connection_error:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, float(getattr(settings, "MAX_RETRY_DELAY", 60.0)))  # Exponential backoff with cap
                    continue
            
            # If we've exhausted retries or it's not a connection error
            raise Exception(f"Failed to open browser after {attempt+1} attempts: {e}")


def get_page_content(browser_id: str) -> str:
    """Gets the full HTML content of the current page in the specified browser."""
    if browser_id not in browsers:
        raise Exception(f"Browser with ID '{browser_id}' not found.")
    try:
        driver = browsers[browser_id]
        # Prefer executing JS to get full HTML for accurate parsing of links, images, tables, etc.
        try:
            html = driver.execute_script(
                "return document.documentElement ? document.documentElement.outerHTML : (document.body ? document.body.outerHTML : '');"
            )
        except Exception:
            html = driver.page_source
        return html
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