"""
Centralized utilities for consistent folder naming across AutoTube components.
"""

import re
from datetime import datetime
from pathlib import Path

def sanitize_folder_name(name: str) -> str:
    """
    Consistent folder name sanitization across all AutoTube components.
    
    Rules:
    - Remove all non-alphanumeric characters except hyphens and underscores
    - Replace spaces with underscores
    - Limit to 50 characters
    - Ensure consistent naming like: EinsteinsSecretThePlagiarismScandal
    
    Args:
        name: The original name to sanitize
        
    Returns:
        Sanitized folder name
    """
    if not name:
        return "untitled"
    
    # Remove all non-alphanumeric characters except hyphens and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', name)
    
    # Replace spaces with underscores (though spaces should already be removed above)
    sanitized = sanitized.replace(' ', '_')
    
    # Remove any leading/trailing underscores or hyphens
    sanitized = sanitized.strip('_-')
    
    # Limit to 50 characters
    sanitized = sanitized[:50]
    
    # Ensure it's not empty
    if not sanitized:
        return "untitled"
    
    return sanitized

def create_log_filename(topic_name: str, pipeline_type: str = "content_gen") -> str:
    """
    Create a consistent log filename with topic name and timestamp.
    
    Args:
        topic_name: The topic name for the log
        pipeline_type: Type of pipeline (content_gen, audio_video, etc.)
        
    Returns:
        Log filename like: EinsteinsSecretThePlagiarismScandal_content_gen_2025-07-18_11-30-45.log
    """
    sanitized_name = sanitize_folder_name(topic_name)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{sanitized_name}_{pipeline_type}_{timestamp}.log"

def setup_logging_with_file(topic_name: str, pipeline_type: str = "content_gen", log_dir: str = None):
    """
    Setup logging with a file handler using consistent naming.
    
    Args:
        topic_name: The topic name for the log
        pipeline_type: Type of pipeline
        log_dir: Directory to store logs (defaults to Config.OUTPUT_DIR/content_gen_logs)
        
    Returns:
        Logger instance
    """
    import logging
    
    # Use Config.OUTPUT_DIR if log_dir is not specified
    if log_dir is None:
        from config import Config
        log_dir = str(Config.OUTPUT_DIR / "content_gen_logs")
    
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create log filename
    log_filename = create_log_filename(topic_name, pipeline_type)
    log_path = Path(log_dir) / log_filename
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    logger = logging.getLogger(f"autotube.{pipeline_type}")
    logger.info(f"🚀 Starting {pipeline_type} pipeline for topic: {topic_name}")
    logger.info(f"📝 Log file: {log_path}")
    
    return logger 