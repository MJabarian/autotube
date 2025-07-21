"""
Music selection utility for video generation.
"""
import os
import random
import json
import re
from pathlib import Path
from typing import Optional

class MusicSelector:
    """Handles music file selection based on story classification."""
    
    def __init__(self, music_dir: Optional[str] = None):
        """Initialize with music directory path."""
        if music_dir:
            self.music_dir = Path(music_dir)
        else:
            # Default to data/music in project root
            self.music_dir = Path(__file__).parent.parent.parent / "data" / "music"
        
        self.categories = ["Intense", "Somber", "Uplifting", "Mystery"]
    
    def get_music_file(self, category: str) -> Optional[str]:
        """
        Get a random music file from the specified category.
        
        Args:
            category: Music category (Intense, Somber, Uplifting, Mystery)
            
        Returns:
            Path to selected music file or None if not found
        """
        if category not in self.categories:
            print(f"[WARNING] Invalid music category '{category}', using 'Intense'")
            category = "Intense"
        
        category_dir = self.music_dir / category
        if not category_dir.exists():
            print(f"[ERROR] Music category directory not found: {category_dir}")
            return None
        
        # Get all music files (.wav and .mp3) in the category directory
        music_files = list(category_dir.glob("*.wav")) + list(category_dir.glob("*.mp3"))
        
        if not music_files:
            print(f"[ERROR] No music files found in category: {category}")
            return None
        
        # Select a random music file
        selected_file = random.choice(music_files)
        print(f"[INFO] Selected music file: {selected_file} for category: {category}")
        
        return str(selected_file)
    
    def get_music_file_by_story(self, story_data: dict, story_title: str = None) -> Optional[str]:
        """
        Get music file based on story's music category and save selection data.
        
        Args:
            story_data: Story dictionary containing 'music_category' key
            story_title: Title of the story for folder creation
            
        Returns:
            Path to selected music file or None if not found
        """
        category = story_data.get('music_category', 'Intense')
        music_file = self.get_music_file(category)
        
        # Save music selection data if story_title is provided
        if story_title and music_file:
            self._save_music_selection(story_title, category, music_file, story_data)
        
        return music_file
    
    def _save_music_selection(self, story_title: str, category: str, music_file: str, story_data: dict):
        """
        Save music selection data to a JSON file in the story's folder.
        
        Args:
            story_title: Title of the story
            category: Selected music category
            music_file: Path to selected music file
            story_data: Full story data
        """
        try:
            # Create output directory structure
            # Use absolute path to ensure consistent output location
            import sys
            from pathlib import Path

            # Add project root to path to import config
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))

            from config import Config
            output_dir = Config.OUTPUT_DIR / "music_selections"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Sanitize story title for folder name
            sanitized_title = self._sanitize_folder_name(story_title)
            story_dir = output_dir / sanitized_title
            story_dir.mkdir(parents=True, exist_ok=True)
            
            # Create music selection data
            from datetime import datetime
            music_data = {
                "story_title": story_title,
                "music_category": category,
                "selected_music_file": music_file,
                "music_filename": Path(music_file).name,
                "selection_timestamp": datetime.now().isoformat(),
                "story_data": {
                    "title": story_data.get('title', ''),
                    "hook": story_data.get('hook', ''),
                    "story_length_words": len(story_data.get('story', '').split()),
                    "music_category": story_data.get('music_category', '')
                }
            }
            
            # Save to JSON file
            json_file = story_dir / "music_selection.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(music_data, f, indent=2, ensure_ascii=False)
            
            print(f"[INFO] Music selection saved to: {json_file}")
            
        except Exception as e:
            print(f"[ERROR] Failed to save music selection: {e}")
    
    def _sanitize_folder_name(self, title: str) -> str:
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', title)
        sanitized = sanitized.replace(' ', '_')
        return sanitized[:50]
    
    def list_available_music(self) -> dict:
        """
        List all available music files by category.
        
        Returns:
            Dictionary with categories as keys and lists of music files as values
        """
        available_music = {}
        
        for category in self.categories:
            category_dir = self.music_dir / category
            if category_dir.exists():
                music_files = [f.name for f in category_dir.glob("*.wav")] + [f.name for f in category_dir.glob("*.mp3")]
                available_music[category] = music_files
            else:
                available_music[category] = []
        
        return available_music

# Example usage
if __name__ == "__main__":
    selector = MusicSelector()
    
    # List available music
    print("Available music files:")
    for category, files in selector.list_available_music().items():
        print(f"{category}: {len(files)} files")
    
    # Test music selection
    test_story = {"music_category": "Intense"}
    music_file = selector.get_music_file_by_story(test_story)
    print(f"Selected music: {music_file}") 