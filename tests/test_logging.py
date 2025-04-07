"""
Tests for the logging configuration.
"""

import os
import logging
import tempfile
import unittest
from pyfr24.logging import configure_logging

class TestLogging(unittest.TestCase):
    """Test cases for the logging configuration."""
    
    def test_configure_logging_default(self):
        """Test configure_logging with default parameters."""
        logger = configure_logging()
        
        self.assertEqual(logger.name, 'pyfr24')
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
    
    def test_configure_logging_with_file(self):
        """Test configure_logging with a log file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_file = temp_file.name
        
        try:
            logger = configure_logging(log_file=log_file)
            
            self.assertEqual(logger.name, 'pyfr24')
            self.assertEqual(logger.level, logging.INFO)
            self.assertEqual(len(logger.handlers), 2)
            
            # Check that the file exists
            self.assertTrue(os.path.exists(log_file))
        finally:
            # Clean up
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_configure_logging_with_custom_format(self):
        """Test configure_logging with a custom format."""
        custom_format = '%(levelname)s - %(message)s'
        logger = configure_logging(log_format=custom_format)
        
        self.assertEqual(logger.name, 'pyfr24')
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 1)
        
        # Check that the formatter has the custom format
        formatter = logger.handlers[0].formatter
        self.assertEqual(formatter._fmt, custom_format)
    
    def test_configure_logging_with_custom_level(self):
        """Test configure_logging with a custom level."""
        logger = configure_logging(level=logging.DEBUG)
        
        self.assertEqual(logger.name, 'pyfr24')
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(len(logger.handlers), 1)

if __name__ == '__main__':
    unittest.main() 