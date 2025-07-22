"""
Trending Summary Generator for TrendingByMJ
Generates engaging summaries for trending topics optimized for short-form content
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import openai
from datetime import datetime

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config

class TrendingSummaryGenerator:
    """Generates engaging summaries for trending topics."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Load prompts
        self.prompts = self._load_prompts()
        
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts for summary generation."""
        prompts_path = project_root / "prompts" / "trending_prompts.yaml"
        
        if prompts_path.exists():
            try:
                import yaml
                with open(prompts_path, 'r', encoding='utf-8') as f:
                    prompts = yaml.safe_load(f)
                self.logger.info("📝 Loaded trending prompts from file")
                return prompts
            except Exception as e:
                self.logger.error(f"❌ Error loading prompts: {e}")
        
        # Default prompts if file doesn't exist
        return {
            "summary_generation": """You are a viral content creator for YouTube Shorts. Your job is to create engaging, informative summaries of trending topics that will captivate viewers in 20-30 seconds.

TASK: Create a compelling summary of the trending topic that:
- Is exactly 15-20 seconds when read aloud (approximately 45-60 words)
- Starts with a hook that grabs attention
- Provides key facts and context
- Ends with an interesting conclusion or question
- Uses simple, engaging language
- Avoids jargon and complex sentences
- Is suitable for a general audience
- Maintains factual accuracy

TRENDING TOPIC: {topic}
SEARCH VOLUME: {search_volume}
CONTEXT: {context}

FORMAT: Write only the summary text, no additional formatting or explanations.""",
            
            "title_generation": """Generate a compelling, clickable title for a YouTube Short about this trending topic.

TASK: Create a title that:
- Is under 60 characters
- Uses power words and emotional triggers
- Creates curiosity and urgency
- Is accurate to the content
- Avoids clickbait or misleading claims

TRENDING TOPIC: {topic}
SUMMARY: {summary}

FORMAT: Write only the title, no additional text.""",
            
            "image_prompt_generation": """Generate a detailed image prompt for creating visuals for this trending topic.

TASK: Create an image prompt that:
- Is visually descriptive and specific
- Captures the essence of the topic
- Uses cinematic, professional photography terms
- Avoids text or logos in the image
- Creates an engaging, shareable visual
- Is suitable for a general audience

TRENDING TOPIC: {topic}
SUMMARY: {summary}

