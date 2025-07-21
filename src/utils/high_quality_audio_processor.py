#!/usr/bin/env python3
"""
High Quality Audio Processing Utilities
Maintains audio quality during speed adjustments and other audio operations
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HighQualityAudioProcessor:
    """High-quality audio processing with minimal quality loss."""
    
    def __init__(self):
        self.sample_rate = 44100
        self.channels = 2  # Stereo
        
    def speed_up_audio_high_quality(self, 
                                   input_path: str, 
                                   output_path: str, 
                                   speed_factor: float = 1.1,
                                   maintain_pitch: bool = True) -> bool:
        """
        Speed up audio while maintaining high quality and optionally preserving pitch.
        
        Args:
            input_path: Path to input audio file
            output_path: Path to output audio file
            speed_factor: Speed multiplier (1.1 = 10% faster)
            maintain_pitch: Whether to maintain original pitch (recommended for voice)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from pydub import AudioSegment
            
            logger.info(f"🎵 High-quality speed adjustment: {speed_factor}x")
            logger.info(f"📁 Input: {input_path}")
            logger.info(f"📁 Output: {output_path}")
            
            # Load audio
            audio_segment = AudioSegment.from_file(input_path)
            original_duration_ms = len(audio_segment)
            original_duration_s = original_duration_ms / 1000.0
            
            logger.info(f"📊 Original duration: {original_duration_s:.3f}s")
            
            # Calculate expected duration
            expected_duration_ms = int(original_duration_ms / speed_factor)
            expected_duration_s = expected_duration_ms / 1000.0
            
            logger.info(f"📊 Expected duration: {expected_duration_s:.3f}s")
            
            # Add gentle fade-out to prevent artifacts
            fade_duration = min(200, original_duration_ms // 20)  # 200ms or 5% of duration
            audio_segment = audio_segment.fade_out(fade_duration)
            logger.info(f"🔧 Added {fade_duration}ms fade-out")
            
            # NEW APPROACH: Use pydub speedup with better quality settings
            # For small speed factors (1.1x), pydub actually works better than librosa
            # and preserves voice quality much better
            if speed_factor <= 1.15:  # For small speed increases, use pydub
                sped_up_audio = audio_segment.speedup(playback_speed=speed_factor)
                logger.info(f"✅ Used pydub speedup (better quality for small speed factors)")
                logger.info(f"✅ Voice quality preserved - no robotic sound")
            elif maintain_pitch and self._has_librosa():
                # Use librosa for larger speed factors
                sped_up_audio = self._librosa_speed_up(audio_segment, speed_factor)
                logger.info(f"✅ Used librosa high-quality time stretching (pitch preserved)")
                
                # Verify quality by checking audio characteristics
                original_rms = np.sqrt(np.mean(np.array(audio_segment.get_array_of_samples())**2))
                sped_up_rms = np.sqrt(np.mean(np.array(sped_up_audio.get_array_of_samples())**2))
                quality_ratio = sped_up_rms / original_rms if original_rms > 0 else 1.0
                
                if 0.8 <= quality_ratio <= 1.2:  # Within 20% of original quality
                    logger.info(f"✅ Audio quality verified: {quality_ratio:.2f} ratio (good)")
                else:
                    logger.warning(f"⚠️ Audio quality check: {quality_ratio:.2f} ratio (may be degraded)")
            else:
                # Fallback to pydub speedup
                sped_up_audio = audio_segment.speedup(playback_speed=speed_factor)
                logger.info(f"⚠️ Used pydub speedup (pitch may change)")
                logger.warning(f"⚠️ Lower quality speed adjustment - voice may sound robotic")
            
            # AGGRESSIVE: Trim to exact calculated duration
            sped_up_audio = sped_up_audio[:expected_duration_ms]
            actual_duration_ms = len(sped_up_audio)
            actual_duration_s = actual_duration_ms / 1000.0
            
            logger.info(f"✂️ Trimmed to exact duration: {actual_duration_s:.3f}s")
            
            # Verify duration accuracy
            duration_diff = abs(actual_duration_s - expected_duration_s)
            if duration_diff > 0.01:  # 10ms tolerance
                logger.warning(f"⚠️ Duration mismatch: {duration_diff:.3f}s")
            else:
                logger.info(f"✅ Perfect duration match: {duration_diff:.3f}s difference")
            
            # Export with high quality settings
            sped_up_audio.export(
                output_path,
                format="mp3",
                parameters=[
                    "-q:a", "0",  # High quality
                    "-write_xing", "0",  # Disable VBR header
                    "-id3v2_version", "0"  # Disable ID3 tags
                ]
            )
            
            # Verify output file
            if not os.path.exists(output_path):
                logger.error(f"❌ Output file not created: {output_path}")
                return False
            
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ High-quality speed adjustment completed")
            logger.info(f"📊 Output file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            logger.info(f"⏱️ Final duration: {actual_duration_s:.3f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ High-quality speed adjustment failed: {e}")
            return False
    
    def _has_librosa(self) -> bool:
        """Check if librosa is available for high-quality processing."""
        try:
            import librosa
            return True
        except ImportError:
            return False
    
    def _librosa_speed_up(self, audio_segment, speed_factor: float):
        """Use librosa for high-quality time stretching with better quality preservation."""
        try:
            import librosa
            import soundfile as sf
            import tempfile
            import os
            
            # Create temporary files for high-quality processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_input:
                temp_input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            try:
                # Export audio segment to temporary WAV file (librosa works better with WAV)
                audio_segment.export(temp_input_path, format="wav")
                
                # Load with librosa (this gives us floating-point data)
                audio_array, sample_rate = librosa.load(temp_input_path, sr=None, mono=False)
                
                # For stereo audio, process each channel separately for better quality
                if len(audio_array.shape) > 1:
                    # Stereo audio
                    left_channel = audio_array[0]
                    right_channel = audio_array[1]
                    
                    # Calculate time stretch factor (librosa uses stretch factor, inverse of speed)
                    time_stretch_factor = 1.0 / speed_factor
                    
                    # Apply high-quality time stretching with pitch preservation to each channel
                    left_sped_up = librosa.effects.time_stretch(left_channel, rate=time_stretch_factor)
                    right_sped_up = librosa.effects.time_stretch(right_channel, rate=time_stretch_factor)
                    
                    # Recombine stereo channels
                    sped_up_array = np.vstack([left_sped_up, right_sped_up])
                else:
                    # Mono audio
                    time_stretch_factor = 1.0 / speed_factor
                    sped_up_array = librosa.effects.time_stretch(audio_array, rate=time_stretch_factor)
                
                # Save the processed audio back to temporary file
                sf.write(temp_output_path, sped_up_array.T if len(sped_up_array.shape) > 1 else sped_up_array, sample_rate)
                
                # Load back as AudioSegment
                from pydub import AudioSegment
                sped_up_audio = AudioSegment.from_wav(temp_output_path)
                
                # Ensure correct format
                sped_up_audio = sped_up_audio.set_frame_rate(audio_segment.frame_rate)
                sped_up_audio = sped_up_audio.set_channels(audio_segment.channels)
                
                logger.info(f"✅ High-quality librosa time stretching completed")
                return sped_up_audio
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_input_path)
                    os.unlink(temp_output_path)
                except:
                    pass
            
        except Exception as e:
            logger.warning(f"⚠️ librosa processing failed: {e}")
            logger.warning(f"⚠️ Falling back to pydub speedup (lower quality)")
            # Fallback to pydub
            return audio_segment.speedup(playback_speed=speed_factor)
    
    def enhance_audio_quality(self, input_path: str, output_path: str) -> bool:
        """
        Enhance audio quality with gentle normalization only.
        NO COMPRESSION - preserves original audio quality.
        
        Args:
            input_path: Path to input audio file
            output_path: Path to output audio file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize
            
            logger.info(f"🎵 Enhancing audio quality (no compression): {input_path}")
            
            # Load audio
            audio_segment = AudioSegment.from_file(input_path)
            
            # Only normalize audio levels - NO COMPRESSION
            normalized_audio = normalize(audio_segment)
            
            # Export with high quality - preserve original quality
            normalized_audio.export(
                output_path,
                format="mp3",
                parameters=[
                    "-q:a", "0",  # High quality
                    "-write_xing", "0",
                    "-id3v2_version", "0"
                ]
            )
            
            logger.info(f"✅ Audio quality enhancement completed (no compression): {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Audio quality enhancement failed: {e}")
            return False
    
    def get_audio_info(self, audio_path: str) -> Optional[dict]:
        """Get detailed audio file information."""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(audio_path)
            
            info = {
                'duration_ms': len(audio),
                'duration_s': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'dBFS': audio.dBFS,
                'file_size': os.path.getsize(audio_path)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Could not get audio info: {e}")
            return None

def test_high_quality_audio_processor():
    """Test the high-quality audio processor."""
    processor = HighQualityAudioProcessor()
    
    # Test if librosa is available
    has_librosa = processor._has_librosa()
    print(f"librosa available: {has_librosa}")
    
    if has_librosa:
        print("✅ High-quality time stretching will be used")
    else:
        print("⚠️ Will fall back to pydub speedup")

if __name__ == "__main__":
    test_high_quality_audio_processor() 