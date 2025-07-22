"""
Real Google Trends Fetcher
Gets actual live trending topics from Google Trends
"""

import requests
import json
import logging
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from urllib.parse import quote_plus

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config

class RealTrendingFetcher:
    """Real trending fetcher that gets live data from Google Trends."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
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
        """Check if a topic was used recently."""
        cutoff_date = datetime.now() - timedelta(days=Config.AVOID_RECENT_DAYS)
        
        for topic_data in self.history.get("topics", []):
            if topic_data.get("topic", "").lower() == topic.lower():
                used_date = datetime.fromisoformat(topic_data.get("used_date", "2000-01-01"))
                if used_date > cutoff_date:
                    return True
        return False
    
    def fetch_trending_topics(self) -> List[Dict[str, Any]]:
        """Fetch real trending topics from Google Trends with fallbacks."""
        try:
            self.logger.info("🔍 Fetching REAL trending topics from Google Trends...")
            
            # Get trending searches from multiple sources
            trending_topics = []
            
            # 1. Google Trends (PRIMARY SOURCE)
            google_trends = self._fetch_google_trends()
            if google_trends:
                trending_topics.extend(google_trends)
                self.logger.info(f"✅ Found {len(google_trends)} Google Trends topics")
            
            # 2. Only use Reddit if Google Trends fails (FALLBACK)
            if not trending_topics:
                self.logger.warning("⚠️ Google Trends failed, using Reddit as fallback...")
                reddit_trends = self._fetch_reddit_trends()
                if reddit_trends:
                    trending_topics.extend(reddit_trends)
                    self.logger.info(f"✅ Found {len(reddit_trends)} Reddit fallback topics")
            
            # 3. Twitter/X as last resort (if still no topics)
            if not trending_topics:
                self.logger.warning("⚠️ Both Google Trends and Reddit failed, trying Twitter...")
                twitter_trends = self._fetch_twitter_trends()
                if twitter_trends:
                    trending_topics.extend(twitter_trends)
                    self.logger.info(f"✅ Found {len(twitter_trends)} Twitter fallback topics")
            
            # Filter out recent topics and get context
            filtered_topics = []
            for topic_data in trending_topics:
                topic = topic_data["topic"]
                if self._is_topic_recent(topic):
                    self.logger.info(f"⏭️ Skipping recent topic: {topic}")
                    continue
                
                # Get enhanced context
                enhanced_topic = self._get_topic_context(topic_data)
                if enhanced_topic:
                    filtered_topics.append(enhanced_topic)
                
                # Limit to max topics
                if len(filtered_topics) >= Config.MAX_TRENDING_TOPICS:
                    break
                
                # Rate limiting
                time.sleep(1)
            
            self.logger.info(f"✅ Found {len(filtered_topics)} new trending topics")
            
            # Log the selected topics with their volumes
            for i, topic in enumerate(filtered_topics, 1):
                self.logger.info(f"  {i}. {topic['topic']} (Volume: {topic['search_volume']})")
            
            return filtered_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching trending topics: {e}")
            return []
    
    def _fetch_google_trends(self) -> List[Dict[str, Any]]:
        """Fetch trending searches from Google Trends with Selenium."""
        try:
            topics = []
            
            # Method 1: Google Trends with Selenium (PRIMARY SOURCE)
            google_topics = self._fetch_google_trends_main()
            if google_topics:
                topics.extend(google_topics)
                self.logger.info(f"📊 Found {len(google_topics)} topics from Google Trends Selenium")
            
            # Method 2: News API as backup (if available)
            if not topics:
                news_topics = self._fetch_news_api_trending()
                if news_topics:
                    topics.extend(news_topics)
                    self.logger.info(f"📊 Found {len(news_topics)} topics from News API backup")
            
            # Method 3: Reddit news as last resort
            if not topics:
                self.logger.warning("⚠️ Google Trends and News API failed, using Reddit news as fallback...")
                reddit_news_topics = self._fetch_reddit_news_trending()
                if reddit_news_topics:
                    topics.extend(reddit_news_topics)
                    self.logger.info(f"📊 Found {len(reddit_news_topics)} Reddit news fallback topics")
            
            # Remove duplicates and sort by volume
            unique_topics = {}
            for topic in topics:
                topic_name = topic["topic"].lower()
                if topic_name not in unique_topics or topic["search_volume"] > unique_topics[topic_name]["search_volume"]:
                    unique_topics[topic_name] = topic
            
            final_topics = list(unique_topics.values())
            final_topics.sort(key=lambda x: x["search_volume"], reverse=True)
            
            self.logger.info(f"📊 Total unique Google Trends topics: {len(final_topics)}")
            return final_topics[:Config.MAX_TRENDING_TOPICS]
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Google Trends: {e}")
            return []
    
    def _fetch_google_trends_main(self) -> List[Dict[str, Any]]:
        """Fetch trending searches from Google Trends using Selenium."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            import time
            
            self.logger.info("🔍 Fetching Google Trends with Selenium...")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
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
                driver.get(url)
                
                # Wait for page to load
                self.logger.info("⏳ Waiting for Google Trends page to load...")
                time.sleep(5)  # Initial wait
                
                # Wait for trending topics to appear
                wait = WebDriverWait(driver, 20)
                
                # Try to find trending topics in table rows
                selectors_to_try = [
                    "table tr",
                    "div[role='row']",
                    ".trending-item"
                ]
                
                topics = []
                found_topics = False
                
                for selector in selectors_to_try:
                    try:
                        # Wait for elements to be present
                        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                        
                        if elements:
                            self.logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                            
                            for i, element in enumerate(elements):
                                try:
                                    text = element.text.strip()
                                    
                                    # Look for trending topic patterns in the text
                                    # Pattern: "topic_name\nsearch_volume\narrow_upward\npercentage\nhours ago"
                                    lines = text.split('\n')
                                    
                                    if len(lines) >= 3:
                                        # First line is usually the topic name
                                        topic_name = lines[0].strip()
                                        
                                        # Check if it looks like a trending topic
                                        if (topic_name and 
                                            len(topic_name) > 3 and 
                                            not topic_name.startswith('Search') and
                                            not topic_name.startswith('Trends') and
                                            not topic_name.startswith('Home') and
                                            not topic_name.startswith('Explore')):
                                            
                                            # Extract search volume from second line
                                            search_volume_text = lines[1] if len(lines) > 1 else ""
                                            search_volume = self._extract_search_volume(search_volume_text)
                                            
                                            # Extract percentage increase
                                            percentage_text = lines[3] if len(lines) > 3 else ""
                                            percentage = self._extract_percentage(percentage_text)
                                            
                                            # Extract time ago
                                            time_text = lines[4] if len(lines) > 4 else ""
                                            time_ago = self._extract_time_ago(time_text)
                                            
                                            topics.append({
                                                "topic": topic_name,
                                                "search_volume": search_volume,
                                                "recent_volume": search_volume,
                                                "avg_volume": max(50, search_volume - 20),
                                                "context": f"Google Trends: {search_volume_text} searches, {percentage} increase",
                                                "trending_reason": f"Trending with {search_volume_text} searches, {percentage} increase {time_ago}",
                                                "related_searches": [],
                                                "news_context": f"Trending on Google Trends with {search_volume_text} searches",
                                                "discovered_date": datetime.now().isoformat()
                                            })
                                            
                                            if len(topics) >= 10:  # Limit to top 10
                                                break
                                            
                                except Exception as e:
                                    self.logger.warning(f"⚠️ Error processing element {i}: {e}")
                                    continue
                            
                            if topics:
                                found_topics = True
                                break
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ Selector {selector} failed: {e}")
                        continue
                
                if not found_topics:
                    # Try to get any text that might be trending topics
                    self.logger.info("🔍 Trying to extract topics from page text...")
                    page_text = driver.page_source
                    
                    # Look for potential trending topics in the page source
                    import re
                    # Look for patterns that might be trending topics
                    potential_topics = re.findall(r'<[^>]*>([A-Z][a-zA-Z\s]+)</[^>]*>', page_text)
                    
                    for i, topic in enumerate(potential_topics[:10]):
                        topic = topic.strip()
                        if len(topic) > 3 and len(topic) < 50:
                            search_volume = 90 - (i * 5)
                            topics.append({
                                "topic": topic,
                                "search_volume": search_volume,
                                "recent_volume": search_volume,
                                "avg_volume": search_volume,
                                "context": f"Google Trends Text Extraction: {topic}",
                                "trending_reason": f"Extracted from Google Trends page",
                                "related_searches": [],
                                "news_context": f"Trending on Google Trends",
                                "discovered_date": datetime.now().isoformat()
                            })
                
                self.logger.info(f"📊 Google Trends Selenium: Found {len(topics)} topics")
                return topics
                
            finally:
                driver.quit()
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Google Trends with Selenium: {e}")
            return []
    
    def _extract_search_volume(self, text: str) -> int:
        """Extract search volume from text like '2M+', '200K+', '50K+'."""
        try:
            import re
            # Look for patterns like "2M+", "200K+", "50K+"
            match = re.search(r'(\d+(?:\.\d+)?)([MK]?)\+?', text)
            if match:
                number = float(match.group(1))
                multiplier = match.group(2)
                
                if multiplier == 'M':
                    return int(number * 1000000)
                elif multiplier == 'K':
                    return int(number * 1000)
                else:
                    return int(number)
            
            # Fallback: try to extract any number
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
            
            return 50  # Default fallback
        except:
            return 50
    
    def _extract_percentage(self, text: str) -> str:
        """Extract percentage from text like '1,000%', '300%'."""
        try:
            import re
            match = re.search(r'(\d+(?:,\d+)?)%', text)
            if match:
                return match.group(1) + '%'
            return '100%'  # Default
        except:
            return '100%'
    
    def _extract_time_ago(self, text: str) -> str:
        """Extract time from text like '3 hours ago', '17 hours ago'."""
        try:
            import re
            match = re.search(r'(\d+)\s+(hour|day|minute)s?\s+ago', text)
            if match:
                number = match.group(1)
                unit = match.group(2)
                return f"{number} {unit}s ago"
            return 'recently'  # Default
        except:
            return 'recently'
    
    def _fetch_news_api_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending topics from News API."""
        try:
            from config import Config
            
            # Check if News API key is available
            if not Config.NEWS_API_KEY:
                self.logger.warning("⚠️ News API key not available, skipping News API")
                return []
            
            # Get top headlines which often indicate trending topics
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "country": "us",
                "apiKey": Config.NEWS_API_KEY,
                "pageSize": 20
            }
            
            self.logger.info("🔍 Fetching News API top headlines...")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            topics = []
            for i, article in enumerate(articles[:10]):
                title = article.get("title", "")
                
                # Extract potential trending topics from headlines
                # Look for names, events, etc.
                words = title.split()
                potential_topics = []
                
                for word in words:
                    # Filter out common words and look for proper nouns
                    if (len(word) > 3 and 
                        word[0].isupper() and 
                        word not in ['The', 'This', 'That', 'What', 'When', 'Where', 'Why', 'How', 'Breaking', 'News']):
                        potential_topics.append(word)
                
                if potential_topics:
                    topic = ' '.join(potential_topics[:2])  # Take first 2 words
                    search_volume = 90 - (i * 5)
                    
                    topics.append({
                        "topic": topic,
                        "search_volume": search_volume,
                        "recent_volume": search_volume,
                        "avg_volume": search_volume,
                        "context": f"News API: {title[:100]}...",
                        "trending_reason": f"Top headline with {search_volume} search volume",
                        "related_searches": [title[:50]],
                        "news_context": f"Breaking news: {title}",
                        "discovered_date": datetime.now().isoformat()
                    })
            
            self.logger.info(f"📊 News API: Found {len(topics)} topics")
            return topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching News API trending: {e}")
            return []
    
    def _fetch_reddit_news_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending topics from Reddit news subreddits."""
        try:
            # News-focused subreddits
            news_subreddits = [
                'news',
                'worldnews', 
                'politics',
                'technology',
                'science',
                'business',
                'sports',
                'entertainment'
            ]
            
            trending_topics = []
            
            for subreddit in news_subreddits[:3]:  # Limit to top 3 to avoid rate limiting
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                    
                    self.logger.info(f"🔍 Fetching Reddit r/{subreddit} hot posts...")
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for i, post in enumerate(posts[:5]):  # Get top 5 from each subreddit
                        post_data = post.get('data', {})
                        title = post_data.get('title', '')
                        score = post_data.get('score', 0)
                        
                        # Only high-engagement posts
                        if score > 500:
                            # Extract potential trending topics from titles
                            words = title.split()
                            potential_topics = []
                            
                            for word in words:
                                # Filter out common words and look for proper nouns
                                if (len(word) > 3 and 
                                    word[0].isupper() and 
                                    word not in ['The', 'This', 'That', 'What', 'When', 'Where', 'Why', 'How', 'Breaking', 'News']):
                                    potential_topics.append(word)
                            
                            if potential_topics:
                                topic = ' '.join(potential_topics[:2])  # Take first 2 words
                                search_volume = max(60, 95 - (len(trending_topics) * 5))
                                
                                trending_topics.append({
                                    "topic": topic,
                                    "search_volume": search_volume,
                                    "recent_volume": search_volume,
                                    "avg_volume": max(50, search_volume - 10),
                                    "context": f"Reddit news in r/{subreddit}",
                                    "trending_reason": f"High Reddit news engagement: {score} upvotes",
                                    "related_searches": [title[:50]],
                                    "news_context": f"Trending news on Reddit r/{subreddit}",
                                    "discovered_date": datetime.now().isoformat()
                                })
                                
                                if len(trending_topics) >= 10:  # Limit total
                                    break
                    
                    # Rate limiting between subreddits
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error fetching r/{subreddit}: {e}")
                    continue
            
            self.logger.info(f"📰 Reddit News: Found {len(trending_topics)} topics")
            return trending_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Reddit news trending: {e}")
            return []
    
    def _fetch_reddit_trending_filtered(self) -> List[Dict[str, Any]]:
        """Fetch trending topics from Reddit with better filtering for real events."""
        try:
            # Get trending topics from Reddit
            url = "https://www.reddit.com/r/popular.json"
            
            self.logger.info("🔍 Fetching Reddit trending topics (filtered)...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            trending_topics = []
            for i, post in enumerate(posts[:20]):  # Get more to filter
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                score = post_data.get('score', 0)
                subreddit = post_data.get('subreddit', '')
                
                # Filter for real events and news (not memes/jokes)
                if (score > 1000 and  # High engagement
                    subreddit.lower() not in ['memes', 'funny', 'jokes', 'dankmemes', 'meirl'] and
                    not any(word in title.lower() for word in ['meme', 'joke', 'funny', 'lol', 'haha'])):
                    
                    # Extract potential trending topics from titles
                    words = title.split()
                    potential_topics = []
                    
                    for word in words:
                        # Filter out common words and look for proper nouns
                        if (len(word) > 3 and 
                            word[0].isupper() and 
                            word not in ['The', 'This', 'That', 'What', 'When', 'Where', 'Why', 'How']):
                            potential_topics.append(word)
                    
                    if potential_topics:
                        topic = ' '.join(potential_topics[:2])  # Take first 2 words
                        search_volume = max(50, 100 - (len(trending_topics) * 5))
                        
                        trending_topics.append({
                            "topic": topic,
                            "search_volume": search_volume,
                            "recent_volume": search_volume,
                            "avg_volume": max(40, search_volume - 10),
                            "context": f"Reddit trending in r/{subreddit}",
                            "trending_reason": f"High Reddit engagement: {score} upvotes",
                            "related_searches": [title[:50]],
                            "news_context": f"Trending on Reddit r/{subreddit}",
                            "discovered_date": datetime.now().isoformat()
                        })
                        
                        if len(trending_topics) >= 10:  # Limit to top 10
                            break
            
            self.logger.info(f"📱 Reddit Filtered: Found {len(trending_topics)} topics")
            return trending_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Reddit trending filtered: {e}")
            return []
    
    def _fetch_google_trends_pytrends(self) -> List[Dict[str, Any]]:
        """Fetch trending searches using pytrends library."""
        try:
            # Try to import pytrends
            try:
                from pytrends.request import TrendReq
            except ImportError:
                self.logger.warning("⚠️ pytrends not available, skipping pytrends method")
                return []
            
            # Initialize pytrends with compatibility fixes
            try:
                pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2, backoff_factor=0.1)
            except TypeError:
                # Fallback for newer pytrends versions
                try:
                    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2)
                except Exception:
                    # Last resort - minimal initialization
                    pytrends = TrendReq(hl='en-US', tz=360)
            
            self.logger.info("🔍 Fetching Google Trends via pytrends...")
            
            # Get trending searches
            trending_searches = pytrends.trending_searches(pn='united_states')
            
            topics = []
            for i, topic in enumerate(trending_searches.head(20).iloc[:, 0]):
                # Get interest over time for volume estimation
                try:
                    pytrends.build_payload([topic], timeframe='now 1-d', geo='US')
                    interest_data = pytrends.interest_over_time()
                    
                    if not interest_data.empty:
                        search_volume = int(interest_data[topic].max())
                    else:
                        search_volume = 100 - (i * 5)  # Fallback volume
                except:
                    search_volume = 100 - (i * 5)  # Fallback volume
                
                topics.append({
                    "topic": topic,
                    "search_volume": search_volume,
                    "recent_volume": search_volume,
                    "avg_volume": search_volume,
                    "context": "Google Trends trending search",
                    "trending_reason": f"High search volume: {search_volume}",
                    "related_searches": [],
                    "news_context": f"Trending on Google Trends",
                    "discovered_date": datetime.now().isoformat()
                })
                
                # Rate limiting
                time.sleep(1)
            
            return topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Google Trends via pytrends: {e}")
            return []
    
    def _fetch_google_trends_web(self) -> List[Dict[str, Any]]:
        """Fetch trending searches by web scraping Google Trends realtime."""
        try:
            # Google Trends realtime page (working URL)
            url = "https://trends.google.com/trends/trendingsearches/realtime?geo=US"
            
            self.logger.info("🔍 Web scraping Google Trends realtime...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse HTML for trending topics
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            topics = []
            
            # Look for trending topic elements in the realtime page
            topic_selectors = [
                'table tr td:first-child',  # First column of table rows
                '.trending-item',
                '[data-topic]',
                '.trending-story-title',
                '.story-title',
                'a[href*="/trends/explore"]'  # Links to trend exploration
            ]
            
            for selector in topic_selectors:
                elements = soup.select(selector)
                if elements:
                    for i, element in enumerate(elements[:15]):
                        title = element.get_text().strip()
                        if title and len(title) > 3 and not title.startswith('Search'):
                            topics.append({
                                "topic": title,
                                "search_volume": 95 - (i * 5),
                                "recent_volume": 95 - (i * 5),
                                "avg_volume": 90 - (i * 5),
                                "context": "Google Trends realtime web scraping",
                                "trending_reason": f"Currently trending on Google Trends",
                                "related_searches": [],
                                "news_context": f"Trending right now on Google Trends",
                                "discovered_date": datetime.now().isoformat()
                            })
                    break
            
            return topics
            
        except Exception as e:
            self.logger.error(f"❌ Error web scraping Google Trends realtime: {e}")
            return []
    
    def _fetch_twitter_trends(self) -> List[Dict[str, Any]]:
        """Fetch trending topics from Twitter/X."""
        try:
            # Try to get Twitter trends (this is limited due to API restrictions)
            # For now, we'll use a web scraping approach
            url = "https://trends24.in/united-states/"
            
            self.logger.info("🔍 Fetching Twitter/X trending topics...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse trending topics from the page
            # This is a simplified approach - in production you'd want a more robust parser
            content = response.text
            
            # Look for trending topic patterns
            topic_pattern = r'<a[^>]*class="trend-card"[^>]*>([^<]+)</a>'
            topics = re.findall(topic_pattern, content)
            
            trending_topics = []
            for i, topic in enumerate(topics[:10]):  # Top 10
                trending_topics.append({
                    "topic": topic.strip(),
                    "search_volume": 80 - (i * 5),  # Decreasing volume
                    "recent_volume": 80 - (i * 5),
                    "avg_volume": 70 - (i * 5),
                    "context": "Twitter/X trending topic",
                    "trending_reason": "High social media engagement",
                    "related_searches": [],
                    "news_context": f"Trending on Twitter/X",
                    "discovered_date": datetime.now().isoformat()
                })
            
            self.logger.info(f"🐦 Found {len(trending_topics)} Twitter/X trending topics")
            return trending_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Twitter trends: {e}")
            return []
    
    def _fetch_reddit_trends(self) -> List[Dict[str, Any]]:
        """Fetch trending topics from Reddit."""
        try:
            # Get trending topics from Reddit
            url = "https://www.reddit.com/r/popular.json"
            
            self.logger.info("🔍 Fetching Reddit trending topics...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            trending_topics = []
            for i, post in enumerate(posts[:10]):  # Top 10
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                score = post_data.get('score', 0)
                subreddit = post_data.get('subreddit', '')
                
                # Extract potential trending topics from titles
                # Look for names, events, etc.
                words = title.split()
                potential_topics = []
                
                for word in words:
                    # Filter out common words and look for proper nouns
                    if (len(word) > 3 and 
                        word[0].isupper() and 
                        word not in ['The', 'This', 'That', 'What', 'When', 'Where', 'Why', 'How']):
                        potential_topics.append(word)
                
                if potential_topics:
                    topic = ' '.join(potential_topics[:2])  # Take first 2 words
                    trending_topics.append({
                        "topic": topic,
                        "search_volume": max(50, 100 - (i * 5)),
                        "recent_volume": max(50, 100 - (i * 5)),
                        "avg_volume": max(40, 90 - (i * 5)),
                        "context": f"Reddit trending in r/{subreddit}",
                        "trending_reason": f"High Reddit engagement: {score} upvotes",
                        "related_searches": [title[:50]],
                        "news_context": f"Trending on Reddit r/{subreddit}",
                        "discovered_date": datetime.now().isoformat()
                    })
            
            self.logger.info(f"📱 Found {len(trending_topics)} Reddit trending topics")
            return trending_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Reddit trends: {e}")
            return []
    
    def _get_topic_context(self, topic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get enhanced context for a topic."""
        try:
            topic = topic_data["topic"]
            search_volume = topic_data.get("search_volume", 50)
            
            # Get search volume trend
            recent_volume = topic_data.get("recent_volume", search_volume)
            avg_volume = topic_data.get("avg_volume", search_volume)
            
            # Use the higher of recent or average volume
            final_volume = max(recent_volume, avg_volume)
            
            if final_volume < Config.MIN_SEARCH_VOLUME:
                self.logger.info(f"📉 Topic {topic} has low search volume: {final_volume:.1f}")
                return None
            
            # Get related topics for context
            related_topics = topic_data.get("related_searches", [])
            context = topic_data.get("context", "")
            
            enhanced_topic = {
                "topic": topic,
                "search_volume": int(final_volume),
                "recent_volume": int(recent_volume),
                "avg_volume": int(avg_volume),
                "context": context,
                "trending_reason": topic_data.get("trending_reason", f"High search volume: {final_volume}"),
                "related_searches": related_topics,
                "news_context": topic_data.get("news_context", f"Trending topic with {final_volume} search volume"),
                "discovered_date": datetime.now().isoformat()
            }
            
            # Add sensitivity check
            if any(word in topic.lower() for word in ['death', 'died', 'killed', 'shooting', 'accident']):
                enhanced_topic["sensitivity_level"] = "high"
                enhanced_topic["content_approach"] = "respectful_tribute_only"
            
            self.logger.info(f"📈 Topic: {topic} (Recent: {recent_volume:.1f}, Avg: {avg_volume:.1f})")
            return enhanced_topic
            
        except Exception as e:
            self.logger.error(f"❌ Error getting topic context for {topic}: {e}")
            return None
    
    def mark_topic_used(self, topic: str):
        """Mark a topic as used in history."""
        try:
            # Find existing topic
            for topic_data in self.history.get("topics", []):
                if topic_data.get("topic", "").lower() == topic.lower():
                    topic_data["used_date"] = datetime.now().isoformat()
                    topic_data["use_count"] = topic_data.get("use_count", 0) + 1
                    self._save_history()
                    return
            
            # Add new topic
            self.history["topics"].append({
                "topic": topic,
                "used_date": datetime.now().isoformat(),
                "use_count": 1
            })
            self._save_history()
            
        except Exception as e:
            self.logger.error(f"❌ Error marking topic as used: {e}")

def test_real_trending_fetcher():
    """Test the real trending fetcher."""
    print("🧪 Testing Real Trending Fetcher...")
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_real_trending")
    
    fetcher = RealTrendingFetcher(logger)
    
    # Fetch trending topics
    trending_topics = fetcher.fetch_trending_topics()
    
    print(f"✅ Found {len(trending_topics)} trending topics:")
    for i, topic in enumerate(trending_topics, 1):
        print(f"  {i}. {topic['topic']} (Volume: {topic['search_volume']})")
        print(f"     Reason: {topic['trending_reason']}")
        print()
    
    return True

if __name__ == "__main__":
    test_real_trending_fetcher() 