"""
Logging configuration for the Flightradar24 API client.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

def configure_logging(level=logging.WARNING, log_file=None, log_format=None):
    """
    Configure logging for the Flightradar24 API client.
    
    Args:
        level: Logging level (default: logging.WARNING)
        log_file: Path to log file (default: None, which means log to console only)
        log_format: Log format string (default: None, which uses a standard format)
        
    Returns:
        Logger instance
    """
    # Get the logger
    logger = logging.getLogger('pyfr24')
    
    # Set the log level
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    if log_format is None:
        formatter = logging.Formatter(
            '%(message)s'  # Simple format for console output
        )
    else:
        formatter = logging.Formatter(log_format)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        # Use detailed format for file logging
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger 