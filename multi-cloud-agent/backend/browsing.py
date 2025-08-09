from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os
import time
from bs4 import BeautifulSoup
import json
from datetime import datetime

browsers: Dict[str, WebDriver] = {}


def search_web(query: str, engine: str = 'duckduckgo') -> str:
    """Searches the web for the given query using DuckDuckGo Instant Answer API or headless browser scraping."""
    
    if engine not in ['google', 'bing', 'duckduckgo']:
        engine = 'duckduckgo'
    
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
            # If API fails, we'll fall back to browser scraping
            pass
    
    # Fallback to headless browser + BeautifulSoup scraping
    try:
        browser_id = open_browser(f"https://www.{engine}.com/search?q={query.replace(' ', '+')}") 
        driver = browsers[browser_id]
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        results = []
        
        if engine == 'google':
            # Extract Google search results
            search_results = soup.select('div.g')
            for result in search_results[:5]:  # Limit to 5 results
                title_elem = result.select_one('h3')
                link_elem = result.select_one('a')
                snippet_elem = result.select_one('div.VwiC3b')
                
                title = title_elem.text if title_elem else 'N/A'
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else 'N/A'
                snippet = snippet_elem.text if snippet_elem else 'N/A'
                
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
        
        elif engine == 'duckduckgo':
            # Extract DuckDuckGo search results
            search_results = soup.select('article')
            for result in search_results[:5]:  # Limit to 5 results
                title_elem = result.select_one('h2')
                link_elem = result.select_one('a.result__a')
                snippet_elem = result.select_one('div.result__snippet')
                
                title = title_elem.text if title_elem else 'N/A'
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else 'N/A'
                snippet = snippet_elem.text if snippet_elem else 'N/A'
                
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
        
        elif engine == 'bing':
            # Extract Bing search results
            search_results = soup.select('li.b_algo')
            for result in search_results[:5]:  # Limit to 5 results
                title_elem = result.select_one('h2')
                link_elem = result.select_one('cite')
                snippet_elem = result.select_one('p')
                
                title = title_elem.text if title_elem else 'N/A'
                link = link_elem.text if link_elem else 'N/A'
                snippet = snippet_elem.text if snippet_elem else 'N/A'
                
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
        
        close_browser(browser_id)
        return "\n".join(results) if results else "No search results found. Try refining your query."
    except Exception as be:
        return f"Error during web search: {be}"

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