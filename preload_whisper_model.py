"""
Pre-load Whisper Model
Download and cache the Whisper model once to avoid repeated downloads
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def preload_whisper_model():
    """Pre-load the Whisper model to cache it properly."""
    
    print("Pre-loading Whisper Model")
    print("=" * 40)
    
    try:
        from faster_whisper import WhisperModel
        
        print("Loading Whisper model (base)...")
        start_time = time.time()
        
        # This will download and cache the model
        model = WhisperModel("small", compute_type="int8")
        
        load_time = time.time() - start_time
        print(f"Model loaded successfully in {load_time:.2f} seconds")
        
        # Test transcription to ensure it's working
        print("Testing model with a simple audio file...")
        
        # Check if we have the test audio
        test_audio = "temp-audio.m4a"
        if os.path.exists(test_audio):
            print(f"Testing with: {test_audio}")
            segments, info = model.transcribe(test_audio, word_timestamps=True)
            
            # Just get first few words to test
            word_count = 0
            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        print(f"  Word: '{word.word}' ({word.start:.2f}s - {word.end:.2f}s)")
                        word_count += 1
                        if word_count >= 5:  # Just show first 5 words
                            break
                    if word_count >= 5:
                        break
            
            print(f"Model test successful! Found {word_count} words")
        else:
            print("No test audio found, but model loaded successfully")
        
        # Show cache location
        print("\nModel Cache Information:")
        print("-" * 30)
        
        # Check common faster-whisper cache locations
        cache_locations = [
            os.path.expanduser("~/.cache/faster-whisper"),
            os.path.expanduser("~/.cache/huggingface/hub"),
            os.path.expanduser("~/AppData/Local/huggingface/hub"),
            "./.cache/faster-whisper",
            "./models"
        ]
        
        for location in cache_locations:
            if os.path.exists(location):
                print(f"Found cache: {location}")
                # Look for whisper models
                for root, dirs, files in os.walk(location):
                    for dir_name in dirs:
                        if "whisper" in dir_name.lower():
                            model_path = os.path.join(root, dir_name)
                            size_mb = sum(os.path.getsize(os.path.join(dirpath, filename))
                                         for dirpath, dirnames, filenames in os.walk(model_path)
                                         for filename in filenames) / (1024 * 1024)
                            print(f"  - {model_path} ({size_mb:.1f} MB)")
        
        print("\nNext time you run the subtitle processor, it should use the cached model!")
        return True
        
    except Exception as e:
        print(f"Error pre-loading model: {e}")
        return False

if __name__ == "__main__":
    preload_whisper_model() 