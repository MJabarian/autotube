import os
from elevenlabs import generate, save, set_api_key
from dotenv import load_dotenv
import re

# Load environment variables from .env
load_dotenv()

# Import folder utilities first
from src.utils.folder_utils import sanitize_folder_name

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")  # Set this in your .env

if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment or .env file.")
if not ELEVENLABS_VOICE_ID:
    raise ValueError("ELEVENLABS_VOICE_ID not set in environment or .env file.")

set_api_key(ELEVENLABS_API_KEY)

# Import config resolver to get the correct output directory
import sys
from pathlib import Path

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
# Use config to get the correct output directory
OUTPUT_DIR = Config.OUTPUT_DIR / "audio"

def process_story_for_tts(story_text: str) -> str:
    """
    Convert/clean tags for ElevenLabs compatibility:
    - Convert [pause:1s] to <break time="1s"/>
    - Convert voice modulation tags to SSML prosody tags
    - Keep sound effect tags as-is: [gunshot], [applause], [laughter]
    - Remove unsupported tags
    """
    if not story_text or not isinstance(story_text, str):
        return ""
    
    # 1. Convert [pause:0.5s] or [pause:1s] to <break time="0.5s"/> etc.
    story_text = re.sub(r"\[pause:(\d+(?:\.\d*)?)s\]", r'<break time="\1s"/>', story_text)
    
    # 2. Convert voice modulation tags to SSML prosody
    voice_modulation_map = {
        # Emotional states
        'whispers': '<prosody volume="x-soft">',
        'excited': '<prosody rate="fast" pitch="high">',
        'sarcastic': '<prosody rate="slow" pitch="low">',
        'curious': '<prosody pitch="high">',
        'angry': '<prosody rate="fast" pitch="high" volume="loud">',
        'sad': '<prosody rate="slow" pitch="low">',
        'nervous': '<prosody rate="fast">',
        'confident': '<prosody volume="loud">',
        'mysterious': '<prosody rate="slow" pitch="low" volume="soft">',
        'dramatic': '<prosody rate="slow" volume="loud">',
        
        # Actions that should be removed (not sound effects)
        'sighs': '',
        'gasps': '',
        'chuckles': '',
        'pauses': '',
        'breathes': '',
        'gulps': '',
        'swallows': '',
    }
    
    # 3. Sound effects that should be kept as-is (ElevenLabs supports these)
    sound_effects = {
        'gunshot', 'applause', 'clapping', 'explosion', 'laughter', 'laughs', 
        'laughs harder', 'starts laughing', 'wheezing', 'crying', 'snorts'
    }
    
    # 4. Process voice modulation tags
    def replace_voice_tag(match):
        tag = match.group(1).lower().strip()
        
        # If it's a sound effect, keep it as-is
        if tag in sound_effects:
            return match.group(0)
        
        # If it's a voice modulation, convert to SSML
        if tag in voice_modulation_map:
            replacement = voice_modulation_map[tag]
            if replacement:  # If not empty
                return replacement
            else:  # If empty (should be removed)
                return ""
        
        # Unknown tag - remove it
        return ""
    
    # Apply voice tag replacements
    story_text = re.sub(r'\[([a-zA-Z\s]+)\]', replace_voice_tag, story_text)
    
    # 5. Close any opened prosody tags at the end of sentences
    # Find sentences and ensure prosody tags are closed
    sentences = re.split(r'([.!?])', story_text)
    processed_sentences = []
    
    for sentence in sentences:
        if sentence.strip():
            # Count open prosody tags
            open_tags = sentence.count('<prosody')
            close_tags = sentence.count('</prosody>')
            
            # Add missing closing tags
            if open_tags > close_tags:
                sentence += '</prosody>' * (open_tags - close_tags)
            
            processed_sentences.append(sentence)
    
    story_text = ''.join(processed_sentences)
    
    # 6. Clean up any malformed tags or extra spaces
    story_text = re.sub(r'\s+', ' ', story_text)  # Multiple spaces to single
    story_text = re.sub(r'<break time="(\d+(?:\.\d*)?)s"/>', r'<break time="\1s"/>', story_text)
    
    return story_text.strip()

