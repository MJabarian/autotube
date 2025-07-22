"""
Effect Presets - Predefined effects and configurations for video processing
"""

from typing import Dict, List, Any
import random

class EffectPresets:
    """Predefined effects and configurations for video processing"""
    
    @staticmethod
    def get_ken_burns_presets() -> List[Dict[str, Any]]:
        """Get preset Ken Burns effects for variety"""
        return [
            {
                'name': 'zoom_in',
                'start_scale': 1.0,
                'end_scale': 1.2,
                'start_x': 0.5,
                'end_x': 0.5,
                'start_y': 0.5,
                'end_y': 0.5,
                'description': 'Gentle zoom in from center'
            },
            {
                'name': 'zoom_out',
                'start_scale': 1.2,
                'end_scale': 1.0,
                'start_x': 0.5,
                'end_x': 0.5,
                'start_y': 0.5,
                'end_y': 0.5,
                'description': 'Gentle zoom out to center'
            },
            {
                'name': 'pan_left',
                'start_scale': 1.1,
                'end_scale': 1.1,
                'start_x': 0.4,
                'end_x': 0.6,
                'start_y': 0.5,
                'end_y': 0.5,
                'description': 'Pan from left to right'
            },
            {
                'name': 'pan_right',
                'start_scale': 1.1,
                'end_scale': 1.1,
                'start_x': 0.6,
                'end_x': 0.4,
                'start_y': 0.5,
                'end_y': 0.5,
                'description': 'Pan from right to left'
            },
            {
                'name': 'pan_up',
                'start_scale': 1.1,
                'end_scale': 1.1,
                'start_x': 0.5,
                'end_x': 0.5,
                'start_y': 0.6,
                'end_y': 0.4,
                'description': 'Pan from bottom to top'
            },
            {
                'name': 'pan_down',
                'start_scale': 1.1,
                'end_scale': 1.1,
                'start_x': 0.5,
                'end_x': 0.5,
                'start_y': 0.4,
                'end_y': 0.6,
                'description': 'Pan from top to bottom'
            },
            {
                'name': 'diagonal_zoom',
                'start_scale': 1.0,
                'end_scale': 1.15,
                'start_x': 0.4,
                'end_x': 0.6,
                'start_y': 0.4,
                'end_y': 0.6,
                'description': 'Diagonal zoom with movement'
            },
            {
                'name': 'static',
                'start_scale': 1.0,
                'end_scale': 1.0,
                'start_x': 0.5,
                'end_x': 0.5,
                'start_y': 0.5,
                'end_y': 0.5,
                'description': 'Static image (no movement)'
            }
        ]
    
    @staticmethod
    def get_random_ken_burns_effect() -> Dict[str, Any]:
        """Get a random Ken Burns effect"""
        presets = EffectPresets.get_ken_burns_presets()
        return random.choice(presets)
    
    @staticmethod
    def get_transition_presets() -> List[Dict[str, Any]]:
        """Get preset transition effects"""
        return [
            {
                'name': 'fade',
                'duration': 0.3,
                'type': 'fade',
                'description': 'Cross fade between images'
            },
            {
                'name': 'cut',
                'duration': 0.0,
                'type': 'cut',
                'description': 'Hard cut (no transition)'
            },
            {
                'name': 'slide_left',
                'duration': 0.4,
                'type': 'slide',
                'direction': 'left',
                'description': 'Slide transition left'
            },
            {
                'name': 'slide_right',
                'duration': 0.4,
                'type': 'slide',
                'direction': 'right',
                'description': 'Slide transition right'
            }
        ]
    
    @staticmethod
    def get_video_quality_presets() -> Dict[str, Dict[str, Any]]:
        """Get video quality presets for different use cases"""
        return {
            'youtube_shorts': {
                'width': 1080,
                'height': 1920,
                'fps': 30,
                'bitrate': '2M',
                'crf': 23,
                'preset': 'fast',
                'description': 'Optimized for YouTube Shorts'
            },
            'high_quality': {
                'width': 1080,
                'height': 1920,
                'fps': 30,
                'bitrate': '4M',
                'crf': 18,
                'preset': 'medium',
                'description': 'High quality for premium content'
            },
            'fast_processing': {
                'width': 1080,
                'height': 1920,
                'fps': 30,
                'bitrate': '1.5M',
                'crf': 28,
                'preset': 'ultrafast',
                'description': 'Fast processing for testing'
            }
        }
    
    @staticmethod
    def get_subtitle_presets() -> Dict[str, Dict[str, Any]]:
        """Get subtitle styling presets"""
        return {
            'youtube_shorts': {
                'font_size': 48,
                'font_color': 'white',
                'outline_color': 'black',
                'outline_width': 2,
                'background_color': 'rgba(0,0,0,0.5)',
                'position': 'bottom',
                'margin': 50,
                'description': 'Optimized for YouTube Shorts readability'
            },
            'cinematic': {
                'font_size': 36,
                'font_color': 'white',
                'outline_color': 'black',
                'outline_width': 1,
                'background_color': 'transparent',
                'position': 'bottom',
                'margin': 80,
                'description': 'Cinematic style with minimal background'
            },
            'bold': {
                'font_size': 52,
                'font_color': 'white',
                'outline_color': 'black',
                'outline_width': 3,
                'background_color': 'rgba(0,0,0,0.7)',
                'position': 'bottom',
                'margin': 40,
                'description': 'Bold style for maximum readability'
            }
        }
    
    @staticmethod
    def get_audio_presets() -> Dict[str, Dict[str, Any]]:
        """Get audio processing presets"""
        return {
            'youtube_optimized': {
                'sample_rate': 44100,
                'bitrate': '128k',
                'channels': 2,
                'normalize': True,
                'description': 'Optimized for YouTube'
            },
            'high_quality': {
                'sample_rate': 48000,
                'bitrate': '192k',
                'channels': 2,
                'normalize': True,
                'description': 'High quality audio'
            }
        } 