"""
TrendingByMJ Full Pipeline
Complete pipeline for trending topics: Google Trends → Summary → Video Generation
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project-specific config
from config import Config, PATHS

# Import trending components
from src.real_trending_fetcher import RealTrendingFetcher as TrendingFetcher
from src.trending_summary_generator import TrendingSummaryGenerator

# Import pipeline components
from partial_pipelines.content_generation_pipeline import test_complete_replicate_pipeline_whisper
from partial_pipelines.audio_video_processor_pipeline import process_video_for_topic
from src.utils.folder_utils import sanitize_folder_name, setup_logging_with_file

class TrendingFullPipeline:
    """Complete TrendingByMJ pipeline from Google Trends to final video."""
    
    def __init__(self, logger=None):
        self.start_time = None
        self.step_timings = {}
        self.logger = logger
        self.trending_topics = []
        self.summary_packages = []
        
        # Setup logging if not provided
        if self.logger is None:
            self.logger = self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the trending pipeline."""
        # Create fp_logs directory
        fp_logs_dir = Config.LOGS_DIR
        fp_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"trending_pipeline_{timestamp}.log"
        log_path = fp_logs_dir / log_filename
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        self.logger = logging.getLogger("trendingbyMJ.full_pipeline")
        self.logger.info(f"🚀 Starting TrendingByMJ Full Pipeline")
        self.logger.info(f"📝 Log file: {log_path}")
        
        return self.logger
    
    def log_step_start(self, step_name: str):
        """Log the start of a pipeline step."""
        step_start = time.time()
        self.step_timings[step_name] = {"start": step_start}
        self.logger.info(f"🔄 Starting: {step_name}")
        print(f"\n🔄 [{step_name}] Starting...")
        
    def log_step_end(self, step_name: str, success: bool = True):
        """Log the end of a pipeline step with timing."""
        step_end = time.time()
        if step_name in self.step_timings:
            duration = step_end - self.step_timings[step_name]["start"]
            self.step_timings[step_name]["end"] = step_end
            self.step_timings[step_name]["duration"] = duration
            self.step_timings[step_name]["success"] = success
            
            status = "✅" if success else "❌"
            self.logger.info(f"{status} Completed: {step_name} ({duration:.2f}s)")
            print(f"{status} [{step_name}] Completed in {duration:.2f}s")
        else:
            self.logger.warning(f"⚠️ Step timing not found for: {step_name}")
    
    def get_step_timing(self, step_name: str) -> float:
        """Get the duration of a specific step."""
        if step_name in self.step_timings:
            return self.step_timings[step_name].get("duration", 0)
        return 0
    
    def save_pipeline_report(self):
        """Save a comprehensive pipeline report."""
        if not self.trending_topics:
            self.logger.error("❌ No trending topics available for report")
            return
        
        # Create report data
        total_time = time.time() - self.start_time
        
        report_data = {
            "pipeline_info": {
                "name": "TrendingByMJ Full Pipeline",
                "timestamp": datetime.now().isoformat(),
                "total_duration": total_time,
                "trending_topics_count": len(self.trending_topics),
                "successful_videos": len([s for s in self.step_timings.values() if s.get("success", False)])
            },
            "step_timings": self.step_timings,
            "trending_topics": [
                {
                    "topic": topic["topic"],
                    "search_volume": topic["search_volume"],
                    "context": topic.get("context", "")
                }
                for topic in self.trending_topics
            ],
            "summary_packages": [
                {
                    "topic": summary["topic"],
                    "title": summary["title"],
                    "estimated_duration": summary["estimated_duration"]
                }
                for summary in self.summary_packages
            ]
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Config.LOGS_DIR / f"trending_pipeline_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"📊 Pipeline report saved: {report_file}")
        except Exception as e:
            self.logger.error(f"❌ Error saving pipeline report: {e}")
    
    async def fetch_trending_topics(self) -> bool:
        """Step 1: Fetch trending topics from Google Trends."""
        try:
            self.log_step_start("Fetch Trending Topics")
            
            # Initialize trending fetcher
            fetcher = TrendingFetcher(self.logger)
            
            # Fetch trending topics
            self.trending_topics = fetcher.fetch_trending_topics()
            
            if not self.trending_topics:
                self.logger.error("❌ No trending topics found")
                self.log_step_end("Fetch Trending Topics", success=False)
                return False
            
            # Log trending topics
            self.logger.info(f"📊 Found {len(self.trending_topics)} trending topics:")
            for i, topic in enumerate(self.trending_topics, 1):
                self.logger.info(f"  {i}. {topic['topic']} (Volume: {topic['search_volume']})")
            
            self.log_step_end("Fetch Trending Topics", success=True)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in fetch_trending_topics: {e}")
            self.log_step_end("Fetch Trending Topics", success=False)
            return False
    
    async def generate_summaries(self) -> bool:
        """Step 2: Generate summaries for trending topics with interactive approval."""
        try:
            self.log_step_start("Generate Summaries")
            
            # Initialize summary generator
            generator = TrendingSummaryGenerator(self.logger)
            
            # Generate summaries for all topics
            self.summary_packages = generator.generate_multiple_summaries(self.trending_topics)
            
            if not self.summary_packages:
                self.logger.error("❌ No summaries generated")
                self.log_step_end("Generate Summaries", success=False)
                return False
            
            # Interactive approval for each summary
            approved_summaries = []
            
            for i, summary_package in enumerate(self.summary_packages, 1):
                topic = summary_package["topic"]
                title = summary_package["title"]
                summary = summary_package["summary"]
                duration = summary_package["estimated_duration"]
                
                # Check for sensitive content
                topic_data = next((t for t in self.trending_topics if t["topic"] == topic), None)
                if topic_data and topic_data.get("sensitivity_level") == "high":
                    print(f"\n{'='*80}")
                    print(f"⚠️  SENSITIVE CONTENT DETECTED: {topic.upper()}")
                    print(f"{'='*80}")
                    print(f"📰 This topic involves sensitive content: {topic_data.get('trending_reason', 'N/A')}")
                    print(f"🎯 Recommended approach: {topic_data.get('content_approach', 'skip')}")
                    print(f"\n❓ Do you want to skip this sensitive topic? (y/n): ", end="")
                    
                    skip_sensitive = input().lower().strip()
                    if skip_sensitive in ['y', 'yes']:
                        print(f"⏭️ SKIPPED SENSITIVE TOPIC: {topic}")
                        continue
                    else:
                        print(f"⚠️  Proceeding with sensitive topic: {topic}")
                        print(f"💡 Please ensure content is respectful and appropriate")
                
                print(f"\n{'='*80}")
                print(f"📰 STORY #{i}: {topic.upper()}")
                print(f"{'='*80}")
                print(f"📊 Search Volume: {summary_package['search_volume']}")
                print(f"⏱️ Estimated Duration: {duration:.1f}s")
                print(f"🎵 Music Category: {summary_package['story_data']['music_category']}")
                print(f"\n📝 TITLE: {title}")
                print(f"\n📰 STORY CONTENT:")
                print(f"{summary}")
                print(f"\n🎨 IMAGE PROMPT:")
                print(f"{summary_package['image_prompt'][:200]}...")
                print(f"{'='*80}")
                
                # Get user approval
                while True:
                    approval = input(f"\n❓ Do you approve this story for '{topic}'? (y/n/skip): ").lower().strip()
                    if approval in ['y', 'yes']:
                        approved_summaries.append(summary_package)
                        print(f"✅ APPROVED: {topic}")
                        break
                    elif approval in ['n', 'no']:
                        print(f"❌ REJECTED: {topic} - Moving to next topic")
                        break
                    elif approval in ['s', 'skip']:
                        print(f"⏭️ SKIPPED: {topic} - Moving to next topic")
                        break
                    else:
                        print("Please enter 'y' (yes), 'n' (no), or 's' (skip)")
                
                print(f"\n📊 Progress: {len(approved_summaries)} approved, {i}/{len(self.summary_packages)} reviewed")
            
            # Update summary packages to only include approved ones
            self.summary_packages = approved_summaries
            
            if not self.summary_packages:
                self.logger.error("❌ No summaries approved by user")
                self.log_step_end("Generate Summaries", success=False)
                return False
            
            # Save approved summaries
            summaries_dir = Config.OUTPUT_DIR / "summaries"
            generator.save_summaries(self.summary_packages, summaries_dir)
            
            # Log approved summary packages
            self.logger.info(f"📝 User approved {len(self.summary_packages)} summary packages:")
            for i, summary in enumerate(self.summary_packages, 1):
                self.logger.info(f"  {i}. {summary['title']} ({summary['estimated_duration']:.1f}s)")
            
            self.log_step_end("Generate Summaries", success=True)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in generate_summaries: {e}")
            self.log_step_end("Generate Summaries", success=False)
            return False
    
    async def create_videos(self) -> bool:
        """Step 3: Create videos for each trending topic."""
        try:
            self.log_step_start("Create Videos")
            
            successful_videos = 0
            
            for i, summary_package in enumerate(self.summary_packages, 1):
                topic = summary_package["topic"]
                title = summary_package["title"]
                
                self.logger.info(f"🎬 Creating video {i}/{len(self.summary_packages)}: {title}")
                
                try:
                    # Use story data from summary package (compatible with existing pipeline)
                    story_data = summary_package["story_data"]
                    
                    # Save story data for content generation pipeline
                    story_dir = Config.STORIES_DIR / sanitize_folder_name(topic)
                    story_dir.mkdir(parents=True, exist_ok=True)
                    
                    story_file = story_dir / "story.json"
                    with open(story_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, indent=2, ensure_ascii=False)
                    
                    self.logger.info(f"📄 Story data saved: {story_file}")
                    self.logger.info(f"🎵 Music category: {story_data.get('music_category', 'Unknown')}")
                    
                    # Run content generation pipeline with story data
                    content_success = await test_complete_replicate_pipeline_whisper(
                        topic_name=topic,
                        logger=self.logger
                    )
                    
                    if content_success:
                        # Run audio/video processing pipeline
                        video_success = process_video_for_topic(
                            topic_name=topic,
                            logger=self.logger
                        )
                        
                        if video_success:
                            successful_videos += 1
                            self.logger.info(f"✅ Video created successfully: {title}")
                            
                            # Mark topic as used in history
                            from src.real_trending_fetcher import RealTrendingFetcher
                            fetcher = RealTrendingFetcher(self.logger)
                            fetcher.mark_topic_used(topic)
                        else:
                            self.logger.error(f"❌ Video processing failed: {title}")
                    else:
                        self.logger.error(f"❌ Content generation failed: {title}")
                
                except Exception as e:
                    self.logger.error(f"❌ Error creating video for {topic}: {e}")
                
                # Rate limiting between videos
                if i < len(self.summary_packages):
                    time.sleep(5)
            
            self.logger.info(f"🎬 Video creation completed: {successful_videos}/{len(self.summary_packages)} successful")
            
            success = successful_videos > 0
            self.log_step_end("Create Videos", success=success)
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in create_videos: {e}")
            self.log_step_end("Create Videos", success=False)
            return False
    
    def create_video_for_single_topic(self, topic_data: dict, story_package: dict) -> bool:
        """Create video for a single topic (synchronous version for interactive pipeline)."""
        try:
            self.logger.info(f"🎬 Creating video for single topic: {topic_data['topic']}")
            
            # Create a temporary summary package for the pipeline
            summary_package = {
                'topic': topic_data['topic'],
                'story_data': story_package['story_data'],
                'estimated_duration': story_package['estimated_duration'],
                'search_volume': topic_data.get('search_volume', 1000),
                'context': topic_data.get('context', ''),
                'news_context': topic_data.get('news_context', '')
            }
            
            # Save story data for content generation pipeline
            topic = topic_data['topic']
            story_data = story_package['story_data']
            
            story_dir = Config.STORIES_DIR / sanitize_folder_name(topic)
            story_dir.mkdir(parents=True, exist_ok=True)
            
            story_file = story_dir / "story.json"
            with open(story_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 Story data saved: {story_file}")
            self.logger.info(f"🎵 Music category: {story_data.get('music_category', 'Unknown')}")
            
            # Run content generation pipeline with story data
            content_success = test_complete_replicate_pipeline_whisper(
                topic_name=topic,
                logger=self.logger
            )
            
            if content_success:
                # Run audio/video processing pipeline
                video_success = process_video_for_topic(
                    topic_name=topic,
                    logger=self.logger
                )
                
                if video_success:
                    self.logger.info(f"✅ Video created successfully: {topic}")
                    
                    # Mark topic as used in history
                    from src.real_trending_fetcher import RealTrendingFetcher
                    fetcher = RealTrendingFetcher(self.logger)
                    fetcher.mark_topic_used(topic)
                    
                    return True
                else:
                    self.logger.error(f"❌ Video processing failed: {topic}")
                    return False
            else:
                self.logger.error(f"❌ Content generation failed: {topic}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error creating video for {topic_data['topic']}: {e}")
            return False
    
    async def run_full_pipeline(self) -> bool:
        """Run the complete TrendingByMJ pipeline."""
        try:
            self.start_time = time.time()
            self.logger.info("🚀 Starting TrendingByMJ Full Pipeline")
            
            print("\n" + "="*60)
            print("🚀 TRENDING BY MJ - FULL PIPELINE")
            print("="*60)
            
            # Step 1: Fetch trending topics
            if not await self.fetch_trending_topics():
                self.logger.error("❌ Pipeline failed at step 1: Fetch Trending Topics")
                return False
            
            # Step 2: Generate summaries
            if not await self.generate_summaries():
                self.logger.error("❌ Pipeline failed at step 2: Generate Summaries")
                return False
            
            # Step 3: Create videos
            if not await self.create_videos():
                self.logger.error("❌ Pipeline failed at step 3: Create Videos")
                return False
            
            # Save pipeline report
            self.save_pipeline_report()
            
            # Final summary
            total_time = time.time() - self.start_time
            self.logger.info(f"🎉 TrendingByMJ Pipeline completed successfully!")
            self.logger.info(f"⏱️ Total time: {total_time:.2f} seconds")
            self.logger.info(f"📊 Processed {len(self.trending_topics)} trending topics")
            self.logger.info(f"📝 Generated {len(self.summary_packages)} summaries")
            
            print("\n" + "="*60)
            print("🎉 TRENDING BY MJ - PIPELINE COMPLETED!")
            print("="*60)
            print(f"⏱️ Total time: {total_time:.2f} seconds")
            print(f"📊 Trending topics: {len(self.trending_topics)}")
            print(f"📝 Summaries generated: {len(self.summary_packages)}")
            print(f"🎬 Videos created: {len([s for s in self.step_timings.values() if s.get('success', False)])}")
            print("="*60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Critical error in full pipeline: {e}")
            return False

async def main():
    """Main entry point for TrendingByMJ pipeline."""
    try:
        # Initialize pipeline
        pipeline = TrendingFullPipeline()
        pipeline.setup_logging()
        
        # Run pipeline
        success = await pipeline.run_full_pipeline()
        
        if success:
            print("\n✅ TrendingByMJ pipeline completed successfully!")
            return 0
        else:
            print("\n❌ TrendingByMJ pipeline failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 