FORMAT: Write only the image prompt, no additional text."""
        }
    
    def generate_trending_summary(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete summary package for a trending topic."""
        try:
            topic = topic_data["topic"]
            search_volume = topic_data["search_volume"]
            context = topic_data.get("context", "")
            
            # Get enhanced context about WHY the topic is trending
            from src.news_context_gatherer import NewsContextGatherer
            context_gatherer = NewsContextGatherer(self.logger)
            enhanced_topic = context_gatherer.gather_trending_context(topic_data)
            
            # Use the comprehensive context summary
            context_summary = enhanced_topic.get("context_summary", context)
            
            self.logger.info(f"📝 Generating summary for: {topic}")
            self.logger.info(f"📊 Context: {context_summary[:100]}...")
            
            # Generate main summary with enhanced context
            summary = self._generate_summary(topic, search_volume, context_summary)
            if not summary:
                return None
            
            # Generate title
            title = self._generate_title(topic, summary)
            
            # Generate image prompt
            image_prompt = self._generate_image_prompt(topic, summary)
            
            # Create story data (compatible with existing pipeline)
            story_data = {
                "title": title,
                "story": summary,
                "topic": topic,
                "search_volume": search_volume,
                "context": context,
                "image_prompt": image_prompt,
                "music_category": self._determine_music_category(topic, context),
                "generated_date": datetime.now().isoformat(),
                "estimated_duration": self._estimate_duration(summary)
            }
            
            # Create complete package (for backward compatibility)
            summary_package = {
                "topic": topic,
                "search_volume": search_volume,
                "context": context,
                "summary": summary,
                "title": title,
                "image_prompt": image_prompt,
                "story_data": story_data,  # Add story data for pipeline compatibility
                "generated_date": datetime.now().isoformat(),
                "estimated_duration": self._estimate_duration(summary)
            }
            
            self.logger.info(f"✅ Generated summary package for: {topic}")
            self.logger.info(f"📊 Estimated duration: {summary_package['estimated_duration']:.1f}s")
            
            return summary_package
            
        except Exception as e:
            self.logger.error(f"❌ Error generating summary for {topic}: {e}")
            return None
    
    def _generate_summary(self, topic: str, search_volume: int, context: str) -> Optional[str]:
        """Generate the main summary text."""
        try:
            prompt = self.prompts["summary_generation"].format(
                topic=topic,
                search_volume=search_volume,
                context=context
            )
            
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert viral content creator specializing in trending topics and YouTube Shorts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Validate summary length
            word_count = len(summary.split())
            if word_count < 40 or word_count > 120:
                self.logger.warning(f"⚠️ Summary length ({word_count} words) may not be optimal for 20-30s video")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error generating summary: {e}")
            return None
    
    def _generate_title(self, topic: str, summary: str) -> Optional[str]:
        """Generate a compelling title."""
        try:
            prompt = self.prompts["title_generation"].format(
                topic=topic,
                summary=summary
            )
            
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at creating viral YouTube titles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8
            )
            
            title = response.choices[0].message.content.strip()
            
            # Clean up title
            title = title.replace('"', '').replace("'", "")
            if len(title) > 60:
                title = title[:57] + "..."
            
            return title
            
        except Exception as e:
            self.logger.error(f"❌ Error generating title: {e}")
            return f"Trending: {topic}"
    
    def _generate_image_prompt(self, topic: str, summary: str) -> Optional[str]:
        """Generate an image prompt for the topic."""
        try:
            prompt = self.prompts["image_prompt_generation"].format(
                topic=topic,
                summary=summary
            )
            
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at creating detailed image prompts for AI image generation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            image_prompt = response.choices[0].message.content.strip()
            
            # Enhance with technical parameters
            enhanced_prompt = f"{image_prompt}, professional photography, cinematic lighting, high quality, detailed, 4k"
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"❌ Error generating image prompt: {e}")
            return f"Professional photography of {topic}, cinematic lighting, high quality"
    
    def _estimate_duration(self, text: str) -> float:
        """Estimate the duration of text when read aloud."""
        # Average speaking rate: 150 words per minute
        words = len(text.split())
        duration_minutes = words / 150
        return duration_minutes * 60  # Convert to seconds
    
    def _determine_music_category(self, topic: str, context: str) -> str:
        """Determine appropriate music category based on topic and context."""
        topic_lower = topic.lower()
        context_lower = context.lower()
        
        # Entertainment and celebrity news
        entertainment_keywords = ['celebrity', 'movie', 'music', 'actor', 'actress', 'singer', 'award', 'grammy', 'oscar', 'concert', 'performance']
        if any(keyword in topic_lower or keyword in context_lower for keyword in entertainment_keywords):
            return "Uplifting"
        
        # Sports and competition
        sports_keywords = ['game', 'match', 'tournament', 'championship', 'player', 'team', 'sport', 'win', 'lose', 'score']
        if any(keyword in topic_lower or keyword in context_lower for keyword in sports_keywords):
            return "Intense"
        
        # Technology and innovation
        tech_keywords = ['technology', 'ai', 'artificial intelligence', 'robot', 'innovation', 'startup', 'app', 'software', 'digital']
        if any(keyword in topic_lower or keyword in context_lower for keyword in tech_keywords):
            return "Uplifting"
        
        # Politics and serious news
        politics_keywords = ['politics', 'election', 'government', 'president', 'congress', 'policy', 'law', 'court', 'justice']
        if any(keyword in topic_lower or keyword in context_lower for keyword in politics_keywords):
            return "Somber"
        
        # Business and finance
        business_keywords = ['business', 'finance', 'economy', 'market', 'stock', 'company', 'ceo', 'investment', 'money']
        if any(keyword in topic_lower or keyword in context_lower for keyword in business_keywords):
            return "Uplifting"
        
        # Crime and mystery
        crime_keywords = ['crime', 'murder', 'investigation', 'police', 'arrest', 'mystery', 'disappearance', 'suspicious']
        if any(keyword in topic_lower or keyword in context_lower for keyword in crime_keywords):
            return "Mystery"
        
        # Default to uplifting for general trending topics
        return "Uplifting"
    
    def generate_multiple_summaries(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate summaries for multiple trending topics."""
        summaries = []
        
        for i, topic_data in enumerate(topics, 1):
            self.logger.info(f"📝 Processing topic {i}/{len(topics)}: {topic_data['topic']}")
            
            summary_package = self.generate_trending_summary(topic_data)
            if summary_package:
                summaries.append(summary_package)
            
            # Rate limiting
            if i < len(topics):
                time.sleep(2)
        
        self.logger.info(f"✅ Generated {len(summaries)} summary packages")
        return summaries
    
    def save_summaries(self, summaries: List[Dict[str, Any]], output_dir: Path):
        """Save summaries to files."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for summary in summaries:
                topic = summary["topic"]
                sanitized_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
                sanitized_topic = sanitized_topic.replace(' ', '_')
                
                # Save individual summary
                summary_file = output_dir / f"{sanitized_topic}_summary.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                
                # Save summary text
                text_file = output_dir / f"{sanitized_topic}_summary.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {summary['title']}\n\n")
                    f.write(f"Summary: {summary['summary']}\n\n")
                    f.write(f"Image Prompt: {summary['image_prompt']}\n\n")
                    f.write(f"Estimated Duration: {summary['estimated_duration']:.1f} seconds\n")
                    f.write(f"Search Volume: {summary['search_volume']}\n")
                    f.write(f"Context: {summary['context']}\n")
            
            # Save all summaries
            all_summaries_file = output_dir / "all_summaries.json"
            with open(all_summaries_file, 'w', encoding='utf-8') as f:
                json.dump(summaries, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Saved {len(summaries)} summaries to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving summaries: {e}")

def test_summary_generator():
    """Test the summary generator functionality."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_summary_generator")
    
    generator = TrendingSummaryGenerator(logger)
    
    # Test data
    test_topic = {
        "topic": "Taylor Swift Grammy Performance",
        "search_volume": 85,
        "context": "Related: Grammy Awards 2024, Music Awards, Live Performance"
    }
    
    print("📝 Testing Summary Generator...")
    
    summary_package = generator.generate_trending_summary(test_topic)
    
    if summary_package:
        print(f"\n📊 Generated Summary Package:")
        print(f"Topic: {summary_package['topic']}")
        print(f"Title: {summary_package['title']}")
        print(f"Duration: {summary_package['estimated_duration']:.1f}s")
        print(f"\nSummary: {summary_package['summary']}")
        print(f"\nImage Prompt: {summary_package['image_prompt']}")
    else:
        print("❌ Failed to generate summary")

if __name__ == "__main__":
    test_summary_generator() 