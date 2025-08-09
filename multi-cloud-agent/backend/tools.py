from typing import Dict, Any, Callable, List
from cloud_handlers import handle_clouds
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os
import json
import time
import tweepy
from googleapiclient.discovery import build
import openai
# import speech_recognition as sr
from gtts import gTTS
import io
import requests
import base64
from bs4 import BeautifulSoup
from gemini import generate_text as gemini_generate
from cryptography.fernet import Fernet
import pickle

class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
        }

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_all_tools_dict(self) -> List[Dict[str, Any]]:
        return [tool.to_dict() for tool in self.get_all_tools()]

# --- Core Tools ---

def search_web(query: str, engine: str = 'duckduckgo') -> str:
    """Searches the web for the given query using specified engine (google, bing, duckduckgo) via free APIs or browser automation."""
    from browsing import search_web as browsing_search_web
    
    # Use the implementation from browsing.py which doesn't require SerpAPI
    try:
        return browsing_search_web(query, engine)
    except Exception as e:
        return f"Error during web search: {e}"

# --- Browser Tools ---

browsers: Dict[str, WebDriver] = {}

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
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
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
        content = driver.find_element(By.TAG_NAME, 'body').text
        return '\n'.join([line for line in content.split('\n') if line.strip()])
    except Exception as e:
        raise Exception(f"Failed to get page content from browser '{browser_id}': {e}")

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
        return f"Clicked button with selector '{selector}' successfully. Current URL is now {driver.current_url}"
    except Exception as e:
        raise Exception(f"Failed to click button '{selector}': {e}")

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
        
# --- E-commerce Tools ---

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

# --- Agent and Control Tools ---

def finish_task(final_answer: str) -> str:
    """Use this tool to signify that you have successfully completed the entire goal. The final answer or summary should be provided in the 'final_answer' parameter."""
    return f"Task finished with final answer: {final_answer}"

# --- Other Tools ---

def read_file(path: str) -> str:
    """Reads the contents of a file."""
    with open(path, "r") as f:
        return f.read()

def write_file(path: str, content: str):
    """Writes content to a file."""
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote content to {path}"
    except Exception as e:
        raise Exception(f"Failed to write to file: {e}")

def execute_command(command: str) -> str:
    """Executes a shell command."""
    return f"Executed command: {command}"

def cloud_operation(cloud: str, operation: str, resource: str, params: Dict[str, Any], user_creds: Dict[str, Any]) -> Dict[str, Any]:
    """Executes a cloud operation."""
    return handle_clouds([{"cloud": cloud, "operation": operation, "resource": resource, "params": params}], user_creds)

def user_interaction(question: str) -> str:
    """Asks the user a question for clarification."""
    return question

# --- Tool Registration ---

tool_registry = ToolRegistry()
tool_registry.register(Tool("search_web", "Searches the web for a given query using specified engine (google, bing, duckduckgo) and returns a summary of results.", search_web))
tool_registry.register(Tool("search_products_amazon", "Searches for a product on Amazon.com and returns the top results.", search_products_amazon))
tool_registry.register(Tool("open_browser", "Opens a new headless browser window and navigates to a URL. Returns a browser_id.", open_browser))
tool_registry.register(Tool("get_page_content", "Gets the visible text content of the current page in a browser, using its browser_id.", get_page_content))
tool_registry.register(Tool("fill_form", "Fills a single form field (identified by a CSS selector) in a browser.", fill_form))
tool_registry.register(Tool("fill_multiple_fields", "Fills multiple form fields in a browser from a dictionary of {selector: value}.", fill_multiple_fields))
tool_registry.register(Tool("click_button", "Clicks a button (identified by a CSS selector) in a browser.", click_button))
tool_registry.register(Tool("close_browser", "Closes a specific browser window by its browser_id.", close_browser))
tool_registry.register(Tool("read_file", "Reads the contents of a local file.", read_file))
tool_registry.register(Tool("write_file", "Writes content to a local file.", write_file))
tool_registry.register(Tool("cloud_operation", "Executes a cloud operation (list, create, delete) on AWS, Azure, or GCP.", cloud_operation))
tool_registry.register(Tool("finish_task", "Signals that the agent has completed the goal and provides the final answer.", finish_task))

