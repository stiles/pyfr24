"""
Tests for the custom exceptions.
"""

import unittest
from pyfr24.exceptions import (
    FR24Error, FR24AuthenticationError, FR24RateLimitError, 
    FR24NotFoundError, FR24ServerError, FR24ClientError, 
    FR24ValidationError, FR24ConnectionError
)

class TestExceptions(unittest.TestCase):
    """Test cases for the custom exceptions."""
    
    def test_fr24_error(self):
        """Test FR24Error."""
        error = FR24Error("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertIsInstance(error, Exception)
    
    def test_fr24_authentication_error(self):
        """Test FR24AuthenticationError."""
        error = FR24AuthenticationError("Authentication failed")
        self.assertEqual(str(error), "Authentication failed")
        self.assertIsInstance(error, FR24Error)
    
    def test_fr24_rate_limit_error(self):
        """Test FR24RateLimitError."""
        error = FR24RateLimitError("Rate limit exceeded")
        self.assertEqual(str(error), "Rate limit exceeded")
        self.assertIsInstance(error, FR24Error)
    
    def test_fr24_not_found_error(self):
        """Test FR24NotFoundError."""
        error = FR24NotFoundError("Resource not found")
        self.assertEqual(str(error), "Resource not found")
        self.assertIsInstance(error, FR24Error)
    
    def test_fr24_server_error(self):
        """Test FR24ServerError."""
        error = FR24ServerError("Server error")
        self.assertEqual(str(error), "Server error")
        self.assertIsInstance(error, FR24Error)
    
    def test_fr24_client_error(self):
        """Test FR24ClientError."""
        error = FR24ClientError("Client error")
        self.assertEqual(str(error), "Client error")
        self.assertIsInstance(error, FR24Error)
    
    def test_fr24_validation_error(self):
        """Test FR24ValidationError."""
        error = FR24ValidationError("Validation error")
        self.assertEqual(str(error), "Validation error")
        self.assertIsInstance(error, FR24Error)
    
    def test_fr24_connection_error(self):
        """Test FR24ConnectionError."""
        error = FR24ConnectionError("Connection error")
        self.assertEqual(str(error), "Connection error")
        self.assertIsInstance(error, FR24Error)

if __name__ == '__main__':
    unittest.main() 