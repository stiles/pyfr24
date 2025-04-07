#!/usr/bin/env python3
"""
Test runner script for the Pyfr24 client.
This script can be run from any directory and will discover and run all tests.
"""

import unittest
import sys
import os

def run_tests():
    """Discover and run all tests in the tests directory."""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the project root to the Python path
    sys.path.insert(0, script_dir)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(script_dir, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if tests passed, 1 if any failed
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 