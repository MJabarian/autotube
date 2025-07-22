#!/usr/bin/env python3
"""
Debug script to see what's actually on the Google Trends page
"""

import requests
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_google_trends_page():
    """Debug the Google Trends realtime page to see its structure."""
    
    print("🔍 DEBUGGING GOOGLE TRENDS PAGE")
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
    
    url = "https://trends.google.com/trends/trendingsearches/realtime?geo=US"
    
    try:
        print(f"🔍 Fetching: {url}")
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"📏 Content Length: {len(response.content)} bytes")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n🔍 PAGE STRUCTURE ANALYSIS:")
        print("=" * 30)
        
        # Look for tables
        tables = soup.find_all('table')
        print(f"📊 Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            print(f"\n📊 Table {i+1}:")
            rows = table.find_all('tr')
            print(f"   Rows: {len(rows)}")
            
            if rows:
                # Show first few rows
                for j, row in enumerate(rows[:5]):
                    cells = row.find_all(['td', 'th'])
                    cell_texts = [cell.get_text().strip() for cell in cells]
                    print(f"   Row {j+1}: {cell_texts}")
        
        # Look for specific elements
        print(f"\n🔍 ELEMENT SEARCH:")
        print("=" * 20)
        
        selectors_to_test = [
            'table tr td:first-child',
            '.trending-item',
            '[data-topic]',
            '.trending-story-title',
            '.story-title',
            'a[href*="/trends/explore"]',
            'table',
            'tr',
            'td',
            'th'
        ]
        
        for selector in selectors_to_test:
            elements = soup.select(selector)
            if elements:
                print(f"✅ {selector}: {len(elements)} elements found")
                # Show first few elements
                for i, elem in enumerate(elements[:3]):
                    text = elem.get_text().strip()
                    if text:
                        print(f"   {i+1}. {text[:50]}...")
            else:
                print(f"❌ {selector}: No elements found")
        
        # Look for any text that might be trending topics
        print(f"\n🔍 TEXT ANALYSIS:")
        print("=" * 20)
        
        # Get all text and look for potential trending topics
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        
        # Look for lines that might be trending topics (not too long, not too short)
        potential_topics = []
        for line in lines:
            if 3 < len(line) < 50 and not line.startswith('http') and not line.startswith('Search'):
                # Check if it looks like a trending topic
                if any(word in line.lower() for word in ['trump', 'biden', 'nba', 'nfl', 'mlb', 'news', 'breaking']):
                    potential_topics.append(line)
        
        print(f"🎯 Potential trending topics found: {len(potential_topics)}")
        for i, topic in enumerate(potential_topics[:10]):
            print(f"   {i+1}. {topic}")
        
        # Save the HTML for manual inspection
        with open('google_trends_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 Saved HTML to: google_trends_debug.html")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_google_trends_page() 