from bs4 import BeautifulSoup
from browsing import open_browser, get_page_content, close_browser, browsers
from gemini import generate_text as gemini_generate
import requests
import re
import json
from typing import Dict, List, Any, Optional, Union
import time
from datetime import datetime
import lxml.html
from lxml import etree
import csv
import os
from urllib.parse import urljoin, urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from task_data_manager import task_manager

def scrape_website_comprehensive(url: str, scrape_type: str = 'all', max_depth: int = 1, browser_id: str = None) -> str:
    """Comprehensive website scraping with intelligent data extraction.
    
    Args:
        url: The URL to scrape
        scrape_type: Type of scraping ('all', 'text', 'links', 'images', 'tables', 'forms', 'structured')
        max_depth: Maximum depth for crawling (1 = current page only)
        browser_id: Optional browser ID (automatically provided by agent loop)
    
    Returns:
        str: JSON string with comprehensive scraped data
    """
    import json
    
    def extract_all_links(soup, base_url):
        """Extract all links from the page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            links.append({
                'text': link.get_text(strip=True),
                'url': absolute_url,
                'title': link.get('title', ''),
                'target': link.get('target', '')
            })
        return links
    
    def extract_all_images(soup, base_url):
        """Extract all images from the page"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                })
        return images
    
    def extract_all_tables(soup):
        """Extract all tables from the page"""
        tables = []
        for i, table in enumerate(soup.find_all('table')):
            table_data = []
            headers = []
            
            # Extract headers
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Extract rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                row_data = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if row_data:
                    table_data.append(row_data)
            
            tables.append({
                'table_id': i + 1,
                'headers': headers,
                'data': table_data,
                'row_count': len(table_data),
                'column_count': len(headers)
            })
        return tables
    
    def extract_all_forms(soup):
        """Extract all forms from the page"""
        forms = []
        for i, form in enumerate(soup.find_all('form')):
            form_data = {
                'form_id': i + 1,
                'action': form.get('action', ''),
                'method': form.get('method', 'GET'),
                'inputs': []
            }
            
            # Extract form inputs
            for input_elem in form.find_all(['input', 'select', 'textarea']):
                input_data = {
                    'type': input_elem.get('type', input_elem.name),
                    'name': input_elem.get('name', ''),
                    'id': input_elem.get('id', ''),
                    'placeholder': input_elem.get('placeholder', ''),
                    'required': input_elem.has_attr('required'),
                    'value': input_elem.get('value', '')
                }
                form_data['inputs'].append(input_data)
            
            forms.append(form_data)
        return forms
    
    def extract_structured_data(soup):
        """Extract structured data (JSON-LD, microdata, etc.)"""
        structured_data = []
        
        # JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append({
                    'type': 'json-ld',
                    'data': data
                })
            except:
                pass
        
        # Meta tags
        meta_data = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('itemprop')
            content = meta.get('content')
            if name and content:
                meta_data[name] = content
        
        if meta_data:
            structured_data.append({
                'type': 'meta_tags',
                'data': meta_data
            })
        
        return structured_data
    
    def extract_text_content(soup):
        """Extract and organize text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text(strip=True),
                    'id': heading.get('id', '')
                })
        
        # Extract paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        
        # Extract lists
        lists = []
        for ul in soup.find_all(['ul', 'ol']):
            list_items = [li.get_text(strip=True) for li in ul.find_all('li')]
            lists.append({
                'type': ul.name,
                'items': list_items
            })
        
        return {
            'title': soup.title.string if soup.title else '',
            'headings': headings,
            'paragraphs': paragraphs,
            'lists': lists,
            'full_text': soup.get_text(separator=' ', strip=True)
        }
    
    try:
        # Open browser and navigate to URL
        if not browser_id:
            browser_result = open_browser(url)
            # Extract browser ID
            if "browser_" in browser_result:
                browser_id = browser_result.split("browser_")[1].split(".")[0]
                browser_id = f"browser_{browser_id}"
            else:
                return json.dumps({
                    "success": False,
                    "error": "Failed to open browser",
                    "url": url
                }, indent=2)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get page content
        content = get_page_content(browser_id)
        
        if not content:
            close_browser(browser_id)
            return json.dumps({
                "success": False,
                "error": "Failed to get page content",
                "url": url
            }, indent=2)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Initialize result structure
        result = {
            "success": True,
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "scrape_type": scrape_type,
            "data": {}
        }
        
        # Extract data based on scrape_type
        if scrape_type in ['all', 'text']:
            result['data']['text_content'] = extract_text_content(soup)
        
        if scrape_type in ['all', 'links']:
            result['data']['links'] = extract_all_links(soup, url)
        
        if scrape_type in ['all', 'images']:
            result['data']['images'] = extract_all_images(soup, url)
        
        if scrape_type in ['all', 'tables']:
            result['data']['tables'] = extract_all_tables(soup)
        
        if scrape_type in ['all', 'forms']:
            result['data']['forms'] = extract_all_forms(soup)
        
        if scrape_type in ['all', 'structured']:
            result['data']['structured_data'] = extract_structured_data(soup)
        
        # Add page statistics
        result['statistics'] = {
            'total_links': len(soup.find_all('a')),
            'total_images': len(soup.find_all('img')),
            'total_tables': len(soup.find_all('table')),
            'total_forms': len(soup.find_all('form')),
            'total_headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'total_paragraphs': len(soup.find_all('p')),
            'page_size_chars': len(content),
            'word_count': len(soup.get_text().split())
        }
        
        # Save successful scraping result to database
        try:
            task_id = task_manager.save_task_result(
                task_type='web_scraping',
                result_data=result,
                task_description=f'Comprehensive scraping of {url}',
                url=url,
                metadata={
                    'scrape_type': scrape_type,
                    'max_depth': max_depth,
                    'browser_used': browser_id,
                    'statistics': result.get('statistics', {})
                }
            )
            
            # Save detailed scraping data
            task_manager.save_scraping_result(task_id, result)
            
            # Add task_id to result for reference
            result['task_id'] = task_id
            result['saved_to_database'] = True
            
        except Exception as save_error:
            # Don't fail the scraping if saving fails
            result['save_error'] = str(save_error)
            result['saved_to_database'] = False
        
        # Close browser
        close_browser(browser_id)
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        if browser_id:
            try:
                close_browser(browser_id)
            except:
                pass
        
        return json.dumps({
            "success": False,
            "error": f"Error scraping website: {str(e)}",
            "url": url
        }, indent=2)

def scrape_and_analyze(url: str, analysis: str = 'summarize') -> str:
    """Legacy function - kept for backward compatibility"""
    try:
        browser_id = open_browser(url)
        content = get_page_content(browser_id)
        close_browser(browser_id)
        soup = BeautifulSoup(content, 'html.parser')
        clean_text = soup.get_text(separator=' ', strip=True)
        if analysis == 'summarize':
            prompt = f"Summarize the following content: {clean_text[:2000]}"
            return gemini_generate(prompt)
        elif analysis == 'extract_data':
            prompt = f"Extract key data points from: {clean_text[:2000]}"
            return gemini_generate(prompt)
        return "Unsupported analysis type."
    except Exception as e:
        return f"Error scraping and analyzing: {e}"