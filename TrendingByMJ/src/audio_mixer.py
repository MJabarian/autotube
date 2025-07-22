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

        # High-quality audio processing
        try:
            from src.utils.high_quality_audio_processor import HighQualityAudioProcessor
            self.high_quality_processor = HighQualityAudioProcessor()
            self.has_high_quality = True
        except ImportError:
            self.high_quality_processor = None
            self.has_high_quality = False

    def load_audio_file(self, file_path: str) -> AudioSegment:
        """Load audio file and convert to consistent format."""
        try:
            logger.info(f"Loading audio file: {file_path}")
            audio = AudioSegment.from_file(file_path)
            
            # Convert to consistent format
            audio = audio.set_frame_rate(self.sample_rate)
            audio = audio.set_channels(self.channels)
            
            # CRITICAL: Verify audio quality and duration
            duration_ms = len(audio)
            duration_sec = duration_ms / 1000.0
            
            logger.info(f"Loaded audio: {duration_ms}ms ({duration_sec:.3f}s), {audio.frame_rate}Hz, {audio.channels} channels")
            
            # Check for potential issues
            if duration_ms < 1000:  # Less than 1 second
                logger.warning(f"⚠️ Very short audio: {duration_sec:.3f}s")
            elif duration_ms > 300000:  # More than 5 minutes
                logger.warning(f"⚠️ Very long audio: {duration_sec:.3f}s")
            
            return audio
            
        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {e}")
            raise
    
    def verify_audio_duration(self, audio: AudioSegment, expected_duration_ms: int = None) -> bool:
        """Verify audio duration and log any issues."""
        actual_duration = len(audio)
        
        if expected_duration_ms:
            tolerance = 50  # 50ms tolerance
            if abs(actual_duration - expected_duration_ms) > tolerance:
                logger.warning(f"⚠️ Duration mismatch: {actual_duration}ms vs expected {expected_duration_ms}ms")
                return False
            else:
                logger.info(f"✅ Duration verified: {actual_duration}ms")
                return True
        else:
            logger.info(f"📊 Audio duration: {actual_duration}ms")
            return True
    
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
        """Loop and trim music to match target duration with EXACT precision."""
        if len(music_audio) >= target_duration:
            # CRITICAL: Exact trim to prevent extra audio
            result = music_audio[:target_duration]
            logger.info(f"Trimmed music to exact duration: {len(result)}ms")
            return result
        
        loops_needed = int(np.ceil(target_duration / len(music_audio)))
        extended = music_audio * loops_needed
        
        # CRITICAL: Exact trim to prevent extra audio at end
        result = extended[:target_duration]
        logger.info(f"Extended music with {loops_needed} loops, trimmed to exact duration: {len(result)}ms")
        return result
    
    def mix_audio(self, voice_audio: AudioSegment, music_audio: AudioSegment) -> AudioSegment:
        """
        Mix voice and music audio with EXACT duration matching to prevent end audio issues.
        """
        logger.info("Mixing audio with exact duration matching...")
        
        # Get exact voice duration (this is our target)
        voice_duration = len(voice_audio)
        logger.info(f"Target duration: {voice_duration}ms")
        
        # Extend music if needed
        if len(music_audio) < voice_duration:
            music_audio = self.extend_music_simple(music_audio, voice_duration)
        elif len(music_audio) > voice_duration:
            # CRITICAL: Trim music to exact voice duration (no extra audio)
            music_audio = music_audio[:voice_duration]
            logger.info(f"Trimmed music from {len(music_audio)}ms to {voice_duration}ms")
        
        # Balance levels (no ducking)
        balanced_voice, balanced_music = self.balance_audio_levels(voice_audio, music_audio)
        
        # Mix audio
        mixed = balanced_voice.overlay(balanced_music)
        
        # CRITICAL: Ensure exact duration match (prevent end audio issues)
        if len(mixed) > voice_duration:
            mixed = mixed[:voice_duration]
            logger.info(f"Trimmed mixed audio to exact duration: {voice_duration}ms")
        
        # AGGRESSIVE FIX: Add fade-out to prevent any end artifacts
        fade_duration = min(500, voice_duration // 10)  # 500ms or 10% of duration, whichever is smaller
        if fade_duration > 0:
            mixed = mixed.fade_out(fade_duration)
            logger.info(f"Added {fade_duration}ms fade-out to prevent end artifacts")
        
        # CRITICAL: Final trim to exact duration after fade
        if len(mixed) > voice_duration:
            mixed = mixed[:voice_duration]
            logger.info(f"Final trim after fade: {len(mixed)}ms")
        
        # Normalize final output
        mixed = normalize(mixed)
        
        # CRITICAL: Ultra-strict duration verification (1ms tolerance)
        final_duration = len(mixed)
        if abs(final_duration - voice_duration) > 1:  # Ultra-strict tolerance (1ms)
            logger.warning(f"⚠️ Duration mismatch: {final_duration}ms vs {voice_duration}ms")
            # Force exact duration
            if final_duration > voice_duration:
                mixed = mixed[:voice_duration]
                logger.info(f"🔧 Forced exact duration: {len(mixed)}ms")
            elif final_duration < voice_duration:
                # Add silence to match duration (rare case)
                silence_needed = voice_duration - final_duration
                silence = AudioSegment.silent(duration=silence_needed)
                mixed = mixed + silence
                logger.info(f"🔧 Added {silence_needed}ms silence to match duration: {len(mixed)}ms")
        else:
            logger.info(f"✅ Perfect duration match: {final_duration}ms")
        
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
            
            # Load audio files with duration verification
            voice_audio = self.load_audio_file(str(tts_audio_path))
            music_audio = self.load_audio_file(music_file)
            
            # CRITICAL: Verify voice audio duration before mixing
            voice_duration = len(voice_audio)
            self.verify_audio_duration(voice_audio, voice_duration)
            
            # Mix audio with exact duration matching
            mixed_audio = self.mix_audio(voice_audio, music_audio)
            
            # CRITICAL: Final verification of mixed audio
            final_duration = len(mixed_audio)
            if not self.verify_audio_duration(mixed_audio, voice_duration):
                logger.warning(f"⚠️ Mixed audio duration issue: {final_duration}ms vs expected {voice_duration}ms")
            else:
                logger.info(f"✅ Perfect audio mixing: {final_duration}ms")
            
            # Create output directory
            sanitized_title = self.sanitize_folder_name(story_title)
            output_dir = Config.OUTPUT_DIR / "mixed_audio" / sanitized_title
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save final mixed audio
            output_path = output_dir / f"mixed_audio_{sanitized_title}.mp3"
            
            # AGGRESSIVE FIX: Ensure exact duration before export
            export_duration = len(mixed_audio)
            if export_duration > voice_duration:
                mixed_audio = mixed_audio[:voice_duration]
                logger.info(f"Final trim before export: {len(mixed_audio)}ms")
            
            # Export with high quality and exact duration
            mixed_audio.export(
                str(output_path),
                format="mp3",
                parameters=[
                    "-q:a", "0",  # High quality
                    "-write_xing", "0",  # Disable VBR header that can cause issues
                    "-id3v2_version", "0"  # Disable ID3 tags that can cause issues
                ]
            )
            
            # HIGH QUALITY: Enhance audio quality after export (DISABLED - was causing quality issues)
            # Audio enhancement disabled to preserve original quality
            # The mixed audio is already high quality and doesn't need additional processing
            
            # VERIFICATION: Check the exported file duration
            try:
                exported_audio = AudioSegment.from_file(str(output_path))
                exported_duration = len(exported_audio)
                logger.info(f"Exported audio duration: {exported_duration}ms")
                
                if abs(exported_duration - voice_duration) > 10:
                    logger.warning(f"⚠️ Exported audio duration mismatch: {exported_duration}ms vs {voice_duration}ms")
                else:
                    logger.info(f"✅ Exported audio duration verified: {exported_duration}ms")
            except Exception as e:
                logger.warning(f"⚠️ Could not verify exported audio duration: {e}")
            
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
            
            # Get exact voice duration
            voice_duration = len(voice_audio)
            logger.info(f"Voice duration: {voice_duration}ms")
            
            mixed = self.mix_audio(voice_audio, music_audio)
            
            # AGGRESSIVE FIX: Final verification before export
            final_duration = len(mixed)
            if final_duration > voice_duration:
                mixed = mixed[:voice_duration]
                logger.info(f"Final trim in simple mix: {len(mixed)}ms")
            
            out_dir = Path(output_path).parent
            out_dir.mkdir(parents=True, exist_ok=True)
            
            # Export with enhanced parameters
            mixed.export(
                str(output_path), 
                format="mp3", 
                parameters=[
                    "-q:a", "0",  # High quality
                    "-write_xing", "0",  # Disable VBR header
                    "-id3v2_version", "0"  # Disable ID3 tags
                ]
            )
            
            # HIGH QUALITY: Enhance audio quality after export (DISABLED - was causing quality issues)
            # Audio enhancement disabled to preserve original quality
            # The mixed audio is already high quality and doesn't need additional processing
            
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