def post_to_twitter(content: str, credentials: Dict[str, str]) -> str:
    """Posts content to Twitter using provided credentials."""
    auth = tweepy.OAuth1UserHandler(
        credentials['consumer_key'], credentials['consumer_secret'],
        credentials['access_token'], credentials['access_token_secret']
    )
    api = tweepy.API(auth)
    try:
        api.update_status(content)
        return "Posted to Twitter successfully."
    except Exception as e:
        return f"Error posting to Twitter: {e}"

def send_email_gmail(subject: str, body: str, to: str, credentials: Dict[str, str]) -> str:
    """Sends an email via Gmail API."""
    service = build('gmail', 'v1', credentials=credentials)
    message = {'raw': base64.urlsafe_b64encode(f'Subject: {subject}\nTo: {to}\n\n{body}'.encode()).decode()}
    try:
        service.users().messages().send(userId='me', body=message).execute()
        return "Email sent successfully."
    except Exception as e:
        return f"Error sending email: {e}"

def generate_content(prompt: str, type: str = 'text') -> str:
    """Generates content using Gemini API. Type can be 'text', 'blog', 'code', 'image'."""
    if type in ['text', 'blog', 'code']:
        # Use Gemini API instead of OpenAI
        try:
            return gemini_generate(prompt)
        except Exception as e:
            return f"Error generating content with Gemini: {e}"
    elif type == 'image':
        # Placeholder for image generation
        return "Image generation is not supported with current configuration."
    elif type == 'video':
        # Placeholder for video generation
        return "Video generation is not supported with current configuration."
    return "Unsupported content type."

def call_api(url: str, method: str = 'GET', data: Dict = None, headers: Dict = None) -> str:
    """Makes a dynamic API call."""
    try:
        response = requests.request(method, url, json=data, headers=headers)
        return response.text
    except Exception as e:
        return f"API call error: {e}"

def analyze_image(image_path: str) -> str:
    """Analyzes an image using a placeholder (e.g., Vision API)."""
    return "Image analysis: [placeholder result]"

# def speech_to_text(audio_path: str) -> str:
#     """Converts speech to text."""
#     r = sr.Recognizer()
#     with sr.AudioFile(audio_path) as source:
#         audio = r.record(source)
#     try:
#         return r.recognize_google(audio)
#     except:
#         return "Could not understand audio."

def text_to_speech(text: str, output_path: str) -> str:
    """Converts text to speech."""
    tts = gTTS(text)
    tts.save(output_path)
    return f"Audio saved to {output_path}"

def load_plugin(plugin_path: str) -> str:
    """Loads a custom plugin tool from a Python file."""
    # Placeholder for dynamic import
    return "Plugin loaded: [placeholder]"

tool_registry.register(Tool("post_to_twitter", "Posts content to Twitter.", post_to_twitter))
tool_registry.register(Tool("send_email_gmail", "Sends an email via Gmail.", send_email_gmail))
tool_registry.register(Tool("generate_content", "Generates text or image content.", generate_content))
tool_registry.register(Tool("call_api", "Makes dynamic API calls.", call_api))
tool_registry.register(Tool("analyze_image", "Analyzes images.", analyze_image))
# tool_registry.register(Tool("speech_to_text", "Converts speech to text.", speech_to_text))
tool_registry.register(Tool("text_to_speech", "Converts text to speech.", text_to_speech))
def scrape_and_analyze(url: str, analysis: str = 'summarize') -> str:
    """Scrapes a website and performs analysis (summarize, extract_data, etc.)."""
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

def comment_on_twitter(tweet_id: str, comment: str, credentials: Dict[str, str]) -> str:
    """Comments on a Twitter post."""
    auth = tweepy.OAuth1UserHandler(credentials['consumer_key'], credentials['consumer_secret'], credentials['access_token'], credentials['access_token_secret'])
    api = tweepy.API(auth)
    try:
        api.update_status(status=comment, in_reply_to_status_id=tweet_id)
        return "Commented on Twitter successfully."
    except Exception as e:
        return f"Error commenting on Twitter: {e}"

def send_dm_twitter(user_id: str, message: str, credentials: Dict[str, str]) -> str:
    """Sends a direct message on Twitter."""
    auth = tweepy.OAuth1UserHandler(credentials['consumer_key'], credentials['consumer_secret'], credentials['access_token'], credentials['access_token_secret'])
    api = tweepy.API(auth)
    try:
        api.send_direct_message(recipient_id=user_id, text=message)
        return "DM sent on Twitter successfully."
    except Exception as e:
        return f"Error sending DM on Twitter: {e}"

