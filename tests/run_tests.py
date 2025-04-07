#!/usr/bin/env python
"""
Test runner for the pyfr24 package.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the test modules
from test_client import TestFR24API
from test_logging import TestLogging
from test_exceptions import TestExceptions

def run_tests():
    """Run all the tests."""
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add the test cases
    test_suite.addTest(unittest.makeSuite(TestFR24API))
    test_suite.addTest(unittest.makeSuite(TestLogging))
    test_suite.addTest(unittest.makeSuite(TestExceptions))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return the exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 