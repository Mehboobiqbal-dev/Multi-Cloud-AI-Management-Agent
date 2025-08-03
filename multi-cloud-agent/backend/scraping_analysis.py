from bs4 import BeautifulSoup
from .browsing import open_browser, get_page_content, close_browser
from .gemini import generate_content as gemini_generate

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