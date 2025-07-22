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
        with open(prompts_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
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

    async def generate_story(self, topic: str) -> Dict[str, Any]:
        """Generate a viral-format story using the exact prompt from prompts.yaml."""
        prompt = self.story_template.format(topic=topic)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.story_system},
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
        if word_count < 160:
            print(f"[WARNING] Story is too short! Expected 160-170 words, got {word_count}")
        elif word_count > 170:
            print(f"[WARNING] Story is too long! Expected 160-170 words, got {word_count}")
        
        # The hook is now part of the story itself (first sentence)
        # Extract hook for backward compatibility with existing systems
        story_lines = story_text.split('.')
        if story_lines:
            hook = story_lines[0].strip() + '.'
            data['hook'] = hook  # Keep hook field for backward compatibility
        else:
            data['hook'] = story_text  # Fallback if no periods found
        
        # Classify music category
        music_category = await self.classify_music_category(story_text)
        data['music_category'] = music_category
        print(f"[INFO] Music category classified as: {music_category}")
        
        return data

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

    async def generate_image_moments_and_prompts(self, story_text: str, num_images: int = 20) -> List[str]:
        """
        Break the story into visually distinct moments and generate a high-quality, concise prompt for each.
        Prompts are vivid, descriptive, and not too long for the Schnell model.
        Returns a list of  prompts (one per image).
        """
        # Step 1: Ask OpenAI to break the story into moments
        split_prompt = (
            f"You are an expert at visual storytelling for AI image generation. "
            f"Given the following story, break it into EXACTLY {num_images} visually distinct, cinematic moments that would best illustrate the story as a sequence of images for a 60-second YouTube Short. "
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
        num_images: int = 20,
        audio_transcript: str = None,
        story_title: str = None,
        save_to_json: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate image prompts that are perfectly synchronized with audio content.
        
        Args:
            story_text: The story content
            audio_duration: Duration of the audio in seconds
            num_images: Number of images to generate (default 20)
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
        # 1. Always use 20 images
        num_images = 20
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
        """
        Suggest a viral historical topic for a YouTube Short using one of seven prompt types.
        Weighted randomization: creative (20, shocking/disturbing/unbelievable/celebrity_secrets (15ach), epic_moments/close_calls (10).
        Returns: topic title and one-sentence description.
        Optionally excludes a list of topics.
        """
        import time
        import random
        import os
        from pathlib import Path
        
        # Load banned topics from used_topics.txt
        banned_topics = self._load_banned_topics()
        
        # Combine exclude_topics with banned_topics
        all_excluded = set()
        if exclude_topics:
            all_excluded.update(exclude_topics)
        if banned_topics:
            all_excluded.update(banned_topics)
        
        random.seed(time.time_ns())  # Ensure true randomization per call
        prompt_options = [
            ("topic_suggestion_shocking", 0.15),
            ("topic_suggestion_disturbing", 0.15),
            ("topic_suggestion_unbelievable", 0.15),
            ("topic_suggestion_celebrity_secrets", 0.15),
            ("topic_suggestion_epic_moments", 0.10),
            ("topic_suggestion_close_calls", 0.10),
            ("topic_suggestion_creative", 0.20)
        ]
        keys, weights = zip(*prompt_options)
        
        # Keep trying until we get a valid topic (no 3-attempt limit)
        attempt = 0
        max_attempts = 10  # Safety limit to prevent infinite loops
        
        while attempt < max_attempts:
            attempt += 1
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
                print(f"[DEBUG] Topic accepted: {suggested_topic[:50]}...")
                return suggested_topic
            else:
                print(f"[DEBUG] Topic rejected (contains banned content): {suggested_topic[:50]}...")
                print(f"[DEBUG] Retrying with stronger exclusion...")
        
        # If we hit the safety limit, raise an error instead of using fallback
        print(f"[ERROR] Failed to generate unique topic after {max_attempts} attempts")
        raise Exception(f"Could not generate unique topic after {max_attempts} attempts. Consider clearing used_topics.txt or providing different exclusion criteria.")
    
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
        """Check if the suggested topic contains any banned topics"""
        if not banned_topics:
            return False
        
        suggested_lower = suggested_topic.lower()
        
        for banned_topic in banned_topics:
            banned_lower = banned_topic.lower()
            
            # Check for exact matches or significant overlaps
            if banned_lower in suggested_lower or suggested_lower in banned_lower:
                return True
            
            # Check for key words that indicate the same topic
            banned_words = set(banned_lower.split())
            suggested_words = set(suggested_lower.split())
            
            # If more than 50% of banned words are in suggested topic, consider it a match
            if len(banned_words) > 0:
                overlap = len(banned_words.intersection(suggested_words))
                if overlap / len(banned_words) > 0.5:
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
