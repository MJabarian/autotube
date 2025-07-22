"""
IMPROVED Replicate Image Generation Module for AutoTube
Optimized for viral content quality and cost efficiency
"""
import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the project root to the Python path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors, validate_input
from src.replicate_image_client import OptimizedReplicateImageClient
from src.story_analyzer import StoryAnalyzer

# Initialize logger
logger = get_logger(__name__)

class OptimizedReplicateImageGenerator:
    """
    OPTIMIZED Replicate image generator for viral video content.
    
    Key improvements:
    - Quality presets for different use cases (MVP, Production, Premium)
    - Smart cost management with automatic fallbacks
    - Viral content optimizations
    - Better error handling and retry logic
    - Performance monitoring
    """
    
    def __init__(self, api_key: Optional[str] = None, default_preset: str = "production"):
        self.api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_key:
            raise ValueError("REPLICATE_API_TOKEN environment variable is required")
        
        self.client = OptimizedReplicateImageClient(self.api_key)
        self.story_analyzer = StoryAnalyzer()
        self.default_preset = default_preset
        
        # Performance tracking
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_cost": 0.0,
            "quality_modes_used": {},
            "average_generation_time": 0.0
        }
        
        logger.info(f"Initialized OptimizedReplicateImageGenerator with '{default_preset}' preset")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Log final stats
        self._log_session_stats()

    def _process_image_prompts(self, image_prompts, story_data):
        """
        Helper to process image_prompts for generate_images_for_story.
        Handles both audio-synchronized (list of dict) and simple (list of str) prompts.
        Returns (scene_descriptions, analysis)
        """
        if not image_prompts:
            return [], {'scenes': []}
        if isinstance(image_prompts[0], dict):
            # Audio-synchronized prompts: extract just the image_prompt strings
            scene_descriptions = [prompt_data['image_prompt'] for prompt_data in image_prompts]
            image_count = len(scene_descriptions)
            analysis = {
                'scenes': [type('Scene', (), {
                    'scene_type': 'audio_synchronized',
                    'duration': image_prompts[i].get('timestamp_end', 0) - image_prompts[i].get('timestamp_start', 0),
                    'timestamp_start': image_prompts[i].get('timestamp_start', 0),
                    'timestamp_end': image_prompts[i].get('timestamp_end', 0)
                })() for i in range(image_count)]
            }
        else:
            # Simple string prompts
            scene_descriptions = image_prompts
            image_count = len(image_prompts)
            analysis = {
                'scenes': [type('Scene', (), {
                    'scene_type': 'gpt_generated',
                    'duration': 3.0,
                    'timestamp_start': i * 3.0,
                    'timestamp_end': (i + 1) * 3.0
                })() for i in range(image_count)]
            }
        return scene_descriptions, analysis

    def _sanitize_folder_name(self, title: str) -> str:
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', title)
        sanitized = sanitized.replace(' ', '_')
        return sanitized[:50]

    async def generate_images_for_story(
        self,
        story_data: Dict[str, Any],
        image_prompts: List[str] = None,
        quality_preset: str = None,
        custom_folder_name: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate optimized images for viral video story.
        
        Args:
            story_data: Story information
            image_prompts: Pre-generated prompts or None to use story analyzer
            quality_preset: "mvp_testing", "production", or "premium_content"
            **kwargs: Additional generation parameters
        """
        
        preset = quality_preset or self.default_preset
        # Map all presets to 'flux-schnell' for now
        model_key = "flux-schnell"
        # Always return a dict for config
        config = {"cost_per_video": self.client.model_costs.get(model_key, 0.003)}
        
        logger.info(f"Generating images for story: {story_data.get('title', 'Unknown')}")
        logger.info(f"Using quality preset: {preset} (${config['cost_per_video']:.2f}/video)")
        
        # Handle different prompt input formats
        if image_prompts:
            scene_descriptions, analysis = self._process_image_prompts(image_prompts, story_data)
        else:
            analysis = self.story_analyzer.analyze_story(story_data)
            scene_descriptions = analysis['scene_descriptions']
        
        image_count = len(scene_descriptions)
        estimated_cost = image_count * self.client.model_costs.get(
            model_key, 0.003
        )
        
        logger.info(f"Generating {image_count} images with {preset} quality")
        logger.info(f"Estimated cost: ${estimated_cost:.3f}")
        
        # Create sanitized folder for story
        if custom_folder_name:
            story_folder = self._sanitize_folder_name(custom_folder_name)
        else:
            story_folder = self._sanitize_folder_name(story_data.get('title', 'story'))
        
        # Track performance
        start_time = asyncio.get_event_loop().time()
        self.generation_stats["total_requests"] += 1
        
        # Generate images using optimized batch processing
        loop = asyncio.get_event_loop()
        print(f"🎬 Starting optimized generation of {image_count} images...")
        
        batch_result = await loop.run_in_executor(
            None,
            lambda: self.client.batch_generate_for_viral_video(
                prompts=scene_descriptions,
                story_folder=story_folder,
                quality_mode=preset,
                fallback_enabled=kwargs.get("fallback_enabled", True)
            )
        )
        
        # Process results and create response
        successful_images = []
        failed_images = []
        total_cost = batch_result["total_cost"]
        
        for i, result in enumerate(batch_result["results"]):
            if 'error' in result:
                failed_images.append({
                    'scene_index': i,
                    'prompt': scene_descriptions[i],
                    'error': result['error']
                })
                self.generation_stats["failed_generations"] += 1
            else:
                successful_images.append({
                    'scene_index': i,
                    'image_path': result['image_path'],
                    'prompt': result['prompt'],
                    'scene_type': analysis['scenes'][i].scene_type if hasattr(analysis['scenes'][i], 'scene_type') else 'optimized',
                    'duration': analysis['scenes'][i].duration if hasattr(analysis['scenes'][i], 'duration') else 3.0,
                    'timestamp_start': analysis['scenes'][i].timestamp_start if hasattr(analysis['scenes'][i], 'timestamp_start') else i * 3.0,
                    'timestamp_end': analysis['scenes'][i].timestamp_end if hasattr(analysis['scenes'][i], 'timestamp_end') else (i + 1) * 3.0,
                    'generation_time': result.get('generation_time', 0),
                    'cost': result.get('cost', 0),
                    'quality_mode': result.get('quality_mode', preset),
                    'model_used': result.get('model_used', 'unknown'),
                    'file_size': result.get('file_size', 0)
                })
                self.generation_stats["successful_generations"] += 1
        
        # Update performance stats
        generation_time = asyncio.get_event_loop().time() - start_time
        self.generation_stats["total_cost"] += total_cost
        self.generation_stats["average_generation_time"] = (
            (self.generation_stats["average_generation_time"] * (self.generation_stats["total_requests"] - 1) + generation_time) 
            / self.generation_stats["total_requests"]
        )
        
        quality_mode = batch_result.get("final_quality_mode", preset)
        if quality_mode not in self.generation_stats["quality_modes_used"]:
            self.generation_stats["quality_modes_used"][quality_mode] = 0
        self.generation_stats["quality_modes_used"][quality_mode] += 1
        
        # Get enhanced usage stats
        usage_stats = self.client.get_usage_stats()
        
        logger.info(f"Generation complete: {len(successful_images)}/{image_count} successful")
        logger.info(f"Total cost: ${total_cost:.3f} (avg: ${total_cost/max(1, len(successful_images)):.4f}/image)")
        
        return {
            'story_title': story_data.get('title', ''),
            'total_images_requested': image_count,
            'successful_images': len(successful_images),
            'failed_images': len(failed_images),
            'images': successful_images,
            'failed_prompts': failed_images,
            'analysis': analysis,
            'total_cost': total_cost,
            'scene_descriptions': scene_descriptions,
            'usage_stats': usage_stats,
            'quality_preset': preset,
            'final_quality_mode': quality_mode,
            'generation_time': generation_time,
            'cost_per_image': total_cost / max(1, len(successful_images)),
            'performance_stats': self.generation_stats.copy()
        }
    
    def _log_session_stats(self):
        """Log final session statistics."""
        logger.info(f"Session Stats - Total requests: {self.generation_stats['total_requests']}")
        logger.info(f"Session Stats - Successful: {self.generation_stats['successful_generations']}")
        logger.info(f"Session Stats - Failed: {self.generation_stats['failed_generations']}")
        logger.info(f"Session Stats - Total cost: ${self.generation_stats['total_cost']:.4f}")
        logger.info(f"Session Stats - Avg generation time: {self.generation_stats['average_generation_time']:0.2f}")

    async def generate_image(
        self, 
        prompt: str,
        quality_preset: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a single optimized image."""
        
        preset = quality_preset or self.default_preset
        
        # Use the client's single image generation method
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.generate_and_download_image(
                prompt=prompt,
                quality_mode=preset,
                **kwargs
            )
        )

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics from the client."""
        return self.client.get_usage_stats()

    def cleanup_images(self):
        """Cleanup method for compatibility."""
        return self.client.cleanup_images()