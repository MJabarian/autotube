"""
Timing Calculator - Utilities for video timing and synchronization
"""

from typing import List, Dict, Tuple
import json

class TimingCalculator:
    """Calculate timing for video elements and synchronization"""
    
    def __init__(self, fps: int = 30, num_images: int = 12):
        self.fps = fps
        self.num_images = num_images
        
    def calculate_image_timings(self, audio_duration: float, num_images: int = None) -> List[Dict]:
        """
        Calculate start/end times for each image based on audio duration
        
        Args:
            audio_duration: Duration of audio in seconds
            num_images: Number of images (defaults to self.num_images)
            
        Returns:
            List of dicts with 'start', 'end', 'duration' for each image
        """
        if num_images is None:
            num_images = self.num_images
            
        image_duration = audio_duration / num_images
        timings = []
        
        for i in range(num_images):
            start_time = i * image_duration
            end_time = start_time + image_duration
            
            timings.append({
                'index': i,
                'start': start_time,
                'end': end_time,
                'duration': image_duration
            })
        
        return timings
    
    def calculate_total_duration(self, audio_duration: float, num_images: int = None) -> float:
        """Calculate total video duration (should match audio duration)"""
        if num_images is None:
            num_images = self.num_images
        return audio_duration  # Video duration should match audio duration
    
    def frames_to_seconds(self, frames: int) -> float:
        """Convert frame count to seconds"""
        return frames / self.fps
    
    def seconds_to_frames(self, seconds: float) -> int:
        """Convert seconds to frame count"""
        return int(seconds * self.fps)
    
    def calculate_audio_sync_points(self, audio_duration: float, num_images: int = None) -> List[float]:
        """
        Calculate optimal sync points for audio-visual synchronization
        
        Args:
            audio_duration: Duration of audio in seconds
            num_images: Number of images to sync with (defaults to self.num_images)
            
        Returns:
            List of timestamps for sync points
        """
        if num_images is None:
            num_images = self.num_images
            
        # Calculate image duration based on audio length
        image_duration = audio_duration / num_images
        
        # Return sync points at the start of each image
        return [i * image_duration for i in range(num_images)]
    
    def create_ssml_timing_map(self, story_text: str, audio_duration: float, num_images: int = None) -> Dict:
        """
        Create timing map for SSML tags based on image transitions
        
        Args:
            story_text: The story text with potential SSML tags
            audio_duration: Duration of audio in seconds
            num_images: Number of images in the video (defaults to self.num_images)
            
        Returns:
            Dict mapping SSML tags to timing information
        """
        if num_images is None:
            num_images = self.num_images
            
        timings = self.calculate_image_timings(audio_duration, num_images)
        
        # Simple approach: divide story into chunks based on image count
        words = story_text.split()
        words_per_image = max(1, len(words) // num_images)
        
        timing_map = {
            'image_timings': timings,
            'word_timings': [],
            'ssml_sync_points': []
        }
        
        for i, timing in enumerate(timings):
            start_word = i * words_per_image
            end_word = min((i + 1) * words_per_image, len(words))
            
            timing_map['word_timings'].append({
                'image_index': i,
                'start_word': start_word,
                'end_word': end_word,
                'start_time': timing['start'],
                'end_time': timing['end']
            })
            
            # Add sync point for SSML
            timing_map['ssml_sync_points'].append({
                'time': timing['start'],
                'image_index': i
            })
        
        return timing_map 