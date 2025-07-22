"""
Complete AutoTube Pipeline Test with Replicate (Schnell) Image Generation + Whisper Audio Synchronization
Project: ThroughTheLensofHistory
Tests the pipeline: Story -> Audio -> Whisper Audio Sync -> Replicate Image Generation
Uses Whisper to get exact word timestamps for precise image synchronization
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from tqdm import tqdm

# Add project root to path (use project's own src directory)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project-specific config
from config import Config, PATHS

from src.llm.story_generator import StoryGenerator
from src.replicate_image_generator import OptimizedReplicateImageGenerator
from src.video_composition.whisper_audio_synchronizer import WhisperAudioSynchronizer
from src.utils.folder_utils import sanitize_folder_name, setup_logging_with_file

def validate_file_creation(file_path: str, step_name: str, logger) -> bool:
    """
    Validate that a file was actually created and is not empty.
    
    Args:
        file_path: Path to the file to validate
        step_name: Name of the step for error reporting
        logger: Logger instance for logging errors
        
    Returns:
        True if file exists and is not empty, False otherwise
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        error_msg = f"❌ {step_name} FAILED: File not created at {file_path}"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    if file_path_obj.stat().st_size == 0:
        error_msg = f"❌ {step_name} FAILED: File created but is empty at {file_path}"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    success_msg = f"✅ {step_name} validation passed: {file_path} ({file_path_obj.stat().st_size:,} bytes)"
    print(success_msg)
    logger.info(success_msg)
    return True

def validate_folder_creation(folder_path: str, step_name: str, logger) -> bool:
    """
    Validate that a folder was created and contains expected files.
    
    Args:
        folder_path: Path to the folder to validate
        step_name: Name of the step for error reporting
        logger: Logger instance for logging errors
        
    Returns:
        True if folder exists and is not empty, False otherwise
    """
    folder_path_obj = Path(folder_path)
    
    if not folder_path_obj.exists():
        error_msg = f"❌ {step_name} FAILED: Folder not created at {folder_path}"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    if not folder_path_obj.is_dir():
        error_msg = f"❌ {step_name} FAILED: Path exists but is not a folder at {folder_path}"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    # Check if folder has any files
    files_in_folder = list(folder_path_obj.iterdir())
    if not files_in_folder:
        error_msg = f"❌ {step_name} FAILED: Folder created but is empty at {folder_path}"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    success_msg = f"✅ {step_name} validation passed: {folder_path} ({len(files_in_folder)} items)"
    print(success_msg)
    logger.info(success_msg)
    return True

def validate_story_data(story_data: dict, step_name: str, logger) -> bool:
    """
    Validate that story data contains required fields and is not empty.
    
    Args:
        story_data: Story data dictionary to validate
        step_name: Name of the step for error reporting
        logger: Logger instance for logging errors
        
    Returns:
        True if story data is valid, False otherwise
    """
    required_fields = ['title', 'story']
    optional_fields = ['hook', 'description', 'tags', 'keywords', 'music_category']
    
    # Check required fields
    for field in required_fields:
        if field not in story_data:
            error_msg = f"❌ {step_name} FAILED: Missing required field '{field}' in story data"
            print(error_msg)
            logger.error(error_msg)
            return False
        
        if not story_data[field]:
            error_msg = f"❌ {step_name} FAILED: Required field '{field}' is empty in story data"
            print(error_msg)
            logger.error(error_msg)
            return False
    
    # Check story content length
    story_text = story_data.get('story', '')
    if len(story_text.split()) < 50:  # Minimum 50 words
        error_msg = f"❌ {step_name} FAILED: Story too short ({len(story_text.split())} words, minimum 50)"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    success_msg = f"✅ {step_name} validation passed: Story has {len(story_text.split())} words"
    print(success_msg)
    logger.info(success_msg)
    return True

