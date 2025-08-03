from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os
import time

browsers: Dict[str, WebDriver] = {}

def search_web(query: str, engine: str = 'google') -> str:
    """Searches the web for the given query using specified engine (google, bing, duckduckgo) via SerpApi, with browser fallback."""
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if not serpapi_key:
        return "Error: Web search is not configured. The SERPAPI_KEY environment variable is not set."
    
    if engine not in ['google', 'bing', 'duckduckgo']:
        engine = 'google'
    
    params = {"api_key": serpapi_key, "q": query, "engine": engine}
    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        summary_parts = []
        if "answer_box" in data:
            summary_parts.append(f"Answer Box: {data['answer_box'].get('answer') or data['answer_box'].get('snippet')}")
        if "organic_results" in data and data["organic_results"]:
            summary_parts.append("Organic Results:")
            for r in data["organic_results"][:3]:
                summary_parts.append(f"  - Title: {r.get('title', 'N/A')}\n    Link: {r.get('link', 'N/A')}\n    Snippet: {r.get('snippet', 'N/A')}")
        
        return "\n".join(summary_parts) if summary_parts else "No definitive search results found."
    except requests.exceptions.RequestException as e:
        # Fallback to browser automation
        try:
            browser_id = open_browser(f"https://www.{engine}.com/search?q={query.replace(' ', '+')}")
            content = get_page_content(browser_id)
            close_browser(browser_id)
            return f"API failed, used browser fallback: {content[:500]}..."  # Truncate for brevity
        except Exception as be:
            return f"Error during web search: API failed ({e}), browser fallback also failed ({be})"

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