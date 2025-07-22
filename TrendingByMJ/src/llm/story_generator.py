"""
Story generator using OpenAI GPT-4o Mini and prompts.yaml templates.
"""
from dotenv import load_dotenv
import os
import asyncio
from typing import Dict, Any, List
import openai
import yaml
import random
from pathlib import Path
import re
import sys
from pathlib import Path
import hashlib
from datetime import datetime

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

# Load prompts directly from project prompts file
def load_prompts():
    prompts_path = project_root / "prompts" / "prompts.yaml"
    if prompts_path.exists():
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                prompts = yaml.safe_load(f)
                print(f"[DEBUG] Loaded prompts from: {prompts_path}")
                print(f"[DEBUG] Available keys: {list(prompts.keys())}")
                return prompts
        except Exception as e:
            print(f"[ERROR] Failed to load prompts from {prompts_path}: {e}")
            # Fallback prompts if file doesn't exist or fails to load
            return {
                "story_generation": {
                    "system": "You are a YouTube Shorts creator specializing in historical content.",
                    "template": "Create a viral YouTube Short about: {topic}"
                },
                "audio_synchronized_image_prompts": {
                    "system": "Generate cinematic image prompts for historical content.",
                    "template": "Create image prompt for: {scene_description}"
                },
                "music_category_classification": {
                    "system": "Classify story into music category.",
                    "template": "Classify this story: {story}"
                }
            }
    else:
        print(f"[WARNING] Prompts file not found: {prompts_path}")
        # Fallback prompts if file doesn't exist
        return {
            "story_generation": {
                "system": "You are a YouTube Shorts creator specializing in historical content.",
                "template": "Create a viral YouTube Short about: {topic}"
            },
            "audio_synchronized_image_prompts": {
                "system": "Generate cinematic image prompts for historical content.",
                "template": "Create image prompt for: {scene_description}"
            },
            "music_category_classification": {
                "system": "Classify story into music category.",
                "template": "Classify this story: {story}"
            }
        }

PROMPTS = load_prompts()

