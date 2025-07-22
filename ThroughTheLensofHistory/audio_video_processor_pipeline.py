import os
import sys
import json
from pathlib import Path
import logging
from typing import Optional

# Add project root to path to access src modules (use project's own src directory)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project-specific config
from config import Config, PATHS

from src.video_composition.moviepy_video_composer import MoviePyVideoComposer
from src.video_composition.whisper_subtitle_processor import OptimizedWhisperViralSubtitleProcessor
from src.utils.folder_utils import sanitize_folder_name, setup_logging_with_file

# Set up output directory for this project
# Use Config.OUTPUT_DIR directly instead of creating a local variable

def process_video_for_topic(topic_name: str, logger: Optional[logging.Logger] = None) -> bool:
    if not logger:
        logger = setup_logging_with_file(topic_name, "audio_video")
    
    sanitized_name = sanitize_folder_name(topic_name)
    logger.info(f"📁 Sanitized folder name: {sanitized_name}")
    
    # Step 0: Audio Mixing (NEW - first step)
    logger.info(f"🎚️ Step 0: Audio Mixing for topic: {topic_name}")
    
    # Check if source TTS audio exists
    source_audio_path = Config.OUTPUT_DIR / "audio" / sanitized_name / f"audio_{sanitized_name}.mp3"
    if not source_audio_path.exists():
        logger.error(f"❌ Source TTS audio not found: {source_audio_path}")
        logger.error("Please run the content generation pipeline first to generate TTS audio.")
        return False
    
    logger.info(f"✅ Found source TTS audio: {source_audio_path}")
    
    # Check if music selection exists
    music_selection_path = Config.OUTPUT_DIR / "music_selections" / sanitized_name / "music_selection.json"
    if not music_selection_path.exists():
        logger.error(f"❌ Music selection not found: {music_selection_path}")
        logger.error("Please run the content generation pipeline first to generate music selection.")
        return False
    
    logger.info(f"✅ Found music selection: {music_selection_path}")
    
    # Load music selection
    with open(music_selection_path, 'r', encoding='utf-8') as f:
        music_data = json.load(f)
    
    music_file = music_data.get('selected_music_file', '')
    if not Path(music_file).exists():
        logger.error(f"❌ Music file not found: {music_file}")
        return False
    
    logger.info(f"✅ Found music file: {music_file}")
    
    # Mix audio
    from src.audio_mixer import AudioMixer
    mixer = AudioMixer()
    
    # Create mixed audio directory
    mixed_audio_dir = Config.OUTPUT_DIR / "mixed_audio" / sanitized_name
    mixed_audio_dir.mkdir(parents=True, exist_ok=True)
    
    mixed_audio_path = mixed_audio_dir / f"mixed_audio_{sanitized_name}.mp3"
    
    logger.info(f"🎚️ Mixing TTS with background music...")
    result_path = mixer.mix_story_audio(source_audio_path, music_file, mixed_audio_path)
    
    if not result_path or not Path(result_path).exists():
        logger.error("❌ Audio mixing failed")
        return False
    
    file_size = Path(result_path).stat().st_size
    logger.info(f"✅ Mixed audio created: {result_path}")
    logger.info(f"📊 Mixed audio size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    # Step 1: Create Ken Burns video and save to videos folder
    image_dir = Config.OUTPUT_DIR / "images" / sanitized_name
    videos_dir = Config.OUTPUT_DIR / "videos"
    kenburns_video_path = videos_dir / f"{sanitized_name}_kenburns.mp4"
    
    # Step 2: Subtitle processed video will be saved here
    subtitles_output_dir = Config.OUTPUT_DIR / "subtitles_processed_video"
    final_video_path = subtitles_output_dir / f"{sanitized_name}_final.mp4"
    
    if not image_dir.exists():
        logger.error(f"Image directory not found: {image_dir}")
        return False
    
    # Create directories
    videos_dir.mkdir(parents=True, exist_ok=True)
    subtitles_output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Create Ken Burns video
        logger.info(f"🎬 Creating Ken Burns video for topic: {topic_name}")
        composer = MoviePyVideoComposer(output_dir=videos_dir, logger=logger)
        
        kenburns_video = composer.compose_video(
            image_dir=image_dir,
            audio_file=result_path,  # Use the mixed audio we just created
            topic_name=sanitized_name,
            output_filename=f"{sanitized_name}_kenburns.mp4",
            enable_ken_burns=True,
            num_images=20
        )
        
        if not Path(kenburns_video).exists():
            logger.error("Ken Burns video creation failed")
            return False
        
        logger.info(f"✅ Ken Burns video created: {kenburns_video}")
        
        # Step 2: Add dynamic subtitles to the video
        logger.info(f"🎬 Adding dynamic subtitles to video")
        subtitle_processor = OptimizedWhisperViralSubtitleProcessor(logger=logger)
        
        # Get story path for subtitle enhancement
        story_path = Config.OUTPUT_DIR / "stories" / sanitized_name / "story.txt"
        
        final_video = subtitle_processor.add_viral_subtitles_to_video(
            video_path=kenburns_video,
            audio_path=result_path,  # Use the mixed audio
            output_path=final_video_path,
            story_path=story_path if story_path.exists() else None
        )
        
        if not Path(final_video).exists():
            logger.error("Subtitle processing failed")
            return False
        
        file_size = Path(final_video).stat().st_size
        logger.info(f"✅ Final video with subtitles created: {final_video}")
        logger.info(f"📊 Final video size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        logger.info(f"🎉 Audio/Video processing completed successfully!")
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
        print("Usage: python audio_video_processor_pipeline.py <topic_name>")
        print("Example: python audio_video_processor_pipeline.py 'The Great Emu War'")
        sys.exit(1)
    
    topic_name = sys.argv[1]
    success = process_video_for_topic(topic_name)
    
    if success:
        print("Audio/Video processing completed successfully!")
        sys.exit(0)
    else:
        print("Audio/Video processing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()