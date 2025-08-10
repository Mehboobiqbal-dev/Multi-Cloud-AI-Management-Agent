#!/usr/bin/env python3
"""
Simple TempMail Account Creation Script
This script will create a TempMail account by visiting the site and extracting the auto-generated email.
"""

import time
import re
from browsing import open_browser, close_browser
from tools import get_page_content

def create_tempmail_account():
    """Create a TempMail account by extracting auto-generated email."""
    print("\n=== Starting TempMail Account Creation ===")
    
    # List of TempMail sites to try
    tempmail_sites = [
        "https://temp-mail.org",
        "https://10minutemail.com",
        "https://tempmail.email",
        "https://guerrillamail.com"
    ]
    
    for site in tempmail_sites:
        print(f"\nTrying {site}...")
        browser_id = None
        
        try:
            # Step 1: Open browser
            print(f"Step 1: Opening browser for {site}...")
            result = open_browser(site)
            print(f"Browser result: {result}")
            
            if "Error" in result:
                print(f"❌ Failed to open browser for {site}: {result}")
                continue
            
            # Extract browser ID
            browser_id = "browser_0"  # Default
            if "browser_" in result:
                match = re.search(r'browser_([0-9]+)', result)
                if match:
                    browser_id = f"browser_{match.group(1)}"
            
            print(f"✅ Browser opened with ID: {browser_id}")
            
            # Step 2: Wait for page to load
            print("Step 2: Waiting for page to load...")
            time.sleep(5)  # Give more time for page to fully load
            
            # Step 3: Get page content
            print("Step 3: Getting page content...")
            content_result = get_page_content(browser_id)
            print(f"Page content length: {len(content_result) if content_result else 0}")
            
            if not content_result:
                print(f"❌ No content received from {site}")
                continue
            
            # Step 4: Look for email addresses in the content
            print("Step 4: Looking for email addresses...")
            
            # Multiple regex patterns to catch different email formats
            email_patterns = [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Standard email
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Word boundary
                r'[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}',  # More strict
            ]
            
            found_emails = []
            for pattern in email_patterns:
                emails = re.findall(pattern, content_result)
                found_emails.extend(emails)
            
            # Remove duplicates and filter out common non-temp emails
            unique_emails = list(set(found_emails))
            temp_emails = []
            
            # Filter to keep only temporary email addresses
            exclude_domains = ['example.com', 'test.com', 'localhost', 'gmail.com', 'yahoo.com', 'hotmail.com']
            for email in unique_emails:
                domain = email.split('@')[1].lower() if '@' in email else ''
                if domain and not any(excl in domain for excl in exclude_domains):
                    temp_emails.append(email)
            
            print(f"Found {len(temp_emails)} potential temporary emails: {temp_emails}")
            
            if temp_emails:
                email = temp_emails[0]  # Use the first valid temp email
                print(f"\n🎉 SUCCESS: Temporary email created!")
                print(f"✅ Email: {email}")
                print(f"✅ Site: {site}")
                print(f"✅ Browser ID: {browser_id}")
                
                # Close browser
                close_browser(browser_id)
                return True, email, site
            else:
                print(f"❌ No valid temporary email found on {site}")
                
                # Print a sample of the content for debugging
                sample_content = content_result[:500] if content_result else "No content"
                print(f"Content sample: {sample_content}...")
                
        except Exception as e:
            print(f"❌ Error with {site}: {e}")
        
        finally:
            # Always close browser
            if browser_id:
                try:
                    close_browser(browser_id)
                except:
                    pass
    
    print("\n❌ Failed to create temporary email account from any site")
    return False, None, None

if __name__ == "__main__":
    success, email, site = create_tempmail_account()
    if success:
        print(f"\n🎉 FINAL SUCCESS: Temporary email account created!")
        print(f"📧 Email: {email}")
        print(f"🌐 Site: {site}")
        print("\n✅ Task completed successfully!")
    else:
        print("\n❌ FAILED: Could not create temporary email account from any site")