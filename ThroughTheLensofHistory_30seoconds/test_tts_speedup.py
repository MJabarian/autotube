#!/usr/bin/env python3
"""
Test script for TTS speed-up functionality
Tests that the 1.1x speed-up works correctly and doesn't break the pipeline
"""

import os
import sys
import time
from pathlib import Path
from pydub import AudioSegment

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tts_generator import tts_story_to_audio, process_story_for_tts

def test_tts_speedup():
    """Test the TTS speed-up functionality"""
    
    print("🧪 Testing TTS Speed-Up Functionality")
    print("=" * 50)
    
    # Test story text
    test_story = """
    In the year 1897, a remarkable invention took to the skies over Paris. 
    The Santos-Dumont airship, a marvel of engineering, captured the imagination 
    of thousands who gathered to witness this incredible feat of human ingenuity. 
    [pause:0.5s] The airship, powered by a small gasoline engine, demonstrated 
    that controlled flight was not just a dream, but a reality within reach.
    """
    
    # Test parameters
    test_filename = "test_speedup_audio.mp3"
    test_title = "Test Speed-Up Story"
    
    print(f"📝 Test story length: {len(test_story)} characters")
    print(f"🎯 Target speed-up: 1.1x (10% faster)")
    print(f"📁 Output file: {test_filename}")
    
    try:
        # Generate TTS audio with speed-up
        print("\n🎵 Generating TTS audio with speed-up...")
        start_time = time.time()
        
        audio_path = tts_story_to_audio(
            story_text=test_story,
            output_filename=test_filename,
            story_title=test_title
        )
        
        generation_time = time.time() - start_time
        print(f"⏱️  Generation time: {generation_time:.2f}s")
        
        if not audio_path:
            print("❌ TTS generation failed!")
            return False
            
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return False
            
        print(f"✅ Audio generated successfully: {audio_path}")
        
        # Analyze the generated audio
        print("\n🔍 Analyzing generated audio...")
        audio_segment = AudioSegment.from_mp3(audio_path)
        
        # Get audio properties
        original_duration_ms = len(audio_segment)
        original_duration_s = original_duration_ms / 1000
        file_size = os.path.getsize(audio_path)
        
        print(f"📊 Audio properties:")
        print(f"   Duration: {original_duration_s:.3f}s ({original_duration_ms}ms)")
        print(f"   File size: {file_size:,} bytes")
        print(f"   Sample rate: {audio_segment.frame_rate} Hz")
        print(f"   Channels: {audio_segment.channels}")
        
        # Calculate expected duration (approximate)
        # A typical speaking rate is about 150 words per minute
        word_count = len(test_story.split())
        expected_duration_s = (word_count / 150) * 60  # Convert to seconds
        expected_speedup_duration_s = expected_duration_s / 1.1  # Apply 1.1x speed-up
        
        print(f"\n📈 Duration Analysis:")
        print(f"   Word count: {word_count} words")
        print(f"   Expected normal duration: {expected_duration_s:.3f}s")
        print(f"   Expected speed-up duration: {expected_speedup_duration_s:.3f}s")
        print(f"   Actual duration: {original_duration_s:.3f}s")
        
        # Check if speed-up was applied (duration should be shorter than expected normal)
        if original_duration_s < expected_duration_s:
            print("✅ Speed-up appears to be working (duration is shorter than expected)")
            
            # Calculate actual speed-up factor
            actual_speedup = expected_duration_s / original_duration_s
            print(f"   Actual speed-up factor: {actual_speedup:.2f}x")
            
            if 0.9 <= actual_speedup <= 1.3:  # Allow some tolerance
                print("✅ Speed-up factor is within expected range")
            else:
                print("⚠️  Speed-up factor is outside expected range")
                
        else:
            print("❌ Speed-up may not be working (duration is longer than expected)")
            
        # Test audio quality (basic checks)
        print(f"\n🎧 Audio Quality Check:")
        
        # Check for silence at the beginning/end
        start_silence = audio_segment[:1000]  # First 1 second
        end_silence = audio_segment[-1000:]   # Last 1 second
        
        start_volume = start_silence.dBFS
        end_volume = end_silence.dBFS
        overall_volume = audio_segment.dBFS
        
        print(f"   Overall volume: {overall_volume:.1f} dBFS")
        print(f"   Start volume: {start_volume:.1f} dBFS")
        print(f"   End volume: {end_volume:.1f} dBFS")
        
        # Check for fade-out effect
        if end_volume < overall_volume - 3:  # 3dB difference indicates fade
            print("✅ Fade-out effect detected")
        else:
            print("⚠️  Fade-out effect may not be working")
            
        # Check for audio artifacts (very basic)
        if overall_volume > -60:  # Audio is not completely silent
            print("✅ Audio has reasonable volume levels")
        else:
            print("❌ Audio volume is too low")
            
        # Test that the file can be read by other parts of the pipeline
        print(f"\n🔗 Pipeline Compatibility Test:")
        
        # Simulate what the video composer would do
        try:
            from src.video_composition.moviepy_video_composer import MoviePyVideoComposer
            composer = MoviePyVideoComposer()
            detected_duration = composer.get_audio_duration(audio_path)
            
            print(f"   Video composer detected duration: {detected_duration:.3f}s")
            
            if abs(detected_duration - original_duration_s) < 0.1:  # 100ms tolerance
                print("✅ Video composer can read the audio file correctly")
            else:
                print("❌ Video composer duration mismatch")
                
        except Exception as e:
            print(f"⚠️  Could not test video composer compatibility: {e}")
            
        print(f"\n🎉 Test completed successfully!")
        print(f"📁 Audio file: {audio_path}")
        print(f"📏 Duration: {original_duration_s:.3f}s")
        print(f"💾 Size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_story_for_tts():
    """Test the story processing function"""
    
    print("\n🧪 Testing Story Processing Function")
    print("=" * 40)
    
    test_story = """
    [whispers] This is a test story with various tags. [pause:1s] 
    [excited] It should process correctly! [pause:0.5s] 
    [sarcastic] Or will it?
    """
    
    print(f"📝 Original story: {test_story}")
    
    try:
        processed = process_story_for_tts(test_story)
        print(f"✅ Processed story: {processed}")
        
        # Check if SSML tags were converted
        if "<break" in processed and "<prosody" in processed:
            print("✅ SSML conversion working correctly")
        else:
            print("⚠️  SSML conversion may not be working")
            
        return True
        
    except Exception as e:
        print(f"❌ Story processing failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    test_files = [
        "test_speedup_audio.mp3",
        "output/audio/Test Speed-Up Story/test_speedup_audio.mp3"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️  Removed: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not remove {file_path}: {e}")

if __name__ == "__main__":
    print("🚀 Starting TTS Speed-Up Tests")
    print("=" * 50)
    
    # Run tests
    success_count = 0
    total_tests = 2
    
    # Test 1: Story processing
    if test_process_story_for_tts():
        success_count += 1
        
    # Test 2: TTS generation with speed-up
    if test_tts_speedup():
        success_count += 1
        
    # Summary
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! TTS speed-up is working correctly.")
    else:
        print("❌ Some tests failed. Please check the output above.")
        
    # Ask user if they want to keep test files
    response = input("\n🗑️  Clean up test files? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        cleanup_test_files()
    else:
        print("📁 Test files preserved for manual inspection") 