def tts_story_to_audio(story_text: str, output_filename: str = "story_audio.mp3", story_title: str = None) -> str:
    """
    Convert story text (with SSML) to audio using ElevenLabs and save to output/audio/<story_folder>/.
    Returns the path to the saved audio file.
    """
    # Ensure .mp3 extension and strip any existing extension
    base_filename = os.path.splitext(output_filename)[0]
    output_filename = base_filename + ".mp3"
    print(f"[DEBUG] TTS: Ensuring .mp3 extension - {output_filename}")
    
    # Process tags for ElevenLabs compatibility
    processed_text = process_story_for_tts(story_text)
    if not processed_text:
        print(f"[ERROR] TTS: Processed text is empty")
        return None
    
    # Determine output path
    if story_title:
        folder_name = sanitize_folder_name(story_title)
        story_dir = os.path.join(OUTPUT_DIR, folder_name)
        output_path = os.path.join(story_dir, output_filename)
    else:
        story_dir = OUTPUT_DIR
        output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    print(f"[DEBUG] TTS: Generating audio for {len(processed_text)} characters")
    print(f"[DEBUG] TTS: Target folder: {story_dir}")
    print(f"[DEBUG] TTS: Target file: {output_path}")
    
    try:
        # Create directory with error handling
        try:
            os.makedirs(story_dir, exist_ok=True)
            print(f"[DEBUG] TTS: Directory created/verified: {story_dir}")
        except Exception as dir_error:
            print(f"[ERROR] TTS: Failed to create directory {story_dir}: {dir_error}")
            return None
        
        # Generate audio
        audio = generate(
            text=processed_text,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_multilingual_v2"
        )
        
        # Check if audio is valid (not None, not empty)
        if not audio or (hasattr(audio, '__len__') and len(audio) == 0):
            print(f"[ERROR] ElevenLabs returned empty audio for: {output_filename}")
            return None
        
        print(f"[DEBUG] TTS: Audio generated successfully, size: {len(audio)} bytes")
        
        # Test if we can write to the directory
        test_file = os.path.join(story_dir, "test_write.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"[DEBUG] TTS: Directory write test passed")
        except Exception as write_error:
            print(f"[ERROR] TTS: Cannot write to directory {story_dir}: {write_error}")
            return None
        
        # Save audio file with explicit error handling
        try:
            save(audio, output_path)
            print(f"[DEBUG] TTS: Audio saved to: {output_path}")
            
            # Add fade-out to prevent end artifacts in TTS audio
            try:
                from pydub import AudioSegment
                audio_segment = AudioSegment.from_mp3(output_path)
                original_duration = len(audio_segment)
                
                # Add gentle fade-out (200ms or 5% of duration, whichever is smaller)
                fade_duration = min(200, original_duration // 20)
                audio_segment = audio_segment.fade_out(fade_duration)
                
                # Speed up audio by 1.1x for viral effect (preserves pitch and quality)
                speed_factor = 1.1
                audio_segment = audio_segment.speedup(playback_speed=speed_factor)
                
                # Re-export with fade-out and speed-up
                audio_segment.export(output_path, format="mp3")
                new_duration = len(audio_segment)
                print(f"[DEBUG] TTS: Added {fade_duration}ms fade-out and {speed_factor}x speed-up to TTS audio")
                print(f"[DEBUG] TTS: Duration changed from {original_duration}ms to {new_duration}ms")
                
            except Exception as fade_error:
                print(f"[WARNING] TTS: Could not add fade-out and speed-up: {fade_error}")
                # Continue without fade-out and speed-up if it fails
                
        except Exception as save_error:
            print(f"[ERROR] TTS: ElevenLabs save() failed: {save_error}")
            return None
        
        # IMMEDIATELY check if file exists after save
        if not os.path.exists(output_path):
            print(f"[ERROR] Audio file was not created: {output_path}")
            print(f"[ERROR] ElevenLabs save() function failed silently")
            return None
            
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            print(f"[ERROR] Audio file was created but is empty: {output_path}")
            return None
            
        print(f"[INFO] Audio file saved: {output_path} ({file_size} bytes)")
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Exception during TTS generation: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up any partial file
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"[DEBUG] TTS: Removed failed file: {output_path}")
            except Exception as cleanup_error:
                print(f"[ERROR] Failed to cleanup failed file: {cleanup_error}")
        return None

if __name__ == "__main__":
    # Example usage
    example_text = "Hello! [pause:1s] [whispers] This is a test of your ElevenLabs voice. <emphasis>It supports SSML tags!</emphasis> <break time=\"1s\"/>"
    out_path = tts_story_to_audio(example_text, "test_audio.mp3", story_title="Test Story Title")
    print(f"Audio saved to: {out_path}") 