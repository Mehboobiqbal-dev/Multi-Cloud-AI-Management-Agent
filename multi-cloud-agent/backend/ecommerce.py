from typing import Dict, Any, List, Optional, Union
import requests
from browsing import open_browser, close_browser, browsers
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime
import csv
import os


def search_products_amazon(product_query: str) -> str:
    """Searches for a product on Amazon.com and returns the top 3 results with titles, prices, and links."""
    results = []
    browser_id = ""
    try:
        search_url = f"https://www.amazon.com/s?k={product_query.replace(' ', '+')}"
        browser_id = open_browser(search_url)
        driver = browsers[browser_id]
        
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']")))
        search_results = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
        
        for i, item in enumerate(search_results[:3]):
            title, price, link = "Not found", "Not found", "Not found"
            try:
                title_element = item.find_element(By.CSS_SELECTOR, "h2 a.a-link-normal span.a-text-normal")
                title = title_element.text
                link = title_element.find_element(By.XPATH, "..").get_attribute('href')
            except: pass
            try:
                price_whole = item.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
                price_fraction = item.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
                price = f"${price_whole}.{price_fraction}"
            except: pass
            results.append(f"Result {i+1}:\n  - Title: {title}\n  - Price: {price}\n  - Link: {link}")

        return "\n".join(results) if results else "No products found."
    except TimeoutException:
        return "Timed out waiting for Amazon search results to load. The page might have a CAPTCHA."
    except Exception as e:
        return f"An error occurred while searching Amazon: {e}"
    finally:
        if browser_id in browsers:
            close_browser(browser_id)

def search_products_ebay(product_query: str) -> str:
    """Searches for a product on eBay.com and returns the top 3 results with titles, prices, and links."""
    results = []
    browser_id = ""
    try:
        search_url = f"https://www.ebay.com/sch/i.html?_nkw={product_query.replace(' ', '+')}"
        browser_id = open_browser(search_url)
        driver = browsers[browser_id]
        
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.s-item")))
        search_results = driver.find_elements(By.CSS_SELECTOR, "li.s-item")
        
        for i, item in enumerate(search_results[1:4]):  # Skip first item as it's often a header
            title, price, link = "Not found", "Not found", "Not found"
            try:
                title_element = item.find_element(By.CSS_SELECTOR, "div.s-item__title span")
                title = title_element.text
            except: pass
            try:
                price_element = item.find_element(By.CSS_SELECTOR, "span.s-item__price")
                price = price_element.text
            except: pass
            try:
                link_element = item.find_element(By.CSS_SELECTOR, "a.s-item__link")
                link = link_element.get_attribute('href')
            except: pass
            results.append(f"Result {i+1}:\n  - Title: {title}\n  - Price: {price}\n  - Link: {link}")

        return "\n".join(results) if results else "No products found."
    except TimeoutException:
        return "Timed out waiting for eBay search results to load."
    except Exception as e:
        return f"An error occurred while searching eBay: {e}"
    finally:
        if browser_id:
            close_browser(browser_id)


def search_products_aliexpress(product_query: str) -> str:
    """Searches for a product on AliExpress and returns the top 3 results with titles, prices, and links."""
    results = []
    browser_id = ""
    try:
        search_url = f"https://www.aliexpress.com/wholesale?SearchText={product_query.replace(' ', '+')}"
        browser_id = open_browser(search_url)
        driver = browsers[browser_id]
        
        # AliExpress may take longer to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div._1OUGS")))
        time.sleep(2)  # Additional wait for dynamic content
        
        # Get page source and parse with BeautifulSoup for more reliable extraction
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find product cards
        product_cards = soup.select("div._1OUGS")[:3]
        
        for i, card in enumerate(product_cards):
            title = card.select_one("h1") or card.select_one("a._3t7zg")
            title = title.text.strip() if title else "Not found"
            
            price = card.select_one("div._12A8D") or card.select_one("div.mGXnE")
            price = price.text.strip() if price else "Not found"
            
            link = card.select_one("a")
            link = "https:" + link['href'] if link and 'href' in link.attrs else "Not found"
            
            results.append(f"Result {i+1}:\n  - Title: {title}\n  - Price: {price}\n  - Link: {link}")

        return "\n".join(results) if results else "No products found."
    except TimeoutException:
        return "Timed out waiting for AliExpress search results to load. The site might be blocking automated access."
    except Exception as e:
        return f"An error occurred while searching AliExpress: {e}"
    finally:
        if browser_id:
            close_browser(browser_id)


def compare_prices(product: str) -> str:
    """Compares prices of a product across Amazon, eBay, and AliExpress using direct scraping."""
    results = []
    
    # Amazon search
    amazon_results = search_products_amazon(product)
    results.append(f"Amazon:\n{amazon_results}\n")
    
    # eBay search
    ebay_results = search_products_ebay(product)
    results.append(f"eBay:\n{ebay_results}\n")
    
    # AliExpress search
    aliexpress_results = search_products_aliexpress(product)
    results.append(f"AliExpress:\n{aliexpress_results}\n")
    
    return "\n".join(results)

def add_to_cart_amazon(product_url: str) -> str:
    """Adds a product to Amazon cart using browser automation."""
    try:
        browser_id = open_browser(product_url)
        driver = browsers[browser_id]
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'add-to-cart-button'))).click()
        close_browser(browser_id)
        return "Added to Amazon cart successfully."
    except Exception as e:
        return f"Error adding to cart: {e}"