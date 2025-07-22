"""
YouTube Setup Script for AutoTube
Helps users configure their YouTube channels for posting
"""

import json
import os
from pathlib import Path
import sys

def setup_youtube_channels():
    """Interactive setup for YouTube channels."""
    print("🎬 YouTube Shorts Setup for AutoTube")
    print("=" * 50)
    
    # Create social_media directory
    social_media_dir = Path(__file__).parent
    social_media_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = social_media_dir / "youtube_config.json"
    
    print(f"\n📁 Configuration will be saved to: {config_file}")
    
    # Check if config already exists
    if config_file.exists():
        print("\n⚠️  YouTube config already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("\n🔧 Let's set up your YouTube channels...")
    
    channels = {}
    
    # Setup first channel
    print("\n📺 Channel 1 Setup:")
    print("-" * 30)
    
    channel1_name = input("Channel name (e.g., 'History Channel 1'): ").strip()
    if not channel1_name:
        channel1_name = "History Channel 1"
    
    channel1_id = input("YouTube Channel ID (optional, can be found later): ").strip()
    if not channel1_id:
        channel1_id = "YOUR_CHANNEL_ID_HERE"
    
    api_key1 = input("YouTube API Key (optional, can be added later): ").strip()
    if not api_key1:
        api_key1 = "YOUR_API_KEY_HERE"
    
    channels["channel1"] = {
        "name": channel1_name,
        "description": "First history channel for educational content",
        "credentials_file": "credentials_channel1.json",
        "client_secrets_file": "client_secrets_channel1.json",
        "enabled": True,
        "api_key": api_key1,
        "channel_id": channel1_id
    }
    
    # Ask about second channel
    print("\n📺 Channel 2 Setup:")
    print("-" * 30)
    
    setup_channel2 = input("Do you want to set up a second channel? (y/N): ").lower()
    
    if setup_channel2 == 'y':
        channel2_name = input("Channel name (e.g., 'History Channel 2'): ").strip()
        if not channel2_name:
            channel2_name = "History Channel 2"
        
        channel2_id = input("YouTube Channel ID (optional): ").strip()
        if not channel2_id:
            channel2_id = "YOUR_CHANNEL_ID_HERE"
        
        api_key2 = input("YouTube API Key (optional): ").strip()
        if not api_key2:
            api_key2 = "YOUR_API_KEY_HERE"
        
        channels["channel2"] = {
            "name": channel2_name,
            "description": "Second history channel for viral content",
            "credentials_file": "credentials_channel2.json",
            "client_secrets_file": "client_secrets_channel2.json",
            "enabled": True,
            "api_key": api_key2,
            "channel_id": channel2_id
        }
    
    # Create full config
    config = {
        "channels": channels,
        "default_settings": {
            "made_for_kids": False,
            "privacy_status": "public",
            "category_id": "27",
            "tags": ["history", "shorts", "educational", "viral", "youtube shorts"],
            "language": "en",
            "location": "US",
            "thumbnail_path": None,
            "playlist_id": None
        },
        "upload_settings": {
            "max_retries": 3,
            "timeout_seconds": 300,
            "chunk_size_mb": 10,
            "resumable_upload": True
        },
        "description_template": {
            "include_tags": True,
            "include_links": False,
            "include_timestamp": True,
            "custom_footer": "🔔 Subscribe for more historical content!\n📚 Learn something new every day!"
        }
    }
    
    # Save config
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ YouTube configuration saved to: {config_file}")
    
    # Show next steps
    print("\n📋 Next Steps:")
    print("1. Get YouTube API credentials:")
    print("   • Go to https://console.developers.google.com/")
    print("   • Create a new project or select existing")
    print("   • Enable YouTube Data API v3")
    print("   • Create credentials (API Key)")
    print("   • Download client_secrets.json for OAuth2")
    
    print("\n2. Update your config file with:")
    print("   • API Key")
    print("   • Channel ID (found in YouTube Studio)")
    print("   • Client secrets file path")
    
    print("\n3. Test your setup:")
    print("   python youtube_shorts_poster.py --list-channels")
    
    print("\n4. Post a video:")
    print("   python youtube_shorts_poster.py 'YourTopicName'")
    print("   python youtube_shorts_poster.py 'YourTopicName' --channel channel1")

def show_help():
    """Show help information."""
    print("\n🎬 YouTube Shorts Poster Help")
    print("=" * 40)
    
    print("\n📋 Commands:")
    print("• Setup: python setup_youtube.py")
    print("• List channels: python youtube_shorts_poster.py --list-channels")
    print("• Post to all channels: python youtube_shorts_poster.py 'TopicName'")
    print("• Post to specific channel: python youtube_shorts_poster.py 'TopicName' --channel channel1")
    
    print("\n📁 File Structure:")
    print("social_media/")
    print("├── youtube_config.json          # Channel configuration")
    print("├── youtube_shorts_poster.py     # Main posting script")
    print("├── setup_youtube.py             # Setup script")
    print("├── credentials_channel1.json    # OAuth2 credentials (after setup)")
    print("└── credentials_channel2.json    # OAuth2 credentials (after setup)")
    
    print("\n🔧 Configuration:")
    print("• Edit youtube_config.json to add your API keys and channel IDs")
    print("• Set 'enabled': false to disable a channel")
    print("• Customize tags, description template, and upload settings")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_help()
    else:
        setup_youtube_channels() 