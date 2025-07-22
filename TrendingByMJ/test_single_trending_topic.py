"""
Test Single Trending Topic Pipeline
Processes one trending topic through the complete pipeline to verify everything works
"""

import asyncio
import sys
import os
import json
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project components
from config import Config
from src.real_trending_fetcher import RealTrendingFetcher
from src.news_context_gatherer import NewsContextGatherer
from src.trending_summary_generator import TrendingSummaryGenerator
from trending_video_pipeline import create_trending_video

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

async def test_single_trending_topic():
    """Test the complete pipeline with one trending topic."""
    logger = setup_logging()
    
    print("🧪 TESTING SINGLE TRENDING TOPIC PIPELINE")
    print("=" * 60)
    
    # Step 1: Get one trending topic
    print("\n📊 Step 1: Fetching one trending topic...")
    fetcher = RealTrendingFetcher(logger)
    topics = fetcher.fetch_trending_topics()
    
    # Take only the first topic
    if topics:
        topics = topics[:1]
    
    if not topics:
        print("❌ No trending topics found!")
        return False
    
    topic = topics[0]
    print(f"✅ Found trending topic: {topic['topic']}")
    print(f"   • Search Volume: {topic.get('search_volume', 'Unknown')}")
    print(f"   • Trending Reason: {topic.get('trending_reason', 'Unknown')}")
    
    # Step 2: Gather news context
    print(f"\n📰 Step 2: Gathering news context for: {topic['topic']}")
    news_gatherer = NewsContextGatherer(logger)
    enhanced_topic = news_gatherer.gather_trending_context(topic['topic'])
    
    # Merge the enhanced topic data with the original topic data
    enhanced_topic.update(topic)
    
    print(f"✅ News context gathered:")
    print(f"   • Context: {enhanced_topic.get('context', 'No context')}")
    print(f"   • News articles found: {len(enhanced_topic.get('news_articles', []))}")
    
    # Step 3: Generate story
    print(f"\n📝 Step 3: Generating story for: {topic['topic']}")
    summary_generator = TrendingSummaryGenerator(logger)
    story_package = summary_generator.generate_summary_package(enhanced_topic)
    
    if not story_package:
        print("❌ Failed to generate story!")
        return False
    
    print(f"✅ Story generated:")
    print(f"   • Title: {story_package['story_data']['title']}")
    print(f"   • Duration: {story_package['estimated_duration']} seconds")
    print(f"   • Music: {story_package['story_data']['music_category']}")
    print(f"   • Story: {story_package['story_data']['story'][:100]}...")
    
    # Step 4: Create video using the full pipeline
    print(f"\n🎬 Step 4: Creating video using full pipeline...")
    print("This will run:")
    print("  • TTS Audio Generation")
    print("  • Whisper Audio Synchronization (6 images)")
    print("  • Music Selection")
    print("  • Image Generation (6 images with Schnell)")
    print("  • Audio Mixing (TTS + background music)")
    print("  • Video Composition (Ken Burns effects)")
    print("  • Final Video Output")
    
    success = await create_trending_video(
        topic_name=topic['topic'],
        story_package=story_package,
        logger=logger
    )
    
    if success:
        print(f"\n🎉 SUCCESS! Video created for: {topic['topic']}")
        print(f"📁 Check output folder for the final video")
        return True
    else:
        print(f"\n❌ FAILED! Video creation failed for: {topic['topic']}")
        return False

if __name__ == "__main__":
    asyncio.run(test_single_trending_topic()) 