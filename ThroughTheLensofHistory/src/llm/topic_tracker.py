"""
Topic tracking system to manage historical topics and prevent repetition.
"""
import json
import logging
from pathlib import Path
from typing import Set, List, Dict, Optional
from datetime import datetime, timedelta
import hashlib

import sys
from pathlib import Path

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from utils.error_handling import handle_errors, validate_input

# Initialize logger
logger = get_logger(__name__)

class TopicTracker:
    """Tracks used topics to prevent content repetition."""
    
    def __init__(self, data_file: Optional[Path] = None):
        """
        Initialize the topic tracker.
        
        Args:
            data_file: Path to the JSON file for storing used topics
        """
        self.data_file = data_file or (Config.DATA_DIR / "topic_history.json")
        self.used_topics: Dict[str, Dict] = {}
        self._load_used_topics()
        
        # Ensure data directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized TopicTracker with {len(self.used_topics)} tracked topics")
    
    def _load_used_topics(self) -> None:
        """Load used topics from the data file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.used_topics = data.get('topics', {})
                    
                    # Clean up old entries (older than 90 days)
                    cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
                    self.used_topics = {
                        k: v for k, v in self.used_topics.items()
                        if v.get('last_used', '') > cutoff_date
                    }
                    
                    if len(self.used_topics) != len(data.get('topics', {})):
                        self._save_used_topics()
                        
        except Exception as e:
            logger.error(f"Error loading used topics: {str(e)}")
            self.used_topics = {}
    
    def _save_used_topics(self) -> None:
        """Save used topics to the data file."""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'topics': self.used_topics
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving used topics: {str(e)}")
    
    def _generate_topic_id(self, topic: str) -> str:
        """Generate a unique ID for a topic."""
        return hashlib.md5(topic.lower().encode('utf-8')).hexdigest()
    
    def is_topic_used(self, topic: str) -> bool:
        """
        Check if a topic has already been used.
        
        Args:
            topic: The topic to check
            
        Returns:
            bool: True if the topic has been used, False otherwise
        """
        topic_id = self._generate_topic_id(topic)
        return topic_id in self.used_topics
    
    def get_topic_info(self, topic: str) -> Optional[Dict]:
        """
        Get information about a previously used topic.
        
        Args:
            topic: The topic to look up
            
        Returns:
            Optional[Dict]: Topic information if found, None otherwise
        """
        topic_id = self._generate_topic_id(topic)
        return self.used_topics.get(topic_id)
    
    def mark_topic_used(
        self,
        topic: str,
        video_id: Optional[str] = None,
        usage_context: Optional[Dict] = None
    ) -> None:
        """
        Mark a topic as used.
        
        Args:
            topic: The topic to mark as used
            video_id: Optional video ID associated with this topic
            usage_context: Additional context about how the topic was used
        """
        topic_id = self._generate_topic_id(topic)
        now = datetime.now().isoformat()
        
        self.used_topics[topic_id] = {
            'topic': topic,
            'first_used': now,
            'last_used': now,
            'use_count': self.used_topics.get(topic_id, {}).get('use_count', 0) + 1,
            'video_id': video_id or self.used_topics.get(topic_id, {}).get('video_id'),
            'context': usage_context or self.used_topics.get(topic_id, {}).get('context', {})
        }
        
        self._save_used_topics()
        logger.info(f"Marked topic as used: {topic[:50]}...")
    
    def get_similar_topics(self, topic: str, threshold: float = 0.8) -> List[Dict]:
        """
        Find topics similar to the given topic.
        
        Args:
            topic: The topic to find similar topics for
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar topics with their information
        """
        # Simple implementation - in a real app, you'd use a proper NLP similarity metric
        topic_lower = topic.lower()
        similar = []
        
        for topic_info in self.used_topics.values():
            used_topic = topic_info['topic'].lower()
            
            # Simple word overlap check
            overlap = len(set(topic_lower.split()) & set(used_topic.split()))
            total = max(len(set(topic_lower.split())), len(set(used_topic.split())))
            similarity = overlap / total if total > 0 else 0
            
            if similarity >= threshold:
                similar.append({
                    'topic': topic_info['topic'],
                    'similarity': similarity,
                    'last_used': topic_info.get('last_used'),
                    'use_count': topic_info.get('use_count', 0)
                })
        
        # Sort by similarity (descending)
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)
    
    def get_topic_statistics(self) -> Dict:
        """
        Get statistics about topic usage.
        
        Returns:
            Dict containing usage statistics
        """
        now = datetime.now()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        
        recent_topics = [
            t for t in self.used_topics.values()
            if t.get('last_used', '') >= thirty_days_ago
        ]
        
        return {
            'total_topics': len(self.used_topics),
            'recent_topics': len(recent_topics),
            'most_used_topic': max(
                self.used_topics.values(),
                key=lambda x: x.get('use_count', 0),
                default={'topic': 'N/A', 'use_count': 0}
            ) if self.used_topics else {'topic': 'N/A', 'use_count': 0},
            'last_used': max(
                (t.get('last_used', '') for t in self.used_topics.values()),
                default='Never'
            )
        }

# Example usage:
# tracker = TopicTracker()
# 
# # Check if a topic has been used
# if not tracker.is_topic_used("The Fall of the Roman Empire"):
#     # Generate content...
#     tracker.mark_topic_used(
#         "The Fall of the Roman Empire",
#         video_id="abc123",
#         usage_context={"era": "Ancient Rome", "category": "Empires"}
#     )
# 
# # Get similar topics
# similar = tracker.get_similar_topics("Roman Empire collapse")
# 
# # Get statistics
# stats = tracker.get_topic_statistics()
