import os
import sys
import re
from pathlib import Path
import logging
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from video_composition.moviepy_video_composer import MoviePyVideoComposer
from video_composition.whisper_subtitle_processor import OptimizedWhisperViralSubtitleProcessor

from src.utils.folder_utils import sanitize_folder_name

def setup_logger():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def process_video_for_topic(topic_name: str, logger: Optional[logging.Logger] = None) -> bool:
    if not logger:
        logger = setup_logger()
    
    sanitized_name = sanitize_folder_name(topic_name)
    image_dir = Config.PATHS['images'] / sanitized_name
    audio_file = Config.PATHS['mixed_audio'] / sanitized_name / f"mixed_audio_{sanitized_name}.mp3"
    
    # Step 1: Create Ken Burns video and save to videos folder
    videos_dir = Config.PATHS['videos'] / sanitized_name
    kenburns_video_path = videos_dir / f"{sanitized_name}_kenburns.mp4"
    
    # Step 2: Subtitle processed video will be saved here
    subtitles_output_dir = Config.PATHS['subtitles_processed_video'] / sanitized_name
    final_video_path = subtitles_output_dir / f"{sanitized_name}_final.mp4"
    
    if not Path(image_dir).exists():
        logger.error(f"Image directory not found: {image_dir}")
        return False
    
    if not Path(audio_file).exists():
        logger.error(f"Audio file not found: {audio_file}")
        return False
    
    # Create directories
    Path(videos_dir).mkdir(parents=True, exist_ok=True)
    Path(subtitles_output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Create Ken Burns video
        logger.info(f"🎬 Creating Ken Burns video for topic: {topic_name}")
        composer = MoviePyVideoComposer(output_dir=videos_dir, logger=logger)
        
        kenburns_video = composer.compose_video(
            image_dir=image_dir,
            audio_file=audio_file,
            topic_name=sanitized_name,
            output_filename=f"{sanitized_name}_kenburns.mp4",
            enable_ken_burns=True,
            num_images=12
        )
        
        if not Path(kenburns_video).exists():
            logger.error("Ken Burns video creation failed")
            return False
        
        logger.info(f"✅ Ken Burns video created: {kenburns_video}")
        
        # Step 2: Add dynamic subtitles to the video
        logger.info(f"🎬 Adding dynamic subtitles to video")
        subtitle_processor = OptimizedWhisperViralSubtitleProcessor(logger=logger)
        
        # Get story path for subtitle enhancement
        story_path = Config.PATHS['stories'] / sanitized_name / "story.txt"
        
        final_video = subtitle_processor.add_viral_subtitles_to_video(
            video_path=kenburns_video,
            audio_path=audio_file,
            output_path=final_video_path,
            story_path=story_path if Path(story_path).exists() else None
        )
        
        if not Path(final_video).exists():
            logger.error("Subtitle processing failed")
            return False
        
        file_size = Path(final_video).stat().st_size
        logger.info(f"✅ Final video with subtitles created: {final_video}")
        logger.info(f"📊 Final video size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        logger.info(f"🎉 Video processing completed successfully!")
        logger.info(f"📁 Ken Burns video: {kenburns_video}")
        logger.info(f"📁 Final video with subtitles: {final_video}")
        
        return True
        
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python video_processor.py <topic_name>")
        print("Example: python video_processor.py 'The Great Emu War'")
        sys.exit(1)
    
    topic_name = sys.argv[1]
    logger = setup_logger()
    success = process_video_for_topic(topic_name, logger)
    
    if success:
        logger.info("Video processing completed successfully!")
        sys.exit(0)
    else:
        logger.error("Video processing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()