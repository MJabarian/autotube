"""
Whisper Audio Synchronizer
Uses Whisper to get exact word timestamps from generated audio for precise image synchronization
"""

import os
import json
import logging
import sys
import openai
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from faster_whisper import WhisperModel
import numpy as np

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

class WhisperAudioSynchronizer:
    """
    Uses Whisper to synchronize audio content with image generation
    Provides exact word timestamps for precise image timing
    """
    
    def __init__(self, model_name: str = "base", logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.model_name = model_name
        self.model = None
        self.logger.info(f"🎤 Initializing Whisper Audio Synchronizer with model: {model_name}")
        
        # Content analysis keywords for classification
        self.content_keywords = {
            'character_action': [
                'walked', 'ran', 'fought', 'moved', 'entered', 'left', 'approached', 
                'reached', 'climbed', 'descended', 'opened', 'closed', 'picked', 'dropped',
                'grabbed', 'pushed', 'pulled', 'jumped', 'fell', 'stood', 'sat', 'lay'
            ],
            'environment_description': [
                'palace', 'room', 'building', 'city', 'street', 'forest', 'mountain', 
                'river', 'ocean', 'desert', 'garden', 'chamber', 'hall', 'temple',
                'castle', 'fortress', 'village', 'town', 'landscape', 'scenery'
            ],
            'emotional_moment': [
                'felt', 'thought', 'realized', 'understood', 'feared', 'hoped', 'loved',
                'hated', 'worried', 'excited', 'sad', 'happy', 'angry', 'surprised',
                'confused', 'determined', 'desperate', 'proud', 'ashamed', 'grateful'
            ],
            'dialogue_confrontation': [
                'said', 'spoke', 'told', 'asked', 'answered', 'replied', 'shouted',
                'whispered', 'argued', 'debated', 'discussed', 'agreed', 'disagreed',
                'confronted', 'challenged', 'threatened', 'promised', 'warned'
            ],
            'exposition_setup': [
                'was', 'were', 'had', 'been', 'became', 'remained', 'stayed',
                'lived', 'ruled', 'governed', 'controlled', 'owned', 'possessed',
                'belonged', 'existed', 'occurred', 'happened', 'took place'
            ]
        }
        
        # Shot type mapping based on content type - more flexible
        self.shot_type_mapping = {
            'character_action': ['medium_shot', 'wide_shot', 'close_up', 'establishing_shot'],
            'environment_description': ['establishing_shot', 'wide_shot', 'close_up', 'medium_shot'],
            'emotional_moment': ['close_up', 'medium_shot', 'wide_shot', 'establishing_shot'],
            'dialogue_confrontation': ['medium_shot', 'two_shot', 'close_up', 'wide_shot'],
            'exposition_setup': ['establishing_shot', 'wide_shot', 'medium_shot', 'close_up']
        }
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("whisper_audio_synchronizer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        return logger
    
    def load_model(self):
        """Load faster-whisper model (lazy loading to save memory)"""
        if self.model is None:
            self.logger.info(f"📥 Loading faster-whisper model: {self.model_name}")
            self.model = WhisperModel(self.model_name, compute_type="int8")
            self.logger.info("✅ faster-whisper model loaded successfully")
        return self.model
    
    def transcribe_audio_with_timestamps(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio and get word-level timestamps
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary with transcription data including word timestamps
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self.logger.info(f"🎤 Transcribing audio: {audio_path}")
        
        # Load model if not loaded
        model = self.load_model()
        
        # Transcribe with word timestamps using faster-whisper
        segments, info = model.transcribe(
            audio_path,
            word_timestamps=True
        )
        
        # Convert faster-whisper format to standard format
        result = {
            'segments': [],
            'text': ''
        }
        
        for segment in segments:
            segment_data = {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text,
                'words': []
            }
            
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    word_data = {
                        'word': word.word,
                        'start': word.start,
                        'end': word.end,
                        'probability': getattr(word, 'probability', 0.0)
                    }
                    segment_data['words'].append(word_data)
            
            result['segments'].append(segment_data)
            result['text'] += segment.text
        
        self.logger.info(f"✅ Transcription completed. Duration: {result['segments'][-1]['end']:.2f}s")
        
        return result
    
    def extract_word_timestamps(self, transcription_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract word-level timestamps from Whisper result
        
        Args:
            transcription_result: Result from Whisper transcription
            
        Returns:
            List of words with start/end timestamps
        """
        words = []
        
        for segment in transcription_result['segments']:
            if 'words' in segment:
                for word_info in segment['words']:
                    words.append({
                        'word': word_info['word'].strip(),
                        'start': word_info['start'],
                        'end': word_info['end'],
                        'confidence': word_info.get('probability', 0.0)
                    })
        
        self.logger.info(f"📝 Extracted {len(words)} words with timestamps")
        return words
    
    def create_image_timing_schedule(
        self, 
        word_timestamps: List[Dict[str, Any]], 
        num_images: int = 12,
        original_story: str = None
    ) -> List[Dict[str, Any]]:
        """
        Create image timing schedule based on word timestamps
        
        Args:
            word_timestamps: List of words with timestamps
            num_images: Number of images to generate
            original_story: Original story text for reference
            
        Returns:
            List of image timing data
        """
        if not word_timestamps:
            raise ValueError("No word timestamps provided")
        
        # Get total audio duration
        total_duration = word_timestamps[-1]['end']
        image_duration = total_duration / num_images
        
        self.logger.info(f"⏱️  Total duration: {total_duration:.2f}s, Image duration: {image_duration:.2f}s")
        
        # Create image timing schedule
        image_schedule = []
        
        for i in range(num_images):
            start_time = i * image_duration
            end_time = (i + 1) * image_duration
            
            # Find words that fall within this time window
            words_in_window = [
                word for word in word_timestamps 
                if word['start'] >= start_time and word['end'] <= end_time
            ]
            
            # Get words that overlap with this window
            overlapping_words = [
                word for word in word_timestamps 
                if (word['start'] < end_time and word['end'] > start_time)
            ]
            
            # Create audio content text
            if words_in_window:
                audio_content = ' '.join([word['word'] for word in words_in_window])
            elif overlapping_words:
                audio_content = ' '.join([word['word'] for word in overlapping_words])
            else:
                audio_content = f"Audio segment {i+1}"
            
            image_schedule.append({
                'image_number': i + 1,
                'timestamp_start': start_time,
                'timestamp_end': end_time,
                'audio_content': audio_content,
                'words_in_segment': len(words_in_window),
                'confidence_avg': np.mean([word['confidence'] for word in words_in_window]) if words_in_window else 0.0
            })
        
        self.logger.info(f"📅 Created image timing schedule for {num_images} images")
        return image_schedule
    
    async def analyze_content_type(self, audio_content: str) -> str:
        """
        Analyze audio content to determine the type of narrative content
        
        Args:
            audio_content: The audio text to analyze
            
        Returns:
            Content type: character_action, environment_description, emotional_moment, 
                         dialogue_confrontation, or exposition_setup
        """
        # Use GPT-4 for contextual analysis instead of rigid keyword matching
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from llm.story_generator import StoryGenerator
            
            async with StoryGenerator() as generator:
                prompt = f"""
                Analyze this audio segment and classify its narrative purpose:
                
                AUDIO: "{audio_content}"
                
                Classify as ONE of these types:
                - character_action: Someone doing something physical, movement, action, behavior
                - environment_description: Describing a place, location, setting, atmosphere
                - emotional_moment: Feelings, thoughts, reactions, internal states, emotional responses
                - dialogue_confrontation: Conversation, conflict, interaction between people, speaking
                - exposition_setup: Background information, context, setup, historical facts
                
                Consider the CONTEXT and MEANING, not just individual words.
                Examples:
                - "Her eyes blazed with fury" → emotional_moment (even though "eyes" isn't an emotion keyword)
                - "The palace trembled under his footsteps" → character_action (the trembling shows his movement/impact)
                - "They exchanged knowing glances" → dialogue_confrontation (non-verbal communication)
                
                Return only the classification (character_action, environment_description, emotional_moment, dialogue_confrontation, or exposition_setup)
                """
                
                response = await generator.client.chat.completions.create(
                    model=generator.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing narrative content for visual storytelling."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=50,
                    temperature=0.1,
                )
                
                return response.choices[0].message.content.strip().lower()
            
        except Exception as e:
            self.logger.warning(f"GPT analysis failed, falling back to keyword matching: {e}")
            # Fallback to keyword matching
            audio_lower = audio_content.lower()
            scores = {}
            for content_type, keywords in self.content_keywords.items():
                score = sum(1 for keyword in keywords if keyword in audio_lower)
                scores[content_type] = score
            
            if max(scores.values()) == 0:
                return 'exposition_setup'
            
            return max(scores, key=scores.get)
    
    def determine_shot_type(self, content_type: str, image_number: int, previous_shot_types: List[str]) -> str:
        """
        Determine the appropriate shot type based on content type and story progression
        
        Args:
            content_type: The analyzed content type
            image_number: Current image number (1-12)
            previous_shot_types: List of previous shot types to avoid repetition
            
        Returns:
            Shot type: wide_shot, medium_shot, close_up, establishing_shot, two_shot
        """
        # SPECIAL TREATMENT FOR FIRST IMAGE - Maximum attention-grabbing impact
        if image_number == 1:
            # For first image, prefer shots that create immediate intrigue
            if content_type == 'character_action':
                return 'medium_shot'  # Show action clearly
            elif content_type == 'emotional_moment':
                return 'close_up'     # Show emotion intimately
            elif content_type == 'dialogue_confrontation':
                return 'two_shot'     # Show interaction
            elif content_type == 'environment_description':
                return 'establishing_shot'  # Show mysterious environment
            else:  # exposition_setup
                return 'wide_shot'    # Show grand scale
        
        # Get available shot types for this content type
        available_shots = self.shot_type_mapping.get(content_type, ['medium_shot'])
        
        # Avoid repeating the same shot type too many times
        if len(previous_shot_types) >= 2:
            last_two = previous_shot_types[-2:]
            if len(set(last_two)) == 1:  # Last two were the same
                # Force a different shot type
                for shot in available_shots:
                    if shot not in last_two:
                        return shot
        
        # Consider story progression
        if image_number <= 3:
            # Early images: prefer establishing shots and wide shots
            preferred = ['establishing_shot', 'wide_shot']
        elif image_number >= 9:
            # Late images: prefer close-ups and emotional shots
            preferred = ['close_up', 'medium_shot']
        else:
            # Middle images: balanced approach
            preferred = available_shots
        
        # Return the first available preferred shot type
        for shot in preferred:
            if shot in available_shots:
                return shot
        
        # Fallback to first available shot type
        return available_shots[0]
    
    async def analyze_and_generate_prompt(
        self, 
        audio_content: str, 
        story_context: str,
        image_number: int,
        previous_shot_types: List[str]
    ) -> Dict[str, str]:
        """
        Single GPT-4 call to analyze content type, determine shot type, and generate prompt
        
        Args:
            audio_content: The audio content for this segment
            story_context: The full story context
            image_number: Current image number
            previous_shot_types: List of previous shot types to avoid repetition
            
        Returns:
            Dictionary with content_type, shot_type, and image_prompt
        """
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from llm.story_generator import StoryGenerator
            
            async with StoryGenerator() as generator:
                prompt = f"""
                Analyze this audio segment and create a cinematic image prompt:
                
                AUDIO: "{audio_content}"
                STORY CONTEXT: {story_context}
                IMAGE NUMBER: {image_number} (out of 12)
                PREVIOUS SHOT TYPES: {previous_shot_types}
                
                TASK 1 - Content Analysis:
                Classify the audio content as ONE of these types:
                - character_action: Someone doing something physical, movement, action, behavior
                - environment_description: Describing a place, location, setting, atmosphere  
                - emotional_moment: Feelings, thoughts, reactions, internal states, emotional responses
                - dialogue_confrontation: Conversation, conflict, interaction between people, speaking
                - exposition_setup: Background information, context, setup, historical facts
                
                TASK 2 - Shot Type Selection:
                Based on content type and story progression, choose the best shot type:
                - wide_shot: Expansive view showing environment and context
                - medium_shot: Balanced composition showing characters and action
                - close_up: Intimate focus on faces, emotions, or details
                - establishing_shot: Wide view introducing new locations
                - two_shot: Medium shot showing two characters in interaction
                
                Consider:
                - Early images (1-3): Prefer establishing_shot and wide_shot
                - Middle images (4-8): Mix medium_shot and wide_shot for variety
                - Late images (9-12): Prefer close_up and emotional shots
                - Avoid repeating same shot type 2+ times in a row (faster pacing for 30s)
                - Content type should guide but not restrict shot choice
                
                TASK 3 - Image Prompt Generation:
                Create a natural, flowing image prompt that:
                - Uses the selected shot type naturally
                - Focuses on the content type appropriately
                - Maintains cinematic quality and visual appeal
                - Includes dramatic chiaroscuro lighting, expressive faces, sharp shadows
                - NO text elements (books, signs, papers)
                - Maximum 50 words
                - Tells this specific moment of the story
                
                {f"*** FIRST IMAGE SPECIAL REQUIREMENTS ***" if image_number == 1 else ""}
                {f"- MUST be EXTREMELY attention-grabbing and intriguing" if image_number == 1 else ""}
                {f"- Should create immediate curiosity and hook the viewer" if image_number == 1 else ""}
                {f"- Use dramatic lighting, mysterious atmosphere, or shocking visual elements" if image_number == 1 else ""}
                {f"- Make the viewer want to watch the entire video" if image_number == 1 else ""}
                {f"- Focus on the most compelling, mysterious, or shocking aspect of the story" if image_number == 1 else ""}
                {f"- NO boring establishing shots, empty rooms, or wide views" if image_number == 1 else ""}
                {f"- MUST show ACTION, DRAMA, or INTRIGUE immediately" if image_number == 1 else ""}
                {f"- Examples: Close-up of intense emotion, dramatic confrontation, shocking discovery" if image_number == 1 else ""}
                {f"- Think: What would make someone stop scrolling and watch?" if image_number == 1 else ""}
                
                Return your response in this EXACT JSON format:
                {{
                    "content_type": "character_action",
                    "shot_type": "medium_shot", 
                    "image_prompt": "Medium shot of Cleopatra walking through the palace..."
                }}
                """
                
                response = await generator.client.chat.completions.create(
                    model=generator.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing narrative content and creating cinematic image prompts for historical storytelling videos."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7,
                )
                
                # Parse JSON response
                import json
                result_text = response.choices[0].message.content.strip()
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON in the response
                    start_idx = result_text.find('{')
                    end_idx = result_text.rfind('}') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = result_text[start_idx:end_idx]
                        result = json.loads(json_str)
                        
                        # Validate required fields
                        required_fields = ['content_type', 'shot_type', 'image_prompt']
                        if all(field in result for field in required_fields):
                            return result
                except json.JSONDecodeError:
                    pass
                
                # If JSON parsing fails, fall back to structured parsing
                self.logger.warning("JSON parsing failed, using fallback parsing")
                return self._fallback_parse_response(result_text, audio_content)
                
        except Exception as e:
            self.logger.warning(f"GPT analysis failed, using fallback: {e}")
            return self._fallback_analysis(audio_content, story_context, image_number, previous_shot_types)
    
    def _fallback_parse_response(self, response_text: str, audio_content: str) -> Dict[str, str]:
        """Fallback parsing when JSON parsing fails"""
        # Simple keyword-based fallback
        audio_lower = audio_content.lower()
        
        # Determine content type
        if any(word in audio_lower for word in ['walked', 'ran', 'fought', 'moved', 'entered']):
            content_type = 'character_action'
        elif any(word in audio_lower for word in ['palace', 'room', 'city', 'building']):
            content_type = 'environment_description'
        elif any(word in audio_lower for word in ['felt', 'thought', 'realized', 'feared']):
            content_type = 'emotional_moment'
        elif any(word in audio_lower for word in ['said', 'spoke', 'told', 'asked']):
            content_type = 'dialogue_confrontation'
        else:
            content_type = 'exposition_setup'
        
        # Determine shot type
        shot_type = 'medium_shot'  # Default
        
        # Generate simple prompt
        image_prompt = f"Cinematic {shot_type} of {audio_content}, highly detailed cinematic illustration with dramatic lighting, expressive faces, sharp shadows, atmospheric interiors"
        
        return {
            'content_type': content_type,
            'shot_type': shot_type,
            'image_prompt': image_prompt
        }
    
    def _fallback_analysis(self, audio_content: str, story_context: str, image_number: int, previous_shot_types: List[str]) -> Dict[str, str]:
        """Complete fallback when GPT-4 fails"""
        # Use keyword-based content analysis
        content_type = self._keyword_content_analysis(audio_content)
        
        # Use rule-based shot type determination
        shot_type = self.determine_shot_type(content_type, image_number, previous_shot_types)
        
        # Generate template-based prompt with image number consideration
        image_prompt = self._generate_template_prompt(audio_content, content_type, shot_type, image_number)
        
        return {
            'content_type': content_type,
            'shot_type': shot_type,
            'image_prompt': image_prompt
        }
    
    def _keyword_content_analysis(self, audio_content: str) -> str:
        """Keyword-based content analysis fallback"""
        audio_lower = audio_content.lower()
        scores = {}
        for content_type, keywords in self.content_keywords.items():
            score = sum(1 for keyword in keywords if keyword in audio_lower)
            scores[content_type] = score
        
        if max(scores.values()) == 0:
            return 'exposition_setup'
        
        return max(scores, key=scores.get)
    
    def _generate_template_prompt(self, audio_content: str, content_type: str, shot_type: str, image_number: int) -> str:
        """Generate template-based prompt fallback"""
        shot_descriptions = {
            'wide_shot': 'wide cinematic shot showing expansive view',
            'medium_shot': 'medium shot with balanced composition',
            'close_up': 'intimate close-up shot focusing on details',
            'establishing_shot': 'wide establishing shot showing location and context',
            'two_shot': 'medium shot showing two characters in interaction'
        }
        
        content_enhancements = {
            'character_action': 'dynamic action scene with movement',
            'environment_description': 'detailed environmental scene with atmosphere',
            'emotional_moment': 'emotionally charged scene with expressive faces',
            'dialogue_confrontation': 'tense interaction scene with dramatic lighting',
            'exposition_setup': 'contextual scene establishing story elements'
        }
        
        shot_desc = shot_descriptions.get(shot_type, 'cinematic shot')
        content_enhancement = content_enhancements.get(content_type, 'story scene')
        
        # Special treatment for first image
        first_image_enhancement = ""
        if image_number == 1:
            if content_type in ['exposition_setup', 'environment_description']:
                first_image_enhancement = "mysterious and attention-grabbing, "
            elif content_type in ['character_action', 'emotional_moment']:
                first_image_enhancement = "dramatic and compelling, "
            elif content_type == 'dialogue_confrontation':
                first_image_enhancement = "tense and intriguing, "
            else:
                first_image_enhancement = "shocking and mysterious, "
        
        prompt = f"{shot_desc} of {audio_content}, {first_image_enhancement}{content_enhancement}, "
        prompt += "highly detailed cinematic illustration with dramatic lighting and atmosphere, "
        prompt += "expressive faces, sharp shadows, atmospheric interiors, "
        prompt += "hyper-realistic but stylized characters, painterly texture"
        
        return prompt

    async def generate_enhanced_image_prompt(
        self, 
        audio_content: str, 
        content_type: str, 
        shot_type: str, 
        story_context: str,
        image_number: int
    ) -> str:
        """
        Generate an enhanced image prompt using GPT-4 for natural, story-driven descriptions
        
        Args:
            audio_content: The audio content for this segment
            content_type: The analyzed content type
            shot_type: The determined shot type
            story_context: The full story context
            image_number: Current image number
            
        Returns:
            Enhanced image prompt
        """
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from llm.story_generator import StoryGenerator
            
            async with StoryGenerator() as generator:
                # Content type descriptions for context
                content_descriptions = {
                    'character_action': 'focus on movement, action, and physical behavior',
                    'environment_description': 'emphasize location, setting, and atmospheric details',
                    'emotional_moment': 'highlight facial expressions, emotions, and internal states',
                    'dialogue_confrontation': 'show interaction, tension, and communication',
                    'exposition_setup': 'establish context, background, and story elements'
                }
                
                # Shot type descriptions
                shot_descriptions = {
                    'wide_shot': 'wide cinematic shot showing expansive view and context',
                    'medium_shot': 'medium shot with balanced composition showing characters and action',
                    'close_up': 'intimate close-up shot focusing on faces, emotions, or important details',
                    'establishing_shot': 'wide establishing shot introducing new locations or settings',
                    'two_shot': 'medium shot showing two characters in interaction or confrontation'
                }
                
                content_desc = content_descriptions.get(content_type, 'story scene')
                shot_desc = shot_descriptions.get(shot_type, 'cinematic shot')
                
                prompt_request = f"""
                Create a {shot_type} image prompt for this story moment:
                
                AUDIO: "{audio_content}"
                CONTENT TYPE: {content_type} - {content_desc}
                SHOT TYPE: {shot_type} - {shot_desc}
                STORY CONTEXT: {story_context}
                IMAGE NUMBER: {image_number} (out of 12)
                
                Requirements:
                - Use {shot_type} composition naturally
                - {content_desc}
                - Cinematic quality and visual appeal
                - Dramatic chiaroscuro lighting
                - Expressive faces and sharp shadows
                - Warm candlelit interiors
                - Modern cinematic intensity
                - NO text elements (books, signs, papers)
                - Vivid, cinematic description that tells the story
                - Maximum 50 words
                
                {f"*** FIRST IMAGE - ATTENTION GRABBING REQUIREMENTS ***" if image_number == 1 else ""}
                {f"- This is the FIRST image viewers see - it MUST hook them immediately" if image_number == 1 else ""}
                {f"- Use the most shocking, mysterious, or compelling visual from the story" if image_number == 1 else ""}
                {f"- Create intense curiosity - make viewers want to watch the entire video" if image_number == 1 else ""}
                {f"- Emphasize dramatic lighting, mysterious atmosphere, or shocking elements" if image_number == 1 else ""}
                {f"- Focus on the most attention-grabbing aspect of this story moment" if image_number == 1 else ""}
                {f"- Use words like 'shocking', 'mysterious', 'hidden', 'secret', 'revealed' if appropriate" if image_number == 1 else ""}
                {f"- NO boring establishing shots, empty rooms, or wide views" if image_number == 1 else ""}
                {f"- MUST show ACTION, DRAMA, or INTRIGUE immediately" if image_number == 1 else ""}
                {f"- Examples: Close-up of intense emotion, dramatic confrontation, shocking discovery" if image_number == 1 else ""}
                {f"- Think: What would make someone stop scrolling and watch?" if image_number == 1 else ""}
                
                Write a natural, flowing image prompt that combines the shot type, content focus, and story moment seamlessly.
                """
                
                response = await generator.client.chat.completions.create(
                    model=generator.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at creating cinematic image prompts for historical storytelling videos. You write natural, flowing descriptions that combine technical requirements with narrative storytelling."},
                        {"role": "user", "content": prompt_request}
                    ],
                    max_tokens=150,
                    temperature=0.7,
                )
                
                image_prompt = response.choices[0].message.content.strip()
                
                # Clean up the prompt
                image_prompt = image_prompt.strip('"').strip("'")
                
                return image_prompt
                
        except Exception as e:
            self.logger.warning(f"GPT prompt generation failed, using fallback: {e}")
            # Fallback to template-based prompt
            shot_descriptions = {
                'wide_shot': 'wide cinematic shot showing expansive view',
                'medium_shot': 'medium shot with balanced composition',
                'close_up': 'intimate close-up shot focusing on details',
                'establishing_shot': 'wide establishing shot showing location and context',
                'two_shot': 'medium shot showing two characters in interaction'
            }
            
            content_enhancements = {
                'character_action': 'dynamic action scene with movement',
                'environment_description': 'detailed environmental scene with atmosphere',
                'emotional_moment': 'emotionally charged scene with expressive faces',
                'dialogue_confrontation': 'tense interaction scene with dramatic lighting',
                'exposition_setup': 'contextual scene establishing story elements'
            }
            
            shot_desc = shot_descriptions.get(shot_type, 'cinematic shot')
            content_enhancement = content_enhancements.get(content_type, 'story scene')
            
            # Build the fallback prompt
            prompt = f"{shot_desc} of {audio_content}, {content_enhancement}, "
            prompt += "highly detailed cinematic illustration with dramatic lighting and atmosphere, "
            prompt += "expressive faces, sharp shadows, atmospheric interiors, "
            prompt += "hyper-realistic but stylized characters, painterly texture"
            
            return prompt
    
    async def generate_synchronized_image_prompts(
        self,
        image_schedule: List[Dict[str, Any]],
        original_story: str,
        story_title: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generate story-driven image prompts based on audio-synchronized timing with enhanced diversity
        
        Args:
            image_schedule: Timing schedule from create_image_timing_schedule
            original_story: Original story text
            story_title: Title for saving data
            
        Returns:
            List of image prompts with timing data
        """
        self.logger.info("🎨 Generating story-driven synchronized image prompts with enhanced diversity")
        
        # Track shot types to avoid repetition
        previous_shot_types = []
        synchronized_prompts = []
        
        for segment in image_schedule:
            try:
                # Single GPT-4 call for analysis and prompt generation
                result = await self.analyze_and_generate_prompt(
                    segment['audio_content'],
                    original_story,
                    segment['image_number'],
                    previous_shot_types
                )
                
                content_type = result['content_type']
                shot_type = result['shot_type']
                image_prompt = result['image_prompt']
                
                # Track shot types for diversity
                previous_shot_types.append(shot_type)
                
                synchronized_prompts.append({
                    'image_number': segment['image_number'],
                    'timestamp_start': segment['timestamp_start'],
                    'timestamp_end': segment['timestamp_end'],
                    'audio_content': segment['audio_content'],
                    'image_prompt': image_prompt,
                    'words_in_segment': segment['words_in_segment'],
                    'confidence_avg': segment['confidence_avg'],
                    'content_type': content_type,
                    'shot_type': shot_type
                })
                
                self.logger.info(f"✅ Generated prompt for image {segment['image_number']} ({content_type}/{shot_type}): {image_prompt[:50]}...")
                
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to generate prompt for image {segment['image_number']}: {e}")
                # Fallback prompt - still story-driven but simpler
                fallback_prompt = f"Cinematic scene from the story: {segment['audio_content']}"
                synchronized_prompts.append({
                    'image_number': segment['image_number'],
                    'timestamp_start': segment['timestamp_start'],
                    'timestamp_end': segment['timestamp_end'],
                    'audio_content': segment['audio_content'],
                    'image_prompt': fallback_prompt,
                    'words_in_segment': segment['words_in_segment'],
                    'confidence_avg': segment['confidence_avg'],
                    'content_type': 'exposition_setup',
                    'shot_type': 'medium_shot'
                })
        
        # Save to JSON if story title provided
        if story_title:
            self.save_synchronized_data(story_title, original_story, image_schedule, synchronized_prompts)
        
        self.logger.info(f"✅ Generated {len(synchronized_prompts)} story-driven synchronized image prompts with enhanced diversity")
        return synchronized_prompts
    
    def save_synchronized_data(
        self, 
        story_title: str, 
        original_story: str, 
        image_schedule: List[Dict[str, Any]],
        synchronized_prompts: List[Dict[str, Any]]
    ) -> str:
        """Save synchronized data to JSON file"""
        
        # Use absolute path to ensure consistent output location
        output_dir = Config.OUTPUT_DIR / "audio_sync_data"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        
        output_file = output_dir / f"{safe_title}_whisper_sync.json"
        
        data = {
            'story_title': story_title,
            'original_story': original_story,
            'image_schedule': image_schedule,
            'synchronized_prompts': synchronized_prompts,
            'metadata': {
                'total_images': len(synchronized_prompts),
                'total_duration': image_schedule[-1]['timestamp_end'] if image_schedule else 0,
                'whisper_model': self.model_name
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Saved synchronized data to: {output_file}")
        return str(output_file)
    
    async def process_audio_for_image_sync(
        self, 
        audio_path: str, 
        original_story: str,
        num_images: int = 12,
        story_title: str = None
    ) -> List[Dict[str, Any]]:
        """
        Complete pipeline: transcribe audio and generate synchronized image prompts
        
        Args:
            audio_path: Path to audio file
            original_story: Original story text
            num_images: Number of images to generate
            story_title: Title for saving data
            
        Returns:
            List of synchronized image prompts
        """
        self.logger.info("🚀 Starting Whisper-based audio synchronization pipeline")
        
        # Step 1: Transcribe audio with word timestamps
        transcription_result = self.transcribe_audio_with_timestamps(audio_path)
        
        # Step 2: Extract word timestamps
        word_timestamps = self.extract_word_timestamps(transcription_result)
        
        # Step 3: Create image timing schedule
        image_schedule = self.create_image_timing_schedule(word_timestamps, num_images, original_story)
        
        # Step 4: Generate synchronized image prompts (now async)
        synchronized_prompts = await self.generate_synchronized_image_prompts(
            image_schedule, original_story, story_title
        )
        
        self.logger.info("✅ Whisper-based audio synchronization pipeline completed")
        return synchronized_prompts 