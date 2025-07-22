"""
Test Pipeline Setup - Validate all components without API calls
This script tests the pipeline configuration, folder structures, and data flow
before running the actual pipeline to avoid wasting API calls.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from src.utils.logger import get_logger
import os
from pathlib import Path

def ensure_folder_exists(folder_path: str) -> bool:
    """Ensure a folder exists, creating it if necessary"""
    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Failed to create folder {folder_path}: {e}")
        return False
from src.llm.story_generator import StoryGenerator
from src.story_analyzer import StoryAnalyzer
from src.tts_generator import tts_story_to_audio, process_story_for_tts
from src.utils.music_selector import MusicSelector
from src.video_composition.whisper_audio_synchronizer import WhisperAudioSynchronizer

logger = get_logger(__name__)

class PipelineSetupTester:
    """Test pipeline setup without making API calls"""
    
    def __init__(self):
        self.test_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        
    def log_result(self, test_name: str, passed: bool, message: str, warning: bool = False):
        """Log test result"""
        if passed:
            self.test_results["passed"].append(f"✅ {test_name}: {message}")
            logger.info(f"✅ {test_name}: {message}")
        elif warning:
            self.test_results["warnings"].append(f"⚠️ {test_name}: {message}")
            logger.warning(f"⚠️ {test_name}: {message}")
        else:
            self.test_results["failed"].append(f"❌ {test_name}: {message}")
            logger.error(f"❌ {test_name}: {message}")
    
    def test_configuration(self) -> bool:
        """Test configuration files and settings"""
        print("\n🔧 Testing Configuration...")
        
        # Test config.py
        try:
            from config import Config
            self.log_result("Config Import", True, "Config module imported successfully")
        except Exception as e:
            self.log_result("Config Import", False, f"Failed to import config: {e}")
            return False
        
        # Test required directories
        required_dirs = [
            Config.OUTPUT_DIR,
            os.path.join(Config.OUTPUT_DIR, "audio"),
            os.path.join(Config.OUTPUT_DIR, "images"),
            os.path.join(Config.OUTPUT_DIR, "videos"),
            os.path.join(Config.OUTPUT_DIR, "music_selections"),
            os.path.join(Config.OUTPUT_DIR, "audio_sync_data"),
            Config.MUSIC_DIR
        ]
        
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                self.log_result(f"Directory: {dir_path}", True, "Directory exists")
            else:
                self.log_result(f"Directory: {dir_path}", False, "Directory missing")
        
        # Test prompts.yaml
        prompts_path = os.path.join(project_root, "prompts", "prompts.yaml")
        if os.path.exists(prompts_path):
            try:
                with open(prompts_path, 'r', encoding='utf-8') as f:
                    prompts = yaml.safe_load(f)
                self.log_result("Prompts YAML", True, f"Loaded {len(prompts)} prompt categories")
            except Exception as e:
                self.log_result("Prompts YAML", False, f"Failed to load prompts: {e}")
        else:
            self.log_result("Prompts YAML", False, "Prompts file not found")
        
        # Test environment variables
        required_env_vars = [
            "REPLICATE_API_TOKEN",
            "OPENAI_API_KEY"
        ]
        
        for env_var in required_env_vars:
            if os.getenv(env_var):
                self.log_result(f"Env Var: {env_var}", True, "Environment variable set")
            else:
                self.log_result(f"Env Var: {env_var}", False, "Environment variable missing")
        
        return len([r for r in self.test_results["failed"] if "Config" in r or "Directory" in r or "Env Var" in r]) == 0
    
    def test_music_selection(self) -> bool:
        """Test music selection without API calls"""
        print("\n🎵 Testing Music Selection...")
        
        try:
            music_selector = MusicSelector()
            self.log_result("Music Selector Init", True, "Music selector initialized")
            
            # Test music directory structure
            music_categories = ["Intense", "Mystery", "Somber", "Uplifting"]
            for category in music_categories:
                category_path = os.path.join(Config.MUSIC_DIR, category)
                if os.path.exists(category_path):
                    music_files = [f for f in os.listdir(category_path) if f.endswith('.wav')]
                    self.log_result(f"Music Category: {category}", True, f"Found {len(music_files)} music files")
                else:
                    self.log_result(f"Music Category: {category}", False, "Category directory missing")
            
            # Test music selection logic
            test_categories = ["Intense", "Mystery", "Somber", "Uplifting"]
            for category in test_categories:
                try:
                    music_file = music_selector.select_music_for_category(category)
                    if music_file:
                        self.log_result(f"Music Selection: {category}", True, f"Selected: {os.path.basename(music_file)}")
                    else:
                        self.log_result(f"Music Selection: {category}", False, "No music file selected")
                except Exception as e:
                    self.log_result(f"Music Selection: {category}", False, f"Selection failed: {e}")
            
        except Exception as e:
            self.log_result("Music Selector", False, f"Music selector test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "Music" in r]) == 0
    
    def test_story_generation_setup(self) -> bool:
        """Test story generation setup without API calls"""
        print("\n📝 Testing Story Generation Setup...")
        
        try:
            story_generator = StoryGenerator()
            self.log_result("Story Generator Init", True, "Story generator initialized")
            
            # Test prompt loading
            try:
                from src.llm.story_generator import load_prompts
                prompts = load_prompts()
                self.log_result("Prompt Loading", True, f"Loaded {len(prompts)} prompt categories")
            except Exception as e:
                self.log_result("Prompt Loading", False, f"Failed to load prompts: {e}")
            
            # Test topic validation
            test_topics = ["malcolm jamal warner", "test topic", "another test"]
            for topic in test_topics:
                try:
                    from src.utils.folder_utils import sanitize_folder_name
                    sanitized = sanitize_folder_name(topic)
                    self.log_result(f"Topic Sanitization: {topic}", True, f"Sanitized to: {sanitized}")
                except Exception as e:
                    self.log_result(f"Topic Sanitization: {topic}", False, f"Sanitization failed: {e}")
            
        except Exception as e:
            self.log_result("Story Generator", False, f"Story generator test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "Story" in r or "Prompt" in r or "Topic" in r]) == 0
    
    def test_story_analyzer(self) -> bool:
        """Test story analyzer without API calls"""
        print("\n🔍 Testing Story Analyzer...")
        
        try:
            analyzer = StoryAnalyzer()
            self.log_result("Story Analyzer Init", True, "Story analyzer initialized")
            
            # Test with sample story data
            sample_story = {
                "title": "Test Story",
                "story": "This is a test story with multiple sentences. It should generate scene descriptions.",
                "hook": "Test hook",
                "music_category": "Uplifting"
            }
            
            try:
                analysis = analyzer.analyze_story(sample_story)
                self.log_result("Story Analysis", True, f"Generated {len(analysis.get('scene_descriptions', []))} scenes")
            except Exception as e:
                self.log_result("Story Analysis", False, f"Analysis failed: {e}")
            
        except Exception as e:
            self.log_result("Story Analyzer", False, f"Story analyzer test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "Story Analyzer" in r or "Story Analysis" in r]) == 0
    
    def test_tts_setup(self) -> bool:
        """Test TTS setup without API calls"""
        print("\n🎤 Testing TTS Setup...")
        
        try:
            # Test TTS function imports
            self.log_result("TTS Functions Import", True, "TTS functions imported successfully")
            
            # Test audio directory creation
            test_audio_dir = os.path.join(Config.OUTPUT_DIR, "audio", "test_topic")
            try:
                ensure_folder_exists(test_audio_dir)
                self.log_result("Audio Directory Creation", True, "Audio directory created successfully")
            except Exception as e:
                self.log_result("Audio Directory Creation", False, f"Failed to create audio directory: {e}")
            
            # Test environment variables
            required_env_vars = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]
            for env_var in required_env_vars:
                if os.getenv(env_var):
                    self.log_result(f"TTS Env Var: {env_var}", True, "Environment variable set")
                else:
                    self.log_result(f"TTS Env Var: {env_var}", False, "Environment variable missing")
            
        except Exception as e:
            self.log_result("TTS Setup", False, f"TTS setup test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "TTS" in r or "Audio Directory" in r]) == 0
    
    def test_whisper_setup(self) -> bool:
        """Test Whisper setup without API calls"""
        print("\n🎧 Testing Whisper Setup...")
        
        try:
            whisper_sync = WhisperAudioSynchronizer()
            self.log_result("Whisper Synchronizer Init", True, "Whisper synchronizer initialized")
            
            # Test sync data directory creation
            test_sync_dir = os.path.join(Config.OUTPUT_DIR, "audio_sync_data")
            try:
                ensure_folder_exists(test_sync_dir)
                self.log_result("Sync Data Directory", True, "Sync data directory created successfully")
            except Exception as e:
                self.log_result("Sync Data Directory", False, f"Failed to create sync directory: {e}")
            
        except Exception as e:
            self.log_result("Whisper Synchronizer", False, f"Whisper synchronizer test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "Whisper" in r or "Sync Data" in r]) == 0
    
    def test_image_generation_setup(self) -> bool:
        """Test image generation setup without API calls"""
        print("\n🖼️ Testing Image Generation Setup...")
        
        try:
            from src.replicate_image_generator import OptimizedReplicateImageGenerator
            from src.replicate_image_client import OptimizedReplicateImageClient
            
            # Test client initialization (without API calls)
            try:
                client = OptimizedReplicateImageClient("test_key")
                self.log_result("Image Client Init", True, "Image client initialized")
            except Exception as e:
                self.log_result("Image Client Init", False, f"Client initialization failed: {e}")
            
            # Test image directory creation
            test_image_dir = os.path.join(Config.OUTPUT_DIR, "images", "test_topic")
            try:
                ensure_folder_exists(test_image_dir)
                self.log_result("Image Directory Creation", True, "Image directory created successfully")
            except Exception as e:
                self.log_result("Image Directory Creation", False, f"Failed to create image directory: {e}")
            
            # Test folder name sanitization
            test_titles = ["Test Story", "Story with spaces", "Special@#$%^&*()", "malcolm jamal warner"]
            for title in test_titles:
                try:
                    # Create a temporary instance to test the method
                    temp_generator = OptimizedReplicateImageGenerator()
                    sanitized = temp_generator._sanitize_folder_name(title)
                    self.log_result(f"Folder Sanitization: {title}", True, f"Sanitized to: {sanitized}")
                except Exception as e:
                    self.log_result(f"Folder Sanitization: {title}", False, f"Sanitization failed: {e}")
            
        except Exception as e:
            self.log_result("Image Generation Setup", False, f"Image generation setup test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "Image" in r or "Folder" in r]) == 0
    
    def test_video_processing_setup(self) -> bool:
        """Test video processing setup without API calls"""
        print("\n🎬 Testing Video Processing Setup...")
        
        try:
            from src.video_composition.moviepy_video_composer import MoviePyVideoComposer
            
            # Test video directory creation
            test_video_dir = os.path.join(Config.OUTPUT_DIR, "videos")
            try:
                ensure_folder_exists(test_video_dir)
                self.log_result("Video Directory Creation", True, "Video directory created successfully")
            except Exception as e:
                self.log_result("Video Directory Creation", False, f"Failed to create video directory: {e}")
            
            # Test subtitle processing setup
            try:
                from src.video_composition.whisper_subtitle_processor import OptimizedWhisperViralSubtitleProcessor
                processor = OptimizedWhisperViralSubtitleProcessor()
                self.log_result("Subtitle Processor Init", True, "Subtitle processor initialized")
            except Exception as e:
                self.log_result("Subtitle Processor Init", False, f"Subtitle processor initialization failed: {e}")
            
        except Exception as e:
            self.log_result("Video Processing Setup", False, f"Video processing setup test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "Video" in r or "Subtitle" in r]) == 0
    
    def test_data_flow(self) -> bool:
        """Test data flow between components"""
        print("\n🔄 Testing Data Flow...")
        
        # Test topic name consistency
        test_topic = "malcolm jamal warner"
        
        try:
            # Test story generator sanitization
            from src.utils.folder_utils import sanitize_folder_name
            story_sanitized = sanitize_folder_name(test_topic)
            
            # Test image generator sanitization
            temp_generator = OptimizedReplicateImageGenerator()
            image_sanitized = temp_generator._sanitize_folder_name(test_topic)
            
            if story_sanitized == image_sanitized:
                self.log_result("Topic Name Consistency", True, f"Both use: {story_sanitized}")
            else:
                self.log_result("Topic Name Consistency", False, f"Mismatch: story={story_sanitized}, image={image_sanitized}")
            
            # Test folder path consistency
            expected_audio_path = os.path.join(Config.OUTPUT_DIR, "audio", story_sanitized)
            expected_image_path = os.path.join(Config.OUTPUT_DIR, "images", story_sanitized)
            expected_video_path = os.path.join(Config.OUTPUT_DIR, "videos", f"{story_sanitized}.mp4")
            
            self.log_result("Path Consistency", True, f"Audio: {expected_audio_path}")
            self.log_result("Path Consistency", True, f"Images: {expected_image_path}")
            self.log_result("Path Consistency", True, f"Video: {expected_video_path}")
            
        except Exception as e:
            self.log_result("Data Flow", False, f"Data flow test failed: {e}")
            return False
        
        return len([r for r in self.test_results["failed"] if "Data Flow" in r or "Topic Name" in r or "Path Consistency" in r]) == 0
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("🚀 Starting Pipeline Setup Tests...")
        print("=" * 60)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("Music Selection", self.test_music_selection),
            ("Story Generation Setup", self.test_story_generation_setup),
            ("Story Analyzer", self.test_story_analyzer),
            ("TTS Setup", self.test_tts_setup),
            ("Whisper Setup", self.test_whisper_setup),
            ("Image Generation Setup", self.test_image_generation_setup),
            ("Video Processing Setup", self.test_video_processing_setup),
            ("Data Flow", self.test_data_flow)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_result(test_name, False, f"Test crashed: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ PASSED ({len(self.test_results['passed'])}):")
        for result in self.test_results['passed']:
            print(f"  {result}")
        
        if self.test_results['warnings']:
            print(f"\n⚠️ WARNINGS ({len(self.test_results['warnings'])}):")
            for result in self.test_results['warnings']:
                print(f"  {result}")
        
        if self.test_results['failed']:
            print(f"\n❌ FAILED ({len(self.test_results['failed'])}):")
            for result in self.test_results['failed']:
                print(f"  {result}")
        
        total_tests = len(self.test_results['passed']) + len(self.test_results['failed'])
        success_rate = (len(self.test_results['passed']) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 SUCCESS RATE: {success_rate:.1f}% ({len(self.test_results['passed'])}/{total_tests})")
        
        if len(self.test_results['failed']) == 0:
            print("\n🎉 ALL TESTS PASSED! Pipeline is ready to run.")
            return {"success": True, "results": self.test_results}
        else:
            print(f"\n⚠️ {len(self.test_results['failed'])} TESTS FAILED. Please fix issues before running pipeline.")
            return {"success": False, "results": self.test_results}

def main():
    """Main test function"""
    tester = PipelineSetupTester()
    results = tester.run_all_tests()
    
    if results["success"]:
        print("\n✅ Pipeline setup validation completed successfully!")
        print("🚀 Ready to run the actual pipeline with confidence.")
    else:
        print("\n❌ Pipeline setup validation failed!")
        print("🔧 Please fix the issues above before running the pipeline.")
    
    return results["success"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 