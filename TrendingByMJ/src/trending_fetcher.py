"""
Google Trends Fetcher for TrendingByMJ
Fetches trending topics from Google Trends and provides context
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import requests
from pytrends.request import TrendReq

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config

class TrendingFetcher:
    """Fetches trending topics from Google Trends and manages history."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        # Fix compatibility issue with newer pytrends versions
        try:
            self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2, backoff_factor=0.1)
        except TypeError:
            # Fallback for newer pytrends versions
            self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2)
        
        self.history_file = Config.HISTORY_FILE
        self.history = self._load_history()
        
    def _load_history(self) -> Dict[str, Any]:
        """Load trending history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                self.logger.info(f"📚 Loaded trending history: {len(history.get('topics', []))} topics")
                return history
            else:
                self.logger.info("📚 No trending history found, creating new file")
                return {"topics": [], "last_updated": None}
        except Exception as e:
            self.logger.error(f"❌ Error loading trending history: {e}")
            return {"topics": [], "last_updated": None}
    
    def _save_history(self):
        """Save trending history to file."""
        try:
            self.history["last_updated"] = datetime.now().isoformat()
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            self.logger.info(f"💾 Saved trending history: {len(self.history['topics'])} topics")
        except Exception as e:
            self.logger.error(f"❌ Error saving trending history: {e}")
    
    def _is_topic_recent(self, topic: str) -> bool:
        """Check if a topic was used recently (within avoid_recent_days)."""
        cutoff_date = datetime.now() - timedelta(days=Config.AVOID_RECENT_DAYS)
        
        for topic_data in self.history.get("topics", []):
            if topic_data.get("topic", "").lower() == topic.lower():
                used_date = datetime.fromisoformat(topic_data.get("used_date", "2000-01-01"))
                if used_date > cutoff_date:
                    return True
        return False
    
    def _add_to_history(self, topic: str, search_volume: int, context: str = ""):
        """Add a topic to history."""
        topic_data = {
            "topic": topic,
            "search_volume": search_volume,
            "context": context,
            "used_date": datetime.now().isoformat(),
            "discovered_date": datetime.now().isoformat()
        }
        
        self.history["topics"].append(topic_data)
        
        # Keep only the most recent topics
        if len(self.history["topics"]) > Config.MAX_HISTORY_SIZE:
            self.history["topics"] = self.history["topics"][-Config.MAX_HISTORY_SIZE:]
        
        self._save_history()
    
    def fetch_trending_topics(self) -> List[Dict[str, Any]]:
        """Fetch trending topics from Google Trends."""
        try:
            self.logger.info("🔍 Fetching trending topics from Google Trends...")
            
            # Get trending searches
            trending_searches = self.pytrends.trending_searches(pn='united_states')
            
            if trending_searches.empty:
                self.logger.warning("⚠️ No trending searches found")
                return []
            
            # Get top searches (get more to filter for best ones)
            top_searches = trending_searches.head(30).iloc[:, 0].tolist()
            self.logger.info(f"📊 Found {len(top_searches)} trending searches")
            
            # Get context and volume for all topics first
            all_topic_data = []
            
            for topic in top_searches:
                if self._is_topic_recent(topic):
                    self.logger.info(f"⏭️ Skipping recent topic: {topic}")
                    continue
                
                # Get search volume and context
                topic_data = self._get_topic_context(topic)
                if topic_data:
                    all_topic_data.append(topic_data)
                
                # Rate limiting
                time.sleep(1)
            
            # Sort by search volume (highest first) and recency
            all_topic_data.sort(key=lambda x: (x['search_volume'], x.get('discovered_date', '')), reverse=True)
            
            # Take the top trending topics
            trending_topics = all_topic_data[:Config.MAX_TRENDING_TOPICS]
            
            self.logger.info(f"✅ Found {len(trending_topics)} high-volume trending topics")
            
            # Log the selected topics with their volumes
            for i, topic in enumerate(trending_topics, 1):
                self.logger.info(f"  {i}. {topic['topic']} (Volume: {topic['search_volume']})")
            
            return trending_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching trending topics: {e}")
            return []
    
    def _get_topic_context(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get context and search volume for a topic."""
        try:
            # Build payload for pytrends
            self.pytrends.build_payload([topic], cat=0, timeframe='now 1-d', geo='US')
            
            # Get interest over time
            interest_data = self.pytrends.interest_over_time()
            
            if interest_data.empty:
                return None
            
            # Calculate search volume (use max recent value for trending topics)
            recent_volume = interest_data[topic].tail(4).max()  # Last 4 data points (last few hours)
            avg_volume = interest_data[topic].mean()
            
            # Use the higher of recent or average volume
            search_volume = max(recent_volume, avg_volume)
            
            if search_volume < Config.MIN_SEARCH_VOLUME:
                self.logger.info(f"📉 Topic {topic} has low search volume: {search_volume:.1f}")
                return None
            
            # Get related topics for context
            related_topics = self.pytrends.related_topics()
            context = self._extract_context(topic, related_topics)
            
            topic_data = {
                "topic": topic,
                "search_volume": int(search_volume),
                "recent_volume": int(recent_volume),
                "avg_volume": int(avg_volume),
                "context": context,
                "discovered_date": datetime.now().isoformat()
            }
            
            self.logger.info(f"📈 Topic: {topic} (Recent: {recent_volume:.1f}, Avg: {avg_volume:.1f})")
            return topic_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting context for {topic}: {e}")
            return None
    
    def _extract_context(self, topic: str, related_topics: Dict) -> str:
        """Extract context from related topics."""
        try:
            context_parts = []
            
            # Get top related topics
            if 'top' in related_topics and related_topics['top'] is not None:
                top_related = related_topics['top'].head(3)
                if not top_related.empty:
                    related_list = top_related['topic_title'].tolist()
                    context_parts.append(f"Related: {', '.join(related_list)}")
            
            # Get rising related topics
            if 'rising' in related_topics and related_topics['rising'] is not None:
                rising_related = related_topics['rising'].head(2)
                if not rising_related.empty:
                    rising_list = rising_related['topic_title'].tolist()
                    context_parts.append(f"Rising: {', '.join(rising_list)}")
            
            return " | ".join(context_parts) if context_parts else f"Trending topic: {topic}"
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting context: {e}")
            return f"Trending topic: {topic}"
    
    def mark_topic_used(self, topic: str):
        """Mark a topic as used in history."""
        for topic_data in self.history.get("topics", []):
            if topic_data.get("topic", "").lower() == topic.lower():
                topic_data["used_date"] = datetime.now().isoformat()
                self._save_history()
                self.logger.info(f"✅ Marked topic as used: {topic}")
                break
    
    def get_trending_summary(self, topics: List[Dict[str, Any]]) -> str:
        """Generate a summary of trending topics."""
        if not topics:
            return "No trending topics found."
        
        summary_parts = []
        for i, topic_data in enumerate(topics, 1):
            topic = topic_data["topic"]
            volume = topic_data["search_volume"]
            summary_parts.append(f"{i}. {topic} (Volume: {volume})")
        
        return "\n".join(summary_parts)
    
    def cleanup_old_history(self):
        """Remove topics older than avoid_recent_days from history."""
        cutoff_date = datetime.now() - timedelta(days=Config.AVOID_RECENT_DAYS)
        
        original_count = len(self.history.get("topics", []))
        self.history["topics"] = [
            topic for topic in self.history.get("topics", [])
            if datetime.fromisoformat(topic.get("used_date", "2000-01-01")) > cutoff_date
        ]
        
        removed_count = original_count - len(self.history["topics"])
        if removed_count > 0:
            self.logger.info(f"🧹 Cleaned up {removed_count} old topics from history")
            self._save_history()

def test_trending_fetcher():
    """Test the trending fetcher functionality."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_trending_fetcher")
    
    fetcher = TrendingFetcher(logger)
    
    print("🔍 Testing Trending Fetcher...")
    
    # Fetch trending topics
    topics = fetcher.fetch_trending_topics()
    
    if topics:
        print(f"\n📊 Found {len(topics)} trending topics:")
        for i, topic_data in enumerate(topics, 1):
            print(f"{i}. {topic_data['topic']} (Volume: {topic_data['search_volume']})")
            print(f"   Context: {topic_data['context']}")
            print()
        
        # Test summary
        summary = fetcher.get_trending_summary(topics)
        print("📝 Summary:")
        print(summary)
        
        # Test marking as used
        if topics:
            fetcher.mark_topic_used(topics[0]["topic"])
            print(f"✅ Marked '{topics[0]['topic']}' as used")
    else:
        print("❌ No trending topics found")

if __name__ == "__main__":
    test_trending_fetcher() 