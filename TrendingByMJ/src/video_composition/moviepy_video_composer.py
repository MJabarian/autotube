"""
Unified MoviePy Video Composer
Stitches images and applies Ken Burns effects in one operation
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Literal
import logging
import math
import tempfile
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx import resize, crop

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

def setup_logger(name: str = "moviepy_video_composer") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

class MoviePyVideoComposer:
    """
    Unified MoviePy Video Composer
    Stitches images and applies Ken Burns effects in one operation
    """
    
    def __init__(self, output_dir: str = None, logger: Optional[logging.Logger] = None):
        # Use absolute path to ensure consistent output location
        if output_dir is None:
            self.output_dir = Config.OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or setup_logger()
        # FLUX Schnell 9:16 dimensions (actual generated size from test)
        # Maintain 768x1344 throughout pipeline - NO downscaling
        self.width = 768
        self.height = 1344
        self.fps = 30
        self.logger.info("✅ MoviePy Video Composer initialized")
        self.logger.info(f"📐 Video dimensions: {self.width}x{self.height} (maintained throughout pipeline)")
    
    def get_audio_duration(self, audio_file: str) -> float:
        """Get audio duration using MoviePy"""
        audio = AudioFileClip(audio_file)
        duration = audio.duration
        audio.close()
        return duration
    
    def get_core_effects(self) -> List[str]:
        """Get the 4 core Ken Burns effects used consistently in all videos"""
        return ['zoom_in', 'zoom_out', 'pan_left', 'pan_right']
    
    def generate_random_effects(self, num_images: int) -> List[str]:
        """
        Generate random effects ensuring no back-to-back repeats
        """
        import random
        import time
        
        # Set random seed for true randomization
        random.seed(time.time_ns())
        
        effects = self.get_core_effects()
        result = []
        last_effect = None
        
        for i in range(num_images):
            # Get available effects (exclude the last one used)
            available = [e for e in effects if e != last_effect]
            # Randomly select from available effects
            selected = random.choice(available)
            result.append(selected)
            last_effect = selected
        
        return result
    
    def load_images(self, image_dir: str, num_images: int = 6) -> List[str]:
        """Load and validate images from directory"""
        image_dir = Path(image_dir)
        if not image_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {image_dir}")
        
        # Get all image files, sorted by name
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            for pattern in [f"*{ext}", f"*{ext.upper()}"]:
                image_files.extend(image_dir.glob(pattern))
        
        # Remove duplicates and sort by filename
        image_files = list(set(image_files))
        image_files.sort(key=lambda x: x.name)
        
        if not image_files:
            raise FileNotFoundError(f"No image files found in {image_dir}")
        
        # Validate we have enough images
        if len(image_files) < num_images:
            self.logger.warning(f"⚠️  Only {len(image_files)} images found, need {num_images}")
            self.logger.info("Will use available images and repeat if necessary")
        
        # Take first N images (or repeat if we have fewer)
        selected_images = []
        for i in range(num_images):
            selected_images.append(str(image_files[i % len(image_files)]))
        
        # Validate image dimensions (ensure they're 768x1344)
        from PIL import Image
        for img_path in selected_images[:3]:  # Check first 3 images
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    if width != self.width or height != self.height:
                        self.logger.warning(f"⚠️  Image {Path(img_path).name} is {width}x{height}, expected {self.width}x{self.height}")
                        self.logger.info("Images will be resized to maintain 768x1344 throughout pipeline")
            except Exception as e:
                self.logger.warning(f"⚠️  Could not validate image {Path(img_path).name}: {e}")
        
        self.logger.info(f"📸 Loaded {len(selected_images)} images for video")
        self.logger.info(f"📐 Target dimensions: {self.width}x{self.height} (no downscaling)")
        return selected_images
    
    def create_ken_burns_clip(self, image_path: str, effect: Literal['zoom_in','zoom_out','pan_left','pan_right'], duration: float):
        """
        Create a MoviePy clip with Ken Burns effect from an image
        CRITICAL: Ensures exact duration to prevent video/audio sync issues
        """
        # Create base clip with exact duration first
        clip = ImageClip(image_path, duration=duration)
        base_zoom = 1.1
        zoom_range = 0.1  # 10% zoom in/out for effect
        pan_zoom = 1.2    # 20% zoom for pan effects
        crop_w, crop_h = self.width, self.height
        
        if effect == 'zoom_in':
            def zoom(t):
                return 1.0 + (zoom_range * (t / duration))
            moving = clip.resize(zoom)
            moving = moving.crop(x_center=self.width/2, y_center=self.height/2, width=crop_w, height=crop_h)
        elif effect == 'zoom_out':
            def zoom(t):
                return base_zoom - (zoom_range * (t / duration))
            moving = clip.resize(zoom)
            moving = moving.crop(x_center=self.width/2, y_center=self.height/2, width=crop_w, height=crop_h)
        elif effect == 'pan_left' or effect == 'pan_right':
            # Always zoom in for pan
            zoomed = clip.resize(pan_zoom)
            # Calculate max horizontal offset (in zoomed image)
            img_w, img_h = zoomed.size
            max_offset = (img_w - crop_w) // 2
            def crop_x(t):
                frac = t / duration
                if effect == 'pan_right':
                    # Start at left, end at right
                    x = -max_offset + 2 * max_offset * frac
                else:
                    # pan_left: start at right, end at left
                    x = max_offset - 2 * max_offset * frac
                return x
            def crop_func(get_frame, t):
                x = crop_x(t)
                y = (img_h - crop_h) // 2
                frame = get_frame(t)
                # Crop the frame to (x, y, crop_w, crop_h)
                return frame[int(y):int(y+crop_h), int(x+img_w//2-crop_w//2):int(x+img_w//2+crop_w//2), :]
            moving = zoomed.fl(crop_func, apply_to=['mask'])
            moving = moving.set_position(('center', 'center'))
        else:
            moving = clip.resize(base_zoom)
            moving = moving.crop(x_center=self.width/2, y_center=self.height/2, width=crop_w, height=crop_h)
        
        # CRITICAL: Force exact duration to prevent sync issues
        moving = moving.set_duration(duration)
        
        # Double-check duration is correct
        if abs(moving.duration - duration) > 0.001:  # 1ms tolerance
            self.logger.warning(f"⚠️ Duration mismatch in Ken Burns clip: {moving.duration:.3f}s vs {duration:.3f}s")
            # Force exact duration
            moving = moving.set_duration(duration)
        
        return moving
    
    def create_basic_clip(self, image_path: str, duration: float):
        """
        Create a basic MoviePy clip from an image (no effects)
        Maintains 768x1344 dimensions throughout pipeline
        """
        clip = ImageClip(image_path, duration=duration)
        # Ensure exact dimensions - no downscaling, maintain aspect ratio
        clip = clip.resize((self.width, self.height))
        self.logger.debug(f"📐 Basic clip created: {self.width}x{self.height}")
        return clip
    
    def compose_video(self, 
                     image_dir: str, 
                     audio_file: str, 
                     topic_name: str,
                     output_filename: Optional[str] = None,
                     enable_ken_burns: bool = True,
                     effects: Optional[List[str]] = None,
                     num_images: int = 6) -> str:
        """
        Compose video with images and Ken Burns effects in one operation
        """
        try:
            self.logger.info(f"🎬 Starting unified video composition for: {topic_name}")
            if not Path(audio_file).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            # Get the actual target duration from the audio file
            audio_duration = self.get_audio_duration(audio_file)
            image_paths = self.load_images(image_dir, num_images)
            
            # CRITICAL: Use the exact audio duration for image timing
            image_duration = audio_duration / len(image_paths)
            
            # Log the exact timing for verification
            self.logger.info(f"🎵 Audio duration: {audio_duration:.3f}s")
            self.logger.info(f"📸 Number of images: {len(image_paths)}")
            self.logger.info(f"⏱️ Calculated image duration: {image_duration:.3f}s")
            self.logger.info(f"📐 Expected total video duration: {audio_duration:.3f}s")
            self.logger.info(f"⏱️  Image duration: {image_duration:.2f} seconds per image")
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if not output_filename:
                if enable_ken_burns:
                    output_filename = f"{topic_name}_kenburns.mp4"
                else:
                    output_filename = f"{topic_name}_basic.mp4"
            output_path = self.output_dir / output_filename
            self.logger.info(f"🔗 Creating video: {output_path}")
            if enable_ken_burns and not effects:
                # Use random effects with no back-to-back repeats
                effects = self.generate_random_effects(num_images)
                self.logger.info(f"🎲 Generated random effects sequence: {effects[:5]}..." if len(effects) > 5 else f"🎲 Generated random effects sequence: {effects}")
            clips = []
            for i, image_path in enumerate(image_paths):
                self.logger.info(f"📸 Processing image {i+1}/{len(image_paths)}: {Path(image_path).name}")
                if enable_ken_burns and effects:
                    effect = effects[i % len(effects)]
                    self.logger.info(f"✨ Applying {effect} effect")
                    clip = self.create_ken_burns_clip(image_path, effect, image_duration)
                else:
                    clip = self.create_basic_clip(image_path, image_duration)
                clips.append(clip)
            self.logger.info(f"🔗 Concatenating {len(clips)} clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # CRITICAL: Force video duration to match expected duration exactly
            expected_duration = len(image_paths) * image_duration
            actual_duration = final_video.duration
            
            self.logger.info(f"📐 Expected video duration: {expected_duration:.3f}s")
            self.logger.info(f"📹 Actual video duration: {actual_duration:.3f}s")
            
            # AGGRESSIVE: Force exact duration to prevent sync issues (NO TOLERANCE)
            if abs(actual_duration - expected_duration) > 0.001:  # 1ms tolerance
                self.logger.warning(f"⚠️ Video duration mismatch: {abs(actual_duration - expected_duration):.3f}s")
                if actual_duration > expected_duration:
                    final_video = final_video.subclip(0, expected_duration)
                    self.logger.info(f"✂️ AGGRESSIVE TRIM: Video {actual_duration:.3f}s → {expected_duration:.3f}s")
                else:
                    # Extend last frame if video is too short
                    last_clip = clips[-1]
                    extension_needed = expected_duration - actual_duration
                    extension_clip = last_clip.set_duration(extension_needed)
                    final_video = concatenate_videoclips([final_video, extension_clip], method="compose")
                    self.logger.info(f"🔧 Extended video from {actual_duration:.3f}s to {expected_duration:.3f}s")
                actual_duration = expected_duration
            else:
                self.logger.info(f"✅ Video duration matches expected: {actual_duration:.3f}s")
            
            # CRITICAL: Ensure exact audio/video synchronization
            self.logger.info(f"🎵 Adding audio to video with exact duration matching...")
            audio = AudioFileClip(audio_file)
            
            # Get exact durations
            video_duration = final_video.duration
            audio_duration = audio.duration
            
            self.logger.info(f"📹 Video duration: {video_duration:.3f}s")
            self.logger.info(f"🎵 Audio duration: {audio_duration:.3f}s")
            
            # CRITICAL: ALWAYS trim video to match audio duration exactly (ZERO TOLERANCE)
            # This prevents the issue where images continue showing after audio ends
            if abs(audio_duration - video_duration) > 0.0001:  # 0.1ms tolerance (essentially zero)
                if audio_duration > video_duration:
                    audio = audio.subclip(0, video_duration)
                    self.logger.info(f"✂️ Trimmed audio from {audio_duration:.3f}s to {video_duration:.3f}s")
                else:
                    # CRITICAL FIX: Always trim video to match audio (prevent end audio issues)
                    final_video = final_video.subclip(0, audio_duration)
                    self.logger.info(f"🔧 CRITICAL FIX: Trimmed video from {video_duration:.3f}s to {audio_duration:.3f}s")
                    self.logger.info(f"🔧 This prevents images from showing after audio ends")
                    video_duration = audio_duration
            else:
                self.logger.info(f"✅ Perfect duration match: {audio_duration:.3f}s")
            
            # CRITICAL: ALWAYS ensure video never exceeds audio duration (ZERO TOLERANCE)
            # This is the main fix for the "images showing after audio ends" issue
            if audio_duration > video_duration:
                audio = audio.subclip(0, video_duration)
                self.logger.info(f"🔧 Aggressive trim: Audio {audio_duration:.3f}s → {video_duration:.3f}s")
            elif audio_duration < video_duration:
                # CRITICAL FIX: Always trim video to match audio (prevents end audio issues)
                final_video = final_video.subclip(0, audio_duration)
                self.logger.info(f"🔧 CRITICAL FIX: Video {video_duration:.3f}s → {audio_duration:.3f}s")
                self.logger.info(f"🔧 This ensures video ends exactly when audio ends")
                video_duration = audio_duration
            else:
                self.logger.info(f"✅ Perfect audio/video duration match: {audio_duration:.3f}s")
            
            # Set audio with exact duration match
            final_video = final_video.set_audio(audio)
            
            # CRITICAL VERIFICATION: Final check to ensure video ends exactly when audio ends
            final_audio_duration = final_video.audio.duration
            final_video_duration = final_video.duration
            
            self.logger.info(f"🔍 Final verification - Audio: {final_audio_duration:.3f}s, Video: {final_video_duration:.3f}s")
            
            if abs(final_audio_duration - final_video_duration) > 0.0001:  # 0.1ms tolerance (essentially zero)
                self.logger.warning(f"⚠️ Final sync mismatch: Audio {final_audio_duration:.3f}s vs Video {final_video_duration:.3f}s")
                
                # CRITICAL FIX: Force video to match audio duration exactly
                if final_video_duration > final_audio_duration:
                    self.logger.warning(f"⚠️ Video still longer than audio - this will cause images to show after audio ends!")
                    # Force trim the video to match audio
                    try:
                        final_video = final_video.subclip(0, final_audio_duration)
                        self.logger.info(f"🔧 CRITICAL FIX: Forced video trim to match audio: {final_audio_duration:.3f}s")
                        self.logger.info(f"🔧 This prevents the 'images showing after audio ends' issue")
                    except Exception as e:
                        self.logger.error(f"❌ Failed to force trim video: {e}")
                elif final_audio_duration > final_video_duration:
                    self.logger.warning(f"⚠️ Audio longer than video - this may cause end audio issues")
                    # Try to force trim the audio
                    try:
                        trimmed_audio = final_video.audio.subclip(0, final_video_duration)
                        final_video = final_video.set_audio(trimmed_audio)
                        self.logger.info(f"🔧 Forced audio trim to match video: {final_video_duration:.3f}s")
                    except Exception as e:
                        self.logger.error(f"❌ Failed to force trim audio: {e}")
            else:
                self.logger.info(f"✅ Perfect audio/video sync: {final_audio_duration:.3f}s")
                self.logger.info(f"✅ Video will end exactly when audio ends")
            self.logger.info(f"💾 Writing final video: {output_path}")
            import tempfile
            temp_audio = tempfile.NamedTemporaryFile(suffix='.m4a', delete=False)
            temp_audio.close()
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                audio_bitrate='320k',
                audio_fps=44100,  # Ensure high audio sample rate
                temp_audiofile=temp_audio.name,
                remove_temp=True,
                preset='slow',  # High-quality encoding preset
                bitrate='8000k',  # High bitrate for HD quality
                threads=4,  # Multi-threading for faster encoding
                ffmpeg_params=[
                    '-crf', '18',  # High quality (lower CRF = better quality, 18 is visually lossless)
                    '-profile:v', 'high',  # High profile for better quality
                    '-level', '4.1',  # Support for HD content
                    '-pix_fmt', 'yuv420p'  # Better compatibility
                ]
            )
            try:
                os.unlink(temp_audio.name)
            except:
                pass
            final_video.close()
            audio.close()
            for clip in clips:
                clip.close()
            
            # Verify final video quality and dimensions
            self.verify_video_quality(str(output_path))
            
            self.logger.info(f"✅ Video composition completed: {output_path}")
            self.logger.info(f"🎯 HD Quality Video: {self.width}x{self.height} @ {self.fps}fps")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"❌ Error in video composition: {str(e)}")
            raise
    
    def verify_video_quality(self, video_path: str):
        """Verify the final video meets HD quality standards"""
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            
            # Check dimensions
            width, height = clip.size
            if width != self.width or height != self.height:
                self.logger.warning(f"⚠️  Video dimensions: {width}x{height}, expected: {self.width}x{self.height}")
            else:
                self.logger.info(f"✅ Video dimensions verified: {width}x{height}")
            
            # Check FPS
            if clip.fps != self.fps:
                self.logger.warning(f"⚠️  Video FPS: {clip.fps}, expected: {self.fps}")
            else:
                self.logger.info(f"✅ Video FPS verified: {clip.fps}")
            
            # Check duration
            duration = clip.duration
            self.logger.info(f"✅ Video duration: {duration:.2f} seconds")
            
            # Check file size for quality indication
            file_size = Path(video_path).stat().st_size
            size_mb = file_size / (1024 * 1024)
            self.logger.info(f"✅ Video file size: {size_mb:.1f} MB")
            
            # Quality assessment based on file size and dimensions
            if width >= 1920 and height >= 1080:
                self.logger.info(f"🎯 4K/HD Quality: {width}x{height} resolution")
            elif width >= 1280 and height >= 720:
                self.logger.info(f"🎯 HD Quality: {width}x{height} resolution")
            else:
                self.logger.warning(f"⚠️  Resolution seems low for HD: {width}x{height}")
            
            # File size quality assessment
            if size_mb > 15:  # Excellent quality for short videos
                self.logger.info("🎯 HD Quality: Excellent file size indicates high quality")
            elif size_mb > 8:
                self.logger.info("🎯 HD Quality: Good file size indicates good quality")
            elif size_mb > 5:
                self.logger.info("🎯 HD Quality: Acceptable file size")
            else:
                self.logger.warning("⚠️  File size seems low for HD quality")
            
            clip.close()
            
        except Exception as e:
            self.logger.warning(f"⚠️  Could not verify video quality: {e}") 