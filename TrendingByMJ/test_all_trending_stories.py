#!/usr/bin/env python3
"""
Test script to generate stories for all top 5 trending topics
Shows the context and generated content for each topic
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.simple_trending_fetcher import SimpleTrendingFetcher
from src.trending_summary_generator import TrendingSummaryGenerator
from src.news_context_gatherer import NewsContextGatherer
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_all_trending_stories():
    """Generate stories for all top 5 trending topics"""
    
    print("🎬 TRENDING BY MJ - ALL TOP 5 STORIES")
    print("=" * 60)
    
    # Initialize components
    print("🔧 Initializing components...")
    trending_fetcher = SimpleTrendingFetcher(logger)
    summary_generator = TrendingSummaryGenerator(logger)
    context_gatherer = NewsContextGatherer(logger)
    
    # Fetch all trending topics
    print("\n🔍 Fetching all trending topics...")
    trending_topics = trending_fetcher.fetch_trending_topics()
    
    if not trending_topics:
        print("❌ No trending topics found!")
        return
    
    print(f"✅ Found {len(trending_topics)} trending topics")
    
    # Generate stories for each topic
    for i, topic_data in enumerate(trending_topics, 1):
        topic = topic_data["topic"]
        search_volume = topic_data["search_volume"]
        
        print(f"\n{'='*60}")
        print(f"📰 TOPIC #{i}: {topic.upper()}")
        print(f"📊 Search Volume: {search_volume}")
        print(f"{'='*60}")
        
        # Get enhanced context
        print(f"\n🔍 Gathering context for: {topic}")
        enhanced_topic = context_gatherer.gather_trending_context(topic_data)
        
        # Display context information
        print(f"\n📋 CONTEXT SUMMARY:")
        print(f"   Trending Reason: {enhanced_topic.get('trending_reason', 'N/A')}")
        print(f"   News Context: {enhanced_topic.get('news_context', 'N/A')}")
        print(f"   Social Context: {enhanced_topic.get('social_context', 'N/A')}")
        print(f"   Related Searches: {', '.join(enhanced_topic.get('related_searches', []))}")
        
        # Generate story
        print(f"\n📝 Generating story for: {topic}")
        story_package = summary_generator.generate_trending_summary(topic_data)
        
        if story_package:
            print(f"\n✅ STORY GENERATED:")
            print(f"   Title: {story_package['title']}")
            print(f"   Duration: {story_package['estimated_duration']:.1f}s")
            print(f"   Music Category: {story_package['story_data']['music_category']}")
            
            print(f"\n📰 STORY CONTENT:")
            print(f"   {story_package['summary']}")
            
            print(f"\n🎨 IMAGE PROMPT:")
            print(f"   {story_package['image_prompt']}")
            
            # Save to file for reference
            output_dir = Config.OUTPUT_DIR / "test_stories"
            output_dir.mkdir(exist_ok=True)
            
            story_file = output_dir / f"story_{i}_{topic.replace(' ', '_')}.txt"
            with open(story_file, 'w', encoding='utf-8') as f:
                f.write(f"TOPIC: {topic}\n")
                f.write(f"SEARCH VOLUME: {search_volume}\n")
                f.write(f"TRENDING REASON: {enhanced_topic.get('trending_reason', 'N/A')}\n")
                f.write(f"NEWS CONTEXT: {enhanced_topic.get('news_context', 'N/A')}\n")
                f.write(f"SOCIAL CONTEXT: {enhanced_topic.get('social_context', 'N/A')}\n")
                f.write(f"RELATED SEARCHES: {', '.join(enhanced_topic.get('related_searches', []))}\n\n")
                f.write(f"TITLE: {story_package['title']}\n")
                f.write(f"DURATION: {story_package['estimated_duration']:.1f}s\n")
                f.write(f"MUSIC CATEGORY: {story_package['story_data']['music_category']}\n\n")
                f.write(f"STORY:\n{story_package['summary']}\n\n")
                f.write(f"IMAGE PROMPT:\n{story_package['image_prompt']}\n")
            
            print(f"\n💾 Story saved to: {story_file}")
        else:
            print(f"❌ Failed to generate story for: {topic}")
        
        print(f"\n{'-'*60}")
    
    print(f"\n🎉 COMPLETED: Generated stories for {len(trending_topics)} trending topics")
    print(f"📁 All stories saved to: {Config.OUTPUT_DIR / 'test_stories'}")

if __name__ == "__main__":
    test_all_trending_stories() 