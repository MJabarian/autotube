#!/usr/bin/env python3
"""
Interactive Trending Pipeline
Shows top 20 Google Trends topics with news context and lets user choose which to process
"""

import sys
import os
import json
from pathlib import Path
import logging
from typing import List, Dict, Any
import time

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from src.real_trending_fetcher import RealTrendingFetcher
from src.news_context_gatherer import NewsContextGatherer
from src.trending_summary_generator import TrendingSummaryGenerator

def setup_logging():
    """Setup logging for the pipeline."""
    # Use simple logging without Unicode characters to avoid encoding issues
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Config.LOGS_DIR / "interactive_pipeline.log", encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def get_top_20_trending_topics(logger) -> List[Dict[str, Any]]:
    """Get top 20 trending topics from Google Trends."""
    logger.info("🔍 Fetching top 20 Google Trends topics...")
    
    fetcher = RealTrendingFetcher(logger)
    topics = fetcher.fetch_trending_topics()
    
    if not topics:
        logger.error("❌ No trending topics found!")
        return []
    
    logger.info(f"✅ Found {len(topics)} trending topics")
    return topics

def gather_news_context_for_single_topic(topic: Dict[str, Any], logger) -> Dict[str, Any]:
    """Gather news context for a single trending topic."""
    logger.info(f"📰 Gathering news context for: {topic['topic']}")
    
    try:
        news_gatherer = NewsContextGatherer(logger)
        enhanced_topic = news_gatherer.gather_trending_context(topic['topic'])
        return enhanced_topic
        
    except Exception as e:
        logger.error(f"❌ Error gathering news for {topic['topic']}: {e}")
        return topic  # Use original topic if news gathering fails

def generate_story_for_topic(topic: Dict[str, Any], logger) -> Dict[str, Any]:
    """Generate a story for a trending topic."""
    logger.info(f"📝 Generating story for: {topic['topic']}")
    
    try:
        generator = TrendingSummaryGenerator(logger)
        story_package = generator.generate_trending_summary(topic)
        return story_package
    except Exception as e:
        logger.error(f"❌ Error generating story for {topic['topic']}: {e}")
        return None

def display_topic_with_context(topic: Dict[str, Any], story_package: Dict[str, Any], index: int, total: int):
    """Display a topic with its news context and generated story."""
    print(f"\n{'='*80}")
    print(f"📊 TOPIC #{index} OF {total}: {topic['topic'].upper()}")
    print(f"{'='*80}")
    
    # Display trending info
    print(f"🔥 Trending Info:")
    print(f"   • Search Volume: {topic.get('search_volume', 'Unknown'):,}")
    print(f"   • Trending Reason: {topic.get('trending_reason', 'Unknown')}")
    print(f"   • Context: {topic.get('context', 'Unknown')}")
    
    # Display news context
    if 'news_context' in topic and topic['news_context']:
        print(f"\n📰 News Context:")
        print(f"   {topic['news_context']}")
    
    # Display generated story
    if story_package and 'story_data' in story_package:
        story_data = story_package['story_data']
        print(f"\n📝 Generated Story:")
        print(f"   Title: {story_data.get('title', 'No title')}")
        
        # Show the actual story content
        if 'story' in story_data:
            print(f"   Story: {story_data['story']}")
        elif 'summary' in story_data and story_data['summary'] != 'No summary':
            print(f"   Summary: {story_data['summary']}")
        else:
            print(f"   Story: [Story content not available]")
            
        # Also show the main summary if it's different from story
        if 'summary' in story_package and story_package['summary'] != story_data.get('story', ''):
            print(f"   Main Summary: {story_package['summary']}")
            
        print(f"   Estimated Duration: {story_package.get('estimated_duration', 'Unknown')} seconds")
        print(f"   Music Category: {story_data.get('music_category', 'Unknown')}")
        
        # Show image prompts
        if 'image_prompts' in story_data:
            print(f"\n🖼️  Image Prompts (6 images):")
            for i, prompt in enumerate(story_data['image_prompts'][:6], 1):
                print(f"   {i}. {prompt}")
    
    print(f"\n{'='*80}")

def get_user_choice(topic: Dict[str, Any]) -> str:
    """Get user choice for a topic."""
    while True:
        print(f"\n🤔 Do you want to make a video about '{topic['topic']}'?")
        print("   [y] Yes - Make video")
        print("   [n] No - Skip this topic")
        print("   [s] Skip all remaining topics")
        print("   [q] Quit pipeline")
        
        choice = input("\nEnter your choice (y/n/s/q): ").lower().strip()
        
        if choice in ['y', 'n', 's', 'q']:
            return choice
        else:
            print("❌ Invalid choice. Please enter y, n, s, or q.")

