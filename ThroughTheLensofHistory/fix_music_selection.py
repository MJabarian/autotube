"""
Quick script to fix missing music selection for a specific topic.
"""
import json
import random
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config

def fix_music_selection(topic_name: str):
    """Fix music selection for a specific topic by finding available music and creating JSON."""
    
    # Sanitize topic name
    sanitized_name = topic_name.replace(' ', '').replace('-', '').replace('_', '')
    
    print(f"🔧 Fixing music selection for topic: {topic_name}")
    print(f"📁 Sanitized name: {sanitized_name}")
    
    # Find available music files
    music_dir = project_root / "data" / "music"
    print(f"🎵 Looking for music in: {music_dir}")
    
    if not music_dir.exists():
        print(f"❌ Music directory not found: {music_dir}")
        return False
    
    # Get all music files from all categories
    all_music_files = []
    categories = ["Intense", "Somber", "Uplifting", "Mystery"]
    
    for category in categories:
        category_dir = music_dir / category
        if category_dir.exists():
            music_files = list(category_dir.glob("*.wav")) + list(category_dir.glob("*.mp3"))
            for music_file in music_files:
                all_music_files.append((category, str(music_file)))
    
    if not all_music_files:
        print("❌ No music files found!")
        return False
    
    print(f"✅ Found {len(all_music_files)} music files")
    
    # Select a random music file from Intense category for this topic
    intense_music_files = [(cat, file) for cat, file in all_music_files if cat == "Intense"]
    if intense_music_files:
        selected_category, selected_music_file = random.choice(intense_music_files)
    else:
        # Fallback to any category if no Intense music found
        selected_category, selected_music_file = random.choice(all_music_files)
    print(f"🎵 Selected music: {Path(selected_music_file).name}")
    print(f"📂 Category: {selected_category}")
    print(f"📍 Full path: {selected_music_file}")
    
    # Verify the music file exists
    if not Path(selected_music_file).exists():
        print(f"❌ Selected music file doesn't exist: {selected_music_file}")
        return False
    
    # Create music selection data
    music_data = {
        "story_title": topic_name,
        "music_category": selected_category,
        "selected_music_file": selected_music_file,
        "music_filename": Path(selected_music_file).name,
        "selection_timestamp": "2025-07-18T14:40:00",
        "story_data": {
            "title": topic_name,
            "hook": "",
            "story_length_words": 0,
            "music_category": selected_category
        }
    }
    
    # Create output directory
    output_dir = Config.OUTPUT_DIR / "music_selections" / sanitized_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON file
    json_file = output_dir / "music_selection.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(music_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Music selection saved to: {json_file}")
    print(f"📄 JSON content preview:")
    print(json.dumps(music_data, indent=2)[:500] + "...")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_music_selection.py <topic_name>")
        print("Example: python fix_music_selection.py 'TheDayBeesStoleaBaseballGame'")
        sys.exit(1)
    
    topic_name = sys.argv[1]
    success = fix_music_selection(topic_name)
    
    if success:
        print("\n🎉 Music selection fixed successfully!")
        print("🚀 You can now run the audio/video processor:")
        print(f"   python audio_video_processor_pipeline.py '{topic_name}'")
    else:
        print("\n❌ Failed to fix music selection!")
        sys.exit(1) 