"""Error handling utilities for the AI Video Generator."""
import functools
import logging
from typing import Callable, TypeVar, Any, Optional, Type, Tuple

# Config import removed as it's not used in this file
from .logger import get_logger

# Create a logger for error handling
error_logger = get_logger('error_handling')

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])

class VideoGenerationError(Exception):
    """Base exception for video generation errors."""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class APIError(VideoGenerationError):
    """Exception raised for API-related errors."""
    pass

class ValidationError(VideoGenerationError):
    """Exception raised for validation errors."""
    pass

def handle_errors(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = False
):
    """
    A decorator to handle exceptions in a consistent way.
    
    Args:
        exceptions: Tuple of exception types to catch
        default_return: Value to return if an exception is caught
        log_error: Whether to log the error
        reraise: Whether to re-raise the exception after handling it
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    error_logger.error(
                        f"Error in {func.__name__}: {str(e)}",
                        exc_info=True,
                        extra={
                            'function': func.__name__,
                            'args': args,
                            'kwargs': kwargs,
                            'error_type': type(e).__name__
                        }
                    )
                
                if reraise:
                    raise
                
                return default_return
        return wrapper  # type: ignore
    return decorator

def validate_input(
    condition: bool, 
    message: str,
    error_type: Type[Exception] = ValidationError,
    **details: Any
) -> None:
    """
    Validate an input condition and raise an exception if it's not met.
    
    Args:
        condition: The condition to check
        message: Error message if the condition is False
        error_type: Type of exception to raise
        **details: Additional details to include in the exception
    """
    if not condition:
        error = error_type(message, details)
        error_logger.error(f"Validation failed: {message}", extra=details)
        raise error

def log_execution(func: F) -> F:
    """
    Decorator to log function execution start and end.
    
    Args:
        func: Function to decorate
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Starting {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__} successfully")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper  # type: ignore

# Example usage:
# @handle_errors((APIError,), default_return=None)
# def some_api_call():
#     # API call implementation
#     pass
# 
# @log_execution
# def some_important_function():
#     # Function implementation
#     pass
