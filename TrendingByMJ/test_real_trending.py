"""
Test Real Trending Topics
Actually fetch real trending topics from Google Trends to see what we're getting
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config

def test_real_trending_fetch():
    """Test fetching real trending topics from Google Trends."""
    print("🔍 TESTING REAL TRENDING TOPICS FETCH")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_real_trending")
    
    try:
        from src.trending_fetcher import TrendingFetcher
        
        # Initialize fetcher
        fetcher = TrendingFetcher(logger)
        print("✅ TrendingFetcher initialized")
        
        # Fetch real trending topics
        print("\n🔍 Fetching real trending topics from Google Trends...")
        topics = fetcher.fetch_trending_topics()
        
        if not topics:
            print("❌ No trending topics found!")
            print("This could be due to:")
            print("  - pytrends compatibility issue")
            print("  - Network connectivity")
            print("  - Google Trends API changes")
            return False
        
        print(f"\n✅ Found {len(topics)} real trending topics:")
        print("-" * 60)
        
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic['topic']}")
            print(f"   📊 Search Volume: {topic['search_volume']}")
            print(f"   📈 Recent Volume: {topic.get('recent_volume', 'N/A')}")
            print(f"   📊 Avg Volume: {topic.get('avg_volume', 'N/A')}")
            print(f"   📝 Context: {topic.get('context', 'N/A')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pytrends_direct():
    """Test pytrends directly to see what's happening."""
    print("\n🔧 TESTING PYTENDS DIRECTLY")
    print("=" * 60)
    
    try:
        from pytrends.request import TrendReq
        
        print("📥 Initializing pytrends...")
        
        # Try different initialization methods
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2, backoff_factor=0.1)
            print("✅ Method 1: With backoff_factor")
        except TypeError:
            try:
                pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2)
                print("✅ Method 2: Without backoff_factor")
            except Exception as e:
                print(f"❌ Method 2 failed: {e}")
                pytrends = TrendReq(hl='en-US', tz=360)
                print("✅ Method 3: Basic initialization")
        
        print("🔍 Fetching trending searches...")
        trending_searches = pytrends.trending_searches(pn='united_states')
        
        if trending_searches.empty:
            print("❌ No trending searches found")
            return False
        
        print(f"✅ Found {len(trending_searches)} trending searches")
        print("\n📊 Top 10 trending searches:")
        print("-" * 40)
        
        for i, search in enumerate(trending_searches.head(10).iloc[:, 0], 1):
            print(f"{i}. {search}")
        
        return True
        
    except Exception as e:
        print(f"❌ pytrends test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the tests."""
    print("🧪 REAL TRENDING TOPICS TEST")
    print("=" * 60)
    
    # Test 1: Direct pytrends
    pytrends_success = test_pytrends_direct()
    
    if pytrends_success:
        # Test 2: Our trending fetcher
        fetcher_success = test_real_trending_fetch()
        
        if fetcher_success:
            print("\n🎉 SUCCESS! Real trending topics are working!")
            return 0
        else:
            print("\n⚠️ pytrends works but our fetcher has issues")
            return 1
    else:
        print("\n❌ pytrends itself is not working")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 