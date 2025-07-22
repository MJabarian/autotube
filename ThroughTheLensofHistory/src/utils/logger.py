"""Logging configuration for the AI Video Generator."""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import sys
from pathlib import Path

# Add project root to path to import config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

def setup_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Name of the logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Config.OUTPUT_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logger
    logger = logging.getLogger(name)
    
    # Set log level
    level = getattr(logging, log_level or 'INFO', logging.INFO)
    logger.setLevel(level)
    
    # Prevent adding handlers multiple times in case of module reloading
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Create file handler
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f'{name.lower()}_{timestamp}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Create a default logger for the application
logger = setup_logger('ai_video_generator')

# Example usage:
# from utils.logger import get_logger
# logger = get_logger(__name__)
# logger.info('This is an info message')
# logger.error('This is an error message')