class StoryGenerator:
    """Story generator using OpenAI GPT-4o Mini and prompts.yaml templates."""
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.story_system = PROMPTS["story_generation"]["system"]
        self.story_template = PROMPTS["story_generation"]["template"]
        # Interactive story generation prompts
        self.interactive_story_system = PROMPTS["interactive_story_generation"]["system"]
        self.interactive_story_template = PROMPTS["interactive_story_generation"]["template"]
        # Use audio_synchronized_image_prompts for image generation since image_prompt_generation doesn't exist
        self.image_system = PROMPTS["audio_synchronized_image_prompts"]["system"]
        self.image_template = PROMPTS["audio_synchronized_image_prompts"]["template"]
        self.audio_sync_system = PROMPTS["audio_synchronized_image_prompts"]["system"]
        self.audio_sync_template = PROMPTS["audio_synchronized_image_prompts"]["template"]
        self.music_system = PROMPTS["music_category_classification"]["system"]
        self.music_template = PROMPTS["music_category_classification"]["template"]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def generate_story(self, topic: str, use_interactive_prompt: bool = False) -> Dict[str, Any]:
        """Generate a viral-format story using the exact prompt from prompts.yaml."""
        # Check topic for content safety first
        if not self._is_content_safe(topic):
            print(f"[WARNING] Topic contains unsafe content: {topic}")
            # Try to regenerate with a safer topic
            safer_topic = await self._generate_safer_topic(topic)
            if safer_topic:
                topic = safer_topic
                print(f"[INFO] Using safer topic: {safer_topic}")
            else:
                print(f"[ERROR] Could not generate safe topic, proceeding with caution")
        
        # Use interactive prompt if requested
        if use_interactive_prompt:
            prompt = self.interactive_story_template.format(topic=topic)
            system_content = self.interactive_story_system
        else:
            prompt = self.story_template.format(topic=topic)
            system_content = self.story_system
            
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.8,
        )
        content = response.choices[0].message.content
        print(f"[DEBUG] Raw GPT response:\n{content}")
        
        import json
        try:
            data = json.loads(content)
        except Exception as e:
            print(f"[DEBUG] JSON parsing failed: {e}")
            # Fallback: try to extract JSON from text
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception as e2:
                    print(f"[DEBUG] JSON extraction also failed: {e2}")
                    data = {"title": f"Story about {topic}", "story": content, "hook": "", "description": "", "tags": [], "keywords": []}
            else:
                data = {"title": f"Story about {topic}", "story": content, "hook": "", "description": "", "tags": [], "keywords": []}
        
        # Debug: Check word count
        story_text = data.get('story', '')
        word_count = len(story_text.split())
        print(f"[DEBUG] Generated story word count: {word_count} words")
        if word_count < 45:
            print(f"[WARNING] Story is too short! Expected 45-60 words, got {word_count}")
        elif word_count > 60:
            print(f"[WARNING] Story is too long! Expected 45-60 words, got {word_count}")
        
        # The hook is now part of the story itself (first sentence)
        # Extract hook for backward compatibility with existing systems
        story_lines = story_text.split('.')
        if story_lines:
            hook = story_lines[0].strip() + '.'
            data['hook'] = hook  # Keep hook field for backward compatibility
        else:
            data['hook'] = story_text  # Fallback if no periods found
        
        # Check generated story for content safety
        if not self._is_content_safe(story_text):
            print(f"[WARNING] Generated story contains unsafe content, attempting to regenerate...")
            # Try to regenerate the story with stronger safety guidelines
            data = await self._regenerate_safe_story(topic)
            if not data:
                print(f"[ERROR] Failed to generate safe story, using original with warnings")
                # Continue with original story but add warning
                data['content_warning'] = "Story may contain advertiser-unfriendly content"
        
        # Classify music category
        music_category = await self.classify_music_category(story_text)
        data['music_category'] = music_category
        print(f"[INFO] Music category classified as: {music_category}")
        
        return data

    def _is_content_safe(self, content: str) -> bool:
        """Check if content is YouTube advertiser-friendly with intelligent context awareness."""
        
        # Define unsafe keywords with context exceptions
        unsafe_patterns = [
            # Explicit violence (no exceptions)
            r'\b(murder(ed|ing)?|assassination|execution|torture|massacre|genocide|slaughter)\b',
            
            # Violence with context exceptions
            r'\b(kill(ed|ing|s)?|death|dead|die|died)\b(?!\s+(bacteria|infection|disease|mold|germ))',
            r'\b(bloody|gore|gory|gruesome|horrific)\b',
            
            # Weapons (no exceptions)
            r'\b(gun|guns|sword|swords|knife|knives|weapon|weapons)\b',
            
            # War and violence (no exceptions)
            r'\b(battle|war|fighting|fought|attack|attacked|bomb|bombed|explosion|exploded)\b',
            
            # Terrorism (no exceptions)
            r'\b(terror|terrorist|terrorism)\b',
            
            # Inappropriate content (no exceptions)
            r'\b(nude|naked|sex|sexual|porn|pornographic|explicit|adult|mature)\b',
            
            # Extreme language (no exceptions)
            r'\b(hate|hateful|racist|racism|discrimination|discriminatory|abuse|abusive)\b'
        ]
        
        content_lower = content.lower()
        
        # Check for unsafe patterns
        for pattern in unsafe_patterns:
            if re.search(pattern, content_lower):
                match = re.search(pattern, content_lower)
                print(f"[CONTENT SAFETY] Unsafe pattern detected: '{match.group()}' in context")
                return False
        
        # Additional context checks for historical content
        historical_safe_contexts = [
            'infection', 'disease', 'bacteria', 'mold', 'germ', 'medicine', 'medical',
            'discovery', 'invention', 'science', 'scientific', 'research', 'experiment',
            'ancient', 'historical', 'archaeology', 'civilization', 'culture',
            'treasure', 'artifact', 'monument', 'building', 'architecture',
            'king', 'queen', 'emperor', 'empire', 'kingdom', 'dynasty',
            'trade', 'commerce', 'economy', 'wealth', 'fortune'
        ]
        
        # If content contains historical safe contexts, be more lenient
        has_historical_context = any(context in content_lower for context in historical_safe_contexts)
        
        # Check for problematic words only if no historical context
        if not has_historical_context:
            problematic_words = ['violent', 'violence', 'brutal', 'brutally', 'horror', 'disturbing', 'shocking', 'terrifying', 'fear', 'fearful', 'scary', 'scared', 'afraid', 'terrified']
            for word in problematic_words:
                if word in content_lower:
                    print(f"[CONTENT SAFETY] Problematic word detected: '{word}' in '{content}'")
                    return False
        
        return True

    async def _generate_safer_topic(self, original_topic: str) -> str:
        """Generate a safer alternative topic that avoids unsafe content."""
        try:
            safer_prompt = f"""
            The topic "{original_topic}" contains content that may not be YouTube advertiser-friendly.
            
            Generate a safer alternative topic that:
            - Focuses on the same historical period or theme
            - Avoids violence, death, murder, torture, executions, war crimes
            - Emphasizes mysteries, discoveries, secrets, inventions, hidden treasures
            - Is fascinating and viral while being advertiser-friendly
            
            Examples of good vs bad topics:
            ❌ Bad: 'How 10,000 People Were Brutally Murdered'
            ✅ Good: 'The Lost City That Vanished Without a Trace'
            ❌ Bad: 'The Gruesome Execution Methods of Medieval Times'
            ✅ Good: 'The Secret Underground City That Housed 20,000 People'
            
            Return only the new topic title.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a YouTube content safety expert who creates advertiser-friendly historical topics."},
                    {"role": "user", "content": safer_prompt}
                ],
                max_tokens=100,
                temperature=0.7,
            )
            
            safer_topic = response.choices[0].message.content.strip()
            if self._is_content_safe(safer_topic):
                return safer_topic
            else:
                print(f"[WARNING] Generated topic still unsafe: {safer_topic}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Failed to generate safer topic: {e}")
            return None

    async def _regenerate_safe_story(self, topic: str) -> Dict[str, Any]:
        """Regenerate a story with stronger content safety guidelines."""
        try:
            safety_prompt = f"""
            Generate a YouTube advertiser-friendly story about: {topic}
            
            CRITICAL CONTENT SAFETY REQUIREMENTS:
            - AVOID: murder, death, violence, war crimes, torture, executions, assassinations, massacres, genocide, gore, blood, weapons, killing, brutal, gruesome, horrific
            - FOCUS ON: mysteries, discoveries, secrets, inventions, hidden treasures, strange customs, fascinating personalities, architectural marvels, lost civilizations
            - PRIORITIZE: educational, fascinating, mysterious, and awe-inspiring aspects of history
            - TONE: Keep content advertiser-friendly while being engaging and viral
            
            The story MUST be 45-60 words for 15-20 second video duration.
            
            Return your response in this EXACT JSON format:
            {{
                "title": "Viral title under 60 characters (NO EMOJIS, avoid starting with 'The')",
                "story": "Full story (45-60 words) starting with a powerful hook and voice tags, flowing naturally into the narrative with cinematic pacing. Every word must serve the story - NO filler content.",
                "description": "Compelling YouTube description (100-150 chars) with specific facts and hashtags - NO generic 'discover' phrases",
                "tags": ["tag1", "tag2", "tag3"],
                "keywords": ["keyword1", "keyword2", "keyword3"]
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a YouTube content safety expert who creates advertiser-friendly historical stories."},
                    {"role": "user", "content": safety_prompt}
                ],
                max_tokens=2000,
                temperature=0.8,
            )
            
            content = response.choices[0].message.content
            import json
            try:
                data = json.loads(content)
                # Verify the regenerated story is safe
                story_text = data.get('story', '')
                if self._is_content_safe(story_text):
                    print(f"[SUCCESS] Generated safe story about: {topic}")
                    return data
                else:
                    print(f"[WARNING] Regenerated story still contains unsafe content")
                    return None
            except Exception as e:
                print(f"[ERROR] Failed to parse regenerated story JSON: {e}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Failed to regenerate safe story: {e}")
            return None

    async def classify_music_category(self, story_text: str) -> str:
        """Classify the story into a music category for background music selection."""
        prompt = self.music_template.format(story=story_text)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.music_system},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.3,
            )
            category = response.choices[0].message.content.strip()
            # Validate category
            valid_categories = ["Intense", "Somber", "Uplifting", "Mystery"]
            if category in valid_categories:
                return category
            else:
                print(f"[WARNING] Invalid music category '{category}', defaulting to 'Intense'")
                return "Intense"
        except Exception as e:
            print(f"[ERROR] Failed to classify music category: {e}")
            return "Intense"  # Default fallback

    async def generate_image_moments_and_prompts(self, story_text: str, num_images: int = 12) -> List[str]:
        """
        Break the story into visually distinct moments and generate a high-quality, concise prompt for each.
        Prompts are vivid, descriptive, and not too long for the Schnell model.
        Returns a list of  prompts (one per image).
        """
        # Step 1: Ask OpenAI to break the story into moments
        split_prompt = (
            f"You are an expert at visual storytelling for AI image generation. "
            f"Given the following story, break it into EXACTLY {num_images} visually distinct, cinematic moments that would best illustrate the story as a sequence of images for a 15-20 second YouTube Short. "
            f"Each moment should be concise (1-2 sentences), vivid, and focused on a key visual or action. "
            f"Avoid vagueness, and ensure each moment flows with the story. "
            f"CRITICAL: You MUST return EXACTLY {num_images} numbered moments (1. through {num_images}.). "
            f"Return ONLY a numbered list of {num_images} moments, no extra text.\n\nStory:\n{story_text}"
        )
        split_response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.story_system},
                {"role": "user", "content": split_prompt}
            ],
            max_tokens=600,
            temperature=0.6,
        )
        split_content = split_response.choices[0].message.content.strip()
        # Parse the numbered list into a list of moments
        import re
        moments = re.findall(r'\d+\.\s*(.+)', split_content)
        if not moments or len(moments) < num_images:
            # fallback: split by lines
            moments = [line.strip('- ').strip() for line in split_content.split('\n') if line.strip()]
        
        # Ensure we have exactly num_images moments
        if len(moments) < num_images:
            # If we have fewer moments, repeat the last few to reach num_images
            while len(moments) < num_images:
                moments.append(moments[-1] if moments else "Story continuation")
        elif len(moments) > num_images:
            # If we have more moments, truncate to num_images
            moments = moments[:num_images]

        # Step 2: For each moment, generate a concise, vivid image prompt
        prompts = []
        for moment in moments:
            # Use the existing image prompt template, but add a length constraint
            prompt = (
                self.image_template.format(scene_description=moment)
                + "\nKeep the prompt under 50 words. Be vivid, cinematic, and specific, but concise."
            )
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.image_system},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            prompts.append(response.choices[0].message.content.strip())
        return prompts

    async def generate_audio_synchronized_image_prompts(
        self, 
        story_text: str, 
        audio_duration: float, 
        num_images: int = 12,
        audio_transcript: str = None,
        story_title: str = None,
        save_to_json: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate image prompts that are perfectly synchronized with audio content.
        
        Args:
            story_text: The story content
            audio_duration: Duration of the audio in seconds
            num_images: Number of images to generate (default 12)
            audio_transcript: Optional transcript of the audio for better synchronization
            story_title: Title of the story for saving JSON file
            save_to_json: Whether to save the data to JSON file
            
        Returns:
            List of dictionaries with image prompts and timing information
        """
        image_duration = audio_duration / num_images
        
        prompt = self.audio_sync_template.format(
            story_text=story_text,
            audio_duration=audio_duration,
            num_images=num_images,
            image_duration=image_duration,
            image_duration_2=image_duration * 2,
            audio_transcript=audio_transcript or "Not available"
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.audio_sync_system},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            import json
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    synchronized_prompts = data
                else:
                    raise ValueError("Expected JSON array")
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from text
                import re
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    synchronized_prompts = json.loads(match.group(0))
                else:
                    # Fallback to simple prompt generation
                    print("[WARNING] Failed to parse audio-synchronized prompts, falling back to simple generation")
                    simple_prompts = await self.generate_image_moments_and_prompts(story_text, num_images)
                    synchronized_prompts = [
                        {
                            "image_number": i + 1,
                            "timestamp_start": i * image_duration,
                            "timestamp_end": (i + 1) * image_duration,
                            "audio_content": f"Story segment {i + 1}",
                            "image_prompt": prompt
                        }
                        for i, prompt in enumerate(simple_prompts)
                    ]
            
            # Save to JSON if requested
            if save_to_json and story_title:
                self.save_audio_sync_data_to_json(
                    story_title=story_title,
                    story_text=story_text,
                    audio_duration=audio_duration,
                    synchronized_prompts=synchronized_prompts
                )
            
            return synchronized_prompts
                    
        except Exception as e:
            print(f"[ERROR] Failed to generate audio-synchronized prompts: {e}")
            # Fallback to simple prompt generation
            simple_prompts = await self.generate_image_moments_and_prompts(story_text, num_images)
            synchronized_prompts = [
                {
                    "image_number": i + 1,
                    "timestamp_start": i * image_duration,
                    "timestamp_end": (i + 1) * image_duration,
                    "audio_content": f"Story segment {i + 1}",
                    "image_prompt": prompt
                }
                for i, prompt in enumerate(simple_prompts)
            ]
            
            # Save to JSON if requested
            if save_to_json and story_title:
                self.save_audio_sync_data_to_json(
                    story_title=story_title,
                    story_text=story_text,
                    audio_duration=audio_duration,
                    synchronized_prompts=synchronized_prompts
                )
            
            return synchronized_prompts

    def save_audio_sync_data_to_json(
        self, 
        story_title: str, 
        story_text: str, 
        audio_duration: float, 
        synchronized_prompts: List[Dict[str, Any]]
    ) -> str:
        """
        Save audio-synchronized data to JSON file in the audio folder.
        
        Args:
            story_title: Title of the story
            story_text: Full story text
            audio_duration: Duration of audio in seconds
            synchronized_prompts: List of synchronized prompt data
            
        Returns:
            Path to the saved JSON file
        """
        try:
            import json
            from datetime import datetime
            
            # Create audio sync data structure
            audio_sync_data = {
                "story_title": story_title,
                "story_text": story_text,
                "audio_duration": audio_duration,
                "audio_filename": f"audio_{self.sanitize_folder_name(story_title)[:32]}.mp3",
                "num_segments": len(synchronized_prompts),
                "segment_duration": audio_duration / len(synchronized_prompts),
                "generated_at": datetime.now().isoformat(),
                "synchronized_segments": synchronized_prompts
            }
            
            # Create output directory
            sanitized_title = self.sanitize_folder_name(story_title)
            output_dir = Config.OUTPUT_DIR / "audio" / sanitized_title
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save JSON file
            json_file = output_dir / "audio_sync_data.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(audio_sync_data, f, indent=2, ensure_ascii=False)
            
            print(f"[INFO] Audio sync data saved: {json_file}")
            return str(json_file)
            
        except Exception as e:
            print(f"[ERROR] Failed to save audio sync data: {e}")
            raise

    def get_context_aware_shot_type(self, moment: str, position_in_story: float) -> str:
        moment_lower = moment.lower()
        # Enhanced emotional keywords
        emotional_keywords = [
            "crying", "tears", "fear", "shock", "surprise", "emotional", "desperate",
            "angry", "rage", "joy", "celebration", "grief", "worried", "terrified",
            "amazed", "horrified", "relieved", "heartbroken"
        ]
        # Emotional moments need close-ups
        if any(word in moment_lower for word in emotional_keywords):
            return "dramatic close-up"
        # Action/chaos needs wide shots, with people focus if mentioned
        action_keywords = ["fight", "chaos", "crowd", "flood", "explosion", "running", "panic", "battle"]
        people_keywords = ["people", "person", "man", "woman", "soldier", "crowd"]
        if any(word in moment_lower for word in action_keywords):
            if any(word in moment_lower for word in people_keywords):
                return "wide action shot featuring people"
            else:
                return "wide action shot"
        # Conversations need medium shots
        if any(word in moment_lower for word in ["talking", "conversation", "meeting", "discussing", "whispering"]):
            return "medium shot"
        # Story opening needs establishing shots
        if position_in_story < 0.2:
            return "wide establishing shot"
        # Story climax needs epic shots
        if 0.6 <= position_in_story <= 0.8:
            return "epic reveal shot"
        # Default to medium shot
        return "medium shot"

    async def generate_story_driven_visual_sequence(self, story_text: str, num_images: int = None) -> list:
        """
        Generate a visually engaging sequence that follows the story naturally while maximizing retention.
        Uses proven techniques: visual variety, story flow, and natural emotional progression.
        Always uses 20 images.
        """
        import json
        import re
        # 1. Always use 6 images for 15-20 second videos
        num_images = 6
        # 2. Step 1: Analyze story for natural visual opportunities
        analysis_system = PROMPTS["visual_sequence_analysis"]["system"]
        analysis_template = PROMPTS["visual_sequence_analysis"]["template"].format(story_text=story_text)
        analysis_response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": analysis_system},
                {"role": "user", "content": analysis_template}
            ],
            max_tokens=400,
            temperature=0.4,
        )
        try:
            story_analysis = json.loads(analysis_response.choices[0].message.content)
        except Exception:
            story_analysis = {
                "story_arc": "natural story progression",
                "key_scenes": "dramatic moments",
                "character_moments": "emotional reactions",
                "setting_changes": "location shifts",
                "surprise_elements": "unexpected events",
                "visual_contrasts": "dramatic differences"
            }
        # 3. Step 2: Break story into visual moments
        breakdown_system = PROMPTS["visual_sequence_breakdown"]["system"]
        breakdown_template = PROMPTS["visual_sequence_breakdown"]["template"].format(
            num_images=num_images,
            story_text=story_text,
            story_arc=story_analysis.get("story_arc", ""),
            key_scenes=story_analysis.get("key_scenes", ""),
            surprise_elements=story_analysis.get("surprise_elements", ""),
            visual_contrasts=story_analysis.get("visual_contrasts", "")
        )
        breakdown_response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": breakdown_system},
                {"role": "user", "content": breakdown_template}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        sequence_content = breakdown_response.choices[0].message.content.strip()
        moments = re.findall(r'\d+\.\s*(.+)', sequence_content)
        if not moments or len(moments) < num_images:
            moments = [line.strip('- ').strip() for line in sequence_content.split('\n') if line.strip()]
        moments = moments[:num_images]
        # 4. Step 3: Generate prompts with proven retention techniques
        prompts = []
        image_system = PROMPTS["visual_sequence_image_prompt"]["system"]
        image_template = PROMPTS["visual_sequence_image_prompt"]["template"]
        for i, moment in enumerate(moments):
            position_in_story = i / num_images
            shot_type = self.get_context_aware_shot_type(moment, position_in_story)
            prompt_text = image_template.format(
                moment=moment,
                shot_type=shot_type
            )
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": image_system},
                    {"role": "user", "content": prompt_text}
                ],
                max_tokens=200,
                temperature=0.6,
            )
            base_prompt = response.choices[0].message.content.strip()
            quality_elements = "Cinematic lighting, sharp focus, professional composition"
            final_prompt = f"{base_prompt}. {quality_elements}."
            prompts.append(final_prompt)
        return prompts

    async def suggest_topic(self, exclude_topics=None) -> str:
        """Suggest a unique topic that hasn't been used before."""
        
        import time
        import random
        import os
        from pathlib import Path
        
        # Load banned topics from used_topics.txt
        banned_topics = self._load_banned_topics()
        
        # Add any additional excluded topics
        all_excluded = set(banned_topics)
        if exclude_topics:
            if isinstance(exclude_topics, str):
                all_excluded.add(exclude_topics)
            else:
                all_excluded.update(exclude_topics)
        
        print(f"[DEBUG] Loaded {len(banned_topics)} banned topics from used_topics.txt")
        print(f"[DEBUG] Total excluded topics: {len(all_excluded)}")
        
        # Try to generate a unique topic
        max_attempts = 5  # Reduced from 10 to 5 for faster generation
        failed_attempts = []
        
        random.seed(time.time_ns())  # Ensure true randomization per call
        # Updated weights to prioritize safer, more advertiser-friendly topics
        prompt_options = [
            ("topic_suggestion_creative", 0.30),  # Increased weight for creative topics
            ("topic_suggestion_unbelievable", 0.20),  # Increased weight for unbelievable facts
            ("topic_suggestion_celebrity_secrets", 0.20),  # Increased weight for celebrity secrets
            ("topic_suggestion_epic_moments", 0.15),  # Moderate weight for epic moments
            ("topic_suggestion_close_calls", 0.10),  # Reduced weight for close calls
            ("topic_suggestion_shocking", 0.03),  # Reduced weight for shocking topics
            ("topic_suggestion_disturbing", 0.02)  # Minimal weight for disturbing topics
        ]
        keys, weights = zip(*prompt_options)
        
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            
            # After 3 attempts, start using adaptive prompting
            if attempt > 3:
                chosen_key = self._get_adaptive_prompt_key(attempt, failed_attempts)
                print(f"[DEBUG] Using adaptive prompt: {chosen_key} (attempt {attempt})")
            else:
                chosen_key = random.choices(keys, weights=weights, k=1)[0]
                print(f"[DEBUG] Using topic prompt: {chosen_key} (attempt {attempt})")
            
            system = PROMPTS[chosen_key]["system"]
            
            # Build exclusion string for prompt
            if all_excluded:
                exclude_text = (
                    "🚫 FORBIDDEN TOPICS - DO NOT SUGGEST ANY OF THESE:\n"
                    + "\n".join([f"• {topic}" for topic in all_excluded])
                    + f"\n\n⚠️ CRITICAL: You MUST choose a completely different topic. If you suggest any of the above topics, your response will be rejected and you will be asked to try again. Choose something entirely new and unique."
                )
            else:
                exclude_text = ""
            
            # After 3 attempts, add context about failed attempts
            if attempt > 3 and failed_attempts:
                failed_context = (
                    f"\n\n🚫 RECENTLY REJECTED CONCEPTS (avoid similar themes):\n"
                    + "\n".join([f"• {topic[:60]}..." for topic in failed_attempts[-3:]])
                    + f"\n\n💡 INSTRUCTIONS: Choose a topic that is COMPLETELY DIFFERENT from the rejected concepts above. Focus on different historical periods, different types of events, or different themes entirely."
                )
                exclude_text += failed_context
            
            # Check if the chosen_key exists in PROMPTS
            if chosen_key not in PROMPTS:
                print(f"[ERROR] Prompt key '{chosen_key}' not found in PROMPTS. Available keys: {list(PROMPTS.keys())}")
                failed_attempts.append(f"Missing prompt: {chosen_key}")
                continue
            
            # Check if template exists for this key
            if "template" not in PROMPTS[chosen_key]:
                print(f"[ERROR] Template not found for prompt key '{chosen_key}'. Available fields: {list(PROMPTS[chosen_key].keys())}")
                failed_attempts.append(f"Missing template: {chosen_key}")
                continue
            
            template = PROMPTS[chosen_key]["template"].format(exclude_topics=exclude_text)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": template}
                ],
                max_tokens=120,
                temperature=1.0,  # Increase for more variety
            )
            
            suggested_topic = response.choices[0].message.content.strip()
            
            # Check if the suggested topic contains any banned topics
            if not self._contains_banned_topic(suggested_topic, all_excluded):
                # Additional content safety check
                if self._is_content_safe(suggested_topic):
                    print(f"[DEBUG] Topic accepted (safe): {suggested_topic[:50]}...")
                    return suggested_topic
                else:
                    print(f"[DEBUG] Topic rejected (unsafe content): {suggested_topic[:50]}...")
                    failed_attempts.append(suggested_topic)
                    continue
            else:
                print(f"[DEBUG] Topic rejected (contains banned content): {suggested_topic[:50]}...")
                failed_attempts.append(suggested_topic)
                print(f"[DEBUG] Retrying with stronger exclusion...")
        
        # If we hit the safety limit, raise an error instead of using fallback
        print(f"[ERROR] Failed to generate unique topic after {max_attempts} attempts")
        
        # CRITICAL FALLBACK: Use proven high-view eras and ask GPT to generate story
        print(f"[WARNING] Using era-based fallback system to prevent pipeline failure...")
        
        # Proven high-view eras/periods (these get consistent good views)
        high_view_eras = [
            "World War II",
            "Roman Empire", 
            "Ancient Egypt",
            "Medieval Europe",
            "Ancient Greece",
            "Viking Age",
            "Renaissance Italy",
            "Ancient China",
            "Napoleonic Wars",
            "American Civil War"
        ]
        
        # BANNED TOPICS - No boring civil rights/human rights stories
        banned_topics = [
            "civil rights", "human rights", "racial equality", "social justice", "activism",
            "NAACP", "W.E.B. Du Bois", "segregation", "discrimination", "equality",
            "socialism", "communism", "political activism", "protest", "demonstration"
        ]
        
        # Try each era until one works
        for era in high_view_eras:
            if not self._contains_banned_topic(era, all_excluded):
                print(f"[SUCCESS] Using fallback era: {era}")
                
                # Generate a story topic about this specific era
                era_topic = await self._generate_era_based_topic(era)
                if era_topic:
                    print(f"[SUCCESS] Generated era-based topic: {era_topic}")
                    return era_topic
        
        # If even eras fail, return a guaranteed unique topic
        import time
        timestamp = int(time.time())
        guaranteed_topic = f"The Secret Historical Discovery of {timestamp}"
        print(f"[SUCCESS] Using guaranteed unique topic: {guaranteed_topic}")
        return guaranteed_topic
    
    def _get_adaptive_prompt_key(self, attempt: int, failed_attempts: list) -> str:
        """Get an adaptive prompt key based on failed attempts to avoid repeating concepts."""
        
        # Analyze failed attempts to understand what's being rejected
        failed_text = " ".join(failed_attempts).lower()
        
        # Define concept categories and their associated prompts
        concept_prompts = {
            "medical": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "disease": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "plague": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "war": ["topic_suggestion_celebrity_secrets", "topic_suggestion_creative"],
            "battle": ["topic_suggestion_celebrity_secrets", "topic_suggestion_creative"],
            "assassination": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "death": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "disaster": ["topic_suggestion_celebrity_secrets", "topic_suggestion_creative"],
            "accident": ["topic_suggestion_celebrity_secrets", "topic_suggestion_creative"],
            "experiment": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "secret": ["topic_suggestion_epic_moments", "topic_suggestion_creative"],
            "mystery": ["topic_suggestion_epic_moments", "topic_suggestion_creative"],
            "dancing": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "balloon": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "zoo": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "apollo": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "space": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "stink": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "sewage": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "womb": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "leviathan": ["topic_suggestion_creative", "topic_suggestion_epic_moments"],
            "monster": ["topic_suggestion_creative", "topic_suggestion_epic_moments"]
        }
        
        # Find which concepts are being rejected
        rejected_concepts = []
        for concept, keywords in concept_prompts.items():
            if any(keyword in failed_text for keyword in [concept] + keywords):
                rejected_concepts.append(concept)
        
        # If we have rejected concepts, choose a prompt that avoids them
        if rejected_concepts:
            # Get all available prompts
            all_prompts = ["topic_suggestion_shocking", "topic_suggestion_disturbing", 
                          "topic_suggestion_unbelievable", "topic_suggestion_celebrity_secrets",
                          "topic_suggestion_epic_moments", "topic_suggestion_close_calls", 
                          "topic_suggestion_creative"]
            
            # Filter out prompts associated with rejected concepts
            available_prompts = []
            for prompt in all_prompts:
                is_rejected = False
                for concept in rejected_concepts:
                    if prompt in concept_prompts.get(concept, []):
                        is_rejected = True
                        break
                if not is_rejected:
                    available_prompts.append(prompt)
            
            # If we have available prompts, choose one
            if available_prompts:
                return available_prompts[0]  # Use the first available
        
        # Fallback to creative prompt if no specific avoidance needed
        return "topic_suggestion_creative"
    
    async def _generate_era_based_topic(self, era: str) -> str:
        """Generate a viral topic about a specific historical era using GPT."""
        try:
            system_prompt = f"""You are a viral content creator specializing in historical mysteries and secrets. 
Generate ONE compelling topic about {era} that would go viral on YouTube Shorts.

Requirements:
- Must be about {era} specifically
- Must be shocking, mysterious, or reveal a hidden truth
        - Must be suitable for a 15-20 second video
- Must be historically accurate but sensational
- Must grab attention immediately
- NO civil rights, human rights, or political activism topics
- Focus on: secrets, conspiracies, mysteries, scandals, hidden treasures, lost technology, ancient secrets, military secrets, royal scandals, scientific discoveries, archaeological mysteries

Format: Just the title, no extra text."""

            user_prompt = f"""Generate a viral YouTube Shorts topic about {era}. 
Focus on secrets, mysteries, hidden truths, or shocking revelations from this period.
        Make it compelling and attention-grabbing for a 15-20 second video.

AVOID: civil rights, human rights, political activism, social justice, equality topics
FOCUS ON: secrets, conspiracies, mysteries, scandals, hidden treasures, lost technology, ancient secrets, military secrets, royal scandals, scientific discoveries, archaeological mysteries

Example style: "The Secret [Something] of {era}" or "The Hidden Truth About [Something] in {era}"

Return ONLY the title, nothing else."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=60,
                temperature=0.9,  # Creative but focused
            )
            
            topic = response.choices[0].message.content.strip()
            
            # Clean up the topic (remove quotes, extra formatting)
            topic = topic.strip('"').strip("'").strip()
            
            # Ensure it's about the era
            if era.lower() not in topic.lower():
                topic = f"The Secret Truth About {era}"
            
            return topic
            
        except Exception as e:
            print(f"[WARNING] Failed to generate era-based topic for {era}: {e}")
            return f"The Hidden Secrets of {era}"
    
    def save_used_topic(self, topic: str) -> bool:
        """Save a used topic to used_topics.txt to prevent future duplicates."""
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            used_topics_file = project_root / "used_topics.txt"
            
            # Create the file if it doesn't exist
            used_topics_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate a hash of the topic for efficient storage
            import hashlib
            topic_hash = hashlib.md5(topic.lower().encode('utf-8')).hexdigest()[:8]
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Read existing topics to check for duplicates and manage file size
            existing_topics = set()
            if used_topics_file.exists():
                with open(used_topics_file, 'r', encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 2:
                                existing_topics.add(parts[0])  # Add hash to set
            
            # Check if topic already exists
            if topic_hash in existing_topics:
                print(f"[INFO] Topic already exists in used_topics.txt: {topic[:50]}...")
                return True
            
            # Append the topic hash and date to the file
            with open(used_topics_file, 'a', encoding="utf-8") as f:
                f.write(f"{topic_hash}|{current_date}|{topic[:100]}\n")
            
            # Cleanup old entries if file gets too large (keep last 1000 entries)
            self._cleanup_used_topics_file(used_topics_file, max_entries=1000)
     
            print(f"[INFO] Topic saved to used_topics.txt: {topic[:50]}... (hash: {topic_hash})")
            return True
            
        except Exception as e:
            print(f"[WARNING] Failed to save topic to used_topics.txt: {e}")
            return False
    
    def _cleanup_used_topics_file(self, used_topics_file: Path, max_entries: int = 1000):
        """Clean up the used_topics.txt file to prevent it from growing too large."""
        try:
            if not used_topics_file.exists():
                return
            
            # Read all lines
            with open(used_topics_file, 'r', encoding="utf-8") as f:
                lines = f.readlines()
            
            # If file is small enough, no cleanup needed
            if len(lines) <= max_entries:
                return
            
            # Keep only the most recent entries
            lines_to_keep = lines[-max_entries:]
            
            # Write back the cleaned file
            with open(used_topics_file, 'w', encoding="utf-8") as f:
                f.writelines(lines_to_keep)
            
            print(f"[INFO] Cleaned up used_topics.txt: kept {len(lines_to_keep)} entries, removed {len(lines) - len(lines_to_keep)} old entries")
            
        except Exception as e:
            print(f"[WARNING] Failed to cleanup used_topics.txt: {e}")
    
    def _load_banned_topics(self) -> list:
        """Load banned topics from used_topics.txt"""
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            used_topics_file = project_root / "used_topics.txt"
            
            if not used_topics_file.exists():
                return []
            
            with open(used_topics_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extract topic titles from the new format (hash|date|topic)
            banned_topics = []
            for line in lines:
                line = line.strip()
                if line and '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        # Use the full topic name (part 2)
                        topic = parts[2].strip()
                        banned_topics.append(topic)
                elif line:
                    # Handle old format (just topic name)
                    topic = line.strip()
                    banned_topics.append(topic)
            
            return banned_topics
            
        except Exception as e:
            print(f"[WARNING] Error loading banned topics: {e}")
            return []
    
    def _contains_banned_topic(self, suggested_topic: str, banned_topics: set) -> bool:
        """Check if the suggested topic contains any banned topics - MUCH LESS AGGRESSIVE"""
        if not banned_topics:
            return False
        
        suggested_lower = suggested_topic.lower()
        
        for banned_topic in banned_topics:
            banned_lower = banned_topic.lower()
            
            # ONLY check for EXACT title matches or very close matches
            # Remove common words and punctuation for comparison
            import re
            
            # Clean both topics
            suggested_clean = re.sub(r'[^\w\s]', '', suggested_lower)
            banned_clean = re.sub(r'[^\w\s]', '', banned_lower)
            
            # Split into words
            suggested_words = set(suggested_clean.split())
            banned_words = set(banned_clean.split())
            
            # Remove common words that don't matter
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now', 'title', 'summary', 'story', 'history', 'historical', 'secret', 'hidden', 'real', 'true', 'story', 'behind', 'what', 'if', 'when', 'where', 'how', 'why', 'who', 'which', 'that', 'this', 'these', 'those'}
            
            suggested_words = suggested_words - common_words
            banned_words = banned_words - common_words
            
            # Only consider it a match if there's a very high overlap (80%+ of unique words)
            if len(banned_words) > 0 and len(suggested_words) > 0:
                overlap = len(banned_words.intersection(suggested_words))
                total_unique = len(banned_words.union(suggested_words))
                
                # Only reject if there's very high similarity (80%+ overlap)
                if overlap / total_unique > 0.8:
                    print(f"[DEBUG] High overlap detected: {overlap}/{total_unique} = {overlap/total_unique:.2f}")
                    return True
            
            # Also check for exact title matches (case insensitive)
            if suggested_clean.strip() == banned_clean.strip():
                return True
        
        return False
    


    def save_story_assets(self, topic: str, story_data: dict, image_prompts: list):
        """Save topic, story, and image prompts to output/stories/<story_folder>/"""
        from src.utils.folder_utils import sanitize_folder_name
        folder_name = sanitize_folder_name(story_data.get('title', topic))
        base_dir = Path('output') / 'stories' / folder_name
        base_dir.mkdir(parents=True, exist_ok=True)
        # Save topic
        with open(base_dir / 'topic.txt', 'w', encoding='utf-8') as f:
            f.write(topic.strip() + '\n')
        # Save story (as JSON for structure)
        import json
        with open(base_dir / 'story.json', 'w', encoding='utf-8') as f:
            json.dump(story_data, f, indent=2, ensure_ascii=False)
        # Save image prompts
        with open(base_dir / 'image_prompts.txt', 'w', encoding='utf-8') as f:
            for prompt in image_prompts:
                f.write(prompt.strip() + '\n')