def validate_audio_file(audio_path: str, step_name: str, logger) -> bool:
    """
    Validate that audio file was created and is playable.
    
    Args:
        audio_path: Path to the audio file to validate
        step_name: Name of the step for error reporting
        logger: Logger instance for logging errors
        
    Returns:
        True if audio file is valid, False otherwise
    """
    if not validate_file_creation(audio_path, step_name, logger):
        return False
    
    try:
        from moviepy.editor import AudioFileClip
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()
        
        if duration < 1.0:  # Minimum 1 second
            error_msg = f"❌ {step_name} FAILED: Audio too short ({duration:.2f}s, minimum 1.0s)"
            print(error_msg)
            logger.error(error_msg)
            return False
        
        success_msg = f"✅ {step_name} audio validation passed: {duration:.2f}s duration"
        print(success_msg)
        logger.info(success_msg)
        return True
        
    except Exception as e:
        error_msg = f"❌ {step_name} FAILED: Audio file not playable - {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        return False

def validate_whisper_sync_data(sync_data: list, step_name: str, logger) -> bool:
    """
    Validate that Whisper synchronization data is valid.
    
    Args:
        sync_data: List of synchronized prompt data
        step_name: Name of the step for error reporting
        logger: Logger instance for logging errors
        
    Returns:
        True if sync data is valid, False otherwise
    """
    if not sync_data:
        error_msg = f"❌ {step_name} FAILED: No synchronized prompts generated"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    if len(sync_data) < 5:  # Minimum 5 segments
        error_msg = f"❌ {step_name} FAILED: Too few synchronized segments ({len(sync_data)}, minimum 5)"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    # Check each segment has required fields
    required_fields = ['image_prompt', 'timestamp_start', 'timestamp_end', 'audio_content']
    for i, segment in enumerate(sync_data):
        for field in required_fields:
            if field not in segment:
                error_msg = f"❌ {step_name} FAILED: Segment {i} missing required field '{field}'"
                print(error_msg)
                logger.error(error_msg)
                return False
    
    success_msg = f"✅ {step_name} validation passed: {len(sync_data)} synchronized segments"
    print(success_msg)
    logger.info(success_msg)
    return True

def validate_image_generation_result(result: dict, step_name: str, logger) -> bool:
    """
    Validate that image generation was successful.
    
    Args:
        result: Image generation result dictionary
        step_name: Name of the step for error reporting
        logger: Logger instance for logging errors
        
    Returns:
        True if image generation was successful, False otherwise
    """
    if not result:
        error_msg = f"❌ {step_name} FAILED: No result returned from image generation"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    successful_images = result.get('successful_images', 0)
    total_requested = result.get('total_images_requested', 0)
    
    if successful_images == 0:
        error_msg = f"❌ {step_name} FAILED: No images generated successfully"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    if successful_images < total_requested * 0.8:  # At least 80% success rate
        error_msg = f"❌ {step_name} FAILED: Low success rate ({successful_images}/{total_requested} = {successful_images/total_requested*100:.1f}%)"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    # Check that image files actually exist
    images = result.get('images', [])
    existing_images = 0
    for img in images:
        img_path = img.get('image_path', '')
        if img_path and Path(img_path).exists():
            existing_images += 1
    
    if existing_images < successful_images:
        error_msg = f"❌ {step_name} FAILED: {successful_images - existing_images} image files missing from disk"
        print(error_msg)
        logger.error(error_msg)
        return False
    
    success_msg = f"✅ {step_name} validation passed: {successful_images}/{total_requested} images generated"
    print(success_msg)
    logger.info(success_msg)
    return True

