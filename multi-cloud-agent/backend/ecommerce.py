from typing import Dict, Any
import requests
from .browsing import open_browser, close_browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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

def compare_prices(product: str) -> str:
    """Compares prices of a product across Amazon, eBay, and Walmart using search."""
    results = []
    for site in ['amazon', 'ebay', 'walmart']:
        query = f"site:{site}.com {product}"
        search_result = search_web(query)
        results.append(f"{site.capitalize()}: {search_result[:300]}")
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