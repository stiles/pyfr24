"""
Test that the version is defined in exactly one place.

Version 0.2.0 shipped reporting itself as 1.0.0 because setup.py and
__init__.py each carried their own literal and the bump only updated one.
"""

import os
import re
import subprocess
import sys
import unittest

import pyfr24

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestVersion(unittest.TestCase):
    """Test version consistency across packaging files."""

    def test_setup_py_matches_package_version(self):
        """setup.py must report what pyfr24.__version__ says."""
        result = subprocess.run(
            [sys.executable, 'setup.py', '--version'],
            cwd=ROOT, capture_output=True, text=True,
        )

        self.assertEqual(result.returncode, 0, f"setup.py failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), pyfr24.__version__)

    def test_setup_py_does_not_hardcode_a_version(self):
        """A literal in setup.py reintroduces the number that drifted."""
        with open(os.path.join(ROOT, 'setup.py'), encoding='utf-8') as f:
            source = f.read()

        self.assertIsNone(
            re.search(r'''version\s*=\s*['"]\d''', source),
            "setup.py hardcodes a version; it should call read_version() instead",
        )

    def test_version_looks_like_a_release(self):
        """Guard against a mangled __version__ line."""
        self.assertRegex(pyfr24.__version__, r'^\d+\.\d+\.\d+$')

if __name__ == '__main__':
    unittest.main()
