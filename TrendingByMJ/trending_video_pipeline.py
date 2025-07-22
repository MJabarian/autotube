"""
TrendingByMJ Video Pipeline
Creates videos from pre-generated trending stories using the existing pipeline components
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project-specific config
from config import Config, PATHS

# Import pipeline components
from partial_pipelines.content_generation_pipeline import test_complete_replicate_pipeline_whisper_with_story
from partial_pipelines.audio_video_processor_pipeline import process_video_for_topic
from src.utils.folder_utils import sanitize_folder_name

class TrendingVideoPipeline:
    """Pipeline to create videos from pre-generated trending stories."""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.step_timings = {}
        
        # Setup logging if not provided
        if self.logger is None:
            self.logger = self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for the trending video pipeline."""
        # Create logs directory
        logs_dir = Config.LOGS_DIR
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"trending_video_pipeline_{timestamp}.log"
        log_path = logs_dir / log_filename
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        self.logger = logging.getLogger("trendingbyMJ.video_pipeline")
        self.logger.info(f"🚀 Starting TrendingByMJ Video Pipeline")
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
    
    async def create_video_from_story(self, topic_name: str, story_package: dict) -> bool:
        """Create video from pre-generated story data."""
        try:
            self.logger.info(f"🎬 Creating video for trending topic: {topic_name}")
            
            # Step 1: Save story data (required by the pipeline)
            self.log_step_start("Story Data Setup")
            
            story_data = story_package['story_data']
            sanitized_name = sanitize_folder_name(topic_name)
            
            # Create story directory
            story_dir = Config.STORIES_DIR / sanitized_name
            story_dir.mkdir(parents=True, exist_ok=True)
            
            # Save story data
            story_file = story_dir / "story.json"
            with open(story_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 Story data saved: {story_file}")
            self.log_step_end("Story Data Setup", success=True)
            
            # Step 2: Content Generation (TTS + Images)
            self.log_step_start("Content Generation")
            
            # Run the content generation pipeline with pre-generated story data
            content_success = await test_complete_replicate_pipeline_whisper_with_story(
                story_data=story_data,
                topic_name=topic_name,
                logger=self.logger
            )
            
            if not content_success:
                self.logger.error(f"❌ Content generation failed for: {topic_name}")
                self.log_step_end("Content Generation", success=False)
                return False
            
            self.log_step_end("Content Generation", success=True)
            
            # Step 3: Audio/Video Processing
            self.log_step_start("Audio/Video Processing")
            
            # Run the audio/video processing pipeline
            video_success = process_video_for_topic(
                topic_name=topic_name,
                logger=self.logger
            )
            
            if not video_success:
                self.logger.error(f"❌ Video processing failed for: {topic_name}")
                self.log_step_end("Audio/Video Processing", success=False)
                return False
            
            self.log_step_end("Audio/Video Processing", success=True)
            
            # Success!
            self.logger.info(f"✅ Video created successfully for: {topic_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creating video for {topic_name}: {e}")
            return False

async def create_trending_video(topic_name: str, story_package: dict, logger=None) -> bool:
    """Convenience function to create a video from trending story data."""
    pipeline = TrendingVideoPipeline(logger)
    return await pipeline.create_video_from_story(topic_name, story_package)

if __name__ == "__main__":
    # Test the pipeline
    async def test():
        pipeline = TrendingVideoPipeline()
        
        # Test with sample data
        test_story_package = {
            'story_data': {
                'title': 'Test Trending Story',
                'story': 'This is a test story for the trending video pipeline.',
                'music_category': 'Uplifting'
            }
        }
        
        success = pipeline.create_video_from_story("test_topic", test_story_package)
        print(f"Test result: {'✅ Success' if success else '❌ Failed'}")
    
    asyncio.run(test()) 