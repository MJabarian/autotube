"""
Story analyzer for intelligent image generation.
"""
import re
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Scene:
    """Represents a visual scene from the story."""
    scene_type: str
    description: str
    timestamp_start: float
    timestamp_end: float
    duration: float
    visual_elements: List[str]
    emotional_tone: str
    action_level: str  # low, medium, high

class StoryAnalyzer:
    """Analyzes stories to extract key visual moments for image generation."""
    
    def __init__(self):
        """Initialize the story analyzer."""
        self.min_images = 12
        self.max_images = 12
        self.target_duration = 30  # seconds for 30-second videos
        
        # Scene type patterns
        self.scene_patterns = {
            'hook': r'(hook|opening|beginning|start)',
            'setup': r'(background|context|setting|establish)',
            'conflict': r'(conflict|problem|challenge|drama|tension)',
            'action': r'(action|battle|fight|struggle|movement)',
            'resolution': r'(resolution|conclusion|ending|result|outcome)',
            'twist': r'(twist|surprise|reveal|discovery)',
            'character': r'(character|person|figure|leader|hero)',
            'location': r'(location|place|setting|environment|scene)',
            'emotion': r'(emotion|feeling|mood|atmosphere|tone)'
        }
        
        # Emotional tone keywords
        self.emotional_keywords = {
            'dramatic': ['dramatic', 'intense', 'powerful', 'shocking', 'amazing'],
            'mysterious': ['mysterious', 'secret', 'hidden', 'unknown', 'mystery'],
            'triumphant': ['triumphant', 'victory', 'success', 'achievement', 'win'],
            'tragic': ['tragic', 'sad', 'loss', 'defeat', 'failure'],
            'peaceful': ['peaceful', 'calm', 'quiet', 'serene', 'tranquil'],
            'chaotic': ['chaotic', 'wild', 'crazy', 'intense', 'frenzy']
        }
        
        # Action level keywords
        self.action_keywords = {
            'high': ['battle', 'fight', 'war', 'attack', 'explosion', 'chase', 'run'],
            'medium': ['move', 'walk', 'travel', 'journey', 'search', 'explore'],
            'low': ['sit', 'stand', 'wait', 'observe', 'think', 'plan']
        }
    
    def analyze_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze story and extract scenes for image generation.
        
        Args:
            story_data: The generated story data
            
        Returns:
            Dictionary with analysis results and scene descriptions
        """
        story_text = story_data.get('story', '')
        title = story_data.get('title', '')
        
        logger.info(f"Analyzing story: {title}")
        
        # Basic story metrics
        word_count = len(story_text.split())
        sentence_count = len(re.split(r'[.!?]+', story_text))
        
        # Determine optimal image count based on story complexity
        image_count = self._calculate_image_count(word_count, sentence_count)
        
        # Extract scenes
        scenes = self._extract_scenes(story_text, image_count)
        
        # Generate scene descriptions
        scene_descriptions = self._generate_scene_descriptions(scenes, story_data)
        
        # Calculate timing
        timing = self._calculate_timing(scenes)
        
        return {
            'story_title': title,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'image_count': image_count,
            'scenes': scenes,
            'scene_descriptions': scene_descriptions,
            'timing': timing,
            'total_duration': timing['total_duration']
        }
    
    def _calculate_image_count(self, word_count: int, sentence_count: int) -> int:
        """Calculate optimal number of images based on story complexity."""
        # Always generate exactly 12 images for 30-second videos
        return 12
    
    def _extract_scenes(self, story_text: str, image_count: int) -> List[Scene]:
        """Extract key scenes from story text."""
        sentences = re.split(r'[.!?]+', story_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        scenes = []
        total_sentences = len(sentences)
        
        # Calculate sentences per scene
        sentences_per_scene = max(1, total_sentences // image_count)
        
        for i in range(0, total_sentences, sentences_per_scene):
            scene_sentences = sentences[i:i + sentences_per_scene]
            scene_text = '. '.join(scene_sentences)
            
            # Analyze scene characteristics
            scene_type = self._classify_scene(scene_text)
            emotional_tone = self._detect_emotional_tone(scene_text)
            action_level = self._detect_action_level(scene_text)
            visual_elements = self._extract_visual_elements(scene_text)
            
            # Calculate timing
            scene_duration = len(scene_sentences) * 2.5  # ~2.5 seconds per sentence
            timestamp_start = len(scenes) * scene_duration
            timestamp_end = timestamp_start + scene_duration
            
            scene = Scene(
                scene_type=scene_type,
                description=scene_text,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                duration=scene_duration,
                visual_elements=visual_elements,
                emotional_tone=emotional_tone,
                action_level=action_level
            )
            
            scenes.append(scene)
        
        return scenes
    
    def _classify_scene(self, scene_text: str) -> str:
        """Classify scene type based on content."""
        scene_lower = scene_text.lower()
        
        for scene_type, pattern in self.scene_patterns.items():
            if re.search(pattern, scene_lower):
                return scene_type
        
        # Default classification based on position
        return 'setup'
    
    def _detect_emotional_tone(self, scene_text: str) -> str:
        """Detect emotional tone of the scene."""
        scene_lower = scene_text.lower()
        
        for tone, keywords in self.emotional_keywords.items():
            if any(keyword in scene_lower for keyword in keywords):
                return tone
        
        return 'neutral'
    
    def _detect_action_level(self, scene_text: str) -> str:
        """Detect action level of the scene."""
        scene_lower = scene_text.lower()
        
        for level, keywords in self.action_keywords.items():
            if any(keyword in scene_lower for keyword in keywords):
                return level
        
        return 'low'
    
    def _extract_visual_elements(self, scene_text: str) -> List[str]:
        """Extract visual elements from scene text."""
        visual_elements = []
        
        # Common visual elements
        visual_patterns = [
            r'\b(man|woman|person|figure|character)\b',
            r'\b(building|house|castle|tower|structure)\b',
            r'\b(mountain|hill|valley|forest|river|ocean)\b',
            r'\b(sun|moon|stars|sky|clouds)\b',
            r'\b(sword|shield|armor|weapon|tool)\b',
            r'\b(horse|carriage|ship|vehicle)\b',
            r'\b(fire|smoke|lightning|storm)\b'
        ]
        
        for pattern in visual_patterns:
            matches = re.findall(pattern, scene_text, re.IGNORECASE)
            visual_elements.extend(matches)
        
        return list(set(visual_elements))  # Remove duplicates
    
    def _generate_scene_descriptions(self, scenes: List[Scene], story_data: Dict[str, Any]) -> List[str]:
        """Generate detailed image prompts for each scene."""
        title = story_data.get('title', '')
        story_text = story_data.get('story', '')
        
        scene_descriptions = []
        
        for i, scene in enumerate(scenes):
            # Base prompt
            prompt = f"Historical scene from '{title}': "
            
            # Add scene-specific details
            if scene.scene_type == 'hook':
                prompt += f"Dramatic opening scene with {scene.emotional_tone} atmosphere. "
            elif scene.scene_type == 'action':
                prompt += f"High-action scene with {scene.action_level} movement. "
            elif scene.scene_type == 'resolution':
                prompt += f"Concluding scene with {scene.emotional_tone} mood. "
            else:
                prompt += f"{scene.scene_type.title()} scene with {scene.emotional_tone} tone. "
            
            # Add visual elements
            if scene.visual_elements:
                elements_str = ', '.join(scene.visual_elements[:3])  # Limit to 3 elements
                prompt += f"Features: {elements_str}. "
            
            # Add cinematic specifications
            prompt += "Cinematic photography, high quality, detailed, photorealistic, historical accuracy, dramatic lighting, professional composition."
            
            scene_descriptions.append(prompt)
        
        return scene_descriptions
    
    def _calculate_timing(self, scenes: List[Scene]) -> Dict[str, Any]:
        """Calculate timing for video composition."""
        total_duration = sum(scene.duration for scene in scenes)
        
        # Adjust durations to fit target
        if total_duration > self.target_duration:
            scale_factor = self.target_duration / total_duration
            for scene in scenes:
                scene.duration *= scale_factor
                scene.timestamp_end = scene.timestamp_start + scene.duration
            total_duration = self.target_duration
        
        return {
            'total_duration': total_duration,
            'scene_durations': [scene.duration for scene in scenes],
            'scene_timestamps': [(scene.timestamp_start, scene.timestamp_end) for scene in scenes]
        }

# Example usage:
# analyzer = StoryAnalyzer()
# analysis = analyzer.analyze_story(story_data)
# print(f"Generated {analysis['image_count']} scene descriptions")
# for i, desc in enumerate(analysis['scene_descriptions']):
#     print(f"Scene {i+1}: {desc[:100]}...") 