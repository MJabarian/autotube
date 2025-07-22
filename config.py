"""
Simple Project-Specific Configuration for ThroughTheLensofHistory
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Output directories (all relative to project root)
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"

# Audio settings
# Using original TTS audio directly - no speed adjustment needed

# API Keys (from .env file)
class API:
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
    RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# RunPod settings
class RUNPOD:
    GPU_TYPE = os.getenv('RUNPOD_GPU_TYPE', 'RTX 3090')
    IMAGE_MODEL = os.getenv('RUNPOD_IMAGE_MODEL', 'flux-dev')
    MAX_IMAGES_PER_BATCH = int(os.getenv('RUNPOD_MAX_IMAGES_PER_BATCH', 20))
    AUTO_SHUTDOWN = os.getenv('RUNPOD_AUTO_SHUTDOWN', 'true').lower() == 'true'
    COST_LIMIT_PER_DAY = float(os.getenv('RUNPOD_COST_LIMIT_PER_DAY', 2.00))

# OpenAI settings
class OPENAI:
    API_KEY = os.getenv('OPENAI_API_KEY', '')
    MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# Main config class
class Config:
    OUTPUT_DIR = OUTPUT_DIR
    DATA_DIR = DATA_DIR
    API = API
    RUNPOD = RUNPOD
    OPENAI = OPENAI

# Paths for easy access
PATHS = {
    'output': OUTPUT_DIR,
    'data': DATA_DIR,
    'stories': OUTPUT_DIR / "stories",
    'audio': OUTPUT_DIR / "audio", 
    'images': OUTPUT_DIR / "images",
    'videos': OUTPUT_DIR / "videos",
    'music_selections': OUTPUT_DIR / "music_selections",
    'mixed_audio': OUTPUT_DIR / "mixed_audio",
    'subtitles_processed_video': OUTPUT_DIR / "subtitles_processed_video",
    'music': DATA_DIR / "music"
} 
