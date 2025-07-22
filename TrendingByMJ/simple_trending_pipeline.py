"""
Simple Trending Pipeline
Gets trending topics and generates videos using the full pipeline
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

# Import the full pipeline components
from partial_pipelines.content_generation_pipeline import test_complete_replicate_pipeline_whisper_with_story
from partial_pipelines.audio_video_processor_pipeline import process_video_for_topic
from src.real_trending_fetcher import RealTrendingFetcher
from src.news_context_gatherer import NewsContextGatherer
from src.trending_summary_generator import TrendingSummaryGenerator
from src.utils.folder_utils import sanitize_folder_name
from config import Config

def setup_logging():
    """Setup logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

async def generate_video_for_trending_topic(topic_name: str, logger):
    """Generate video for a single trending topic using the full pipeline."""
    try:
        logger.info(f"🎬 Starting video generation for: {topic_name}")
        
        # Step 1: Get news context
        logger.info(f"📰 Getting news context for: {topic_name}")
        news_gatherer = NewsContextGatherer(logger)
        enhanced_topic = news_gatherer.gather_trending_context(topic_name)
        
        # Step 2: Generate story
        logger.info(f"📝 Generating story for: {topic_name}")
        summary_generator = TrendingSummaryGenerator(logger)
        story_package = summary_generator.generate_summary_package(enhanced_topic)
        
        if not story_package:
            logger.error(f"❌ Failed to generate story for: {topic_name}")
            return False
        
        logger.info(f"✅ Story generated: {story_package['story_data']['title']}")
        
        # Step 3: Run content generation pipeline (TTS + Images)
        logger.info(f"🔊 Running content generation pipeline...")
        content_success = await test_complete_replicate_pipeline_whisper_with_story(
            story_data=story_package['story_data'],
            topic_name=topic_name,
            logger=logger
        )
        
        if not content_success:
            logger.error(f"❌ Content generation failed for: {topic_name}")
            return False
        
        # Step 4: Run audio/video processing pipeline
        logger.info(f"🎬 Running audio/video processing pipeline...")
        video_success = process_video_for_topic(topic_name, logger)
        
        if not video_success:
            logger.error(f"❌ Video processing failed for: {topic_name}")
            return False
        
        logger.info(f"✅ Video generated successfully for: {topic_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating video for {topic_name}: {e}")
        return False

async def main():
    """Main function to process trending topics."""
    logger = setup_logging()
    
    print("🚀 SIMPLE TRENDING PIPELINE")
    print("=" * 50)
    print("This will:")
    print("1. Get trending topics from Google Trends")
    print("2. Generate videos for each topic using the full pipeline")
    print("3. Save videos to output folder")
    print("=" * 50)
    
    # Get trending topics
    logger.info("📊 Fetching trending topics...")
    fetcher = RealTrendingFetcher(logger)
    topics = fetcher.fetch_trending_topics()
    
    if not topics:
        logger.error("❌ No trending topics found!")
        return
    
    logger.info(f"✅ Found {len(topics)} trending topics")
    
    # Process each topic
    successful_videos = 0
    
    for i, topic_data in enumerate(topics, 1):
        topic_name = topic_data['topic']
        
        print(f"\n{'='*60}")
        print(f"📊 PROCESSING TOPIC {i}/{len(topics)}: {topic_name.upper()}")
        print(f"{'='*60}")
        
        # Generate video for this topic
        success = await generate_video_for_trending_topic(topic_name, logger)
        
        if success:
            successful_videos += 1
            print(f"✅ Video created for: {topic_name}")
            
            # Mark topic as used
            fetcher.mark_topic_used(topic_name)
        else:
            print(f"❌ Failed to create video for: {topic_name}")
        
        # Small delay between topics
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 PIPELINE COMPLETED")
    print(f"{'='*60}")
    print(f"✅ Successful videos: {successful_videos}")
    print(f"❌ Failed videos: {len(topics) - successful_videos}")
    print(f"📊 Total topics: {len(topics)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main()) 