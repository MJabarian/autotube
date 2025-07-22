"""
YouTube Shorts Poster for AutoTube
Supports multiple channels and individual channel posting
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config

class YouTubeShortsPoster:
    """YouTube Shorts posting system with multi-channel support."""
    
    def __init__(self, config_file: str = "youtube_config.json"):
        self.config_file = Path(__file__).parent / config_file
        self.channels = self._load_channel_config()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for YouTube posting."""
        logger = logging.getLogger("youtube_shorts_poster")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Create logs directory
            logs_dir = Config.OUTPUT_DIR / "social_media_logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # File handler
            log_file = logs_dir / f"youtube_posting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _load_channel_config(self) -> Dict:
        """Load YouTube channel configuration."""
        if not self.config_file.exists():
            self._create_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('channels', {})
        except Exception as e:
            print(f"Error loading YouTube config: {e}")
            return {}
    
    def _create_default_config(self):
        """Create default YouTube configuration file."""
        default_config = {
            "channels": {
                "channel1": {
                    "name": "History Channel 1",
                    "description": "First history channel",
                    "credentials_file": "credentials_channel1.json",
                    "client_secrets_file": "client_secrets_channel1.json",
                    "enabled": True
                },
                "channel2": {
                    "name": "History Channel 2", 
                    "description": "Second history channel",
                    "credentials_file": "credentials_channel2.json",
                    "client_secrets_file": "client_secrets_channel2.json",
                    "enabled": True
                }
            },
            "default_settings": {
                "made_for_kids": False,
                "privacy_status": "public",
                "category_id": "27",  # Education
                "tags": ["history", "shorts", "educational", "viral"],
                "language": "en",
                "location": "US"
            }
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created default YouTube config: {self.config_file}")
        print("📝 Please edit the config file with your actual channel credentials")
    
    def get_available_channels(self) -> List[str]:
        """Get list of available channel IDs."""
        return [channel_id for channel_id, config in self.channels.items() 
                if config.get('enabled', True)]
    
    def load_story_metadata(self, topic_name: str) -> Dict:
        """Load story metadata from the topic's metadata.json file."""
        try:
            # Sanitize topic name for folder
            sanitized_name = topic_name.replace(' ', '').replace('-', '').replace('_', '')
            
            # Path to metadata file
            metadata_path = Config.OUTPUT_DIR / "stories" / sanitized_name / "metadata.json"
            
            if not metadata_path.exists():
                raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            self.logger.info(f"✅ Loaded metadata for topic: {topic_name}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"❌ Error loading metadata: {e}")
            raise
    
    def get_video_path(self, topic_name: str) -> str:
        """Get the path to the final video file."""
        sanitized_name = topic_name.replace(' ', '').replace('-', '').replace('_', '')
        video_path = Config.OUTPUT_DIR / "subtitles_processed_video" / f"{sanitized_name}_final.mp4"
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        return str(video_path)
    
    def prepare_upload_data(self, topic_name: str, channel_id: str) -> Dict:
        """Prepare all data needed for YouTube upload."""
        try:
            # Load metadata
            metadata = self.load_story_metadata(topic_name)
            
            # Get video path
            video_path = self.get_video_path(topic_name)
            
            # Get channel config
            channel_config = self.channels.get(channel_id, {})
            
            # Prepare upload data
            upload_data = {
                "video_path": video_path,
                "title": metadata.get('title', topic_name),
                "description": metadata.get('description', ''),
                "tags": metadata.get('tags', []) + ["history", "shorts", "educational"],
                "category_id": "27",  # Education
                "privacy_status": "public",
                "made_for_kids": False,
                "channel_id": channel_id,
                "channel_name": channel_config.get('name', channel_id),
                "topic_name": topic_name,
                "upload_timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Prepared upload data for {channel_id}: {upload_data['title']}")
            return upload_data
            
        except Exception as e:
            self.logger.error(f"❌ Error preparing upload data: {e}")
            raise
    
    def upload_to_youtube(self, upload_data: Dict) -> bool:
        """Upload video to YouTube using the YouTube Data API."""
        try:
            # This is a placeholder for the actual YouTube API integration
            # You'll need to implement the actual upload logic using google-api-python-client
            
            self.logger.info(f"🎬 Starting YouTube upload for: {upload_data['title']}")
            self.logger.info(f"📺 Channel: {upload_data['channel_name']}")
            self.logger.info(f"📁 Video: {upload_data['video_path']}")
            self.logger.info(f"🏷️ Tags: {', '.join(upload_data['tags'][:5])}...")
            
            # TODO: Implement actual YouTube API upload
            # For now, just log the upload data
            self._save_upload_log(upload_data)
            
            self.logger.info("✅ YouTube upload completed (simulated)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ YouTube upload failed: {e}")
            return False
    
    def _save_upload_log(self, upload_data: Dict):
        """Save upload log for tracking."""
        logs_dir = Config.OUTPUT_DIR / "social_media_logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = logs_dir / f"youtube_uploads_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Load existing logs or create new
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Add new upload log
        logs.append(upload_data)
        
        # Save updated logs
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def post_to_channel(self, topic_name: str, channel_id: str) -> bool:
        """Post a video to a specific YouTube channel."""
        try:
            self.logger.info(f"🚀 Starting YouTube posting for channel: {channel_id}")
            
            # Prepare upload data
            upload_data = self.prepare_upload_data(topic_name, channel_id)
            
            # Upload to YouTube
            success = self.upload_to_youtube(upload_data)
            
            if success:
                self.logger.info(f"✅ Successfully posted to {channel_id}")
            else:
                self.logger.error(f"❌ Failed to post to {channel_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error posting to {channel_id}: {e}")
            return False
    
    def post_to_all_channels(self, topic_name: str) -> Dict[str, bool]:
        """Post a video to all enabled YouTube channels."""
        results = {}
        available_channels = self.get_available_channels()
        
        if not available_channels:
            self.logger.error("❌ No enabled channels found")
            return results
        
        self.logger.info(f"🎬 Posting to {len(available_channels)} channels: {', '.join(available_channels)}")
        
        for channel_id in available_channels:
            success = self.post_to_channel(topic_name, channel_id)
            results[channel_id] = success
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        self.logger.info(f"📊 Upload Summary: {successful}/{total} channels successful")
        
        return results
    
    def list_channels(self):
        """List all configured channels."""
        print("\n📺 Configured YouTube Channels:")
        print("=" * 50)
        
        for channel_id, config in self.channels.items():
            status = "✅ Enabled" if config.get('enabled', True) else "❌ Disabled"
            print(f"• {channel_id}: {config.get('name', 'Unnamed')} - {status}")
        
        print(f"\n📁 Config file: {self.config_file}")
        print("💡 Edit the config file to add your channel credentials")

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="YouTube Shorts Poster")
    parser.add_argument("topic_name", help="Name of the topic to post")
    parser.add_argument("--channel", "-c", help="Specific channel ID to post to")
    parser.add_argument("--list-channels", "-l", action="store_true", help="List available channels")
    parser.add_argument("--config", help="Path to YouTube config file")
    
    args = parser.parse_args()
    
    # Initialize poster
    config_file = args.config or "youtube_config.json"
    poster = YouTubeShortsPoster(config_file)
    
    if args.list_channels:
        poster.list_channels()
        return
    
    if args.channel:
        # Post to specific channel
        success = poster.post_to_channel(args.topic_name, args.channel)
        if success:
            print(f"✅ Successfully posted to {args.channel}")
        else:
            print(f"❌ Failed to post to {args.channel}")
            sys.exit(1)
    else:
        # Post to all channels
        results = poster.post_to_all_channels(args.topic_name)
        successful = sum(results.values())
        total = len(results)
        
        print(f"\n📊 Upload Results:")
        for channel_id, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"• {channel_id}: {status}")
        
        if successful == total:
            print(f"\n🎉 All uploads successful!")
        else:
            print(f"\n⚠️ {total - successful} upload(s) failed")
            sys.exit(1)

if __name__ == "__main__":
    main() 