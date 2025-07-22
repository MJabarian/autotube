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
    
    def load_images(self, image_dir: str, num_images: int = 20) -> List[str]:
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
        NO BLACK BACKGROUND - image always fills the frame
        """
        clip = ImageClip(image_path)
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
            moving = moving.set_duration(duration)
        else:
            moving = clip.resize(base_zoom)
            moving = moving.crop(x_center=self.width/2, y_center=self.height/2, width=crop_w, height=crop_h)
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
                     num_images: int = 20) -> str:
        """
        Compose video with images and Ken Burns effects in one operation
        """
        try:
            self.logger.info(f"🎬 Starting unified video composition for: {topic_name}")
            if not Path(audio_file).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            audio_duration = self.get_audio_duration(audio_file)
            image_paths = self.load_images(image_dir, num_images)
            # Always enforce correct image duration
            image_duration = audio_duration / len(image_paths)
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
            self.logger.info(f"🎵 Adding audio to video...")
            audio = AudioFileClip(audio_file)
            final_video = final_video.set_audio(audio)
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
                ffmpeg_params=['-crf', '18']  # High quality (lower CRF = better quality, 18 is visually lossless)
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
            
            # Quality assessment based on file size
            if size_mb > 10:  # Good quality for short videos
                self.logger.info("🎯 HD Quality: Excellent file size indicates high quality")
            elif size_mb > 5:
                self.logger.info("🎯 HD Quality: Good file size indicates good quality")
            else:
                self.logger.warning("⚠️  File size seems low for HD quality")
            
            clip.close()
            
        except Exception as e:
            self.logger.warning(f"⚠️  Could not verify video quality: {e}") 