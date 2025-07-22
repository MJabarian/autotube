"""
Approved Trending Pipeline
Shows trending topics with stories and asks for user approval before generating videos
Uses the EXACT same full pipeline as the original project
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

# Import the EXACT same pipeline components as the full pipeline
from partial_pipelines.content_generation_pipeline import test_complete_replicate_pipeline_whisper_with_story
from partial_pipelines.audio_video_processor_pipeline import process_video_for_topic
from src.real_trending_fetcher import RealTrendingFetcher
from src.news_context_gatherer import NewsContextGatherer
from src.trending_summary_generator import TrendingSummaryGenerator
from config import Config

def setup_logging():
    """Setup logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def get_user_approval(topic_name: str, story_package: dict) -> bool:
    """Show the topic and story to user and get approval."""
    print(f"\n{'='*80}")
    print(f"📊 TRENDING TOPIC: {topic_name.upper()}")
    print(f"{'='*80}")
    
    # Show trending info
    print(f"🔥 Trending Info:")
    print(f"   • Search Volume: {story_package.get('search_volume', 'Unknown')}")
    print(f"   • Trending Reason: {story_package.get('trending_reason', 'Unknown')}")
    
    # Show news context
    print(f"\n📰 News Context:")
    print(f"   {story_package.get('context', 'No context available')}")
    
    # Show generated story
    story_data = story_package['story_data']
    print(f"\n📝 Generated Story:")
    print(f"   Title: {story_data['title']}")
    print(f"   Story: {story_data['story']}")
    print(f"   Duration: {story_package['estimated_duration']} seconds")
    print(f"   Music: {story_data['music_category']}")
    
    print(f"\n{'='*80}")
    
    while True:
        choice = input("🤔 Do you want to generate a video for this topic? (y/n/q to quit): ").lower().strip()
        
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        elif choice == 'q':
            print("👋 Quitting pipeline...")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please enter y, n, or q.")

async def generate_full_pipeline_video(topic_name: str, story_package: dict, logger):
    """Generate video using the EXACT same full pipeline as the original project."""
    try:
        logger.info(f"🎬 Starting FULL PIPELINE for: {topic_name}")
        
        # Step 1: Content Generation Pipeline (TTS + Whisper Sync + 6 Images)
        logger.info(f"🔄 Step 1: Content Generation Pipeline")
        logger.info(f"   • TTS Audio Generation")
        logger.info(f"   • Whisper Audio Synchronization (6 images)")
        logger.info(f"   • Music Selection")
        logger.info(f"   • Image Generation (6 images with Schnell)")
        
        content_success = await test_complete_replicate_pipeline_whisper_with_story(
            story_data=story_package['story_data'],
            topic_name=topic_name,
            logger=logger
        )
        
        if not content_success:
            logger.error(f"❌ Content generation pipeline failed for: {topic_name}")
            return False
        
        logger.info(f"✅ Content generation pipeline completed successfully")
        
        # Step 2: Audio/Video Processing Pipeline (Audio Mixing + Ken Burns + Subtitles)
        logger.info(f"🔄 Step 2: Audio/Video Processing Pipeline")
        logger.info(f"   • Audio Mixing (TTS + background music)")
        logger.info(f"   • Video Composition (Ken Burns effects)")
        logger.info(f"   • Subtitle Processing")
        logger.info(f"   • Final Video Output")
        
        video_success = process_video_for_topic(topic_name, logger)
        
        if not video_success:
            logger.error(f"❌ Audio/video processing pipeline failed for: {topic_name}")
            return False
        
        logger.info(f"✅ Audio/video processing pipeline completed successfully")
        logger.info(f"🎉 FULL PIPELINE COMPLETED for: {topic_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in full pipeline for {topic_name}: {e}")
        return False

async def main():
    """Main function to process trending topics with user approval."""
    logger = setup_logging()
    
    print("🚀 APPROVED TRENDING PIPELINE")
    print("=" * 60)
    print("This will:")
    print("1. Get trending topics from Google Trends")
    print("2. Show each topic with its generated story")
    print("3. Ask for your approval before generating video")
    print("4. Run the EXACT same full pipeline as the original project:")
    print("   • TTS Audio Generation")
    print("   • Whisper Audio Synchronization (6 images)")
    print("   • Music Selection")
    print("   • Image Generation (6 images with Schnell)")
    print("   • Audio Mixing (TTS + background music)")
    print("   • Video Composition (Ken Burns effects)")
    print("   • Subtitle Processing")
    print("   • Final Video Output")
    print("=" * 60)
    
    # Get trending topics
    logger.info("📊 Fetching trending topics...")
    fetcher = RealTrendingFetcher(logger)
    topics = fetcher.fetch_trending_topics()
    
    if not topics:
        logger.error("❌ No trending topics found!")
        return
    
    logger.info(f"✅ Found {len(topics)} trending topics")
    
    # Process each topic with user approval
    successful_videos = 0
    skipped_videos = 0
    
    for i, topic_data in enumerate(topics, 1):
        topic_name = topic_data['topic']
        
        print(f"\n{'='*80}")
        print(f"📊 PROCESSING TOPIC {i}/{len(topics)}: {topic_name.upper()}")
        print(f"{'='*80}")
        
        try:
            # Step 1: Get news context
            logger.info(f"📰 Getting news context for: {topic_name}")
            news_gatherer = NewsContextGatherer(logger)
            enhanced_topic = news_gatherer.gather_trending_context({"topic": topic_name, **topic_data})
            
            # Step 2: Generate story
            logger.info(f"📝 Generating story for: {topic_name}")
            summary_generator = TrendingSummaryGenerator(logger)
            story_package = summary_generator.generate_trending_summary(enhanced_topic)
            
            if not story_package:
                logger.error(f"❌ Failed to generate story for: {topic_name}")
                skipped_videos += 1
                continue
            
            # Step 3: Get user approval
            approved = get_user_approval(topic_name, story_package)
            
            if approved:
                # Step 4: Generate video using the EXACT full pipeline
                logger.info(f"🎬 User approved! Starting full pipeline for: {topic_name}")
                success = await generate_full_pipeline_video(topic_name, story_package, logger)
                
                if success:
                    successful_videos += 1
                    print(f"✅ Video created successfully for: {topic_name}")
                    
                    # Mark topic as used
                    fetcher.mark_topic_used(topic_name)
                else:
                    print(f"❌ Failed to create video for: {topic_name}")
            else:
                skipped_videos += 1
                print(f"⏭️ Skipped video generation for: {topic_name}")
                
        except Exception as e:
            logger.error(f"❌ Error processing {topic_name}: {e}")
            skipped_videos += 1
        
        # Small delay between topics
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 PIPELINE COMPLETED")
    print(f"{'='*80}")
    print(f"✅ Successful videos: {successful_videos}")
    print(f"⏭️ Skipped videos: {skipped_videos}")
    print(f"📊 Total topics: {len(topics)}")
    print(f"{'='*80}")
    
    if successful_videos > 0:
        print(f"🎉 Successfully created {successful_videos} videos!")
        print(f"📁 Check the output folder for your videos")
    else:
        print(f"ℹ️ No videos were created")

if __name__ == "__main__":
    asyncio.run(main()) 