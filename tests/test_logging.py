"""
Test logging configuration.
"""

import unittest
import logging
import tempfile
import os
from pyfr24 import configure_logging

class TestLogging(unittest.TestCase):
    """Test logging configuration."""
    
    def test_configure_logging_default(self):
        """Test configure_logging with default parameters."""
        logger = configure_logging()
        
        self.assertEqual(logger.name, 'pyfr24')
        self.assertEqual(logger.level, logging.WARNING)
        self.assertTrue(len(logger.handlers) > 0)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
    
    def test_configure_logging_with_file(self):
        """Test configure_logging with a log file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_file = temp_file.name
        
        try:
            logger = configure_logging(log_file=log_file)
            
            self.assertEqual(logger.name, 'pyfr24')
            self.assertEqual(logger.level, logging.WARNING)
            self.assertTrue(len(logger.handlers) > 1)
            self.assertIsInstance(logger.handlers[1], logging.handlers.RotatingFileHandler)
            self.assertEqual(logger.handlers[1].baseFilename, log_file)
        finally:
            # Clean up the temporary file
            if os.path.exists(log_file):
                os.remove(log_file)
    
    def test_configure_logging_with_custom_level(self):
        """Test configure_logging with a custom level."""
        logger = configure_logging(level=logging.DEBUG)
        
        self.assertEqual(logger.name, 'pyfr24')
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_configure_logging_with_custom_format(self):
        """Test configure_logging with a custom format."""
        custom_format = '%(levelname)s - %(message)s'
        logger = configure_logging(log_format=custom_format)
        
        self.assertEqual(logger.name, 'pyfr24')
        self.assertEqual(logger.level, logging.WARNING)
        self.assertTrue(len(logger.handlers) > 0)
        self.assertEqual(logger.handlers[0].formatter._fmt, custom_format)

if __name__ == '__main__':
    unittest.main() 