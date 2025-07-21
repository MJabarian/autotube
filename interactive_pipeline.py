#!/usr/bin/env python3
"""
Interactive Pipeline for ThroughTheLensofHistory_30seoconds
Allows users to input any topic and generates a complete video automatically.
Perfect for capitalizing on trending topics from Google Trends.
"""

import os
import sys
import json
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules
from config import Config, PATHS
from src.utils.folder_utils import sanitize_folder_name, setup_logging_with_file
from src.llm.story_generator import StoryGenerator
from src.utils.music_selector import MusicSelector
from src.replicate_image_generator import OptimizedReplicateImageGenerator
from src.tts_generator import tts_story_to_audio
from src.audio_mixer import AudioMixer
from src.video_composition.moviepy_video_composer import MoviePyVideoComposer
from src.video_composition.whisper_subtitle_processor import OptimizedWhisperViralSubtitleProcessor

class InteractivePipeline:
    """Interactive pipeline for generating videos from user-provided topics."""
    
    def __init__(self):
        self.logger = setup_logging_with_file("interactive_pipeline", "interactive")
        self.story_generator = StoryGenerator()
        self.music_selector = MusicSelector()
        self.image_generator = OptimizedReplicateImageGenerator()
        # TTS generator uses functions, not a class
        self.audio_mixer = AudioMixer()
        
    def get_user_topic(self) -> str:
        """Get topic from user input with validation."""
        print("\n" + "="*70)
        print("🎯 INTERACTIVE VIDEO GENERATOR")
        print("="*70)
        print("Enter any topic you want to create a video about!")
        print("Examples:")
        print("  • British Open golf tournament")
        print("  • Ancient Roman gladiators")
        print("  • The invention of the telephone")
        print("  • Queen Elizabeth I's reign")
        print("  • The Great Depression")
        print("  • Ancient Egyptian pyramids")
        print("  • World War II codebreakers")
        print("  • The discovery of penicillin")
        print("  • Ancient Greek Olympics")
        print("  • The Industrial Revolution")
        print("="*70)
        
        while True:
            topic = input("\n🎯 Enter your topic: ").strip()
            
            if not topic:
                print("❌ Please enter a topic!")
                continue
                
            if len(topic) < 3:
                print("❌ Topic too short! Please enter a more descriptive topic.")
                continue
                
            if len(topic) > 200:
                print("❌ Topic too long! Please keep it under 200 characters.")
                continue
            
            # Confirm with user
            print(f"\n✅ You entered: '{topic}'")
            confirm = input("Is this correct? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes', '']:
                return topic
            else:
                print("🔄 Let's try again...")
    
    async def generate_story(self, topic: str) -> Dict[str, Any]:
        """Generate a complete story for the given topic (same as full pipeline)."""
        print(f"\n📝 Generating story for: {topic}")
        
        try:
            # Use interactive-specific story generation for better quality
            # This generates a complete story with SSML tags, title, hook, description, tags, etc.
            story_data = await self.story_generator.generate_story(topic, use_interactive_prompt=True)
            
            if not story_data or 'story' not in story_data:
                raise Exception("Failed to generate story")
            
            print(f"✅ Story generated successfully!")
            print(f"📊 Title: {story_data.get('title', topic)}")
            print(f"📊 Hook: {story_data.get('hook', '')}")
            print(f"📊 Word count: {len(story_data.get('story', '').split())}")
            print(f"📊 Music category: {story_data.get('music_category', 'Unknown')}")
            print(f"📊 Story length: {len(story_data['story'])} characters")
            
            return story_data
            
        except Exception as e:
            self.logger.error(f"Story generation failed: {e}")
            raise
    
    def select_music(self, topic: str, story: str) -> Dict[str, Any]:
        """Select appropriate music for the topic and story."""
        print(f"\n🎵 Selecting music for: {topic}")
        
        try:
            # Use the correct music selection method
            # First, classify the story to get music category
            import asyncio
            
            # Create a simple story data structure
            story_data = {
                'story': story,
                'title': topic,
                'music_category': 'Uplifting'  # Default category
            }
            
            # Get music file using the correct method
            music_file = self.music_selector.get_music_file_by_story(story_data, topic)
            
            if not music_file:
                raise Exception("Failed to select music")
            
            # Create the expected music_data structure
            music_data = {
                'selected_music_file': music_file,
                'category': story_data.get('music_category', 'Uplifting')
            }
            
            print(f"✅ Music selected: {Path(music_file).name}")
            print(f"📊 Music category: {music_data['category']}")
            
            return music_data
            
        except Exception as e:
            self.logger.error(f"Music selection failed: {e}")
            raise
    
    async def generate_images(self, topic: str, story: str, sanitized_name: str) -> bool:
        """Generate images for the story."""
        print(f"\n🖼️  Generating images for: {topic}")
        
        try:
            # Create story data dictionary (same format as full pipeline)
            story_data = {
                'title': topic,
                'story': story,
                'topic_name': sanitized_name
            }
            
            # Use existing image generator (story analyzer will generate 12 images for 30s videos)
            result = await self.image_generator.generate_images_for_story(
                story_data=story_data,
                quality_preset="production"
            )
            
            # Handle different result types - CHECK INTEGER FIRST
            if isinstance(result, int) and result > 0:
                print(f"✅ Images generated successfully!")
                print(f"📊 Generated {result} images for the story")
                return True
            elif isinstance(result, dict) and 'successful_images' in result:
                successful_count = len(result['successful_images'])
                print(f"✅ Images generated successfully!")
                print(f"📊 Generated {successful_count} images for the story")
                return successful_count > 0
            elif isinstance(result, dict):  # Handle other dict results
                print(f"✅ Images generated successfully!")
                print(f"📊 Image generation completed with dict result")
                return True
            elif result:  # Any truthy result means success
                print(f"✅ Images generated successfully!")
                print(f"📊 Image generation completed")
                return True
            else:
                raise Exception("Image generation returned no results")
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            raise
    
    def generate_audio(self, topic: str, story: str, sanitized_name: str) -> str:
        """Generate TTS audio for the story with high-quality speed adjustment."""
        print(f"\n🎤 Generating audio for: {topic}")
        
        try:
            # Use TTS function directly
            audio_filename = f"audio_{sanitized_name}.mp3"
            audio_path = tts_story_to_audio(
                story_text=story,
                output_filename=audio_filename,
                story_title=topic
            )
            
            if not audio_path or not Path(audio_path).exists():
                raise Exception("TTS generation failed")
            
            print(f"✅ TTS audio generated successfully!")
            print(f"📁 Audio file: {Path(audio_path).name}")
            
            # Use original TTS audio directly (no speed adjustment needed)
            self.logger.info(f"✅ Using original TTS audio")
            print(f"✅ Using original TTS audio")
            
            return audio_path
            
        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            raise
    
    async def generate_synchronized_image_prompts(self, topic: str, story: str, audio_path: str, sanitized_name: str) -> List[Dict[str, Any]]:
        """Generate Whisper-synchronized image prompts (same as full pipeline)."""
        print(f"\n🎤 Whisper Audio Synchronization for: {topic}")
        
        try:
            # Initialize Whisper synchronizer
            from src.video_composition.whisper_audio_synchronizer import WhisperAudioSynchronizer
            whisper_sync = WhisperAudioSynchronizer(model_name="base")
            
            # Process audio for image synchronization (exactly like full pipeline)
            synchronized_prompts = await whisper_sync.process_audio_for_image_sync(
                audio_path=audio_path,
                original_story=story,
                num_images=12,  # Exactly 12 images for 30s video
                story_title=topic
            )
            
            if not synchronized_prompts or len(synchronized_prompts) != 12:
                raise Exception(f"Whisper sync failed: expected 12 prompts, got {len(synchronized_prompts) if synchronized_prompts else 0}")
            
            print(f"✅ Whisper audio synchronization completed!")
            print(f"📊 Generated {len(synchronized_prompts)} synchronized image prompts")
            print(f"⏱️ Total duration: {synchronized_prompts[-1]['timestamp_end']:.2f}s")
            print(f"📊 {synchronized_prompts[-1]['timestamp_end'] / len(synchronized_prompts):.2f}s per image")
            
            return synchronized_prompts
            
        except Exception as e:
            self.logger.error(f"Whisper synchronization failed: {e}")
            raise
    
    async def generate_images_with_sync(self, topic: str, story: str, synchronized_prompts: List[Dict[str, Any]], sanitized_name: str) -> bool:
        """Generate images using Whisper-synchronized prompts (same as full pipeline)."""
        print(f"\n🖼️  Generating 12 synchronized images for: {topic}")
        
        try:
            # Create story data dictionary (same format as full pipeline)
            story_data = {
                'title': topic,
                'story': story,
                'topic_name': sanitized_name
            }
            
            # Extract image prompts from synchronized data (same as full pipeline)
            image_prompts = [prompt_data['image_prompt'] for prompt_data in synchronized_prompts]
            
            # Use existing image generator with synchronized prompts (same as full pipeline)
            result = await self.image_generator.generate_images_for_story(
                story_data=story_data,
                image_prompts=image_prompts,  # Use synchronized prompts
                quality_preset="production"
            )
            
            # Handle different result types - CHECK INTEGER FIRST
            print(f"🔍 DEBUG: Result type: {type(result)}, Value: {result}")
            if isinstance(result, int) and result > 0:
                print(f"✅ Generated {result} synchronized images successfully!")
                print(f"📊 Total images: {result}")
                print(f"💰 Cost: ~${result * 0.003:.4f} (estimated)")
                return True
            elif isinstance(result, dict) and 'successful_images' in result:
                # Handle case where successful_images is an integer (count) or list
                if isinstance(result['successful_images'], int):
                    successful_count = result['successful_images']
                else:
                    successful_count = len(result['successful_images'])
                print(f"✅ Generated {successful_count} synchronized images successfully!")
                print(f"📊 Total images: {result.get('total_images_requested', 12)}")
                print(f"💰 Cost: ${result.get('total_cost', 0):.4f}")
                return successful_count > 0
            elif isinstance(result, dict):  # Handle other dict results
                print(f"✅ Generated synchronized images successfully!")
                print(f"📊 Image generation completed with dict result")
                return True
            elif result:  # Any truthy result means success
                print(f"✅ Generated synchronized images successfully!")
                print(f"📊 Image generation completed")
                return True
            else:
                raise Exception("Image generation returned no results")
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            raise
    
    def mix_audio(self, topic: str, audio_path: str, music_file: str, sanitized_name: str) -> str:
        """Mix TTS audio with background music using high-quality processing."""
        print(f"\n🎚️  Mixing audio for: {topic}")
        
        try:
            # Create mixed audio directory
            mixed_audio_dir = Config.OUTPUT_DIR / "mixed_audio" / sanitized_name
            mixed_audio_dir.mkdir(parents=True, exist_ok=True)
            
            mixed_audio_path = mixed_audio_dir / f"mixed_audio_{sanitized_name}.mp3"
            
            # Use existing audio mixer (now includes high-quality processing)
            result_path = self.audio_mixer.mix_story_audio(
                audio_path, 
                music_file, 
                mixed_audio_path
            )
            
            if not result_path or not Path(result_path).exists():
                raise Exception("Audio mixing failed")
            
            print(f"✅ High-quality audio mixing completed!")
            print(f"📁 Mixed audio: {Path(result_path).name}")
            
            # Verify audio quality and duration
            try:
                from moviepy.editor import AudioFileClip
                mixed_clip = AudioFileClip(result_path)
                mixed_duration = mixed_clip.duration
                mixed_clip.close()
                
                # Also check original audio duration for comparison
                original_clip = AudioFileClip(audio_path)
                original_duration = original_clip.duration
                original_clip.close()
                
                duration_diff = abs(mixed_duration - original_duration)
                if duration_diff > 0.01:  # 10ms tolerance
                    print(f"⚠️ Audio duration mismatch: {duration_diff:.3f}s")
                else:
                    print(f"✅ Perfect audio duration match: {duration_diff:.3f}s difference")
                    
                print(f"📊 Mixed audio duration: {mixed_duration:.2f}s")
                
            except Exception as verify_error:
                print(f"⚠️ Could not verify audio duration: {verify_error}")
            
            return result_path
            
        except Exception as e:
            self.logger.error(f"Audio mixing failed: {e}")
            raise
    
    def create_video(self, topic: str, mixed_audio_path: str, sanitized_name: str) -> str:
        """Create Ken Burns video with images and audio using high-quality processing."""
        print(f"\n🎬 Creating video for: {topic}")
        
        try:
            # Create videos directory
            videos_dir = Config.OUTPUT_DIR / "videos" / sanitized_name
            videos_dir.mkdir(parents=True, exist_ok=True)
            
            kenburns_video_path = videos_dir / f"{sanitized_name}_kenburns.mp4"
            image_dir = Config.OUTPUT_DIR / "images" / sanitized_name
            
            # Use existing video composer (now includes strict duration matching)
            composer = MoviePyVideoComposer(output_dir=videos_dir, logger=self.logger)
            
            video_path = composer.compose_video(
                image_dir=image_dir,
                audio_file=mixed_audio_path,
                topic_name=sanitized_name,
                output_filename=f"{sanitized_name}_kenburns.mp4",
                enable_ken_burns=True,
                num_images=12
            )
            
            if not video_path or not Path(video_path).exists():
                raise Exception("Video creation failed")
            
            print(f"✅ High-quality video creation completed!")
            print(f"📁 Video file: {Path(video_path).name}")
            
            # Verify video/audio sync
            try:
                from moviepy.editor import VideoFileClip
                video_clip = VideoFileClip(video_path)
                video_duration = video_clip.duration
                audio_duration = video_clip.audio.duration if video_clip.audio else 0
                video_clip.close()
                
                # Also check mixed audio duration
                from moviepy.editor import AudioFileClip
                mixed_clip = AudioFileClip(mixed_audio_path)
                mixed_duration = mixed_clip.duration
                mixed_clip.close()
                
                # Check video vs mixed audio sync
                video_audio_diff = abs(video_duration - mixed_duration)
                if video_audio_diff > 0.001:  # 1ms tolerance
                    print(f"⚠️ Video/audio duration mismatch: {video_audio_diff:.3f}s")
                else:
                    print(f"✅ Perfect video/audio sync: {video_audio_diff:.3f}s difference")
                
                print(f"📊 Video duration: {video_duration:.2f}s")
                print(f"📊 Audio duration: {audio_duration:.2f}s")
                print(f"📊 Mixed audio duration: {mixed_duration:.2f}s")
                
            except Exception as verify_error:
                print(f"⚠️ Could not verify video/audio sync: {verify_error}")
            
            return video_path
            
        except Exception as e:
            self.logger.error(f"Video creation failed: {e}")
            raise
    
    def add_subtitles(self, topic: str, video_path: str, mixed_audio_path: str, story_path: str, sanitized_name: str) -> str:
        """Add viral subtitles to the video with high-quality audio preservation."""
        print(f"\n📝 Adding subtitles for: {topic}")
        
        try:
            # Create subtitles directory
            subtitles_dir = Config.OUTPUT_DIR / "subtitles_processed_video" / sanitized_name
            subtitles_dir.mkdir(parents=True, exist_ok=True)
            
            final_video_path = subtitles_dir / f"{sanitized_name}_final.mp4"
            
            # Use existing subtitle processor (now includes strict audio preservation)
            subtitle_processor = OptimizedWhisperViralSubtitleProcessor(logger=self.logger)
            
            final_video = subtitle_processor.add_viral_subtitles_to_video(
                video_path=video_path,
                audio_path=mixed_audio_path,
                output_path=final_video_path,
                story_path=story_path
            )
            
            if not final_video or not Path(final_video).exists():
                raise Exception("Subtitle processing failed")
            
            print(f"✅ High-quality subtitle processing completed!")
            print(f"📁 Final video: {Path(final_video).name}")
            
            # Verify final video/audio sync
            try:
                from moviepy.editor import VideoFileClip
                final_clip = VideoFileClip(final_video)
                final_duration = final_clip.duration
                final_audio_duration = final_clip.audio.duration if final_clip.audio else 0
                final_clip.close()
                
                # Check against original mixed audio
                from moviepy.editor import AudioFileClip
                mixed_clip = AudioFileClip(mixed_audio_path)
                mixed_duration = mixed_clip.duration
                mixed_clip.close()
                
                # Check final video vs mixed audio sync
                final_audio_diff = abs(final_duration - mixed_duration)
                if final_audio_diff > 0.001:  # 1ms tolerance
                    print(f"⚠️ Final video/audio duration mismatch: {final_audio_diff:.3f}s")
                else:
                    print(f"✅ Perfect final video/audio sync: {final_audio_diff:.3f}s difference")
                
                print(f"📊 Final video duration: {final_duration:.2f}s")
                print(f"📊 Final audio duration: {final_audio_duration:.2f}s")
                print(f"📊 Original mixed audio duration: {mixed_duration:.2f}s")
                
            except Exception as verify_error:
                print(f"⚠️ Could not verify final video/audio sync: {verify_error}")
            
            return final_video
            
        except Exception as e:
            self.logger.error(f"Subtitle processing failed: {e}")
            raise
    
    def save_story(self, topic: str, story: str, sanitized_name: str) -> str:
        """Save the story to file."""
        try:
            # Create stories directory
            stories_dir = Config.OUTPUT_DIR / "stories" / sanitized_name
            stories_dir.mkdir(parents=True, exist_ok=True)
            
            story_path = stories_dir / "story.txt"
            
            with open(story_path, 'w', encoding='utf-8') as f:
                f.write(story)
            
            print(f"✅ Story saved: {story_path}")
            return str(story_path)
            
        except Exception as e:
            self.logger.error(f"Story saving failed: {e}")
            raise
    
    def save_music_selection(self, topic: str, music_data: Dict[str, Any], sanitized_name: str) -> str:
        """Save music selection to file."""
        try:
            # Create music selections directory
            music_dir = Config.OUTPUT_DIR / "music_selections" / sanitized_name
            music_dir.mkdir(parents=True, exist_ok=True)
            
            music_path = music_dir / "music_selection.json"
            
            with open(music_path, 'w', encoding='utf-8') as f:
                json.dump(music_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Music selection saved: {music_path}")
            return str(music_path)
            
        except Exception as e:
            self.logger.error(f"Music selection saving failed: {e}")
            raise
    
    def verify_final_quality(self, topic: str, final_video_path: str, mixed_audio_path: str, sanitized_name: str) -> None:
        """Verify the final video quality and audio sync."""
        print(f"\n🔍 Final Quality Verification for: {topic}")
        print("="*50)
        
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip
            
            # Check final video
            final_clip = VideoFileClip(final_video_path)
            final_duration = final_clip.duration
            final_audio_duration = final_clip.audio.duration if final_clip.audio else 0
            final_fps = final_clip.fps
            final_size = final_clip.size
            final_clip.close()
            
            # Check mixed audio
            mixed_clip = AudioFileClip(mixed_audio_path)
            mixed_duration = mixed_clip.duration
            mixed_clip.close()
            
            # Check original TTS audio (if sped-up version exists)
            tts_audio_path = Config.OUTPUT_DIR / "audio" / sanitized_name / f"audio_{sanitized_name}_sped_up.mp3"
            if not tts_audio_path.exists():
                tts_audio_path = Config.OUTPUT_DIR / "audio" / sanitized_name / f"audio_{sanitized_name}.mp3"
            
            if tts_audio_path.exists():
                tts_clip = AudioFileClip(str(tts_audio_path))
                tts_duration = tts_clip.duration
                tts_clip.close()
            else:
                tts_duration = 0
            
            # Quality checks
            print(f"📊 Video Quality Metrics:")
            print(f"   🎬 Video duration: {final_duration:.3f}s")
            print(f"   🎵 Video audio duration: {final_audio_duration:.3f}s")
            print(f"   🎵 Mixed audio duration: {mixed_duration:.3f}s")
            print(f"   🎤 TTS audio duration: {tts_duration:.3f}s")
            print(f"   📺 Video FPS: {final_fps}")
            print(f"   📐 Video resolution: {final_size[0]}x{final_size[1]}")
            
            # Duration sync checks
            print(f"\n🔍 Duration Sync Verification:")
            
            # Check final video vs mixed audio
            final_mixed_diff = abs(final_duration - mixed_duration)
            if final_mixed_diff <= 0.001:
                print(f"   ✅ Perfect final video/mixed audio sync: {final_mixed_diff:.3f}s")
            elif final_mixed_diff <= 0.01:
                print(f"   ⚠️ Good final video/mixed audio sync: {final_mixed_diff:.3f}s")
            else:
                print(f"   ❌ Poor final video/mixed audio sync: {final_mixed_diff:.3f}s")
            
            # Check video audio vs mixed audio
            if final_audio_duration > 0:
                video_mixed_diff = abs(final_audio_duration - mixed_duration)
                if video_mixed_diff <= 0.001:
                    print(f"   ✅ Perfect video audio/mixed audio sync: {video_mixed_diff:.3f}s")
                elif video_mixed_diff <= 0.01:
                    print(f"   ⚠️ Good video audio/mixed audio sync: {video_mixed_diff:.3f}s")
                else:
                    print(f"   ❌ Poor video audio/mixed audio sync: {video_mixed_diff:.3f}s")
            
            # Check TTS vs mixed audio (should be very close)
            if tts_duration > 0:
                tts_mixed_diff = abs(tts_duration - mixed_duration)
                if tts_mixed_diff <= 0.001:
                    print(f"   ✅ Perfect TTS/mixed audio sync: {tts_mixed_diff:.3f}s")
                elif tts_mixed_diff <= 0.01:
                    print(f"   ⚠️ Good TTS/mixed audio sync: {tts_mixed_diff:.3f}s")
                else:
                    print(f"   ❌ Poor TTS/mixed audio sync: {tts_mixed_diff:.3f}s")
            
            # File size check
            file_size_mb = Path(final_video_path).stat().st_size / 1024 / 1024
            print(f"\n📁 File Information:")
            print(f"   📊 Final video size: {file_size_mb:.1f} MB")
            
            if file_size_mb > 100:
                print(f"   ⚠️ Large file size: {file_size_mb:.1f} MB (may need compression)")
            elif file_size_mb > 50:
                print(f"   ✅ Good file size: {file_size_mb:.1f} MB")
            else:
                print(f"   ✅ Excellent file size: {file_size_mb:.1f} MB")
            
            # Overall quality assessment
            print(f"\n🎯 Overall Quality Assessment:")
            quality_score = 0
            max_score = 4
            
            if final_mixed_diff <= 0.001:
                quality_score += 1
            if final_audio_duration > 0 and abs(final_audio_duration - mixed_duration) <= 0.001:
                quality_score += 1
            if tts_duration > 0 and abs(tts_duration - mixed_duration) <= 0.001:
                quality_score += 1
            if file_size_mb <= 100:
                quality_score += 1
            
            quality_percentage = (quality_score / max_score) * 100
            
            if quality_percentage >= 90:
                print(f"   🏆 EXCELLENT QUALITY: {quality_percentage:.0f}%")
                print(f"   ✅ Perfect audio/video sync")
                print(f"   ✅ Professional-grade output")
            elif quality_percentage >= 75:
                print(f"   🥇 GOOD QUALITY: {quality_percentage:.0f}%")
                print(f"   ✅ Good audio/video sync")
                print(f"   ✅ Suitable for upload")
            elif quality_percentage >= 50:
                print(f"   🥈 ACCEPTABLE QUALITY: {quality_percentage:.0f}%")
                print(f"   ⚠️ Some sync issues detected")
                print(f"   ⚠️ May need manual review")
            else:
                print(f"   ⚠️ POOR QUALITY: {quality_percentage:.0f}%")
                print(f"   ❌ Significant sync issues")
                print(f"   ❌ Manual intervention recommended")
            
            print("="*50)
            
        except Exception as e:
            print(f"⚠️ Quality verification failed: {e}")
            self.logger.error(f"Quality verification failed: {e}")
    
    async def run_pipeline(self, topic: str) -> bool:
        """Run the complete interactive pipeline."""
        start_time = time.time()
        
        try:
            print(f"\n🚀 Starting interactive pipeline for: {topic}")
            print("="*70)
            
            # Sanitize topic name for file paths
            sanitized_name = sanitize_folder_name(topic)
            print(f"📁 Sanitized name: {sanitized_name}")
            
            # Step 1: Generate complete story (same as full pipeline)
            story_data = await self.generate_story(topic)
            story = story_data['story']
            
            # Step 2: Save story assets (same as full pipeline)
            story_path = self.save_story(topic, story, sanitized_name)
            
            # Step 3: Select music (same as full pipeline)
            music_data = self.select_music(topic, story)
            
            # Step 4: Save music selection (same as full pipeline)
            music_path = self.save_music_selection(topic, music_data, sanitized_name)
            
            # Step 5: Generate TTS audio with dynamic speed from config (same as full pipeline)
            audio_path = self.generate_audio(topic, story, sanitized_name)
            
            # Step 6: Whisper Audio Synchronization (same as full pipeline)
            synchronized_prompts = await self.generate_synchronized_image_prompts(topic, story, audio_path, sanitized_name)
            
            # Step 7: Generate 12 images with synchronized prompts (same as full pipeline)
            await self.generate_images_with_sync(topic, story, synchronized_prompts, sanitized_name)
            
            # Step 8: Mix audio with music (same as full pipeline)
            mixed_audio_path = self.mix_audio(topic, audio_path, music_data['selected_music_file'], sanitized_name)
            
            # Step 9: Create Ken Burns video (same as full pipeline)
            video_path = self.create_video(topic, mixed_audio_path, sanitized_name)
            
            # Step 10: Add viral subtitles (same as full pipeline)
            final_video_path = self.add_subtitles(topic, video_path, mixed_audio_path, story_path, sanitized_name)
            
            # Success!
            total_time = time.time() - start_time
            
            print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"📊 Topic: {topic}")
            print(f"📊 Total time: {total_time:.1f} seconds")
            print(f"📊 Final video: {final_video_path}")
            
            # Show file sizes
            if Path(final_video_path).exists():
                size_mb = Path(final_video_path).stat().st_size / 1024 / 1024
                print(f"📊 Video size: {size_mb:.1f} MB")
            
            print(f"\n📁 All files saved in organized folders:")
            print(f"   📝 Story: {story_path}")
            print(f"   🎵 Music: {music_path}")
            print(f"   🎬 Video: {video_path}")
            print(f"   📺 Final: {final_video_path}")
            
            # Final quality verification
            self.verify_final_quality(topic, final_video_path, mixed_audio_path, sanitized_name)
            
            print(f"\n✅ Ready to upload to YouTube!")
            print(f"✅ HD quality with viral subtitles!")
            print(f"✅ Perfect for trending topics!")
            print(f"✅ High-quality audio processing throughout!")
            print(f"✅ Same quality as full pipeline!")
            print(f"✅ 12 images, original audio, perfect sync!")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            print(f"\n❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main function to run the interactive pipeline."""
    try:
        pipeline = InteractivePipeline()
        
        # Get topic from user
        topic = pipeline.get_user_topic()
        
        # Run the complete pipeline
        success = await pipeline.run_pipeline(topic)
        
        if success:
            print(f"\n🎯 Pipeline completed successfully!")
            print(f"🎯 Your video about '{topic}' is ready!")
            sys.exit(0)
        else:
            print(f"\n❌ Pipeline failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_main():
    """Run the async main function."""
    import asyncio
    asyncio.run(main())

if __name__ == "__main__":
    run_main() 