#!/usr/bin/env python3
"""
Debug script for Selenium Google Trends scraping
"""

import sys
from pathlib import Path
import time

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_selenium_google_trends():
    """Debug Selenium Google Trends scraping."""
    
    print("🔍 DEBUGGING SELENIUM GOOGLE TRENDS")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # Navigate to Google Trends
            url = "https://trends.google.com/trending?geo=US&sort=search-volume"
            print(f"🔍 Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            time.sleep(10)  # Longer wait
            
            # Get page title
            title = driver.title
            print(f"📄 Page title: {title}")
            
            # Try different selectors
            selectors_to_try = [
                "table tr td:first-child",
                "div[role='row'] div[role='cell']:first-child",
                ".trending-item",
                "[data-topic]",
                ".trending-story-title",
                ".story-title",
                "a[href*='/trends/explore']",
                "table tr",
                "div[role='row']",
                "td",
                "th"
            ]
            
            wait = WebDriverWait(driver, 10)
            
            for selector in selectors_to_try:
                try:
                    print(f"\n🔍 Trying selector: {selector}")
                    elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                    
                    if elements:
                        print(f"✅ Found {len(elements)} elements")
                        
                        # Show first few elements
                        for i, element in enumerate(elements[:5]):
                            try:
                                text = element.text.strip()
                                print(f"   {i+1}. Text: '{text}'")
                                
                                # Also try to get HTML
                                html = element.get_attribute('outerHTML')
                                print(f"      HTML: {html[:100]}...")
                                
                            except Exception as e:
                                print(f"   {i+1}. Error getting text: {e}")
                        
                        # Check if any have meaningful text
                        meaningful_elements = []
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 3 and not text.startswith('Search'):
                                meaningful_elements.append(text)
                        
                        if meaningful_elements:
                            print(f"🎯 Found {len(meaningful_elements)} meaningful elements:")
                            for i, text in enumerate(meaningful_elements[:10]):
                                print(f"   {i+1}. {text}")
                            break
                        else:
                            print("❌ No meaningful text found")
                    
                except Exception as e:
                    print(f"❌ Selector failed: {e}")
                    continue
            
            # Save page source for manual inspection
            page_source = driver.page_source
            with open('selenium_google_trends_debug.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"\n💾 Saved page source to: selenium_google_trends_debug.html")
            
            # Try to find any text that looks like trending topics
            print(f"\n🔍 TEXT ANALYSIS:")
            print("=" * 20)
            
            # Look for patterns in the page source
            import re
            
            # Look for potential trending topics
            potential_patterns = [
                r'<[^>]*>([A-Z][a-zA-Z\s]{3,30})</[^>]*>',
                r'"([A-Z][a-zA-Z\s]{3,30})"',
                r"'([A-Z][a-zA-Z\s]{3,30})'"
            ]
            
            for pattern in potential_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    print(f"🎯 Pattern '{pattern}' found {len(matches)} matches:")
                    for i, match in enumerate(matches[:10]):
                        print(f"   {i+1}. {match}")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_selenium_google_trends() 