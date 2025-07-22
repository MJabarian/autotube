"""
Optimized Whisper Viral Subtitle Processor
Scientifically optimized viral configuration with dynamic word highlighting
"""

import json
import time
import requests
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip, ImageClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import logging
from faster_whisper import WhisperModel
import re

class OptimizedWhisperViralSubtitleProcessor:
    """Scientifically optimized viral subtitle processor with dynamic word highlighting."""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        # 🎯 SCIENTIFICALLY PROVEN VIRAL SETTINGS
        self.font_size = 49  # Increased by ~3% from 48 to 49
        self.font_size_render = self.font_size * 4  # Increased to 4x for higher quality
        self.word_color = (255, 255, 0, 255)  # Electric Yellow (#FFFF00)
        self.stroke_color = (0, 0, 0, 255)  # Black outline
        self.stroke_width = 4 * 4  # Increased stroke width for 4x rendering
        # FLUX Schnell 9:16 dimensions (actual generated size from test)
        self.width = 768
        self.height = 1344
        self.vertical_position = 0.55  # 55% down from top
        self.text_height = 200  # Reduced for smaller text
        self._font_cache = {}
        
        # ⚡ VIRAL OPTIMIZATION SETTINGS
        self.min_word_duration = 0.15  # Minimum duration for each word
        self.max_word_duration = 0.8   # Maximum duration for very long words
        self.scale_pop_duration = 0.08  # Fast speech responsiveness
        
        # 🚀 SPEED OPTIMIZATION: Text caching for repeated words
        self._text_cache = {}  # Cache rendered text images
        
        # 🎬 APPEARANCE MODE: Choose between instant or animated
        self.instant_appearance = False  # Set to False for smooth easing animations
        
        # 🎨 DYNAMIC WORD HIGHLIGHTING SETTINGS
        self.current_word_color = (255, 255, 0, 255)  # Electric Yellow for current word
        self.previous_word_color = (200, 200, 200, 255)  # Gray for previous words
        self.next_word_color = (255, 255, 255, 255)  # White for next words
        self.stroke_color = (0, 0, 0, 255)  # Black outline for all words
        self.stroke_width = 4 * 2  # Thick black outline (increased slightly)
        self.word_spacing = 24  # Space between words (increased from 18 to 24)
        self.letter_spacing = 1  # Space between letters for better readability
        self.line_height = 60  # Space between lines
        
        # 📝 STORY FALLBACK SETTINGS
        self.story_fallback_enabled = False  # Disable aggressive story-based word completion
        self.min_whisper_confidence = 0.7  # Confidence threshold for using Whisper words
        self.gpt4_fallback_enabled = False  # Enable GPT-4 for advanced word placement (costs extra)
        self.gpt4_api_key = None  # Set your OpenAI API key if using GPT-4 fallback
        
        # Initialize Whisper model and font
        self._init_whisper()
        self._init_font()
    
    def _init_whisper(self):
        """Initialize faster-whisper model."""
        try:
            # Try to find cached model first
            model_paths = [
                os.path.expanduser("~/.cache/faster-whisper/small"),
                os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-small"),
                "./models/whisper-small",
                "small"  # Fallback to download
            ]
            
            model_loaded = False
            for model_path in model_paths:
                if os.path.exists(model_path) and model_path != "base":
                    try:
                        self.logger.info(f"Loading cached Whisper model from: {model_path}")
                        self.whisper_model = WhisperModel(model_path, compute_type="int8")
                        self.logger.info("Cached Whisper model loaded successfully")
                        model_loaded = True
                        break
                    except Exception as e:
                        self.logger.warning(f"Failed to load from {model_path}: {e}")
                        continue
            
            if not model_loaded:
                self.logger.info("Loading Whisper model (small) - will download if not cached...")
                self.whisper_model = WhisperModel("small", compute_type="int8")
                self.logger.info("Whisper model loaded successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def _download_font(self):
        """Download Bebas Neue font for professional typography."""
        font_path = "assets/fonts/BebasNeue-Regular.ttf"
        
        # Create fonts directory if it doesn't exist
        os.makedirs("assets/fonts", exist_ok=True)
        
        if not os.path.exists(font_path):
            try:
                self.logger.info("Downloading Bebas Neue font...")
                # Bebas Neue from a reliable source
                url = "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                
                self.logger.info("Bebas Neue font downloaded successfully")
                return font_path
            except Exception as e:
                self.logger.warning(f"Failed to download Bebas Neue font: {e}")
                return None
        
        return font_path
    
    def _init_font(self):
        """Initialize Impact font with fallbacks."""
        # Check if font is already loaded
        if self.font_size_render in self._font_cache:
            return
            
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/Impact.ttf",
            "impact.ttf",
            "Impact.ttf",
            "/System/Library/Fonts/Impact.ttf",
            "/Library/Fonts/Impact.ttf",
            "assets/fonts/Montserrat-Bold.ttf",  # Fallback
            "arial.ttf",
            "Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        
        for font_path in font_paths:
            if font_path and os.path.exists(font_path):
                try:
                    self._font_cache[self.font_size_render] = ImageFont.truetype(font_path, self.font_size_render)
                    self.logger.info(f"Loaded font: {font_path}")
                    return
                except Exception as e:
                    self.logger.warning(f"Failed to load font {font_path}: {e}")
                    continue
        
        self._font_cache[self.font_size_render] = ImageFont.load_default()
        self.logger.warning("Using default font")
    
    def _calculate_dynamic_duration(self, word: str, speech_speed: float = 1.0) -> float:
        """Calculate dynamic word duration based on word length and speech speed."""
        # Base duration calculation
        word_length = len(word)
        
        # Short words (1-3 chars): 0.15-0.25s
        if word_length <= 3:
            base_duration = 0.15 + (word_length * 0.03)
        # Medium words (4-7 chars): 0.25-0.4s
        elif word_length <= 7:
            base_duration = 0.25 + ((word_length - 3) * 0.04)
        # Long words (8+ chars): 0.4-0.8s
        else:
            base_duration = 0.4 + min((word_length - 7) * 0.05, 0.4)
        
        # Apply speech speed adjustment
        adjusted_duration = base_duration / speech_speed
        
        # Clamp to reasonable bounds
        return max(self.min_word_duration, min(adjusted_duration, self.max_word_duration))
    
    def _extract_story_words(self, story_path: str) -> List[str]:
        """Extract all words from the story file for fallback."""
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                story_text = f.read()
            
            # Clean and tokenize the story
            words = re.findall(r'\b\w+\b', story_text.lower())
            return words
        except Exception as e:
            self.logger.warning(f"Failed to extract story words: {e}")
            return []
    
    def _enhance_whisper_words_with_story(self, whisper_words: List[Dict], story_path: str) -> List[Dict]:
        """Enhance Whisper results with comprehensive story-based fallback for missing words."""
        if not self.story_fallback_enabled:
            return whisper_words
        
        story_words = self._extract_story_words(story_path)
        if not story_words:
            return whisper_words
        
        # Step 1: Fill gaps between Whisper words
        enhanced_words = []
        story_word_index = 0
        
        for i, whisper_word in enumerate(whisper_words):
            enhanced_words.append(whisper_word)
            
            # Check for gaps in timing
            if i < len(whisper_words) - 1:
                current_end = whisper_word['end']
                next_start = whisper_words[i + 1]['start']
                gap_duration = next_start - current_end
                
                # If there's a significant gap, try to fill it with story words
                if gap_duration > 0.3:  # Gap longer than 300ms
                    gap_words = []
                    gap_time = current_end
                    
                    # Try to fit story words in the gap
                    while (story_word_index < len(story_words) and 
                           gap_time < next_start - 0.1):  # Leave 100ms buffer
                        
                        story_word = story_words[story_word_index]
                        word_duration = self._calculate_dynamic_duration(story_word)
                        
                        if gap_time + word_duration <= next_start - 0.1:
                            gap_words.append({
                                'word': story_word,
                                'start': gap_time,
                                'end': gap_time + word_duration,
                                'confidence': 0.5,  # Lower confidence for inferred words
                                'source': 'story_fallback'
                            })
                            gap_time += word_duration
                            story_word_index += 1
                        else:
                            break
                    
                    # Insert gap words
                    enhanced_words.extend(gap_words)
        
        # Step 2: Ensure ALL story words are included (comprehensive fallback)
        whisper_word_set = {word['word'].lower().strip() for word in whisper_words}
        missing_words = []
        
        for i, story_word in enumerate(story_words):
            if story_word.lower() not in whisper_word_set:
                missing_words.append((i, story_word))
        
        if missing_words:
            self.logger.info(f"Found {len(missing_words)} missing words from story")
            
            # Insert missing words at appropriate positions
            enhanced_words = self._insert_missing_words_comprehensive(
                enhanced_words, missing_words, story_words
            )
        
        return enhanced_words
    
    def _insert_missing_words_comprehensive(self, enhanced_words: List[Dict], missing_words: List[tuple], story_words: List[str]) -> List[Dict]:
        """Insert missing words at their correct story positions with intelligent timing."""
        if not missing_words:
            return enhanced_words
        
        # Create a mapping of story word positions
        story_word_positions = {word: i for i, word in enumerate(story_words)}
        
        # Sort enhanced words by start time
        enhanced_words.sort(key=lambda x: x['start'])
        
        # Create a timeline of story positions vs actual timing
        story_timeline = []
        for word_data in enhanced_words:
            if word_data['source'] == 'whisper':
                word_pos = story_word_positions.get(word_data['word'].lower(), -1)
                if word_pos != -1:
                    story_timeline.append((word_pos, word_data['start'], word_data['end']))
        
        # Sort timeline by story position
        story_timeline.sort(key=lambda x: x[0])
        
        # For each missing word, calculate its timing based on story position
        for missing_idx, missing_word in missing_words:
            # Find the story words before and after this missing word
            before_timeline = [t for t in story_timeline if t[0] < missing_idx]
            after_timeline = [t for t in story_timeline if t[0] > missing_idx]
            
            # Calculate timing based on story position
            if before_timeline and after_timeline:
                # Interpolate timing between surrounding words
                last_before = before_timeline[-1]
                first_after = after_timeline[0]
                
                # Calculate story position ratio
                story_gap = first_after[0] - last_before[0]
                missing_offset = missing_idx - last_before[0]
                ratio = missing_offset / story_gap
                
                # Interpolate timing
                time_gap = first_after[1] - last_before[2]  # Start of after - end of before
                insertion_time = last_before[2] + (time_gap * ratio)
                
            elif before_timeline:
                # Insert after the last word before
                last_before = before_timeline[-1]
                insertion_time = last_before[2] + 0.15  # Small gap
                
            elif after_timeline:
                # Insert before the first word after
                first_after = after_timeline[0]
                insertion_time = max(0, first_after[1] - 0.15)  # Small gap before
                
            else:
                # No context, insert at beginning
                insertion_time = 0.0
            
            # Calculate word duration
            word_duration = self._calculate_dynamic_duration(missing_word)
            
            # Create missing word entry
            missing_word_data = {
                'word': missing_word,
                'start': insertion_time,
                'end': insertion_time + word_duration,
                'confidence': 0.3,  # Low confidence for inferred words
                'source': 'story_comprehensive_fallback',
                'story_position': missing_idx  # Track original story position
            }
            
            # Insert at appropriate position
            enhanced_words.append(missing_word_data)
            self.logger.debug(f"Inserted missing word '{missing_word}' (story pos {missing_idx}) at {insertion_time:.2f}s")
        
        # Sort by start time again
        enhanced_words.sort(key=lambda x: x['start'])
        
        return enhanced_words
    
    def extract_word_timing(self, audio_path: str, story_path: Optional[str] = None) -> List[Dict]:
        """Extract word-level timing using faster-whisper with minimal story fallback."""
        self.logger.info("Transcribing audio with word-level timing...")
        
        try:
            segments, info = self.whisper_model.transcribe(audio_path, word_timestamps=True)
            
            words_with_timing = []
            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        # Only include words with reasonable confidence
                        confidence = getattr(word, 'confidence', 0.9)
                        if confidence >= self.min_whisper_confidence:
                            # Calculate dynamic duration based on word length
                            dynamic_duration = self._calculate_dynamic_duration(word.word)
                            
                            words_with_timing.append({
                                'word': word.word,
                                'start': word.start,
                                'end': word.end,  # Use actual Whisper end time for tighter timing
                                'confidence': confidence,
                                'source': 'whisper'
                            })
            
            self.logger.info(f"Extracted {len(words_with_timing)} words with timing")
            
            # Only apply story fallback for very large gaps (>1 second) if enabled
            if story_path and self.story_fallback_enabled:
                enhanced_words = self._enhance_whisper_words_with_story_conservative(words_with_timing, story_path)
                self.logger.info(f"Enhanced to {len(enhanced_words)} words with conservative story fallback")
                return enhanced_words
            
            return words_with_timing
            
        except Exception as e:
            self.logger.error(f"Whisper transcription failed: {e}")
            raise
    
    def _create_dynamic_word_image(self, current_word: str, previous_words: List[str], next_words: List[str]) -> np.ndarray:
        """Create image showing current word highlighted with context words."""
        try:
            # Render at 2x size for anti-aliasing
            img = Image.new('RGBA', (self.width*2, self.text_height*2), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            font = self._font_cache[self.font_size_render]
            
            # Prepare all words for display
            all_words = previous_words + [current_word] + next_words
            
            # Split into two lines if needed
            if len(all_words) > 6:  # If more than 6 words, split into two lines
                mid_point = len(all_words) // 2
                line1_words = all_words[:mid_point]
                line2_words = all_words[mid_point:]
                lines = [line1_words, line2_words]
            else:
                lines = [all_words]
            
            # Calculate positions for each line
            line_positions = []
            total_height = len(lines) * self.font_size_render + (len(lines) - 1) * self.line_height * 2
            
            for i, line in enumerate(lines):
                # Calculate line width
                line_width = 0
                for word in line:
                    bbox = draw.textbbox((0, 0), word.upper(), font=font)
                    word_width = bbox[2] - bbox[0]
                    line_width += word_width + self.word_spacing
                line_width -= self.word_spacing  # Remove extra spacing from last word
                
                # Center the line
                x_start = (self.width*2 - line_width) // 2
                y = (self.text_height*2 - total_height) // 2 + i * (self.font_size_render + self.line_height * 2)
                
                line_positions.append((line, x_start, y))
            
            # Draw each line
            for line, x_start, y in line_positions:
                current_x = x_start
                
                for i, word in enumerate(line):
                    text = word.upper()
                    
                    # Determine color based on word position
                    if word == current_word:
                        text_color = self.current_word_color  # Yellow for current word
                    elif word in previous_words:
                        text_color = self.previous_word_color  # Gray for previous words
                    else:
                        text_color = self.next_word_color  # White for next words
                    
                    # Draw stroke (black outline)
                    for dx, dy in [(-self.stroke_width, 0), (self.stroke_width, 0), 
                                  (0, -self.stroke_width), (0, self.stroke_width)]:
                        draw.text((current_x + dx, y + dy), text, font=font, fill=self.stroke_color)
                    
                    # Draw main text
                    draw.text((current_x, y), text, font=font, fill=text_color)
                    
                    # Move to next word position
                    bbox = draw.textbbox((0, 0), text, font=font)
                    word_width = bbox[2] - bbox[0]
                    current_x += word_width + self.word_spacing
            
            # Convert to numpy array and resize to original size
            result_array = np.array(img)
            result_array = result_array[::2, ::2]  # Downsample to original size
            
            return result_array
            
        except Exception as e:
            self.logger.error(f"Failed to create dynamic word image: {e}")
            return None
    
    def create_viral_subtitle_clips(self, words_with_timing: List[Dict], video_duration: float = None) -> List[ImageClip]:
        """Create individual subtitle clips for each word highlighting state with transparency."""
        clips = []
        subtitle_start = time.time()
        
        self.logger.info(f"Creating individual subtitle clips from {len(words_with_timing)} words...")
        
        # Group words into chunks of 3-4 words
        word_groups = self._group_words_into_chunks(words_with_timing)
        
        # Create individual clips for each word highlighting state
        for group_index, word_group in enumerate(word_groups):
            group_words = word_group['words']
            group_start = word_group['start_time']
            group_end = word_group['end_time']
            
            self.logger.info(f"Creating clips for group {group_index + 1}: {len(group_words)} words")
            
            # Create ONE continuous clip per word group that stays visible until the next group starts
            group_start = word_group['start_time']
            group_end = word_group['end_time']
            
            # Calculate the end time for this group (either when next group starts or when this group ends)
            if group_index < len(word_groups) - 1:
                next_group_start = word_groups[group_index + 1]['start_time']
                # Add small gap to prevent overlap (50ms)
                group_clip_end = min(next_group_start - 0.05, group_end + 0.3)  # Reduced max extension to 300ms
            else:
                # For the last group, extend it only slightly to avoid staying on screen too long
                group_clip_end = group_end + 0.2  # Reduced from 500ms to 200ms
            
            # Ensure clips don't extend beyond video duration
            if video_duration:
                group_clip_end = min(group_clip_end, video_duration - 0.1)  # End 100ms before video ends
            
            group_clip_duration = group_clip_end - group_start
            
            # Create continuous clips that maintain word state during pauses
            for word_index, word_data in enumerate(group_words):
                word_start = word_data['start']
                word_end = word_data['end']
                
                # Find the start of the next word (or group end)
                if word_index < len(group_words) - 1:
                    next_word_start = group_words[word_index + 1]['start']
                    # This word should stay highlighted until the next word starts
                    clip_end = next_word_start
                else:
                    # For the last word, extend it to the group clip end
                    clip_end = group_clip_end
                
                # Tighten timing - start exactly when word starts, minimal overlap
                overlap = 0.02  # Reduced from 50ms to 20ms for tighter timing
                clip_start = max(group_start, word_start - overlap)
                clip_end = min(group_clip_end, clip_end + overlap)
                clip_duration = clip_end - clip_start
                
                # Create image for this specific word highlighting state
                word_image = self._create_simplified_word_group_image(group_words, word_index)
                if word_image is not None:
                    # Convert numpy array to PIL Image for ImageClip with RGBA support
                    pil_image = Image.fromarray(word_image, 'RGBA')
                    
                    # Create ImageClip that maintains this word state until next word
                    img_clip = ImageClip(np.array(pil_image), duration=clip_duration)
                    y_position = int(self.height * self.vertical_position)
                    img_clip = img_clip.set_position(('center', y_position)).set_start(clip_start)
                    
                    clips.append(img_clip)
                    
                    self.logger.info(f"Created continuous clip for word {word_index + 1} in group {group_index + 1}: {clip_start:.2f}s - {clip_end:.2f}s")
            
            # Progress logging
            if group_index % 10 == 0:
                elapsed = time.time() - subtitle_start
                self.logger.info(f"Created clips for {group_index + 1}/{len(word_groups)} word groups - ETA: {elapsed:.0f}s")
        
        self.logger.info(f"Created {len(clips)} individual subtitle clips")
        return clips
    
    def _group_words_into_chunks(self, words_with_timing: List[Dict]) -> List[Dict]:
        """Group words into chunks of 3-4 words with smart length limiting for mobile UI."""
        import random
        
        word_groups = []
        i = 0
        padding = 0.02  # Reduced to 20ms padding between groups to reduce lag
        
        while i < len(words_with_timing):
            # Prefer 3-4 words, avoid 5 words for mobile UI
            group_size = random.choice([3, 4])  # Removed 5-word option
            
            # Ensure we don't go beyond available words
            if i + group_size > len(words_with_timing):
                group_size = len(words_with_timing) - i
            
            if group_size == 0:
                break
            
            # Get words for this group
            group_words = words_with_timing[i:i + group_size]
            
            if not group_words:
                break
            
            # Check total character length of the group
            total_chars = sum(len(word['word']) for word in group_words)
            
            # If group is too long (>25 chars), reduce to 3 words max
            if total_chars > 25 and group_size > 3:
                group_size = 3
                group_words = words_with_timing[i:i + group_size]
                total_chars = sum(len(word['word']) for word in group_words)
            
            # Calculate group timing with minimal padding
            group_start = group_words[0]['start']
            group_end = group_words[-1]['end'] + padding
            
            # Check for overlap with previous group (but allow minimal overlap to reduce lag)
            if word_groups and group_start < word_groups[-1]['end_time'] - 0.1:  # Allow 100ms overlap
                # Adjust start time to avoid excessive overlap
                group_start = word_groups[-1]['end_time'] - 0.05  # Small overlap instead of gap
                # Adjust all word timings in this group
                time_offset = group_start - group_words[0]['start']
                for word in group_words:
                    word['start'] += time_offset
                    word['end'] += time_offset
                group_end = group_words[-1]['end'] + padding
            
            word_groups.append({
                'words': group_words,
                'start_time': group_start,
                'end_time': group_end
            })
            
            self.logger.info(f"Group {len(word_groups)}: {group_size} words ({total_chars} chars), {group_start:.2f}s - {group_end:.2f}s")
            
            i += group_size
        
        self.logger.info(f"Created {len(word_groups)} word groups with smart length limiting")
        return word_groups
    
    def _enhance_whisper_words_with_story_conservative(self, whisper_words: List[Dict], story_path: str) -> List[Dict]:
        """Conservative story fallback - only fill very large gaps (>1 second)."""
        if not whisper_words:
            return whisper_words
        
        story_words = self._extract_story_words(story_path)
        if not story_words:
            return whisper_words
        
        enhanced_words = whisper_words.copy()
        
        # Only fill gaps larger than 1 second
        min_gap_size = 1.0
        
        # Find large gaps between words
        for i in range(len(enhanced_words) - 1):
            current_end = enhanced_words[i]['end']
            next_start = enhanced_words[i + 1]['start']
            gap_size = next_start - current_end
            
            if gap_size > min_gap_size:
                # Only add 1-2 words for very large gaps
                words_to_add = min(2, int(gap_size / 0.5))  # 1 word per 0.5 seconds
                
                # Find story words that might fit
                story_word_index = 0
                for j in range(words_to_add):
                    if story_word_index < len(story_words):
                        # Add word in the middle of the gap
                        word_start = current_end + (gap_size * (j + 1)) / (words_to_add + 1)
                        word_end = word_start + 0.3  # 300ms duration
                        
                        enhanced_words.append({
                            'word': story_words[story_word_index],
                            'start': word_start,
                            'end': word_end,
                            'confidence': 0.5,  # Lower confidence for story words
                            'source': 'story_fallback'
                        })
                        story_word_index += 1
        
        # Sort by start time
        enhanced_words.sort(key=lambda x: x['start'])
        
        return enhanced_words
    

    
    def _create_simplified_word_group_image(self, group_words: List[Dict], current_word_index: int) -> np.ndarray:
        """Create image for a word group with current word highlighted."""
        try:
            # Validate inputs
            if not group_words:
                self.logger.error("No group words provided")
                return None
            
            num_words = len(group_words)
            if num_words == 0:
                self.logger.error("Empty group words")
                return None
            
            # Ensure current_word_index is within bounds
            if current_word_index < 0:
                current_word_index = 0
            elif current_word_index >= num_words:
                current_word_index = num_words - 1
            
            # Create image with 4x scale for higher quality
            img_width = self.width * 4
            img_height = self.text_height * 4
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))  # Transparent background
            draw = ImageDraw.Draw(img)
            
            # Get font
            font = self._font_cache.get(self.font_size_render)
            if not font:
                self._init_font()
                font = self._font_cache.get(self.font_size_render)
                if not font:
                    self.logger.error("Failed to load font")
                    return None
            
            # Determine layout based on number of words with bounds checking
            if num_words == 3:
                # 1 word on top, 2 words on bottom
                top_words = [group_words[0]]
                bottom_words = [group_words[1], group_words[2]]
            elif num_words == 4:
                # 2 words on top, 2 words on bottom
                top_words = [group_words[0], group_words[1]]
                bottom_words = [group_words[2], group_words[3]]
            elif num_words == 5:
                # 2 words on top, 3 words on bottom
                top_words = [group_words[0], group_words[1]]
                bottom_words = [group_words[2], group_words[3], group_words[4]]
            else:
                # Handle any other number of words (fallback to single line)
                top_words = group_words
                bottom_words = []
            
            # Calculate line positions with reduced spacing
            top_y = img_height // 3
            bottom_y = img_height * 2 // 3
            
            # Draw top line with global word index tracking
            if top_words:
                self._draw_word_line(draw, font, top_words, current_word_index, img_width // 2, top_y, 0)
            
            # Draw bottom line with global word index tracking
            if bottom_words:
                self._draw_word_line(draw, font, bottom_words, current_word_index, img_width // 2, bottom_y, len(top_words))
            
            # Convert to numpy array and resize to original size
            result_array = np.array(img)
            result_array = result_array[::4, ::4]  # Downsample from 4x to original size
            
            return result_array
            
        except Exception as e:
            self.logger.error(f"Failed to create simplified word group image: {e}")
            return None
    
    def _draw_word_line(self, draw, font, words: List[Dict], current_word_index: int, center_x: int, y: int, line_offset: int = 0):
        """Draw a line of words with proper highlighting and collision detection."""
        if not words:
            return
            
        # Calculate total width of all words with proper spacing
        total_width = 0
        word_widths = []
        
        for word_data in words:
            word = word_data['word'].upper()  # Convert to uppercase
            bbox = draw.textbbox((0, 0), word, font=font)
            word_width = bbox[2] - bbox[0]
            word_widths.append(word_width)
            total_width += word_width
        
        # Add spacing between words
        total_width += (len(words) - 1) * self.word_spacing
        
        # Start position (center the line)
        current_x = center_x - total_width // 2
        
        # Draw each word
        for i, (word_data, word_width) in enumerate(zip(words, word_widths)):
            word = word_data['word'].upper()  # Convert to uppercase
            
            # Calculate global word index within the group
            global_word_index = line_offset + i
            
            # Determine color based on whether this is the current word being spoken
            if global_word_index == current_word_index:
                text_color = self.current_word_color  # Yellow
            else:
                text_color = self.next_word_color  # White
            
            # Draw word with letter spacing
            letter_x = current_x
            for letter in word:
                # Draw stroke (outline) for each letter - 8-direction rendering for smoother borders
                for dx in range(-self.stroke_width, self.stroke_width + 1):
                    for dy in range(-self.stroke_width, self.stroke_width + 1):
                        if dx != 0 or dy != 0:  # Skip the center (0,0)
                            draw.text((letter_x + dx, y + dy), letter, font=font, fill=self.stroke_color)
                
                # Draw main letter
                draw.text((letter_x, y), letter, font=font, fill=text_color)
                
                # Move to next letter position with spacing
                letter_bbox = draw.textbbox((0, 0), letter, font=font)
                letter_width = letter_bbox[2] - letter_bbox[0]
                letter_x += letter_width + self.letter_spacing
            
            # Move to next word position with proper spacing
            current_x += word_width + self.word_spacing
    
    def add_viral_subtitles_to_video(self, video_path: str, audio_path: str, output_path: Optional[str] = None, story_path: Optional[str] = None) -> str:
        """Add scientifically optimized viral subtitles to video with story fallback."""
        total_start_time = time.time()
        
        try:
            # Extract word-level timing with story fallback
            timing_start = time.time()
            words_with_timing = self.extract_word_timing(audio_path, story_path)
            self.logger.info(f"Word timing extraction with story fallback took {time.time() - timing_start:.2f}s")
            
            # Load video with audio validation
            video_start = time.time()
            video = VideoFileClip(video_path)
            self.logger.info(f"Video loading took {time.time() - video_start:.2f}s")
            
            # Pre-composite validation
            self.logger.info(f"Original video - Duration: {video.duration:.2f}s, FPS: {video.fps}, Audio: {video.audio is not None}")
            if video.audio is None:
                self.logger.warning("Original video has no audio track!")
            
            # Create viral subtitle clips
            subtitle_start = time.time()
            subtitle_clips = self.create_viral_subtitle_clips(words_with_timing, video.duration)
            self.logger.info(f"Viral subtitle creation took {time.time() - subtitle_start:.2f}s")
            self.logger.info(f"Subtitle clips count: {len(subtitle_clips)}")
            
            # Composite video
            composite_start = time.time()
            final_video = CompositeVideoClip([video] + subtitle_clips)
            self.logger.info(f"Video composition took {time.time() - composite_start:.2f}s")
            
            # CRITICAL: Ensure exact audio duration preservation using MIXED AUDIO duration
            # Load the mixed audio to get the correct target duration
            try:
                from moviepy.editor import AudioFileClip
                mixed_audio = AudioFileClip(audio_path)
                target_audio_duration = mixed_audio.duration
                mixed_audio.close()
                self.logger.info(f"📊 Mixed audio duration (target): {target_audio_duration:.3f}s")
            except Exception as e:
                self.logger.warning(f"Could not load mixed audio, using video audio: {e}")
                target_audio_duration = video.audio.duration if video.audio else 0
            
            original_audio_duration = video.audio.duration if video.audio else 0
            final_audio_duration = final_video.audio.duration if final_video.audio else 0
            
            self.logger.info(f"Original video audio duration: {original_audio_duration:.3f}s")
            self.logger.info(f"Target mixed audio duration: {target_audio_duration:.3f}s")
            self.logger.info(f"Final video duration: {final_video.duration:.3f}s")
            self.logger.info(f"Final audio duration: {final_audio_duration:.3f}s")
            
            # CRITICAL FIX: Force exact audio duration to match MIXED AUDIO duration
            if final_video.audio and abs(final_audio_duration - target_audio_duration) > 0.01:
                self.logger.warning(f"⚠️ Audio duration mismatch: {final_audio_duration:.3f}s vs target {target_audio_duration:.3f}s")
                
                # Trim audio to exact mixed audio duration
                if final_audio_duration > target_audio_duration:
                    trimmed_audio = final_video.audio.subclip(0, target_audio_duration)
                    final_video = final_video.set_audio(trimmed_audio)
                    self.logger.info(f"🔧 Trimmed audio to mixed audio duration: {target_audio_duration:.3f}s")
                
                # Also trim video to match mixed audio duration
                if final_video.duration > target_audio_duration:
                    final_video = final_video.subclip(0, target_audio_duration)
                    self.logger.info(f"🔧 Trimmed video to mixed audio duration: {target_audio_duration:.3f}s")
            
            # Post-composite validation
            self.logger.info(f"Final video - Duration: {final_video.duration:.2f}s, Audio: {final_video.audio is not None}")
            if final_video.audio is None:
                self.logger.error("Final video lost audio track!")
                # Try to restore audio from original video
                final_video = final_video.set_audio(video.audio)
                self.logger.info("Restored audio from original video")
            
            # Set output path
            if not output_path:
                video_path_obj = Path(video_path)
                output_path = str(video_path_obj.parent / f"{video_path_obj.stem}_viral_subtitles.mp4")
            else:
                # Ensure output_path is a string, not a Path object
                output_path = str(output_path)
            
            # Write video with HD encoding settings
            write_start = time.time()
            self.logger.info(f"Writing HD viral subtitle video: {output_path}")
            final_video.write_videofile(
                output_path,
                fps=30,  # Fixed FPS for better compatibility
                codec='libx264',
                audio_codec='aac',
                audio_bitrate='320k',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset='slow',  # High-quality encoding preset
                bitrate='8000k',  # High bitrate for HD quality
                threads=4,  # Multi-threading for faster encoding
                ffmpeg_params=[
                    '-pix_fmt', 'yuv420p',  # Better compatibility
                    '-crf', '18',  # High quality (lower CRF = better quality, 18 is visually lossless)
                    '-profile:v', 'high',  # High profile for better quality
                    '-level', '4.1'  # Support for HD content
                ]
            )
            self.logger.info(f"Video writing took {time.time() - write_start:.2f}s")
            
            # CRITICAL: Final output file validation with duration verification
            self.logger.info("Validating output file with duration verification...")
            try:
                test_video = VideoFileClip(output_path)
                test_audio_duration = test_video.audio.duration if test_video.audio else 0
                test_video_duration = test_video.duration
                
                self.logger.info(f"Output file - Video Duration: {test_video_duration:.3f}s, Audio Duration: {test_audio_duration:.3f}s")
                
                # CRITICAL: Verify exact duration match against MIXED AUDIO duration
                if abs(test_audio_duration - target_audio_duration) > 0.05:
                    self.logger.error(f"❌ CRITICAL: Final audio duration mismatch! Expected: {target_audio_duration:.3f}s, Got: {test_audio_duration:.3f}s")
                    self.logger.error("This will cause end audio repetition issues!")
                else:
                    self.logger.info(f"✅ Perfect audio duration match: {test_audio_duration:.3f}s")
                
                if abs(test_video_duration - target_audio_duration) > 0.05:
                    self.logger.error(f"❌ CRITICAL: Final video duration mismatch! Expected: {target_audio_duration:.3f}s, Got: {test_video_duration:.3f}s")
                else:
                    self.logger.info(f"✅ Perfect video duration match: {test_video_duration:.3f}s")
                
                test_video.close()
            except Exception as e:
                self.logger.error(f"Output file validation failed: {e}")
            
            # Cleanup
            video.close()
            final_video.close()
            for clip in subtitle_clips:
                clip.close()
            
            self.logger.info(f"Scientifically optimized viral subtitle video created: {output_path}")
            self.logger.info(f"Total processing time: {time.time() - total_start_time:.2f}s")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to add viral subtitles: {e}")
            raise
    
    def create_viral_preview(self, audio_path: str, output_path: Optional[str] = None, duration: float = 10.0, story_path: Optional[str] = None) -> str:
        """Create a preview of scientifically optimized viral subtitles with story fallback."""
        try:
            # Extract word timing with story fallback
            words_with_timing = self.extract_word_timing(audio_path, story_path)
            
            # Filter words within preview duration
            preview_words = [w for w in words_with_timing if w['start'] < duration]
            
            # Create background
            background = ColorClip(size=(self.width, self.height), color=(0, 0, 0)).set_duration(duration)
            
            # Create viral subtitle clips
            subtitle_clips = self.create_viral_subtitle_clips(preview_words)
            
            # Composite preview
            preview_video = CompositeVideoClip([background] + subtitle_clips)
            
            if not output_path:
                output_path = "output/viral_subtitle_preview.mp4"
            
            self.logger.info(f"Creating scientifically optimized viral subtitle preview: {output_path}")
            preview_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio=False,
                preset='fast'
            )
            
            # Cleanup
            background.close()
            preview_video.close()
            for clip in subtitle_clips:
                clip.close()
            
            self.logger.info(f"Scientifically optimized viral subtitle preview created: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create viral preview: {e}")
            raise 