"""
Test TrendingByMJ Components
Test each component individually to ensure they work correctly
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config

def test_config():
    """Test configuration loading."""
    print("🔧 Testing Configuration...")
    
    try:
        print(f"✅ Project root: {Config.PROJECT_ROOT}")
        print(f"✅ Max trending topics: {Config.MAX_TRENDING_TOPICS}")
        print(f"✅ Number of images: {Config.NUM_IMAGES}")
        print(f"✅ Target duration: {Config.TARGET_DURATION_MIN}-{Config.TARGET_DURATION_MAX}s")
        print(f"✅ Video dimensions: {Config.VIDEO_WIDTH}x{Config.VIDEO_HEIGHT}")
        print(f"✅ TTS voice: {Config.TTS_VOICE}")
        print(f"✅ LLM model: {Config.LLM_MODEL}")
        print(f"✅ History file: {Config.HISTORY_FILE}")
        
        # Check API keys
        if Config.OPENAI_API_KEY:
            print(f"✅ OpenAI API key: {'*' * 10}{Config.OPENAI_API_KEY[-4:]}")
        else:
            print("❌ OpenAI API key not found")
        
        if Config.REPLICATE_API_KEY:
            print(f"✅ Replicate API key: {'*' * 10}{Config.REPLICATE_API_KEY[-4:]}")
        else:
            print("❌ Replicate API key not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_trending_fetcher():
    """Test Google Trends fetcher."""
    print("\n🔍 Testing Trending Fetcher...")
    
    try:
        from src.simple_trending_fetcher import SimpleTrendingFetcher
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("test_trending_fetcher")
        
        # Initialize fetcher
        fetcher = SimpleTrendingFetcher(logger)
        print("✅ SimpleTrendingFetcher initialized")
        
        # Test history loading
        print(f"✅ History loaded: {len(fetcher.history.get('topics', []))} topics")
        
        # Test trending topics fetch (limited to 2 for testing)
        print("🔍 Fetching trending topics (limited to 2)...")
        topics = fetcher.fetch_trending_topics()
        
        if topics:
            print(f"✅ Found {len(topics)} trending topics:")
            for i, topic in enumerate(topics[:2], 1):
                print(f"  {i}. {topic['topic']} (Volume: {topic['search_volume']})")
                print(f"     Context: {topic['context']}")
        else:
            print("⚠️ No trending topics found (this might be normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Trending fetcher test failed: {e}")
        return False

def test_summary_generator():
    """Test summary generator."""
    print("\n📝 Testing Summary Generator...")
    
    try:
        from src.trending_summary_generator import TrendingSummaryGenerator
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("test_summary_generator")
        
        # Check OpenAI API key
        if not Config.OPENAI_API_KEY:
            print("❌ OpenAI API key required for summary generation")
            return False
        
        # Initialize generator
        generator = TrendingSummaryGenerator(logger)
        print("✅ TrendingSummaryGenerator initialized")
        
        # Get real trending topics for testing
        from src.simple_trending_fetcher import SimpleTrendingFetcher
        trending_fetcher = SimpleTrendingFetcher(logger)
        trending_topics = trending_fetcher.fetch_trending_topics()
        
        if not trending_topics:
            print("❌ No trending topics available for testing")
            return False
        
        # Use the first real trending topic
        test_topic = trending_topics[0]
        print(f"📝 Using real trending topic: {test_topic['topic']}")
        
        # Generate summary
        print("📝 Generating test summary...")
        summary_package = generator.generate_trending_summary(test_topic)
        
        if summary_package:
            print("✅ Summary generated successfully:")
            print(f"  Topic: {summary_package['topic']}")
            print(f"  Title: {summary_package['title']}")
            print(f"  Duration: {summary_package['estimated_duration']:.1f}s")
            print(f"  Summary: {summary_package['summary'][:100]}...")
            print(f"  Image Prompt: {summary_package['image_prompt'][:100]}...")
        else:
            print("❌ Summary generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Summary generator test failed: {e}")
        return False

def test_video_composer():
    """Test video composer with 6 images."""
    print("\n🎬 Testing Video Composer...")
    
    try:
        from src.video_composition.moviepy_video_composer import MoviePyVideoComposer
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("test_video_composer")
        
        # Initialize composer
        composer = MoviePyVideoComposer(output_dir=Config.VIDEOS_DIR, logger=logger)
        print("✅ MoviePyVideoComposer initialized")
        
        # Test core effects
        effects = composer.get_core_effects()
        print(f"✅ Core effects: {effects}")
        
        # Test random effects generation for 6 images
        random_effects = composer.generate_random_effects(6)
        print(f"✅ Random effects for 6 images: {random_effects}")
        
        # Test image loading (if test images exist)
        test_image_dir = Config.IMAGES_DIR
        if test_image_dir.exists() and any(test_image_dir.iterdir()):
            print("✅ Test images directory exists")
        else:
            print("⚠️ No test images found (this is normal for first run)")
        
        return True
        
    except Exception as e:
        print(f"❌ Video composer test failed: {e}")
        return False

def test_pipeline_integration():
    """Test pipeline integration."""
    print("\n🔗 Testing Pipeline Integration...")
    
    try:
        # Test imports
        from partial_pipelines.content_generation_pipeline import test_complete_replicate_pipeline_whisper
        from partial_pipelines.audio_video_processor_pipeline import process_video_for_topic
        from src.utils.folder_utils import sanitize_folder_name
        
        print("✅ All pipeline components imported successfully")
        
        # Test folder utilities
        test_name = "Test Trending Topic 123!"
        sanitized = sanitize_folder_name(test_name)
        print(f"✅ Folder sanitization: '{test_name}' → '{sanitized}'")
        
        # Test directory creation
        test_dir = Config.OUTPUT_DIR / "test_integration"
        test_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory creation: {test_dir}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        print("✅ Test cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline integration test failed: {e}")
        return False

def main():
    """Run all component tests."""
    print("🧪 TRENDING BY MJ - COMPONENT TESTS")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Trending Fetcher", test_trending_fetcher),
        ("Summary Generator", test_summary_generator),
        ("Video Composer", test_video_composer),
        ("Pipeline Integration", test_pipeline_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! TrendingByMJ is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 