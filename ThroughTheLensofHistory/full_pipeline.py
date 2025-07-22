"""
AutoTube Full Pipeline - Complete Content Generation to Final Video
Runs both content generation and audio/video processing in one seamless pipeline
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

# Import pipeline components
from content_generation_pipeline import test_complete_replicate_pipeline_whisper
from audio_video_processor_pipeline import process_video_for_topic
from src.utils.folder_utils import sanitize_folder_name, setup_logging_with_file

class FullPipeline:
    """Complete AutoTube pipeline from story generation to final video."""
    
    def __init__(self):
        self.start_time = None
        self.step_timings = {}
        self.logger = None
        self.story_title = None
        self.sanitized_title = None
        
    def setup_logging(self):
        """Setup logging for the full pipeline."""
        # Create fp_logs directory
        fp_logs_dir = Config.OUTPUT_DIR / "fp_logs"
        fp_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"full_pipeline_{timestamp}.log"
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
        
        self.logger = logging.getLogger("autotube.full_pipeline")
        self.logger.info(f"🚀 Starting AutoTube Full Pipeline")
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
        if not self.story_title:
            self.logger.error("❌ No story title available for report")
            return
        
        # Create report data
        total_time = time.time() - self.start_time
        successful_steps = sum(1 for step in self.step_timings.values() if step.get("success", False))
        total_steps = len(self.step_timings)
        
        report = {
            "pipeline_info": {
                "story_title": self.story_title,
                "sanitized_title": self.sanitized_title,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_duration": total_time,
                "successful_steps": successful_steps,
                "total_steps": total_steps,
                "success_rate": f"{(successful_steps/total_steps)*100:.1f}%" if total_steps > 0 else "0%"
            },
            "step_timings": self.step_timings,
            "output_files": self._get_output_files(),
            "pipeline_status": "SUCCESS" if successful_steps == total_steps else "PARTIAL_SUCCESS" if successful_steps > 0 else "FAILED"
        }
        
        # Save report
        fp_logs_dir = Config.OUTPUT_DIR / "fp_logs"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"pipeline_report_{self.sanitized_title}_{timestamp}.json"
        report_path = fp_logs_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📊 Pipeline report saved: {report_path}")
        return report_path
    
    def _get_output_files(self) -> dict:
        """Get list of output files created during the pipeline."""
        if not self.sanitized_title:
            return {}
        
        output_files = {}
        
        # Check for story files
        story_dir = Config.OUTPUT_DIR / "stories" / self.sanitized_title
        if story_dir.exists():
            output_files["story_files"] = [str(f) for f in story_dir.glob("*")]
        
        # Check for audio files
        audio_dir = Config.OUTPUT_DIR / "audio" / self.sanitized_title
        if audio_dir.exists():
            output_files["audio_files"] = [str(f) for f in audio_dir.glob("*")]
        
        # Check for mixed audio
        mixed_audio_dir = Config.OUTPUT_DIR / "mixed_audio" / self.sanitized_title
        if mixed_audio_dir.exists():
            output_files["mixed_audio_files"] = [str(f) for f in mixed_audio_dir.glob("*")]
        
        # Check for images
        images_dir = Config.OUTPUT_DIR / "images" / self.sanitized_title
        if images_dir.exists():
            output_files["image_files"] = [str(f) for f in images_dir.glob("*")]
        
        # Check for videos
        videos_dir = Config.OUTPUT_DIR / "videos"
        video_file = videos_dir / f"{self.sanitized_title}_kenburns.mp4"
        if video_file.exists():
            output_files["kenburns_video"] = str(video_file)
        
        # Check for final video
        final_video_dir = Config.OUTPUT_DIR / "subtitles_processed_video"
        final_video_file = final_video_dir / f"{self.sanitized_title}_final.mp4"
        if final_video_file.exists():
            output_files["final_video"] = str(final_video_file)
        
        return output_files
    
    async def run_content_generation(self) -> bool:
        """Run the content generation pipeline."""
        try:
            self.log_step_start("Content Generation")
            
            # Run the content generation pipeline
            success = await test_complete_replicate_pipeline_whisper()
            
            if success:
                # Extract story title from the generated content
                # This is a bit of a workaround since the function doesn't return the title
                # We'll need to find the most recent story folder
                stories_dir = Config.OUTPUT_DIR / "stories"
                if stories_dir.exists():
                    # Get the most recently created story folder
                    story_folders = [f for f in stories_dir.iterdir() if f.is_dir()]
                    if story_folders:
                        latest_folder = max(story_folders, key=lambda x: x.stat().st_mtime)
                        self.sanitized_title = latest_folder.name
                        
                        # Try to get the actual title from metadata
                        metadata_file = latest_folder / "metadata.json"
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                self.story_title = metadata.get('title', self.sanitized_title)
                        else:
                            self.story_title = self.sanitized_title
                
                self.log_step_end("Content Generation", True)
                return True
            else:
                self.log_step_end("Content Generation", False)
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Content generation failed: {e}")
            self.log_step_end("Content Generation", False)
            return False
    
    def run_audio_video_processing(self) -> bool:
        """Run the audio/video processing pipeline."""
        try:
            if not self.story_title:
                self.logger.error("❌ No story title available for audio/video processing")
                return False
            
            self.log_step_start("Audio/Video Processing")
            
            # Run the audio/video processing pipeline
            success = process_video_for_topic(self.story_title, self.logger)
            
            self.log_step_end("Audio/Video Processing", success)
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Audio/video processing failed: {e}")
            self.log_step_end("Audio/Video Processing", False)
            return False
    
    async def run_full_pipeline(self) -> bool:
        """Run the complete AutoTube pipeline from start to finish."""
        self.start_time = time.time()
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("🎬 Starting AutoTube Full Pipeline")
        self.logger.info("=" * 60)
        
        print("\n🎬 AutoTube Full Pipeline - Complete Content to Video")
        print("=" * 60)
        
        # Step 1: Content Generation
        self.log_step_start("Content Generation")
        content_success = await self.run_content_generation()
        
        if not content_success:
            self.logger.error("❌ Content generation failed - stopping pipeline")
            self.log_step_end("Full Pipeline", False)
            return False
        
        # Step 2: Audio/Video Processing
        self.log_step_start("Audio/Video Processing")
        video_success = self.run_audio_video_processing()
        
        if not video_success:
            self.logger.error("❌ Audio/video processing failed")
            self.log_step_end("Full Pipeline", False)
            return False
        
        # Pipeline completed successfully
        total_time = time.time() - self.start_time
        self.log_step_end("Full Pipeline", True)
        
        # Save comprehensive report
        report_path = self.save_pipeline_report()
        
        # Final summary
        self.logger.info("🎉 Full Pipeline Completed Successfully!")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Total Pipeline Time: {total_time:.2f}s")
        self.logger.info(f"📁 Story Title: {self.story_title}")
        self.logger.info(f"📁 Sanitized Title: {self.sanitized_title}")
        self.logger.info(f"📊 Report Saved: {report_path}")
        
        print("\n🎉 Full Pipeline Completed Successfully!")
        print("=" * 60)
        print(f"📊 Total Time: {total_time:.2f}s")
        print(f"📁 Story: {self.story_title}")
        print(f"📁 Final Video: {Config.OUTPUT_DIR}/subtitles_processed_video/{self.sanitized_title}_final.mp4")
        print(f"📊 Report: {report_path}")
        
        # Print step breakdown
        print("\n⏱️ Step Breakdown:")
        for step_name, step_data in self.step_timings.items():
            if step_name != "Full Pipeline":  # Skip the overall timing
                duration = step_data.get("duration", 0)
                success = step_data.get("success", False)
                status = "✅" if success else "❌"
                print(f"  {status} {step_name}: {duration:.2f}s")
        
        return True

async def main():
    """Main function to run the full pipeline."""
    pipeline = FullPipeline()
    
    try:
        success = await pipeline.run_full_pipeline()
        
        if success:
            print("\n🎉 Pipeline completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Pipeline failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 