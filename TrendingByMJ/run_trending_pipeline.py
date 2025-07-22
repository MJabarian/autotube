#!/usr/bin/env python3
"""
TrendingByMJ - Simple Run Script
Easy way to run the trending topics video generation pipeline
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_environment():
    """Check if required environment variables are set."""
    print("🔧 Checking environment...")
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for GPT summary generation",
        "REPLICATE_API_KEY": "Replicate API key for AI image generation"
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
        else:
            print(f"✅ {var}: {'*' * 10}{os.getenv(var)[-4:]}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(var)
        print("\nPlease set these environment variables:")
        print("export OPENAI_API_KEY='your_openai_api_key'")
        print("export REPLICATE_API_KEY='your_replicate_api_key'")
        return False
    
    return True

def show_banner():
    """Show the TrendingByMJ banner."""
    print("=" * 60)
    print("🚀 TRENDING BY MJ - AUTOMATED VIDEO GENERATOR")
    print("=" * 60)
    print("📊 Fetches trending topics from Google Trends")
    print("📝 Generates engaging 20-30 second summaries")
    print("🎬 Creates professional YouTube Shorts with 6 images")
    print("📱 Optimized for mobile viewing (768x1344)")
    print("=" * 60)

def show_menu():
    """Show the main menu."""
    print("\n🎯 Choose an option:")
    print("1. 🚀 Run Full Pipeline (Fetch + Generate + Create Videos)")
    print("2. 🧪 Test Components (Verify everything works)")
    print("3. 🔍 Fetch Trending Topics Only")
    print("4. 📝 Generate Summaries Only")
    print("5. 🎬 Create Videos Only")
    print("6. 📊 View Configuration")
    print("7. ❌ Exit")
    
    return input("\nEnter your choice (1-7): ").strip()

async def run_full_pipeline():
    """Run the complete trending pipeline."""
    print("\n🚀 Starting TrendingByMJ Full Pipeline...")
    
    try:
        from trending_full_pipeline import TrendingFullPipeline
        
        pipeline = TrendingFullPipeline()
        pipeline.setup_logging()
        
        success = await pipeline.run_full_pipeline()
        
        if success:
            print("\n🎉 Pipeline completed successfully!")
            print("📁 Check the 'output' folder for generated videos")
        else:
            print("\n❌ Pipeline failed. Check the logs for details.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error running pipeline: {e}")
        return False

def test_components():
    """Test individual components."""
    print("\n🧪 Testing TrendingByMJ Components...")
    
    try:
        from test_trending_components import main as test_main
        return test_main() == 0
    except Exception as e:
        print(f"❌ Error testing components: {e}")
        return False

async def fetch_trending_only():
    """Fetch trending topics only."""
    print("\n🔍 Fetching trending topics...")
    
    try:
        from src.trending_fetcher import TrendingFetcher
        import logging
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("fetch_trending")
        
        fetcher = TrendingFetcher(logger)
        topics = fetcher.fetch_trending_topics()
        
        if topics:
            print(f"\n✅ Found {len(topics)} trending topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic['topic']} (Volume: {topic['search_volume']})")
                print(f"     Context: {topic['context']}")
        else:
            print("❌ No trending topics found")
        
        return len(topics) > 0
        
    except Exception as e:
        print(f"❌ Error fetching trending topics: {e}")
        return False

async def generate_summaries_only():
    """Generate summaries only."""
    print("\n📝 Generating summaries...")
    
    try:
        from src.trending_fetcher import TrendingFetcher
        from src.trending_summary_generator import TrendingSummaryGenerator
        import logging
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("generate_summaries")
        
        # First fetch trending topics
        fetcher = TrendingFetcher(logger)
        topics = fetcher.fetch_trending_topics()
        
        if not topics:
            print("❌ No trending topics to generate summaries for")
            return False
        
        # Generate summaries
        generator = TrendingSummaryGenerator(logger)
        summaries = generator.generate_multiple_summaries(topics)
        
        if summaries:
            print(f"\n✅ Generated {len(summaries)} summaries:")
            for i, summary in enumerate(summaries, 1):
                print(f"  {i}. {summary['title']} ({summary['estimated_duration']:.1f}s)")
            
            # Save summaries
            summaries_dir = Path("output/summaries")
            generator.save_summaries(summaries, summaries_dir)
            print(f"💾 Summaries saved to: {summaries_dir}")
        else:
            print("❌ No summaries generated")
        
        return len(summaries) > 0
        
    except Exception as e:
        print(f"❌ Error generating summaries: {e}")
        return False

def create_videos_only():
    """Create videos only (requires existing summaries)."""
    print("\n🎬 Creating videos...")
    
    try:
        # Check if summaries exist
        summaries_dir = Path("output/summaries")
        if not summaries_dir.exists():
            print("❌ No summaries found. Please generate summaries first.")
            return False
        
        # This would require existing story data
        print("⚠️ Video creation requires existing story data.")
        print("Please run the full pipeline or generate summaries first.")
        return False
        
    except Exception as e:
        print(f"❌ Error creating videos: {e}")
        return False

def show_configuration():
    """Show current configuration."""
    print("\n📊 TrendingByMJ Configuration:")
    print("=" * 40)
    
    try:
        from config import Config
        
        config_items = [
            ("Max Trending Topics", Config.MAX_TRENDING_TOPICS),
            ("Number of Images", Config.NUM_IMAGES),
            ("Target Duration", f"{Config.TARGET_DURATION_MIN}-{Config.TARGET_DURATION_MAX}s"),
            ("Video Dimensions", f"{Config.VIDEO_WIDTH}x{Config.VIDEO_HEIGHT}"),
            ("TTS Voice", Config.TTS_VOICE),
            ("LLM Model", Config.LLM_MODEL),
            ("Trending Country", Config.TRENDING_COUNTRY),
            ("Trending Timeframe", Config.TRENDING_TIMEFRAME),
            ("Min Search Volume", Config.MIN_SEARCH_VOLUME),
            ("History File", Config.HISTORY_FILE),
        ]
        
        for name, value in config_items:
            print(f"  {name}: {value}")
        
        print("\n📁 Directories:")
        print(f"  Project Root: {Config.PROJECT_ROOT}")
        print(f"  Output: {Config.OUTPUT_DIR}")
        print(f"  Data: {Config.DATA_DIR}")
        print(f"  Logs: {Config.LOGS_DIR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error showing configuration: {e}")
        return False

async def main():
    """Main function."""
    show_banner()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please set required variables.")
        return 1
    
    while True:
        choice = show_menu()
        
        if choice == "1":
            success = await run_full_pipeline()
            if not success:
                print("\n⚠️ Pipeline failed. Check logs for details.")
        
        elif choice == "2":
            success = test_components()
            if not success:
                print("\n⚠️ Some component tests failed.")
        
        elif choice == "3":
            success = await fetch_trending_only()
            if not success:
                print("\n⚠️ Trending fetch failed.")
        
        elif choice == "4":
            success = await generate_summaries_only()
            if not success:
                print("\n⚠️ Summary generation failed.")
        
        elif choice == "5":
            success = create_videos_only()
            if not success:
                print("\n⚠️ Video creation failed.")
        
        elif choice == "6":
            show_configuration()
        
        elif choice == "7":
            print("\n👋 Goodbye! Thanks for using TrendingByMJ!")
            break
        
        else:
            print("\n❌ Invalid choice. Please enter 1-7.")
        
        # Ask if user wants to continue
        if choice != "7":
            continue_choice = input("\n🔄 Run another operation? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("\n👋 Goodbye! Thanks for using TrendingByMJ!")
                break

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user. Goodbye!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 