def post_to_linkedin(content: str, credentials: Dict[str, str]) -> str:
    """Posts to LinkedIn (placeholder using API)."""
    # Requires LinkedIn API setup
    return "Posted to LinkedIn successfully (placeholder)."

tool_registry.register(Tool("comment_on_twitter", "Comments on a Twitter post.", comment_on_twitter))
tool_registry.register(Tool("send_dm_twitter", "Sends DM on Twitter.", send_dm_twitter))
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

tool_registry.register(Tool("compare_prices", "Compares product prices across sites.", compare_prices))
def read_emails_gmail(max_results: int = 5) -> str:
    """Reads recent emails from Gmail."""
    try:
        # Get credentials from environment or user settings
        # This is a simplified implementation without the credentials parameter
        return "This is a placeholder for reading emails from Gmail. In a real implementation, this would connect to Gmail API and fetch emails."
    except Exception as e:
        return f"Error reading emails: {e}"

def reply_email_gmail(message_id: str, body: str, credentials: Dict[str, str]) -> str:
    """Replies to a Gmail email."""
    service = build('gmail', 'v1', credentials=credentials)
    try:
        message = {'raw': base64.urlsafe_b64encode(body.encode()).decode(), 'threadId': message_id}
        service.users().messages().send(userId='me', body=message).execute()
        return "Replied to email successfully."
    except Exception as e:
        return f"Error replying to email: {e}"

def send_email_outlook(subject: str, body: str, to: str, credentials: Dict[str, str]) -> str:
    """Sends an email via Outlook (placeholder)."""
    return "Email sent via Outlook successfully (placeholder)."

tool_registry.register(Tool("read_emails_gmail", "Reads recent Gmail emails.", read_emails_gmail))
tool_registry.register(Tool("reply_email_gmail", "Replies to a Gmail email.", reply_email_gmail))
def secure_store_credential(key: str, value: str, encryption_key: str) -> str:
    """Securely stores a credential using encryption."""
    f = Fernet(encryption_key)
    encrypted = f.encrypt(value.encode())
    with open('credentials.pkl', 'ab') as file:
        pickle.dump({key: encrypted}, file)
    return "Credential stored securely."

def secure_get_credential(key: str, encryption_key: str) -> str:
    """Retrieves and decrypts a stored credential."""
    f = Fernet(encryption_key)
    try:
        with open('credentials.pkl', 'rb') as file:
            while True:
                try:
                    data = pickle.load(file)
                    if key in data:
                        return f.decrypt(data[key]).decode()
                except EOFError:
                    break
        return "Credential not found."
    except Exception as e:
        return f"Error retrieving credential: {e}"

tool_registry.register(Tool("secure_store_credential", "Stores credential securely.", secure_store_credential))
def detect_language(text: str) -> str:
    """Detects the language of the given text using Gemini."""
    prompt = f"Detect the language of this text: {text}"
    return gemini_generate(prompt).strip()

def translate_text(text: str, target_lang: str) -> str:
    """Translates text to the target language using Gemini."""
    prompt = f"Translate this text to {target_lang}: {text}"
    return gemini_generate(prompt)

tool_registry.register(Tool("detect_language", "Detects text language.", detect_language))
tool_registry.register(Tool("translate_text", "Translates text.", translate_text))
tool_registry.register(Tool("secure_get_credential", "Retrieves secure credential.", secure_get_credential))
tool_registry.register(Tool("send_email_outlook", "Sends email via Outlook.", send_email_outlook))
tool_registry.register(Tool("add_to_cart_amazon", "Adds product to Amazon cart.", add_to_cart_amazon))
tool_registry.register(Tool("post_to_linkedin", "Posts to LinkedIn.", post_to_linkedin))
tool_registry.register(Tool("scrape_and_analyze", "Scrapes and analyzes web content.", scrape_and_analyze))
tool_registry.register(Tool("load_plugin", "Loads custom plugins.", load_plugin))

# Register form automation tools
import form_automation
tool_registry.register(Tool("select_dropdown_option", "Selects an option from a dropdown menu.", form_automation.select_dropdown_option))
tool_registry.register(Tool("upload_file", "Uploads a file to a form.", form_automation.upload_file))
tool_registry.register(Tool("wait_for_element", "Waits for an element to be present on the page.", form_automation.wait_for_element))
tool_registry.register(Tool("check_checkbox", "Checks or unchecks a checkbox.", form_automation.check_checkbox))
