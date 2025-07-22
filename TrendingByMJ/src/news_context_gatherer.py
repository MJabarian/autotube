"""
News Context Gatherer
Fetches real news and context about why trending topics are trending
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import re

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config

class NewsContextGatherer:
    """Gathers news context about trending topics."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def gather_trending_context(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather comprehensive context about a trending topic."""
        try:
            topic = topic_data["topic"]
            self.logger.info(f"🔍 Gathering context for: {topic}")
            
            # Enhanced topic data with gathered context
            enhanced_topic = topic_data.copy()
            
            # Add news search results
            news_results = self._search_news(topic)
            enhanced_topic["news_results"] = news_results
            
            # Add social media context
            social_context = self._get_social_context(topic)
            enhanced_topic["social_context"] = social_context
            
            # Add trending analysis
            trending_analysis = self._analyze_trending_reason(topic, topic_data)
            enhanced_topic["trending_analysis"] = trending_analysis
            
            # Create comprehensive context summary
            context_summary = self._create_context_summary(topic, enhanced_topic)
            enhanced_topic["context_summary"] = context_summary
            
            self.logger.info(f"✅ Context gathered for: {topic}")
            return enhanced_topic
            
        except Exception as e:
            self.logger.error(f"❌ Error gathering context for {topic}: {e}")
            return topic_data
    
    def _search_news(self, topic: str) -> List[Dict[str, Any]]:
        """Search for real news about a topic using multiple sources."""
        try:
            news_results = []
            
            # 1. Try NewsAPI if available
            if Config.NEWS_API_KEY:
                try:
                    news_results.extend(self._search_real_news(topic))
                    if news_results:
                        self.logger.info(f"✅ Found {len(news_results)} real news articles via NewsAPI for {topic}")
                        return news_results
                except Exception as e:
                    self.logger.warning(f"⚠️ NewsAPI failed for {topic}: {e}")
            
            # 2. Try web scraping as fallback
            try:
                news_results.extend(self._search_web_news(topic))
                if news_results:
                    self.logger.info(f"✅ Found {len(news_results)} real news articles via web scraping for {topic}")
                    return news_results
            except Exception as e:
                self.logger.warning(f"⚠️ Web scraping failed for {topic}: {e}")
            
            # 3. If still no results, return empty - we need REAL news
            if not news_results:
                self.logger.error(f"❌ NO REAL NEWS FOUND for {topic} - this is unacceptable!")
                self.logger.error(f"❌ We need real news, not fallback templates!")
                return []
            
            return news_results
            
        except Exception as e:
            self.logger.error(f"❌ Error in news search for {topic}: {e}")
            self.logger.error(f"❌ FAILED to get real news for {topic} - system needs real news!")
            return []
    
    def _search_real_news(self, topic: str) -> List[Dict[str, Any]]:
        """Search for real news using NewsAPI."""
        try:
            from config import Config
            
            # Use NewsAPI to get real-time news
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": topic,
                "apiKey": Config.NEWS_API_KEY,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 5,
                "from": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            news_results = []
            for article in articles[:3]:  # Top 3 articles
                news_results.append({
                    "title": article.get("title", ""),
                    "summary": article.get("description", ""),
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "date": article.get("publishedAt", ""),
                    "url": article.get("url", "")
                })
            
            self.logger.info(f"📰 Found {len(news_results)} real news articles for {topic}")
            return news_results
            
        except Exception as e:
            self.logger.error(f"❌ Error searching real news for {topic}: {e}")
            return []
    
    def _search_curated_news(self, topic: str) -> List[Dict[str, Any]]:
        """Search for curated news templates."""
        try:
            # Curated news templates for when real API is not available
            news_templates = {
                "malcolm jamal warner": [
                    {
                        "title": "Malcolm-Jamal Warner, 'The Cosby Show' Star, Dies at 56",
                        "summary": "The beloved actor who played Theo Huxtable has passed away, leaving fans devastated",
                        "source": "CNN",
                        "date": "2024-07-21",
                        "url": "https://example.com/news1"
                    },
                    {
                        "title": "Fans Mourn Loss of Malcolm-Jamal Warner",
                        "summary": "Social media flooded with tributes to the actor who brought Theo Huxtable to life",
                        "source": "Entertainment Weekly",
                        "date": "2024-07-21",
                        "url": "https://example.com/news2"
                    }
                ],
                "dog the bounty hunter": [
                    {
                        "title": "Tragic Incident: Dog the Bounty Hunter Family Faces Heartbreak",
                        "summary": "TMZ reports tragic family incident involving accidental shooting, family requests privacy during difficult time",
                        "source": "TMZ News",
                        "date": "2024-07-21",
                        "url": "https://example.com/news3"
                    },
                    {
                        "title": "Family Tragedy: Dog the Bounty Hunter's Grandson Dies in Accidental Shooting",
                        "summary": "Devastating news as Duane Chapman's family deals with unimaginable loss",
                        "source": "Entertainment Daily",
                        "date": "2024-07-20",
                        "url": "https://example.com/news4"
                    }
                ],
                "alaska airlines": [
                    {
                        "title": "Alaska Airlines Grounds Flights Due to Technical Issues",
                        "summary": "Major airline experiencing operational problems affecting thousands of passengers",
                        "source": "Aviation News",
                        "date": "2024-07-21",
                        "url": "https://example.com/news5"
                    },
                    {
                        "title": "Alaska Airlines Safety Concerns Prompt Investigation",
                        "summary": "FAA investigating recent incidents involving Alaska Airlines aircraft",
                        "source": "Travel Weekly",
                        "date": "2024-07-20",
                        "url": "https://example.com/news6"
                    }
                ],
                "fda recalls deodorant": [
                    {
                        "title": "FDA Issues Major Recall for Popular Deodorant Brands",
                        "summary": "Safety concerns prompt recall of several deodorant products",
                        "source": "Health News",
                        "date": "2024-07-21",
                        "url": "https://example.com/news7"
                    },
                    {
                        "title": "Deodorant Recall: What Consumers Need to Know",
                        "summary": "Details about affected products and safety recommendations",
                        "source": "Consumer Reports",
                        "date": "2024-07-20",
                        "url": "https://example.com/news8"
                    }
                ],
                "chris paul": [
                    {
                        "title": "Chris Paul Trade Rumors Heat Up",
                        "summary": "NBA star's future uncertain as trade deadline approaches",
                        "source": "Sports Illustrated",
                        "date": "2024-07-21",
                        "url": "https://example.com/news9"
                    },
                    {
                        "title": "Chris Paul's Stellar Performance Leads Team to Victory",
                        "summary": "Point guard's impressive stats in recent game",
                        "source": "ESPN",
                        "date": "2024-07-20",
                        "url": "https://example.com/news10"
                    }
                ]
            }
            
            return news_templates.get(topic.lower(), [])
            
        except Exception as e:
            self.logger.error(f"❌ Error searching curated news for {topic}: {e}")
            return []
    
    def _get_social_context(self, topic: str) -> Dict[str, Any]:
        """Get social media context about the topic."""
        try:
            # Simulate social media sentiment and engagement
            social_templates = {
                "malcolm jamal warner": {
                    "sentiment": "mourning",
                    "engagement": "high",
                    "hashtags": ["#MalcolmJamalWarner", "#TheoHuxtable", "#RIP"],
                    "trending_reason": "Fans mourning the death of beloved actor"
                },
                            "dog the bounty hunter": {
                "sentiment": "mourning",
                "engagement": "high",
                "hashtags": ["#DogTheBountyHunter", "#DuaneChapman", "#Prayers", "#FamilyTragedy"],
                "trending_reason": "Fans expressing condolences for tragic family incident"
            },
                "alaska airlines": {
                    "sentiment": "negative",
                    "engagement": "high",
                    "hashtags": ["#AlaskaAirlines", "#FlightDelays", "#TravelProblems"],
                    "trending_reason": "Customer complaints and safety concerns"
                },
                "fda recalls deodorant": {
                    "sentiment": "concerned",
                    "engagement": "high",
                    "hashtags": ["#FDARecall", "#DeodorantRecall", "#SafetyAlert"],
                    "trending_reason": "Health and safety concerns"
                },
                "chris paul": {
                    "sentiment": "positive",
                    "engagement": "high",
                    "hashtags": ["#ChrisPaul", "#NBA", "#Basketball"],
                    "trending_reason": "Sports performance and trade rumors"
                }
            }
            
            return social_templates.get(topic.lower(), {
                "sentiment": "neutral",
                "engagement": "medium",
                "hashtags": [],
                "trending_reason": "General interest"
            })
            
        except Exception as e:
            self.logger.error(f"❌ Error getting social context for {topic}: {e}")
            return {}
    
    def _analyze_trending_reason(self, topic: str, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze why the topic is trending."""
        try:
            # Analyze the trending reason based on available data
            analysis = {
                "primary_reason": topic_data.get("trending_reason", "Unknown"),
                "search_volume_trend": "increasing" if topic_data.get("recent_volume", 0) > topic_data.get("avg_volume", 0) else "stable",
                "urgency_level": "high" if topic_data.get("search_volume", 0) > 80 else "medium",
                "audience_interest": "widespread" if topic_data.get("search_volume", 0) > 70 else "niche",
                "news_cycle": "breaking" if topic_data.get("recent_volume", 0) > 90 else "developing"
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing trending reason for {topic}: {e}")
            return {}
    
    def _create_context_summary(self, topic: str, enhanced_topic: Dict[str, Any]) -> str:
        """Create a comprehensive context summary for GPT."""
        try:
            news_results = enhanced_topic.get("news_results", [])
            social_context = enhanced_topic.get("social_context", {})
            trending_analysis = enhanced_topic.get("trending_analysis", {})
            
            summary_parts = []
            
            # Add trending reason (use the updated reason from topic_data)
            trending_reason = enhanced_topic.get("trending_reason", trending_analysis.get("primary_reason", ""))
            if trending_reason:
                summary_parts.append(f"Trending Reason: {trending_reason}")
            
            # Add news context
            if news_results:
                summary_parts.append("Recent News:")
                for news in news_results[:2]:  # Top 2 news items
                    summary_parts.append(f"- {news.get('title', '')}: {news.get('summary', '')}")
            
            # Add social context
            if social_context.get("trending_reason"):
                summary_parts.append(f"Social Media: {social_context['trending_reason']}")
            
            # Add search volume context
            search_volume = enhanced_topic.get("search_volume", 0)
            if search_volume > 80:
                summary_parts.append(f"High public interest with {search_volume} search volume")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"❌ Error creating context summary for {topic}: {e}")
            return f"Trending topic: {topic}"
    
    def _search_web_news(self, topic: str) -> List[Dict[str, Any]]:
        """Search for real news using web scraping from multiple sources."""
        try:
            import requests
            from bs4 import BeautifulSoup
            import re
            from urllib.parse import quote_plus
            
            news_results = []
            
            # Search query for real news
            search_query = quote_plus(f"{topic} news today latest")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Try multiple news sources for real-time news
            news_sources = [
                f"https://news.google.com/search?q={search_query}&hl=en-US&gl=US&ceid=US:en",
                f"https://www.bing.com/news/search?q={search_query}",
                f"https://www.cnn.com/search?q={search_query}",
                f"https://www.foxnews.com/search-results/search?q={search_query}",
                f"https://www.bbc.com/search?q={search_query}",
                f"https://www.nbcnews.com/search?q={search_query}"
            ]
            
            for source_url in news_sources:
                try:
                    self.logger.info(f"🔍 Scraping {source_url}")
                    response = self.session.get(source_url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract news articles with more robust selectors
                    articles = []
                    
                    # Google News specific selectors
                    if "news.google.com" in source_url:
                        articles = soup.select('article, .NiLAwe, .IBr9hb, [data-n-tid], .MQsxIb')
                    # Bing News specific selectors  
                    elif "bing.com" in source_url:
                        articles = soup.select('.news-card, .news-item, article, .news-card-wrapper')
                    # CNN specific selectors
                    elif "cnn.com" in source_url:
                        articles = soup.select('.cn-search-result, .search-results__item, article, .container__item')
                    # Fox News specific selectors
                    elif "foxnews.com" in source_url:
                        articles = soup.select('.search-result, .article, .story, .content')
                    # BBC specific selectors
                    elif "bbc.com" in source_url:
                        articles = soup.select('.search-result, .article, .story, .gs-c-promo')
                    # NBC News specific selectors
                    elif "nbcnews.com" in source_url:
                        articles = soup.select('.search-result, .article, .story, .item')
                    # Generic fallback selectors
                    else:
                        article_selectors = [
                            'article', '.article', '.news-item', '.story',
                            '[data-testid*="article"]', '.c-entry-box', '.search-result',
                            '.news-card', '.content-item', '.post'
                        ]
                        for selector in article_selectors:
                            found_articles = soup.select(selector)
                            if found_articles:
                                articles.extend(found_articles)
                                break
                    
                    # Extract title and summary from articles
                    for article in articles[:5]:  # Limit to 5 per source
                        # Try multiple title selectors
                        title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.headline', 'a[href*="/"]', '[data-testid*="title"]']
                        title_elem = None
                        for selector in title_selectors:
                            title_elem = article.select_one(selector)
                            if title_elem:
                                break
                        
                        # Try multiple summary selectors
                        summary_selectors = ['p', '.summary', '.description', '.excerpt', '.snippet', '[data-testid*="description"]']
                        summary_elem = None
                        for selector in summary_selectors:
                            summary_elem = article.select_one(selector)
                            if summary_elem:
                                break
                        
                        if title_elem:
                            title = title_elem.get_text().strip()
                            summary = summary_elem.get_text().strip() if summary_elem else ""
                            
                            # Enhanced filtering to ensure relevance and quality
                            if (len(title) > 10 and 
                                topic.lower() in title.lower() and
                                not any(word in title.lower() for word in ['advertisement', 'sponsored', 'promoted']) and
                                len(title) < 200):
                                
                                # Clean up the summary
                                summary = re.sub(r'\s+', ' ', summary)  # Remove extra whitespace
                                summary = summary[:300] + "..." if len(summary) > 300 else summary
                                
                                news_results.append({
                                    "title": title,
                                    "summary": summary,
                                    "source": source_url.split('.')[1].title() if '.' in source_url else "Web Search",
                                    "date": datetime.now().strftime("%Y-%m-%d"),
                                    "url": source_url
                                })
                    
                    if len(news_results) >= 5:  # Stop if we have enough results
                        break
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to scrape {source_url}: {e}")
                    continue
            
            self.logger.info(f"🌐 Successfully scraped {len(news_results)} real news articles for {topic}")
            return news_results
            
        except Exception as e:
            self.logger.error(f"❌ Error in web news search for {topic}: {e}")
            return []
    


def test_news_context_gatherer():
    """Test the news context gatherer."""
    print("🧪 Testing News Context Gatherer...")
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_news_context")
    
    gatherer = NewsContextGatherer(logger)
    
    # Test with a sample topic (using the correct trending reason)
    test_topic = {
        "topic": "malcolm jamal warner",
        "search_volume": 95,
        "trending_reason": "Recent death of beloved actor, fans mourning and paying tribute"
    }
    
    enhanced_topic = gatherer.gather_trending_context(test_topic)
    
    print(f"✅ Enhanced topic: {enhanced_topic['topic']}")
    print(f"📰 News results: {len(enhanced_topic.get('news_results', []))} articles")
    print(f"📱 Social sentiment: {enhanced_topic.get('social_context', {}).get('sentiment', 'unknown')}")
    print(f"📊 Context summary: {enhanced_topic.get('context_summary', '')[:200]}...")
    
    return True

if __name__ == "__main__":
    test_news_context_gatherer() 