async def test_complete_replicate_pipeline_whisper():
    """Test the complete AutoTube pipeline with Replicate (Schnell) image generation + Whisper audio sync."""
    print("\n🚀 AutoTube Pipeline Test - Replicate (Schnell) + Whisper Audio Sync\n" + ("="*70))
    timings = {}
    t0 = time.time()
    
    # Step 1: Story Generation
    print("\n[STEP 1] 📝 Story Generation...")
    t1 = time.time()
    async with StoryGenerator() as sg:
        print("\n[STEP 0.5] 🎯 Topic Suggestion (Avoiding Duplicates)...")
        with tqdm(total=1, desc="Suggesting unique topic", unit="topic") as pbar_topic:
            story_title = await sg.suggest_topic()
            print(f"✅ Suggested topic: {story_title}")
            pbar_topic.update(1)
        with tqdm(total=1, desc="Generating story", unit="story") as pbar:
            story_data = await sg.generate_story(story_title)
            print(f"✅ Story: {story_data['title']}")
            print(f"✅ Hook: {story_data.get('hook', '')}")
            print(f"✅ Word count: {len(story_data.get('story', '').split())}")
            print(f"✅ Music category: {story_data.get('music_category', 'Unknown')}")
            pbar.update(1)
        # Save topic to used_topics.txt to prevent duplicates
        sg.save_used_topic(story_title)
        
    timings['Story Generation'] = time.time() - t1
    print(f"⏱️ Story generation completed in {timings['Story Generation']:.2f}s")

    # Create universal sanitized title for all asset folders
    sanitized_title = sanitize_folder_name(story_data['title'])
    print(f"📁 Using universal folder name: {sanitized_title}")
    
    # Setup logging with file
    logger = setup_logging_with_file(story_title, "content_gen")
    logger.info(f"📁 Sanitized folder name: {sanitized_title}")

    # VALIDATE STORY DATA
    if not validate_story_data(story_data, "Story Generation", logger):
        print("\n❌ STORY GENERATION VALIDATION FAILED - STOPPING PIPELINE")
        logger.error("❌ STORY GENERATION VALIDATION FAILED - STOPPING PIPELINE")
        return False

    # Step 1.5: Save story assets to output/stories/{sanitized_title}/
    print("\n[STEP 1.5] 💾 Saving Story Assets...")
    t1_5 = time.time()
    story_folder = PATHS['stories'] / sanitized_title
    story_folder.mkdir(parents=True, exist_ok=True)
    
    # Save story data, topic, and metadata
    story_json_path = story_folder / 'story.json'
    with open(story_json_path, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, indent=2, ensure_ascii=False)
    
    topic_txt_path = story_folder / 'topic.txt'
    with open(topic_txt_path, 'w', encoding='utf-8') as f:
        f.write(story_title)
    
    # Save viral title suggestions
    title_data = {
        "main_title": story_data['title'],
        "hook": story_data.get('hook', ''),
        "description": story_data.get('description', ''),
        "tags": story_data.get('tags', []),
        "keywords": story_data.get('keywords', []),
        "music_category": story_data.get('music_category', 'Unknown'),
        "word_count": len(story_data.get('story', '').split())
    }
    metadata_json_path = story_folder / 'metadata.json'
    with open(metadata_json_path, 'w', encoding='utf-8') as f:
        json.dump(title_data, f, indent=2, ensure_ascii=False)
    
    story_txt_path = story_folder / 'story.txt'
    with open(story_txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Title: {story_data['title']}\n")
        f.write(f"Hook: {story_data.get('hook', '')}\n")
        f.write(f"Music Category: {story_data.get('music_category', 'Unknown')}\n")
        f.write(f"Word Count: {len(story_data.get('story', '').split())}\n")
        f.write(f"\nStory:\n{story_data.get('story', '')}\n")
        f.write(f"\nDescription:\n{story_data.get('description', '')}\n")
        f.write(f"\nTags: {', '.join(story_data.get('tags', []))}\n")
        f.write(f"Keywords: {', '.join(story_data.get('keywords', []))}\n")
    
    # VALIDATE STORY ASSETS CREATION
    story_assets_valid = (
        validate_file_creation(str(story_json_path), "Story JSON Creation", logger) and
        validate_file_creation(str(topic_txt_path), "Topic TXT Creation", logger) and
        validate_file_creation(str(metadata_json_path), "Metadata JSON Creation", logger) and
        validate_file_creation(str(story_txt_path), "Story TXT Creation", logger)
    )
    
    if not story_assets_valid:
        print("\n❌ STORY ASSETS VALIDATION FAILED - STOPPING PIPELINE")
        logger.error("❌ STORY ASSETS VALIDATION FAILED - STOPPING PIPELINE")
        return False
    
    print(f"✅ Story assets saved to: {story_folder}")
    print(f"   📄 story.json - Complete story data")
    print(f"   📄 story.txt - Human-readable story")
    print(f"   📄 topic.txt - Story topic")
    print(f"   📄 metadata.json - Title, tags, description")
    logger.info(f"✅ Story assets saved to: {story_folder}")
    timings['Story Saving'] = time.time() - t1_5
    print(f"⏱️ Story saving completed in {timings['Story Saving']:.2f}s")
    print(f"📝 Marking topic as used: {story_title}")
    
    print("⏳ Waiting 2 seconds before TTS generation...")
    await asyncio.sleep(2)

    # Step 2: Audio Generation (TTS) - Save to output/audio/{sanitized_title}/
    print("\n[STEP 2] 🔊 Audio Generation (TTS)...")
    t2 = time.time()
    from src.tts_generator import tts_story_to_audio
    audio_filename = f"audio_{sanitized_title}.mp3"
    with tqdm(total=1, desc="Generating TTS audio", unit="audio") as pbar:
        audio_path = tts_story_to_audio(story_data['story'], audio_filename, story_title=story_data['title'])
        pbar.update(1)
    
    # VALIDATE TTS RETURN VALUE FIRST
    if not audio_path:
        error_msg = "❌ TTS AUDIO GENERATION FAILED: TTS function returned None or empty path"
        print(f"\n{error_msg}")
        logger.error(error_msg)
        return False
    
    # VALIDATE AUDIO GENERATION
    if not validate_audio_file(audio_path, "TTS Audio Generation", logger):
        print("\n❌ TTS AUDIO GENERATION VALIDATION FAILED - STOPPING PIPELINE")
        logger.error("❌ TTS AUDIO GENERATION VALIDATION FAILED - STOPPING PIPELINE")
        return False
    
    print(f"✅ TTS audio generated: {audio_path}")
    file_size = os.path.getsize(audio_path)
    print(f"📊 Audio file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    from moviepy.editor import AudioFileClip
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    audio_clip.close()
    print(f"⏱️ Audio duration: {audio_duration:.2f} seconds")
    logger.info(f"✅ TTS audio generated: {audio_path} ({file_size:,} bytes, {audio_duration:.2f}s)")
    timings['Audio Generation'] = time.time() - t2
    print(f"⏱️ Audio generation completed in {timings['Audio Generation']:.2f}s")

    # Step 3: Whisper Audio Synchronization (NEW - replaces guessing with exact timestamps)
    print("\n[STEP 3] 🎤 Whisper Audio Synchronization...")
    t3 = time.time()
    with tqdm(total=1, desc="Whisper audio sync", unit="sync") as pbar:
        # Initialize Whisper synchronizer
        whisper_sync = WhisperAudioSynchronizer(model_name="base")
        
        # Process audio for image synchronization (now async)
        synchronized_prompts = await whisper_sync.process_audio_for_image_sync(
            audio_path=audio_path,
            original_story=story_data['story'],
            num_images=20,
            story_title=story_data['title']
        )
        
        pbar.update(1)
    
    # VALIDATE WHISPER SYNCHRONIZATION
    if not validate_whisper_sync_data(synchronized_prompts, "Whisper Audio Synchronization", logger):
        print("\n❌ WHISPER AUDIO SYNCHRONIZATION VALIDATION FAILED - STOPPING PIPELINE")
        logger.error("❌ WHISPER AUDIO SYNCHRONIZATION VALIDATION FAILED - STOPPING PIPELINE")
        return False
    
    print(f"✅ Whisper audio synchronization completed!")
    print(f"📊 Generated {len(synchronized_prompts)} synchronized image prompts")
    print(f"📁 Whisper sync data saved to: {PATHS['output']}/audio_sync_data/{sanitized_title}_whisper_sync.json")
    logger.info(f"✅ Whisper sync completed: {len(synchronized_prompts)} prompts")
    
    # Extract image prompts for generation
    image_prompts = [prompt_data['image_prompt'] for prompt_data in synchronized_prompts]
    
    # Show timing accuracy improvement
    print(f"\n🎯 Whisper Timing Accuracy:")
    total_duration = synchronized_prompts[-1]['timestamp_end'] if synchronized_prompts else 0
    print(f"   Total duration: {total_duration:.2f}s (exact from Whisper)")
    print(f"   Image duration: {total_duration / len(synchronized_prompts):.2f}s per image")
    
    # Show first few synchronized segments
    print(f"\n🔍 First 3 synchronized segments:")
    for i, segment in enumerate(synchronized_prompts[:3]):
        print(f"   Image {segment['image_number']}: {segment['timestamp_start']:.1f}s - {segment['timestamp_end']:.1f}s")
        print(f"     Audio: '{segment['audio_content']}'")
        print(f"     Words: {segment['words_in_segment']}, Confidence: {segment['confidence_avg']:.2f}")
    
    timings['Whisper Audio Sync'] = time.time() - t3
    print(f"⏱️ Whisper audio sync completed in {timings['Whisper Audio Sync']:.2f}s")

    # Step 4: Music Selection - Save to output/music_selections/{sanitized_title}/
    print("\n[STEP 4] 🎵 Music Selection...")
    t4 = time.time()
    from src.utils.music_selector import MusicSelector
    selector = MusicSelector()
    with tqdm(total=1, desc="Selecting background music", unit="music") as pbar:
        music_file = selector.get_music_file_by_story(story_data, story_title=story_data['title'])
        pbar.update(1)
    
    # VALIDATE MUSIC SELECTION
    if not validate_file_creation(music_file, "Music Selection", logger):
        print("\n❌ MUSIC SELECTION VALIDATION FAILED - STOPPING PIPELINE")
        logger.error("❌ MUSIC SELECTION VALIDATION FAILED - STOPPING PIPELINE")
        return False
    
    music_filename = music_file.split('/')[-1] if '/' in music_file else music_file.split('\\')[-1]
    print(f"✅ Music selected: {music_filename}")
    
    # Save music selection to output/music_selections/{sanitized_title}/
    music_selection_folder = Config.OUTPUT_DIR / "music_selections" / sanitized_title
    music_selection_folder.mkdir(parents=True, exist_ok=True)
    music_selection_data = {
        "story_title": story_data['title'],
        "music_category": story_data.get('music_category', 'Unknown'),
        "selected_music_file": music_file,
        "music_filename": music_filename,
        "selection_timestamp": time.time()
    }
    music_selection_path = music_selection_folder / 'music_selection.json'
    with open(music_selection_path, 'w', encoding='utf-8') as f:
        json.dump(music_selection_data, f, indent=2, ensure_ascii=False)
    
    # VALIDATE MUSIC SELECTION SAVE
    if not validate_file_creation(str(music_selection_path), "Music Selection Save", logger):
        print("\n❌ MUSIC SELECTION SAVE VALIDATION FAILED - STOPPING PIPELINE")
        logger.error("❌ MUSIC SELECTION SAVE VALIDATION FAILED - STOPPING PIPELINE")
        return False
    
    print(f"📁 Music selection saved to: {music_selection_folder}/music_selection.json")
    logger.info(f"✅ Music selected: {music_filename}")
    timings['Music Selection'] = time.time() - t4
    print(f"⏱️ Music selection completed in {timings['Music Selection']:.2f}s")

    # Step 5: Audio Mixing - REMOVED (now handled by audio/video processor)
    print("\n[STEP 5] 🎚️ Audio Mixing - SKIPPED (will be handled by audio/video processor)")
    print("✅ Audio mixing step removed from content generation pipeline")
    print("📁 Mixed audio will be generated during video processing")
    timings['Audio Mixing'] = 0.0
    print(f"⏱️ Audio mixing skipped (0.00s)")

    # Step 6: Image Generation (using Whisper-synchronized prompts) - Save to output/images/{sanitized_title}/
    print("\n[STEP 6] 🖼️ Replicate Image Generation (Schnell) with Whisper Sync...")
    t6 = time.time()
    image_generator = OptimizedReplicateImageGenerator(default_preset="mvp_testing")
    with tqdm(total=len(image_prompts), desc="Generating images with Schnell", unit="image") as pbar:
        result = await image_generator.generate_images_for_story(
            story_data=story_data,
            image_prompts=image_prompts,
            quality_preset="mvp_testing"
        )
        pbar.update(len(image_prompts) - result.get('successful_images', 0))
    
    # VALIDATE IMAGE GENERATION
    if not validate_image_generation_result(result, "Image Generation", logger):
        print("\n❌ IMAGE GENERATION VALIDATION FAILED - STOPPING PIPELINE")
        logger.error("❌ IMAGE GENERATION VALIDATION FAILED - STOPPING PIPELINE")
        return False
    
    print(f"✅ Image generation successful!")
    print(f"   🖼️ Generated: {result['successful_images']}/{result['total_images_requested']} images")
    print(f"   💰 Total cost: ${result['total_cost']:.4f}")
    print(f"   🎯 Quality preset: {result.get('quality_preset', 'unknown')}")
    print(f"   ⏱️ Total generation time: {result.get('generation_time', 0):.2f}s")
    print(f"   💰 Cost per image: ${result.get('cost_per_image', 0):.4f}")
    for i, img in enumerate(result.get('images', [])):
        print(f"  🖼️ Image {i+1}: {img.get('image_path', 'N/A')}")
    if result.get('failed_images', 0) > 0:
        print(f"\n❌ Failed images: {result['failed_images']}")
        for failed in result.get('failed_prompts', []):
            print(f"   ❌ Scene {failed.get('scene_index', '?')}: {failed.get('error', '')}")
    logger.info(f"✅ Image generation: {result['successful_images']}/{result['total_images_requested']} images, cost: ${result['total_cost']:.4f}")
    timings['Image Generation'] = time.time() - t6
    print(f"⏱️ Image generation completed in {timings['Image Generation']:.2f}s")

    # Final Summary
    print("\n" + ("="*70))
    print("🎉 CONTENT GENERATION PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    total_time = time.time() - t0
    print(f"⏱️ Total pipeline time: {total_time:.2f}s")
    print(f"📊 Story: {story_data['title']}")
    print(f"📊 Audio duration: {audio_duration:.2f}s")
    print(f"📊 Images generated: {result['successful_images']}/{len(image_prompts)}")
    print(f"💰 Total cost: ${result['total_cost']:.4f}")
    print(f"🎵 Music: {music_filename}")
    print(f"🎤 Whisper sync: {len(synchronized_prompts)} synchronized segments")
    print("\n📁 Generated Files:")
    print(f"   📄 Story: {story_folder}")
    print(f"   🔊 Audio: {Config.OUTPUT_DIR}/audio/{sanitized_title}/")
    print(f"   🖼️ Images: {Config.OUTPUT_DIR}/images/{sanitized_title}/")
    print(f"   🎵 Music Selection: {Config.OUTPUT_DIR}/music_selections/{sanitized_title}/")
    print(f"   🎤 Whisper Sync: {Config.OUTPUT_DIR}/audio_sync_data/{sanitized_title}_whisper_sync.json")
    print("\n⏱️ Timing Breakdown:")
    for step, duration in timings.items():
        print(f"  {step}: {duration:.2f}s")
    print(f"\n💰 Cost Breakdown:")
    print(f"   Image Generation: ${result['total_cost']:.4f}")
    print(f"   Cost per image: ${result.get('cost_per_image', 0):.4f}")
    print(f"   Estimated monthly cost (6 videos/day): ${result['total_cost'] * 30 * 6:.2f}")
    print(f"\n🎯 Whisper Sync Benefits:")
    print(f"   ✅ Exact word timestamps instead of guessing")
    print(f"   ✅ Perfect audio-image synchronization")
    print(f"   ✅ Confidence scoring for accuracy")
    print(f"   ✅ Missing word detection and handling")
    print(f"\n📋 Next Steps:")
    print(f"   🎬 Run audio/video processor to create final video with subtitles")
    print(f"   📁 Use topic: {story_title}")
    
    logger.info(f"🎉 Content generation pipeline completed successfully!")
    logger.info(f"📊 Total time: {total_time:.2f}s, Cost: ${result['total_cost']:.4f}")
    logger.info(f"📋 Ready for audio/video processing with topic: {story_title}")
    
    return True

async def main():
    print("🚀 Starting Content Generation Pipeline...")
    try:
        success = await test_complete_replicate_pipeline_whisper()
        if success:
            print("\n🎉 Content generation pipeline completed successfully!")
            print("📋 Ready for audio/video processing!")
        else:
            print("\n❌ Content generation pipeline failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Content generation pipeline failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 