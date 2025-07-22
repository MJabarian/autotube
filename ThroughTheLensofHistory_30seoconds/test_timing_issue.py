#!/usr/bin/env python3
"""
Test to verify the timing issue between video and audio duration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from moviepy.editor import VideoFileClip, AudioFileClip

def test_timing_issue():
    """Test the timing issue between video and audio."""
    print("🔍 Testing timing issue between video and audio...")
    
    # Check the most recent video output
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ No output directory found")
        return
    
    # Find the most recent video
    video_files = list(output_dir.rglob("*_final.mp4"))
    if not video_files:
        print("❌ No final video files found")
        return
    
    # Get the most recent video
    latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
    print(f"📹 Testing video: {latest_video}")
    
    # Load video and check duration
    try:
        video = VideoFileClip(str(latest_video))
        video_duration = video.duration
        video_audio_duration = video.audio.duration if video.audio else 0
        video.close()
        
        print(f"📊 Video duration: {video_duration:.3f}s")
        print(f"📊 Video audio duration: {video_audio_duration:.3f}s")
        
        # Check if there's a mismatch
        if abs(video_duration - video_audio_duration) > 0.01:
            print(f"❌ TIMING ISSUE: Video is {video_duration - video_audio_duration:.3f}s longer than audio!")
            print(f"   This means images continue showing after audio ends.")
        else:
            print(f"✅ Perfect timing: Video and audio match")
            
    except Exception as e:
        print(f"❌ Error testing video: {e}")
    
    # Also check the mixed audio file
    mixed_audio_files = list(output_dir.rglob("mixed_audio_*.mp3"))
    if mixed_audio_files:
        latest_mixed = max(mixed_audio_files, key=lambda x: x.stat().st_mtime)
        print(f"\n🎵 Testing mixed audio: {latest_mixed}")
        
        try:
            mixed_audio = AudioFileClip(str(latest_mixed))
            mixed_duration = mixed_audio.duration
            mixed_audio.close()
            
            print(f"📊 Mixed audio duration: {mixed_duration:.3f}s")
            
            # Compare with video
            if abs(video_duration - mixed_duration) > 0.01:
                print(f"❌ TIMING ISSUE: Video is {video_duration - mixed_duration:.3f}s longer than mixed audio!")
                print(f"   This confirms the video continues after audio ends.")
            else:
                print(f"✅ Perfect timing: Video and mixed audio match")
                
        except Exception as e:
            print(f"❌ Error testing mixed audio: {e}")

if __name__ == "__main__":
    test_timing_issue() 