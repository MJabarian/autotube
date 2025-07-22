"""
TrendingByMJ Configuration
Configuration for trending topics video generation pipeline
"""

import os
from pathlib import Path
from typing import Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = OUTPUT_DIR / "logs"
STORIES_DIR = OUTPUT_DIR / "stories"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEOS_DIR = OUTPUT_DIR / "videos"
IMAGES_DIR = OUTPUT_DIR / "images"
MUSIC_DIR = DATA_DIR / "music"

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUT_DIR, LOGS_DIR, STORIES_DIR, AUDIO_DIR, VIDEOS_DIR, IMAGES_DIR, MUSIC_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Trending topics configuration
TRENDING_CONFIG = {
    "country": "US",  # Country for Google Trends
    "max_topics": 20,  # Number of trending topics to fetch for selection
    "timeframe": "1d",  # Timeframe for trends (1d = last 24 hours)
    "category": "all",  # Category for trends
    "min_search_volume": 20,  # Lowered threshold to capture more trending topics
}

# Video configuration for trending topics
VIDEO_CONFIG = {
    "num_images": 6,  # Number of images (reduced from 12)
    "target_duration_min": 20,  # Minimum video duration in seconds
    "target_duration_max": 30,  # Maximum video duration in seconds
    "width": 768,  # Video width
    "height": 1344,  # Video height (vertical for shorts)
    "fps": 30,  # Frames per second
    "enable_ken_burns": True,  # Enable Ken Burns effects
}

# Audio settings
AUDIO_CONFIG = {
    "tts_voice": "alloy",  # TTS voice for trending topics
    "speech_rate": 1.0,  # Speech rate (1.0 = normal)
    "background_music_volume": 0.3,  # Background music volume (0.0-1.0)
}

# LLM configuration
LLM_CONFIG = {
    "model": "gpt-4o-mini",  # Model for generating summaries
    "max_tokens": 500,  # Maximum tokens for summary generation
    "temperature": 0.7,  # Creativity level for summaries
}

# Image generation configuration
IMAGE_CONFIG = {
    "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    "num_images": 6,  # Number of images to generate
    "width": 768,
    "height": 1344,
    "prompt_strength": 7.5,
    "guidance_scale": 7.5,
    "num_inference_steps": 20,
}

# History tracking configuration
HISTORY_CONFIG = {
    "history_file": DATA_DIR / "trending_history.json",  # File to store trending history
    "max_history_size": 1000,  # Maximum number of topics to keep in history
    "avoid_recent_days": 7,  # Avoid topics from last 7 days
}

# API Keys (load from environment variables)
API_KEYS = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "replicate_api_key": os.getenv("REPLICATE_API_TOKEN"),  # Fixed: use REPLICATE_API_TOKEN
    "google_trends_api_key": os.getenv("GOOGLE_TRENDS_API_KEY"),  # Optional for pytrends
    "news_api_key": os.getenv("NEWS_API_KEY"),  # For real-time news gathering
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_logging": True,
    "console_logging": True,
}

# Paths for easy access
PATHS = {
    "project_root": PROJECT_ROOT,
    "data_dir": DATA_DIR,
    "output_dir": OUTPUT_DIR,
    "logs_dir": LOGS_DIR,
    "stories_dir": STORIES_DIR,
    "audio_dir": AUDIO_DIR,
    "videos_dir": VIDEOS_DIR,
    "images_dir": IMAGES_DIR,
    "music_dir": MUSIC_DIR,
}

class Config:
    """Configuration class for easy access to all settings."""
    
    # Directories
    PROJECT_ROOT = PROJECT_ROOT
    DATA_DIR = DATA_DIR
    OUTPUT_DIR = OUTPUT_DIR
    LOGS_DIR = LOGS_DIR
    STORIES_DIR = STORIES_DIR
    AUDIO_DIR = AUDIO_DIR
    VIDEOS_DIR = VIDEOS_DIR
    IMAGES_DIR = IMAGES_DIR
    MUSIC_DIR = MUSIC_DIR
    
    # Trending configuration
    TRENDING_COUNTRY = TRENDING_CONFIG["country"]
    MAX_TRENDING_TOPICS = TRENDING_CONFIG["max_topics"]
    TRENDING_TIMEFRAME = TRENDING_CONFIG["timeframe"]
    TRENDING_CATEGORY = TRENDING_CONFIG["category"]
    MIN_SEARCH_VOLUME = TRENDING_CONFIG["min_search_volume"]
    
    # Video configuration
    NUM_IMAGES = VIDEO_CONFIG["num_images"]
    TARGET_DURATION_MIN = VIDEO_CONFIG["target_duration_min"]
    TARGET_DURATION_MAX = VIDEO_CONFIG["target_duration_max"]
    VIDEO_WIDTH = VIDEO_CONFIG["width"]
    VIDEO_HEIGHT = VIDEO_CONFIG["height"]
    VIDEO_FPS = VIDEO_CONFIG["fps"]
    ENABLE_KEN_BURNS = VIDEO_CONFIG["enable_ken_burns"]
    
    # Audio configuration
    TTS_VOICE = AUDIO_CONFIG["tts_voice"]
    SPEECH_RATE = AUDIO_CONFIG["speech_rate"]
    BACKGROUND_MUSIC_VOLUME = AUDIO_CONFIG["background_music_volume"]
    
    # LLM configuration
    LLM_MODEL = LLM_CONFIG["model"]
    MAX_TOKENS = LLM_CONFIG["max_tokens"]
    TEMPERATURE = LLM_CONFIG["temperature"]
    
    # Image configuration
    IMAGE_MODEL = IMAGE_CONFIG["model"]
    IMAGE_WIDTH = IMAGE_CONFIG["width"]
    IMAGE_HEIGHT = IMAGE_CONFIG["height"]
    PROMPT_STRENGTH = IMAGE_CONFIG["prompt_strength"]
    GUIDANCE_SCALE = IMAGE_CONFIG["guidance_scale"]
    NUM_INFERENCE_STEPS = IMAGE_CONFIG["num_inference_steps"]
    
    # History configuration
    HISTORY_FILE = HISTORY_CONFIG["history_file"]
    MAX_HISTORY_SIZE = HISTORY_CONFIG["max_history_size"]
    AVOID_RECENT_DAYS = HISTORY_CONFIG["avoid_recent_days"]
    
    # API Keys
    OPENAI_API_KEY = API_KEYS["openai_api_key"]
    REPLICATE_API_KEY = API_KEYS["replicate_api_key"]
    GOOGLE_TRENDS_API_KEY = API_KEYS["google_trends_api_key"]
    NEWS_API_KEY = API_KEYS["news_api_key"]
    
    # Logging
    LOG_LEVEL = LOGGING_CONFIG["level"]
    LOG_FORMAT = LOGGING_CONFIG["format"]
    FILE_LOGGING = LOGGING_CONFIG["file_logging"]
    CONSOLE_LOGGING = LOGGING_CONFIG["console_logging"]

# Export paths for compatibility
PATHS = PATHS 