"""
Quality Optimizer - Video quality optimization and validation utilities
"""

import ffmpeg
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

class QualityOptimizer:
    """Video quality optimization and validation utilities"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def validate_video_file(self, video_path: str) -> Dict[str, any]:
        """
        Validate video file quality and specifications
        
        Returns:
            Dict with validation results and recommendations
        """
        try:
            probe = ffmpeg.probe(video_path)
            
            # Get video stream info
            video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            # Calculate video specs
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            fps = eval(video_stream['r_frame_rate'])
            duration = float(probe['format']['duration'])
            file_size_mb = float(probe['format']['size']) / (1024 * 1024)
            
            # YouTube Shorts requirements
            shorts_requirements = {
                'min_width': 1080,
                'min_height': 1920,
                'aspect_ratio': 9/16,  # 0.5625
                'min_duration': 15,  # seconds
                'max_duration': 60,  # seconds
                'max_file_size_mb': 256
            }
            
            # Validation results
            validation = {
                'file_path': video_path,
                'specs': {
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'duration': duration,
                    'file_size_mb': file_size_mb,
                    'has_audio': audio_stream is not None
                },
                'youtube_shorts_compliance': {
                    'resolution_ok': width >= shorts_requirements['min_width'] and height >= shorts_requirements['min_height'],
                    'aspect_ratio_ok': abs((width/height) - shorts_requirements['aspect_ratio']) < 0.1,
                    'duration_ok': shorts_requirements['min_duration'] <= duration <= shorts_requirements['max_duration'],
                    'file_size_ok': file_size_mb <= shorts_requirements['max_file_size_mb'],
                    'has_audio': audio_stream is not None
                },
                'quality_score': 0,
                'recommendations': []
            }
            
            # Calculate quality score (0-100)
            score = 0
            
            # Resolution score (40 points)
            if validation['youtube_shorts_compliance']['resolution_ok']:
                score += 40
            elif width >= 720 and height >= 1280:
                score += 30
            elif width >= 480 and height >= 854:
                score += 20
            
            # Aspect ratio score (20 points)
            if validation['youtube_shorts_compliance']['aspect_ratio_ok']:
                score += 20
            elif abs((width/height) - shorts_requirements['aspect_ratio']) < 0.2:
                score += 10
            
            # Duration score (20 points)
            if validation['youtube_shorts_compliance']['duration_ok']:
                score += 20
            elif duration > 0:
                score += 10
            
            # Audio score (10 points)
            if validation['youtube_shorts_compliance']['has_audio']:
                score += 10
            
            # File size score (10 points)
            if validation['youtube_shorts_compliance']['file_size_ok']:
                score += 10
            elif file_size_mb <= 512:  # Still acceptable
                score += 5
            
            validation['quality_score'] = score
            
            # Generate recommendations
            if not validation['youtube_shorts_compliance']['resolution_ok']:
                validation['recommendations'].append(
                    f"Resolution {width}x{height} is below YouTube Shorts minimum (1080x1920)"
                )
            
            if not validation['youtube_shorts_compliance']['aspect_ratio_ok']:
                validation['recommendations'].append(
                    f"Aspect ratio {width/height:.3f} should be closer to 0.5625 (9:16)"
                )
            
            if not validation['youtube_shorts_compliance']['duration_ok']:
                validation['recommendations'].append(
                    f"Duration {duration:.1f}s should be between 15-60 seconds for YouTube Shorts"
                )
            
            if not validation['youtube_shorts_compliance']['has_audio']:
                validation['recommendations'].append("Video should include audio track")
            
            if not validation['youtube_shorts_compliance']['file_size_ok']:
                validation['recommendations'].append(
                    f"File size {file_size_mb:.1f}MB exceeds YouTube Shorts limit (256MB)"
                )
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Error validating video file {video_path}: {str(e)}")
            return {
                'file_path': video_path,
                'error': str(e),
                'quality_score': 0,
                'recommendations': ['Unable to validate video file']
            }
    
    def optimize_video_for_youtube_shorts(self, 
                                        input_path: str, 
                                        output_path: str,
                                        target_bitrate: str = "2M",
                                        crf: int = 23) -> bool:
        """
        Optimize video specifically for YouTube Shorts
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            target_bitrate: Target video bitrate
            crf: Constant Rate Factor (18-28, lower = better quality)
            
        Returns:
            True if optimization successful
        """
        try:
            self.logger.info(f"Optimizing video for YouTube Shorts: {input_path}")
            
            # FFmpeg optimization command
            stream = (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    s='1080x1920',  # YouTube Shorts resolution
                    r=30,  # 30 FPS
                    preset='fast',
                    crf=crf,
                    b=target_bitrate,
                    pix_fmt='yuv420p',
                    movflags='faststart'  # Optimize for web streaming
                )
                .overwrite_output()
                .global_args('-y')
            )
            
            # Run optimization
            stream.run(capture_stdout=True, capture_stderr=True)
            
            # Validate output
            if Path(output_path).exists():
                validation = self.validate_video_file(output_path)
                self.logger.info(f"Optimization complete. Quality score: {validation['quality_score']}/100")
                return True
            else:
                self.logger.error("Optimized video file was not created")
                return False
                
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg optimization error: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error in video optimization: {str(e)}")
            return False
    
    def get_optimal_encoding_settings(self, 
                                    target_quality: str = "youtube_shorts",
                                    processing_speed: str = "balanced") -> Dict[str, any]:
        """
        Get optimal encoding settings based on target quality and processing speed
        
        Args:
            target_quality: 'youtube_shorts', 'high_quality', 'fast_processing'
            processing_speed: 'fast', 'balanced', 'slow'
            
        Returns:
            Dict with optimal encoding settings
        """
        settings = {
            'youtube_shorts': {
                'fast': {
                    'preset': 'ultrafast',
                    'crf': 25,
                    'bitrate': '1.5M',
                    'description': 'Fast processing for YouTube Shorts'
                },
                'balanced': {
                    'preset': 'fast',
                    'crf': 23,
                    'bitrate': '2M',
                    'description': 'Balanced quality and speed for YouTube Shorts'
                },
                'slow': {
                    'preset': 'medium',
                    'crf': 20,
                    'bitrate': '3M',
                    'description': 'High quality for YouTube Shorts'
                }
            },
            'high_quality': {
                'fast': {
                    'preset': 'fast',
                    'crf': 20,
                    'bitrate': '3M',
                    'description': 'Fast high quality processing'
                },
                'balanced': {
                    'preset': 'medium',
                    'crf': 18,
                    'bitrate': '4M',
                    'description': 'Balanced high quality'
                },
                'slow': {
                    'preset': 'slow',
                    'crf': 16,
                    'bitrate': '6M',
                    'description': 'Maximum quality processing'
                }
            }
        }
        
        return settings.get(target_quality, {}).get(processing_speed, settings['youtube_shorts']['balanced']) 