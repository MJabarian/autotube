"""
Audio Mixing System for AutoTube
Combines TTS voiceover with background music for viral YouTube Shorts.
"""

import os
import json
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
import librosa
import soundfile as sf
from pathlib import Path
import logging
import re
import sys
from pathlib import Path

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioMixer:
    """Audio mixing system for combining TTS voiceover with background music."""
    
    def __init__(self):
        self.sample_rate = 44100
        self.channels = 2  # Stereo
        self.voice_target_db = -12  # Mobile optimized
        self.music_target_db = -24  # Mobile optimized (12dB below voice)

    def load_audio_file(self, file_path: str) -> AudioSegment:
        """Load audio file and convert to consistent format."""
        try:
            logger.info(f"Loading audio file: {file_path}")
            audio = AudioSegment.from_file(file_path)
            
            # Convert to consistent format
            audio = audio.set_frame_rate(self.sample_rate)
            audio = audio.set_channels(self.channels)
            
            logger.info(f"Loaded audio: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} channels")
            return audio
            
        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {e}")
            raise
    
    def balance_audio_levels(self, voice_audio: AudioSegment, music_audio: AudioSegment) -> tuple:
        """
        Balance audio levels for optimal voice prominence.
        Returns (balanced_voice, balanced_music)
        """
        logger.info("Balancing audio levels for mobile...")
        
        # Set voice to -12dB
        voice_adjustment = self.voice_target_db - voice_audio.dBFS
        balanced_voice = voice_audio + voice_adjustment
        
        # Set music to -24dB
        music_adjustment = self.music_target_db - music_audio.dBFS
        balanced_music = music_audio + music_adjustment
        
        logger.info(f"Voice adjusted by {voice_adjustment:.1f}dB, Music by {music_adjustment:.1f}dB")
        return balanced_voice, balanced_music
    
    def extend_music_simple(self, music_audio: AudioSegment, target_duration: int) -> AudioSegment:
        """Loop and trim music to match target duration. No crossfade, no math errors."""
        if len(music_audio) >= target_duration:
            return music_audio[:target_duration]
        loops_needed = int(np.ceil(target_duration / len(music_audio)))
        extended = music_audio * loops_needed
        return extended[:target_duration]
    
    def mix_audio(self, voice_audio: AudioSegment, music_audio: AudioSegment) -> AudioSegment:
        """
        Mix voice and music audio with proper balancing (no ducking).
        """
        logger.info("Mixing audio (simple, mobile-optimized)...")
        
        # Extend music if needed
        if len(music_audio) < len(voice_audio):
            music_audio = self.extend_music_simple(music_audio, len(voice_audio))
        elif len(music_audio) > len(voice_audio):
            music_audio = music_audio[:len(voice_audio)]
        
        # Balance levels (no ducking)
        balanced_voice, balanced_music = self.balance_audio_levels(voice_audio, music_audio)
        
        # Mix audio
        mixed = balanced_voice.overlay(balanced_music)
        
        # Normalize final output
        mixed = normalize(mixed)
        
        logger.info(f"Audio mixing completed: {len(mixed)}ms")
        return mixed
    
    def load_music_selection(self, story_title: str) -> str:
        """
        Load music selection from saved JSON file.
        """
        try:
            # Construct path to music selection file
            sanitized_title = self.sanitize_folder_name(story_title)
            music_selection_path = Config.OUTPUT_DIR / "music_selections" / sanitized_title / "music_selection.json"
            
            if not music_selection_path.exists():
                raise FileNotFoundError(f"Music selection file not found: {music_selection_path}")
            
            with open(music_selection_path, 'r') as f:
                music_data = json.load(f)
            
            music_file = music_data.get('selected_music_file')
            if not music_file:
                raise ValueError("No music file found in selection data")
            
            logger.info(f"Loaded music selection: {music_file}")
            return music_file
            
        except Exception as e:
            logger.error(f"Error loading music selection: {e}")
            raise
    
    from src.utils.folder_utils import sanitize_folder_name
    
    def process_story_audio(self, story_title: str, tts_audio_path: str = None) -> str:
        """
        Complete audio processing pipeline for a story.
        Returns path to final mixed audio file.
        """
        logger.info(f"Processing audio for story: {story_title}")
        
        try:
            # Load music selection
            music_file = self.load_music_selection(story_title)
            
            # Determine TTS audio path if not provided
            if tts_audio_path is None:
                sanitized_title = self.sanitize_folder_name(story_title)
                tts_audio_path = Config.OUTPUT_DIR / "audio" / sanitized_title / f"audio_{sanitized_title[:32]}.mp3"
            
            # Load audio files
            voice_audio = self.load_audio_file(str(tts_audio_path))
            music_audio = self.load_audio_file(music_file)
            
            # Mix audio
            mixed_audio = self.mix_audio(voice_audio, music_audio)
            
            # Create output directory
            sanitized_title = self.sanitize_folder_name(story_title)
            output_dir = Config.OUTPUT_DIR / "mixed_audio" / sanitized_title
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save final mixed audio
            output_path = output_dir / f"mixed_audio_{sanitized_title}.mp3"
            mixed_audio.export(
                str(output_path),
                format="mp3",
                parameters=["-q:a", "0"]  # High quality
            )
            
            logger.info(f"Final mixed audio saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error processing story audio: {e}")
            raise

    def mix_story_audio(self, tts_path, music_path, output_path):
        """Simple direct integration: mix TTS and music, save to output_path."""
        try:
            voice_audio = self.load_audio_file(tts_path)
            music_audio = self.load_audio_file(music_path)
            mixed = self.mix_audio(voice_audio, music_audio)
            out_dir = Path(output_path).parent
            out_dir.mkdir(parents=True, exist_ok=True)
            mixed.export(str(output_path), format="mp3", parameters=["-q:a", "0"])
            logger.info(f"Mixed story audio saved: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error in mix_story_audio: {e}")
            raise

def main():
    """Test the audio mixing system."""
    mixer = AudioMixer()
    
    # Example usage
    story_title = "What If the Roman Empire Embraced Christianity Early?"
    try:
        output_path = mixer.process_story_audio(story_title)
        print(f"✅ Audio mixing completed: {output_path}")
    except Exception as e:
        print(f"❌ Audio mixing failed: {e}")

if __name__ == "__main__":
    main() 