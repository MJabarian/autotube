#!/usr/bin/env python3
"""
Test script to find working Google Trends URLs
"""

import requests
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_google_trends_urls():
    """Test various Google Trends URLs to find working ones."""
    
    print("🔍 TESTING GOOGLE TRENDS URLS")
    print("=" * 50)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Test various Google Trends URLs
    urls_to_test = [
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
        "https://trends.google.com/trends/trendingsearches/daily?geo=US",
        "https://trends.google.com/trends/trendingsearches/daily",
        "https://trends.google.com/trends/trendingsearches/realtime?geo=US",
        "https://trends.google.com/trends/trendingsearches/realtime",
        "https://trends.google.com/trends/explore?geo=US",
        "https://trends.google.com/trends/",
        "https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=-300&geo=US&ns=15",
        "https://trends.google.com/trends/api/trendingsearches/daily?hl=en-US&tz=-300&geo=US&ns=15"
    ]
    
    working_urls = []
    
    for url in urls_to_test:
        print(f"\n🔍 Testing: {url}")
        try:
            response = session.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                content_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
                print(f"   Preview: {content_preview}")
                working_urls.append(url)
            else:
                print(f"   Error: {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    print(f"\n✅ WORKING URLS ({len(working_urls)}):")
    for url in working_urls:
        print(f"   - {url}")
    
    return working_urls

if __name__ == "__main__":
    test_google_trends_urls() 