async def process_single_topic_video(topic: Dict[str, Any], story_package: Dict[str, Any], logger):
    """Process a single topic to generate video using the trending-specific pipeline."""
    logger.info(f"🎬 Processing video for: {topic['topic']}")
    
    try:
        # Import the trending-specific video pipeline
        from trending_video_pipeline import create_trending_video
        
        logger.info(f"✅ Processing video for: {topic['topic']}")
        logger.info(f"   - Title: {story_package['story_data']['title']}")
        logger.info(f"   - Duration: {story_package['estimated_duration']} seconds")
        logger.info(f"   - Music: {story_package['story_data']['music_category']}")
        
        # Use the trending-specific video pipeline
        success = await create_trending_video(
            topic_name=topic['topic'],
            story_package=story_package,
            logger=logger
        )
        
        if success:
            print(f"✅ Video generated and saved for: {topic['topic']}")
            
            # Mark topic as used in history
            from src.real_trending_fetcher import RealTrendingFetcher
            fetcher = RealTrendingFetcher(logger)
            fetcher.mark_topic_used(topic['topic'])
        else:
            print(f"❌ Failed to generate video for: {topic['topic']}")
        
    except Exception as e:
        logger.error(f"❌ Error processing video for {topic['topic']}: {e}")
        print(f"❌ Failed to generate video for: {topic['topic']}")
        return False
    
    return True

async def main():
    """Main interactive pipeline."""
    logger = setup_logging()
    
    print("🚀 INTERACTIVE TRENDING PIPELINE")
    print("=" * 50)
    print("This pipeline will:")
    print("1. Fetch top 20 Google Trends topics")
    print("2. For each topic:")
    print("   - Gather news context")
    print("   - Generate story")
    print("   - Show you and ask for confirmation")
    print("   - If confirmed: Generate video and save")
    print("   - If not confirmed: Move to next topic")
    print("3. Repeat for all trending topics")
    print("=" * 50)
    
    # Step 1: Get top 20 trending topics
    topics = get_top_20_trending_topics(logger)
    if not topics:
        print("❌ No trending topics found. Exiting.")
        return
    
    print(f"\n✅ Found {len(topics)} trending topics. Starting individual processing...")
    
    # Step 2: Process each topic individually
    processed_count = 0
    skipped_count = 0
    
    for i, topic in enumerate(topics, 1):
        print(f"\n{'='*80}")
        print(f"📊 PROCESSING TOPIC {i} OF {len(topics)}: {topic['topic'].upper()}")
        print(f"{'='*80}")
        
        # Step 2a: Gather news context for this topic
        print(f"📰 Gathering news context for: {topic['topic']}")
        enhanced_topic = gather_news_context_for_single_topic(topic, logger)
        
        # Step 2b: Generate story for this topic
        print(f"📝 Generating story for: {topic['topic']}")
        story_package = generate_story_for_topic(enhanced_topic, logger)
        if not story_package:
            print(f"❌ Failed to generate story for {topic['topic']}. Skipping to next topic.")
            skipped_count += 1
            continue
        
        # Step 2c: Display topic with context and story
        display_topic_with_context(enhanced_topic, story_package, i, len(topics))
        
        # Step 2d: Get user choice
        choice = get_user_choice(enhanced_topic)
        
        if choice == 'y':
            # User wants to make a video - process it immediately
            print(f"🎬 Processing video for: {topic['topic']}")
            await process_single_topic_video(enhanced_topic, story_package, logger)
            processed_count += 1
            
        elif choice == 'n':
            # User wants to skip this topic
            print(f"⏭️ Skipping '{topic['topic']}'. Moving to next topic.")
            skipped_count += 1
            
        elif choice == 's':
            # User wants to skip all remaining topics
            print(f"⏭️ Skipping all remaining topics.")
            break
            
        elif choice == 'q':
            # User wants to quit
            print(f"👋 Quitting pipeline.")
            break
    
    # Step 3: Summary
    print(f"\n{'='*80}")
    print(f"📊 PIPELINE SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Topics processed: {processed_count}")
    print(f"⏭️ Topics skipped: {skipped_count}")
    print(f"📊 Total topics: {len(topics)}")
    print(f"{'='*80}")
    
    if processed_count > 0:
        print(f"🎉 Successfully processed {processed_count} videos!")
    else:
        print(f"ℹ️ No videos were processed.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 